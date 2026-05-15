import { initializeApp }          from 'https://www.gstatic.com/firebasejs/11.8.0/firebase-app.js';
import { getAuth, onAuthStateChanged, signOut } from 'https://www.gstatic.com/firebasejs/11.8.0/firebase-auth.js';

const FIREBASE_CONFIG = {
  apiKey:            "AIzaSyB0GaJXI_lbLhEXmctMJ0LoHiV3cHL5vQY",
  authDomain:        "careguide-def76.firebaseapp.com",
  projectId:         "careguide-def76",
  storageBucket:     "careguide-def76.firebasestorage.app",
  messagingSenderId: "658340465706",
  appId:             "1:658340465706:web:0e412731947ff51474c753"
};

const CONFIG_READY = !FIREBASE_CONFIG.apiKey.startsWith('REPLACE');
const PREVIEW_PARAM = 'preview';

// Hide body immediately until auth resolves (prevents flash of content)
document.documentElement.style.visibility = 'hidden';

if (!CONFIG_READY) {
  // Firebase not configured yet — show page normally in dev
  document.documentElement.style.visibility = '';
} else {
  const app  = initializeApp(FIREBASE_CONFIG);
  const auth = getAuth(app);

  onAuthStateChanged(auth, async user => {
    // Allow access if a ?preview=1 param is set (admin shared the link for a demo)
    const params  = new URLSearchParams(location.search);
    const preview = params.get(PREVIEW_PARAM) === '1';

    if (preview) {
      document.documentElement.style.visibility = '';
      injectPreviewBanner();
      return;
    }

    if (!user) {
      redirect();
      return;
    }

    try {
      const token = await user.getIdTokenResult();
      if (token.claims.admin) {
        document.documentElement.style.visibility = '';
        injectAdminToolbar(user, auth);
      } else {
        await signOut(auth);
        redirect();
      }
    } catch {
      redirect();
    }
  });
}

function redirect() {
  document.documentElement.style.visibility = '';
  location.href = '/login.html?next=' + encodeURIComponent(location.pathname + location.search);
}

function injectAdminToolbar(user, auth) {
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
      #admin-toolbar button {
        font-size: 11px; font-weight: 700; padding: 4px 12px;
        border-radius: 6px; border: 1px solid; cursor: pointer;
        transition: opacity 0.15s;
      }
      #admin-toolbar button:hover { opacity: 0.8; }
      #admin-toolbar .btn-share {
        background: #0d2a18; border-color: #1a3a20; color: #3fb950;
      }
      #admin-toolbar .btn-signout {
        background: #1c2128; border-color: #30363d; color: #8b949e;
      }
      #admin-toolbar .at-copied {
        color: #3fb950; font-size: 11px; display: none;
      }
    </style>
    <span class="at-label">Admin:</span>
    <span class="at-email">${user.email}</span>
    <span class="at-spacer"></span>
    <span class="at-copied" id="at-copied">Link copied!</span>
    <button class="btn-share" id="btn-share">Share Preview Link</button>
    <button class="btn-signout" id="btn-signout">Sign Out</button>
  `;
  document.body.appendChild(bar);
  // Add bottom padding so toolbar doesn't overlap page content
  document.body.style.paddingBottom = '48px';

  document.getElementById('btn-share').addEventListener('click', () => {
    const url = new URL(location.href);
    url.searchParams.set(PREVIEW_PARAM, '1');
    navigator.clipboard.writeText(url.toString()).then(() => {
      const copied = document.getElementById('at-copied');
      copied.style.display = 'inline';
      setTimeout(() => { copied.style.display = 'none'; }, 2500);
    });
  });

  document.getElementById('btn-signout').addEventListener('click', async () => {
    await signOut(auth);
    location.href = '/login.html';
  });
}

function injectPreviewBanner() {
  const bar = document.createElement('div');
  bar.innerHTML = `
    <style>
      #preview-banner {
        position: fixed; bottom: 0; left: 0; right: 0; z-index: 9999;
        background: #1a2a40; border-top: 1px solid #1f4068;
        padding: 8px 20px; display: flex; align-items: center; gap: 10px;
        font-family: -apple-system, sans-serif; font-size: 12px; color: #58a6ff;
      }
    </style>
    <div id="preview-banner">
      ◉ Preview link — internal page shared for review
    </div>
  `;
  document.body.appendChild(bar);
  document.body.style.paddingBottom = '40px';
}
