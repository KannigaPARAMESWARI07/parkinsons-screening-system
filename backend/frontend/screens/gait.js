let gaitState = 'idle';
let gaitTimer = null;
let gaitListener = null;
let gaitSamples = [];

function resetGait() {
  gaitState = 'idle';
  clearInterval(gaitTimer);
  if (gaitListener) window.removeEventListener('devicemotion', gaitListener);
  document.getElementById('btn-gait').textContent = 'Start walking test';
  document.getElementById('btn-gait').disabled = false;
  document.getElementById('gait-visual').innerHTML =
    '<div class="big-icon">🚶</div><div class="visual-label">Ready to measure</div>';
  document.getElementById('gait-progress-wrap').style.display = 'none';
  document.getElementById('gait-progress').style.width = '0%';
}

document.getElementById('btn-gait').addEventListener('click', async () => {
  if (gaitState !== 'idle') return;
  gaitSamples = [];
  gaitState = 'collecting';
  document.getElementById('btn-gait').textContent = 'Walk now...';
  document.getElementById('btn-gait').disabled = true;
  document.getElementById('gait-progress-wrap').style.display = 'block';
  let elapsed = 0;
  document.getElementById('gait-visual').innerHTML =
    `<div class="countdown-num" id="gait-cd">15</div>
     <div class="visual-label">Walk at your normal pace</div>`;

  if (typeof DeviceMotionEvent !== 'undefined' &&
      typeof DeviceMotionEvent.requestPermission === 'function') {
    await DeviceMotionEvent.requestPermission().catch(() => {});
  }

  gaitListener = e => {
    const a = e.accelerationIncludingGravity;
    if (!a) return;
    const x = a.x||0, y = a.y||0, z = a.z||0;
    const mag = Math.sqrt(x*x + y*y + z*z);
    gaitSamples.push([x,y,z, x*0.9,y*0.9,z*0.9, x*0.8,y*0.8,z*0.8,
                      x*0.7,y*0.7,z*0.7, x*0.6,y*0.6,z*0.6, mag]);
  };
  window.addEventListener('devicemotion', gaitListener);

  gaitTimer = setInterval(async () => {
    elapsed++;
    const cd = document.getElementById('gait-cd');
    if (cd) cd.textContent = 15 - elapsed;
    document.getElementById('gait-progress').style.width = (elapsed/15*100) + '%';
    if (elapsed >= 15) {
      clearInterval(gaitTimer);
      window.removeEventListener('devicemotion', gaitListener);
      gaitState = 'analysing';
      document.getElementById('gait-visual').innerHTML =
        '<div class="spinner"></div><div class="visual-label">Analysing gait patterns...</div>';
      try {
        if (gaitSamples.length < 50) throw new Error('Not enough motion data');
        const data = await apiPredictGait(gaitSamples);
        scores.gait = data.probability;
      } catch(e) {
        showToast('Gait skipped — ' + e.message);
        scores.gait = null;
      }
      gaitState = 'idle';
      showScreen('tapping');
    }
  }, 1000);
});

document.getElementById('btn-gait-skip').addEventListener('click', () => {
  scores.gait = null;
  clearInterval(gaitTimer);
  if (gaitListener) window.removeEventListener('devicemotion', gaitListener);
  showScreen('tapping');
});