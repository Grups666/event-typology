const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const path=require('node:path');
(async()=>{
  const browser=await chromium.launch({channel:'chrome',headless:true});
  try {
    const page=await browser.newPage({viewport:{width:1440,height:1000}});
    await page.goto(process.env.ATLAS_URL||'http://127.0.0.1:8873/');
    await page.waitForFunction(()=>!!window.EventTypologyModule && document.getElementById('atlasCount')?.textContent.includes('4,838'));
    const result=await page.evaluate(()=>{
      const m=new window.EventTypologyModule(App,{id:'test'});
      const vp={width:200,height:200,scale:0.5,offsetX:0,offsetY:0};
      const radii=[1,2,4,16,256].map(z=>m.markerRadius({...vp,scale:0.5*z}));
      const canvas=document.createElement('canvas');canvas.width=200;canvas.height=200;
      const ctx=canvas.getContext('2d');
      m.rows=[{GCIN:1,longitude:0,latitude:0,primary_event_type:'Rain-Mod',event_type_with_percentiles:'Rain-Mod:46.4 & Rain-Wet:41.1'}];
      m.render(ctx,{...vp,scale:8});
      const pixels=ctx.getImageData(100,100,8,1).data;
      return {radii,alpha:Array.from({length:8},(_,i)=>pixels[i*4+3]),center:Array.from(pixels.slice(0,3)),outer:Array.from(pixels.slice(28,31))};
    });
    assert.deepEqual(result.radii,[2.5,4.1,5.7,8.9,10]);
    assert(result.alpha.every(a=>a===255),'Gap inside concentric symbol');
    assert.deepEqual(result.center,[255,129,47]);assert.deepEqual(result.outer,[235,51,46]);
    await page.screenshot({path:path.resolve('../qa/symbols-global.png')});
    await page.evaluate(()=>{
      App.viewport.scale=4;
      const base=App.getBaseScale();
      App.viewport.offsetX=111*base;App.viewport.offsetY=34*base;
      App.clampOffset();App.draw();
    });
    await page.waitForTimeout(200);
    await page.screenshot({path:path.resolve('../qa/symbols-regional.png')});
    await page.setViewportSize({width:390,height:844});
    await page.goto((process.env.ATLAS_URL||'http://127.0.0.1:8873/')+'?season=dormant&metric=type');
    await page.waitForFunction(()=>document.getElementById('atlasCount')?.textContent.includes('4,838'));
    await page.waitForTimeout(400);
    await page.screenshot({path:path.resolve('../qa/symbols-mobile.png')});
    console.log('PASS: zoom radii, contiguous opaque ring, primary/secondary colors, global/regional/mobile screenshots',result);
  } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exit(1);});
