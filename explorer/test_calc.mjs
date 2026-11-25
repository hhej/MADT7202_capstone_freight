// Checks the explorer's JavaScript calculations against the Python/notebook results.  Run: node explorer/test_calc.mjs
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const Calc = require('./calc.js');
const fs = require('fs');
const D = JSON.parse(fs.readFileSync(new URL('./data.json', import.meta.url), 'utf8'));
let fails = 0;
const check = (name, ok, got) => { console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${ok ? '' : '  got ' + JSON.stringify(got)}`); if (!ok) fails++; };
const near = (a, b, tol = 1e-6) => Math.abs(a - b) < tol;
const sameSet = (a, b) => a.length === b.length && [...a].sort((x, y) => x - y).every((v, i) => v === [...b].sort((x, y) => x - y)[i]);

const all = D.products.map(() => true);
const w = Calc.weights(D, all, 'trips');
const A = Calc.reach(D.dist, 150);
check('total interprovince trips = 990,030', w.reduce((s, x) => s + x, 0) === 990030, w.reduce((s, x) => s + x, 0));
const r150 = D.radius.filter(r => r.radius_km === 150);
check('Model A2 coverage matches notebook', near(Calc.coverage(D.models.A_2, w, A), r150.find(r => r.k === 2).coverage), Calc.coverage(D.models.A_2, w, A));
check('Model A3 coverage matches notebook', near(Calc.coverage(D.models.A_3, w, A), r150.find(r => r.k === 3).coverage), Calc.coverage(D.models.A_3, w, A));
for (const r of D.radius) {
  const b = Calc.best(r.k, w, Calc.reach(D.dist, r.radius_km));
  check(`best set = MILP at ${r.radius_km} km, k=${r.k}`, near(b.pct, r.coverage) && sameSet(b.hubs, r.hubs_idx), b);
}
const g = Calc.greedy(3, w, A);
check('greedy 3 hubs matches notebook', near(g[2].pct, D.seeding.find(s => s.k === 3 && s.method === 'Greedy').coverage), g[2]);
const T = Calc.tripMatrix(D, all);
check('lane coverage of A3 matches notebook', near(Calc.lane(D.models.A_3, T, A), D.lane.find(l => l.set === 'A_3').lane_coverage), Calc.lane(D.models.A_3, T, A));
const bl = Calc.bestLane(3, T, A);
check('best lane set matches notebook', near(bl.pct, D.lane.find(l => l.set === 'Lane-optimal' && l.k === 3).lane_coverage), bl);
const noCassava = D.products.map(p => p !== 'Cassava products');
const bc = Calc.best(3, Calc.weights(D, noCassava, 'trips'), A);
const expected = D.stress['3_perturbation'].leave_one_out['drop_product_ผลิตภัณฑ์มันสำปะหลัง'][0].map(th => D.nodes.findIndex(n => n.th === th));
check('no-cassava best set matches stress test', sameSet(bc.hubs, expected), bc);
const bt = Calc.best(3, Calc.weights(D, all, 'tons'), A);
check('weighting by tons gives the same 3 hubs', sameSet(bt.hubs, D.models.A_3), bt);
check('Model A3: no province within reach of two hubs', Calc.overlap(D.models.A_3, A) === 0, Calc.overlap(D.models.A_3, A));
console.log(fails ? `${fails} FAILED` : 'All checks passed');
process.exit(fails ? 1 : 0);
