window.EventTypologyModule = class EventTypologyModule {
  constructor(app, manifest) {
    this.app = app;
    this.manifest = manifest;
    this.id = manifest.id;
    this.season = 'dormant';
    this.metric = 'type';
    this.country = '';
    this.consistent = false;
    this.selected = null;
    this.colors = {};
    this.params = new URLSearchParams(location.search);
  }
  async onLoad() {
    const base = new URL(this.manifest.basePath || './modules/event-typology/', location.href);
    const palette=await fetch(new URL('colors.json',base));
    if(!palette.ok)throw new Error(`Catchment palette: ${palette.status}`);
    this.colors=await palette.json();
    this.data = {};
    await Promise.all(['dormant','growing'].map(async season => {
      const res = await fetch(new URL(`${season}.json`, base));
      if (!res.ok) throw new Error(`Catchment data: ${res.status}`);
      this.data[season] = await res.json();
    }));
    this.byId = Object.fromEntries(Object.entries(this.data).map(([s,rows]) => [s,new Map(rows.map(r => [r.GCIN,r]))]));
    this.season = this.params.get('season') === 'growing' ? 'growing' : 'dormant';
    const countries = [...new Set(this.data.dormant.map(r => r.country))].sort();
    this.country = countries.includes(this.params.get('country')) ? this.params.get('country') : '';
    this.consistent = this.params.get('ci') === 'high';
    document.getElementById('atlasControls').innerHTML = `
      <h1>Event Typology</h1><p class="subtitle">Global catchment atlas<br>Ying Yan, Hamed Sharif &amp; Ali A. Ameli</p>
      <div class="seasons" aria-label="Season"><button data-season="dormant">Dormant</button><button data-season="growing">Growing</button></div>
      <label for="atlasCountry">Country</label><select id="atlasCountry"><option value="">All countries</option>${countries.map(c=>`<option value="${c}">${this.countryName(c)}</option>`).join('')}</select>
      <label class="check"><input id="atlasCI" type="checkbox"> High consistency (CI &gt; 0.9)</label>
      <label for="atlasSearch">Catchment GCIN</label><input id="atlasSearch" type="search" inputmode="numeric" placeholder="Search GCIN" autocomplete="off"><div class="atlas-results" id="atlasResults"></div>
      <p class="atlas-count" id="atlasCount" role="status"></p>
      <div class="links"><a href="https://doi.org/10.1038/s43247-026-04079-6" target="_blank" rel="noopener">Paper</a><a href="https://github.com/Grups666/event-typology" target="_blank" rel="noopener">Code</a><a href="#" id="atlasDownload">CSV</a></div>`;
    document.querySelectorAll('[data-season]').forEach(b => b.onclick = () => {this.season=b.dataset.season; this.update();});
    document.getElementById('atlasCountry').value=this.country;
    document.getElementById('atlasCountry').onchange=e=>{this.country=e.target.value;this.update();this.fitCountry();};
    document.getElementById('atlasCI').checked=this.consistent;
    document.getElementById('atlasCI').onchange=e=>{this.consistent=e.target.checked;this.update();};
    document.getElementById('atlasSearch').oninput=()=>this.search();
    document.getElementById('atlasDownload').onclick=e=>{e.preventDefault();this.download();};
    this.app.layerManager.addLayer({id:this.id,name:'Study catchments',moduleId:this.id,interactive:true,
      renderer:(ctx,layer,vp)=>this.render(ctx,vp),hitTest:(lon,lat,vp)=>this.hit(lon,lat,vp)});
    this.unsubscribe=Foundation.eventBus.on(Foundation.Events.FEATURE_CLICK,p=>{if(p.layer?.id===this.id)this.inspect(p.feature.GCIN);});
    this.update();
    if(innerWidth<700)document.getElementById('leftPanel').classList.add('hidden');
    if(this.country)this.fitCountry();
    const id=Number(this.params.get('gcin'));
    if(this.byId[this.season].has(id))this.focus(this.byId[this.season].get(id));
  }
  countryName(c) {try{return new Intl.DisplayNames(['en'],{type:'region'}).of(c);}catch{return c;}}
  escape(s) {return this.app.escape(s);}
  label(s) {return String(s||'Unclassified').replace(/-Mod\b/g,'-Moderate');}
  ring(row) {
    // Match the paper plotter using the exported classification, not rounded CI.
    const parts=String(row.event_type_with_percentiles||'').split(' & ');
    if(parts.length<2)return this.colors[row.primary_event_type]||'#888888';
    const [type,percent]=parts[1].split(':');
    return Number(percent)>=25?(this.colors[type]||'#666666'):'#666666';
  }
  color(row) {
    return this.colors[row.primary_event_type]||'#888888';
  }
  update() {
    this.rows=this.data[this.season].filter(r=>(!this.country||r.country===this.country)&&(!this.consistent||r.consistency_index>0.9));
    document.querySelectorAll('[data-season]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.season===this.season)));
    document.getElementById('atlasCount').textContent=`${this.rows.length.toLocaleString()} / ${this.data[this.season].length.toLocaleString()} catchments`;
    let html;
    if(this.metric==='type') {
      const types=[...new Set(this.rows.flatMap(r=>[r.primary_event_type,...String(r.event_type_with_percentiles||'').split(' & ').slice(1).filter(p=>Number(p.split(':')[1])>=25).map(p=>p.split(':')[0])]))];
      const ordered=[...Object.keys(this.colors),...types.filter(t=>!this.colors[t])].filter(t=>types.includes(t));
      html=`<div class="atlas-legend">${ordered.map(t=>`<span class="atlas-swatch" style="background:${this.colors[t]||'#888'}"></span><span>${this.escape(this.label(t))}</span>`).join('')}</div>`;
      html+='<div class="atlas-ring-key"><span class="atlas-ring-symbol"></span><span>Inner: primary type<br>Outer: secondary type<br>Gray outer: secondary &lt; 25%</span></div>';
    }
    this.app.registerLegend(this.id,{title:'Hydro-meteorological type',html});
    const query=new URLSearchParams(location.search);query.set('season',this.season);query.set('metric',this.metric);
    this.country?query.set('country',this.country):query.delete('country');this.consistent?query.set('ci','high'):query.delete('ci');
    history.replaceState(null,'',`${location.pathname}?${query}`);
    if(this.selected!==null)this.inspect(this.selected);
    this.search();this.app.draw();
  }
  markerRadius(vp) {
    const worldScale=Math.min(1, vp.width/(2*vp.height));
    const zoom=Math.max(1,vp.scale/worldScale);
    return Math.min(10,2.5+1.6*Math.log2(zoom));
  }
  orderedRows() {
    const rows=this.rows||[];
    return this.selected===null?rows:[...rows.filter(r=>r.GCIN!==this.selected),...rows.filter(r=>r.GCIN===this.selected)];
  }
  render(ctx,vp) {
    const base=vp.height/180*vp.scale;
    const left=(-vp.width/2-vp.offsetX)/base,right=(vp.width/2-vp.offsetX)/base;
    const radius=this.markerRadius(vp);
    ctx.save();
    for(const row of this.orderedRows()) {
      const y=vp.height/2-row.latitude*base+vp.offsetY;if(y<-radius-3||y>vp.height+radius+3)continue;
      for(let seg=Math.ceil((left-row.longitude)/360);seg<=Math.floor((right-row.longitude)/360);seg++) {
        const x=vp.width/2+(row.longitude+seg*360)*base+vp.offsetX;
        if(this.metric==='type') {
          // Overlaid filled disks keep the secondary ring flush with the primary disk.
          ctx.beginPath();ctx.arc(x,y,radius,0,Math.PI*2);ctx.fillStyle=this.ring(row);ctx.fill();
          ctx.beginPath();ctx.arc(x,y,radius*0.68,0,Math.PI*2);ctx.fillStyle=this.color(row);ctx.fill();
        }
        if(row.GCIN===this.selected){ctx.beginPath();ctx.arc(x,y,radius+2,0,Math.PI*2);ctx.strokeStyle='#111';ctx.lineWidth=1.4;ctx.stroke();}
      }
    }
    ctx.restore();
  }
  hit(lon,lat,vp) {
    const base=vp.height/180*vp.scale,radius=this.markerRadius(vp);
    let best=null,dist=Math.max(9,radius+2)**2;
    const rows=this.orderedRows();
    // The last-painted disk owns overlapping pixels; proximity is only a fallback.
    for(let i=rows.length-1;i>=0;i--) {
      const row=rows[i];
      const dx=((((lon-row.longitude+180)%360+360)%360)-180)*base,dy=(lat-row.latitude)*base,d=dx*dx+dy*dy;
      if(d<=radius*radius)return row;
      if(d<dist){dist=d;best=row;}
    }
    return best;
  }
  inspect(id) {
    this.selected=id;
    const fmt=v=>v===null||v===undefined?'No data':Number(v).toFixed(3);
    const d=this.byId.dormant.get(id),g=this.byId.growing.get(id),r=this.byId[this.season].get(id)||d||g;
    const row=(title,key,format=fmt)=>`<tr><th>${title}</th><td>${d?format(d[key]):'No data'}</td><td>${g?format(g[key]):'No data'}</td></tr>`;
    this.app.showInspector(`GCIN ${id}`,`<h2>${this.escape(this.countryName(r.country))}</h2><p>${r.latitude.toFixed(4)}, ${r.longitude.toFixed(4)}</p><table class="atlas-table"><thead><tr><th>Season</th><th>Dormant</th><th>Growing</th></tr></thead><tbody>${row('Primary type','primary_event_type',v=>this.escape(this.label(v)))}${row('Secondary type','secondary_event_type',v=>this.escape(this.label(v)))}${row('Consistency','consistency_index')}${row('Daily coherence','WI-Q_daily')}${row('Weekly coherence','WI-Q_weekly')}</tbody></table>`);
    const q=new URLSearchParams(location.search);q.set('gcin',id);history.replaceState(null,'',`${location.pathname}?${q}`);this.app.draw();
  }
  search() {
    const input=document.getElementById('atlasSearch'),el=document.getElementById('atlasResults');if(!input)return;
    const term=input.value.trim();el.replaceChildren();if(!term)return;
    const matches=this.rows.filter(r=>String(r.GCIN).includes(term)).sort((a,b)=>(String(b.GCIN)===term)-(String(a.GCIN)===term)).slice(0,20);
    if(!matches.length){el.textContent='No matching catchments';return;}
    for(const r of matches){const b=document.createElement('button');b.textContent=`${r.GCIN} · ${this.countryName(r.country)}`;b.onclick=()=>this.focus(r);el.append(b);}
  }
  focus(r) {
    this.app.viewport.scale=5;const base=this.app.getBaseScale();this.app.viewport.offsetX=-r.longitude*base;this.app.viewport.offsetY=r.latitude*base;this.app.clampOffset();this.inspect(r.GCIN);
    if(innerWidth<700)document.getElementById('leftPanel').classList.add('hidden');
  }
  fitCountry() {
    if(!this.rows.length)return;
    if(!this.country){document.getElementById('btnReset').click();return;}
    const xs=this.rows.map(r=>r.longitude),ys=this.rows.map(r=>r.latitude),xmin=Math.min(...xs),xmax=Math.max(...xs),ymin=Math.min(...ys),ymax=Math.max(...ys),vp=this.app.viewport;
    vp.scale=Math.max(this.app.getMinViewportScale(),Math.min(8,180/Math.max(ymax-ymin+12,(xmax-xmin+12)*vp.height/vp.width)));
    const base=this.app.getBaseScale();vp.offsetX=-(xmin+xmax)/2*base;vp.offsetY=(ymin+ymax)/2*base;this.app.clampOffset();this.app.draw();
  }
  download() {
    const fields=Object.keys(this.data[this.season][0]);const cell=v=>'"'+String(v??'').replace(/"/g,'""')+'"';
    const csv=[fields.map(cell).join(','),...this.rows.map(r=>fields.map(k=>cell(r[k])).join(','))].join('\r\n');
    const url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download=`event-typology-${this.season}.csv`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  getLayerIds(){return [this.id];}
  onUnload(){this.unsubscribe?.();this.app.unregisterLegend(this.id);this.app.layerManager.removeLayer(this.id);document.getElementById('atlasControls').replaceChildren();}
};
