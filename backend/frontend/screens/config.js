// Auto-detect server URL
const CONFIG_SERVER_URL = window.location.origin;

document.getElementById('backend-url').value = CONFIG_SERVER_URL;

document.getElementById('btn-connect').addEventListener('click', async () => {
  const url = document.getElementById('backend-url').value;
  const dot = document.getElementById('status-dot');
  const txt = document.getElementById('status-text');
  txt.textContent = 'Testing...';
  dot.className = 'status-dot';
  try {
    setBaseUrl(url);
    const data = await apiTestConnection();
    if (data.status === 'ok') {
      dot.className = 'status-dot online';
      txt.textContent = 'Connected — models loaded';
      setDemoMode(false);
      setTimeout(() => showScreen('welcome'), 600);
    }
  } catch(e) {
    dot.className = 'status-dot offline';
    txt.textContent = 'Cannot reach server — check IP and port';
  }
});

document.getElementById('btn-skip').addEventListener('click', () => {
  setDemoMode(true);
  showToast('Demo mode — results are simulated');
  showScreen('welcome');
});