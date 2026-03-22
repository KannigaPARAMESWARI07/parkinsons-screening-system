let BASE_URL = window.location.origin;
let DEMO_MODE = false;
const USER_ID = () => currentUser ? currentUser.email : 'guest';

function setBaseUrl(url) { BASE_URL = url.trim().replace(/\/$/, ''); }
function setDemoMode(val) { DEMO_MODE = val; }
function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function apiTestConnection() {
  const res = await fetch(BASE_URL + '/health', {
    signal: AbortSignal.timeout(4000)
  });
  return res.json();
}

async function apiRegister(data) {
  const res = await fetch(BASE_URL + '/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  const json = await res.json();
  if (!res.ok) throw new Error(json.detail || 'Registration failed');
  return json;
}

async function apiLogin(email, password) {
  const res = await fetch(BASE_URL + '/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  const json = await res.json();
  if (!res.ok) throw new Error(json.detail || 'Login failed');
  return json;
}

async function apiPredictVoice(audioBlob) {
  if (DEMO_MODE) { await sleep(1500); return { probability: Math.random() * 0.5 }; }
  const form = new FormData();
  form.append('file', audioBlob, 'voice.wav');
  const res = await fetch(`${BASE_URL}/predict/voice?user_id=${USER_ID()}`, {
    method: 'POST', body: form
  });
  return res.json();
}

async function apiPredictTremor(samples) {
  if (DEMO_MODE) { await sleep(1200); return { probability: Math.random() * 0.4 }; }
  const res = await fetch(`${BASE_URL}/predict/tremor`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: USER_ID(), samples })
  });
  return res.json();
}

async function apiPredictGait(samples) {
  if (DEMO_MODE) { await sleep(1500); return { probability: Math.random() * 0.45 }; }
  const res = await fetch(`${BASE_URL}/predict/gait`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: USER_ID(), samples })
  });
  return res.json();
}

async function apiPredictTapping(intervals) {
  if (DEMO_MODE) { await sleep(1000); return { probability: Math.random() * 0.35 }; }
  const res = await fetch(`${BASE_URL}/predict/tapping`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: USER_ID(), intervals_ms: intervals })
  });
  return res.json();
}

async function apiFuseScores(scores) {
  if (DEMO_MODE) {
    await sleep(1000);
    const raw = (
      (scores.voice   || 0) * 0.40 +
      (scores.tremor  || 0) * 0.25 +
      (scores.gait    || 0) * 0.20 +
      (scores.tapping || 0) * 0.15
    ) * 100;
    const level = raw < 30 ? 'low' : raw < 60 ? 'moderate' : 'high';
    return {
      risk_score: Math.round(raw),
      risk_level: level,
      modality_scores: {
        voice:   Math.round((scores.voice   || 0) * 100),
        tremor:  Math.round((scores.tremor  || 0) * 100),
        gait:    Math.round((scores.gait    || 0) * 100),
        tapping: Math.round((scores.tapping || 0) * 100),
      },
      advice: raw < 30
        ? 'Your motor patterns appear within normal range. Continue regular monitoring.'
        : raw < 60
        ? 'Some patterns show mild variation. Consider scheduling a check-up with your doctor.'
        : 'Several biomarkers show Parkinson\'s risk patterns. Please consult a neurologist.',
      baseline_active: false,
    };
  }
  const res = await fetch(`${BASE_URL}/predict/fuse`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: USER_ID(), ...scores })
  });
  return res.json();
}

async function apiGetHistory() {
  if (DEMO_MODE) return { history: [] };
  const res = await fetch(`${BASE_URL}/history/${USER_ID()}`);
  return res.json();
}