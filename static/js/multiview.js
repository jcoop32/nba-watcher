let activeGameId = null;
let selectedGames = [];
let allGames = [];
let nbaGamesCache = [];
let euroGamesCache = [];
let idleTimer = null;
const IDLE_TIMEOUT = 3000;

function setActiveGame(gameId) {
  activeGameId = gameId;

  document.querySelectorAll('.game-container').forEach(container => {
    container.classList.remove('active');
  });

  const activeContainer = document.querySelector(`[data-game-id="${gameId}"]`);
  if (activeContainer) {
    activeContainer.classList.add('active');
  }

  localStorage.setItem('nba_watcher_active_game', gameId);
}

function updateGridLayout() {
  const grid = document.getElementById('gameGrid');
  const numGames = selectedGames.length;

  grid.className = `multi-game-grid grid-${numGames}`;
}

function renderGames() {
  const grid = document.getElementById('gameGrid');

  if (selectedGames.length === 0) {
    grid.innerHTML = `
            <div class="empty-state">
                <h2>No Games Selected</h2>
                <p>Add games to start watching</p>
                <button class="control-btn control-btn-primary" onclick="showGameSelector()">
                    ➕ Add Game
                </button>
            </div>
        `;
    updateGridLayout();
    return;
  }

  const emptyState = grid.querySelector('.empty-state');
  if (emptyState) {
    emptyState.remove();
  }

  const existingContainers = Array.from(
    grid.querySelectorAll('.game-container'),
  );
  const existingGameIds = existingContainers.map(c => c.dataset.gameId);
  const newGameIds = selectedGames.map(g => g.game_id);

  existingContainers.forEach(container => {
    if (!newGameIds.includes(container.dataset.gameId)) {
      container.remove();
    }
  });

  selectedGames.forEach((game, index) => {
    if (!existingGameIds.includes(game.game_id)) {
      const container = createGameContainer(game, index);
      grid.appendChild(container);
    } else {
      updateStreamSourceButtons(game);
    }
  });

  updateGridLayout();

  if (activeGameId) {
    const activeContainer = document.querySelector(
      `[data-game-id="${activeGameId}"]`,
    );
    if (activeContainer) {
      activeContainer.classList.add('active');
    }
  } else if (selectedGames.length > 0) {
    setActiveGame(selectedGames[0].game_id);
  }
}

function updateStreamSourceButtons(game) {
  const container = document.querySelector(`[data-game-id="${game.game_id}"]`);
  if (!container) return;

  const selector = container.querySelector('.stream-source-selector');
  if (!selector || !game.streams || game.streams.length === 0) return;

  selector.innerHTML = game.streams
    .map(
      (stream, idx) => `
        <button class="stream-source-btn ${
          idx === game.currentStreamIndex ? 'active' : ''
        }"
                onclick="event.stopPropagation(); changeStreamSource('${
                  game.game_id
                }', ${idx})">
            ${stream.name || `Source ${idx + 1}`}
        </button>
    `,
    )
    .join('');
}

function createGameContainer(game, index) {
  const container = document.createElement('div');
  container.className = 'game-container';
  container.dataset.gameId = game.game_id;

  const showAddButton = selectedGames.length < 4;

  let streamSourcesHTML = '';
  if (game.streams && game.streams.length > 0) {
    streamSourcesHTML = `
            <div class="stream-source-selector">
                ${game.streams
                  .map(
                    (stream, idx) => `
                    <button class="stream-source-btn ${
                      idx === game.currentStreamIndex ? 'active' : ''
                    }"
                            onclick="event.stopPropagation(); changeStreamSource('${
                              game.game_id
                            }', ${idx})">
                        ${stream.name || `Source ${idx + 1}`}
                    </button>
                `,
                  )
                  .join('')}
            </div>
        `;
  }

  container.innerHTML = `
        ${
          showAddButton
            ? '<button class="add-game-overlay-btn" onclick="event.stopPropagation(); showGameSelector()" title="Add Game">➕ Add Game</button>'
            : ''
        }

        <div class="game-controls">
            <button class="game-control-btn replace-btn" onclick="event.stopPropagation(); replaceGame('${
              game.game_id
            }')" title="Replace Game">⇄</button>
            <button class="game-control-btn" onclick="event.stopPropagation(); removeGame('${
              game.game_id
            }')" title="Remove">✕</button>
        </div>

        <div class="stream-container">
            <iframe src="${game.stream_url}"
                    allowfullscreen
                    allow="autoplay; fullscreen"></iframe>
        </div>

        ${streamSourcesHTML}
    `;

  return container;
}

