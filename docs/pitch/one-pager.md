<!--
One-pager: LineSleuth. Draft v0.1, 2026-09-24, Sandy (Sales). For the boss's review.
Sources: docs/meetings/2026-09-24-駭客松主題方向.md, docs/prd.md, docs/pitch/pitch-deck.md, pitch-script.md, judge-qa.md, submission-summary.md, docs/finance/roi-model.md
Markers:
  [pending interviews] = replace only with a real interview number or approved quote (docs/sales/interview-guide.md). Never fill X with the assumed values in roi-model.csv.
  [to measure]         = replace with a measured regression / rehearsal result.
  [to verify]          = check against the vendor's current public material or a public source.
Before this goes to judges or partners: replace every marker or delete its line, and delete the 重點 lines (internal reading only).
Product name is still a working name (PRD Q7).
-->

# LineSleuth

**One button takes a night-shift supervisor from line stoppage to root cause, with evidence anyone can check.**

AI Builder Cup 2026 · Manufacturing

> 重點：給中小代工廠夜班主管的停線調查 Copilot，一鍵找根因，每個結論都查得到證據。

## Problem

3 a.m., Line 2 stops. The night supervisor is alone; engineers are off site. Finding the cause means digging through Excel sheets, PLC CSV exports and shift logs, about 40 minutes [pending interviews], while every hour of downtime costs X [pending interviews].

> 重點：凌晨停線、主管一個人翻 Excel 找原因。40 分鐘和每小時損失都還沒有訪談數字。

## Solution

One **Investigate** button, no chat box. Gemini calls five fixed, tested queries and never writes SQL (demo data runs on DuckDB; the data layer can be swapped for BigQuery). Every step becomes an evidence card that opens to its source rows. No evidence, no conclusion: it answers **"Insufficient evidence"** instead of guessing.

**Demo in three steps** (about 12 seconds per investigation; measured median 12.6 s, gemini-2.5-flash, docs/qa/runs)

1. **Alarm.** 03:00, Line 2 turns red; the supervisor presses Investigate.
2. **Evidence.** Cards appear one by one (temperature, coolant flow, valve, shift log), each tracing back to source data rows.
3. **Action.** Root cause "cooling valve CV-2 stuck" with a server-scored confidence label; one click creates a work order, opened on a phone by QR.

> 重點：Gemini 只能選固定查詢，數字可回查原始列，證據不足就出灰卡。實測約 12 秒找到根因（中位數 12.6 秒，出處 docs/qa/runs/README.md）；示範用 DuckDB，可換 BigQuery，不能說「已支援」。Demo 三步：亮紅燈按鈕 → 證據卡 → 根因加 QR 工單。

## Why now, why JAPAC SMBs

- "China plus one" is moving production to Vietnam, Thailand and Malaysia [to verify].
- Target: contract manufacturers with 50–300 staff [pending interviews], no MES, no data team.
- Gemini function calling makes a constrained, auditable agent practical on files these plants already export.

> 重點：產能南移（來源待查證），目標客戶沒有 MES 也沒有資料團隊，大廠方案顧不到。

## Differentiation

| | Built for | Starts from |
|---|---|---|
| Siemens Industrial Copilot | Large plants in the Siemens automation ecosystem [to verify] | Automation and MES data [to verify] |
| Cognite | Asset-heavy enterprises with data teams [to verify] | Industrial data platform [to verify] |
| Google MDE | Plants building a connected data platform on Google Cloud [to verify] | Connected machine data [to verify] |
| **LineSleuth** | **Small contract manufacturers without MES** | **Excel sheets and PLC CSV exports** |

Google MDE is the platform our customers can grow into, on the same Google Cloud stack.

> 重點：我們跟大廠服務的不是同一群客戶。MDE 是客戶以後的升級路徑，不當對手講。競品描述全部待查證。

## Business model

- **Onboarding fee**: X one-time, to turn Excel and PLC exports into clean data [pending interviews]
- **Subscription**: X per production line per month [pending interviews]
- Priced below the downtime and labour it saves; customer payback in X months [pending interviews]
- Buyer: plant manager or owner [pending interviews]

> 重點：導入費加每條產線月訂閱。金額、回本月數、誰拍板採購，都要等訪談。

## Built on Google Cloud

**Cloud Run** (one service, Singapore region; demo data in DuckDB inside the image, swappable for BigQuery) · **Vertex AI Gemini** function calling over 5 fixed queries, temperature 0 · **Cloud Logging** (every query replayable) · least-privilege **IAM** · budget alerts and rate limits

> 重點：全部跑在 GCP 新加坡區，每次查詢都有紀錄可以重播。

## Traction and validation

- Prototype built on simulated data: one stoppage scenario, one healthy-data scenario
- Regression set: 10 known root causes, 3 with distractors; score 10/10 on real Gemini, 3 runs each, plus 2/2 healthy cases answered "Insufficient evidence" (bar: 9/10; docs/qa/runs)
- Time to root cause: about 12 s (measured median 12.6 s, max 18.6 s, gemini-2.5-flash, docs/qa/runs)
- Plant-manager interviews: [pending interviews]; design partners: [pending interviews]

> 重點：原型是模擬資料。回歸分數與實測秒數已有（docs/qa/runs/README.md）；訪談場數還沒有，不能先寫。

## Team and contact

- Hung Che Nick Lai
- Contact: hongchelai@gmail.com · Live prototype: https://linesleuth-547147056278.asia-southeast1.run.app

> 重點：目前隊員只有 Nick。比賽規定至少 2 人，正式隊員確定後再補上；顧問要另外標示，不能當隊員列。

---

**Stoppage → root cause in ~12 s (measured median 12.6 s, docs/qa/runs). Every conclusion backed by evidence.**
