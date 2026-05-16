const { chromium } = require('playwright-core');
const path = require('path');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  await page.setViewportSize({ width: 2048, height: 1152 });
  const filePath = 'file://' + path.resolve(__dirname, 'designs/yt-banner.html').replace(/\\/g, '/');
  await page.goto(filePath, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1200);
  await page.screenshot({ path: 'designs/yt-banner.png', clip: { x: 0, y: 0, width: 2048, height: 1152 } });
  console.log('yt-banner.png saved (2048×1152)');

  // Small text version
  const smallPath = 'file://' + path.resolve(__dirname, 'designs/yt-banner-small.html').replace(/\\/g, '/');
  await page.goto(smallPath, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1200);
  await page.screenshot({ path: 'designs/yt-banner-small.png', clip: { x: 0, y: 0, width: 2048, height: 1152 } });
  console.log('yt-banner-small.png saved (2048×1152)');

  await browser.close();
})();
