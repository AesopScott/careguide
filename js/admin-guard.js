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
        wireSignOut(auth);
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

function wireSignOut(auth) {
  const btn = document.getElementById('btn-signout');
  if (btn) {
    btn.addEventListener('click', async e => {
      e.preventDefault();
      await signOut(auth);
      location.href = '/login.html';
    });
  }
}

function injectPreviewBanner() {
  const banner = document.createElement('div');
  banner.id = 'preview-banner';
  banner.style.cssText = 'position:fixed;bottom:0;left:0;right:0;z-index:9999;background:#1a2a40;border-top:1px solid #1f4068;padding:8px 20px;font-family:-apple-system,sans-serif;font-size:12px;color:#58a6ff;';
  banner.textContent = '◉ Preview link — internal page shared for review';
  document.body.appendChild(banner);
  document.body.style.paddingBottom = '40px';
}
