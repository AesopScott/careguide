const { chromium } = require('playwright-core');
const path = require('path');
const fs = require('fs');

// Minimal ICO encoder: single 32x32 RGBA image
function pngToIco(pngBuffer) {
  // ICO header: 6 bytes
  // ICONDIRENTRY: 16 bytes
  // PNG data follows
  const pngSize = pngBuffer.length;
  const headerSize = 6;
  const entrySize = 16;
  const dataOffset = headerSize + entrySize;
  const totalSize = dataOffset + pngSize;

  const buf = Buffer.alloc(totalSize);

  // ICONDIR header
  buf.writeUInt16LE(0, 0);       // reserved
  buf.writeUInt16LE(1, 2);       // type: 1 = ICO
  buf.writeUInt16LE(1, 4);       // count: 1 image

  // ICONDIRENTRY
  buf.writeUInt8(32, 6);         // width (32 = 32px; 0 = 256px)
  buf.writeUInt8(32, 7);         // height
  buf.writeUInt8(0, 8);          // color count
  buf.writeUInt8(0, 9);          // reserved
  buf.writeUInt16LE(1, 10);      // color planes
  buf.writeUInt16LE(32, 12);     // bits per pixel
  buf.writeUInt32LE(pngSize, 14);   // size of image data
  buf.writeUInt32LE(dataOffset, 18); // offset of image data

  pngBuffer.copy(buf, dataOffset);
  return buf;
}

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  const svgContent = fs.readFileSync(path.resolve(__dirname, 'favicon.svg'), 'utf8');

  // Create a minimal HTML page rendering the SVG at different sizes
  const html = `<!DOCTYPE html>
<html><head><style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { background: transparent; }
  svg { display: block; }
</style></head>
<body>${svgContent}</body></html>`;

  await page.setContent(html, { waitUntil: 'networkidle' });

  // --- 512x512 PNG (high-res, also used for apple-touch-icon) ---
  await page.setViewportSize({ width: 512, height: 512 });
  await page.evaluate(() => {
    document.querySelector('svg').setAttribute('width', '512');
    document.querySelector('svg').setAttribute('height', '512');
  });
  const png512 = await page.screenshot({
    clip: { x: 0, y: 0, width: 512, height: 512 },
    omitBackground: true,
  });
  fs.writeFileSync('favicon-512.png', png512);
  console.log('favicon-512.png saved');

  // --- 180x180 PNG (Apple touch icon) ---
  await page.setViewportSize({ width: 180, height: 180 });
  await page.evaluate(() => {
    document.querySelector('svg').setAttribute('width', '180');
    document.querySelector('svg').setAttribute('height', '180');
  });
  const png180 = await page.screenshot({
    clip: { x: 0, y: 0, width: 180, height: 180 },
    omitBackground: true,
  });
  fs.writeFileSync('apple-touch-icon.png', png180);
  console.log('apple-touch-icon.png saved');

  // --- 32x32 PNG (standard favicon PNG) ---
  await page.setViewportSize({ width: 32, height: 32 });
  await page.evaluate(() => {
    document.querySelector('svg').setAttribute('width', '32');
    document.querySelector('svg').setAttribute('height', '32');
  });
  const png32 = await page.screenshot({
    clip: { x: 0, y: 0, width: 32, height: 32 },
    omitBackground: true,
  });
  fs.writeFileSync('favicon-32.png', png32);
  console.log('favicon-32.png saved');

  // --- 16x16 PNG ---
  await page.setViewportSize({ width: 16, height: 16 });
  await page.evaluate(() => {
    document.querySelector('svg').setAttribute('width', '16');
    document.querySelector('svg').setAttribute('height', '16');
  });
  const png16 = await page.screenshot({
    clip: { x: 0, y: 0, width: 16, height: 16 },
    omitBackground: true,
  });
  fs.writeFileSync('favicon-16.png', png16);
  console.log('favicon-16.png saved');

  await browser.close();

  // --- Build ICO from the 32x32 PNG ---
  const icoBuffer = pngToIco(png32);
  fs.writeFileSync('favicon.ico', icoBuffer);
  console.log('favicon.ico saved');

  console.log('\nAll favicon assets generated:');
  console.log('  favicon.svg       (existing, unchanged)');
  console.log('  favicon-512.png   (512×512, general use)');
  console.log('  apple-touch-icon.png (180×180, iOS home screen)');
  console.log('  favicon-32.png    (32×32)');
  console.log('  favicon-16.png    (16×16)');
  console.log('  favicon.ico       (32×32 ICO, max browser compat)');
})();
