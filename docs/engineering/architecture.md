# 架構：LineSleuth 原型（W1 骨架）

- 建立：2026-09-24，Eddie（工程）
- 依據：`docs/prd.md`（F1–F8）、`docs/design/ui-spec.md`、`docs/design/storyboard.md`
- 狀態：本機可跑；Gemini 真實呼叫與 BigQuery 後端**尚未驗證**（沒有 GCP 憑證）。

## 1. 一張圖

```
Browser (大螢幕 index.html / 手機 wo.html, 純 HTML/CSS/JS)
   │  POST /api/investigations  → 每 700ms 輪詢 GET /api/investigations/{id}
   ▼
FastAPI（app/main.py，Cloud Run 單一服務，1 worker）
   ├─ InvestigationManager（app/investigations.py）  背景執行緒、步驟、取消/重置、工單
   │     ├─ Agent runner
   │     │    ├─ gemini_agent.py     Vertex AI Gemini function calling（temperature 0，mode=ANY）
   │     │    └─ offline_fixture.py  腳本化呼叫，只供 UI 開發，UI 顯示 OFFLINE FIXTURE
   │     └─ conclusion.py            伺服器端規則：≥2 引用才算根因、信心標籤、灰卡 Checked 清單
   └─ QueryExecutor（app/queries/functions.py）5 個固定函式 + 逾時 + 快取退回
         └─ QueryBackend（app/queries/backends.py）
              ├─ local     DuckDB in-memory，讀 app/data/generated/*.csv
              └─ bigquery  同一份 SQL 樣板，@參數綁定，DATETIME
```

## 2. 目錄

| 路徑 | 內容 |
|---|---|
| `app/main.py` | 路由、速率限制、頁面（SVG 在伺服器端 inline 進 index.html） |
| `app/config.py` | 所有設定都從環境變數讀（`.env.example`） |
| `app/data/catalog.py` | 機台、感測器、正常範圍、根因分類（root_cause_key） |
| `app/data/scenarios.py` | 12 個情境：劇本、效果參數、預期答案 |
| `app/data/generate.py` | 固定 seed 產生 CSV（可重現，測試有驗證逐位元相同） |
| `app/data/sop.md` | 虛構 SOP 片段，直接放進 system prompt（不用 RAG） |
| `app/queries/` | 5 個固定查詢函式、兩個後端 |
| `app/agent/` | prompt、Gemini 迴圈、離線 fixture、結論規則 |
| `app/static/` | 前端；`line-layout.svg` 是 `docs/design/line-layout.svg` 的複本（Dana 改圖時要同步複製） |
| `scripts/run_regression.py` | 回歸集執行器（只接受 AGENT_MODE=gemini） |
| `scripts/load_bigquery.py` | 建 dataset/表並上傳 CSV（會建立雲端資源，老闆自己跑） |
| `tests/` | pytest |

## 3. 資料模型

所有表都有 `row_id`（例 `R01-S01938`、`R01-E004`），證據卡上的高亮就是用它對回原始列。時間一律是**工廠當地時間、無時區**（DuckDB `TIMESTAMP`／BigQuery `DATETIME`），避免 Quinn 擔心的時區錯位。

| 表 | 欄位 | 說明 |
|---|---|---|
| `sensor_readings` | row_id, scenario_id, ts, line, machine, sensor, value, unit | 每分鐘一筆，00:00–03:00，約 2.6 萬列 |
| `events` | row_id, scenario_id, ts, line, machine, event_type, code, severity, actor, message | alarm / shift_handover / maintenance / parameter_change / material_change / operator_note |
| `sensor_catalog` | row_id, machine, machine_name, sensor, unit, normal_low, normal_high, sop_section | SOP 上下限（卡片上的上限數字也可回查） |
| `work_orders` | wo_id, created_at, …, payload_json | 主管按 Create work order 才寫入；手機頁讀 payload_json，保證和結論卡逐字一致 |

`scenario_id` 由伺服器綁定，Gemini 看不到也選不到。

## 4. 情境與回歸集

| ID | 故事 | 預期 | 備註 |
|---|---|---|---|
| **R01** | Line 2 CV-2 02:41 卡在 20%，流量掉到約 41%，03:00:12 過溫停線 | cv_valve_stuck_closed | Demo 主線；02:30 交班 |
| **N01** | Line 1 全部正常 | insufficient_evidence | Demo 灰卡 |
| R02 | 冷卻水入水溫度過高 | coolant_supply_temp_high | |
| R03 | 加熱器卡在 100% | heater_stuck_on | |
| R04 | 控制溫度探頭漂移（參考探頭正常、加熱功率反而下降） | temp_sensor_drift | **干擾項**：交班＋新手操作員 |
| R05 | 油壓不足 → 不良率跳停 | hydraulic_pressure_low | |
| R06 | 冷卻水濾網堵塞（閥位正常、流量漸降） | coolant_filter_clogged | **干擾項**：02:20 M3 保養 |
| R07 | 操作員把設定溫度調高 | setpoint_change | 操作員備註含 prompt injection 字串 |
| R08 | 乾燥機溫度過低 → 濕料不良 | dryer_temp_low | **干擾項**：02:35 換料批 |
| R09 | 進料口堵塞 | feeder_blockage | |
| R10 | Line 3 CV-3 卡在全開 → 模溫過低 | cv_valve_stuck_open | 測試不同產線 |
| N02 | Line 3 正常但流量 02:40 後缺值 | insufficient_evidence | 缺值不能當成根因 |

