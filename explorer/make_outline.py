"""Extract Thailand and its neighbours from Natural Earth country borders (world-atlas countries-50m.json, public domain data)
into explorer/thailand_outline.json, a small GeoJSON used as the map background.

Get the source once:  curl -L -o countries-50m.json https://cdn.jsdelivr.net/npm/world-atlas@2.0.2/countries-50m.json
Run:                  python explorer/make_outline.py countries-50m.json
"""
import json, sys
from pathlib import Path

KEEP = {'764': 'Thailand', '104': 'Myanmar', '418': 'Laos', '116': 'Cambodia', '458': 'Malaysia', '704': 'Vietnam'}
topo = json.loads(Path(sys.argv[1]).read_text())
(sx, sy), (tx, ty) = topo['transform']['scale'], topo['transform']['translate']

def decode(arc):
    x = y = 0; pts = []
    for dx, dy in arc:
        x += dx; y += dy; pts.append([round(x * sx + tx, 3), round(y * sy + ty, 3)])
    return pts

arcs = [decode(a) for a in topo['arcs']]

def ring(ids):
    out = []
    for k, i in enumerate(ids):
        pts = arcs[i] if i >= 0 else arcs[~i][::-1]
        out.extend(pts if k == 0 else pts[1:])
    return out

features = []
for g in topo['objects']['countries']['geometries']:
    if str(g.get('id')) not in KEEP: continue
    polys = [g['arcs']] if g['type'] == 'Polygon' else g['arcs']
    coords = [[ring(r) for r in poly] for poly in polys]
    features.append({'type': 'Feature', 'properties': {'name': KEEP[str(g['id'])]}, 'geometry': {'type': 'MultiPolygon', 'coordinates': coords}})
assert {f['properties']['name'] for f in features} == set(KEEP.values()), 'a country is missing from the source file'
out = Path(__file__).with_name('thailand_outline.json')
out.write_text(json.dumps({'type': 'FeatureCollection', 'features': features}, separators=(',', ':')))
print(out, round(out.stat().st_size / 1024), 'KB,', len(features), 'countries')
