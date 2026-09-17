"""Build the paper's static Tereon site from an explicitly selected data release."""
import argparse
import csv
import hashlib
import json
import math
import shutil
import subprocess
from pathlib import Path
from paper_symbols import paper_symbols

parser = argparse.ArgumentParser()
parser.add_argument('--template', type=Path, required=True)
parser.add_argument('--data', type=Path, required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
site = root / 'docs'
shutil.copytree(args.template / 'public', site, dirs_exist_ok=True)
html = (site / 'index.html').read_text(encoding='utf-8')
html = html.replace('<title>Tereon</title>', '<title>Event Typology | Global Catchment Atlas</title>')
html = html.replace('</head>', '<link rel="stylesheet" href="./atlas.css">\n</head>')
html = html.replace('staticModules: [],', 'staticModules: [{id: "event-typology", name: "Event Typology", defaultLoad: true}],')
html = html.replace('return 180 / this.getWorldLatitudeSpan();', 'return Math.min(180 / this.getWorldLatitudeSpan(), 180 * this.viewport.width / (360 * this.viewport.height));')
html = html.replace('viewport: { width: 0, height: 0, scale: 1, offsetX: 0, offsetY: 0 }', 'viewport: { width: 0, height: 0, scale: 0, offsetX: 0, offsetY: 0 }')
html = html.replace('`${lon.toFixed(1)} deg, ${lat.toFixed(1)} deg`', 'Math.abs(lat) > 90 ? "--" : `${(((lon + 180) % 360 + 360) % 360 - 180).toFixed(1)} deg, ${lat.toFixed(1)} deg`')
# Keep the graticule and layers inside real geographic latitude bounds.
html = html.replace('        // Background\n', '''        ctx.fillStyle = this.themeStyle === 'dark' ? '#18212b' : '#ffffff';
        ctx.fillRect(0, 0, width, height);
        ctx.save();
        const northY = height / 2 - 90 * this.getBaseScale() + viewport.offsetY;
        const southY = height / 2 + 90 * this.getBaseScale() + viewport.offsetY;
        ctx.beginPath();
        ctx.rect(0, northY, width, southY - northY);
        ctx.clip();
        // Background
''')
html = html.replace('        viewport.interacting = false;', '        ctx.restore();\n        viewport.interacting = false;')
# Polar and antimeridian polygon closures are not physical coastlines.
basemap_start = html.index('      renderBasemap(ctx, viewport) {')
basemap_end = html.index('      renderRasterTiles(', basemap_start)
basemap = html[basemap_start:basemap_end]
basemap = basemap.replace('            ctx.stroke(path);', '''            const coast = new Path2D();
            for (let i = 0; i < ring.length; i++) {
              const [lon, lat] = ring[i];
              const previous = ring[Math.max(0, i - 1)];
              const closure = lat <= -89.99 || previous[1] <= -89.99 ||
                (Math.abs(lon) >= 179.99 && Math.abs(previous[0]) >= 179.99);
              const x = width / 2 + (lon + lonOffset) * base + offsetX;
              const y = height / 2 - lat * base + offsetY;
              if (i === 0 || closure) coast.moveTo(x, y);
              else coast.lineTo(x, y);
            }
            ctx.stroke(coast);''')
html = html[:basemap_start] + basemap + html[basemap_end:]
start = html.index('      async fetchModules() {')
end = html.index('      async loadDefaultModules()', start)
html = html[:start] + '      async fetchModules() { this.modules = this.staticModules; this.updateModuleList(); },\n\n' + html[end:]
html = html.replace('<div class="panel-main">', '<div class="panel-main"><section id="atlasControls" class="atlas-controls"><h1>Event Typology</h1><p role="status">Loading catchment data...</p></section>')
html = html.replace('App.init();', 'App.init().catch(error => { document.getElementById("atlasControls").textContent = "Unable to load atlas. Please reload the page."; console.error(error); });')
(site / 'index.html').write_text(html.rstrip() + '\n', encoding='utf-8')
(site / '.nojekyll').touch()
out = site / 'modules' / 'event-typology'
out.mkdir(parents=True, exist_ok=True)
fields = ['GCIN', 'country', 'longitude', 'latitude', 'primary_event_type', 'secondary_event_type', 'event_type_with_percentiles', 'consistency_index', 'WI-Q_daily', 'WI-Q_weekly']
numeric = {'GCIN', 'longitude', 'latitude', 'consistency_index', 'WI-Q_daily', 'WI-Q_weekly'}
report = {'template_commit': subprocess.check_output(['git', '-C', str(args.template), 'rev-parse', 'HEAD'], text=True).strip(), 'sources': {}}
for season, expected in [('dormant', 4838), ('growing', 4797)]:
    source = args.data / f'metadata_{season}.csv'
    rows = []
    for record in csv.DictReader(source.open(encoding='utf-8-sig')):
        row = {k: record[k] for k in fields}
        for k in numeric:
            row[k] = float(row[k]) if row[k] else None
            if row[k] is not None and not math.isfinite(row[k]):
                row[k] = None
        row['GCIN'] = int(row['GCIN'])
        assert row['longitude'] is not None and row['latitude'] is not None
        rows.append(row)
    assert len(rows) == expected and len({r['GCIN'] for r in rows}) == expected
    coordinates, colors, geometry_source = paper_symbols(root, args.data, {r['GCIN'] for r in rows})
    for row in rows:
        row['longitude'], row['latitude'] = coordinates[row['GCIN']]
    (out / f'{season}.json').write_text(json.dumps(rows, separators=(',', ':'), allow_nan=False), encoding='utf-8')
    (out / 'colors.json').write_text(json.dumps(colors, indent=2), encoding='utf-8')
    report['sources'][source.name] = {'sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'catchments': len(rows)}
    report.setdefault('map_coordinates', {})[season] = geometry_source
(out / 'provenance.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report, indent=2))
