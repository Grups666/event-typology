window.AtlasTerrain = {
  image: null,
  ready: false,
  borders: [],
  load(redraw) {
    this.image = new Image();
    this.image.onload = () => { this.ready = true; redraw(); };
    this.image.onerror = () => console.warn('Satellite image unavailable.');
    this.image.src = './assets/blue-marble.jpg';
    fetch('./assets/admin-boundaries.geojson').then(r=>{
      if(!r.ok)throw new Error('Boundary data unavailable');
      return r.json();
    }).then(data=>{
      this.borders=data.features.flatMap(f=>f.geometry.type==='LineString'?[f.geometry.coordinates]:f.geometry.coordinates).filter(line=>line.every(p=>p[1]>-60));
      redraw();
    }).catch(error=>console.warn(error.message));
  },
  render(ctx, app, viewport) {
    const {width,height,offsetX,offsetY} = viewport;
    const base = app.getBaseScale();
    const left = (-width/2-offsetX)/base;
    const right = (width/2-offsetX)/base;
    ctx.save();
    if (this.ready) {
      ctx.globalAlpha = 0.38;
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
      for (const line of this.borders) {
        ctx.beginPath();
        for(let i=0;i<line.length;i++) {
          const [lon,lat]=line[i];
          const x=width/2+(lon+seg*360)*base+offsetX,y=height/2-lat*base+offsetY;
          if(i===0||Math.abs(lon-line[i-1][0])>180)ctx.moveTo(x,y);
          else ctx.lineTo(x,y);
        }
        ctx.stroke();
      }
    }
    ctx.restore();
  }
};
