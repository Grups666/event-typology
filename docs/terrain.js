window.AtlasTerrain = {
  image: null,
  ready: false,
  load(redraw) {
    this.image = new Image();
    this.image.onload = () => { this.ready = true; redraw(); };
    this.image.onerror = () => console.warn('Terrain unavailable; using vector basemap.');
    this.image.src = './assets/earth-relief.webp';
  },
  render(ctx, app, viewport) {
    const {width,height,offsetX,offsetY} = viewport;
    const base = app.getBaseScale();
    const left = (-width/2-offsetX)/base;
    const right = (width/2-offsetX)/base;
    ctx.save();
    if (this.ready) {
      ctx.globalAlpha = 0.16;
      ctx.imageSmoothingEnabled = true;
      for (let seg=Math.ceil((left-180)/360);seg<=Math.floor((right+180)/360);seg++) {
        ctx.drawImage(this.image,width/2+(-180+seg*360)*base+offsetX,
          height/2-90*base+offsetY,360*base,180*base);
      }
    }
    ctx.globalAlpha = 1;
    ctx.strokeStyle = 'rgba(65,82,90,0.20)';
    ctx.lineWidth = 0.6;
    for (let seg=Math.floor(left/360);seg<=Math.ceil(right/360);seg++) {
      for (const country of window.COUNTRY_POLYGONS_110M || []) {
        ctx.stroke(app.createCountryPath(country,seg*360,base,width,height,offsetX,offsetY));
      }
    }
    ctx.restore();
  }
};
