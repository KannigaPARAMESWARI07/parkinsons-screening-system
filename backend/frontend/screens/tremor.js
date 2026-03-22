let tremorState = 'idle';
let tremorTimer = null;
let tremorListener = null;
let tremorSamples = [];

function resetTremor() {
  tremorState = 'idle';
  clearInterval(tremorTimer);
  if (tremorListener) window.removeEventListener('devicemotion', tremorListener);
  document.getElementById('btn-tremor').textContent = 'Start tremor test';
  document.getElementById('btn-tremor').disabled = false;
  document.getElementById('tremor-visual').innerHTML =
    '<div class="big-icon">📱</div><div class="visual-label">Ready to measure</div>';
  document.getElementById('tremor-sensors').style.display = 'none';
}

document.getElementById('btn-tremor').addEventListener('click', async () => {
  if (tremorState !== 'idle') return;
  tremorSamples = [];
  tremorState = 'collecting';
  document.getElementById('btn-tremor').textContent = 'Measuring...';
  document.getElementById('btn-tremor').disabled = true;
  document.getElementById('tremor-sensors').style.display = 'grid';
  let countdown = 5;
  document.getElementById('tremor-visual').innerHTML =
    `<div class="countdown-num" id="tremor-cd">5</div>
     <div class="visual-label">Stay completely still</div>`;

  if (typeof DeviceMotionEvent !== 'undefined' &&
      typeof DeviceMotionEvent.requestPermission === 'function') {
    await DeviceMotionEvent.requestPermission().catch(() => {});
  }

  tremorListener = e => {
    const a = e.accelerationIncludingGravity;
    if (!a) return;
    const x = a.x||0, y = a.y||0, z = a.z||0;
    tremorSamples.push([x, y, z, x*0.8, y*0.8, z*0.8]);
    document.getElementById('sx').textContent = x.toFixed(2);
    document.getElementById('sy').textContent = y.toFixed(2);
    document.getElementById('sz').textContent = z.toFixed(2);
  };
  window.addEventListener('devicemotion', tremorListener);

  tremorTimer = setInterval(async () => {
    countdown--;
    const cd = document.getElementById('tremor-cd');
    if (cd) cd.textContent = countdown;
    if (countdown <= 0) {
      clearInterval(tremorTimer);
      window.removeEventListener('devicemotion', tremorListener);
      tremorState = 'analysing';
      document.getElementById('tremor-visual').innerHTML =
        '<div class="spinner"></div><div class="visual-label">Analysing tremor...</div>';
      try {
        if (tremorSamples.length < 10) throw new Error('Not enough motion data');
        const data = await apiPredictTremor(tremorSamples);
        scores.tremor = data.probability;
      } catch(e) {
        showToast('Tremor skipped — ' + e.message);
        scores.tremor = null;
      }
      tremorState = 'idle';
      showScreen('gait');
    }
  }, 1000);
});

document.getElementById('btn-tremor-skip').addEventListener('click', () => {
  scores.tremor = null;
  clearInterval(tremorTimer);
  if (tremorListener) window.removeEventListener('devicemotion', tremorListener);
  showScreen('gait');
});