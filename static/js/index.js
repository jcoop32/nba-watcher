let multiviewSelections = [];
const maxSelections = 4;
let launchButton = null;
let pollingIntervalId = null;

function initializeMultiview() {
  launchButton = document.getElementById('launch-multiview-btn');
  if (!launchButton) return;

  document.querySelectorAll('.multiview-link').forEach(button => {
    button.addEventListener('click', () => toggleMultiviewSelection(button));
  });

  launchButton.addEventListener('click', e => {
    e.preventDefault();
    launchMultiview();
  });
}

function toggleMultiviewSelection(button) {
  const gameId = button.dataset.gameId;
  const index = multiviewSelections.indexOf(gameId);

  if (index > -1) {
    multiviewSelections.splice(index, 1);
    button.classList.remove('selected');
    button.textContent = '+ Multiview';
  } else {
    if (multiviewSelections.length >= maxSelections) {
      alert(`You can only select up to ${maxSelections} games for multiview.`);
      return;
    }
    multiviewSelections.push(gameId);
    button.classList.add('selected');
    button.textContent = '✓ Added';
  }

  updateLaunchButton();
}

function updateLaunchButton() {
  const count = multiviewSelections.length;
  if (count > 0) {
    launchButton.classList.remove('hidden');
    launchButton.textContent = `Launch Multiview (${count})`;
  } else {
    launchButton.classList.add('hidden');
  }
}

function launchMultiview() {
  if (multiviewSelections.length === 0) return;

  const gameIds = multiviewSelections.join(',');
  const url = `/multiview?games=${gameIds}`;

  window.open(url, '_blank');
}

function updateScoreboard() {
  fetch('/api/scoreboard')
    .then(response => {
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      return response.json();
    })
    .then(data => {
      for (const teamsKey in data) {
        if (data.hasOwnProperty(teamsKey)) {
          const gameData = data[teamsKey];
          const gameItem = document.querySelector(
            `.game-item[data-teams="${teamsKey}"]`,
          );

          if (gameItem) {
            const scoreText = gameItem.querySelector('.live-score-text');
            const statusElement = gameItem.querySelector(
              '.game-details[data-status]',
            );

            if (gameData.game_started_yet) {
              if (scoreText) {
                scoreText.textContent = `${gameData.away_score} - ${gameData.home_score}`;
              }

              statusElement.textContent = `| ${gameData.game_status}`;
            }
          }
        }
      }
    })
    .catch(error => {
      console.error('Error fetching scoreboard data:', error);
    });
}

function initializeButtonGradients() {
  const LIGHT_COLORS = ['#FFFFFF', '#C4CED4'];

  document.querySelectorAll('.game-item').forEach(gameItem => {
    const awayColor = gameItem.dataset.colorAway;
    const homeColor = gameItem.dataset.colorHome;
    const button = gameItem.querySelector('.watch-link');

    if (button && awayColor && homeColor) {
      button.style.background = `linear-gradient(90deg, ${awayColor}, ${homeColor})`;
      button.style.boxShadow = `0 6px 15px rgba(0, 0, 0, 0.4)`;

      if (
        LIGHT_COLORS.includes(awayColor) ||
        LIGHT_COLORS.includes(homeColor)
      ) {
        button.style.color = '#1a1a1a';
      } else {
        button.style.color = '#FFFFFF';
      }
    }
  });
}

// --- NEW: Polling Gatekeeper Logic ---

function runUpdateCycle() {
  updateScoreboard();
}

function startPollingManager() {
  const MINUTES_BEFORE = 10;
  const now = Math.floor(Date.now() / 1000);
  const targetTime = EARLIEST_GAME_TS - MINUTES_BEFORE * 60;

  console.log(`[Polling Manager] Earliest Game TS: ${EARLIEST_GAME_TS}`);
  console.log(`[Polling Manager] Current TS: ${now}`);
  console.log(`[Polling Manager] Target Start TS: ${targetTime}`);

  // --- PERFORMANCE OPTIMIZATION START ---

  const conditionalUpdate = () => {
    if (document.visibilityState === 'visible') {
      runUpdateCycle();
    }
  };

  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') {
      console.log('👁️ Tab visible again. Refreshing scoreboard...');
      runUpdateCycle();
    }
  });

  // --- PERFORMANCE OPTIMIZATION END ---

  if (EARLIEST_GAME_TS === 0 || now >= targetTime) {
    console.log(
      '✅ Game time imminent or active. Starting polling immediately.',
    );
    runUpdateCycle();
    pollingIntervalId = setInterval(conditionalUpdate, 20000);
  } else {
    const secondsToWait = targetTime - now;

    setTimeout(() => {
      runUpdateCycle();
      pollingIntervalId = setInterval(conditionalUpdate, 20000);
    }, secondsToWait * 1000);
  }
}

// --- Initialization ---

document.addEventListener('DOMContentLoaded', () => {
  initializeButtonGradients();
  initializeMultiview();

  startPollingManager();
});
