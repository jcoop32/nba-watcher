const streamIframe = document.getElementById('full-screen-iframe');
const clickAbsorber = document.getElementById('click-absorber');
let hasForwardedClick = false;

// --- Set stream source ---
function setStream(url, buttonElement) {
  streamIframe.src = url;

  // Highlight active button
  document
    .querySelectorAll('.stream-button')
    .forEach(btn => btn.classList.remove('active'));
  if (buttonElement) buttonElement.classList.add('active');

  // Reset click absorber for new stream
  hasForwardedClick = false;
  clickAbsorber.style.display = 'block';
}

// --- Unlock + Auto-load first stream ---
function unlockStream() {
  document.getElementById('overlay').classList.add('hidden');
  streamIframe.classList.add('unlocked');

  // Auto-load first stream
  const firstButton = document.querySelector('.stream-button');
  if (firstButton) {
    const firstUrl = firstButton.dataset.url;
    setStream(firstUrl, firstButton);
  }
}

// --- Click Absorber: Forward ONE real click to iframe ---
clickAbsorber.addEventListener('click', function forwardClick(e) {
  if (hasForwardedClick) return;
  hasForwardedClick = true;

  // Remove absorber
  clickAbsorber.style.display = 'none';

  // Forward click to center of iframe
  const rect = streamIframe.getBoundingClientRect();
  const clickX = rect.left + rect.width / 2;
  const clickY = rect.top + rect.height / 2;

  const clickEvent = new MouseEvent('click', {
    view: window,
    bubbles: true,
    cancelable: true,
    clientX: clickX,
    clientY: clickY,
  });

  streamIframe.contentWindow.dispatchEvent(clickEvent);
});

// --- Block all popups (extra safety) ---
let popupBlocked = false;
window.open = function () {
  if (!popupBlocked) {
    console.log('Popup blocked by protection script');
    popupBlocked = true;
  }
  return null;
};

// --- Block external _blank links (except trusted) ---
document.addEventListener(
  'click',
  function (e) {
    if (e.target.tagName === 'A' && e.target.target === '_blank') {
      const href = e.target.href;
      if (
        !href.includes('lotusgamehd.xyz') &&
        !href.includes('embedsports.top')
      ) {
        e.preventDefault();
        console.log('External link blocked:', href);
      }
    }
  },
  true,
);

// --- Box Score & Polling (unchanged) ---
let boxScoreIntervalId = null;

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

function generateBoxScoreHTML(teamTricode, teamData) {
  let html = `
    <div id="tab-content-${teamTricode}" class="tab-content">
      <table class="boxscore-table">
        <thead>
          <tr>
            <th>PLAYER</th><th>MIN</th><th>PTS</th><th>REB</th><th>AST</th>
            <th>FG</th><th>3PT</th><th>STL</th><th>BLK</th><th>TO</th>
          </tr>
        </thead>
        <tbody>
  `;

  const players = teamData.players.sort(
    (a, b) => (parseFloat(b.min) || 0) - (parseFloat(a.min) || 0),
  );

  players.forEach(p => {
    let playerName = p.name;
    let rowClass = p.is_oncourt ? 'oncourt' : '';
    if (p.is_starter) playerName = `<strong>*${playerName}</strong>`;

    html += `
      <tr class="${rowClass}">
        <td>${playerName}</td>
        <td>${p.min}</td><td>${p.pts}</td><td>${p.reb}</td><td>${p.ast}</td>
        <td>${p.fgm_fga}</td><td>${p.fg3m_fg3a}</td>
        <td>${p.stl}</td><td>${p.blk}</td><td>${p.to}</td>
      </tr>
    `;
  });

  html += `</tbody></table></div>`;
  return html;
}

function fetchAndUpdateBoxScore() {
  const liveStatusElement = document.getElementById('live-status');
  if (!GAME_ID || GAME_ID === 'None' || GAME_ID === 'null') {
    liveStatusElement.textContent = 'Game has not started.';
    return;
  }

  fetch(`/api/boxscore/${GAME_ID}`)
    .then(r => {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    })
    .then(data => {
      if (data.error) throw new Error(data.error);

      const tabNav = document.querySelector('.tab-nav');
      const tabContentContainer = document.getElementById(
        'tab-content-container',
      );
      liveStatusElement.textContent = 'Box Score';

      if (tabNav.children.length === 0) {
        tabNav.innerHTML = '';
        tabContentContainer.innerHTML = '';
        let firstTeam = null;

        for (const team in data) {
          if (data[team].players) {
            if (!firstTeam) firstTeam = team;

            const btn = document.createElement('button');
            btn.className = 'tab-button';
            btn.dataset.team = team;
            btn.textContent = team;
            btn.onclick = () => switchTab(team);
            tabNav.appendChild(btn);

            const html = generateBoxScoreHTML(team, data[team]);
            tabContentContainer.insertAdjacentHTML('beforeend', html);
          }
        }
        if (firstTeam) switchTab(firstTeam);
      } else {
        for (const team in data) {
          if (data[team].players) {
            const newHtml = generateBoxScoreHTML(team, data[team]);
            const tableMatch = newHtml.match(/<table.*?<\/table>/s);
            if (tableMatch) {
              const div = document.getElementById(`tab-content-${team}`);
              if (div) div.innerHTML = tableMatch[0];
            }
          }
        }
      }
    })
    .catch(err => {
      console.error('Box score error:', err);
      liveStatusElement.textContent = 'Game has not Started (or API error)';
    });
}

// Start polling
if (typeof GAME_ID !== 'undefined') {
  // Only start polling if the game has actually started
  if (GAME_STARTED) {
    fetchAndUpdateBoxScore();
    boxScoreIntervalId = setInterval(fetchAndUpdateBoxScore, 10000);
  } else {
    // Optional: Update text to let user know why there are no stats
    document.getElementById('live-status').textContent =
      'Game has not started.';
  }
} else {
  document.getElementById('live-status').textContent = 'Initialization Error.';
}
