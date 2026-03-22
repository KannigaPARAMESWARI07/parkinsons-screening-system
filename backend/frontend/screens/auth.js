// Auto-detect server URL from current page address
const SERVER_URL = window.location.origin;

let currentUser = null;

function setCurrentUser(user) {
  currentUser = user;
  localStorage.setItem('pd_user', JSON.stringify(user));
  updateUserBar();
}

function loadStoredUser() {
  try {
    const s = localStorage.getItem('pd_user');
    if (s) {
      currentUser = JSON.parse(s);
      updateUserBar();
      return true;
    }
  } catch(e) {}
  return false;
}

function logout() {
  currentUser = null;
  localStorage.removeItem('pd_user');
  updateUserBar();
  showAuthScreen('login');
}

function updateUserBar() {
  const bar = document.getElementById('user-bar');
  if (!bar) return;
  if (currentUser) {
    const initials = currentUser.name
      .split(' ')
      .map(n => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
    document.getElementById('user-avatar').textContent   = initials;
    document.getElementById('user-bar-name').textContent = currentUser.name;
  }
}

function showAuthScreen(type) {
  document.getElementById('screen-login').style.display    = type === 'login'    ? 'flex' : 'none';
  document.getElementById('screen-register').style.display = type === 'register' ? 'flex' : 'none';
  document.getElementById('main-header').style.display     = 'none';
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
}

function showError(id, msg) {
  const el = document.getElementById(id);
  if (el) { el.textContent = msg; el.classList.add('show'); }
}

function clearErrors() {
  document.querySelectorAll('.form-error').forEach(e => {
    e.classList.remove('show');
    e.textContent = '';
  });
}

// Password toggles
document.querySelectorAll('.toggle-pw').forEach(btn => {
  btn.addEventListener('click', () => {
    const input = document.getElementById(btn.dataset.target);
    if (!input) return;
    input.type      = input.type === 'password' ? 'text' : 'password';
    btn.textContent = input.type === 'password' ? '👁' : '🙈';
  });
});

// Register
document.getElementById('form-register').addEventListener('submit', async e => {
  e.preventDefault();
  clearErrors();

  const name     = document.getElementById('reg-name').value.trim();
  const email    = document.getElementById('reg-email').value.trim();
  const password = document.getElementById('reg-password').value;
  const confirm  = document.getElementById('reg-confirm').value;
  const age      = parseInt(document.getElementById('reg-age').value);
  const gender   = document.getElementById('reg-gender').value;

  let ok = true;
  if (!name)                 { showError('err-name',     'Name is required');           ok = false; }
  if (!email.includes('@'))  { showError('err-email',    'Enter a valid email');         ok = false; }
  if (password.length < 6)  { showError('err-password', 'Min. 6 characters');           ok = false; }
  if (password !== confirm)  { showError('err-confirm',  'Passwords do not match');      ok = false; }
  if (!age || age < 1)       { showError('err-age',      'Enter a valid age');           ok = false; }
  if (!gender)               { showError('err-gender',   'Select a gender');             ok = false; }
  if (!ok) return;

  const btn = document.getElementById('btn-register');
  btn.textContent = 'Creating account...';
  btn.disabled    = true;

  try {
    const res = await fetch(SERVER_URL + '/auth/register', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ name, email, password, age, gender })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Registration failed');
    setCurrentUser(data);
    // also update BASE_URL in api.js to match server
    if (typeof setBaseUrl === 'function') setBaseUrl(SERVER_URL);
    showToast('Account created! Welcome, ' + name);
    showScreen('config');
  } catch(err) {
    showError('err-register', err.message);
  } finally {
    btn.textContent = 'Create account';
    btn.disabled    = false;
  }
});

// Login
document.getElementById('form-login').addEventListener('submit', async e => {
  e.preventDefault();
  clearErrors();

  const email    = document.getElementById('login-email').value.trim();
  const password = document.getElementById('login-password').value;

  if (!email || !password) {
    showError('err-login', 'Email and password are required');
    return;
  }

  const btn = document.getElementById('btn-login');
  btn.textContent = 'Signing in...';
  btn.disabled    = true;

  try {
    const res = await fetch(SERVER_URL + '/auth/login', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ email, password })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Login failed');
    setCurrentUser(data);
    // also update BASE_URL in api.js to match server
    if (typeof setBaseUrl === 'function') setBaseUrl(SERVER_URL);
    showToast('Welcome back, ' + data.name);
    showScreen('config');
  } catch(err) {
    showError('err-login', err.message);
  } finally {
    btn.textContent = 'Sign in';
    btn.disabled    = false;
  }
});

// Auto-login on page load
window.addEventListener('DOMContentLoaded', () => {
  // Set BASE_URL to current server automatically
  if (typeof setBaseUrl === 'function') setBaseUrl(SERVER_URL);

  if (loadStoredUser()) {
    if (typeof setBaseUrl === 'function') setBaseUrl(SERVER_URL);
    showScreen('config');
  } else {
    showAuthScreen('login');
  }
});