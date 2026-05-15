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

const PREVIEW_PARAM = 'preview';

const app  = initializeApp(FIREBASE_CONFIG);
const auth = getAuth(app);

onAuthStateChanged(auth, async user => {
  if (!user) return;
  try {
    const token = await user.getIdTokenResult();
    if (token.claims.admin) injectAdminToolbar(user);
  } catch { /* not admin, do nothing */ }
});

function injectAdminToolbar(user) {
  const bar = document.createElement('div');
  bar.id = 'admin-toolbar';
  bar.innerHTML = `
    <style>
      #admin-toolbar {
        position: fixed; bottom: 0; left: 0; right: 0; z-index: 9999;
        background: #161b22; border-top: 1px solid #30363d;
        padding: 8px 20px; display: flex; align-items: center;
        gap: 12px; font-family: -apple-system, sans-serif; font-size: 12px;
      }
      #admin-toolbar .at-label { color: #6e7681; }
      #admin-toolbar .at-email { color: #8b949e; font-weight: 600; }
      #admin-toolbar .at-spacer { flex: 1; }
      #admin-toolbar a.at-link {
        font-size: 11px; font-weight: 700; padding: 4px 12px;
        border-radius: 6px; border: 1px solid #1a3a20;
        background: #0d2a18; color: #3fb950; text-decoration: none;
      }
      #admin-toolbar button {
        font-size: 11px; font-weight: 700; padding: 4px 12px;
        border-radius: 6px; border: 1px solid #30363d;
        background: #1c2128; color: #8b949e; cursor: pointer;
        transition: opacity 0.15s;
      }
      #admin-toolbar button:hover, #admin-toolbar a.at-link:hover { opacity: 0.8; }
      #admin-toolbar .at-copied { color: #3fb950; font-size: 11px; display: none; }
    </style>
    <span class="at-label">Admin:</span>
    <span class="at-email">${user.email}</span>
    <span class="at-spacer"></span>
    <span class="at-copied" id="at-copied">Link copied!</span>
    <a class="at-link" href="/build.html">System Map</a>
    <a class="at-link" href="/outreach.html">Outreach</a>
    <button id="btn-share">Share Preview</button>
    <button id="btn-signout">Sign Out</button>
  `;
  document.body.appendChild(bar);
  document.body.style.paddingBottom = '48px';

  document.getElementById('btn-share').addEventListener('click', () => {
    const url = new URL(location.href);
    url.searchParams.set(PREVIEW_PARAM, '1');
    navigator.clipboard.writeText(url.toString()).then(() => {
      const el = document.getElementById('at-copied');
      el.style.display = 'inline';
      setTimeout(() => { el.style.display = 'none'; }, 2500);
    });
  });

  document.getElementById('btn-signout').addEventListener('click', async () => {
    await signOut(auth);
    location.reload();
  });
}
