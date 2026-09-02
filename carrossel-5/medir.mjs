import { chromium } from 'playwright';
import { readFileSync, readdirSync, mkdirSync } from 'fs';

const files = ['Main.dc.html', ...readdirSync('.').filter(f => /^L\d\d\.dc\.html$/.test(f)).sort()];
mkdirSync('previa', { recursive: true });
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium', args: ['--no-sandbox'] });
const page = await browser.newPage({ viewport: { width: 1080, height: 1080 } });

for (const f of files) {
  const html = readFileSync(f, 'utf8')
    .replace('<script src="./support.js"></script>', '')
    .replace(/<\/?x-dc>/g, '').replace(/<\/?helmet>/g, '');
  await page.setContent(html, { waitUntil: 'networkidle' });

  // altura natural: solta a altura fixa e mede o que o conteudo pede
  const natural = await page.evaluate(() => {
    const root = document.querySelector('body > div');
    const antes = root.style.height;
    root.style.height = 'auto';
    const h = Math.ceil(root.getBoundingClientRect().height);
    root.style.height = antes;
    return h;
  });

  const folga = 1080 - natural;
  const flag = natural > 1080 ? `  ESTOURA ${natural - 1080}px` : (folga < 40 ? '  apertado' : '');
  console.log(`${f.padEnd(16)} natural=${String(natural).padStart(5)}px  folga=${String(folga).padStart(5)}px${flag}`);
  await page.screenshot({ path: `previa/${f.replace('.dc.html', '')}.png` });
}
await browser.close();
