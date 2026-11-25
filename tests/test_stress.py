"""Stress tests: independent re-implementation + robustness checks.

Nothing here imports notebook code. Each test recomputes from data/ and compares with results/.
Findings are written to docs/stress_results.json (pass or fail) so the write-up can quote them.
Run:  pytest -q tests/   (needs data/otp_69_01_6*.csv; see README)
"""
import json, math
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
import networkx as nx
import pytest

ROOT = Path(__file__).resolve().parents[1]
DATA, RES = ROOT / 'data', ROOT / 'results'
P = ['ข้าวเปลือก', 'ข้าว', 'น้ำตาลทราย', 'กากน้ำตาล', 'อาหารสัตว์', 'ข้าวโพด', 'ผลิตภัณฑ์มันสำปะหลัง']
REPORT = {}


def record(name, **kv):
    REPORT[name] = kv
    out = ROOT / 'docs' / 'stress_results.json'
    old = json.loads(out.read_text()) if out.exists() else {}
    old.update(REPORT)
    out.write_text(json.dumps(old, ensure_ascii=False, indent=2, default=float))


def load(year='69'):
    df = pd.read_csv(DATA / f'otp_69_01_{year}.csv')
    for c in ['product', 'month', 'province_origin', 'province_destination']:
        df[c] = df[c].astype(str).str.strip()
    return df


@pytest.fixture(scope='session')
def base():
    D = pd.read_csv(DATA / 'straight_line_distance_km.csv', index_col=0)
    nodes = list(D.index)
    raw = load('69')
    d = raw[raw['product'].isin(P) & raw.province_origin.ne(raw.province_destination)]
    return dict(D=D, nodes=nodes, raw=raw, d=d, n=len(nodes))


def flows(d, nodes):
    T = d.groupby(['province_origin', 'province_destination']).trips.sum().unstack().reindex(index=nodes, columns=nodes).fillna(0).values
    return T


def all_cov(w, Acov, k):
    S = np.array(list(combinations(range(len(w)), k)))
    return S, 100 * (w @ Acov[:, S].any(2)) / w.sum()


def best_set(w, Acov, k, nodes):
    S, c = all_cov(w, Acov, k)
    j = int(np.argmax(c))
    return frozenset(nodes[i] for i in S[j]), c[j], c


def ugraph(T, nodes):
    W = T + T.T
    g = nx.Graph()
    g.add_nodes_from(nodes)
    for i, j in zip(*np.triu_indices(len(nodes), 1)):
        if W[i, j] > 0:
            g.add_edge(nodes[i], nodes[j], weight=float(W[i, j]))
    return g


def best_louvain(g, seeds, weight='weight'):
    pp = [nx.community.louvain_communities(g, weight=weight, seed=s) for s in seeds]
    qq = [nx.community.modularity(g, p, weight=weight) for p in pp]
    return pp[int(np.argmax(qq))], max(qq), pp


def ari(a, b):
    from math import comb
    ct = pd.crosstab(a, b).values
    s = sum(comb(int(x), 2) for x in ct.ravel())
    ra, cb, n = sum(comb(int(x), 2) for x in ct.sum(1)), sum(comb(int(x), 2) for x in ct.sum(0)), comb(len(a), 2)
    e = ra * cb / n
    return (s - e) / ((ra + cb) / 2 - e)


def labels(part, nodes):
    m = {v: i for i, c in enumerate(part) for v in c}
    return np.array([m[v] for v in nodes])


A3 = frozenset(['พิษณุโลก', 'สระบุรี', 'มหาสารคาม'])
A2 = frozenset(['พิษณุโลก', 'สระบุรี'])


# ---------------------------------------------------------------- 1. independent re-implementation
def test_independent_reimplementation(base):
    D, nodes, d = base['D'], base['nodes'], base['d']
    T = flows(d, nodes)
    w = T.sum(1)
    A = (D.values <= 150).astype(float)
    s2, c2, _ = best_set(w, A, 2, nodes)
    s3, c3, allc3 = best_set(w, A, 3, nodes)
    models = pd.read_csv(RES / 'models.csv').set_index('model')
    assert s2 == A2 and s3 == A3
    assert abs(c2 - models.coverage['A_2']) < 1e-9 and abs(c3 - models.coverage['A_3']) < 1e-9
    second = np.sort(allc3)[-2]
    # ranking baselines
    strength, outs = T.sum(0) + T.sum(1), T.sum(1)
    cov = lambda ix: 100 * w[A[:, ix].any(1)].sum() / w.sum()
    r_strength = cov(np.argsort(-strength)[:3])
    r_out = cov(np.argsort(-outs)[:3])
    # lane coverage, brute force
    S, _ = all_cov(w, A, 3)
    C = A[:, S].any(2).T.astype(float)
    lane = 100 * ((C @ T) * C).sum(1) / T.sum()
    a3_ix = [nodes.index(v) for v in A3]
    lane_a3 = 100 * T[np.ix_(A[:, a3_ix].any(1), A[:, a3_ix].any(1))].sum() / T.sum()
    lanes = pd.read_csv(RES / 'lane_coverage.csv')
    # modularity of the saved partition
    cc = pd.read_csv(RES / 'community_coverage.csv').query("model=='A_3'")
    part = [set(m.split(' / ')) for m in cc.members]
    g = ugraph(T, nodes)
    q = nx.community.modularity(g, part, weight='weight')
    record('1_independent', A2=sorted(s2), A2_cov=c2, A3=sorted(s3), A3_cov=c3, A3_margin_to_2nd_pp=c3 - second,
           top3_strength=r_strength, top3_out_strength=r_out, lane_A3=lane_a3, lane_best=lane.max(), modularity=q)
    assert abs(r_strength - 57.4) < 0.05 and abs(r_out - 72.1) < 0.05
    assert abs(lane.max() - lanes.query("set=='Lane-optimal' and k==3").lane_coverage.iloc[0]) < 1e-6
    assert abs(lane_a3 - lanes.query("set=='A_3'").lane_coverage.iloc[0]) < 1e-6
    assert abs(q - json.loads((RES / 'summary.json').read_text())['observed_Q']) < 1e-9


