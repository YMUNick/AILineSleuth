# 分鏡稿：LineSleuth 90 秒 Demo ＋ 灰卡加演 ＋ 手機工單

- 建立：2026-09-24，Dana（設計）
- 依據：`docs/prd.md` 第 4、5、8 節；`docs/meetings/2026-09-24-駭客松主題方向.md`
- 搭配：`docs/design/ui-spec.md`（token、元件、版面）、`docs/design/line-layout.svg`（產線圖）
- 會議原定 Figma 三頁，因為沒有 Figma，改成這份文字分鏡＋ `ui-spec.md` 的 ASCII 版面，工程師照做即可。
- 本文件的**英文 UI 文案為定稿**，程式裡請逐字使用；要改文案先改這份。
- 數值（溫度、流量、筆數、時間）是**示意值**，以 Eddie 產生的模擬資料為準；資料定案後我會回填。標 `{…}` 的是由後端回傳的變數。
- **v2 更新（2026-09-24）**：格 ②③④⑤ 和加演 C 的畫面依 `docs/design/ui-v2-spec.md` 修改（證據小圖、產線圖鏡頭拉近與根因亮起、結論卡放在面板頂端、Recap 收尾）。新文案在 §5.8–§5.10。

## 0. 故事主軸

凌晨 3 點，夜班主管一個人面對停線。以前翻 Excel 和 PLC 紀錄要 40 分鐘，現在按一個按鈕，90 秒內看到根因、證據、工單。最後主動展示「資料正常時它不會亂猜」。

旁白語言：英文（決賽在新加坡）。每格旁白字數已控制在該格秒數內可講完（約每秒 2.5 字）。

## 1. 五格分鏡總表

| 格 | 時間 | 秒數 | 畫面重點 | 對應 F |
|---|---|---|---|---|
| ① | 0:00–0:10 | 10s | 03:00 Line 2 M3 亮紅燈，停線計時器跑 | F1 |
| ② | 0:10–0:15 | 5s | 按下唯一的 Investigate | F2 |
| ③ | 0:15–1:00 | 45s | 證據卡逐張出現，點開一張看原始列 | F3、F4 |
| ④ | 1:00–1:15 | 15s | 結論卡＋信心標籤＋排除干擾項 | F5 |
| ⑤ | 1:15–1:30 | 15s | Create work order → QR → 評審手機開出工單 → `Show summary` 收尾（實測秒數；人工基準要有來源才顯示） | F7 |
| 加演 | 另 30s | 30s | 切正常資料 → Investigate → 灰卡 | F8、F6 |

秒數預算是給「即時跑 Gemini」的上限。若後端比較快，旁白照講、畫面先到也沒關係；若第 ③ 格超過 45 秒，簡報者用「補充旁白」撐，超過 60 秒就改放備援錄影。

---

## 2. 逐格分鏡

### 格 ①　03:00 停線（0:00–0:10，10 秒）F1

**畫面**
- 開場就是產線畫面（沒有首頁、沒有 logo 動畫）。
- TopBar：`LineSleuth` · `Demo Plant · Night shift`；中間 `Scenario time 03:00:00`；右側 `Demo scenario` chip。
- 產線 SVG：Line 1、Line 3 所有機台綠燈 `RUNNING`；**Line 2 的 M3 Molding 紅框紅燈 `STOPPED`**，Line 2 狀態文字 `Stopped`。
- Alert banner（紅）：`Line 2 stopped` / `M3 Molding · Over-temperature alarm at 03:00`；右邊 `Downtime 00:00:08` 開始每秒跳。
- 右側 Investigation 面板是空狀態。
- 視線動線：紅色機台 → 紅色 banner → 計時器 → 琥珀色 Investigate 按鈕（就在計時器旁邊）。

**旁白**
> It's 3 a.m. Line 2 just stopped. Every minute costs money, and the night supervisor is alone. Normally, finding out why takes 40 minutes of digging through Excel and PLC logs.

**字幕（錄影版）**：`03:00 — Line 2 stops.`

**備註**：「40 minutes」與每小時損失金額需等 Sandy／Felix 的訪談數字（PRD Q5）。沒有真實數字時，旁白改成 `can take up to 40 minutes`，字幕加註 `*pending validation`。旁白用的分鐘數要和 Recap 的 `MANUAL_BASELINE_MIN` 是同一個來源（D6）；這個數字只能出現在旁白，不能出現在 app 畫面上。

