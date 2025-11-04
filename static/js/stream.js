// --- Existing Overlay/Protection Logic ---
var popupBlocked = false;

window.open = function () {
  if (!popupBlocked) {
    console.log('Popup blocked by protection script');
    popupBlocked = true;
  }
  return null;
};

function unlockStream() {
  document.getElementById('overlay').classList.add('hidden');
  document.getElementById('full-screen-iframe').classList.add('unlocked');

  // Temporarily engage a click absorber to catch the first popup-triggering click
  const absorber = document.getElementById('click-absorber');
  absorber.style.display = 'block';

  // After 1 second, remove the click absorber, allowing normal interaction.
  setTimeout(() => {
    absorber.style.display = 'none';
  }, 1000);
}

document.addEventListener(
  'click',
  function (e) {
    if (e.target.tagName === 'A' && e.target.target === '_blank') {
      if (!e.target.href.includes('lotusgamehd.xyz')) {
        e.preventDefault();
        console.log('External link blocked:', e.target.href);
        return false;
      }
    }
  },
  true,
);

// --- Box Score & Polling Logic ---

// Global variable to hold the polling interval ID
let boxScoreIntervalId = null;

// Function to handle tab switching
function switchTab(teamTricode) {
  document.querySelectorAll('.tab-button').forEach(button => {
    button.classList.remove('active');
  });
  document
    .querySelector(`.tab-button[data-team="${teamTricode}"]`)
    .classList.add('active');

  document.querySelectorAll('.tab-content').forEach(content => {
    content.classList.remove('active');
  });
  document.getElementById(`tab-content-${teamTricode}`).classList.add('active');
}

// Function to generate the HTML table for a team's box score
function generateBoxScoreHTML(teamTricode, teamData) {
  let html = `
        <div id="tab-content-${teamTricode}" class="tab-content">
            <table class="boxscore-table">
                <thead>
                    <tr>
                        <th>PLAYER</th>
                        <th>MIN</th>
                        <th>PTS</th>
                        <th>REB</th>
                        <th>AST</th>
                        <th>FG</th>
                        <th>3PT</th>
                        <th>STL</th>
                        <th>BLK</th>
                        <th>TO</th>
                    </tr>
                </thead>
                <tbody>
    `;

  // Sort players by minutes (MIN) descending
  const players = teamData.players.sort((a, b) => {
    return (parseFloat(b.min) || 0) - (parseFloat(a.min) || 0);
  });

  players.forEach(p => {
    let playerName = p.name;
    let rowClass = ''; // Initialize row class

    // 1. Add class if on court (NEW LOGIC)
    if (p.is_oncourt) {
      rowClass = 'oncourt';
    }

    // 2. Wrap in <strong> if a starter (UNMODIFIED LOGIC)
    if (p.is_starter) {
      playerName = `<strong>*${playerName}</strong>`;
    }

    // The <tr> now uses the dynamic class and the player name without the asterisk
    html += `
            <tr class="${rowClass}">
                <td>${playerName}</td>
                <td>${p.min}</td>
                <td>${p.pts}</td>
                <td>${p.reb}</td>
                <td>${p.ast}</td>
                <td>${p.fgm_fga}</td>
                <td>${p.fg3m_fg3a}</td>
                <td>${p.stl}</td>
                <td>${p.blk}</td>
                <td>${p.to}</td>
            </tr>
        `;
  });

  html += `
                </tbody>
            </table>
        </div>
    `;
  return html;
}

// Main polling function
function fetchAndUpdateBoxScore() {
  const liveStatusElement = document.getElementById('live-status');

  if (!GAME_ID || GAME_ID === 'None' || GAME_ID === 'null') {
    liveStatusElement.textContent = 'Game has not started.';
    return;
  }

  // Fetch box score data from the new Flask API endpoint
  fetch(`/api/boxscore/${GAME_ID}`)
    .then(response => {
      if (!response.ok) {
        throw new Error(
          'Server error when fetching data. Status: ' + response.status,
        );
      }
      return response.json();
    })
    .then(data => {
      // Check for API-level error message returned by the Python function
      if (data.error) {
        throw new Error(data.error);
      }

      // Successfully retrieved and processed data
      const tabNav = document.querySelector('.tab-nav');
      const tabContentContainer = document.getElementById(
        'tab-content-container',
      );

      liveStatusElement.textContent = 'Box Score';

      // If the structure is empty (first load), build the tabs and content
      if (tabNav.children.length === 0) {
        tabNav.innerHTML = '';
        tabContentContainer.innerHTML = '';

        let firstTeamTricode = null;

        // Build Tabs and Content
        for (const teamTricode in data) {
          if (data.hasOwnProperty(teamTricode) && data[teamTricode].players) {
            if (!firstTeamTricode) {
              firstTeamTricode = teamTricode;
            }

            // 1. Create Tab Button
            const button = document.createElement('button');
            button.className = 'tab-button';
            button.setAttribute('data-team', teamTricode);
            button.textContent = teamTricode;
            button.onclick = () => switchTab(teamTricode);
            tabNav.appendChild(button);

            // 2. Generate and Insert Tab Content
            const htmlContent = generateBoxScoreHTML(
              teamTricode,
              data[teamTricode],
            );
            tabContentContainer.insertAdjacentHTML('beforeend', htmlContent);
          }
        }

        // Activate the first tab after building
        if (firstTeamTricode) {
          switchTab(firstTeamTricode);
        }
      } else {
        // If tabs already exist, just update the inner HTML of the tables (more efficient)
        for (const teamTricode in data) {
          if (data.hasOwnProperty(teamTricode) && data[teamTricode].players) {
            const newHtmlContent = generateBoxScoreHTML(
              teamTricode,
              data[teamTricode],
            );
            const existingDiv = document.getElementById(
              `tab-content-${teamTricode}`,
            );
            // Extract only the inner table HTML for update
            const newTableHTML = newHtmlContent.match(/<table.*?<\/table>/s)[0];
            if (existingDiv) {
              existingDiv.innerHTML = newTableHTML;
            }
          }
        }
      }
    })
    .catch(error => {
      console.error('Error fetching box score:', error);
      liveStatusElement.textContent = 'Error with Scoreboard API';
    });
}

// Check if GAME_ID exists before starting polling
if (typeof GAME_ID !== 'undefined') {
  fetchAndUpdateBoxScore();
  // Start polling indefinitely (or until the game ends on its own)
  boxScoreIntervalId = setInterval(fetchAndUpdateBoxScore, 10000);
} else {
  // This case should rarely happen if the JS link works, but is here as a fallback
  document.getElementById('live-status').textContent = 'Initialization Error.';
}
