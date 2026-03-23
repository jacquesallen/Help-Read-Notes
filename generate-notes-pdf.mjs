import { chromium } from 'playwright';
import { fileURLToPath } from 'url';
import path from 'path';

const dir = path.dirname(fileURLToPath(import.meta.url));
const htmlPath = path.resolve(dir, 'presenter-notes.html');
const pdfPath = path.resolve(dir, 'presenter-notes.pdf');

const browser = await chromium.launch({
  executablePath: '/root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome',
});
const page = await browser.newPage();
await page.goto(`file://${htmlPath}`, { waitUntil: 'domcontentloaded' });
await page.pdf({
  path: pdfPath,
  format: 'A4',
  printBackground: true,
  margin: { top: '0', right: '0', bottom: '0', left: '0' },
});
await browser.close();
console.log(`PDF saved to: ${pdfPath}`);