---

### 格 ②　按下 Investigate（0:10–0:15，5 秒）F2

**畫面**
- 游標移到 `Investigate` 按下。
- ≤ 1 秒內：按鈕變灰 `Investigating…`（disabled，spinner）。
- 產線圖鏡頭在 0.7 秒內拉近到 L2-M3（M2–M4 都看得到，其他車道變淡）；L2-M3 外面出現一圈會流動的藍色虛線（`is-focus`），表示「正在查這台」。（v2 §2.4）
- 面板表頭 chip：`Investigating`；`Elapsed 00:01` 開始跑。
- 面板第一張證據卡的 skeleton 出現（`Querying…`）。

**旁白**
> With LineSleuth, there's one button. No chat box, no prompts to write.

**字幕**：`One click. No prompt.`

---

### 格 ③　證據卡時間軸（0:15–1:00，45 秒）F3、F4

**畫面**：卡片由上往下逐張長出（每張約 6–9 秒）。每張卡都有：標題、關鍵數值、函式名稱、時間範圍、筆數、`View source rows`。

| # | 卡片標題 | 關鍵數值（示意） | 說明文字 | 函式（暫名，Eddie 定） | 時間範圍 |
|---|---|---|---|---|---|
| 1 | `Alarm events` | `Over-temperature` | `M3 alarm at 03:00:12 · line stopped` | `get_alarm_events` | 02:30–03:05 |
| 2 | `Mold temperature` | `214 °C` | `Above SOP 4.2 limit of 205 °C since 02:52` | `get_sensor_window` | 02:30–03:05 |
| 3 | `Coolant flow vs. baseline` | `41%` | `of normal flow since 02:41` | `compare_to_baseline` | 02:30–03:05 |
| 4 | `Cooling valve CV-2 position` | `20%` | `Stuck since 02:41 · commanded 80%` | `get_sensor_window` | 02:30–03:05 |
| 5 | `Shift & maintenance log` | `Handover 02:30` | `No parameter changes or maintenance` | `get_shift_log` | 02:00–03:05 |

- 異常數值（#2、#3、#4 的數字）顯示琥珀色；#1 用 danger 紅；#5 正常數值用主文字色。
- 每張卡的數值下方有一張小圖（v2 §1）：#1、#5 是事件時間軸（#1 有 02:54 ▲ Warning、03:00 ◆ Trip）；#2 是溫度折線越過 `SOP limit 205 °C` 虛線，標 `since`；#3 是流量掉到 `Baseline` 線下方，標 `since 02:41`；#4 是 `Commanded 80%` 虛線和掉到 20% 的實際開度，中間填色。線條由左往右畫出來（0.6 秒）。
- 新卡出現時，前一張收成兩行的精簡列（標題、數值、迷你圖），所以面板不用捲動，5 張都看得到。
- 約 0:40 時，簡報者點 **#3** 的精簡列把它展開，再點 `View source rows (12)`：展開原始列表格，`02:41` 那一列的 flow 欄位以琥珀底高亮，表下方 `Source: linesleuth_demo.sensor_readings · 12 rows · query {query_id}`。看 3 秒後按 `Hide source rows` 收起。
- 若某步驟逾時退回快取：該卡右上顯示 `Cached` chip，旁白不必解釋，評審問再答。

