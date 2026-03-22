const scores = { voice: null, tremor: null, gait: null, tapping: null };

function showScreen(name) {
  document.getElementById('screen-login').style.display    = 'none';
  document.getElementById('screen-register').style.display = 'none';
  document.getElementById('main-header').style.display     =
    ['login','register'].includes(name) ? 'none' : 'flex';

  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  const el = document.getElementById('screen-' + name);
  if (el) el.classList.add('active');
  updateDots(name);
}

function updateDots(current) {
  const map = { voice:1, tremor:2, gait:3, tapping:4 };
  Object.keys(map).forEach(test => {
    const dot = document.getElementById('d' + map[test]);
    if (!dot) return;
    if (scores[test] !== null) dot.className = 'dot done';
    else if (current === test)  dot.className = 'dot active';
    else                        dot.className = 'dot';
  });
}

function showToast(msg, duration = 3000) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), duration);
}

function resetAll() {
  scores.voice = null; scores.tremor = null;
  scores.gait  = null; scores.tapping = null;
  resetVoice(); resetTremor(); resetGait(); resetTapping();
  showScreen('config');
}

document.getElementById('btn-restart').addEventListener('click', resetAll);
document.getElementById('btn-logout').addEventListener('click', logout);