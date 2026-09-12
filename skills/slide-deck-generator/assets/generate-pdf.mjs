#!/usr/bin/env node
// Renders a 16:9 slide-deck PDF from an HTML file. See references/puppeteer-render.md.

import path from 'path';

const [, , inputHtml, outputPdf] = process.argv;

if (!inputHtml || !outputPdf) {
  console.error('usage: node generate-pdf.mjs <input.html> <output.pdf>');
  process.exit(1);
}

const { default: puppeteer } = await import('puppeteer');

const htmlPath = path.resolve(inputHtml);
const pdfPath = path.resolve(outputPdf);

const browser = await puppeteer.launch({ headless: true });
const page = await browser.newPage();
await page.setViewport({ width: 1280, height: 720 });
await page.goto(`file://${htmlPath}`, { waitUntil: 'networkidle0', timeout: 30000 });
await page.pdf({
  path: pdfPath,
  width: '1280px',
  height: '720px',
  printBackground: true,
  landscape: true,
  margin: { top: 0, right: 0, bottom: 0, left: 0 },
});
await browser.close();
console.log(`PDF generated: ${pdfPath}`);
