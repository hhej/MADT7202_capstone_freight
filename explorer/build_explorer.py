"""Build explorer/index.html: template.html + calc.js + one inlined DATA blob from data/ and results/.
Run from the repo root after the notebook and deck/build_deck.py:  python explorer/build_explorer.py
"""
import json, re
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RES, DATA, EXP = ROOT / 'results', ROOT / 'data', ROOT / 'explorer'
src = (ROOT / 'deck' / 'build_deck.py').read_text(encoding='utf-8')
ns = {}
exec(src[src.index('EN = dict('):src.index('en = lambda')], ns)  # reuse EN, PROD, GROUP, GCOL from the deck builder
EN, PROD, GROUP, GCOL = ns['EN'], ns['PROD'], ns['GROUP'], ns['GCOL']
products = list(PROD)  # Thai keys, fixed order
rd = lambda f, **k: pd.read_csv(RES / f, encoding='utf-8-sig', **k)

D = pd.read_csv(DATA / 'straight_line_distance_km.csv', index_col=0); nodes = list(D.index); ix = {v: i for i, v in enumerate(nodes)}
coords = pd.read_csv(DATA / 'province_coordinates_used.csv').set_index('province').loc[nodes]
raw = pd.read_csv(DATA / 'otp_69_01_69.csv')
for c in ['product', 'province_origin', 'province_destination', 'month']: raw[c] = raw[c].astype(str).str.strip()
d = raw[raw['product'].isin(products) & raw.province_origin.ne(raw.province_destination)].copy()
d['shipping'] = pd.to_numeric(d.shipping)
fl = d.groupby(['province_origin', 'province_destination', 'product'], as_index=False).agg(trips=('trips', 'sum'), tons=('shipping', 'sum'))
flows = [[ix[r.province_origin], ix[r.province_destination], products.index(r.product), int(r.trips), int(round(r.tons))] for r in fl.itertuples()]

cc = rd('community_coverage.csv'); grp = {v.strip(): int(r.community) for _, r in cc[cc.model == 'A_3'].iterrows() for v in r.members.split(' / ')}
conf = rd('community_confidence.csv').set_index('province').confidence
cent = rd('centrality_directed.csv').set_index('province')
node_rows = [dict(en=EN[v], th=v, lat=round(float(coords.LAT[v]), 4), lng=round(float(coords.LNG[v]), 4), g=grp[v], conf=round(float(conf[v]), 3),
                  partners=int(cent.partners[v]), pr=round(float(cent.pagerank[v]), 5), btw=round(float(cent.betweenness[v]), 4), bridge=int(cent.bridge_trips[v]))
             for v in nodes]
models = rd('models.csv').set_index('model')
hubs = lambda s: [ix[x.strip()] for x in s.split(' / ')]
enset = lambda s: ' / '.join(EN[x.strip()] for x in s.split(' / '))

def recs(df):
    return json.loads(df.to_json(orient='records', force_ascii=False))

seed = rd('seeding.csv'); seed['hubs'] = seed.hubs.fillna('').map(lambda s: enset(s) if s else '')
rad = rd('sensitivity_radius.csv'); rad['hubs_idx'] = rad.hubs.map(hubs); rad['hubs'] = rad.hubs.map(enset)
near = rd('near_optimal.csv'); near['hubs'] = near.hubs.map(enset)
lane = rd('lane_coverage.csv'); lane['hubs'] = lane.hubs.map(enset)
temporal = rd('temporal.csv')
month_en = {'มกราคม': 'Jan 2026', 'กุมภาพันธ์': 'Feb 2026', 'มีนาคม': 'Mar 2026', 'เมษายน': 'Apr 2026', '2025_matched': '2025 (Jan, Mar, Apr)',
            '2026_matched': '2026 (Jan, Mar, Apr)', '2025_matched_dedup': '2025 without duplicates'}
temporal['period'] = temporal.period.map(month_en)
fp = rd('structure_fingerprint.csv', index_col=0).reset_index().rename(columns={'index': 'measure'})
stress = json.loads((ROOT / 'docs' / 'stress_results.json').read_text())

