const {chromium} = require('C:/Users/Lucas/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'); const path=require('path'); const http=require('http');
const base=path.resolve(__dirname,'..');
const preview=path.join(__dirname,'vista_previa.html');
let html=fs.readFileSync(preview,'utf8');
if(!html.includes('<base href="../">'))html=html.replace('<head>','<head><base href="../">');
fs.writeFileSync(preview,html);
const mime={'.html':'text/html; charset=utf-8','.png':'image/png','.svg':'image/svg+xml','.pdf':'application/pdf'};
const server=http.createServer((req,res)=>{
 const local=path.resolve(base,'.'+decodeURIComponent(new URL(req.url,'http://localhost').pathname));
 if(!local.startsWith(base+path.sep)||!fs.existsSync(local)){res.writeHead(404);res.end();return;}
 res.setHeader('Content-Type',mime[path.extname(local)]||'text/plain');fs.createReadStream(local).pipe(res);
});
(async()=>{
 await new Promise(r=>server.listen(0,'127.0.0.1',r));
 let browser;try{browser=await chromium.launch({headless:true});}catch{browser=await chromium.launch({headless:true,channel:'msedge'});}
 try{
  const page=await browser.newPage({viewport:{width:1250,height:950},deviceScaleFactor:1});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(`http://127.0.0.1:${server.address().port}/tmp/vista_previa.html`,{waitUntil:'networkidle'});
  await page.evaluate(async()=>{if(window.MathJax?.Hub)await new Promise(r=>MathJax.Hub.Queue(r));});
  const imagenes=await page.locator('img').evaluateAll(es=>es.map(e=>({src:e.getAttribute('src')?.slice(0,160),ok:e.complete&&e.naturalWidth>0})));
  const sections=await page.locator('h3').allTextContents();
  const mathErrors=await page.locator('.MathJax_Error,.mjx-merror,merror').allTextContents();
  for(let i=0;i<3;i++){
   await page.locator('h3').filter({hasText:'Simulación en LTspice'}).nth(i).locator('..').screenshot({path:path.join(__dirname,`revision_LTspice_final_${i+1}.png`)});
   await page.locator('.jp-CodeCell').filter({hasText:`graficar_transferencia(${i+1},`}).first().screenshot({path:path.join(__dirname,`revision_python_final_${i+1}.png`)});
  }
  const fallos=imagenes.filter(i=>!i.ok);
  const capturas=imagenes.filter(i=>i.src.startsWith('./Imagenes/Ej'));
  const order=sections.filter(s=>/Curvas en Python|Simulación en LTspice|Conclusión/.test(s));
  console.log(JSON.stringify({imagenes:imagenes.length,capturasLTspice:capturas.length,fallos,mathErrors,errors,order},null,2));
  if(fallos.length||mathErrors.length||errors.length||capturas.length!==16)process.exitCode=1;
 }finally{await browser.close();server.close();}
})().catch(e=>{console.error(e);server.close();process.exitCode=1;});
