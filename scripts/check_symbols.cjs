const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const path=require('node:path');
(async()=>{
  const browser=await chromium.launch({channel:'chrome',headless:true});
  try {
    const page=await browser.newPage({viewport:{width:1440,height:1000}});
    await page.goto(process.env.ATLAS_URL||'http://127.0.0.1:8873/');
    await page.waitForFunction(()=>!!window.EventTypologyModule && document.getElementById('atlasCount')?.textContent.includes('4,838'));
    const result=await page.evaluate(async()=>{
      const m=new window.EventTypologyModule(App,{id:'test'});
      m.colors=await (await fetch('./modules/event-typology/colors.json')).json();
      const vp={width:200,height:200,scale:0.5,offsetX:0,offsetY:0};
      const radii=[1,2,4,16,256].map(z=>m.markerRadius({...vp,scale:0.5*z}));
      const canvas=document.createElement('canvas');canvas.width=200;canvas.height=200;
      const ctx=canvas.getContext('2d');
      m.rows=[{GCIN:1,longitude:0,latitude:0,primary_event_type:'Rain-Mod',event_type_with_percentiles:'Rain-Mod:46.4 & Rain-Wet:41.1'}];
      m.render(ctx,{...vp,scale:8});
      const pixels=ctx.getImageData(100,100,8,1).data;
      m.rows=[{GCIN:1,longitude:0,latitude:0},{GCIN:2,longitude:1,latitude:0}];
      const overlap=m.hit(0,0,vp).GCIN;
      m.selected=1;
      const selected=m.hit(0,0,vp).GCIN;
      const wrapped=m.hit(-720,0,vp).GCIN;
      return {radii,overlap,selected,wrapped,alpha:Array.from({length:8},(_,i)=>pixels[i*4+3]),center:Array.from(pixels.slice(0,3)),outer:Array.from(pixels.slice(28,31))};
    });
    assert.deepEqual(result.radii,[2.5,4.1,5.7,8.9,10]);
    assert.equal(result.overlap,2);assert.equal(result.selected,1);assert.equal(result.wrapped,1);
    assert(result.alpha.every(a=>a===255),'Gap inside concentric symbol');
    assert.deepEqual(result.center,[255,102,0]);assert.deepEqual(result.outer,[204,0,0]);
    await page.screenshot({path:path.resolve('../qa/symbols-global.png')});
    await page.evaluate(()=>{
      App.viewport.scale=4;
      const base=App.getBaseScale();
      App.viewport.offsetX=111*base;App.viewport.offsetY=34*base;
      App.clampOffset();App.draw();
    });
    await page.waitForTimeout(200);
    await page.screenshot({path:path.resolve('../qa/symbols-regional.png')});
    const canada=await page.evaluate(async()=>{
      const data=await (await fetch('./modules/event-typology/dormant.json')).json();
      const row=data.find(r=>r.GCIN===4375);
      App.viewport.scale=5;
      const base=App.getBaseScale();
      App.viewport.offsetX=123*base;App.viewport.offsetY=55*base;
      App.clampOffset();App.draw();
      return row;
    });
    assert(Math.abs(canada.longitude-(-125.60630063506937))<1e-8);
    assert(Math.abs(canada.latitude-59.47715140197454)<1e-8);
    assert.equal(canada.primary_event_type,'Rain-Wet');
    await page.waitForTimeout(200);
    await page.screenshot({path:path.resolve('../qa/paper-canada-centroids.png')});
    await page.setViewportSize({width:390,height:844});
    await page.goto((process.env.ATLAS_URL||'http://127.0.0.1:8873/')+'?season=dormant&metric=type');
    await page.waitForFunction(()=>document.getElementById('atlasCount')?.textContent.includes('4,838'));
    await page.waitForTimeout(400);
    await page.screenshot({path:path.resolve('../qa/symbols-mobile.png')});
    console.log('PASS: zoom radii, contiguous opaque ring, primary/secondary colors, global/regional/mobile screenshots',result);
  } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exit(1);});