# Neo4j competency questions, answered from the same data as Freight_GraphDB_Neo4j.ipynb
A = D.values <= 150; a3 = hubs(models.sites['A_3'])
T = np.zeros((77, 77)); P = {}
for o, de, p, t, _ in flows: T[o, de] += t; P[(o, de, p)] = t
cov = A[:, a3].any(1)
def hub_of(i): return [nodes[j] for j in a3 if A[i, j]]
cq = {
 'backhaul': [dict(pickup=EN[h1], delivery=EN[h2], trips=int(sum(T[i, j] for i in range(77) if A[i, nodes.index(h1)] for j in range(77) if A[j, nodes.index(h2)])))
              for h1 in [nodes[j] for j in a3] for h2 in [nodes[j] for j in a3]],
 'destinations': {EN[nodes[h]]: [dict(dest=EN[nodes[j]], trips=int(T[A[:, h], j].sum()), near_hub=bool(cov[j])) for j in np.argsort(-T[A[:, h]].sum(0))[:5]] for h in a3},
 'molasses': sorted([dict(hub=EN[hub_of(o)[0]], origin=EN[nodes[o]], dest=EN[nodes[de]], trips=t) for (o, de, p), t in P.items() if p == products.index('กากน้ำตาล') and cov[o]], key=lambda r: -r['trips'])[:5],
 'unreached': [dict(province=EN[nodes[i]], group=GROUP[grp[nodes[i]]], trips=int(T[i].sum())) for i in np.argsort(-T.sum(1)) if not cov[i]][:6],
 'ports': sorted([dict(origin=EN[nodes[i]], port=EN[nodes[j]], trips=int(T[i, j])) for i in range(77) if cov[i] for j in [ix['ชลบุรี'], ix['สมุทรปราการ']] if T[i, j] > 0], key=lambda r: -r['trips'])[:6],
}
cq['backhaul'].sort(key=lambda r: -r['trips'])

DATA_OUT = dict(
 nodes=node_rows, products=[PROD[p] for p in products], flows=flows, dist=np.round(D.values, 4).tolist(), groups=[GROUP[g] for g in range(4)], gcol=GCOL,
 models={k: hubs(models.sites[k]) for k in ['A_2', 'A_3', 'B_3_0.5']},
 seeding=recs(seed), radius=recs(rad), near=recs(near), lane=recs(lane), temporal=recs(temporal), fingerprint=recs(fp),
 check2=recs(rd('check2_baselines.csv')), cross=recs(rd('community_cross_check.csv')), resolution=recs(rd('resolution.csv')),
 null_weight=rd('null.csv').null_Q.round(4).tolist(), null_topo=rd('null_course.csv').topology_only_Q.round(4).tolist(),
 road=rd('road_calibration.csv', index_col=0)['value'].to_dict(), stress=stress, facts=json.loads((ROOT / 'deck' / 'facts.json').read_text()),
 audit=recs(rd('audit.csv')), cq=cq, months=int(d.month.nunique()),
 outline=json.loads((EXP / 'thailand_outline.json').read_text()),  # Natural Earth borders, see make_outline.py
 obs_topo=stress['2_check2_1000']['observed_Q'], obs_Q=json.loads((RES / 'summary.json').read_text())['observed_Q'],
)
blob = json.dumps(DATA_OUT, ensure_ascii=False, separators=(',', ':'))
(EXP / 'data.json').write_text(blob, encoding='utf-8')
html = (EXP / 'template.html').read_text(encoding='utf-8')
html = html.replace('/*__CALC__*/', (EXP / 'calc.js').read_text(encoding='utf-8')).replace('/*__DATA__*/', 'const DATA = ' + blob.replace('</', '<\\/') + ';')
(EXP / 'index.html').write_text(html, encoding='utf-8')
print('explorer/index.html', round(len(html.encode()) / 1024), 'KB;', len(flows), 'flows')