function changeStreamSource(gameId, streamIndex) {
  const game = selectedGames.find(g => g.game_id === gameId);
  if (!game || !game.streams || streamIndex >= game.streams.length) return;

  game.currentStreamIndex = streamIndex;
  game.stream_url = game.streams[streamIndex].url;

  const container = document.querySelector(`[data-game-id="${gameId}"]`);
  if (container) {
    const iframe = container.querySelector('iframe');
    if (iframe) {
      iframe.src = game.stream_url;
    }

    const buttons = container.querySelectorAll('.stream-source-btn');
    buttons.forEach((btn, idx) => {
      if (idx === streamIndex) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });
  }

  saveSelectedGames();
}

function removeGame(gameId) {
  selectedGames = selectedGames.filter(g => g.game_id !== gameId);

  if (activeGameId === gameId) {
    activeGameId = selectedGames.length > 0 ? selectedGames[0].game_id : null;
  }

  renderGames();
  saveSelectedGames();
}

function removeGameFromModal(gameId) {
  selectedGames = selectedGames.filter(g => g.game_id !== gameId);

  if (activeGameId === gameId) {
    activeGameId = selectedGames.length > 0 ? selectedGames[0].game_id : null;
  }

  renderGames();
  saveSelectedGames();

  const item = document.querySelector(`[data-game-id="${gameId}"]`);
  if (item) {
    const button = item.querySelector('.add-game-btn');
    if (button) {
      button.textContent = '+ Add';
      button.classList.remove('added');
      button.onclick = () => addGame(gameId);
    }
    item.classList.remove('selected');
  }
}

function replaceGame(gameId) {
  showGameSelector(gameId);
}

function replaceWithGame(oldGameId, newGameId) {
  const newGameData = allGames.find(g => g.id === newGameId);
  if (!newGameData) return;

  const oldGameIndex = selectedGames.findIndex(g => g.game_id === oldGameId);
  if (oldGameIndex === -1) return;

  const streamUrls = newGameData.streams || [];
  const streams = streamUrls.map((url, index) => ({
    name: `Stream ${index + 1}`,
    url: url,
  }));

  const newGame = {
    game_id: newGameId,
    stream_url: streams.length > 0 ? streams[0].url : '',
    streams: streams,
    currentStreamIndex: 0,
    game_data: newGameData,
  };

  selectedGames[oldGameIndex] = newGame;

  if (activeGameId === oldGameId) {
    activeGameId = newGameId;
  }

  renderGames();
  saveSelectedGames();

  closeGameSelector();
}

function showGameSelector(replacingGameId = null) {
  const p1 = fetch('/api/games-today').then(res => res.json());
  const p2 = fetch('/api/euro-games').then(res => res.json());

  Promise.all([p1, p2])
    .then(([nbaGames, euroGames]) => {
      nbaGamesCache = nbaGames || [];
      euroGamesCache = euroGames || [];
      allGames = [...nbaGamesCache, ...euroGamesCache];

      createGameSelectorModal(replacingGameId);
    })
    .catch(err => {
      console.error('Error fetching games:', err);
      alert('Failed to load games');
    });
}

function createGameSelectorModal(replacingGameId = null) {
  const existingModal = document.getElementById('gameSelectionModal');
  if (existingModal) existingModal.remove();

  const modal = document.createElement('div');
  modal.id = 'gameSelectionModal';
  modal.className = 'modal-overlay';

  const modalTitle =
    replacingGameId !== null ? 'Replace Game' : 'Add Games to Watch';

  const generateListHTML = games => {
    if (!games || games.length === 0)
      return '<p style="color: #666; padding: 20px; text-align: center;">No games available</p>';

    return games
      .map(game => {
        const gameId = game.id;
        const isAdded = selectedGames.some(g => g.game_id === gameId);
        const isBeingReplaced = gameId === replacingGameId;

        if (replacingGameId && isBeingReplaced) return '';

        const displayTitle =
          game.title || `${game.away_tricode} @ ${game.home_tricode}`;
        let statusDisplay = game.status || 'UPCOMING';
        if (game.status && game.status.includes('LIVE'))
          statusDisplay = '🔴 LIVE';

        return `
            <div class="game-selection-item ${
              isAdded && !replacingGameId ? 'selected' : ''
            }" data-game-id="${gameId}">
                <div class="game-info">
                    <div class="game-teams">${displayTitle}</div>
                    <div class="game-time">${
                      game.game_start || ''
                    } • ${statusDisplay}</div>
                </div>
                <button class="add-game-btn ${
                  isAdded && !replacingGameId ? 'added' : ''
                }"
                        onclick="${
                          replacingGameId
                            ? `replaceWithGame('${replacingGameId}', '${gameId}')`
                            : isAdded
                            ? `removeGameFromModal('${gameId}')`
                            : `addGame('${gameId}')`
                        }">
                    ${
                      replacingGameId
                        ? '↔ Replace'
                        : isAdded
                        ? '✓ Added'
                        : '+ Add'
                    }
                </button>
            </div>
        `;
      })
      .join('');
  };

  modal.innerHTML = `
        <div class="modal-content">
            <h2>${modalTitle}</h2>

            <div class="modal-tabs">
                <button class="modal-tab-btn active" onclick="switchModalTab('nba')">NBA 🏀</button>
                <button class="modal-tab-btn" onclick="switchModalTab('euro')">Euro/Other 🌍</button>
            </div>

            <div id="list-nba" class="game-list-container active">
                ${generateListHTML(nbaGamesCache)}
            </div>
            <div id="list-euro" class="game-list-container">
                ${generateListHTML(euroGamesCache)}
            </div>

            <div class="modal-actions">
                <button class="modal-btn modal-btn-secondary" onclick="closeGameSelector()">Done</button>
            </div>
        </div>
    `;

  document.body.appendChild(modal);
}

