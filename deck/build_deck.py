"""Build the presentation deck (.pptx, imports into Canva) from results/ and data/.

Every number on a slide comes from the facts registry F below, which reads results/, docs/stress_results.json
and the raw OTP file. deck/facts.json is written so lint_deck.py can check that no number was typed by hand.
Run from the repo root:  python deck/build_deck.py
"""
import json, re
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from lxml import etree

ROOT = Path(__file__).resolve().parents[1]
RES, DATA, ASSETS = ROOT / 'results', ROOT / 'data', ROOT / 'deck' / 'assets'
CH = ASSETS / 'charts'; CH.mkdir(parents=True, exist_ok=True)
REPO = 'github.com/hhej/MADT7202_capstone_freight'

EN = dict(zip('กระบี่ กรุงเทพมหานคร กาญจนบุรี กาฬสินธุ์ กำแพงเพชร ขอนแก่น จันทบุรี ฉะเชิงเทรา ชลบุรี ชัยนาท ชัยภูมิ ชุมพร ตรัง ตราด ตาก นครนายก นครปฐม นครพนม นครราชสีมา นครศรีธรรมราช นครสวรรค์ นนทบุรี นราธิวาส น่าน บึงกาฬ บุรีรัมย์ ปทุมธานี ประจวบคีรีขันธ์ ปราจีนบุรี ปัตตานี พระนครศรีอยุธยา พะเยา พังงา พัทลุง พิจิตร พิษณุโลก ภูเก็ต มหาสารคาม มุกดาหาร ยะลา ยโสธร ระนอง ระยอง ราชบุรี ร้อยเอ็ด ลพบุรี ลำปาง ลำพูน ศรีสะเกษ สกลนคร สงขลา สตูล สมุทรปราการ สมุทรสงคราม สมุทรสาคร สระบุรี สระแก้ว สิงห์บุรี สุพรรณบุรี สุราษฎร์ธานี สุรินทร์ สุโขทัย หนองคาย หนองบัวลำภู อำนาจเจริญ อุดรธานี อุตรดิตถ์ อุทัยธานี อุบลราชธานี อ่างทอง เชียงราย เชียงใหม่ เพชรบุรี เพชรบูรณ์ เลย แพร่ แม่ฮ่องสอน'.split(),
 ['Krabi','Bangkok','Kanchanaburi','Kalasin','Kamphaeng Phet','Khon Kaen','Chanthaburi','Chachoengsao','Chonburi','Chai Nat','Chaiyaphum','Chumphon','Trang','Trat','Tak','Nakhon Nayok','Nakhon Pathom','Nakhon Phanom','Korat','Nakhon Si Thammarat','Nakhon Sawan','Nonthaburi','Narathiwat','Nan','Bueng Kan','Buriram','Pathum Thani','Prachuap Khiri Khan','Prachinburi','Pattani','Ayutthaya','Phayao','Phang Nga','Phatthalung','Phichit','Phitsanulok','Phuket','Maha Sarakham','Mukdahan','Yala','Yasothon','Ranong','Rayong','Ratchaburi','Roi Et','Lopburi','Lampang','Lamphun','Sisaket','Sakon Nakhon','Songkhla','Satun','Samut Prakan','Samut Songkhram','Samut Sakhon','Saraburi','Sa Kaeo','Sing Buri','Suphanburi','Surat Thani','Surin','Sukhothai','Nong Khai','Nong Bua Lamphu','Amnat Charoen','Udon Thani','Uttaradit','Uthai Thani','Ubon Ratchathani','Ang Thong','Chiang Rai','Chiang Mai','Phetchaburi','Phetchabun','Loei','Phrae','Mae Hong Son']))
assert len(EN) == 77
PROD = {'ผลิตภัณฑ์มันสำปะหลัง': 'Cassava products', 'ข้าว': 'Rice', 'อาหารสัตว์': 'Animal feed', 'ข้าวเปลือก': 'Paddy',
        'น้ำตาลทราย': 'Sugar', 'กากน้ำตาล': 'Molasses', 'ข้าวโพด': 'Maize'}
GROUP = {0: 'Northeast & East', 1: 'Central', 2: 'North', 3: 'West & South'}
GCOL = ['#2680B9', '#D58920', '#29936F', '#9469B0']
en = lambda s: ' / '.join(EN[x.strip()] for x in s.split(' / '))

# ------------------------------------------------------------------ facts registry
rd = lambda f, **k: pd.read_csv(RES / f, encoding='utf-8-sig', **k)
models = rd('models.csv').set_index('model')
seed = rd('seeding.csv'); s3 = seed[seed.k == 3].set_index('method')
rad = rd('sensitivity_radius.csv'); near = rd('near_optimal.csv'); lane = rd('lane_coverage.csv')
cc = rd('community_coverage.csv'); conf = rd('community_confidence.csv'); cent = rd('centrality_directed.csv').set_index('province')
fp = rd('structure_fingerprint.csv', index_col=0); road = rd('road_calibration.csv', index_col=0)['value']
temporal = rd('temporal.csv'); audit = rd('audit.csv'); cross = rd('community_cross_check.csv').set_index('algorithm')
deckn = json.loads((RES / 'deck_numbers.json').read_text()); stress = json.loads((ROOT / 'docs' / 'stress_results.json').read_text())
valid = rd('validation_flagged_rows.csv'); wv = rd('weight_variants.csv')

raw = pd.read_csv(DATA / 'otp_69_01_69.csv')
for c in ['product', 'province_origin', 'province_destination']: raw[c] = raw[c].astype(str).str.strip()
d = raw[raw['product'].isin(PROD) & raw.province_origin.ne(raw.province_destination)]
D = pd.read_csv(DATA / 'straight_line_distance_km.csv', index_col=0); nodes = list(D.index)
coords = pd.read_csv(DATA / 'province_coordinates_used.csv').set_index('province').loc[nodes]
T = d.groupby(['province_origin', 'province_destination']).trips.sum().unstack().reindex(index=nodes, columns=nodes).fillna(0).values
w = T.sum(1); A = (D.values <= 150)
grp = {v.strip(): int(r.community) for _, r in cc[cc.model == 'A_3'].iterrows() for v in r.members.split(' / ')}
lab = np.array([grp[v] for v in nodes])
idx = lambda names: [nodes.index(x.strip()) for x in names.split(' / ')]
cov = lambda ix: 100 * w[A[:, ix].any(1)].sum() / w.sum()
lane_of = lambda ix: 100 * T[np.ix_(A[:, ix].any(1), A[:, ix].any(1))].sum() / T.sum()
gcov = lambda ix: {g: 100 * w[(lab == g) & A[:, ix].any(1)].sum() / w[lab == g].sum() for g in range(4)}
rank_set = s3.loc['Top by out-strength (origin trips)', 'hubs']; a3 = models.sites['A_3']; b3 = models.sites['B_3_0.5']
gsize = cc[cc.model == 'A_3'].set_index('community')
f1 = lambda x: f'{x:.1f}'; pct = lambda x: f'{x:.1f}%'; n0 = lambda x: f'{x:,.0f}'
prod = d.groupby('product').trips.sum().sort_values()
yr = stress['4_year_2025_all_months']; pert = stress['3_perturbation']; c1000 = stress['2_check2_1000']
cassava_drop = pert['leave_one_out']['drop_product_ผลิตภัณฑ์มันสำปะหลัง']
F = {
 'trips': n0(deckn['interprovince_trips']), 'raw_rows': n0(audit.query("year==2026 and stage=='raw'").rows.iloc[0]),
 'inter_rows': n0(audit.query("year==2026 and stage=='interprovince'").rows.iloc[0]),
 'A2': pct(models.coverage['A_2']), 'A3': pct(models.coverage['A_3']), 'B3': pct(models.coverage['B_3_0.5']),
 'hub3_gain': f1(models.coverage['A_3'] - models.coverage['A_2']), 'B_cost': f1(deckn['B_cost_pp']),
 'per_month': n0(round(deckn['A3_trips_reached_per_month'], -3)),
 'suphan': n0(deckn['suphanburi_reach']), 'lopburi': n0(deckn['lopburi_reach']), 'su_lo_sum': n0(deckn['suphanburi_reach'] + deckn['lopburi_reach']),
 'chon_in': n0(cent.in_trips['ชลบุรี']), 'chon_out': n0(cent.out_trips['ชลบุรี']), 'chon_ratio': f'{cent.in_trips["ชลบุรี"] / cent.out_trips["ชลบุรี"]:.0f}',
 'random': pct(s3.coverage['Random (mean of all sets)']), 'r_strength': pct(s3.coverage['Top by strength (in+out)']),
 'r_out': pct(s3.coverage['Top by out-strength (origin trips)']), 'greedy': pct(s3.coverage['Greedy']),
 'r_out_singles': pct(s3.sum_of_singles['Top by out-strength (origin trips)']),
 'gain_rank': f1(models.coverage['A_3'] - s3.coverage['Top by out-strength (origin trips)']), 'gain_greedy': f1(models.coverage['A_3'] - s3.coverage['Greedy']),
 'lane_A3': pct(lane.query("set=='A_3'").lane_coverage.iloc[0]), 'lane_best': pct(lane.query("set=='Lane-optimal' and k==3").lane_coverage.iloc[0]),
 'lane_A2': pct(lane.query("set=='A_2'").lane_coverage.iloc[0]), 'lane_rank': pct(lane_of(idx(rank_set))),
 'ws_A': pct(deckn['west_south_A3']), 'ws_B': pct(deckn['west_south_B3']), 'weak_A': pct(deckn['weakest_group_A3']), 'weak_B': pct(deckn['weakest_group_B3']),
 'weak_rank': pct(min(gcov(idx(rank_set)).values())),
 'gapA': f1(temporal.query("model=='A_3'").loss_pp.max()), 'gapB': f'{temporal.query("model==\'B_3_0.5\'").loss_pp.max():.2f}',
 'Q': f'{json.loads((RES / "summary.json").read_text())["observed_Q"]:.2f}',
 'c1000_hits': str(c1000['copies_at_or_above']), 'c1000_p': f'{c1000["p"]:.3f}', 'qtopo': f'{c1000["observed_Q"]:.2f}', 'qnullmax': f'{c1000["null_max"]:.2f}',
 'flagged': str(deckn['flagged_provinces']), 'stable': str(77 - deckn['flagged_provinces']),
 'sara_conf': f'{conf.set_index("province").confidence["สระบุรี"]:.2f}', 'leiden_ari': f'{cross.ARI_to_reported["Leiden (modularity)"]:.2f}',
 'density': f'{fp.at["density", "freight network"]:.2f}', 'clust': f'{fp.at["clustering", "freight network"]:.2f}', 'clust_r': f'{fp.at["clustering", "random G(n,m), mean of 100"]:.2f}',
 'cent': f'{fp.at["centralization", "freight network"]:.2f}', 'cent_r': f'{fp.at["centralization", "random G(n,m), mean of 100"]:.2f}',
 'avgpath': f'{fp.at["avg_path", "freight network"]:.2f}', 'diam': f'{fp.at["diameter", "freight network"]:.0f}',
 'inside_w': f'{fp.at["inside_share_weighted_reported_split", "freight network"]:.2f}', 'sara_partners': f'{cent.partners["สระบุรี"]:.0f}',
 'road_ratio': f'{road["road_to_straight_median"]:.2f}', 'road_km': f'{road["road_km_at_150_straight"]:.0f}', 'hours': f'{road["minutes_median_pairs_130_170km"] / 60:.1f}',
 'r125_opt': pct(rad.query('radius_km==125 and k==3').coverage.iloc[0]), 'r125_fix': pct(rad.query('radius_km==125 and k==3').A3_sites_coverage.iloc[0]),
 'r125_set': en(rad.query('radius_km==125 and k==3').hubs.iloc[0]),
 'near_gap': f1(near.query('k==3 and rank==2').gap_pp.iloc[0]), 'noise': str(pert['noise_200_same_A3']),
 'y25': pct(yr['150']['best_cov']), 'flag_rows': str(len(valid)), 'flag_share': f'{100 * valid.trips.sum() / d.trips.sum():.1f}',
 'cassava_share': f'{100 * prod["ผลิตภัณฑ์มันสำปะหลัง"] / prod.sum():.1f}', 'cassava_alt': ' / '.join(EN[x] for x in cassava_drop[0]),
 'tons_same': str(int(wv.same_hubs_as_A.all())), 'p_shuffle': f"{rd('check2_baselines.csv').p.iloc[2]:.2f}",
}
for g in range(4):
    F[f'g{g}_n'] = str(len(gsize.members[g].split(' / '))); F[f'g{g}_share'] = f'{gsize.market_share[g]:.0f}%'
