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

onAuthStateChanged(auth, async user => {
  if (!user) return;
  try {
    const token = await user.getIdTokenResult();
    if (!token.claims.admin) return;

    // Public pages — swap "Sign In" link to "Sign Out"
    const navLink = document.getElementById('nav-auth-link');
    if (navLink) {
      navLink.textContent = 'Sign Out';
      navLink.href = '#';
      navLink.addEventListener('click', async e => {
        e.preventDefault();
        await signOut(auth);
        window.location.href = '/login.html';
      });
    }

    // Protected pages — wire up the Sign Out link in the header
    const signOutBtn = document.getElementById('btn-signout');
    if (signOutBtn) {
      signOutBtn.addEventListener('click', async e => {
        e.preventDefault();
        await signOut(auth);
        window.location.href = '/login.html';
      });
    }
  } catch { /* not admin */ }
});