# ---------------------------------------------------------------- 2. seed robustness of communities and Check 2
def test_community_seed_robustness(base):
    nodes = base['nodes']
    T = flows(base['d'], nodes)
    g = ugraph(T, nodes)
    cc = pd.read_csv(RES / 'community_coverage.csv').query("model=='A_3'")
    ref = labels([set(m.split(' / ')) for m in cc.members], nodes)
    best, qbest, parts = best_louvain(g, range(100, 200))
    aris = [ari(ref, labels(p, nodes)) for p in parts]
    leiden = [nx.community.leiden_communities(g, weight='weight', metric='modularity', seed=s) for s in range(100, 120)]
    record('2_seeds', best_Q_seeds_100_199=qbest, ARI_best_to_reported=ari(ref, labels(best, nodes)),
           ARI_mean=float(np.mean(aris)), groups_min=min(map(len, parts)), groups_max=max(map(len, parts)),
           leiden_ARI_min=min(ari(ref, labels(p, nodes)) for p in leiden))
    assert ari(ref, labels(best, nodes)) == pytest.approx(1.0)


def test_check2_1000_copies(base):
    nodes = base['nodes']
    topo = nx.Graph(ugraph(flows(base['d'], nodes), nodes).edges())
    obs = best_louvain(topo, range(10), weight=None)[1]
    rng = np.random.default_rng(20261125)
    null = []
    for _ in range(1000):
        H = topo.copy()
        nx.double_edge_swap(H, nswap=10 * H.number_of_edges(), max_tries=10**7, seed=int(rng.integers(2**31)))
        null.append(best_louvain(H, range(10), weight=None)[1])
    null = np.array(null)
    hits = int((null >= obs).sum())
    record('2_check2_1000', observed_Q=obs, copies_at_or_above=hits, p=(1 + hits) / 1001, null_max=null.max(), null_mean=null.mean())
    assert hits <= 40  # same 4-in-100 rule, scaled to 1000 copies


# ---------------------------------------------------------------- 3. data perturbation
def test_perturbation(base):
    D, nodes, d = base['D'], base['nodes'], base['d']
    A = (D.values <= 150).astype(float)
    cc = pd.read_csv(RES / 'community_coverage.csv').query("model=='A_3'")
    grp = {v: int(r.community) for _, r in cc.iterrows() for v in r.members.split(' / ')}
    pattern = lambda s: sorted(grp[v] for v in s) == [0, 1, 2]
    out = {}
    for m in sorted(d.month.unique()):
        s, c, _ = best_set(flows(d[d.month != m], nodes).sum(1), A, 3, nodes)
        out[f'drop_month_{m}'] = (sorted(s), round(c, 2), s == A3, pattern(s))
    for p_ in P:
        s, c, _ = best_set(flows(d[d['product'] != p_], nodes).sum(1), A, 3, nodes)
        out[f'drop_product_{p_}'] = (sorted(s), round(c, 2), s == A3, pattern(s))
    rng = np.random.default_rng(7)
    rows = d.reset_index(drop=True)
    same = pat = 0
    for _ in range(200):
        noisy = rows.assign(trips=rows.trips * rng.uniform(.8, 1.2, len(rows)))
        s, _, _ = best_set(flows(noisy, nodes).sum(1), A, 3, nodes)
        same += s == A3
        pat += pattern(s)
    # Bangkok proxy point moved 20 km in four directions
    w = flows(d, nodes).sum(1)
    co = pd.read_csv(DATA / 'province_coordinates_used.csv').set_index('province').loc[nodes]
    bkk = nodes.index('กรุงเทพมหานคร')
    bkk_same = 0
    for dlat, dlng in [(.18, 0), (-.18, 0), (0, .185), (0, -.185)]:
        lat = np.radians(co.LAT.values.copy()); lng = np.radians(co.LNG.values.copy())
        lat[bkk] += math.radians(dlat); lng[bkk] += math.radians(dlng)
        h = np.sin((lat[:, None] - lat) / 2) ** 2 + np.cos(lat[:, None]) * np.cos(lat) * np.sin((lng[:, None] - lng) / 2) ** 2
        s, _, _ = best_set(w, (6371 * 2 * np.arcsin(np.sqrt(h)) <= 150).astype(float), 3, nodes)
        bkk_same += s == A3
    record('3_perturbation', leave_one_out=out, noise_200_same_A3=same, noise_200_same_pattern=pat, bangkok_shift_4_same_A3=bkk_same)
    assert pat >= 190  # zone pattern should survive noise in at least 95% of draws


# ---------------------------------------------------------------- 4. other year
def test_2025_by_radius(base):
    D, nodes = base['D'], base['nodes']
    old = load('68')
    old = old[old['product'].isin(P) & old.province_origin.ne(old.province_destination)]
    w = flows(old, nodes).sum(1)
    rows = {}
    for R in [100, 125, 150, 175, 200]:
        A = (D.values <= R).astype(float)
        s, c, allc = best_set(w, A, 3, nodes)
        fixed = 100 * w[A[:, [nodes.index(v) for v in A3]].any(1)].sum() / w.sum()
        rows[R] = dict(best=sorted(s), best_cov=c, A3_fixed_cov=fixed, gap_pp=c - fixed)
    record('4_year_2025_all_months', **{str(k): v for k, v in rows.items()})
    assert rows[150]['gap_pp'] < 1.0
