// Hub-reach calculations used by the explorer page and by test_calc.mjs (same code in both places).
// All inputs are plain arrays built from DATA (see build_explorer.py).
const Calc = (() => {
  // Origin weights per province for the chosen products and measure ('trips' or 'tons').
  function weights(data, productMask, measure) {
    const w = new Float64Array(data.nodes.length);
    for (const [o, , p, trips, tons] of data.flows) if (productMask[p]) w[o] += measure === 'tons' ? tons : trips;
    return w;
  }
  // Directed trip matrix (row = origin, col = destination) for the chosen products.
  function tripMatrix(data, productMask) {
    const n = data.nodes.length, T = Array.from({ length: n }, () => new Float64Array(n));
    for (const [o, d, p, trips] of data.flows) if (productMask[p]) T[o][d] += trips;
    return T;
  }
  // reach[i][j] = province i is within R km (straight line) of a hub at j.
  function reach(dist, R) { return dist.map(row => row.map(km => km <= R)); }
  function covered(hubs, A) { return A.map(row => hubs.some(j => row[j])); }
  const sum = a => a.reduce((s, x) => s + x, 0);
  function coverage(hubs, w, A) {
    const c = covered(hubs, A); let s = 0;
    for (let i = 0; i < w.length; i++) if (c[i]) s += w[i];
    return 100 * s / sum(w);
  }
  // Share of trips whose origin AND destination are within reach of some hub (return-load lanes).
  function lane(hubs, T, A) {
    const c = covered(hubs, A); let s = 0, tot = 0;
    for (let i = 0; i < T.length; i++) for (let j = 0; j < T.length; j++) { tot += T[i][j]; if (c[i] && c[j]) s += T[i][j]; }
    return tot ? 100 * s / tot : 0;
  }
  function groupCoverage(hubs, w, A, groups, nGroups = 4) {
    const c = covered(hubs, A), num = new Array(nGroups).fill(0), den = new Array(nGroups).fill(0);
    for (let i = 0; i < w.length; i++) { den[groups[i]] += w[i]; if (c[i]) num[groups[i]] += w[i]; }
    return den.map((d, g) => (d ? 100 * num[g] / d : 0));
  }
  // Provinces within reach of two or more hubs.
  function overlap(hubs, A) { return A.map(row => hubs.filter(j => row[j]).length).filter(k => k >= 2).length; }
  // Exact best set for k = 1..3 by checking every combination (same answer as the MILP in the notebook).
  function best(k, w, A) {
    const n = w.length, total = sum(w);
    const cols = Array.from({ length: n }, (_, j) => A.map(row => row[j]));
    let bestVal = -1, bestSet = null;
    const score = set => { let s = 0; for (let i = 0; i < n; i++) if (set.some(j => cols[j][i])) s += w[i]; return s; };
    const rec = (start, set) => {
      if (set.length === k) { const v = score(set); if (v > bestVal + 1e-9) { bestVal = v; bestSet = set.slice(); } return; }
      for (let j = start; j < n; j++) { set.push(j); rec(j + 1, set); set.pop(); }
    };
    rec(0, []);
    return { hubs: bestSet, pct: 100 * bestVal / total };
  }
  // Greedy: add the hub that raises coverage most, one at a time. Returns every step.
  function greedy(k, w, A) {
    const steps = [], hubs = [];
    for (let s = 0; s < k; s++) {
      let bj = -1, bv = -1;
      for (let j = 0; j < w.length; j++) if (!hubs.includes(j)) { const v = coverage(hubs.concat(j), w, A); if (v > bv + 1e-12) { bv = v; bj = j; } }
      hubs.push(bj); steps.push({ hubs: hubs.slice(), pct: bv });
    }
    return steps;
  }
  // Exact best set for return-load lanes (k <= 3).
  function bestLane(k, T, A) {
    const n = T.length; let bv = -1, bs = null; const tot = sum(T.map(sum));
    const rec = (start, set) => {
      if (set.length === k) {
        const c = A.map(row => set.some(j => row[j])); let s = 0;
        for (let i = 0; i < n; i++) if (c[i]) for (let j = 0; j < n; j++) if (c[j]) s += T[i][j];
        if (s > bv + 1e-9) { bv = s; bs = set.slice(); } return;
      }
      for (let j = start; j < n; j++) { set.push(j); rec(j + 1, set); set.pop(); }
    };
    rec(0, []);
    return { hubs: bs, pct: 100 * bv / tot };
  }
  function topK(values, k) { return values.map((v, i) => [v, i]).sort((a, b) => b[0] - a[0]).slice(0, k).map(x => x[1]); }
  return { weights, tripMatrix, reach, covered, coverage, lane, groupCoverage, overlap, best, greedy, bestLane, topK };
})();
if (typeof module !== 'undefined') module.exports = Calc;
