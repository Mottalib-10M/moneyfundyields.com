import { chromium } from 'playwright';
const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: 390, height: 844 } });
await p.goto('file://' + process.argv[2], { waitUntil: 'domcontentloaded' });
await p.waitForTimeout(300);
const r = await p.evaluate(() => {
  const out = [];
  for (const el of document.querySelectorAll('*')) {
    const b = el.getBoundingClientRect();
    if (b.right > window.innerWidth + 1 && b.width > 20) {
      out.push({ tag: el.tagName, cls: (el.className || '').toString().slice(0, 80), right: Math.round(b.right), w: Math.round(b.width), txt: (el.textContent || '').trim().slice(0, 40) });
    }
  }
  return out.slice(0, 8);
});
console.log(JSON.stringify(r, null, 1));
await b.close();