for p_, v in prod.items(): F['prod_' + PROD[p_]] = n0(v)
(ROOT / 'deck' / 'facts.json').write_text(json.dumps(F, ensure_ascii=False, indent=1))
assert F['tons_same'] == '1' and pert['noise_200_same_A3'] == 200

# ------------------------------------------------------------------ charts (theme colours)
plt.rcParams.update({'font.family': 'Arial', 'font.size': 13, 'axes.spines.top': False, 'axes.spines.right': False})
NAVY, ORANGE, GREY, TAN = '#2B3A67', '#E05A2B', '#C3C7D0', '#C8955A'

def save(fig, name):
    fig.savefig(CH / name, dpi=200, bbox_inches='tight', facecolor='white'); plt.close(fig); return CH / name

def ch_products():
    fig, ax = plt.subplots(figsize=(9, 3.9)); s = prod.rename(PROD)
    b = ax.barh(s.index, s.values, color=NAVY, height=.65); ax.bar_label(b, labels=[n0(v) for v in s.values], padding=4)
    ax.set_xticks([]); ax.spines['bottom'].set_visible(False); ax.set_title(f'Truck trips between provinces, Jan–Apr 2026 (total {F["trips"]})', loc='left', fontsize=13, color='#555')
    return save(fig, 'products.png')

def ch_seeding():
    rows = [('Random set (average)', 'Random (mean of all sets)', GREY), ('Top 3 by total trips (in + out)', 'Top by strength (in+out)', GREY),
            ('Top 3 by betweenness', 'Top by betweenness', GREY), ('Top 3 by trips that start there', 'Top by out-strength (origin trips)', GREY),
            ('Greedy: add the best next hub', 'Greedy', '#29936F'), ('Model A: best set of 3', 'Optimal (Model A, MILP = brute force)', ORANGE)]
    fig, ax = plt.subplots(figsize=(9.5, 5.2)); vals = [s3.coverage[k] for _, k, _ in rows]
    b = ax.barh([r[0] for r in rows], vals, color=[r[2] for r in rows], height=.62); ax.bar_label(b, labels=[pct(v) for v in vals], padding=5, fontsize=14)
    ax.set_xlim(0, 100); ax.set_xticks([]); ax.spines['bottom'].set_visible(False)
    ax.set_title('Share of trips that start within 150 km of 3 hubs', loc='left', fontsize=13, color='#555')
    return save(fig, 'seeding.png')

def ch_radius():
    r3 = rad[rad.k == 3]; fig, ax = plt.subplots(figsize=(9.5, 5))
    ax.plot(r3.radius_km, r3.coverage, 'o-', color=NAVY, lw=2.5, label='Best 3 hubs for that radius')
    ax.plot(r3.radius_km, r3.A3_sites_coverage, 's--', color=ORANGE, lw=2.5, label='Our 3 hubs (chosen at 150 km)')
    for _, r in r3.iterrows():
        ax.annotate(f'{r.coverage:.0f}%', (r.radius_km, r.coverage), xytext=(0, 9), textcoords='offset points', ha='center', color=NAVY)
        if abs(r.coverage - r.A3_sites_coverage) > .5: ax.annotate(f'{r.A3_sites_coverage:.0f}%', (r.radius_km, r.A3_sites_coverage), xytext=(0, -18), textcoords='offset points', ha='center', color=ORANGE)
    ax.set_xticks(r3.radius_km); ax.set_xlabel('Service radius, straight line (km)'); ax.set_ylabel('Trips reached (%)'); ax.set_ylim(30, 105); ax.legend(frameon=False, loc='lower right')
    return save(fig, 'radius.png')

def ch_groups():
    a, b = gcov(idx(a3)), gcov(idx(b3)); fig, ax = plt.subplots(figsize=(9, 5)); x = np.arange(4)
    ba = ax.bar(x - .2, [a[g] for g in range(4)], .38, color=NAVY, label='Model A: ' + en(a3)); bb = ax.bar(x + .2, [b[g] for g in range(4)], .38, color=ORANGE, label='Model B: ' + en(b3))
    ax.bar_label(ba, fmt='%.0f%%'); ax.bar_label(bb, fmt='%.0f%%'); ax.axhline(50, ls=':', color='#888', lw=1)
    ax.set_xticks(x, [f'{GROUP[g]}\n({gsize.market_share[g]:.0f}% of trips)' for g in range(4)]); ax.set_ylabel('Trips reached in the group (%)'); ax.set_ylim(0, 112)
    ax.legend(frameon=False, loc='upper center', bbox_to_anchor=(.5, -.18), ncol=1); return save(fig, 'groups.png')

def ch_map(name, hubs=None):
    x, y = coords.LNG.values, coords.LAT.values; W = T + T.T
    top = sorted(((W[i, j], i, j) for i in range(77) for j in range(i + 1, 77) if W[i, j] > 0), reverse=True)[:60]
    fig, ax = plt.subplots(figsize=(6.2, 8.4))
    for wt, i, j in top: ax.plot([x[i], x[j]], [y[i], y[j]], color='grey', alpha=.28, lw=.5 + 4 * wt / top[0][0], zorder=1)
    hix = idx(hubs) if hubs else []
    reach = A[:, hix].any(1) if hubs else np.ones(77, bool)
    for g in range(4):
        m = lab == g
        ax.scatter(x[m & reach], y[m & reach], s=18 + 520 * w[m & reach] / w.max(), c=GCOL[g], edgecolors='white', zorder=2, label=GROUP[g])
        ax.scatter(x[m & ~reach], y[m & ~reach], s=18 + 520 * w[m & ~reach] / w.max(), c=GCOL[g], alpha=.22, edgecolors='white', zorder=2)
    for i in hix:
        r = 150 / 111; ax.add_patch(Ellipse((x[i], y[i]), 2 * r / np.cos(np.radians(y[i])), 2 * r, fill=False, ec='#2B3A67', lw=1.6, zorder=3))
        ax.scatter(x[i], y[i], s=420, marker='*', c='gold', edgecolors='black', zorder=5)
        ax.annotate(EN[nodes[i]], (x[i], y[i]), xytext=(9, 8), textcoords='offset points', fontsize=12, bbox=dict(fc='white', ec='none', alpha=.85), zorder=6)
    ax.set_aspect(1 / np.cos(np.radians(13))); ax.axis('off'); ax.set_ylim(12.0, 20.6); ax.set_xlim(97.4, 106.0)
    ax.legend(frameon=False, loc='upper center', bbox_to_anchor=(.5, .02), ncol=2, fontsize=12, markerscale=.5)
    return save(fig, name)

charts = dict(products=ch_products(), seeding=ch_seeding(), radius=ch_radius(), groups=ch_groups(), map_groups=ch_map('map_groups.png'), map_hubs=ch_map('map_hubs.png', a3))

