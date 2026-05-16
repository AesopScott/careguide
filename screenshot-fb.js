const { chromium } = require('playwright-core');
const path = require('path');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  // --- Cover photo: 1640×624 (2x retina of 820×312) ---
  await page.setViewportSize({ width: 1640, height: 624 });
  const coverPath = 'file://' + path.resolve(__dirname, 'designs/fb-cover.html').replace(/\\/g, '/');
  await page.goto(coverPath, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1200);
  await page.screenshot({ path: 'designs/fb-cover.png', clip: { x: 0, y: 0, width: 1640, height: 624 } });
  console.log('fb-cover.png saved (1640×624)');

  // --- Profile picture: 360×360 ---
  await page.setViewportSize({ width: 360, height: 360 });
  const profilePath = 'file://' + path.resolve(__dirname, 'designs/fb-profile.html').replace(/\\/g, '/');
  await page.goto(profilePath, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1200);
  await page.screenshot({ path: 'designs/fb-profile.png', clip: { x: 0, y: 0, width: 360, height: 360 } });
  console.log('fb-profile.png saved (360×360)');

  await browser.close();
  console.log('\nFacebook assets ready in designs/');
})();
