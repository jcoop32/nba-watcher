let activeGameId = null;
let selectedGames = []; // Array of game objects with {game_id, stream_url, streams, game_data}
let allGames = [];

// Set active game (for visual focus only)
function setActiveGame(gameId) {
  activeGameId = gameId;

  // Update visual indicators
  document.querySelectorAll('.game-container').forEach(container => {
    container.classList.remove('active');
  });

  const activeContainer = document.querySelector(`[data-game-id="${gameId}"]`);
  if (activeContainer) {
    activeContainer.classList.add('active');
  }

  // Save to localStorage
  localStorage.setItem('nba_watcher_active_game', gameId);
}

// Update the grid layout based on number of games
function updateGridLayout() {
  const grid = document.getElementById('gameGrid');
  const numGames = selectedGames.length;

  grid.className = `multi-game-grid grid-${numGames}`;
}

// Render all games
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

  // Remove empty state if it exists
  const emptyState = grid.querySelector('.empty-state');
  if (emptyState) {
    emptyState.remove();
  }

  // Check which games are already rendered
  const existingContainers = Array.from(
    grid.querySelectorAll('.game-container'),
  );
  const existingGameIds = existingContainers.map(c => c.dataset.gameId);
  const newGameIds = selectedGames.map(g => g.game_id);

  // Remove games that are no longer selected
  existingContainers.forEach(container => {
    if (!newGameIds.includes(container.dataset.gameId)) {
      container.remove();
    }
  });

  // Add new games only
  selectedGames.forEach((game, index) => {
    if (!existingGameIds.includes(game.game_id)) {
      const container = createGameContainer(game, index);
      grid.appendChild(container);
    } else {
      // Update stream sources for existing game if needed
      updateStreamSourceButtons(game);
    }
  });

  updateGridLayout();

  // Restore active game
  if (activeGameId) {
    const activeContainer = document.querySelector(
      `[data-game-id="${activeGameId}"]`,
    );
    if (activeContainer) {
      activeContainer.classList.add('active');
    }
  } else if (selectedGames.length > 0) {
    // Set first game as active by default
    setActiveGame(selectedGames[0].game_id);
  }
}

