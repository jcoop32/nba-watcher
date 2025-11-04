function updateScoreboard() {
  // Fetch data from the new Flask API endpoint
  fetch('/api/scoreboard')
    .then(response => {
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      return response.json();
    })
    .then(data => {
      // 'data' is the JSON object returned by /api/scoreboard, keyed by team code (e.g., 'LALBOS')
      for (const teamsKey in data) {
        if (data.hasOwnProperty(teamsKey)) {
          const gameData = data[teamsKey];
          // Find the corresponding game item on the page using the data-teams attribute
          const gameItem = document.querySelector(
            `.game-item[data-teams="${teamsKey}"]`,
          );

          if (gameItem) {
            const scoreText = gameItem.querySelector('.live-score-text');
            const statusElement = gameItem.querySelector(
              '.game-details[data-status]',
            );
            // Target the last event element
            const lastEventElement = gameItem.querySelector('.last-event-text');

            if (gameData.game_started_yet) {
              // Update the score if the game is live or finished
              if (scoreText) {
                scoreText.textContent = `${gameData.away_score} - ${gameData.home_score}`;
              }

              // Update the game status/clock
              statusElement.textContent = `| ${gameData.game_status}`;

              // Update the last game event text
              if (lastEventElement) {
                lastEventElement.textContent = `Last Event: ${gameData.last_game_event}`;
              }
            } else {
              // Update the status for scheduled games (in case time changes)
              statusElement.textContent = `| ${gameData.today_or_tomorrow} ${gameData.game_status}`;
            }
          }
        }
      }
    })
    .catch(error => {
      console.error('Error fetching scoreboard data:', error);
    });
}

// Function to initialize button gradients
function initializeButtonGradients() {
  // List of light hex colors that need black text for contrast
  const LIGHT_COLORS = ['#FFFFFF', '#C4CED4'];

  document.querySelectorAll('.game-item').forEach(gameItem => {
    const awayColor = gameItem.dataset.colorAway;
    const homeColor = gameItem.dataset.colorHome;
    const button = gameItem.querySelector('.watch-link');

    if (button && awayColor && homeColor) {
      // Apply linear gradient from away color to home color
      button.style.background = `linear-gradient(90deg, ${awayColor}, ${homeColor})`;
      // Apply a consistent box shadow for visual depth
      button.style.boxShadow = `0 6px 15px rgba(0, 0, 0, 0.4)`;

      if (
        LIGHT_COLORS.includes(awayColor) ||
        LIGHT_COLORS.includes(homeColor)
      ) {
        button.style.color = '#1a1a1a';
      } else {
        button.style.color = '#FFFFFF';
      }
    } else {
    }
  });
}

// Run the update function immediately on load
updateScoreboard();

// Initialize gradients immediately after scores/status update
initializeButtonGradients();

// Set an interval to poll the server every 20 seconds (20000 milliseconds)
setInterval(updateScoreboard, 20000);