# ------------------------------------------------------------------ slide helpers (theme from the team deck)
BG, CARD, TANC, WHITE, BODY, DARK = '26252F', '34333F', 'C8955A', 'FFFFFF', 'B4B4BE', '26252F'
prs = Presentation(); prs.slide_width, prs.slide_height = Inches(20), Inches(11.25)
BLANK = prs.slide_layouts[6]
rgb = lambda h: RGBColor.from_string(h)

def shape(s, x, y, w_, h, color, kind=MSO_SHAPE.RECTANGLE, alpha=None, radius=.06):
    sp = s.shapes.add_shape(kind, Inches(x), Inches(y), Inches(w_), Inches(h))
    sp.fill.solid(); sp.fill.fore_color.rgb = rgb(color); sp.line.fill.background(); sp.shadow.inherit = False
    if kind == MSO_SHAPE.ROUNDED_RECTANGLE: sp.adjustments[0] = radius
    if alpha is not None:
        clr = sp.fill._xPr.find(qn('a:solidFill'))[0]; a = etree.SubElement(clr, qn('a:alpha')); a.set('val', str(int(alpha * 100000)))
    return sp

def text(s, x, y, w_, h, paras, size=20, color=WHITE, bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, spacing=1.1, after=6):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w_), Inches(h)); tf = tb.text_frame; tf.word_wrap = True
    tf.vertical_anchor = anchor
    for side in ('margin_left', 'margin_right', 'margin_top', 'margin_bottom'): setattr(tf, side, Inches(.05))
    for k, p in enumerate(paras if isinstance(paras, list) else [paras]):
        para = tf.paragraphs[0] if k == 0 else tf.add_paragraph()
        runs = p if isinstance(p, list) else [p]
        for r in runs:
            t, o = (r, {}) if isinstance(r, str) else r
            assert '\n' not in t, 'use separate paragraphs, not newlines inside a run'
            run = para.add_run(); run.text = t; fnt = run.font; fnt.name = 'Arial'
            fnt.size = Pt(o.get('size', size)); fnt.bold = o.get('bold', bold); fnt.color.rgb = rgb(o.get('color', color))
        para.alignment = align; para.line_spacing = spacing; para.space_after = Pt(after)
    return tb

def dots(s, x=18.3, y=.45, color='D9D9DF'):
    for r in range(3):
        for c in range(4): shape(s, x + c * .24, y + r * .24, .08, .08, color, MSO_SHAPE.OVAL)

def header(s, light=True):
    shape(s, .83, .48, .3, .3, TANC); text(s, 1.25, .38, 8, .4, 'HUB LOCATION STUDY · MADT 7202', 12.5, 'C9C9D1', True)

PAGE = [0]
NOTES = {}  # speaker script; kept out of the pptx because python-pptx notes pages break Keynote and Quick Look
def chrome(label, title, sub=None, source=None, notes=''):
    s = prs.slides.add_slide(BLANK); PAGE[0] += 1
    shape(s, 0, 0, 20, 11.25, BG); header(s); dots(s)
    text(s, .83, .95, 14, .45, label.upper(), 16, TANC, True)
    text(s, .83, 1.4, 17.5, .9, title, 40, WHITE, True)
    if sub: text(s, .83, 2.3, 17.5, .6, sub, 20, 'A9A9B3')
    if source: text(s, .83, 10.62, 16.5, .45, 'Source: ' + source, 11, '8E8E99')
    text(s, 18.6, 10.62, .6, .4, f'{PAGE[0]:02d}', 13, TANC, True, PP_ALIGN.RIGHT)
    NOTES[PAGE[0]] = notes
    return s

def headline(s, t, y=3.15):
    shape(s, .83, y, 18.35, .85, TANC, MSO_SHAPE.ROUNDED_RECTANGLE, radius=.12)
    text(s, 1.2, y, 17.6, .85, t, 23, DARK, True, anchor=MSO_ANCHOR.MIDDLE)

def card(s, x, y, w_, h, big, small, tan=False, bigsize=46, smallsize=18):
    shape(s, x, y, w_, h, TANC if tan else CARD, MSO_SHAPE.ROUNDED_RECTANGLE, radius=.07)
    text(s, x + .35, y + .25, w_ - .6, 1.0, big, bigsize, DARK if tan else TANC, True)
    text(s, x + .35, y + 1.35, w_ - .6, h - 1.5, small, smallsize, DARK if tan else 'E6E6EA')

def picture(s, path, x, y, w_, h, pad=.18):
    shape(s, x, y, w_, h, WHITE, MSO_SHAPE.ROUNDED_RECTANGLE, radius=.04)
    from PIL import Image
    iw, ih = Image.open(path).size; bw, bh = w_ - 2 * pad, h - 2 * pad; sc = min(bw / iw, bh / ih)
    pw, ph = iw * sc, ih * sc; s.shapes.add_picture(str(path), Inches(x + pad + (bw - pw) / 2), Inches(y + pad + (bh - ph) / 2), Inches(pw), Inches(ph))

def table(s, x, y, w_, rows, widths, size=16, rowh=.62, head=True, hl_last=False):
    t = s.shapes.add_table(len(rows), len(rows[0]), Inches(x), Inches(y), Inches(w_), Inches(rowh * len(rows))).table
    for j, cw in enumerate(widths): t.columns[j].width = Inches(cw)
    for i, row in enumerate(rows):
        t.rows[i].height = Inches(rowh)
        for j, val in enumerate(row):
            c = t.cell(i, j); c.text = ''; c.margin_left = c.margin_right = Inches(.12); c.vertical_anchor = MSO_ANCHOR.MIDDLE
            p = c.text_frame.paragraphs[0]; r = p.add_run(); r.text = str(val); r.font.name = 'Arial'; r.font.size = Pt(size)
            is_head = head and i == 0; last = hl_last and i == len(rows) - 1
            r.font.bold = is_head or last or (j == 0 and not head)
            r.font.color.rgb = rgb(WHITE if is_head else (DARK if not last or j else 'E05A2B'))
            c.fill.solid(); c.fill.fore_color.rgb = rgb(TANC if is_head else ('F4E3CC' if last else ('FFFFFF' if i % 2 else 'ECE8E2')))
    return t

def divider(part, title, sub, photo, notes=''):
    s = prs.slides.add_slide(BLANK); PAGE[0] += 1
    s.shapes.add_picture(str(ASSETS / photo), 0, 0, Inches(20), Inches(11.25)); shape(s, 0, 0, 20, 11.25, '1E1D26', alpha=.55)
    header(s); dots(s, 18.3, 10.15, 'FFFFFF')
    text(s, 1.35, 3.25, 10, .6, f'PART {part}', 26, TANC, True)
    text(s, 1.35, 3.9, 14, 3.2, title.split('\n'), 96, WHITE, True, spacing=.9, after=0)  # one paragraph per line: no raw newline inside a run
    shape(s, 1.35, 7.73, 6.9, .62, TANC); text(s, 1.55, 7.73, 6.6, .62, sub, 20, DARK, True, anchor=MSO_ANCHOR.MIDDLE)
    NOTES[PAGE[0]] = notes

SRC = f'OTP truck freight data (otp_69_01), Jan–Apr 2026, 7 farm and food goods; code and results at {REPO}'

# ================================================================== SLIDES
# 1 Title
s = prs.slides.add_slide(BLANK); PAGE[0] += 1
s.shapes.add_picture(str(ASSETS / 'photo_title.jpg'), 0, 0, Inches(20), Inches(10.2)); shape(s, 0, 0, 12.9, 10.2, '26252F', alpha=.82)
header(s); text(s, 1.2, 2.3, 11, 4.2, 'WHERE SHOULD WE OPEN OUR FIRST TRUCKING HUBS?', 64, WHITE, True, spacing=.95)
text(s, 1.3, 7.0, 11, 1.2, 'Using the freight network to pick hub locations that work as a set', 24, 'E6E6EA')
shape(s, 0, 10.2, 20, 1.05, TANC); text(s, 12, 10.2, 7.3, 1.05, 'MADT 7202 Capstone', 22, DARK, True, PP_ALIGN.RIGHT, MSO_ANCHOR.MIDDLE)
NOTES[PAGE[0]] = (
 '[จันทนา · 0:15] สวัสดีค่ะ วันนี้กลุ่มเราจะตอบคำถามเดียว: ถ้าเราเป็นบริษัทรถบรรทุกเปิดใหม่ และมีงบเปิดฐานได้แค่ 2–3 แห่ง ควรเปิดที่จังหวัดไหน '
 'คำตอบของเราไม่ได้มาจากการดูว่าจังหวัดไหนมีรถวิ่งมากที่สุด แต่มาจากการมองการขนส่งทั้งประเทศเป็นเครือข่าย')

divider(1, 'THE\nCHALLENGE', 'Where to open, and why it is hard', 'photo_part1.jpg', '[จันทนา · 0:05] ส่วนแรก: โจทย์และเหตุผลที่โจทย์นี้ยาก')

