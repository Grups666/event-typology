const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const path=require('node:path');
(async()=>{
  const browser=await chromium.launch({channel:'chrome',headless:true});
  try {
    for(const width of [1440,1920,390]) {
      const page=await browser.newPage({viewport:{width,height:1000}});
      const errors=[];page.on('pageerror',e=>errors.push(e.message));
      await page.goto(process.env.ATLAS_URL||'http://127.0.0.1:8873/');
      await page.waitForFunction(()=>document.getElementById('atlasCount')?.textContent.includes('4,838'));
      await page.waitForTimeout(300);
      for(let cycle=0;cycle<3;cycle++) {
        if(await page.locator('#leftPanel').evaluate(el=>el.classList.contains('hidden')))
          await page.locator('#btnShowPanel').click();
        await page.waitForTimeout(250);
        const expectedLeft=width>700?260:0;
        assert.equal(await page.locator('.map-area').evaluate(el=>el.getBoundingClientRect().left),expectedLeft);
        await page.locator('#btnHidePanel').click();
        await page.waitForTimeout(250);
        const state=await page.evaluate(()=>{
          const rect=document.querySelector('.map-area').getBoundingClientRect();
          const canvas=document.getElementById('mapCanvas');
          const x=10,y=Math.round(App.viewport.height/2);
          const d=canvas.getContext('2d').getImageData(x,y,1,1).data;
          return {left:rect.left,width:rect.width,viewport:App.viewport.width,canvasWidth:canvas.width,
            expectedPixels:Math.round(innerWidth*devicePixelRatio),pixel:Array.from(d),
            statusLeft:document.querySelector('.map-status').getBoundingClientRect().left};
        });
        assert.equal(state.left,0);assert.equal(state.width,width);assert.equal(state.viewport,width);
        assert.equal(state.canvasWidth,state.expectedPixels);assert(state.statusLeft<30);
        assert.equal(state.pixel[3],255);
      }
      await page.screenshot({path:path.resolve(`../qa/sidebar-collapsed-${width}.png`)});
      assert.deepEqual(errors,[]);await page.close();
      console.log('PASS: repeated sidebar collapse/expand, full-width canvas',width);
    }
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
