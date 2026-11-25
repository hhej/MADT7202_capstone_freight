# Stress tests

Run with `pytest -q tests/` (about 7 minutes; needs the two OTP CSVs in `data/`). The code re-implements the analysis from the raw CSV without importing anything from the notebooks. Raw outputs are in `docs/stress_results.json`.

| # | Test | Result | Verdict |
|---|---|---|---|
| 1 | Independent re-implementation (numpy/pandas brute force over all 2,926 pairs and 73,150 triples) | Same A₂ (66.4%) and A₃ (82.3%); A₃ leads the next set by 0.52 points; ranking baselines 57.4% and 72.1%; lane coverage 75.48% vs best 75.56%; modularity 0.3314. All match `results/` | Pass |
| 2a | Louvain seeds 100–199 instead of 0–99 | Best split identical (ARI 1.00); every run gives 4 groups; mean ARI 0.90; Leiden over 20 seeds: lowest ARI 0.85 | Pass |
| 2b | Chapter 9 baseline with 1,000 rewired copies instead of 100 | 0 of 1,000 reach the observed score (topology Q 0.160 vs best random 0.080), p = 0.001 | Pass |
| 3a | Leave one month out (4 runs) | Same three hubs every time (81.8–83.0%) | Pass |
| 3b | Leave one product out (7 runs) | Same hubs in 6 of 7. **Without cassava products the best set becomes Bangkok / Phichit / Maha Sarakham** | Exception, reported in the deck |
| 3c | ±20% random noise on every row's trips (200 draws) | Same hubs in 200 of 200 | Pass |
| 3d | Bangkok proxy point moved 20 km north, south, east and west | Same hubs in 4 of 4 | Pass |
| 4 | Full 2025 data, radius 100–200 km | At 150 km our three hubs are also the best set in 2025 (83.0%). At 100 and 125 km the best sets differ and our hubs lose 18 points | Pass at 150 km; radius risk reported in the deck |
| 5 | Whole notebook on newer libraries (Python 3.13, pandas 3.1.1, numpy 2.5.5) | All 24 result tables identical | Pass |
| 6 | Deck checks (`deck/lint_deck.py`) | No banned phrasing; every number on the slides and in the notes traces to `deck/facts.json`; text fits every box by Arial metrics; speaking time 14:00 | Pass |
| 8 | Fresh clone of the public repo, data re-downloaded from the official source, notebook run from scratch | Data hashes match; all 29 result tables identical to the published ones | Pass |
| 7 | Secret scan before publishing (working tree and full git history) | No password, URI host or instance ID found | Pass |

## What this does not cover
- Every slide was rendered with macOS Quick Look (one file per slide) and checked by eye. Speaker notes are kept out of the .pptx because python-pptx notes pages stop Keynote and Quick Look from opening the file; the script is in `deck/SCRIPT_TH.md`. Check every slide once more after importing into Canva.
- Monthly checks within 2026 use data the model has seen; 2025 is the only separate year.
- Nothing here tests costs, truck capacity or competitors, because there is no data for them.