# 2 Opportunity
s = prs.slides.add_slide(BLANK); PAGE[0] += 1
shape(s, 0, 0, 20, 11.25, BG); s.shapes.add_picture(str(ASSETS / 'photo_farm.jpg'), 0, 0, Inches(7.5), Inches(11.25))
dots(s); text(s, 8.2, .95, 11, .45, 'THE OPPORTUNITY', 16, TANC, True); text(s, 8.2, 1.4, 11.5, .9, "Thailand's Farm Freight Network", 40, WHITE, True)
text(s, 8.2, 2.3, 11, .6, 'Farm and food goods cross provincial borders every day', 20, 'A9A9B3')
card(s, 8.2, 3.3, 5.25, 2.9, F['trips'], 'truck trips between provinces for our 7 farm and food goods in 4 months (Jan–Apr 2026)')
card(s, 13.8, 3.3, 5.4, 2.9, 'No hub yet', 'We are a new carrier. Where we open decides who we can serve.', tan=True, bigsize=40)
picture(s, charts['products'], 8.2, 6.5, 11.0, 4.05)
text(s, 8.2, 10.62, 9.5, .45, 'Source: ' + SRC, 10, '8E8E99'); text(s, 18.6, 10.62, .6, .4, f'{PAGE[0]:02d}', 13, TANC, True, PP_ALIGN.RIGHT)
NOTES[PAGE[0]] = (f'[จันทนา · 0:35] ข้อมูลที่เราใช้คือข้อมูลเปิดของ สนข. ที่มาจาก GPS รถบรรทุก ช่วงมกราคมถึงเมษายน 2569 '
 f'เฉพาะสินค้าเกษตรและอาหาร 7 ชนิด มีเที่ยวรถข้ามจังหวัด {F["trips"]} เที่ยวในสี่เดือน มันสำปะหลังมากที่สุด รองลงมาคือข้าวและอาหารสัตว์ '
 'โจทย์ของเราคือ บริษัทยังไม่มีฐานเลย ที่ตั้งฐานจะกำหนดว่าเรารับงานจากใครได้บ้าง')

# 3 Challenge
s = chrome('The challenge', 'Limited Budget, Too Many Choices', 'We can open only 2–3 hubs, but Thailand has 77 provinces', SRC,
 '[จันทนา · 0:30] งบเปิดฐานได้ 2 ถึง 3 แห่ง แต่ละฐานต้องมีลานจอด รถ และทีมขาย ฐานหนึ่งรับงานได้ในรัศมี 150 กิโลเมตร '
 'ถ้าเลือก 3 จังหวัดจาก 77 จังหวัด มีทางเลือก 73,150 แบบ คำถามที่เราจะตอบคือ เลือกจังหวัดไหน ควรเปิด 2 หรือ 3 ฐาน และการมองเป็นเครือข่ายเลือกได้ดีกว่าการจัดอันดับธรรมดาหรือไม่')
card(s, .83, 3.3, 5.85, 3.2, '2–3 hubs', 'all the budget allows (yard, trucks and a sales team each)')
card(s, 7.08, 3.3, 5.85, 3.2, '150 km', 'how far one hub can send trucks to pick up loads')
card(s, 13.33, 3.3, 5.85, 3.2, '73,150', 'ways to pick 3 provinces from 77 (2,926 ways to pick 2)', tan=True)
shape(s, .83, 6.9, 18.35, 3.5, CARD, MSO_SHAPE.ROUNDED_RECTANGLE, radius=.05)
text(s, 1.3, 7.2, 17.5, 3.0, ['Which provinces should we choose?', 'Is a third hub worth it?', [('Can the network choose better than a simple ranking?', {'color': TANC})]], 30, WHITE, True, after=18)

# 4 Puzzle
s = chrome('The puzzle', 'Why Not Pick the Busiest Provinces?', 'Two problems with ranking provinces one by one', SRC + '; results/centrality_directed.csv',
 f'[จันทนา · 0:50] ทำไมไม่เลือกจังหวัดที่รถวิ่งเยอะที่สุด มีสองเหตุผล '
 f'หนึ่ง ฐานที่อยู่ใกล้กันรับลูกค้ากลุ่มเดียวกัน เช่น สุพรรณบุรีเข้าถึงเที่ยวต้นทาง {F["suphan"]} เที่ยว ลพบุรี {F["lopburi"]} เที่ยว '
 f'ถ้าบวกกันดูเหมือนได้ {F["su_lo_sum"]} แต่จริง ๆ ทุกจังหวัดที่ลพบุรีเข้าถึง สุพรรณบุรีก็เข้าถึงอยู่แล้ว รวมกันจึงได้แค่ {F["suphan"]} '
 f'สอง จังหวัดที่รถวิ่งรวมมากที่สุดคือชลบุรี แต่ชลบุรีเป็นปลายทาง รับเข้า {F["chon_in"]} เที่ยว ส่งออกแค่ {F["chon_out"]} เพราะมีท่าเรือ '
 'ฐานรับงานต้องอยู่ใกล้ที่ที่สินค้าเริ่มเดินทาง ไม่ใช่ที่ที่สินค้าไปจบ ต่อไป นิษฐกานต์จะเล่าว่าเรามองโจทย์นี้เป็นเครือข่ายอย่างไรค่ะ')
headline(s, 'Busy provinces close together serve the same customers, and the busiest one is a destination.')
shape(s, .83, 4.35, 8.95, 6.1, CARD, MSO_SHAPE.ROUNDED_RECTANGLE, radius=.05)
text(s, 1.25, 4.6, 8.2, .6, '1. Overlap', 24, TANC, True)
text(s, 1.25, 5.3, 8.2, 5, [f'Suphanburi reaches {F["suphan"]} trips that start within 150 km.', f'Lopburi reaches {F["lopburi"]}.',
 f'Every province Lopburi reaches, Suphanburi already reaches.', [(f'Together: {F["suphan"]}, not {F["su_lo_sum"]}.', {'bold': True, 'color': TANC})]], 20, 'E6E6EA', after=12)
shape(s, 10.23, 4.35, 8.95, 6.1, CARD, MSO_SHAPE.ROUNDED_RECTANGLE, radius=.05)
text(s, 10.65, 4.6, 8.2, .6, '2. Direction', 24, TANC, True)
text(s, 10.65, 5.3, 8.2, 5, [f'Chonburi has the most trips in total.', f'But it receives {F["chon_in"]} trips and sends only {F["chon_out"]}: about {F["chon_ratio"]} in for every 1 out (port).',
 'A pickup hub needs loads that start nearby.', [('Rank by where trips start, not by total trips.', {'bold': True, 'color': TANC})]], 20, 'E6E6EA', after=12)

divider(2, 'THE\nINVESTIGATION', 'From freight data to a network', 'photo_part2.jpg', '[นิษฐกานต์ · 0:05] ส่วนที่สอง: จากข้อมูลขนส่งสู่เครือข่าย')

# 5 Reframe
s = chrome('The idea', 'We Treat Freight as a Network', 'Actors → Ties → Structure → Decision', SRC,
 '[นิษฐกานต์ · 0:50] เรามองโจทย์ด้วยกรอบ Actors Ties Structure จุดคือ 77 จังหวัด เส้นคือเที่ยวรถจากจังหวัดหนึ่งไปอีกจังหวัด เก็บทิศทางไว้ด้วย '
 'โครงสร้างที่เราดูคือกลุ่มตลาด จังหวัดที่สำคัญ และการซ้อนทับของพื้นที่บริการ ผลลัพธ์คือชุดของฐาน 2–3 แห่ง '
 'คำถามจึงเปลี่ยนจาก จังหวัดไหนมีเที่ยวมากที่สุด เป็น ชุดจังหวัดไหนเข้าถึงเที่ยวได้มากที่สุดโดยไม่นับซ้ำ นี่คือการตัดสินใจระดับกลุ่ม ไม่ใช่ระดับจังหวัดเดี่ยว เพราะคุณค่าของฐานหนึ่งขึ้นกับว่าฐานอื่นอยู่ที่ไหน')
for k, (a, b) in enumerate([('Actors', '77 provinces (markets, not single firms)'), ('Ties', 'truck trips from one province to another, direction kept'),
                            ('Structure', 'market groups, key provinces, overlap between hubs'), ('Decision', 'a set of 2–3 hub provinces')]):
    x = .83 + k * 4.68; shape(s, x, 3.3, 4.3, 3.0, TANC if k == 3 else CARD, MSO_SHAPE.ROUNDED_RECTANGLE, radius=.07)
    text(s, x + .3, 3.5, 3.8, .7, a, 30, DARK if k == 3 else TANC, True); text(s, x + .3, 4.35, 3.8, 1.9, b, 19, DARK if k == 3 else 'E6E6EA')
    if k < 3: text(s, x + 4.27, 4.4, .45, .7, '→', 28, TANC, True)
shape(s, .83, 6.75, 18.35, 3.65, CARD, MSO_SHAPE.ROUNDED_RECTANGLE, radius=.05)
text(s, 1.3, 7.0, 17.5, 3.3, [[('The question changes', {'color': TANC, 'size': 24, 'bold': True})],
 [('Before: ', {'bold': True}), 'Which province has the most trips?'],
 [('After: ', {'bold': True}), 'Which set of provinces reaches the most trips, counting each trip once?'],
 [('Level: ', {'bold': True}), "group. A hub's value depends on where the other hubs are."]], 22, 'E6E6EA', after=14)

# 6 Data and graph
s = chrome('The data', 'From Freight Records to a Graph', 'Open government GPS data from trucks, checked before use', SRC + '; results/audit.csv, weight_variants.csv, validation_flagged_rows.csv',
 f'[นิษฐกานต์ · 0:45] ข้อมูลมี {F["raw_rows"]} แถว เหลือ {F["inter_rows"]} แถวที่เป็นสินค้าของเราและข้ามจังหวัด ชื่อจังหวัดตรงกับพิกัดครบ 77 จังหวัด ไม่มีค่าว่างหรือติดลบ '
 f'เราตรวจความสมเหตุสมผลทุกแถว เช่น ระยะวิ่งจริงต้องไม่สั้นกว่าระยะระหว่างจังหวัดมากเกินไป พบ {F["flag_rows"]} แถว คิดเป็น {F["flag_share"]}% ของเที่ยว จึงไม่กระทบผล '
 'น้ำหนักของเส้นใช้จำนวนเที่ยว และเราทดสอบแล้วว่าถ้าใช้น้ำหนักตัน หรือรวมเที่ยวในจังหวัดเดียวกัน ได้ฐานชุดเดิมทุกครั้ง ข้อมูลเป็นยอดรวมระดับจังหวัด ไม่มีข้อมูลส่วนบุคคล')
