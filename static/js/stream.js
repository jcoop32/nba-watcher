const streamIframe = document.getElementById('full-screen-iframe');
const clickAbsorber = document.getElementById('click-absorber');
let hasForwardedClick = false;
let momentumChart = null;
let globalTooltip = null;
const playerStatsCache = {};

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

// --- Click Absorber ---
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

// --- Block all popups ---
let popupBlocked = false;
window.open = function () {
  if (!popupBlocked) {
    console.log('Popup blocked by protection script');
    popupBlocked = true;
  }
  return null;
};

// --- Block external _blank links ---
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

// --- Box Score & Polling ---
let boxScoreIntervalId = null;

function switchTab(teamTricode) {
  document.querySelectorAll('.tab-button').forEach(button => {
    button.classList.remove('active');
  });

  const activeBtn = document.querySelector(
    `.tab-button[data-team="${teamTricode}"]`,
  );
  if (activeBtn) activeBtn.classList.add('active');

  document.querySelectorAll('.tab-content').forEach(content => {
    content.classList.remove('active');
  });

  const activeContent = document.getElementById(`tab-content-${teamTricode}`);
  if (activeContent) activeContent.classList.add('active');
}

// --- Initialize Tabs from TEAMS constant (e.g. "BOSLAL") ---
function initStaticTabs() {
  const tabNav = document.querySelector('.tab-nav');
  if (tabNav.children.length > 0) return;

  // Use explicit codes if available, otherwise fallback to slicing TEAMS
  let awayTeam =
    typeof AWAY_CODE !== 'undefined' && AWAY_CODE
      ? AWAY_CODE
      : TEAMS.substring(0, 3);
  let homeTeam =
    typeof HOME_CODE !== 'undefined' && HOME_CODE
      ? HOME_CODE
      : TEAMS.substring(3, 6);

  if (awayTeam && homeTeam) {
    const teams = [awayTeam, homeTeam];
    const tabContentContainer = document.getElementById(
      'tab-content-container',
    );

    tabNav.innerHTML = '';
    tabContentContainer.innerHTML = '';

    teams.forEach((team, index) => {
      const btn = document.createElement('button');
      btn.className = `tab-button ${index === 0 ? 'active' : ''}`;
      btn.dataset.team = team;
      btn.textContent = team;
      btn.onclick = () => switchTab(team);
      tabNav.appendChild(btn);

      const content = document.createElement('div');
      content.id = `tab-content-${team}`;
      content.className = `tab-content ${index === 0 ? 'active' : ''}`;
      content.innerHTML = `
                <div style="padding:40px; text-align:center; color:#71717a;">
                    <h3 style="color: #fff;">${team}</h3>
                    <p>Waiting for tip-off...</p>
                </div>
            `;
      tabContentContainer.appendChild(content);
    });
  }
}

// --- Global Tooltip Initialization ---
function initGlobalTooltip() {
  if (document.getElementById('global-player-tooltip')) return;

  globalTooltip = document.createElement('div');
  globalTooltip.id = 'global-player-tooltip';
  globalTooltip.className = 'player-card-tooltip';
  document.body.appendChild(globalTooltip);
}

// --- Player Card Hover Logic ---
function showPlayerCard(cell) {
  const playerId = cell.dataset.id;
  const playerName = cell.dataset.name;
  const jersey = cell.dataset.jersey;

  if (!globalTooltip) initGlobalTooltip();

  if (!playerId || playerId === '0') return;

  // 1. Reset and Show (Transparent) to measure
  globalTooltip.style.opacity = '0';
  globalTooltip.style.display = 'block';

  // Helper to safely position the card
  const positionCard = () => {
    const tooltipWidth = globalTooltip.offsetWidth;
    const tooltipHeight = globalTooltip.offsetHeight;
    const windowHeight = window.innerHeight;
    const rect = cell.getBoundingClientRect();

    // --- HORIZONTAL: LEFT SIDE PREFERENCE ---
    // Position to the left of the name (over the stream)
    let leftPos = rect.left - tooltipWidth - 10;

    // Safety check: If it goes off the left edge, flip to right
    if (leftPos < 10) {
      leftPos = rect.right + 10;
    }

    // --- VERTICAL: BOUNDARY PROTECTION ---
    // Start centered relative to the row
    let topPos = rect.top + rect.height / 2 - tooltipHeight / 2;

    // Bottom Check: If it hits the bottom, pin it to the bottom margin
    if (topPos + tooltipHeight > windowHeight - 10) {
      topPos = windowHeight - tooltipHeight - 10;
    }

    // Top Check: If it hits the top, pin it to the top margin
    if (topPos < 10) {
      topPos = 10;
    }

    globalTooltip.style.left = `${leftPos}px`;
    globalTooltip.style.top = `${topPos}px`;
  };

  // Initial Position (for "Loading..." state)
  positionCard();
  globalTooltip.style.opacity = '1';
  globalTooltip.classList.add('visible');

  // Check cache
  if (playerStatsCache[playerId]) {
    renderTooltipContent(
      globalTooltip,
      playerName,
      jersey,
      playerId,
      playerStatsCache[playerId],
    );
    // CRITICAL: Re-position immediately because content size changed!
    positionCard();
    return;
  }

  // Loading State
  globalTooltip.innerHTML =
    '<div style="padding:10px; color:#a1a1aa; font-size:0.8rem;">Loading Stats...</div>';

  fetch(`/api/player-card/${playerId}`)
    .then(r => r.json())
    .then(data => {
      playerStatsCache[playerId] = data;
      renderTooltipContent(globalTooltip, playerName, jersey, playerId, data);

      // CRITICAL: Re-position again after new stats render
      positionCard();
    })
    .catch(err => {
      console.error(err);
      globalTooltip.innerHTML =
        '<div style="padding:10px; color:#ef4444; font-size:0.8rem;">Stats Unavailable</div>';
    });
}

