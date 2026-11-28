# Freight Capstone: Network and Base Selection

**English** · [ภาษาไทย](#ภาษาไทย)

## English

A Thai-language notebook for choosing contract-freight bases when the number of bases is fixed at 2 or 3, and for testing what role communities play in market access.

### Getting started

Open `Freight_Capstone_TH.ipynb` to see the explanations, code and saved outputs (the notebook is written in Thai). To recompute, put the data in `data/` as listed below, then Run All.

```bash
python -m pip install pandas numpy scipy networkx matplotlib ipykernel
```

`requirements-tested.txt` records the versions used for testing. Partition results, or answers where scores tie, may differ under other versions, so check the actual output before putting it on slides.

### Required data

- `data/otp_69_01_69.csv`: main data, Jan–Apr 2569 BE (2026)
- `data/otp_69_01_68.csv`: 2568 BE (2025) data, for the overlapping months and the duplicate sensitivity check
- `data/province_coordinates_used.csv`: representative point per province and where each coordinate came from
- `data/straight_line_distance_km.csv`: straight-line distances between province points, cross-checked against Haversine in the notebook

Freight data source: https://otp.gdcatalog.go.th/dataset/91038df9-854e-442d-8408-c54032daf506

See source details in `data/แหล่งที่มา_SOURCES.txt` and the hashes of the files used in `results/input_sha256.json`. Missing data does not mean there is no real demand. Check the source's terms before redistributing the data.

### Analysis steps

1. Audit the data and pick a portfolio of 7 products, excluding sugarcane
2. Build the province network, weighted by total trips in both directions
3. Louvain, 100 seeds per resolution (0.5, 1, 1.5, 2)
4. Fixed-topology weight permutation, 100 runs, with the same optimization budget
5. Check the bridge calculation and report centrality alongside it
6. Model A maximizes total coverage; Model B adds a minimum coverage requirement per group
7. Freeze the bases and back-check, with charts and output files

### Results and key limitations

Main case, 150 km straight-line: A with two bases picks Phitsanulok–Saraburi, coverage 66.4%; A with three bases adds Maha Sarakham, coverage 82.3%; B with three bases and a 50% floor reaches 80.1%.

The market groups pass Check 2 of chapter 9 (rewired copies 0/100, p≈0.01; Leiden gives the same split) but fail the weight permutation (p=0.9604), and 12 provinces in the Central group have confidence < 0.80. Model A beats a sensible ranking (out-strength 72.1%) by 10.2 points and greedy by 4.9 points. The bases change with the radius, but the three bases always sit in North/Central/Northeast (see section 11 and `docs/DECK_REVISIONS.md`). Model B is exploratory, not an investment rule. The back-check is not an unseen holdout, and B's benchmark is Model A without the per-group requirement.

Coverage is not sales or profit. There is no capacity cost, real road distance or competitor data, and the minimum number of bases for a coverage target has not been found yet.

### Use of AI

AI helped generate code, explain and organize documents. The team must check assumptions, formulas, data sources and conclusions themselves. AI is not used as evidence of market facts.

### Open in Colab

[Open in Colab](https://colab.research.google.com/github/hhej/MADT7202_capstone_freight/blob/main/Freight_Capstone_TH.ipynb)

Run the GitHub/Colab data-prep cell before starting the analysis. It downloads the two years of CSVs directly from the Office of Transport and Traffic Policy and Planning (OTP) and checks their SHA-256 against the tested data. Large CSVs are not kept in Git. If the source files change, use the original copies instead of skipping the hash check.

### Interactive explorer

Browse it interactively at **https://hhej.github.io/MADT7202_capstone_freight/** (or double-click `explorer/index.html` locally; an internet connection is needed to load D3 and fonts). Story mode walks through 12 steps in place of slides, and Explore mode lets you place bases yourself, change the radius, drop products and see every result. A 30-second summary sits at the top, the **Common questions** tab explains the study in plain words (for example, that 150 km limits pickups, not deliveries), and you can pin one set of bases to compare with another, copy a link to the current view, and switch the colour theme or show province names in Thai. Rebuild with `python explorer/build_explorer.py` and check the calculations with `node explorer/test_calc.mjs`.

### Slides, tests and Neo4j

- `deck/Hub_Location_Study_MADT7202.pptx`: presentation slides (importable into Canva: Create a design → Import file). The Thai script is in `deck/SCRIPT_TH.md`; speaker order and expected questions are in `deck/PRESENTER_GUIDE.md`
- Rebuild the slides from the latest results: `python deck/build_deck.py`, then check with `python deck/lint_deck.py` (no filler words, every number comes from `results/`, and no text overflows its box)
- Stress tests: `pytest -q tests/` (about 7 minutes). Results and exceptions are summarized in `docs/STRESS_TEST.md`
- Neo4j: `Freight_GraphDB_Neo4j.ipynb` needs `NEO4J_CREDENTIALS_FILE` pointing to the Aura credentials file kept outside the repo. Never commit that file
- Tested libraries: `requirements-tested.txt` (add `python-pptx` and `pytest` for slides and tests)

---

## ภาษาไทย

[English](#english) · **ภาษาไทย**

Notebook ภาษาไทยสำหรับเลือกฐานรับจ้างขนส่งเมื่อกำหนดจำนวนฐาน 2 หรือ 3 แห่ง และทดลองบทบาทของ community ในการเข้าถึงตลาด

### เริ่มต้น

เปิด `Freight_Capstone_TH.ipynb` เพื่อดูคำอธิบาย โค้ด และผลที่รันไว้แล้ว หากต้องการคำนวณใหม่ ให้วางข้อมูลใน `data/` ตามรายการด้านล่าง แล้ว Run All

```bash
python -m pip install pandas numpy scipy networkx matplotlib ipykernel
```

`requirements-tested.txt` บันทึกเวอร์ชันที่ใช้ทดสอบ ผล partition หรือคำตอบที่คะแนนเสมอกันอาจต่างกันเมื่อเปลี่ยนเวอร์ชัน จึงต้องตรวจผลจริงก่อนนำไปใส่สไลด์

### ข้อมูลที่ต้องใช้

- `data/otp_69_01_69.csv`: ข้อมูลหลัก ม.ค.–เม.ย. 2569
- `data/otp_69_01_68.csv`: ข้อมูลปี 2568 สำหรับเดือนร่วมและ duplicate sensitivity
- `data/province_coordinates_used.csv`: จุดแทนจังหวัดและที่มาของพิกัด
- `data/straight_line_distance_km.csv`: ระยะเส้นตรงระหว่างจุดแทนจังหวัด มีการตรวจเทียบ Haversine ใน Notebook

แหล่งข้อมูลขนส่ง: https://otp.gdcatalog.go.th/dataset/91038df9-854e-442d-8408-c54032daf506

ดูรายละเอียดต้นทางใน `data/แหล่งที่มา_SOURCES.txt` และ hash ของไฟล์ที่ใช้รันใน `results/input_sha256.json` ข้อมูลที่ขาดไม่ได้แปลว่าไม่มี demand จริง ตรวจสิทธิ์ของต้นทางก่อนเผยแพร่ข้อมูลต่อ

### ขั้นตอนวิเคราะห์

1. Audit ข้อมูลและเลือกพอร์ต 7 สินค้า ไม่รวมอ้อย
2. สร้างเครือข่ายจังหวัด น้ำหนักเป็นเที่ยวรวมสองทิศทาง
3. Louvain 100 seeds ต่อ resolution (0.5, 1, 1.5, 2)
4. Fixed-topology weight permutation 100 ครั้ง โดยใช้ optimization budget เท่ากัน
5. ตรวจ bridge calculation และรายงาน centrality ประกอบ
6. Model A เพิ่ม coverage รวม; Model B เพิ่มข้อกำหนด coverage ขั้นต่ำรายกลุ่ม
7. ตรึงฐานแล้วตรวจย้อนหลัง พร้อมกราฟและไฟล์ผลลัพธ์

### ผลและข้อจำกัดสำคัญ

กรณีหลัก 150 กม. เส้นตรง: A สองฐานเลือกพิษณุโลก–สระบุรี coverage 66.4%; A สามฐานเพิ่มมหาสารคาม coverage 82.3%; B สามฐาน floor 50% ได้ 80.1%

กลุ่มตลาดผ่าน Check 2 ของบทที่ 9 (rewired copies 0/100, p≈0.01; Leiden ให้ split เดียวกัน) แต่ไม่ผ่าน weight permutation (p=0.9604) และ 12 จังหวัดในกลุ่ม Central ความมั่นใจ < 0.80 Model A ชนะ ranking ที่เหมาะสม (out-strength 72.1%) 10.2 จุด และ greedy 4.9 จุด ฐานเปลี่ยนตามรัศมีแต่สามฐานอยู่ North/Central/Northeast เสมอ (ดูส่วน 11 และ `docs/DECK_REVISIONS.md`) Model B เป็น exploratory ไม่ใช่กฎลงทุน ผลตรวจย้อนหลังไม่ใช่ unseen holdout และ benchmark ของ B เป็น Model A ที่ไม่มีข้อกำหนดรายกลุ่ม

Coverage ไม่ใช่ยอดขายหรือกำไร ไม่มีต้นทุน capacity ระยะถนนจริง หรือข้อมูลคู่แข่ง และยังไม่ได้หาจำนวนฐานน้อยที่สุดภายใต้ coverage target

### การใช้ AI

AI ช่วยสร้างโค้ด อธิบาย และจัดเอกสาร ทีมต้องตรวจสมมติฐาน สูตร แหล่งข้อมูล และข้อสรุปด้วยตนเอง ไม่ใช้ AI เป็นหลักฐานข้อเท็จจริงทางตลาด

### เปิดบน Colab

[Open in Colab](https://colab.research.google.com/github/hhej/MADT7202_capstone_freight/blob/main/Freight_Capstone_TH.ipynb)

รันเซลล์เตรียมข้อมูลสำหรับ GitHub/Colab ก่อนเริ่มวิเคราะห์ ระบบดาวน์โหลด CSV สองปีจาก สนข. โดยตรงและตรวจ SHA-256 กับข้อมูลที่ใช้ทดสอบ ไม่เก็บ CSV ขนาดใหญ่ไว้ใน Git หากไฟล์ต้นทางเปลี่ยนให้ใช้สำเนาเดิมแทนการข้ามการตรวจ hash

### Interactive explorer

เปิดดูแบบคลิกเล่นได้ที่ **https://hhej.github.io/MADT7202_capstone_freight/** (หรือดับเบิลคลิก `explorer/index.html` ในเครื่องได้ ต้องต่ออินเทอร์เน็ตเพื่อโหลด D3 และฟอนต์) มีโหมด Story 12 ขั้นสำหรับเล่าเรื่องแทนสไลด์ และโหมด Explore สำหรับลองวางฐานเอง เปลี่ยนรัศมี ตัดสินค้า และดูผลทุกส่วน ด้านบนมีสรุป 30 วินาที แท็บ **Common questions** อธิบายงานนี้แบบภาษาง่ายๆ (เช่น 150 กม. จำกัดแค่จุดรับของ ไม่ได้จำกัดจุดส่ง) และยังปักหมุดชุดฐานไว้เทียบกับอีกชุด คัดลอกลิงก์ของมุมมองปัจจุบัน สลับธีมสี หรือแสดงชื่อจังหวัดเป็นภาษาไทยได้ สร้างใหม่ด้วย `python explorer/build_explorer.py` และตรวจการคำนวณด้วย `node explorer/test_calc.mjs`

### สไลด์ การทดสอบ และ Neo4j

- `deck/Hub_Location_Study_MADT7202.pptx`: สไลด์นำเสนอ (นำเข้า Canva ได้: Create a design → Import file) สคริปต์ภาษาไทยอยู่ใน `deck/SCRIPT_TH.md` ลำดับผู้พูดและคำถามที่คาดว่าจะโดนถามอยู่ใน `deck/PRESENTER_GUIDE.md`
- สร้างสไลด์ใหม่จากผลล่าสุด: `python deck/build_deck.py` แล้วตรวจด้วย `python deck/lint_deck.py` (ไม่มีคำฟุ่มเฟือย ทุกตัวเลขมาจาก `results/` และข้อความไม่ล้นกล่อง)
- Stress tests: `pytest -q tests/` (ประมาณ 7 นาที) ผลและข้อยกเว้นสรุปใน `docs/STRESS_TEST.md`
- Neo4j: `Freight_GraphDB_Neo4j.ipynb` ต้องตั้ง `NEO4J_CREDENTIALS_FILE` ชี้ไฟล์ credentials จาก Aura ที่เก็บไว้นอก repo ห้าม commit ไฟล์นี้
- ไลบรารีที่ใช้ทดสอบ: `requirements-tested.txt` (เพิ่ม `python-pptx` และ `pytest` สำหรับสไลด์และการทดสอบ)