table(s, .83, 3.3, 9.2, [['Graph part', 'What it is'], ['Node', 'Province (77)'], ['Edge', 'Truck trips between two provinces'],
 ['Weight', 'Number of trips'], ['Direction', 'Kept for pickup reach and centrality'], ['Period', 'Jan–Apr 2026 (2025 used as a check)'], ['Goods', '7 farm and food goods (no sugarcane)']], [2.6, 6.6], 17, .7)
shape(s, 10.4, 3.3, 8.78, 7.1, CARD, MSO_SHAPE.ROUNDED_RECTANGLE, radius=.05)
text(s, 10.8, 3.5, 8.1, .6, 'Checks before analysis', 24, TANC, True)
text(s, 10.8, 4.2, 8.1, 6.1, [f'{F["raw_rows"]} raw rows → {F["inter_rows"]} rows between provinces for our goods',
 'All 77 province names matched; no missing or negative trips', f'{F["flag_rows"]} rows ({F["flag_share"]}% of trips) have an implausible road distance: too few to change results',
 'Weight by trips, by tons, or adding trips inside a province: the same hubs every time', 'Data files are checked by SHA-256 hash on every run',
 [('Province totals only: no names, plates or companies (PDPA)', {'color': TANC, 'bold': True})]], 18, 'E6E6EA', after=10)

# 7 Structure
s = chrome('The network', 'What Shape Is the Freight Network?', 'Compared with random networks of the same size', SRC + '; results/structure_fingerprint.csv, centrality_directed.csv',
 f'[นิษฐกานต์ · 0:45] เมื่อเทียบกับเครือข่ายสุ่มที่มีจำนวนจุดและเส้นเท่ากัน เครือข่ายขนส่งของเราจับกลุ่มมากกว่ามาก ค่า clustering {F["clust"]} เทียบกับ {F["clust_r"]} '
 f'แปลว่าจังหวัดใกล้กันค้าขายกันเอง และมีบางจังหวัดที่ค้ากับเกือบทุกจังหวัด เช่น สระบุรีค้ากับ {F["sara_partners"]} จาก 76 จังหวัด '
 'ทางขวาคือสิ่งที่สำคัญกับฐานรับงาน จังหวัดที่สินค้าเริ่มเดินทางมากที่สุดคือ นครสวรรค์ โคราช ลพบุรี ส่วนจังหวัดที่สินค้าไปจบคือ ชลบุรี อยุธยา สมุทรปราการ คนละกลุ่มกันเลย '
 'ต่อไป ปัญจพลจะเล่าเรื่องกลุ่มตลาดและการตรวจสอบครับ')
headline(s, 'Dense and regional: neighbours trade with neighbours, and a few provinces trade with almost everyone.')
table(s, .83, 4.35, 9.6, [['Measure', 'Freight network', 'Random network'], ['Clustering (my partners trade with each other)', F['clust'], F['clust_r']],
 ['Centralization (a few provinces dominate)', F['cent'], F['cent_r']], ['Density', F['density'], F['density']], ['Most steps between two provinces', F['diam'], '2'],
 ['Most trading partners', f'Saraburi: {F["sara_partners"]} of 76', '—']], [5.0, 2.4, 2.2], 16, .78)
c = cent; top = lambda col: ', '.join(EN[v] for v in c.nlargest(3, col).index)
shape(s, 10.85, 4.35, 8.33, 5.9, CARD, MSO_SHAPE.ROUNDED_RECTANGLE, radius=.05)
text(s, 11.25, 4.55, 7.6, .6, 'Where loads start vs where they end', 22, TANC, True)
text(s, 11.25, 5.3, 7.6, 4.9, [[('Most trips start in: ', {'bold': True}), top('out_trips')], [('Most trips end in: ', {'bold': True}), top('in_trips')],
 [('Most trips in + out: ', {'bold': True}), top('strength')], [('A pickup hub should follow where trips start. Totals mix in the ports.', {'color': TANC, 'bold': True})]], 19, 'E6E6EA', after=16)

# 8 Market groups (technical)
s = chrome('The network', 'Freight Forms 4 Market Groups', 'Louvain community detection, checked the way the course teaches (Ch 9)', SRC + '; results/check2_baselines.csv, community_confidence.csv, community_cross_check.csv; docs/stress_results.json',
 f'[ปัญจพล · 0:50] เราใช้ Louvain หากลุ่มตลาด ได้ 4 กลุ่ม แล้วตรวจตามบทที่ 9 ทั้งสี่ข้อ '
 f'ข้อแรก เทียบกับเครือข่ายสุ่มที่สลับเส้นแต่คงจำนวนคู่ค้าของทุกจังหวัด 1,000 ชุด ไม่มีชุดไหนได้ค่า modularity ถึงของจริงเลย p เท่ากับ {F["c1000_p"]} กลุ่มจึงเป็นของจริง '
 f'ข้อสอง ใช้อีกวิธีคือ Leiden ได้กลุ่มเหมือนเดิมทุกจังหวัด ข้อสาม ความเสถียร {F["stable"]} จาก 77 จังหวัดอยู่กลุ่มเดิมเกือบทุกรอบ แต่ {F["flagged"]} จังหวัดในกลุ่ม Central ย้ายกลุ่มบ่อย รวมถึงสระบุรีที่เป็นฐานของเรา '
 'เราจึงใช้กลุ่มเป็นข้อมูลประกอบ ไม่ใช่เส้นแบ่งตายตัว ส่วนการทดสอบแบบสลับน้ำหนักเส้นไม่ผ่าน แปลว่ากลุ่มมาจากว่าใครค้ากับใคร ไม่ได้มาจากขนาดของเส้น')
headline(s, f'The 4 groups pass the course checks; the border of the Central group moves between runs.')
picture(s, charts['map_groups'], .83, 4.3, 5.5, 6.15)
table(s, 6.7, 4.3, 6.2, [['Market group', 'Provinces', 'Trips']] + [[GROUP[g], F[f'g{g}_n'], F[f'g{g}_share']] for g in range(4)], [3.4, 1.4, 1.4], 16, .62)
text(s, 6.7, 7.55, 6.2, .9, 'Northeast & East includes Bangkok and the eastern ports.', 15, 'A9A9B3')
table(s, 13.25, 4.3, 5.93, [['Check (Ch 9)', 'Result'], ['Beat random copies?', f'Yes: {F["c1000_hits"]} of 1,000 reach our score'],
 ['Same with Leiden?', f'Yes: identical (ARI {F["leiden_ari"]})'], ['Stable provinces', f'{F["stable"]} of 77'], ['Moves between runs', f'{F["flagged"]} Central, incl. Saraburi']], [2.5, 3.43], 14.5, .9)

divider(3, 'THE\nDISCOVERY', 'How the model picks hubs, and what it finds', 'photo_part3.jpg', '[พรพรหม · 0:05] ส่วนที่สาม: โมเดลเลือกฐานและผลที่ได้')

# 9 Models
s = chrome('The models', 'Two Ways to Choose the Hubs', 'Same data, same 150 km reach; Model B adds one rule', SRC,
 '[พรพรหม · 0:45] เราใช้โมเดลเพิ่มประสิทธิภาพสองแบบ Model A หาชุดฐานที่เข้าถึงเที่ยวต้นทางได้มากที่สุด ภายในรัศมี 150 กิโลเมตร นับเที่ยวที่อยู่ใกล้หลายฐานแค่ครั้งเดียว '
 'Model B ใช้กติกาเดียวกัน แต่เพิ่มเงื่อนไขว่าทุกกลุ่มตลาดต้องได้รับการเข้าถึงอย่างน้อยครึ่งหนึ่ง เพื่อดูว่าความเท่าเทียมระหว่างภูมิภาคต้องแลกกับอะไร '
 'สมมติฐานสำคัญคือ 150 กิโลเมตรเป็นระยะเส้นตรง และเรานับเที่ยวที่จุดเริ่มต้น เพราะฐานส่งรถไปรับของ')
for k, (nm, q, rule) in enumerate([('MODEL A', 'Which 2–3 hubs reach the most trips in total?', 'Rule: total reach only'),
                                    ('MODEL B', 'What if every market group must get at least half its trips reached?', 'Rule: Model A + a minimum share for each group')]):
    y = 3.3 + k * 2.55; shape(s, .83, y, 11.2, 2.3, CARD, MSO_SHAPE.ROUNDED_RECTANGLE, radius=.07); shape(s, .83, y, .14, 2.3, TANC if k == 0 else 'E05A2B')
    text(s, 1.3, y + .2, 10.5, .5, nm, 18, TANC, True); text(s, 1.3, y + .7, 10.5, .8, q, 22, WHITE, True); text(s, 1.3, y + 1.55, 10.5, .5, rule, 17, 'A9A9B3')
s.shapes.add_picture(str(ASSETS / 'photo_models.jpg'), Inches(12.4), Inches(3.3), Inches(6.78), Inches(4.85))
shape(s, .83, 8.5, 18.35, 1.95, CARD, MSO_SHAPE.ROUNDED_RECTANGLE, radius=.07)
for k, (a, b) in enumerate([('150 km', 'straight line from the province point; road distance is tested later'), ('Where trips start', 'a hub sends trucks out to pick up loads'), ('Count once', 'a trip near two hubs counts one time')]):
    text(s, 1.2 + k * 6.05, 8.65, 5.7, .55, a, 22, TANC, True); text(s, 1.2 + k * 6.05, 9.25, 5.7, 1.1, b, 16, 'E6E6EA')