function hidePlayerCard(cell) {
  if (globalTooltip) {
    // 1. Remove the CSS animation class
    globalTooltip.classList.remove('visible');

    // 2. CRITICAL FIX: Manually reset the display property.
    // Because showPlayerCard sets 'display: block' inline, we must override it here.
    globalTooltip.style.display = 'none';
  }
}

function renderTooltipContent(container, name, jersey, id, stats) {
  if (!stats || Object.keys(stats).length === 0) {
    container.innerHTML =
      '<p style="color: #a1a1aa; font-size: 0.8rem;">No season stats available</p>';
    return;
  }

  const imgUrl = `https://cdn.nba.com/headshots/nba/latest/1040x760/${id}.png`;
  const gamesPlayed = stats.gp || 0;

  container.innerHTML = `
    <div class="card-header">
      <img src="${imgUrl}" class="card-headshot" onerror="this.src='https://cdn.nba.com/logos/nba/nba-logoman-75-plus/primary/L/logo.svg'">
      <div class="card-info">
        <h3>${name}</h3>
        <span>#${jersey} • 25-26 Stats • GP: ${gamesPlayed}</span>
      </div>
    </div>
    <div class="card-stats-grid">
      <div class="stat-item"><span class="stat-label">PPG</span><span class="stat-value">${stats.pts}</span></div>
      <div class="stat-item"><span class="stat-label">RPG</span><span class="stat-value">${stats.reb}</span></div>
      <div class="stat-item"><span class="stat-label">APG</span><span class="stat-value">${stats.ast}</span></div>

      <div class="stat-item"><span class="stat-label">FG%</span><span class="stat-value">${stats.fg_pct}%</span></div>
      <div class="stat-item"><span class="stat-label">3P%</span><span class="stat-value">${stats.fg3_pct}%</span></div>
      <div class="stat-item"><span class="stat-label">3PA</span><span class="stat-value">${stats.fg3a}</span></div>

      <div class="stat-item"><span class="stat-label">FT%</span><span class="stat-value">${stats.ft_pct}%</span></div>
      <div class="stat-item"><span class="stat-label">STL</span><span class="stat-value">${stats.stl}</span></div>
      <div class="stat-item"><span class="stat-label">BLK</span><span class="stat-value">${stats.blk}</span></div>
    </div>
  `;
}

// --- HTML Generation (Updated) ---
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
        <td class="player-name-cell"
            data-id="${p.id}"
            data-name="${p.name}"
            data-jersey="${p.jersey}"
            onmouseenter="showPlayerCard(this)"
            onmouseleave="hidePlayerCard(this)">
            ${playerName}
        </td>
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
      liveStatusElement.textContent = 'Box Score';

      if (tabNav.children.length === 0) {
        // Tabs should be handled by initStaticTabs
      }

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
    })
    .catch(err => {
      console.error('Box score error:', err);
      if (liveStatusElement.textContent !== 'Game has not started.') {
        liveStatusElement.textContent = 'Live Data Pending...';
      }
    });
}

// --- Momentum Chart Logic ---