**旁白**
> Gemini doesn't write SQL. It picks from five fixed, tested queries — and every step shows up as an evidence card.
> The alarm fired at 3:00. Mold temperature went past the SOP limit. Coolant flow dropped to 41 percent. Valve CV-2 has been stuck at 20 percent since 2:41.
> *(點開 #3)* And every number traces back to the raw rows in BigQuery — right here.
> It also checked the 2:30 shift handover.

**補充旁白（後端慢時用）**
> Each query is logged, so we can replay any investigation step by step.

**字幕**：`Every number traces back to BigQuery.`

---

### 格 ④　結論與信心標籤（1:00–1:15，15 秒）F5

**畫面**
- 結論卡（上緣琥珀線）出現在面板**頂端**並固定不動；證據卡全部收成精簡列排在下面。
- 面板表頭 chip 變 `Root cause found`；Elapsed 停在實際秒數（例 `Elapsed 00:52`）。
- 精簡列 #2、#3、#4 補上 `Cited` tag；#5 補上 `Ruled out` tag（展開後顯示完整文案 `Cited in conclusion`）。
- 產線圖（鏡頭仍然對著 L2-M3）：藍色虛線框轉成琥珀實線；0.3 秒後 `CV-2 valve` 變成琥珀 pill，旁邊出現 `ROOT CAUSE` 標籤；閥門脈動 3 次（約 4 秒）後停住。L2-M3 本體保持紅色 `STOPPED`：紅色是症狀，琥珀色是原因。（v2 §2.2）
- Investigate 按鈕文案變 `Investigated`（仍 disabled）。

**結論卡內容（定稿）**
- `ROOT CAUSE`
- `Cooling valve CV-2 stuck at 20% open`
- `Confidence: High`＋三格條
- 理由列：`3 independent signals agree · 1 alternative ruled out`
- `Evidence` `#2` `#3` `#4`
- `Ruled out` — `Shift handover at 02:30 — no parameter changes (#5)`
- `Recommended actions`
  1. `Open CV-2 manually per SOP 4.2.`
  2. `Inspect the CV-2 actuator for sticking or power loss.`
  3. `Restart Line 2 after mold temperature is below 205 °C.`
- 按鈕：`Create work order`

**旁白**
> Root cause: cooling valve CV-2 stuck. Confidence is high — three independent signals agree, and the shift change is ruled out, not ignored.

**字幕**：`Root cause + confidence + what was ruled out.`

---

### 格 ⑤　工單上手機（1:15–1:30，15 秒）F7

**畫面**
- 按 `Create work order` → 置中 modal。
- 左：白底 QR code，下方 `Scan to open on your phone` 與短網址 `{short_url}`。
- 右：`Work order created`、`WO-{id}`、`Line 2 · M3 Molding`、`Cooling valve CV-2 stuck at 20% open`、`Priority: High`。
- 評審（或簡報者）用手機掃 → 手機 5 秒內出現工單頁（見第 4 節）。
- 簡報者按 modal 的 `Show summary`（或鍵盤 `S`）→ 全螢幕 Recap（v2 §4）：
  - `AFTER`：這次實測的調查秒數（例 `52 s`，和面板的 Elapsed 同一個數字），加上 `5 queries · 3 evidence cited · 1 ruled out · Work order WO-0001`。
  - `BEFORE`：只有設定了 `MANUAL_BASELINE_MIN` 和 `MANUAL_BASELINE_SOURCE` 才會顯示分鐘數、來源和長條對比；沒設定就顯示 `—` 和 `Not yet measured for this plant.`。
  - 底部 `Every conclusion backed by evidence.`
- 錄影版：畫面右下疊手機畫面；最後 3 秒停在 Recap 畫面（取代原本的字幕卡）。

**旁白**（依 Recap 顯示的內容選一個版本）
- 有設定人工基準：
  > One click creates the work order. Scan it — the technician has it on their phone. This investigation took {after} — versus about {before} minutes by hand, according to {source}. And every conclusion comes with its evidence.
- 沒有設定：
  > One click creates the work order. Scan it — the technician has it on their phone. This whole investigation took {after}, measured live. And every conclusion comes with its evidence.

**字幕（錄影版）**：不再使用寫死的 `40 min → 90 sec` 字卡；最後一格就是 Recap 畫面本身。

**備註**
- 大螢幕上**永遠不**出現寫死的「40 min」或「90 sec」：只顯示真實量到的秒數；人工基準一定要附來源。這個原則也適用錄影。pitch 投影片是否使用口號、怎麼標 `*pending validation`，由 Sandy 依 pitch 文件決定。
- 現場網路不穩時：短網址給評審手打；手機再不行就直接展示簡報者自己的手機。
- Recap 不會自動彈出，由簡報者決定時機；灰卡情境沒有 Recap。

---

## 3. 加演：「Insufficient evidence」灰卡（另 30 秒）F8、F6

主動展示，不等評審問。放在五格之後、pitch 收尾之前。

### 加演 A　切到正常資料（5 秒）

**畫面**
- 關掉工單 modal（`Done`）。
- 左下 `Scenario:` 下拉選 `Normal data (Line 1)`（或按鍵盤 `2`）→ 畫面自動重置。
- 產線圖全部綠燈 `RUNNING`；banner 變綠：`All lines running` / `No active alarms`；沒有計時器。
- 按鈕文案：`Investigate Line 1`。
- 面板回到空狀態。

**旁白**
> Now the harder test. What if nothing is actually wrong?

### 加演 B　照樣調查（15 秒）

**畫面**
- 按 `Investigate Line 1` → 產線圖拉近到 L1-M3，同樣逐張長出證據卡，但數值都是正常色；小圖的線全部是藍色、平穩地待在正常帶或基準帶裡，警報卡只有一條空的時間軸加 `No alarms`：

| # | 卡片標題 | 關鍵數值（示意） | 說明文字 |
|---|---|---|---|
| 1 | `Alarm events` | `0` | `No alarms 02:30–03:05` |
| 2 | `Mold temperature` | `188 °C` | `Within SOP 4.2 range` |
| 3 | `Coolant flow vs. baseline` | `98%` | `of normal flow` |
| 4 | `Shift & maintenance log` | `Handover 02:30` | `No parameter changes or maintenance` |

**旁白**
> Same investigation, same five queries — on healthy data.

### 加演 C　灰卡（10 秒）

**畫面**
- 面板頂端出現灰卡（虛線框、問號圖示）；面板 chip 變 `Insufficient evidence`（灰）。
- 產線圖的鏡頭拉回全景（意思是：整條線都查過了，沒有可以指認的地方）；接著 Line 1 外框變成灰色虛線，出現 `No root cause found` 徽章。（v2 §2.2）
- 沒有信心標籤、沒有 `Create work order`、沒有 `Show summary`；沒有任何機台變色、沒有 `ROOT CAUSE`。

**灰卡內容（定稿）**
- 標題：`Insufficient evidence`
- 說明：`No root cause found. LineSleuth will not guess.`
- `Checked`
  - ✓ `Alarm events — none in window`
  - ✓ `Mold temperature — within normal range`
  - ✓ `Coolant flow — within normal range`
  - ✓ `Shift & maintenance log — no changes`
- `Recommended next step`
- `Manual inspection of Line 1 by the shift supervisor.`

**旁白**
> It says "insufficient evidence", shows exactly what it checked, and hands it back to a human. It doesn't make up a root cause. That's why supervisors can trust it.

**字幕**：`No evidence, no conclusion.`

---

## 4. 手機工單頁（F7）

網址形式：`/wo/{id}`，不需登入。版面見 `ui-spec.md` §4.2。

**文案定稿（主線情境）**

| 區塊 | 標籤 | 內容 |
|---|---|---|
| 頁首 | — | `LineSleuth` · `Work order` |
| 抬頭 | — | `WO-{id}`，chip `Open`、`Priority: High` |
| 欄位 | `LINE / MACHINE` | `Line 2 · M3 Molding` |
| 欄位 | `DETECTED` | `03:00 (scenario time)` |
| 欄位 | `ROOT CAUSE` | `Cooling valve CV-2 stuck at 20% open` |
| 欄位 | `CONFIDENCE` | `High`（三格條） |
| 欄位 | `EVIDENCE` | `Mold temperature 214 °C, above SOP limit 205 °C` / `Coolant flow at 41% of normal since 02:41` / `CV-2 position stuck at 20% (commanded 80%)` |
| 欄位 | `RULED OUT` | `Shift handover at 02:30 — no parameter changes` |
| 清單 | `RECOMMENDED ACTIONS` | 同結論卡三項 |
| 欄位 | `SOP REFERENCE` | `SOP 4.2 — Mold over-temperature` |
| 欄位 | `CREATED` | `{created_at} by LineSleuth` |
| 頁尾 | — | `AI-generated from plant data. Verify on site before acting.` |

- 內容必須與大螢幕結論卡**逐字一致**（PRD F7 驗收）。後端同一份結論物件同時餵兩個畫面，不要各自生成。
- 找不到工單：`Work order not found` / `This link may be expired or mistyped.`
- 載入中：`Loading work order…`（置中，16px text-secondary）。

---

## 5. UI 文案總表（定稿，英文逐字）

### 5.1 全域

| 位置 | 文案 |
|---|---|
| 瀏覽器標題 | `LineSleuth — Line investigation` |
| TopBar wordmark | `LineSleuth` |
| TopBar 副標 | `Demo Plant · Night shift` |
| 情境時鐘標籤 | `Scenario time` |
| 情境 chip | `Demo scenario` |
| 圖例 | `Running` / `Warning` / `Stopped` |
| 機台狀態文字 | `RUNNING` / `WARNING` / `STOPPED` / `IDLE` |
| 線狀態文字 | `Running` / `Stopped` |
| 機台名稱 | `M1 Feeder` / `M2 Dryer` / `M3 Molding` / `M4 Inspection` |
| 情境切換標籤 | `Scenario:` |
| 情境選項 | `Line 2 over-temperature` / `Normal data (Line 1)` |
| 重置 | `Reset` |

### 5.2 Alert banner 與按鈕

| 狀態 | 文案 |
|---|---|
| 停線標題 | `Line {n} stopped` |
| 停線副標 | `{machine} · {alarm} at {time}`（例 `M3 Molding · Over-temperature alarm at 03:00`） |
| 計時器標籤 | `Downtime` |
| 正常標題 | `All lines running` |
| 正常副標 | `No active alarms` |
| 按鈕（停線） | `Investigate` |
| 按鈕（正常情境） | `Investigate Line 1` |
| 按鈕（進行中） | `Investigating…` |
| 按鈕（完成） | `Investigated` |

### 5.3 Investigation 面板

| 位置 | 文案 |
|---|---|
| 面板標題 | `Investigation` |
| 耗時 | `Elapsed {mm:ss}` |
| chip | `Not started` / `Investigating` / `Root cause found` / `Insufficient evidence` / `Investigation failed` |
| 空狀態第一行 | `No investigation yet.` |
| 空狀態第二行 | `Press Investigate. LineSleuth will check alarms, sensors, and shift logs, and show every piece of evidence it finds.` |
| 證據卡狀態 | `Querying…` / `Done` / `Cached` / `Failed` |
| Cached tooltip | `Live query timed out. Showing last verified result.` |
| 證據卡錯誤 | `Query failed` |
| 展開 | `View source rows ({n})` / `Hide source rows` |
| 原始列頁尾 | `Source: {dataset.table} · {n} rows · query {query_id}` |
| 證據 tag | `Cited in conclusion` / `Ruled out` |
| 證據 tag（精簡列，v2） | `Cited` / `Ruled out` |
| 證據列小標（v2，結論後出現） | `Evidence · {n} queries` |
| 精簡列 aria-label（v2） | `Step {n}, {title}, {key_value}{, cited in conclusion / , ruled out}. Show details` |
| 調查失敗 | `Investigation failed. Press Reset and try again.` |

### 5.4 結論卡

| 位置 | 文案 |
|---|---|
| 小標 | `Root cause` |
| 信心 | `Confidence: High` / `Confidence: Medium` / `Confidence: Low` |
| 理由列 | 後端回傳，格式 `{n} independent signals agree · {m} alternative(s) ruled out` |
| Low 提示 | `Low confidence — verify on site before acting.` |
| 小標 | `Evidence` / `Ruled out` / `Recommended actions` |
| 處置清單收合按鈕（v2 compact 版） | `Recommended actions ({n})` |
| 按鈕 | `Create work order` |

### 5.5 灰卡

| 位置 | 文案 |
|---|---|
| 標題 | `Insufficient evidence` |
| 說明 | `No root cause found. LineSleuth will not guess.` |
| 小標 | `Checked` |
| 清單格式 | `{check name} — {result}` |
| 小標 | `Recommended next step` |
| 建議 | `Manual inspection of Line {n} by the shift supervisor.` |

### 5.6 工單 modal（大螢幕）

| 位置 | 文案 |
|---|---|
| 標題 | `Work order created` |
| QR 說明 | `Scan to open on your phone` |
| 優先度 | `Priority: High` / `Priority: Medium` / `Priority: Low` |
| 關閉 | `Done` |
| 開啟收尾畫面（v2） | `Show summary` |
| 失敗 | `Could not create work order. Try again.` ＋按鈕 `Try again` |

### 5.7 手機工單頁

見第 4 節表格。

### 5.8 證據小圖（v2）

圖上的字由後端 `card.chart` 回傳，前端照著顯示。**不能**把交班紀錄的 message 原文放進標籤。

| 位置 | 文案 |
|---|---|
| SOP 上下限線 | `SOP limit {value} {unit}`（例 `SOP limit 205 °C`） |
| 沒越限時的正常帶 | `SOP range` |
| 基準線 | `Baseline {value} {unit}`（例 `Baseline 42 L/min`） |
| 指令開度線 | `Commanded {value}%` |
| 實際開度線 | `Actual` |
| 越限／偏離起點 | `since {HH:MM}` |
| 缺值區、整段沒有資料 | `No data` |
| 沒有警報 | `No alarms` |
| 沒有交班／維修紀錄 | `No log entries` |
| 警報事件 | `Trip {HH:MM}` / `Critical {HH:MM}` / `Warning {HH:MM}` |
| 交班紀錄事件 | `Handover {HH:MM}` / `Maintenance {HH:MM}` / `Parameter change {HH:MM}` / `Material change {HH:MM}` / `Note {HH:MM}` |
| 圖的 aria-label | `{title}: {key_value} {key_detail}. Chart of {n} readings, {x_start}–{x_end}.`；事件圖：`{title}: {labels joined by ", " or empty label}.` |

### 5.9 產線圖（v2）

| 位置 | 文案 |
|---|---|
| 根因標籤 | `ROOT CAUSE` |
| 灰卡車道徽章 | `No root cause found` |
| 讀屏提示（根因，閥門） | `Root cause located on the plant map: CV-{n} cooling valve, Line {n} M3.` |
| 讀屏提示（根因，機台） | `Root cause located on the plant map: Line {n} {machine_label}.` |
| 讀屏提示（灰卡） | `No root cause found on Line {n}. The whole line was checked.` |

### 5.10 Recap 收尾畫面（v2）

| 位置 | 文案 |
|---|---|
| 小標 | `Investigation summary` |
| 位置列 | `Line {n} · {machine_label}` |
| 根因 | `{root_cause}`（和結論卡逐字相同） |
| Before 標籤 | `Before` ＋ `Manual investigation (baseline)` |
| Before 數值 | `{minutes} min` |
| Before 來源 | `Source: {MANUAL_BASELINE_SOURCE}` |
| Before 沒設定 | 數值 `—`，文字 `Not yet measured for this plant.` |
| After 標籤 | `After` ＋ `LineSleuth, this investigation (measured)` |
| After 數值 | `{s} s` 或 `{m} min {s} s` |
| After 明細 | `{q} queries · {c} evidence cited · {r} ruled out`，有 cached 時加 ` · {k} cached`，有工單時加 ` · Work order {wo_id}` |
| 量測說明 | `Measured by the server from Investigate to conclusion.` |
| 結尾句 | `Every conclusion backed by evidence.` |
| 按鈕 | `Close` |
| offline fixture 標示 | `OFFLINE FIXTURE — not a Gemini run` |

---

## 6. 需要其他人回覆的事

| # | 問題 | 找誰 | 期限 |
|---|---|---|---|
| D1 | 模擬資料的實際數值（溫度上限、流量百分比、各函式回傳筆數）與 5 個函式正式名稱，我回填本文件 | Eddie | 10/8 |
| D2 | 「Create work order」要由主管按一下才建立（本稿設計，人在迴路裡、呼應 Quinn 的「一鍵放大錯誤」顧慮），還是結論出來自動建立？我建議按一下，後端只多一個 API 觸發點 | Eddie、Paula | 10/1 |
| D3 | 信心標籤理由列的判定規則（PRD Q4） | Paula、Quinn | 10/8 |
| D4 | 旁白的「40 minutes」與損失金額是否已有受訪者數字（PRD Q5） | Sandy、Felix | 10/3 |
| D5 | 錄影版需要誰演「評審掃碼」的手機畫面（錄影腳本在 10/16） | 老闆 | 10/16 |
| D6 | Recap 的人工基準：訪談後提供 `MANUAL_BASELINE_MIN`（分鐘）和 `MANUAL_BASELINE_SOURCE`（來源一句話）。沒有真實數字就不要設定，畫面會自動顯示中性文案 | Sandy、Felix | 10/3 |
| D7 | PRD F1「不做動畫」改成「除了調查鏡頭拉近和根因脈動以外不做動畫，reduced-motion 時全部關閉」 | Paula | 10/1 |