function switchModalTab(tabName) {
  document
    .querySelectorAll('.modal-tab-btn')
    .forEach(btn => btn.classList.remove('active'));
  const activeBtn = document.querySelector(
    `.modal-tab-btn[onclick="switchModalTab('${tabName}')"]`,
  );
  if (activeBtn) activeBtn.classList.add('active');

  document
    .querySelectorAll('.game-list-container')
    .forEach(div => div.classList.remove('active'));
  document.getElementById(`list-${tabName}`).classList.add('active');
}

function addGame(gameId) {
  if (selectedGames.some(g => g.game_id === gameId)) {
    return;
  }

  if (selectedGames.length >= 4) {
    alert('Maximum 4 games can be displayed at once');
    return;
  }

  const gameData = allGames.find(g => g.id === gameId);
  if (!gameData) return;

  const streamUrls = gameData.streams || [];
  const streams = streamUrls.map((url, index) => ({
    name: `Stream ${index + 1}`,
    url: url,
  }));

  const defaultStreamUrl = streams.length > 0 ? streams[0].url : '';

  selectedGames.push({
    game_id: gameId,
    stream_url: defaultStreamUrl,
    streams: streams,
    currentStreamIndex: 0,
    game_data: gameData,
  });

  renderGames();
  saveSelectedGames();

  const button = document.querySelector(
    `[data-game-id="${gameId}"] .add-game-btn`,
  );
  if (button) {
    button.textContent = '✓ Added';
    button.classList.add('added');
    button.disabled = true;
    button.closest('.game-selection-item').classList.add('selected');
  }
}

function closeGameSelector() {
  const modal = document.getElementById('gameSelectionModal');
  if (modal) {
    modal.remove();
  }
}

function saveSelectedGames() {
  return;
}

function loadSelectedGames() {
  return;
}

// Fullscreen Logic
function toggleFullscreen() {
  const elem = document.documentElement; // Make the whole page fullscreen

  if (!document.fullscreenElement) {
    elem.requestFullscreen().catch(err => {
      console.error(
        `Error attempting to enable full-screen mode: ${err.message}`,
      );
    });
  } else {
    document.exitFullscreen();
  }
}

document.addEventListener('fullscreenchange', () => {
  const btn = document.getElementById('fsBtn');
  if (!btn) return;

  if (document.fullscreenElement) {
    btn.textContent = '✕ Exit';
  } else {
    btn.textContent = '⛶ Fullscreen';
  }
});

function setupIdleDetection() {
  const resetIdleTimer = () => {
    document.body.classList.remove('user-idle');

    if (idleTimer) clearTimeout(idleTimer);

    if (document.fullscreenElement) {
      idleTimer = setTimeout(() => {
        document.body.classList.add('user-idle');
      }, IDLE_TIMEOUT);
    }
  };

  document.addEventListener('mousemove', resetIdleTimer);
  document.addEventListener('mousedown', resetIdleTimer);
  document.addEventListener('keydown', resetIdleTimer);

  document.addEventListener('fullscreenchange', resetIdleTimer);
}

document.addEventListener('keydown', e => {
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
    return;
  }

  const games = selectedGames;

  switch (e.key.toLowerCase()) {
    case '1':
    case '2':
    case '3':
    case '4':
      const index = parseInt(e.key) - 1;
      if (games[index]) {
        setActiveGame(games[index].game_id);
      }
      break;

    case 'a':
      showGameSelector();
      break;

    case 'escape':
      closeGameSelector();
      break;
  }
});

document.addEventListener('click', e => {
  if (e.target.classList.contains('modal-overlay')) {
    closeGameSelector();
  }
});

document.addEventListener('DOMContentLoaded', () => {
  loadSelectedGames();
  setupIdleDetection();
});