// Update stream source buttons for an existing game
function updateStreamSourceButtons(game) {
  const container = document.querySelector(`[data-game-id="${game.game_id}"]`);
  if (!container) return;

  const selector = container.querySelector('.stream-source-selector');
  if (!selector || !game.streams || game.streams.length === 0) return;

  // Rebuild stream source buttons
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

// Create a game container element
function createGameContainer(game, index) {
  const container = document.createElement('div');
  container.className = 'game-container';
  container.dataset.gameId = game.game_id;

  // Show add game button only if less than 4 games
  const showAddButton = selectedGames.length < 4;

  // Create stream source selector buttons
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

// Change stream source for a game
function changeStreamSource(gameId, streamIndex) {
  const game = selectedGames.find(g => g.game_id === gameId);
  if (!game || !game.streams || streamIndex >= game.streams.length) return;

  game.currentStreamIndex = streamIndex;
  game.stream_url = game.streams[streamIndex].url;

  // Update only the iframe for this game
  const container = document.querySelector(`[data-game-id="${gameId}"]`);
  if (container) {
    const iframe = container.querySelector('iframe');
    if (iframe) {
      iframe.src = game.stream_url;
    }

    // Update button states
    const buttons = container.querySelectorAll('.stream-source-btn');
    buttons.forEach((btn, idx) => {
      if (idx === streamIndex) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });
  }

  // Save to localStorage
  saveSelectedGames();
}

// Remove a game
function removeGame(gameId) {
  selectedGames = selectedGames.filter(g => g.game_id !== gameId);

  // If removed game was active, set new active game
  if (activeGameId === gameId) {
    activeGameId = selectedGames.length > 0 ? selectedGames[0].game_id : null;
  }

  renderGames();
  saveSelectedGames();
}

// Remove game from modal (updates both modal and main view)
function removeGameFromModal(gameId) {
  // Remove from selected games
  selectedGames = selectedGames.filter(g => g.game_id !== gameId);

  // If removed game was active, set new active game
  if (activeGameId === gameId) {
    activeGameId = selectedGames.length > 0 ? selectedGames[0].game_id : null;
  }

  // Update main view
  renderGames();
  saveSelectedGames();

  // Update modal button
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

// Replace a game with another
function replaceGame(gameId) {
  showGameSelector(gameId);
}

// Replace game with selected game
function replaceWithGame(oldGameId, newGameId) {
  // Find the game data for the new game
  const newGameData = allGames.find(g => g.id === newGameId);
  if (!newGameData) return;

  // Find index of old game
  const oldGameIndex = selectedGames.findIndex(g => g.game_id === oldGameId);
  if (oldGameIndex === -1) return;

  // Create new game object
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

  // Replace the old game
  selectedGames[oldGameIndex] = newGame;

  // If the replaced game was active, make the new game active
  if (activeGameId === oldGameId) {
    activeGameId = newGameId;
  }

  // Update UI
  renderGames();
  saveSelectedGames();

  // Close modal
  closeGameSelector();
}

// Show game selection modal
function showGameSelector(replacingGameId = null) {
  fetch('/api/games-today')
    .then(res => res.json())
    .then(games => {
      allGames = games;
      createGameSelectorModal(games, replacingGameId);
    })
    .catch(err => {
      console.error('Error fetching games:', err);
      alert('Failed to load games');
    });
}

// Create game selector modal
function createGameSelectorModal(games, replacingGameId = null) {
  // Remove existing modal if any
  const existingModal = document.getElementById('gameSelectionModal');
  if (existingModal) {
    existingModal.remove();
  }

  const modal = document.createElement('div');
  modal.id = 'gameSelectionModal';
  modal.className = 'modal-overlay';

  const selectedGameIds = selectedGames.map(g => g.game_id);
  const isReplaceMode = replacingGameId !== null;

  let gamesHTML = '';
  games.forEach(game => {
    const gameId = game.id;
    const isAdded = selectedGameIds.includes(gameId);
    const isBeingReplaced = gameId === replacingGameId;

    // Display game title or format from tricodes
    const displayTitle =
      game.title || `${game.away_tricode} @ ${game.home_tricode}`;

    // Format status
    let statusDisplay = game.status || 'UPCOMING';
    if (game.status === 'LIVE') {
      statusDisplay = '🔴 LIVE';
    }

    // In replace mode, show all games except the one being replaced
    if (isReplaceMode && isBeingReplaced) {
      return; // Skip the game being replaced
    }

    gamesHTML += `
            <div class="game-selection-item ${
              isAdded && !isReplaceMode ? 'selected' : ''
            }" data-game-id="${gameId}">
                <div class="game-info">
                    <div class="game-teams">
                        ${displayTitle}
                    </div>
                    <div class="game-time">${
                      game.game_start || ''
                    } • ${statusDisplay}</div>
                </div>
                <button class="add-game-btn ${
                  isAdded && !isReplaceMode ? 'added' : ''
                }"
                        onclick="${
                          isReplaceMode
                            ? `replaceWithGame('${replacingGameId}', '${gameId}')`
                            : isAdded
                            ? `removeGameFromModal('${gameId}')`
                            : `addGame('${gameId}')`
                        }">
                    ${
                      isReplaceMode
                        ? '↔ Replace'
                        : isAdded
                        ? '✓ Added'
                        : '+ Add'
                    }
                </button>
            </div>
        `;
  });

  const modalTitle = isReplaceMode ? 'Replace Game' : 'Add Games to Watch';

  modal.innerHTML = `
        <div class="modal-content">
            <h2>${modalTitle}</h2>
            <div class="game-selection-list">
                ${gamesHTML || '<p style="color: #666;">No games available</p>'}
            </div>
            <div class="modal-actions">
                <button class="modal-btn modal-btn-secondary" onclick="closeGameSelector()">Done</button>
            </div>
        </div>
    `;

  document.body.appendChild(modal);
}

// Add a game
function addGame(gameId) {
  // Check if already added
  if (selectedGames.some(g => g.game_id === gameId)) {
    return;
  }

  // Check max limit (4 games)
  if (selectedGames.length >= 4) {
    alert('Maximum 4 games can be displayed at once');
    return;
  }

  // Find game data
  const gameData = allGames.find(g => g.id === gameId);
  if (!gameData) return;

  // Get streams for this game - convert from array of URLs to array of objects
  const streamUrls = gameData.streams || [];
  const streams = streamUrls.map((url, index) => ({
    name: `Stream ${index + 1}`,
    url: url,
  }));

  const defaultStreamUrl = streams.length > 0 ? streams[0].url : '';

  // Add to selected games
  selectedGames.push({
    game_id: gameId,
    stream_url: defaultStreamUrl,
    streams: streams,
    currentStreamIndex: 0,
    game_data: gameData,
  });

  // Update UI
  renderGames();
  saveSelectedGames();

  // Update button in modal
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

// Close game selector
function closeGameSelector() {
  const modal = document.getElementById('gameSelectionModal');
  if (modal) {
    modal.remove();
  }
}

// Save selected games to localStorage (removed - no longer saving)
function saveSelectedGames() {
  // No longer saving to localStorage - fresh start each time
  return;
}

// Load selected games from localStorage (removed - always start fresh)
function loadSelectedGames() {
  // No longer loading from localStorage - always start with empty state
  return;
}

// Keyboard shortcuts
document.addEventListener('keydown', e => {
  // Don't trigger if user is typing in an input
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

// Close modal on overlay click
document.addEventListener('click', e => {
  if (e.target.classList.contains('modal-overlay')) {
    closeGameSelector();
  }
});

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
  loadSelectedGames();
});