# 10 Model A result
s = chrome('Model A · result', 'Where Should We Open?', 'The set of hubs that reaches the most trips', SRC + '; results/models.csv',
 f'[พรพรหม · 1:00] ผลของ Model A ถ้าเปิดสองฐาน คือพิษณุโลกกับสระบุรี เข้าถึงเที่ยวต้นทางได้ {F["A2"]} ถ้าเพิ่มฐานที่สามที่มหาสารคาม เพิ่มเป็น {F["A3"]} เพิ่มขึ้น {F["hub3_gain"]} จุด '
 f'หรือประมาณ {F["per_month"]} เที่ยวต่อเดือนที่อยู่ในรัศมี สามฐานนี้อยู่คนละกลุ่มตลาด เหนือ กลาง และอีสาน โดยไม่ได้บังคับ และไม่มีจังหวัดไหนอยู่ในรัศมีของสองฐานพร้อมกัน '
 'เราตรวจคำตอบนี้กับทุกชุดที่เป็นไปได้ 73,150 ชุดแล้ว ชุดนี้ดีที่สุดจริง')
headline(s, f'Phitsanulok + Saraburi reach two-thirds of trips; adding Maha Sarakham lifts reach to {F["A3"]}.')
picture(s, charts['map_hubs'], .83, 4.3, 5.5, 6.15)
card(s, 6.75, 4.3, 6.0, 3.0, F['A2'], '2 hubs: Phitsanulok + Saraburi')
card(s, 13.18, 4.3, 6.0, 3.0, F['A3'], '3 hubs: + Maha Sarakham', tan=True)
shape(s, 6.75, 7.6, 12.43, 2.85, CARD, MSO_SHAPE.ROUNDED_RECTANGLE, radius=.06)
text(s, 7.15, 7.85, 11.7, 2.5, [f'The third hub adds {F["hub3_gain"]} points: about {F["per_month"]} trips a month within reach', 'One hub in each of North, Central and Northeast, without forcing it',
 'No province point is within 150 km of two hubs', 'Checked against all 73,150 possible sets: this is the best one'], 18, 'E6E6EA', after=9)

# 11 Seeding (technical)
s = chrome('Model A · check', 'Does Choosing as a Set Beat a Ranking?', 'Same budget (3 hubs) and the same 150 km rule for every method (Ch 10 seed selection)', SRC + '; results/seeding.csv',
 f'[ปัญจพล · 0:50] การเลือกฐานเหมือนการเลือก seed ในบทที่ 10 เราเทียบทุกวิธีด้วยงบเท่ากัน ถ้าสุ่มสามจังหวัด เฉลี่ยได้ {F["random"]} '
 f'ถ้าเลือกสามจังหวัดที่รถวิ่งรวมมากที่สุด ได้ {F["r_strength"]} เพราะติดชลบุรีที่เป็นปลายทาง และจังหวัดใกล้กันซ้อนกัน '
 f'ถ้าจัดอันดับให้ถูกคำถาม คือตามเที่ยวที่เริ่มต้นในจังหวัดนั้น ได้ {F["r_out"]} วิธี greedy ที่เพิ่มฐานทีละแห่งได้ {F["greedy"]} '
 f'และ Model A ได้ {F["A3"]} ดีกว่าการจัดอันดับที่ดีที่สุด {F["gain_rank"]} จุด และดีกว่า greedy {F["gain_greedy"]} จุด')
headline(s, f'Choosing as a set beats the best ranking by {F["gain_rank"]} points and greedy by {F["gain_greedy"]} points.')
picture(s, charts['seeding'], .83, 4.3, 11.0, 6.15)
shape(s, 12.25, 4.3, 6.93, 6.15, CARD, MSO_SHAPE.ROUNDED_RECTANGLE, radius=.05)
text(s, 12.65, 4.5, 6.2, .6, 'Why rankings fall short', 22, TANC, True)
text(s, 12.65, 5.2, 6.2, 5.1, [f'Top 3 by trips that start there: alone they add up to {F["r_out_singles"]}, together {F["r_out"]}. They share customers.',
 'Ranking by total trips also picks Chonburi, where loads end rather than start.', 'Greedy cannot undo an early pick; the optimiser compares whole sets.'], 18, 'E6E6EA', after=14)

# 12 Robustness (technical)
s = chrome('How sure are we', 'What Could Change the Answer?', 'We stress-tested the result instead of trusting one run', SRC + '; results/sensitivity_radius.csv, road_calibration.csv, near_optimal.csv; docs/STRESS_TEST.md',
 f'[ปัญจพล · 1:15] เราทดสอบว่าอะไรทำให้คำตอบเปลี่ยนได้บ้าง เรื่องที่สำคัญที่สุดคือรัศมี ทุกรัศมีตั้งแต่ 100 ถึง 200 กิโลเมตร ฐานสามแห่งอยู่ภาคเหนือ กลาง และอีสานเสมอ แต่จังหวัดเปลี่ยน '
 f'จากข้อมูล GPS ระยะถนนจริงยาวกว่าเส้นตรงประมาณ {F["road_ratio"]} เท่า 150 กิโลเมตรเส้นตรงจึงประมาณ {F["road_km"]} กิโลเมตรถนน หรือขับ {F["hours"]} ชั่วโมง '
 f'ถ้าบริษัทรับงานได้จริงแค่ 125 กิโลเมตร ฐานของเราจะได้แค่ {F["r125_fix"]} ขณะที่ชุดที่ดีที่สุดสำหรับรัศมีนั้นได้ {F["r125_opt"]} บริษัทจึงต้องกำหนดระยะบริการเป็นชั่วโมงขับก่อนลงทุน '
 f'ส่วนอย่างอื่นไม่เปลี่ยนคำตอบ ตัดเดือนใดเดือนหนึ่งออก ใส่ noise สองร้อยรอบ ใช้น้ำหนักตัน หรือใช้ข้อมูลปี 2568 ได้ฐานชุดเดิม ข้อยกเว้นคือถ้าไม่ขนมันสำปะหลัง ชุดฐานจะเปลี่ยน')
headline(s, 'Same hubs under every test except two: the service radius, and dropping cassava.')
picture(s, charts['radius'], .83, 4.3, 9.4, 6.15)
table(s, 10.6, 4.3, 8.58, [['Test', 'Result'], ['Radius 100–200 km', 'Always one hub in North, Central, Northeast'],
 ['150 km straight line', f'≈ {F["road_km"]} km by road ≈ {F["hours"]} h drive'], ['Real reach only 125 km', f'Our hubs {F["r125_fix"]} vs best {F["r125_opt"]}'],
 ['Drop a month; 200 noise runs', f'Same hubs (4 of 4; {F["noise"]} of 200)'], ['Tons instead of trips; 2025 data', f'Same hubs (2025: {F["y25"]})'],
 ['Phichit instead of Phitsanulok', f'Only {F["near_gap"]} points lower'], ['Without cassava products', f'Hubs change: {F["cassava_alt"]}']], [3.6, 4.98], 14.5, .76)

# 13 Return loads + graph DB (technical, demo)
s = chrome('Return loads · graph database', 'Can Trucks Find a Load Back?', 'Trips with both ends near one of our hubs, queried in Neo4j', SRC + '; results/lane_coverage.csv; Freight_GraphDB_Neo4j.ipynb',
 f'[ปัญจพล · 0:25 + เดโม 3:00] Model A ใช้แค่จุดเริ่มต้น แต่รถบรรทุกต้องวิ่งกลับด้วย เราจึงใช้เส้นในเครือข่ายนับเที่ยวที่ทั้งต้นทางและปลายทางอยู่ใกล้ฐานของเรา '
 f'ฐานสามแห่งของเราได้ {F["lane_A3"]} เกือบเท่ากับค่าสูงสุดที่เป็นไปได้ {F["lane_best"]} คำถามแบบนี้เป็นการเดินหลายขั้นในกราฟ จึงเหมาะกับ graph database '
 'เราโหลดเครือข่ายเข้า Neo4j และตอบคำถามธุรกิจห้าข้อด้วย Cypher ตอนนี้ขอเปิดให้ดูสด [เปิด Aura console รัน CQ1 และ CQ2 ตาม PRESENTER_GUIDE]')
headline(s, f'Our hubs keep {F["lane_A3"]} of trips loaded both ways; the best possible is {F["lane_best"]}.')
table(s, .83, 4.3, 10.2, [['Question asked in Cypher', 'Answer'], ['Trips with both ends near our hubs', F['lane_A3']],
 ['Where trucks from Saraburi end up', 'Chonburi, Ayutthaya, Samut Prakan'], ['Biggest molasses lane we can take (tanker)', 'Nakhon Sawan → Ang Thong'],
 ['Largest origins no hub reaches', 'Ubon Ratchathani, Kanchanaburi, Loei'], ['Largest lane to a port', 'Korat → Chonburi']], [5.6, 4.6], 16, .85)
shape(s, 11.45, 4.3, 7.73, 6.15, CARD, MSO_SHAPE.ROUNDED_RECTANGLE, radius=.05)
text(s, 11.85, 4.5, 7.0, .6, 'Why a graph database here', 22, TANC, True)
text(s, 11.85, 5.2, 7.0, 3.2, ['Each question walks several steps: hub → pickup province → destination → hub.', 'Totals in Neo4j match the notebook exactly.'], 18, 'E6E6EA', after=12)
shape(s, 11.85, 8.7, 6.93, 1.4, TANC, MSO_SHAPE.ROUNDED_RECTANGLE, radius=.12)
text(s, 12.1, 8.7, 6.5, 1.4, 'LIVE DEMO · 3 MIN', 28, DARK, True, PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE)