function hexToRgba(hex, alpha) {
  let c;
  if (/^#([A-Fa-f0-9]{3}){1,2}$/.test(hex)) {
    c = hex.substring(1).split('');
    if (c.length == 3) {
      c = [c[0], c[0], c[1], c[1], c[2], c[2]];
    }
    c = '0x' + c.join('');
    return (
      'rgba(' +
      [(c >> 16) & 255, (c >> 8) & 255, c & 255].join(',') +
      ',' +
      alpha +
      ')'
    );
  }
  return `rgba(161, 161, 170, ${alpha})`;
}

function getZeroLineGradient(context, colorTop, colorBottom, isFill) {
  const chart = context.chart;
  const { ctx, chartArea, scales } = chart;
  if (!chartArea) return null;

  const yScale = scales.y;

  // Get the pixel position of value 0
  const zeroPixel = yScale.getPixelForValue(0);
  const top = chartArea.top;
  const bottom = chartArea.bottom;

  let zeroRatio = (zeroPixel - top) / (bottom - top);
  zeroRatio = Math.min(Math.max(zeroRatio, 0), 1);

  const gradient = ctx.createLinearGradient(0, top, 0, bottom);

  const c1 = isFill ? hexToRgba(colorTop, 0.5) : colorTop;
  const c2 = isFill ? hexToRgba(colorBottom, 0.5) : colorBottom;

  gradient.addColorStop(0, c1);
  gradient.addColorStop(zeroRatio, c1);
  gradient.addColorStop(zeroRatio, c2);
  gradient.addColorStop(1, c2);

  return gradient;
}

function initMomentumChart() {
  const canvas = document.getElementById('momentumChart');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');

  // Use the explicit variables
  let homeName = typeof HOME_CODE !== 'undefined' ? HOME_CODE : 'Home';
  let awayName = typeof AWAY_CODE !== 'undefined' ? AWAY_CODE : 'Away';

  momentumChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: [],
      datasets: [
        {
          label: 'Score Differential',
          data: [],
          borderWidth: 2,
          pointRadius: 0,
          fill: true,
          borderColor: context => {
            return getZeroLineGradient(context, HOME_COLOR, AWAY_COLOR, false);
          },
          backgroundColor: context => {
            return getZeroLineGradient(context, HOME_COLOR, AWAY_COLOR, true);
          },
          tension: 0.4,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          mode: 'index',
          intersect: false,
          callbacks: {
            label: function (context) {
              let label = context.dataset.label || '';
              if (label) label += ': ';
              const val = context.parsed.y;

              if (val > 0) return `${homeName} +${val}`;
              if (val < 0) return `${awayName} +${Math.abs(val)}`;
              return 'Tied';
            },
          },
        },
      },
      scales: {
        x: { display: false },
        y: {
          grid: { color: '#27272a' },
          ticks: { display: true, color: '#71717a', font: { size: 10 } },
          suggestedMin: -10,
          suggestedMax: 10,
        },
      },
    },
  });
}

function updateMomentum() {
  if (!GAME_ID || GAME_ID === 'None') return;

  fetch(`/api/momentum/${GAME_ID}`)
    .then(r => r.json())
    .then(data => {
      if (!momentumChart || data.length === 0) return;

      const labels = data.map(d => d.label);
      const values = data.map(d => d.value);

      momentumChart.data.labels = labels;
      momentumChart.data.datasets[0].data = values;

      momentumChart.update();
    })
    .catch(err => console.error('Momentum Chart Error:', err));
}

// --- Initialization ---
document.addEventListener('DOMContentLoaded', () => {
  initStaticTabs();
  initGlobalTooltip(); // Initialize the global tooltip on load

  if (typeof GAME_ID !== 'undefined') {
    if (GAME_STARTED) {
      // --- Game Active ---
      const conditionalBoxScoreUpdate = () => {
        if (document.visibilityState === 'visible') {
          fetchAndUpdateBoxScore();
        }
      };

      fetchAndUpdateBoxScore();
      boxScoreIntervalId = setInterval(conditionalBoxScoreUpdate, 10000);

      initMomentumChart();
      updateMomentum();
      setInterval(updateMomentum, 60000);

      document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'visible') {
          fetchAndUpdateBoxScore();
          updateMomentum();
        }
      });
    } else {
      // --- Game Not Started ---
      document.getElementById('live-status').textContent =
        'Game has not started.';

      const chartContainer = document.querySelector('.momentum-container');
      if (chartContainer) {
        chartContainer.style.display = 'none';
      }
    }
  } else {
    document.getElementById('live-status').textContent =
      'Initialization Error.';
  }
});
