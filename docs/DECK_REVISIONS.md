# Deck revision guide (Network Graph.pdf, 30 slides)

All numbers below come from `Freight_Capstone_TH.ipynb` §11 and the listed `results/` files. Sections 1–9 reproduce exactly.

## Must change (wrong vs the course, or overstated)

| Slide | Now | Change to | Source |
|---|---|---|---|
| 10 | Betweenness = "on the route between other provinces" | "Broker position in the trade pattern (not a road route: each OD link is already a direct trip)" | Ch 7; §11.4 |
| 10 | Strength (in+out) as the key measure | Add **out-strength** (pickup market): Nakhon Sawan, Korat, Lopburi. Note that **Chonburi is a destination** (out/in 0.10, ports); so is Samut Prakan (0.16). Move the 45/35/20 score to the appendix. | `centrality_directed.csv` |
| 11 | "ARI 0.90 · same 4 groups in all 100 runs" | "4 groups in every run; **12 Central provinces below 0.80 confidence** (incl. Saraburi 0.61); North, NE&East and West&South are stable" | Ch 9 Check 3; `community_confidence.csv` |
| 11 | "p = 0.96 · random networks group just as well" | "**Groups pass the Ch 9 baseline:** 0 of 100 rewired copies reach our Q (p < 0.01). They fail only a weight-shuffle test, so the groups come from *who trades with whom*, not link size. Leiden gives the same split." | `check2_baselines.csv`, `community_cross_check.csv` |
| 11 headline | "not yet proven to be real markets" | "4 market groups pass the course's checks; the Central group's border is unstable" | same |
| 16 | "24.9 points more than the best ranking (57.4%)" | Use the Ch 10 seeding table: random mean 40.3% · top-3 by strength 57.4% · **top-3 by out-strength 72.1%** · greedy 77.3% · optimal 82.3%. Headline: "+10.2 pts over the best ranking, +4.9 over greedy". Use the image `results/seeding.png`. | `seeding.csv` |
| 22 | "Network analytics (Model A) … +24.9 points" | "+10.2 pts vs the best ranking". Add a row: **lane coverage** (both ends in reach) A₃ 75.5% vs best 75.6%; A₂ is the optimum (58.3%). | `lane_coverage.csv` |
| 22 | "None: no province is within 150 km of two hubs" | "No province point is within 150 km of two hubs" (the drawn rings touch: Phitsanulok–Saraburi are 264 km apart) | `deck_numbers.json` |
| 14, 17 | "rules fixed in protocol.json before reading results" | "rules written in code before the models run (protocol.json)". The original claim can't be verified from git history. | — |
| 28 (A1) | "100/200 km must be read alongside" (not shown anywhere) | Add a radius slide (below) and cite it | `sensitivity_radius.csv/.png` |
| 18, 23 | B gap "≤ 3.86 pts" | Add a note: the benchmark is unconstrained Model A, so this includes the 2.2-pt cost of the group rule | `temporal.csv` |
| order | Footer 22 appears before 21 | Swap the two slides | — |

## Add (to reach the 5-point rubric descriptors)
1. **Slide 7 (framing):** "This is a **group-level** decision: a hub's value depends on the other hubs in the set." (Ch 1)
2. **New: radius robustness** (`sensitivity_radius.png`, `near_optimal.csv`):
   - With 3 hubs, every radius from 100 to 200 km gives **one hub each in North, Central and Northeast**.
   - The data's GPS road distance is 1.19× straight-line, so 150 km straight ≈ 178 km by road ≈ 3.7 h of driving.
   - If the real reach is ~125 km, the A₃ sites get only 51.5%, vs 72.8% for the re-optimised set (Ayutthaya / Phichit / Yasothon). **Define the service radius in driving hours before investing.**
   - Near-ties: Phichit can replace Phitsanulok (−0.5 pt); Prachinburi or Nakhon Nayok can replace Saraburi.
3. **New: robustness of weighting** (`weight_variants.csv`): trips, tons, adding intra-province trips (31% of in-scope trips), or origin+destination all give the **same hubs**. (Ch 6 "justified edge weighting")
4. **New: structure fingerprint** (`structure_fingerprint.csv`, Ch 8):
   - 1 piece; density 0.45; average path 1.57; diameter 3.
   - Clustering 0.78 vs 0.45 for a random graph; centralization 0.43 vs 0.14.
   - Saraburi trades with 66 of 76 provinces.
   - Weighted inside share is 0.63, below the 0.80 rule, so groups overlap.
5. **Appendix: six decisions + data-collection spec + validation sample:** copy the tables from notebook §11.1. The validation sample flags 26 rows (0.34% of trips) whose road distance is far below the centroid distance; none run faster than 100 km/h.
6. **Slide 19 (Tech & AI):**
   - Name concrete AI-vs-human moments: the bridge-score bug caught by an assertion; the null test the AI first suggested (weight shuffle) differed from the course's rewiring test.
   - The Neo4j/Cypher layer is still to do (see below).

## Unchanged and verified
990,030 trips · A₂ 66.4% · A₃ 82.3% (unique optimum by brute force) · +15.9 pts · ≈204k trips/month · B₃ 80.1% (−2.2) · weakest group 47.5% → 57.0% · West & South 47.5% → 92.2% · Suphanburi/Lopburi example · 87% sum of singles · group sizes 29/12/14/22 and shares 37/34/15/14%.
