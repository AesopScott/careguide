const { chromium } = require('playwright-core');
const path = require('path');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.setViewportSize({ width: 1200, height: 630 });
  const url = 'file://' + path.resolve(__dirname, 'og-card.html').replace(/\\/g, '/');
  await page.goto(url, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1200);
  await page.screenshot({ path: 'og-preview-check.png' });
  await browser.close();
})();
