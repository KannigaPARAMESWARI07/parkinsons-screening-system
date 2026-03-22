let tapCount = 0;
let tapIntervals = [];
let lastTapTime = null;

function resetTapping() {
  tapCount = 0; tapIntervals = []; lastTapTime = null;
  document.getElementById('tap-count').textContent = '0';
  document.getElementById('tap-progress').style.width = '0%';
  document.getElementById('tap-circle').disabled = true;
  document.getElementById('tap-circle').textContent = 'TAP';
  document.getElementById('btn-tapping-start').style.display = 'block';
}

document.getElementById('btn-tapping-start').addEventListener('click', () => {
  tapCount = 0; tapIntervals = []; lastTapTime = null;
  document.getElementById('tap-count').textContent = '0';
  document.getElementById('tap-progress').style.width = '0%';
  document.getElementById('tap-circle').disabled = false;
  document.getElementById('btn-tapping-start').style.display = 'none';
});

document.getElementById('tap-circle').addEventListener('click', async () => {
  const now = Date.now();
  if (lastTapTime !== null) tapIntervals.push(now - lastTapTime);
  lastTapTime = now;
  tapCount++;
  document.getElementById('tap-count').textContent = tapCount;
  document.getElementById('tap-progress').style.width = (tapCount/25*100) + '%';

  if (tapCount >= 25) {
    document.getElementById('tap-circle').disabled = true;
    document.getElementById('tap-circle').textContent = '✓';
    await new Promise(r => setTimeout(r, 400));
    try {
      const data = await apiPredictTapping(tapIntervals);
      scores.tapping = data.probability;
    } catch(e) {
      showToast('Tapping API error');
      scores.tapping = null;
    }
    try {
      const result = await apiFuseScores(scores);
      renderResult(result);
      showScreen('result');
    } catch(e) {
      showToast('Could not calculate result: ' + e.message);
    }
  }
});

document.getElementById('btn-tapping-skip').addEventListener('click', async () => {
  scores.tapping = null;
  try {
    const result = await apiFuseScores(scores);
    renderResult(result);
    showScreen('result');
  } catch(e) {
    showToast('Could not calculate result: ' + e.message);
  }
});