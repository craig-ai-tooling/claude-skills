#!/usr/bin/env node
// Renders a Letter-format PDF from an HTML file. See references/puppeteer-render.md.

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
await page.goto(`file://${htmlPath}`, { waitUntil: 'networkidle0', timeout: 30000 });
await page.pdf({
  path: pdfPath,
  format: 'letter',
  printBackground: true,
  margin: { top: '20px', right: '28px', bottom: '20px', left: '28px' },
});
await browser.close();
console.log(`PDF generated: ${pdfPath}`);
