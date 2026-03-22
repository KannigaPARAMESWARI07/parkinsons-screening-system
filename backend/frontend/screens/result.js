function renderResult(result) {
  const level = result.risk_level;

  // Profile card
  if (currentUser) {
    document.getElementById('result-profile').style.display = 'flex';
    const initials = currentUser.name.split(' ').map(n=>n[0]).join('').toUpperCase().slice(0,2);
    document.getElementById('result-avatar').textContent = initials;
    document.getElementById('result-name').textContent   = currentUser.name;
    document.getElementById('result-meta').textContent   =
      `Age: ${currentUser.age} · Gender: ${currentUser.gender} · ${currentUser.email}`;
  }

  // Risk badge
  const badge = document.getElementById('result-badge');
  badge.className = 'risk-badge risk-' + level;
  badge.textContent = level === 'low' ? 'Low Risk'
                    : level === 'moderate' ? 'Moderate Risk'
                    : 'High Risk';

  // Score number
  const scoreEl = document.getElementById('result-score');
  scoreEl.className = 'score-number score-' + level;
  scoreEl.textContent = result.risk_score;

  // Advice
  document.getElementById('advice-box').className = 'advice-box ' + level;
  document.getElementById('advice-text').textContent = result.advice;

  // Modality breakdown
  const icons = { voice:'🎤', tremor:'📳', gait:'🚶', tapping:'👆' };
  const grid  = document.getElementById('modality-grid');
  grid.innerHTML = '';
  Object.entries(result.modality_scores || {}).forEach(([key, val]) => {
    const color = val > 60 ? 'var(--red)' : val > 30 ? 'var(--amber)' : 'var(--green)';
    grid.innerHTML += `
      <div class="modality-card">
        <div class="modality-name">${icons[key]||''} ${key}</div>
        <div class="modality-score">${val}</div>
        <div class="mini-bar-track">
          <div class="mini-bar-fill" style="width:${val}%;background:${color}"></div>
        </div>
      </div>`;
  });

  // History
  apiGetHistory().then(data => {
    const history = (data.history || []);
    if (history.length > 1) {
      document.getElementById('history-title').style.display = 'block';
      const container = document.getElementById('history-list');
      container.innerHTML = '';
      history.slice(-7).reverse().forEach(h => {
        const color = h.score > 60 ? 'var(--red)'
                    : h.score > 30 ? 'var(--amber)'
                    : 'var(--green)';
        container.innerHTML += `
          <div class="history-row">
            <div class="history-date">${h.date}</div>
            <div class="history-bar-track">
              <div class="history-bar-fill" style="width:${h.score}%;background:${color}"></div>
            </div>
            <div class="history-score">${h.score}</div>
          </div>`;
      });
    }
  }).catch(() => {});
}