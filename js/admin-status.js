import { initializeApp } from 'https://www.gstatic.com/firebasejs/11.8.0/firebase-app.js';
import { getAuth, onAuthStateChanged, signOut } from 'https://www.gstatic.com/firebasejs/11.8.0/firebase-auth.js';

const FIREBASE_CONFIG = {
  apiKey:            "AIzaSyB0GaJXI_lbLhEXmctMJ0LoHiV3cHL5vQY",
  authDomain:        "careguide-def76.firebaseapp.com",
  projectId:         "careguide-def76",
  storageBucket:     "careguide-def76.firebasestorage.app",
  messagingSenderId: "658340465706",
  appId:             "1:658340465706:web:0e412731947ff51474c753"
};

const app  = initializeApp(FIREBASE_CONFIG);
const auth = getAuth(app);

const navLink    = document.getElementById('nav-auth-link');
const hero       = document.querySelector('.hero');
const adminPanel = document.getElementById('admin-panel');

// Wire the nav link to handle both Sign In (href) and Sign Out (click) dynamically
if (navLink) {
  navLink.addEventListener('click', async e => {
    if (navLink.dataset.mode === 'signout') {
      e.preventDefault();
      localStorage.removeItem('pcg_admin');
      await signOut(auth);
      window.location.href = '/login.html';
    }
    // otherwise it's a regular link to /login.html — let it navigate
  });
}

function applySignOut() {
  if (!navLink) return;
  navLink.textContent  = 'Sign Out';
  navLink.href         = '#';
  navLink.dataset.mode = 'signout';
}

function applySignIn() {
  if (!navLink) return;
  navLink.textContent  = 'Sign In';
  navLink.href         = '/login.html';
  delete navLink.dataset.mode;
}

function showAdminPanel() {
  if (hero)       hero.classList.add('admin-active');
  if (adminPanel) adminPanel.style.display = 'flex';
}

function hideAdminPanel() {
  if (hero)       hero.classList.remove('admin-active');
  if (adminPanel) adminPanel.style.display = 'none';
}

// Apply instant state from localStorage to avoid flash
if (localStorage.getItem('pcg_admin') === '1') {
  applySignOut();
  showAdminPanel();
}

onAuthStateChanged(auth, async user => {
  if (!user) {
    localStorage.removeItem('pcg_admin');
    applySignIn();
    hideAdminPanel();
    return;
  }

  try {
    // Force refresh = true ensures latest custom claims, not a stale cached token
    const token = await user.getIdTokenResult(true);

    applySignOut(); // any logged-in user gets Sign Out

    if (token.claims.admin) {
      localStorage.setItem('pcg_admin', '1');
      showAdminPanel();
    } else {
      localStorage.removeItem('pcg_admin');
      hideAdminPanel();
    }
  } catch {
    hideAdminPanel();
  }
});