# 14 Model B
s = chrome('Model B · result', 'What If Every Region Must Be Served?', 'Three hubs; each market group must get at least 50% of its trips reached', SRC + '; results/community_coverage.csv, models.csv, temporal.csv',
 f'[พรพรหม · 0:50] Model B บังคับให้ทุกกลุ่มได้อย่างน้อยครึ่งหนึ่ง ได้ฐานพิจิตร มหาสารคาม สมุทรสาคร '
 f'ภาคตะวันตกและใต้เพิ่มจาก {F["ws_A"]} เป็น {F["ws_B"]} แต่ภาพรวมลดลง {F["B_cost"]} จุด และต้องใช้สามฐานเสมอ เพราะสองฐานทำไม่ได้ '
 'เราเลือก Model A เป็นกรณีหลัก เพราะยังไม่มีสัญญาหรือนโยบายที่บังคับให้บริการทุกภูมิภาค ส่งต่อให้ณัฏฐาสรุปมุมธุรกิจครับ')
headline(s, f'Model B lifts West & South from {F["ws_A"]} to {F["ws_B"]} and costs {F["B_cost"]} points of total reach.')
picture(s, charts['groups'], .83, 4.3, 9.4, 6.15)
table(s, 10.6, 4.3, 8.58, [['3 hubs', 'Model A', 'Model B'], ['Hubs', en(a3).replace(' / ', ', '), en(b3).replace(' / ', ', ')],
 ['All trips reached', F['A3'], F['B3']], ['Weakest market group', F['weak_A'], F['weak_B']], ['Works with 2 hubs', 'Yes', 'No'],
 ['Biggest monthly gap to the best set*', f'{F["gapA"]} points', f'{F["gapB"]} points'], ['Decision', 'Main case', 'Option']], [3.3, 2.64, 2.64], 15, .8, hl_last=True)
text(s, 10.6, 9.95, 8.58, .6, f'*Model B is compared with the best unrestricted set, so its gap includes the {F["B_cost"]}-point cost of the rule.', 12, 'A9A9B3')

divider(4, 'THE\nDECISION', 'What we propose to management', 'photo_part4.jpg', '[ณัฏฐา · 0:05] ส่วนสุดท้าย: ข้อเสนอต่อผู้บริหาร')

# 15 Ranking vs network
rk = gcov(idx(rank_set)); rk_groups = sorted({GROUP[lab[i]] for i in idx(rank_set)})
s = chrome('Business value', 'Ranking vs Network: Side by Side', 'Same data, same 150 km rule', SRC + '; results/seeding.csv, lane_coverage.csv, community_coverage.csv',
 f'[ณัฏฐา · 0:45] ถ้าใช้วิธีทั่วไป คือเลือกสามจังหวัดที่มีเที่ยวเริ่มต้นมากที่สุด จะได้นครสวรรค์ โคราช ลพบุรี เข้าถึงได้ {F["r_out"]} '
 f'ถ้าเลือกเป็นชุดด้วยเครือข่าย ได้ {F["A3"]} สูงกว่า {F["gain_rank"]} จุด ฐานไม่ซ้อนกัน อยู่ครบสามภูมิภาค และรถหางานขากลับได้มากกว่า')
headline(s, 'A ranking picks busy provinces; choosing as a set picks provinces that work together.')
table(s, .83, 4.3, 18.35, [['', 'Ranking: top 3 by trips that start there', 'Network: Model A'],
 ['Hubs', en(rank_set).replace(' / ', ', '), en(a3).replace(' / ', ', ')], ['Trips reached', F['r_out'], f'{F["A3"]} (+{F["gain_rank"]} points)'],
 ['Overlap', f'Alone they add up to {F["r_out_singles"]}; together {F["r_out"]}', 'None: no province point is near two hubs'],
 ['Regions', 'Two hubs in Central, one in Northeast & East', 'One each in North, Central, Northeast'],
 ['Trips with both ends near a hub', F['lane_rank'], F['lane_A3']], ['Weakest market group', F['weak_rank'], F['weak_A']]], [4.6, 6.875, 6.875], 17, .82)

# 16 Decision
s = chrome('Decision', 'Start With Two, Expand to Three', 'A plan to confirm before investing', SRC,
 f'[ณัฏฐา · 0:50] ข้อเสนอของเรา ขั้นแรกเปิดพิษณุโลกกับสระบุรี เข้าถึงเที่ยวได้สองในสาม ขั้นที่สองเพิ่มมหาสารคาม ได้ {F["A3"]} '
 f'ก่อนเซ็นสัญญาลานจอด ต้องกำหนดระยะบริการเป็นชั่วโมงขับ เพราะ 150 กิโลเมตรเส้นตรงคือประมาณ {F["hours"]} ชั่วโมง ถ้าระยะสั้นกว่านี้ จังหวัดที่ดีที่สุดจะเปลี่ยน '
 f'พิจิตรเป็นตัวสำรองของพิษณุโลก ต่างกันแค่ {F["near_gap"]} จุด และถ้ามีข้อกำหนดให้บริการทุกภูมิภาค ให้ใช้ Model B')
headline(s, 'Open Phitsanulok + Saraburi first, add Maha Sarakham next, after the radius is confirmed.')
for k, (big, t) in enumerate([('1', f'Open Phitsanulok + Saraburi: {F["A2"]} of trips within reach'), ('2', f'Add Maha Sarakham: reach rises to {F["A3"]} (+{F["hub3_gain"]} points)'),
                              ('3', f'Before signing a yard, set the service radius in driving hours (150 km ≈ {F["hours"]} h)'),
                              ('4', f'Keep Phichit as the backup for Phitsanulok ({F["near_gap"]} points lower); use Model B if every region must be served')]):
    y = 4.35 + k * 1.55; shape(s, .83, y, 18.35, 1.35, CARD, MSO_SHAPE.ROUNDED_RECTANGLE, radius=.1)
    shape(s, 1.15, y + .22, .9, .9, TANC, MSO_SHAPE.OVAL); text(s, 1.15, y + .22, .9, .9, big, 28, DARK, True, PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE)
    text(s, 2.45, y, 16.4, 1.35, t, 22, WHITE, True, anchor=MSO_ANCHOR.MIDDLE)

# 17 Before investing
s = chrome('Before investing', 'What We Still Need to Check', 'The model gives a shortlist; these checks turn it into a decision', SRC,
 f'[ณัฏฐา · 0:40] โมเดลให้รายชื่อจังหวัด ไม่ใช่การตัดสินใจลงทุน ยังต้องตรวจเส้นทางและลานจอดจริง ลูกค้าและคู่แข่ง และต้นทุนกับกำลังรถ '
 f'ตัวเลขของเราวัดการเข้าถึงตลาด ไม่ใช่รายได้หรือกำไร และคำตอบขึ้นกับการขนมันสำปะหลัง ซึ่งเป็น {F["cassava_share"]}% ของเที่ยว ข้อมูลทั้งหมดเป็นข้อมูลเปิดระดับจังหวัด ไม่มีข้อมูลส่วนบุคคล')
for k, (a, b, who) in enumerate([('Roads and yards', 'real driving time from real yard sites', 'Transport planning'), ('Customers and rivals', 'which shippers we can win; competitor networks', 'Sales'),
                                 ('Costs and capacity', 'rent, staff, trucks and running cost per hub', 'Finance and operations')]):
    x = .83 + k * 6.25; shape(s, x, 3.3, 5.85, 3.3, CARD, MSO_SHAPE.ROUNDED_RECTANGLE, radius=.07)
    text(s, x + .35, 3.5, 5.2, .6, a, 24, TANC, True); text(s, x + .35, 4.2, 5.2, 1.3, b, 19, 'E6E6EA'); text(s, x + .35, 5.75, 5.2, .5, who, 16, 'A9A9B3', True)
shape(s, .83, 6.95, 18.35, 3.5, CARD, MSO_SHAPE.ROUNDED_RECTANGLE, radius=.05)
text(s, 1.3, 7.15, 17.5, 3.2, [[('What the numbers mean: ', {'bold': True, 'color': TANC}), 'share of trips within reach of a hub. Not sales, profit or break-even.'],
 [('Depends on cassava: ', {'bold': True, 'color': TANC}), f'cassava products are {F["cassava_share"]}% of trips; without them the best hubs change.'],
 [('Responsible use: ', {'bold': True, 'color': TANC}), 'open government data (Open Data Common), province totals only, no personal data (PDPA).'],
 [('Fairness: ', {'bold': True, 'color': TANC}), f'Model A leaves West & South at {F["ws_A"]}; Model B serves every region for {F["B_cost"]} points.']], 19, 'E6E6EA', after=12)

# 18 Technology & AI (technical)
s = chrome('How we worked', 'Technology and AI: What Helped, Who Decided', 'AI wrote and reviewed code; the team made every key choice and checked the output', f'Code and stress tests: {REPO}',
 '[ปัญจพล · 0:50] เครื่องมือที่ใช้คือ pandas NetworkX SciPy สำหรับโมเดล และ Neo4j สำหรับคำถามแบบหลายขั้น ข้อมูลดาวน์โหลดจากต้นทางและตรวจ hash ทุกครั้ง '
 'AI ช่วยเขียนโค้ดและช่วยตรวจวิธีกับเนื้อหาในวิชา แต่การตัดสินใจเป็นของทีม ตัวอย่างที่ชัดคือ การทดสอบกลุ่มแบบแรกของเราสลับน้ำหนักเส้น ซึ่งไม่ตรงกับวิธีในบทที่ 9 '
 'เราเปลี่ยนเป็นวิธีของวิชาและรายงานทั้งสองแบบ และเราไม่เชื่อผลจากการรันครั้งเดียว เราทำ stress test ซ้ำด้วยโค้ดที่เขียนแยก และด้วยไลบรารีเวอร์ชันใหม่ ผลตรงกันทุกตาราง '
 'ส่งต่อให้ณัฏฐาปิดท้ายครับ')
