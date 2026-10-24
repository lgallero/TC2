const {chromium} = require('C:/Users/Lucas/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs = require('fs');
const path = require('path');
const http = require('http');
const base = path.resolve(__dirname, '..');
const preview = path.join(__dirname, 'vista_previa.html');
let html = fs.readFileSync(preview, 'utf8');
html = html.replace('<head>', '<head><base href="../">');
fs.writeFileSync(preview, html, 'utf8');
const mime = {'.html':'text/html; charset=utf-8','.png':'image/png','.svg':'image/svg+xml','.pdf':'application/pdf'};
const server = http.createServer((req,res)=>{
  const local = path.resolve(base, '.'+decodeURIComponent(new URL(req.url,'http://localhost').pathname));
  if(!local.startsWith(base+path.sep) || !fs.existsSync(local)){res.writeHead(404);res.end();return;}
  res.setHeader('Content-Type',mime[path.extname(local)]||'text/plain');
  fs.createReadStream(local).pipe(res);
});
(async()=>{
  await new Promise(r=>server.listen(0,'127.0.0.1',r));
  let browser;
  try {browser=await chromium.launch({headless:true});}
  catch {browser=await chromium.launch({headless:true,channel:'msedge'});}
  try {
    const page=await browser.newPage({viewport:{width:1250,height:950},deviceScaleFactor:1});
    const errores=[];page.on('pageerror',e=>errores.push(e.message));
    await page.goto(`http://127.0.0.1:${server.address().port}/tmp/vista_previa.html`,{waitUntil:'domcontentloaded'});
    await page.waitForFunction(()=>window.MathJax && (window.MathJax.Hub || window.MathJax.startup),{timeout:20000}).catch(()=>{});
    await page.evaluate(async()=>{if(window.MathJax?.Hub)await new Promise(r=>MathJax.Hub.Queue(r));});
    await page.screenshot({path:path.join(__dirname,'revision_inicio.png')});
    await page.locator('h1').filter({hasText:/^Enunciado/}).first().locator('..').screenshot({path:path.join(__dirname,'revision_enunciado.png')});
    await page.locator('h3').filter({hasText:'Primera remoción: inductor L1 en derivación'}).first().locator('..').screenshot({path:path.join(__dirname,'revision_notacion.png')});
    const imagenes=await page.locator('img').evaluateAll(es=>es.map(e=>({src:e.getAttribute('src')?.slice(0,120),ok:e.complete&&e.naturalWidth>0})));
    const fallos=imagenes.filter(e=>!e.ok);
    const mathErrors=await page.locator('.MathJax_Error,.mjx-merror,merror').allTextContents();
    const cabezas=await page.locator('h2').allTextContents();
    for(const n of ['2. Transimpedancia con carga en la salida','3. Transimpedancia con generador real de corriente']){
      const l=page.locator('h2').filter({hasText:n}).first();await l.scrollIntoViewIfNeeded();
      await page.screenshot({path:path.join(__dirname,n.startsWith('2.')?'revision_ejercicio2.png':'revision_ejercicio3.png')});
    }
    console.log(JSON.stringify({imagenes:imagenes.length,fallos,mathErrors,errores,cabezas},null,2));
  } finally {await browser.close();server.close();}
})().catch(e=>{console.error(e);server.close();process.exitCode=1;});
