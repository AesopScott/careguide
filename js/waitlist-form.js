import { initializeApp, getApps } from 'https://www.gstatic.com/firebasejs/11.8.0/firebase-app.js';
import { getFirestore, collection, addDoc, serverTimestamp } from 'https://www.gstatic.com/firebasejs/11.8.0/firebase-firestore.js';

const FIREBASE_CONFIG = {
  apiKey:            "AIzaSyB0GaJXI_lbLhEXmctMJ0LoHiV3cHL5vQY",
  authDomain:        "careguide-def76.firebaseapp.com",
  projectId:         "careguide-def76",
  storageBucket:     "careguide-def76.firebasestorage.app",
  messagingSenderId: "658340465706",
  appId:             "1:658340465706:web:0e412731947ff51474c753"
};

const app = getApps().find(a => a.name === '[DEFAULT]') || initializeApp(FIREBASE_CONFIG);
const db  = getFirestore(app);

const formRow = document.querySelector('.form-row');
const input   = formRow?.querySelector('input[type="email"]');
const btn     = formRow?.querySelector('button[type="submit"]');

if (formRow && input && btn) {
  formRow.addEventListener('submit', async e => {
    e.preventDefault();
    const email = input.value.trim();
    if (!email) return;

    btn.disabled    = true;
    btn.textContent = 'Joining…';

    try {
      await addDoc(collection(db, 'waitlist'), {
        email,
        joinedAt: serverTimestamp(),
      });
      input.value     = '';
      btn.textContent = "You're on the list!";
      btn.style.background = '#2A7A52';
      setTimeout(() => {
        btn.textContent      = 'Join the waitlist';
        btn.style.background = '';
        btn.disabled         = false;
      }, 4000);
    } catch (err) {
      console.error('Waitlist error:', err);
      btn.textContent = 'Try again';
      btn.disabled    = false;
    }
  });
}