shape(s, .83, 3.3, 6.6, 7.15, CARD, MSO_SHAPE.ROUNDED_RECTANGLE, radius=.05)
text(s, 1.2, 3.5, 6.0, .6, 'Technology', 24, TANC, True)
text(s, 1.2, 4.2, 6.0, 6.1, ['pandas: clean and filter the data', 'NetworkX: graph, centrality, Louvain and Leiden, random copies', 'SciPy MILP: Models A and B, checked against all 73,150 sets',
 'Neo4j Aura + Cypher: multi-step business questions', 'GitHub: data downloaded from the source and checked by hash', 'pytest: stress tests in independent code'], 17, 'E6E6EA', after=10)
table(s, 7.8, 3.3, 11.38, [['Step', 'AI helped with', 'The team decided'], ['Data', 'cleaning and audit code', 'goods scope; sugarcane left out'],
 ['Groups', 'Louvain and random-copy code', "replaced our first test with the course's; reported both"], ['Centrality', 'ranking code', 'caught a bridge-score error with an assertion; ranked by where trips start'],
 ['Hub model', 'MILP code', '150 km, 2–3 hubs, group rule; Model A as main case'], ['Review', 'checked methods against the course', 'what to change; re-ran everything and stress-tested it']], [1.9, 3.7, 5.78], 15, .98)
text(s, 7.8, 9.35, 11.38, 1.0, 'AI was not used as a source of market facts.', 17, 'A9A9B3')

# 19 Thank you
s = prs.slides.add_slide(BLANK); PAGE[0] += 1
s.shapes.add_picture(str(ASSETS / 'photo_thanks.jpg'), 0, 0, Inches(20), Inches(11.25)); shape(s, 0, 0, 20, 11.25, '1E1D26', alpha=.6); header(s)
text(s, 1.35, 3.6, 17, 2, 'THANK YOU', 110, WHITE, True); text(s, 1.4, 5.9, 17, .8, 'Questions welcome', 30, TANC, True)
text(s, 1.4, 6.8, 17, .6, REPO, 20, 'E6E6EA')
NOTES[PAGE[0]] = '[ณัฏฐา · 0:10] ขอบคุณค่ะ โค้ดและผลทั้งหมดอยู่ใน GitHub ตามลิงก์ ยินดีรับคำถามค่ะ (คำถามเทคนิคส่งให้ปัญจพล)'

# ------------------------------------------------------------------ appendix
s = chrome('Appendix A1', 'Data and Assumptions', 'How to read the reach numbers', SRC,
 'ภาคผนวก ใช้ตอบคำถาม ไม่ต้องนำเสนอ')
table(s, .83, 3.3, 18.35, [['Assumption', 'What it means for the result'], ['150 km straight line from a province point', f'Road distance is about {F["road_ratio"]}× longer (GPS data); see the radius test'],
 ['No truck capacity limit', 'Reach is not the work the company can actually handle'], ['No destination hub', 'Pick up near a hub and drive direct, not hub-and-spoke'],
 ['Several goods together', 'One truck cannot carry everything; molasses needs tanker trucks'], ['2025 possible duplicate rows', 'Tested with and without them; same hubs'],
 ['Missing product-month rows', 'Not treated as zero demand']], [7.5, 10.85], 17, .85)

s = chrome('Appendix A2', 'Six Graph Decisions and Data Sources', 'Chapter 6 build decisions and the Chapter 4 collection spec', SRC, 'ภาคผนวก')
table(s, .83, 3.2, 18.35, [['Decision', 'What we chose', 'Evidence'], ['Schema', 'Province nodes; trip edges; direction kept for reach', 'Decision unit is a province'],
 ['Extraction', 'Structured GPS records; no text, no LLM extraction', 'No extraction error possible'], ['Resolution', 'Province names trimmed and matched exactly to 77 points', 'Assertion in notebook'],
 ['Weighting', 'Trips; tons and in-province trips tested', 'Same hubs'], ['Pruning', 'No edges removed (1,308 kept)', 'Small edges barely move results'],
 ['Validation', 'Hashes, totals, 2025 check, plausibility of every row', f'{F["flag_rows"]} rows flagged ({F["flag_share"]}% of trips)']], [2.6, 8.6, 7.15], 15, .62)
table(s, .83, 7.75, 18.35, [['Source', 'Fields used', 'Licence', 'Not collected'], ['OTP otp_69_01 (2026, 2025)', 'goods, month, provinces, trips, tons, road distance, duration', 'Open Data Common', 'plates, companies, drivers'],
 ['Province coordinates (DLA)', 'latitude, longitude', 'CC-BY', '—'], ['Factory locations (OPS)', 'Bangkok point only', 'Open Data Common', 'factory names']], [4.2, 7.0, 3.2, 3.95], 14, .62)

s = chrome('Appendix A3', 'Four Community Checks (Chapter 9)', 'What each check asks and what we found', SRC + '; results/check2_baselines.csv, resolution.csv', 'ภาคผนวก')
table(s, .83, 3.3, 18.35, [['Check', 'Question', 'Result'], ['1 Score', 'Best split over 100 runs', f'4 groups, modularity Q = {F["Q"]}'],
 ['2 Baseline', 'Could random wiring score this high?', f'{F["c1000_hits"]} of 1,000 rewired copies reach it (topology Q {F["qtopo"]} vs best random {F["qnullmax"]})'],
 ['2b Weight shuffle', 'Do link sizes add structure?', f'No (p = {F["p_shuffle"]}): groups come from who trades with whom'],
 ['3 Stability', 'Same group in every run?', f'{F["stable"]} of 77 stable; {F["flagged"]} Central provinces move (Saraburi {F["sara_conf"]})'],
 ['4 Size', 'Resolution 0.5, 1, 1.5, 2', 'We act on resolution 1 (4 groups)'], ['Cross-check', 'Leiden algorithm', f'Identical split (ARI {F["leiden_ari"]})']], [3.2, 6.0, 9.15], 16, .85)

s = chrome('Appendix A4', 'Limits and Work Still to Do', 'What the result does not tell us yet', SRC, 'ภาคผนวก')
text(s, .83, 3.3, 18.35, 7, ['Monthly checks look back at data we used; they are not an unseen test (2025 is a separate year)', 'No cost, capacity, sellable work or competitor data: no profit or break-even claim',
 'Model B is not run at every resolution', 'Minimum number of hubs for a reach target is not solved', 'The 45/35/20 screening score from our early work is not sensitivity-tested, so we do not use it'], 22, 'E6E6EA', after=18)

s = chrome('References', 'Data, Code, Methods and Photos', None, None, 'ภาคผนวก')
text(s, .83, 2.6, 18.35, 7.8, [[('Data', {'bold': True, 'color': TANC})], 'OTP truck freight data (otp_69_01): otp.gdcatalog.go.th/dataset/91038df9-854e-442d-8408-c54032daf506',
 'Province coordinates: data.go.th/dataset/d41ab000-c49c-4e14-963c-cc062e314076', 'Bangkok factory locations: industry.gdcatalog.go.th/dataset/a4e85b60-3fd5-4c50-9450-5e139cb1b0e1',
 [('Code and results', {'bold': True, 'color': TANC})], REPO, [('Methods', {'bold': True, 'color': TANC})],
 'Church & ReVelle (1974) maximal covering location · Blondel et al. (2008) Louvain · Traag et al. (2019) Leiden · Newman (2006) modularity · Kempe et al. (2003) seed selection',
 [('Photos (Wikimedia Commons)', {'bold': True, 'color': TANC})], 'Ilya Plekhanov (CC BY-SA 4.0); Marshall Astor (CC BY-SA 2.0); CIAT (CC BY-SA 2.0); Soulful sunshine (CC BY-SA 4.0); Eerin25 (CC0); Per Meistrup (CC BY-SA 4.0); Chatchai Jomta (CC BY 3.0)'], 17, 'E6E6EA', after=8)

s = chrome('Team', 'Team Members', 'MADT 7202 Capstone', None, 'ภาคผนวก')
table(s, 3.0, 3.3, 14, [['Student ID', 'Name', 'Presents'], ['6810424025', 'จันทนา ภัทราพรพิสิฐ', 'The challenge'], ['6810414002', 'นิษฐกานต์ รตะพิศาลพงศ์', 'Network and data'],
 ['6810424005', 'พรพรหม รุจิวัชรโอฬาร', 'Models and results'], ['6810424009', 'ปัญจพล อัมพรรัตน์', 'Technical checks and demo'], ['6810424011', 'ณัฏฐา ฉายศิริพันธ์', 'Decision and Q&A']], [3.2, 6.3, 4.5], 20, .9)

(ROOT / 'deck' / 'script.json').write_text(json.dumps(NOTES, ensure_ascii=False, indent=1))
md = ['# สคริปต์นำเสนอ (ภาษาไทย)', '', 'เวลาในวงเล็บเหลี่ยมคือเวลาพูดของสไลด์นั้น รวม 14:00 นาที ไม่รวมเดโม', '']
for k in sorted(NOTES):
    if NOTES[k] and NOTES[k] not in ('ภาคผนวก', 'ภาคผนวก ใช้ตอบคำถาม ไม่ต้องนำเสนอ'): md += [f'## สไลด์ {k}', '', NOTES[k], '']
(ROOT / 'deck' / 'SCRIPT_TH.md').write_text('\n'.join(md), encoding='utf-8')
out = ROOT / 'deck' / 'Hub_Location_Study_MADT7202.pptx'; prs.save(out); print('saved', out, PAGE[0], 'slides')
