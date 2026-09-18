const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const path=require('node:path');
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true});
 try {
  for(const width of [1440,390]) {
   const page=await browser.newPage({viewport:{width,height:900}});
   const errors=[];page.on('pageerror',e=>errors.push(e.message));
   await page.goto(process.env.ATLAS_URL||'http://127.0.0.1:8873/');
   await page.waitForFunction(()=>window.AtlasTerrain?.ready && AtlasTerrain.borders.length>0 && document.getElementById('atlasCount')?.textContent.includes('4,838'));
   await page.waitForTimeout(350);
   const results=await page.evaluate(()=>{
    const checks=[];
    for(const scale of [0.01,1,2,6]) for(const y of [-1e6,0,1e6]) {
     App.viewport.scale=scale;App.viewport.offsetY=y;App.clampOffset();
     const b=App.getBaseScale(),v=App.viewport;
     checks.push({north:v.height/2-90*b+v.offsetY,south:v.height/2+90*b+v.offsetY,height:v.height});
    }
    document.getElementById('btnReset').click();
    return checks;
   });
   for(const r of results){assert(r.north<=0);assert(r.south>=r.height);}
   await page.waitForTimeout(200);
   await page.screenshot({path:path.resolve(`../qa/terrain-${width}.png`)});
   const diff=await page.evaluate(()=>{
    const ctx=App.ctx,c=App.canvas;
    App.drawNow();const before=ctx.getImageData(0,0,c.width,c.height).data;
    AtlasTerrain.ready=false;App.drawNow();const after=ctx.getImageData(0,0,c.width,c.height).data;
    AtlasTerrain.ready=true;App.drawNow();let changed=0;
    for(let i=0;i<before.length;i+=4)if(Math.abs(before[i]-after[i])>3)changed++;
    return changed;
   });
   assert(diff>1000,'Terrain not visible');assert.deepEqual(errors,[]);
   console.log('PASS: polar bounds at all zooms, relief pixels, width',width,diff);
   await page.close();
  }
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