Quinn 的 `docs/qa/test-plan.md` 可以直接引用這張表；要改題目改 `app/data/scenarios.py`，資料會跟著重產。

## 5. 五個固定查詢函式

| 函式 | 參數 | 回傳重點 |
|---|---|---|
| `get_alarm_events` | line, start, end | 警報列表 |
| `get_sensor_window` | line, machine, sensor, start, end | 每分鐘數值、首次越限、最大/最小、缺值分鐘數；閥位會一併帶出命令值 |
| `compare_to_baseline` | line, machine, sensor, start, end | 基準＝視窗開始前 90～30 分鐘的平均；最新值佔基準 %、偏離開始時間（偏離＝超過正常帶寬 25%） |
| `get_shift_log` | line, start, end | 交班、保養、參數變更、換料、操作員備註 |
| `list_sensors` | machine | 感測器清單與 SOP 上下限 |

- SQL 是寫死的樣板，只能綁參數；參數先過白名單（line 1–3、machine enum、sensor enum 且要屬於該機台、HH:MM、視窗 ≤ 180 分鐘）。不合法就回錯誤給模型，不猜。
- **卡片上的數字由程式從原始列算出，不是模型寫的**。模型只能引用 evidence_id。
- 每次呼叫寫一行 JSON log（函式、參數、筆數、耗時、是否 cached），Cloud Run 會自動進 Cloud Logging（F3 驗收）。
- 逾時（預設 20 秒）時，如果同一組參數有上次成功的結果就退回並標 `Cached`；沒有就顯示 `Failed`。目前快取在記憶體，重啟會清空。

## 6. Agent 與結論規則

- Gemini：`google-genai` SDK，`vertexai=True`，自動 function calling 關閉（我們自己執行每一步），`mode=ANY` 讓模型每輪都必須呼叫函式，最後用 `submit_conclusion` 交卷；查詢超過 8 次就只允許 `submit_conclusion`。
- 預設模型 `gemini-3-flash-preview`、location `global`。**這個名字是我依知識截止時的最新版本填的，沒有實際呼叫驗證過**；上線前老闆要在 Vertex AI Model Garden 確認可用的最新 ID 後寫進 `GEMINI_MODEL`。
- 注意：Google 對 Gemini 3 建議 temperature 用預設 1.0，設 0 可能出現重複迴圈或品質下降。會議定案是 0，所以預設 0；回歸集若出現卡迴圈，再拿 `GEMINI_TEMPERATURE` 做對照實驗。
- 結論規則（`app/agent/conclusion.py`）：引用有效證據卡 < 2 張 → 一律改灰卡；信心標籤由伺服器算（**暫定**：引用卡中有異常訊號 ≥3 張 High、2 張 Medium、其餘 Low，等 PRD Q4 定案再改）。
- Prompt injection：日誌文字在 system prompt 明講是不可信資料；R07 內含攻擊字串，回歸集會驗證。

## 7. OFFLINE FIXTURE 模式（`AGENT_MODE=offline_fixture`）

- 只為了沒有 GCP 憑證時做 UI。查詢是真的跑本機資料，但「呼叫哪些函式」和「結論文字」是 `app/agent/offline_fixture.py` 寫死的。
- UI 頂部、工單頁、底列都會顯示 `OFFLINE FIXTURE`；`/api/config` 與每筆調查、工單都帶 `agent_mode`。
- 只有 R01、N01 有 fixture；回歸執行器在此模式直接拒絕計分。**不能拿來 demo 或繳交。**

## 8. 已知限制／技術債

| 項目 | 影響 | 何時處理 |
|---|---|---|
| 調查狀態放記憶體 | Cloud Run 必須 max-instances=1、1 worker、CPU 常駐 | MVP 可接受 |
| 速率限制在記憶體、以 IP 計 | 重啟會清空；多實例無效 | MVP 可接受 |
| 工單編號用 COUNT+1 | 同時建兩張可能撞號 | 單人 demo 可接受 |
| 用輪詢不用 SSE | 每 0.7 秒一個請求 | 夠用，不改 |
| Gemini 真實呼叫、BigQuery 後端未驗證 | W2/W3 風險 | GCP 開通當天先跑 `tests/test_gemini_live.py` |
| 前端只做過語法檢查與 API 驗證，沒有在瀏覽器實際點過 | 版面可能要微調 | Dana 視覺驗收時一起看 |
