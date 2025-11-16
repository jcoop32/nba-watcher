let activeGameId = null;
let selectedGames = [];
let allGames = [];

// Set active game (for audio focus)
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
    return;
  }

  grid.innerHTML = '';

  selectedGames.forEach((game, index) => {
    const container = createGameContainer(game, index);
    grid.appendChild(container);
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

// Create a game container element
function createGameContainer(game, index) {
  const container = document.createElement('div');
  container.className = 'game-container';
  container.dataset.gameId = game.game_id;
  container.onclick = () => setActiveGame(game.game_id);

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
        <div class="game-controls">
            <button class="game-control-btn" onclick="event.stopPropagation(); removeGame('${game.game_id}')" title="Remove">✕</button>
        </div>

        <div class="audio-indicator">🔊 Audio</div>

        <div class="stream-container">
            <iframe src="${game.stream_url}" allowfullscreen></iframe>
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

  // Re-render games
  renderGames();

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

// Show game selection modal
function showGameSelector() {
  fetch('/api/games-today')
    .then(res => res.json())
    .then(games => {
      allGames = games;
      createGameSelectorModal(games);
    })
    .catch(err => {
      console.error('Error fetching games:', err);
      alert('Failed to load games');
    });
}

// Create game selector modal
function createGameSelectorModal(games) {
  // Remove existing modal if any
  const existingModal = document.getElementById('gameSelectionModal');
  if (existingModal) {
    existingModal.remove();
  }

  const modal = document.createElement('div');
  modal.id = 'gameSelectionModal';
  modal.className = 'modal-overlay';

  const selectedGameIds = selectedGames.map(g => g.game_id);

  let gamesHTML = '';
  games.forEach(game => {
    const gameId = game.id;
    const isAdded = selectedGameIds.includes(gameId);

    // Display game title or format from tricodes
    const displayTitle =
      game.title || `${game.away_tricode} @ ${game.home_tricode}`;

    // Format status
    let statusDisplay = game.status || 'UPCOMING';
    if (game.status === 'LIVE') {
      statusDisplay = '🔴 LIVE';
    }

    gamesHTML += `
            <div class="game-selection-item ${
              isAdded ? 'selected' : ''
            }" data-game-id="${gameId}">
                <div class="game-info">
                    <div class="game-teams">
                        ${displayTitle}
                    </div>
                    <div class="game-time">${
                      game.game_start || ''
                    } • ${statusDisplay}</div>
                </div>
                <button class="add-game-btn ${isAdded ? 'added' : ''}"
                        onclick="${
                          isAdded
                            ? `removeGameFromModal('${gameId}')`
                            : `addGame('${gameId}')`
                        }">
                    ${isAdded ? '✓ Added' : '+ Add'}
                </button>
            </div>
        `;
  });

  modal.innerHTML = `
        <div class="modal-content">
            <h2>Add Games to Watch</h2>
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

// Save selected games to localStorage
function saveSelectedGames() {
  const dataToSave = selectedGames.map(g => ({
    game_id: g.game_id,
    currentStreamIndex: g.currentStreamIndex,
  }));
  localStorage.setItem(
    'nba_watcher_selected_games',
    JSON.stringify(dataToSave),
  );
}

// Load selected games from localStorage
function loadSelectedGames() {
  const saved = localStorage.getItem('nba_watcher_selected_games');
  if (!saved) return;

  try {
    const savedGames = JSON.parse(saved);

    // Fetch current games and restore selection
    fetch('/api/games-today')
      .then(res => res.json())
      .then(games => {
        allGames = games;

        savedGames.forEach(savedGame => {
          const gameData = games.find(g => g.id === savedGame.game_id);
          if (gameData) {
            const streamUrls = gameData.streams || [];
            const streams = streamUrls.map((url, index) => ({
              name: `Stream ${index + 1}`,
              url: url,
            }));

            const streamIndex = savedGame.currentStreamIndex || 0;
            const streamUrl =
              streams.length > streamIndex ? streams[streamIndex].url : '';

            selectedGames.push({
              game_id: savedGame.game_id,
              stream_url: streamUrl,
              streams: streams,
              currentStreamIndex: streamIndex,
              game_data: gameData,
            });
          }
        });

        renderGames();

        // Restore active game
        const savedActiveGame = localStorage.getItem('nba_watcher_active_game');
        if (
          savedActiveGame &&
          selectedGames.some(g => g.game_id === savedActiveGame)
        ) {
          setActiveGame(savedActiveGame);
        }
      })
      .catch(err => console.error('Error loading games:', err));
  } catch (e) {
    console.error('Error parsing saved games:', e);
  }
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
