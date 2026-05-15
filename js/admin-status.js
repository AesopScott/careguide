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

function wireSignOut(auth) {
  const navLink = document.getElementById('nav-auth-link');
  if (navLink) {
    navLink.textContent = 'Sign Out';
    navLink.href = '#';
    navLink.addEventListener('click', async e => {
      e.preventDefault();
      localStorage.removeItem('pcg_admin');
      await signOut(auth);
      window.location.href = '/login.html';
    });
  }
  const signOutBtn = document.getElementById('btn-signout');
  if (signOutBtn) {
    signOutBtn.addEventListener('click', async e => {
      e.preventDefault();
      localStorage.removeItem('pcg_admin');
      await signOut(auth);
      window.location.href = '/login.html';
    });
  }
}

// Apply Sign Out state immediately if we know the user is admin (avoids flash)
if (localStorage.getItem('pcg_admin') === '1') {
  const navLink = document.getElementById('nav-auth-link');
  if (navLink) navLink.textContent = 'Sign Out';
}

onAuthStateChanged(auth, async user => {
  if (!user) {
    // Firebase says not signed in — clear the hint so next load is clean
    localStorage.removeItem('pcg_admin');
    return;
  }
  try {
    const token = await user.getIdTokenResult();
    if (!token.claims.admin) return;
    localStorage.setItem('pcg_admin', '1');
    wireSignOut(auth);
  } catch { /* not admin */ }
});
