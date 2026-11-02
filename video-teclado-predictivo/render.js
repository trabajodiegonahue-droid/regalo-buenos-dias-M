// Captura la animación cuadro por cuadro y la codifica en MP4.
//   node render.js <carpeta_salida> [workers]           -> video completo (segmentos seg*.mp4 + timeline.json)
//   node render.js <carpeta_salida> preview 1.5 10 22   -> PNG de esos segundos (para revisar)
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const PAGE = 'file://' + path.resolve(__dirname, 'teclado-predictivo.html');
const FPS = 30;
const out = path.resolve(process.argv[2] || 'out');
fs.mkdirSync(out, { recursive: true });

async function openPage() {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  await page.goto(PAGE);
  await page.evaluate(async () => { await document.fonts.ready; });
  // fuerza la carga de emojis y fuentes en todos los estados
  for (const t of [1, 15, 30, 45, 60]) await page.evaluate(x => renderAt(x), t);
  await page.waitForTimeout(300);
  return { browser, page };
}

(async () => {
  if (process.argv[3] === 'preview') {
    const { browser, page } = await openPage();
    for (const s of process.argv.slice(4)) {
      await page.evaluate(x => renderAt(x), +s);
      await page.screenshot({ path: path.join(out, `p_${(+s).toFixed(2)}.png`) });
    }
    await browser.close();
    return;
  }
  const workers = +(process.argv[3] || 4);
  const { browser: b0, page: p0 } = await openPage();
  const tl = await p0.evaluate(() => window.TL);
  await b0.close();
  fs.writeFileSync(path.join(out, 'timeline.json'), JSON.stringify(tl, null, 1));
  const N = Math.round(tl.dur * FPS);
  const chunk = Math.ceil(N / workers);
  const t0 = Date.now();
  let done = 0;
  await Promise.all([...Array(workers)].map(async (_, w) => {
    const a = w * chunk, b = Math.min(N, (w + 1) * chunk);
    const { browser, page } = await openPage();
    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
      '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', String(FPS), path.join(out, `seg${w}.mp4`)],
      { stdio: ['pipe', 'inherit', 'inherit'] });
    for (let f = a; f < b; f++) {
      await page.evaluate(x => renderAt(x), f / FPS);
      const buf = await page.screenshot({ type: 'jpeg', quality: 95 });
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
      if (++done % 150 === 0) console.log(`${done}/${N} cuadros · ${((Date.now() - t0) / 1000).toFixed(0)}s`);
    }
    ff.stdin.end();
    await new Promise(r => ff.on('close', r));
    await browser.close();
  }));
  fs.writeFileSync(path.join(out, 'segments.txt'), [...Array(workers)].map((_, w) => `file 'seg${w}.mp4'`).join('\n') + '\n');
  console.log(`Listo: ${N} cuadros en ${((Date.now() - t0) / 1000).toFixed(0)}s`);
})();
