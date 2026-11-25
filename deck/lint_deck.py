"""Check the deck: (1) banned AI-style phrasing, (2) every number traces to deck/facts.json,
(3) text fits its box (measured with Arial metrics). Exit code 1 on any problem.
Run from the repo root:  python deck/lint_deck.py
"""
import json, re, sys
from pathlib import Path
from PIL import ImageFont
from pptx import Presentation
from pptx.util import Emu

ROOT = Path(__file__).resolve().parents[1]
prs = Presentation(ROOT / 'deck' / 'Hub_Location_Study_MADT7202.pptx')
facts = json.loads((ROOT / 'deck' / 'facts.json').read_text())

BANNED = ['leverage', 'unlock', 'seamless', 'robust', 'delve', 'game-changer', 'game changer', 'cutting-edge', 'holistic', 'synergy',
          'empower', 'journey', 'landscape', 'not just', 'in today', 'harness', 'paradigm', 'revolutioniz', 'transformative', 'unleash',
          'elevate', 'navigate the', 'deep dive', 'at the end of the day', 'it is worth noting', 'crucial', 'pivotal', 'tapestry', 'realm',
          'insightful', 'powerful', 'state-of-the-art', 'best-in-class', 'world-class', 'actionable', 'streamline', 'supercharge']
# numbers that are structure, not findings (slide furniture, course facts, problem setup, citations)
FIXED = {'2', '3', '4', '7', '10', '77', '76', '150', '100', '125', '200', '0.5', '1', '1.5', '2025', '2026', '2,926', '73,150', '1,000', '1,308',
         '50', '45', '35', '20', '6', '9', '13', '12', '7202', '2569', '2568', '0', '5', '30', '15', '3:00', '0:05'}
CITE = {'1974', '2008', '2019', '2006', '2003', '4.0', '2.0', '3.0'}
allowed = set(FIXED) | CITE
for v in facts.values():
    allowed |= set(re.findall(r'\d[\d,]*(?:\.\d+)?', str(v)))

problems = []
TIGHT = []
num_re = re.compile(r'(?<![\w.])\d[\d,]*(?:\.\d+)?')
font_dir = Path('/System/Library/Fonts/Supplemental')
fonts = {}
def font(size, bold, thai):
    name = ('Tahoma Bold.ttf' if bold else 'Tahoma.ttf') if thai else ('Arial Bold.ttf' if bold else 'Arial.ttf')
    key = (name, size)
    if key not in fonts: fonts[key] = ImageFont.truetype(str(font_dir / name), size * 10)
    return fonts[key]

def lines_needed(text, size, bold, width_pt):
    thai = bool(re.search(r'[฀-๿]', text)); f = font(size, bold, thai); n = 0
    for para in text.split('\n'):
        words, line = para.split(' '), ''
        n += 1
        for wd in words:
            trial = (line + ' ' + wd).strip()
            if f.getlength(trial) / 10 > width_pt and line: n += 1; line = wd
            else: line = trial
    return n

def frame_height(tf, width_pt):
    h = 0
    for p in tf.paragraphs:
        txt = ''.join(r.text for r in p.runs)
        if not p.runs: continue
        size = max(r.font.size.pt for r in p.runs if r.font.size); bold = any(r.font.bold for r in p.runs)
        ls = p.line_spacing if isinstance(p.line_spacing, float) else 1.0
        h += lines_needed(txt, size, bold, width_pt) * size * 1.2 * ls + (p.space_after.pt if p.space_after else 0)
    return h

pt = lambda emu: Emu(emu).pt
for i, s in enumerate(prs.slides, 1):
    texts = []
    for sh in s.shapes:
        if sh.has_text_frame and sh.text_frame.text.strip():
            texts.append(sh.text_frame.text)
            need = frame_height(sh.text_frame, pt(sh.width) - 7.2)
            TIGHT.append((need / pt(sh.height), i, sh.text_frame.text[:45].replace('\n', ' ')))
            if need > pt(sh.height) * 1.04 + 2: problems.append(f'slide {i}: text overflows box by {need - pt(sh.height):.0f}pt: "{sh.text_frame.text[:50]}"')
            if pt(sh.left + sh.width) > 20 * 72 + 1 or pt(sh.top + sh.height) > 11.25 * 72 + 1: problems.append(f'slide {i}: box outside slide: "{sh.text_frame.text[:40]}"')
        if sh.has_table:
            tbl = sh.table; total = 0
            for r_i, row in enumerate(tbl.rows):
                need_row = pt(row.height)
                for c_i, cell in enumerate(row.cells):
                    texts.append(cell.text)
                    need_row = max(need_row, frame_height(cell.text_frame, pt(tbl.columns[c_i].width) - 17.3) + 7)
                if need_row > pt(row.height) + 2: problems.append(f'slide {i}: table row {r_i} needs {need_row:.0f}pt, has {pt(row.height):.0f}pt: "{row.cells[0].text[:30]}"')
                total += need_row
            if pt(sh.top) + total > 10.55 * 72: problems.append(f'slide {i}: table runs into the footer ({(pt(sh.top) + total) / 72:.2f} in)')
    notes = s.notes_slide.notes_text_frame.text if s.has_notes_slide else ''
    blob = '\n'.join(texts)
    for b in BANNED:
        if b in blob.lower(): problems.append(f'slide {i}: banned phrase "{b}"')
    if blob.count('—') - sum(t.strip() == '—' for t in texts) > 0: problems.append(f'slide {i}: em dash in slide text')
    scan = '\n'.join(t for t in texts if not re.fullmatch(r'\d\d', t.strip())) + '\n' + notes
    scan = re.sub(r'\S+\.\S+/\S+', ' ', scan)                      # URLs and dataset ids
    scan = re.sub(r'\b\d+:\d\d\b|\b68104\d{5}\b|SHA-256', ' ', scan)  # speaking times, student IDs, hash name
    for tok in num_re.findall(scan):
        if tok.rstrip('.,') not in allowed: problems.append(f'slide {i}: number "{tok}" is not in facts.json')

total = 0
for i, s in enumerate(prs.slides, 1):
    nt = s.notes_slide.notes_text_frame.text if s.has_notes_slide else ''
    m = re.match(r'\[[^·]+· (\d+):(\d\d)', nt)
    if not m: continue
    sec = int(m[1]) * 60 + int(m[2]); total += sec
    words = re.sub(r'^\[[^\]]*\]', '', nt)
    rate = len(re.sub(r'\s', '', words)) / sec  # Thai speech ~ 11-13 characters per second
    if rate > 14: print(f'note: slide {i} script is brisk for {m[1]}:{m[2]} ({rate:.0f} chars/s); rehearse the pace')
print(f'Speaking time (without demo): {total // 60}:{total % 60:02d}')
print(f'{len(prs.slides)} slides checked; tightest text fits (need / have, pt):')
for r in sorted(TIGHT, reverse=True)[:6]: print(f'  {r[0]:.2f}  slide {r[1]}: {r[2]}')
print('\n'.join(problems) if problems else 'OK: no banned phrasing, every number traced, all text fits')
sys.exit(1 if problems else 0)
