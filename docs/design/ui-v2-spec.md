# UI v2 規格：證據小圖、根因亮燈、窄螢幕版面、前後對比收尾

- 建立：2026-09-24，Dana（設計）
- 依據：老闆 UI 改版指示（四個重點）、主持人 758px 實測回報、`docs/meetings/2026-09-24-駭客松主題方向.md`
- 讀者：Eddie（實作）、Quinn（驗收）
- 搭配：
  - `docs/design/ui-spec.md`：v1 token 與元件。**本文件和 v1 衝突時，以本文件為準**；v1 被取代的章節我已經在原檔標註。
  - `docs/design/storyboard.md`：英文文案定稿。v2 新增的文案寫在 storyboard §5.8–§5.10，本文件只引用。
  - `docs/design/line-layout-v2.svg`：新版產線圖（取代 `line-layout.svg`），請整份複製成 `app/static/line-layout.svg`。
- 範圍：只有前端表現，外加兩個小的後端資料需求（§1.3 的 `card.chart`、§4.2 的 `manual_baseline`），由 Eddie 決定怎麼實作。

---

## 0. 摘要

| # | 老闆要的 | v2 做法（一句話） |
|---|---|---|
| 1 | 證據小圖 | 每張證據卡依種類畫四種內嵌 SVG 小圖之一（事件時間軸／數值＋SOP 上限／數值 vs 基準／指令 vs 實際）；資料由後端在 `card.chart` 一起回傳，圖上的數字都能在原始列找到。 |
| 2 | 根因亮起 | 按 Investigate 後，產線圖鏡頭拉近到 L2-M3；結論一出，藍色虛線調查框轉成琥珀實線，CV-2 閥門轉琥珀、脈動 3 次，旁邊出現 `ROOT CAUSE` 標籤。灰卡則把鏡頭拉回全景，Line 1 外框變灰色虛線，標 `No root cause found`。 |
| 3 | 窄螢幕 | 四段寬度斷點＋一個矮螢幕修飾。1280×720、1366×768 整頁不捲動，結論卡完整可見；<1024 改成上下堆疊。結論卡移到面板頂端固定，證據卡收合成精簡列。 |
| 4 | 前後對比 | 工單 modal 加 `Show summary`，開啟 Recap 收尾畫面。After＝這次實測秒數；Before＝環境變數設定的人工基準加上來源說明，沒設定就只顯示 `—` 和中性文案。**畫面上沒有任何寫死的 40 分鐘。** |

**這版刻意不做**（請不要順手加上）：圖表函式庫、座標軸與格線、滑鼠 hover tooltip、數字跳動（count-up）動畫、結論出現就自動彈出 Recap、灰卡情境的 Recap、「快 N 倍」這類倍數字樣、地圖可拖曳縮放、輸送帶動畫、停線燈號閃爍。

---

## 1. 證據小圖（Evidence charts）

### 1.1 原則

1. **圖不能自己生出數字**：圖上的每個點都是這張卡原始列的值，不做平滑、不插值、不外推；缺值就斷線。圖上出現的文字數字只能重複卡片文字裡已經有的數字（SOP 上限、基準平均、since 時間），或是這次查詢原始列裡的值（事件時間、指令開度）。Quinn 的「數字可回查」同樣適用在圖上。
2. **圖是佐證，不是主角**：卡片的關鍵數值（28px）仍然是第一眼要看到的東西；圖放在數值下面，高度不超過卡片的 40%。
3. **不引入圖表庫**：純 JS 產生內嵌 `<svg>`，每種圖大約 60–120 行。
4. **同一份資料畫兩種大小**：完整卡用「完整圖」，精簡列用「迷你圖」（沒有文字）。

### 1.2 每種卡用哪種圖

| 卡片（函式／感測器） | 圖種 `kind` | 畫什麼 | Demo 中的例子 |
|---|---|---|---|
| `get_alarm_events` | `events` | 橫向時間軸，每筆警報一個點，**形狀**依嚴重度區分 | #1：02:54 ▲ Warning、03:00 ◆ Trip |
| `get_shift_log` | `events` | 同上；交班、備註畫空心圓，維修、參數變更、換料畫實心方塊 | #5：02:30 ○ Handover |
| `get_sensor_window`（非閥位） | `series_limit` | 數值折線＋SOP 正常帶（淡色）＋越過的那條 SOP 上／下限虛線＋越限起點標記＋關鍵點圓點 | #2：模具溫度越過 SOP 205 °C |
| `get_sensor_window`（`cv_position_pct`） | `command_vs_actual` | 實際開度實線＋指令開度虛線＋兩線之間的差距填色＋卡住起點標記 | #4：CV-2 指令 80%、實際 20% |
| `compare_to_baseline` | `series_baseline` | 時間窗內數值折線＋基準平均虛線＋正常變動帶＋偏離起點標記＋最新值圓點 | #3：冷卻水流量掉到基準的 41% |
| `list_sensors` | 無（`chart: null`） | 不畫圖，也不留空白區域 | — |

### 1.3 資料合約：`step.card.chart`（後端，Eddie）

現況：`/api/investigations/{id}` 的 step 只有 `card`（key_value、key_detail、highlight_row_ids），時間序列只存在給 Gemini 的 `summary`，SOP 上下限也不在 step 裡。前端如果自己去拉 `/evidence/{step}` 原始列，就還得在 JS 裡再寫一份 SOP 上下限，等於兩處各有一份真相。**所以請在 `app/queries/functions.py` 建 card 的同時，決定性地（deterministically）產生 `card["chart"]`。** 它只給前端用，不送進 Gemini，不影響 token 與回歸結果；逾時退回快取時會跟 card 一起被快取。

```jsonc
"chart": {
  "kind": "series_limit",              // series_limit | command_vs_actual | series_baseline | events
  "unit": "°C",
  "x_start": "02:30:00",               // 查詢時間窗起點
  "x_end": "03:00:00",                 // min(時間窗終點, 情境 now)；events 用 end + 59 秒（和 SQL 一致）
  "series": [                          // events 沒有這個欄位
    { "role": "actual",  "points": [["02:30", 188.2, "R01-S01802"], ["02:31", 188.4, "R01-S01814"]] },
    { "role": "command", "points": [["02:30", 80.0, "R01-S01809"]] }   // 只有 command_vs_actual 有
  ],
  "limit":    { "side": "high", "value": 205.0, "label": "SOP limit 205 °C" },  // 只在有越限時出現，否則 null
  "band":     { "low": 180.0, "high": 205.0 },                                  // 見下表
  "baseline": { "value": 42.0, "label": "Baseline 42 L/min" },                  // 只有 series_baseline 有
  "command_label": "Commanded 80%",                                             // 只有 command_vs_actual 有
  "marker":   { "ts": "02:52", "label": "since 02:52", "row_id": "R01-S…" },    // 越限／偏離起點；沒有就 null
  "key_point":{ "ts": "03:00", "value": 214.0, "row_id": "R01-S…" },            // key_value 取自哪一列
  "events": [ { "ts": "03:00:12", "level": "critical", "label": "Trip 03:00", "row_id": "R01-E005" } ],
  "empty_label": "No data"             // 完全沒有點時顯示的字
}
```

`points` 是 `[時間, 值, row_id]`；`value` 可以是 `null`，代表缺值。

**欄位對照（都是 `functions.py` 裡現成的變數，不需要新查詢）**

| chart 欄位 | `series_limit`（`_get_sensor_window`） | `command_vs_actual`（`_get_sensor_window`＋`cmd`） | `series_baseline`（`_compare_to_baseline`） | `events`（`_get_alarm_events`／`_get_shift_log`） |
|---|---|---|---|---|
| `series[actual]` | `main` → `(hm(ts), value, row_id)` | `main` | `win`（只畫時間窗，不畫基準期） | — |
| `series[command]` | — | `cmd` | — | — |
| `limit` | 有 `high` → `{side:"high", value: hi}`；有 `low` → `{side:"low", value: lo}`；否則 `null` | `null` | — | — |
| `band` | `{low: lo, high: hi}`（SOP 正常範圍） | `null` | `{low: b_mean − threshold, high: b_mean + threshold}` | — |
| `baseline` | — | — | `{value: b_mean, label: "Baseline {_fmt(b_mean)} {unit}"}` | — |
| `command_label` | — | `"Commanded {_fmt(cmd[-1].value)}%"`（和 key_detail 的 `commanded 80%` 同一個值） | — | — |
| `marker` | `high` 或 `low` 那一列 → `since {hm}` | 同左（Demo 是 `low`：卡在 20%） | `dev_start` → `since {hm}` | — |
| `key_point` | `mx`（越上限）／`mn`（越下限）／`last`（正常），**和 key_value 同一列** | 同左（Demo 是 `mn`） | `extreme` | — |
| `events[]` | — | — | — | 每列 → `{ts: hms, level, label, row_id}` |
| `empty_label` | `No data` | `No data` | `No data` | 警報：`No alarms`；交班紀錄：`No log entries` |

`events[].level` 與 `label` 規則：

| 來源 | 條件 | level | label |
|---|---|---|---|
| 警報 | severity `critical`、code 結尾是 `_TRIP` | `critical` | `Trip {HH:MM}` |
| 警報 | severity `critical`（其他） | `critical` | `Critical {HH:MM}` |
| 警報 | severity `warning` | `warning` | `Warning {HH:MM}` |
| 交班紀錄 | `parameter_change` | `notable` | `Parameter change {HH:MM}` |
| 交班紀錄 | `maintenance` | `notable` | `Maintenance {HH:MM}` |
| 交班紀錄 | `material_change` | `notable` | `Material change {HH:MM}` |
| 交班紀錄 | `shift_handover` | `info` | `Handover {HH:MM}` |
| 交班紀錄 | `operator_note`、其他 | `info` | `Note {HH:MM}` |

label 由後端組好，是固定模板，**絕對不能**把交班紀錄的 message 原文放進 label（R07 裡有 prompt injection 字串）。

建議 Eddie 在 `tests/test_queries.py` 加三條測試：`chart` 裡每個 `row_id` 都在 `rows` 裡；`key_point.row_id` 在 `highlight_row_ids` 裡；`limit.value` 等於 catalog 的 SOP 上下限。

### 1.4 尺寸

| | XL ≥1600 | L 1280–1599 | M 1024–1279 | S <1024 |
|---|---|---|---|---|
| 完整圖 | 寬 100%（卡片內容寬）× 高 `--chart-h` 96px | 100% × 72px | 100% × 72px | 100% × 72px |
| 迷你圖 | 120 × 32 | 96 × 28 | 96 × 28 | 96 × 28 |
| 資料線寬 | 2.5px | 2.5px | 2.5px | 2.5px（迷你圖 2px） |
| 標籤字 | 16px / 600 | 16px / 600 | 16px / 600 | 16px / 600 |

- 完整圖的 SVG 用實際像素畫：render 時讀容器的 `clientWidth` 當 `w`，`viewBox="0 0 {w} {h}"`。視窗 resize 結束 150ms 後（debounce）重畫；這樣文字和圓點不會變形。迷你圖是固定尺寸，不用重畫。
- 圖區上下各留 `--space-2`（8px）和關鍵數值、meta 列分開。

### 1.5 繪製規則

**座標**
- `x(t) = padL + (t − x_start) / (x_end − x_start) × (w − padL − padR)`，t 換算成秒。
- `y(v) = padT + (1 − (v − y0) / (y1 − y0)) × (h − padT − padB)`。
- 內距：完整圖 `padT 6, padR 10, padB 6, padL 6`；迷你圖 `3, 4, 3, 3`。標籤直接疊在圖上，靠 halo 描邊保持可讀，不另外保留標籤區。

**y 範圍**（上下各加 15% 留白；全部值都一樣時上下各 ±1 單位）
- `series_limit`：有越限 → 所有值 ∪ {limit.value}；沒越限 → 所有值 ∪ {band.low, band.high}
- `series_baseline`：所有值 ∪ {band.low, band.high, baseline.value}
- `command_vs_actual`：固定 0–100

**線**
- 用折線（`L` 指令），不畫曲線。`stroke-linejoin: round; stroke-linecap: round`。
- **斷線**：相鄰兩點相差超過 90 秒，或值是 `null`，就開新的子路徑（`M`），不要把兩邊連起來。
- **缺值區**：斷掉的區間（也包含 x_start 到第一點、最後一點到 x_end）畫 `--chart-missing` 45° 斜線底紋（間距 6px、線寬 1.5px、opacity 0.6）；區間寬度 ≥48px 時在中間標 `No data`。
- **變色**：`card.tone` 不是 `normal` 而且有 `marker` 時，marker 之前用 `--chart-series`（藍），marker 之後（包含 marker 那一點）用 `--chart-series-abnormal`（琥珀）。其餘情況整條藍色。
- **關鍵點**：`key_point` 畫實心圓（完整圖 r5、迷你圖 r3），填該段的顏色，外框 2px `--chart-halo`，讓觀眾看到「卡片上的數字從這一點來」。

**參考線與標籤**（字 16px/600；所有圖內文字都要加 halo：`paint-order: stroke; stroke: var(--chart-halo); stroke-width: 4px; stroke-linejoin: round;`）
- **SOP 上下限**（`limit`）：1.5px 虛線 `6 4`，顏色 `--chart-limit`，橫跨全寬。標籤 `limit.label` 放在左端（x = padL + 4），擺在線「遠離第一個資料點」的那一側：第一點在線下方，標籤就放線上方 4px；反之放線下方 16px。
- **沒越限時的正常帶**（`band`）：只填 `--chart-band` 淡色帶，不畫虛線；左端標 `SOP range`（不寫數字，數字不在卡片文字裡）。
- **基準線**（`baseline`）：1.5px 點線 `2 4`，顏色 `--chart-baseline`；`band` 用 `--chart-band` 填色。標籤放右端靠右對齊（text-anchor end），擺在遠離最後一點的那一側。
- **指令線**（`command`）：2px 虛線 `8 4`，顏色 `--chart-command`。`command_label` 放在指令線上方、右端靠右。實際線的標籤 `Actual` 放在實際線遠離指令線的那一側、右端靠右（**不寫數字**，避免和 key_value 的最小值打架）。從 marker 到 x_end，兩線之間用 `--chart-gap-fill` 填滿。
- **起點標記**（`marker`）：1.5px 虛線 `4 3` 的直線，顏色 `--chart-marker`，由上畫到下。標籤 `marker.label` 貼在直線右邊 6px、圖底部；如果 marker 落在最右側 30% 的範圍內，標籤改放左邊（text-anchor end）。

**繪製順序**：band → 缺值斜線 → limit／baseline 線 → 差距填色 → command 線 → 資料線 → marker 線 → 關鍵點 → 所有文字。

**events**
- 軸線：y = h/2，1px `--chart-axis`，左右兩端各一個 4px 高的刻度。
- 事件形狀（**靠形狀區分，不只靠顏色**）：
  - `critical`：實心菱形 12×12，`--chart-event-critical`
  - `warning`：實心三角 12，`--chart-event-warning`
  - `notable`：實心方塊 10×10，`--chart-event-notable`
  - `info`：空心圓 r5，2px `--chart-event-info`
- 標籤最多 3 個，從最新的往前算：最新的放軸線上方（baseline y = h/2 − 12），下一個放下方（y = h/2 + 24），上下交替。x 超過寬度 70% 時 text-anchor end（x − 8），否則 start（x + 8）。其他事件只畫形狀。
- 兩個點距離小於 8px 時，後畫的往右錯開 4px。
- 沒有事件：只畫軸線，中間放 `empty_label`（16px `--color-text-secondary`，加 halo）。

**迷你圖**：只畫資料線、指令線、limit／baseline 線（1px）、關鍵點；events 只畫軸線和形狀（8px）。**不畫任何文字、不畫斜線底紋**（斷線就好），整個 `aria-hidden="true"`。

### 1.6 狀態與例外

| 卡片狀態／資料情況 | 完整圖 | 迷你圖 |
|---|---|---|
| `running` | 同高度的 skeleton 方塊（`--color-surface-3`、radius-sm），不做閃動 | 不顯示（running 時沒有精簡列） |
| `done` | 正常繪製 | 正常繪製 |
| `cached` | 正常繪製（資料和快取的 card 同一份），右上角照舊有 `Cached` chip | 正常繪製＋精簡列上有 `Cached` chip |
| `error` | 不畫圖，維持 v1 的 `Query failed` | 不畫 |
| `chart` 是 `null`（`list_sensors` 或舊版後端） | 不畫、不留空位 | 不畫 |
| series 完全沒有點（key_value `No data`） | 同高度虛線框（1px `--color-border-strong`，`4 4`），中間 `No data` | 空白，同尺寸 |
| 部分缺值 | 斷線＋斜線底紋＋`No data` | 斷線 |
| 時間窗超過情境 now | 不會發生：x_end 已經截在 now，未來的分鐘不算缺值（和 BUG-002 一致） | — |
| 事件為 0 | 軸線＋`No alarms`／`No log entries` | 只有軸線 |

### 1.7 四種圖的示意（完整圖，L 斷點 382×72）

```
series_limit：#2 Mold temperature（tone warn）
┌──────────────────────────────────────────────────────┐
│ SOP limit 205 °C          ┆                      ╱●  │  ← 琥珀段＋關鍵點（214 °C 那一列）
│ - - - - - - - - - - - - - ┆- - - - - - - - - ╱- - - -│  ← 1.5px 虛線 --chart-limit
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━┆━━━━━━━━━━━━━╱          │  ← 藍段（marker 之前）
│                           ┆since 02:52              │  ← marker 虛線＋標籤
└──────────────────────────────────────────────────────┘

series_baseline：#3 Coolant flow vs. baseline（tone warn）
┌──────────────────────────────────────────────────────┐
│░░━━━━━━━━┓░░░░░░░░░░░░░░░░░░░░░░ Baseline 42 L/min ░│  ← 基準點線＋正常帶（░）
│          ┆                                           │
│          ┃since 02:41                                │
│          ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━●│  ← 琥珀段，● = 最新值（41%）
└──────────────────────────────────────────────────────┘

command_vs_actual：#4 Cooling valve CV-2 position（tone warn）
┌──────────────────────────────────────────────────────┐
│                                      Commanded 80%   │
│ ─ ─ ─ ─ ─ ─ ─ ─ ┬ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ │  ← 指令虛線
│ ━━━━━━━━━━━━━━━━┓▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒│  ← ▒ 差距填色
│                 ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━●│  ← 實際（琥珀），● = 最小值 20%
│                 since 02:41                   Actual │
└──────────────────────────────────────────────────────┘

events：#1 Alarm events（tone danger）
┌──────────────────────────────────────────────────────┐
│                                         Trip 03:00   │
│ ├──────────────────────────────────────────▲──────◆┤ │  ← ▲ warning、◆ critical
│                                   Warning 02:54      │
└──────────────────────────────────────────────────────┘
```

正常情境（灰卡加演）的四張卡：三條線都是藍色、沒有 marker、數值都在正常帶或基準帶裡；#1 只有軸線加 `No alarms`。「看起來很平靜」本身就是灰卡的佐證。

### 1.8 完整卡與精簡列

**完整卡**（v1 §3.6 的結構，加入圖）：

```
┌──────────────────────────────────────────────────┐
│ Mold temperature                        ✓ Done ▾ │  標題 --fs-lg / 600；▾ 可收合
│ 214 °C  Above SOP 4.2 limit of 205 °C since 02:52│  關鍵數值 --fs-xl / 700＋說明 --fs-md
│ ┌──────────────────────────────────────────────┐ │
│ │               （完整圖，--chart-h）            │ │  role="img" aria-label=…
│ └──────────────────────────────────────────────┘ │
│ get_sensor_window · 02:30–03:00 · 31 rows        │  meta 16px muted
│ View source rows (31)        [Cited in conclusion]│
└──────────────────────────────────────────────────┘
```

**精簡列**（整列就是一個 `<button>`，高度 `--compact-h`）：

```
 ②  ┌────────────────────────────────────────────┐
    │ Mold temperature                  ╱‾‾●     │  第 1 行：標題 18px/600，超長就省略號
    │ 214 °C  [Cited]  ▸                          │  第 2 行：關鍵數值 20px/700（tone 色）＋tag＋▸
    └────────────────────────────────────────────┘
```

- grid：`grid-template-columns: minmax(0, 1fr) var(--chart-mini-w); column-gap: var(--space-3); padding: 6px var(--space-3)`；背景 surface-2、1px border、radius-md；hover 時 surface-3；focus 時 `--focus-ring`。
- 第 2 行的 tag 用短文案：`Cited`（info-bg／info）或 `Ruled out`（外框樣式）；有 cached 時再加 `Cached` chip；error 時第 2 行改成 danger 字 `Query failed`。
- 左側時間軸圓圈照舊（v1 §3.6），L 以下縮成 28px。
- 點精簡列就展開成完整卡；完整卡標題列右邊的 `▾` 可以收合。`aria-expanded`、`aria-controls="card-{n}-full"`；按鈕的 aria-label 例：`Step 2, Mold temperature, 214 °C, cited in conclusion. Show details`。

**收合規則（accordion）**

1. 調查中：新的一步出現時，前面所有**沒有被使用者手動展開**的卡都收成精簡列；最新一張（含 running 的 skeleton）維持完整。
2. 使用者手動展開的卡會保持展開，直到使用者自己收合或結論出現。
3. 使用者在證據列上滾輪或點擊後，暫停自動捲動（沿用 v1 規則）。
4. 結論（或灰卡）出現時：全部收成精簡列，**只有原始列正在展開的那一張例外**。
5. 結論卡的引用 chip（`#3`）：捲到 #3、展開它、閃一次 info 外框（v1 的 flash）。
6. 原始列表格最多高 `--rows-max-h`（XL 280px；矮螢幕 200px），超過就在表格內捲動。

---

## 2. 產線圖：根因亮燈與灰卡

### 2.1 SVG v2 改了什麼（`docs/design/line-layout-v2.svg`）

- viewBox 從 `1200×640` 改成 **`1200×600`（2:1）**，`preserveAspectRatio="xMidYMin meet"`。
- 字級放大：車道名 24→30、機台名 20→28、編號 16→20、狀態 18→26、閥門標籤 14→20。1280 寬全景時，機台名和狀態字實際約 16–17px。
- 每台機台多一個隱藏的 `.rc-tag`（`ROOT CAUSE`）；每個閥門多 `.valve-bg`（琥珀 pill）和 `.valve-pulse`（脈動環）；每條車道多一個隱藏的 `#L{n}-badge`（`No root cause found`）。
- 所有樣式都加了 `#line-layout` 前綴，避免和頁面 CSS 撞名。
- v1 用到的 ID 全部保留（`L{n}`、`L{n}-status`、`L{n}-M{m}`、`L{n}-M{m}-state`、`.name`、`L{n}-M3-CV{n}`），`app.js` 現有的 `setMachine`、`resetPlant` 不用改。
- `.valve.is-fault` 移除，改用 `.valve.is-root-cause`（原因見 2.2：根因用琥珀，紅色只代表停線）。

### 2.2 狀態 class

| 對象 | class | 外觀 | 誰加、何時加 |
|---|---|---|---|
| 機台 | `is-focus` | 藍色 3px 虛線框，marching ants（1 秒一圈） | 按 Investigate，加在焦點機台 |
| 機台 | `is-root-cause` | 同一個框變成**琥珀 4px 實線**；`ROOT CAUSE` 標籤淡入（+300ms） | 結論 `root_cause`，同時移除 `is-focus` |
| 機台 | `is-low-confidence` | 疊在 `is-root-cause` 上：標籤改成外框樣式（底色 surface-1、琥珀字）、閥門不脈動 | 信心 Low |
| 閥門 | `is-root-cause` | 琥珀 pill 底＋2px 琥珀框、圖示與字轉琥珀（+300ms）；脈動環 3 次（+500ms 開始，每次 1.2 秒，約 +4.1 秒結束），之後只留靜態 pill | 根因是閥門時 |
| 車道 | `is-dimmed` | opacity 0.5 | 鏡頭拉近時，加在非焦點車道 |
| 車道 | `is-inconclusive` | 外框灰色 3px 虛線 `12 8`＋`No root cause found` 徽章 | 灰卡出現後 +850ms（等鏡頭拉回全景） |

- **根因用琥珀、停線用紅**：L2-M3 本體保持紅色 `STOPPED`（症狀），外框和閥門是琥珀（原因），和面板上緣是琥珀線的結論卡連成一組。兩者另外還有文字（`STOPPED`／`ROOT CAUSE`）和形狀（紅粗框／琥珀實線環）可以分辨，色弱也看得出來。
- 根因的出場時序寫在 SVG 的 CSS delay 裡，**JS 只要在 t=0 換 class**，不需要 setTimeout。灰卡只有一步（+850ms），用一個 setTimeout。
- `prefers-reduced-motion`：SVG 內已經寫好，不跑 marching ants、不脈動、沒有 transition，最終狀態直接出現。

### 2.3 根因對應到地圖上的哪裡

前端常數（`app.js`）。之後如果 Eddie 想把它搬到後端（`conclusion.map_target`），前端照著用即可。

```js
const RC_TARGET = {
  cv_valve_stuck_closed:    { machine: "M3", valve: true },
  cv_valve_stuck_open:      { machine: "M3", valve: true },
  coolant_supply_temp_high: { machine: "M3" },
  coolant_filter_clogged:   { machine: "M3" },
  heater_stuck_on:          { machine: "M3" },
  temp_sensor_drift:        { machine: "M3" },
  setpoint_change:          { machine: "M3" },
  hydraulic_pressure_low:   { machine: "M3" },
  dryer_temp_low:           { machine: "M2" },
  feeder_blockage:          { machine: "M1" },
  // "other" 或未知：地圖上不標 ROOT CAUSE（不替模型猜位置），鏡頭拉回全景
};
```

結論出現時：`L{line}-M{m}` 加 `is-root-cause`（Low 時再加 `is-low-confidence`）；`valve: true` 就對 `L{line}-M3-CV{line}` 加 `is-root-cause`。根因機台如果和目前焦點不同，就把鏡頭補間到新目標（§2.4）。

### 2.4 鏡頭拉近（focus zoom）

只改 SVG 的 `viewBox`，長寬比固定 2:1，所以 Plant 區的大小不會變，不會造成版面跳動。

```js
const OVERVIEW = [0, 0, 1200, 600];
function focusBox(line, m) {                 // m = 1..4
  const cx = 180 + (m - 1) * 256 + 114;      // 機台中心 x
  const cy = 12 + (line - 1) * 200 + 88;     // 車道中心 y
  const w = 768, h = 384;                    // 2:1，約 1.56 倍
  return [Math.min(Math.max(cx - w / 2, 0), 1200 - w),
          Math.min(Math.max(cy - h / 2, 0), 600 - h), w, h];
}
// L2-M3 → [422, 108, 768, 384]；L1-M3 → [422, 0, 768, 384]

const reduceMotion = () => matchMedia("(prefers-reduced-motion: reduce)").matches;
function tweenViewBox(svg, to, ms) {
  const b = svg.viewBox.baseVal, from = [b.x, b.y, b.width, b.height];
  if (reduceMotion() || !ms) return svg.setAttribute("viewBox", to.join(" "));
  const t0 = performance.now(), ease = (t) => (t < .5 ? 4 * t * t * t : 1 - (-2 * t + 2) ** 3 / 2);
  requestAnimationFrame(function step(now) {
    const t = Math.min(1, (now - t0) / ms), e = ease(t);
    svg.setAttribute("viewBox", from.map((v, i) => v + (to[i] - v) * e).join(" "));
    if (t < 1) requestAnimationFrame(step);
  });
}
```

| 時機 | 鏡頭 | 其他 |
|---|---|---|
| 載入、Reset、切換情境 | 全景 `OVERVIEW`（Reset 補間 400ms） | 清除 focus、root-cause、dimmed、inconclusive |
| 按 Investigate | 補間到 `focusBox(line, 焦點機台)`，700ms | 非焦點車道加 `is-dimmed`；焦點機台加 `is-focus` |
| 結論 `root_cause` | 留在原位（目標不同就補間到根因機台） | 見 §2.2 |
| 結論 `insufficient_evidence` | 拉回全景，700ms | 移除 `is-focus` 和 `is-dimmed`；+850ms 對 `L{line}` 加 `is-inconclusive` |
| `failed`、`cancelled` | 拉回全景 | 移除所有調查標記 |

焦點機台 = `scenario.machine`，沒有的話用 `M3`（沿用 v1 的 `focusMachine`）。

**敘事**：找到根因時鏡頭停在凶手身上；證據不足時鏡頭退回全線，意思是「整條線都查過了，沒有可以指認的東西」。

### 2.5 四個狀態示意（Plant 區）

```
A. 載入（全景）                                   B. 調查中（拉近 L2 M2–M4，其他車道 50%）
┌──────────────────────────────────────────┐   ┌──────────────────────────────────────────┐
│ LINE 1 [Feeder][Dryer][Molding][Inspect.]│   │ (L1 下緣，淡化)                            │
│ LINE 2 [Feeder][Dryer][▓Molding▓][Insp.] │   │ ┌Dryer──────┐ ┌╌╌╌╌╌╌╌╌╌╌╌╌╌┐ ┌Inspection┐ │
│  Stopped        STOPPED(紅)              │   │ │L2-M2      │ ╎Molding    ● ╎ │L2-M4     │ │
│ LINE 3 [Feeder][Dryer][Molding][Inspect.]│   │ │RUNNING    │ ╎L2-M3        ╎ │RUNNING   │ │
└──────────────────────────────────────────┘   │ └───────────┘ ╎STOPPED(紅)  ╎ └──────────┘ │
                                                │               └╌╌╌╌╌╌╌╌╌╌╌╌╌┘ 藍虛線在跑   │
                                                │               (⋈ CV-2 valve)               │
                                                │ (L3 上緣，淡化)                            │
                                                └──────────────────────────────────────────┘
C. 找到根因（同一個鏡頭）                          D. 證據不足（拉回全景）
┌──────────────────────────────────────────┐   ┌──────────────────────────────────────────┐
│ ┌Dryer──────┐ ┏━━━━━━━━━━━━━┓ ┌Inspection┐ │   │┌╌LINE 1╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┐│
│ │L2-M2      │ ┃Molding    ● ┃ │L2-M4     │ │   │╎ Running [Feeder][Dryer][Molding][Insp.]╎│
│ │RUNNING    │ ┃L2-M3        ┃ │RUNNING   │ │   │╎ (? No root cause found)                ╎│
│ └───────────┘ ┃STOPPED(紅)  ┃ └──────────┘ │   │└╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┘│
│               ┗━━━━━━━━━━━━━┛ 琥珀實線     │   │ LINE 2 …（全部 RUNNING，沒有任何變色）      │
│              ((⋈ CV-2 valve))[ROOT CAUSE] │   │ LINE 3 …                                  │
│               琥珀 pill＋脈動 3 次          │   └──────────────────────────────────────────┘
└──────────────────────────────────────────┘
```

### 2.6 產線圖無障礙

- SVG 是 `role="img"`，裡面 `<g>` 的 aria-label 讀屏軟體**讀不到**（role=img 的子元素都被當成裝飾）。所以狀態改變時，請同步更新 `<desc id="ls-desc">` 的內容，例：`Line 2 stopped. M3 Molding stopped. Root cause located: CV-2 cooling valve on Line 2 M3.`
- Plant 區加一個隱藏的 live region `<div id="plant-live" class="sr-only" aria-live="polite">`，結論出現時寫入一句（文案見 storyboard §5.9）。
- 鏡頭拉近時淡化的車道（opacity 0.5）屬於背景情境，不需要符合對比要求；它們的狀態一直寫在 banner 和 `<desc>` 裡。

---

## 3. 版面與斷點

### 3.1 斷點與 token

以寬度分四段，加一個「矮螢幕」修飾。數值都寫在 CSS 變數裡（完整程式碼見 §6）。

| | XL ≥1600 | L 1280–1599 | M 1024–1279 | S <1024 |
|---|---|---|---|---|
| 典型裝置 | 1920×1080 大螢幕 | 1366×768、1280×720 投影機；筆電 | 小筆電、視窗化瀏覽器 | 758px 視窗（主持人實測）、平板直向 |
| 欄位 | `7fr / 5fr` | `1fr / clamp(440px, 38vw, 560px)` | `1fr / 420px` | 單欄堆疊 |
| 左右外距 `--gutter` | 32 | 24 | 16 | 16 |
| 欄距 `--gap` | 24 | 16 | 16 | 16 |
| Banner | 單行：文字｜計時器｜按鈕 | 三區：文字＋計時器，按鈕在下一行靠右 | 同 L | 直排：文字 → 計時器＋按鈕 |
| 計時器 `--fs-display` | 64 | 44 | 40 | 40 |
| 根因字 `--fs-2xl` | 40 | 30 | 28 | 28 |
| `--fs-xl`／`--fs-lg` | 28／22 | 24／20 | 24／20 | 24／20 |
| Investigate 按鈕 | 高 64、最小寬 240 | 56、232 | 56、220 | 56、220（<600 時寬 100%） |
| 完整圖高 | 96 | 72 | 72 | 72 |
| 精簡列高 | 60 | 56 | 56 | 56 |
| 面板捲動 | 證據列在面板內捲動 | 同左 | 同左 | 不在面板內捲動，改整頁捲動 |

**矮螢幕修飾**（`min-width: 1024px` 且 `max-height: 959px`，也就是投影機、非全螢幕瀏覽器）：TopBar 72→56、底列 48→40、主區上下內距 24→16、面板內距 24→16、原始列表格最高 280→200，結論卡改用 compact 版（§3.6）。

**全域防溢出規則**（這三條就是 758px bug 的直接修法）：
- `.main > *`、`.alert > *`、`.panel` 一律 `min-width: 0`。
- `#downtime`、`.btn-primary` 設 `white-space: nowrap`；標題與副標設 `overflow-wrap: anywhere`。
- 版面不准用絕對定位疊元素；只有 modal、Recap、產線圖內部可以用。

### 3.2 各斷點示意

**XL（1920×1080，結論出現後）**：整頁不捲動，結論卡和 5 列精簡證據全部看得到。

```
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│ LineSleuth  Demo Plant · Night shift            Scenario time 03:01:05          Demo scenario│ 72
├──────────────────────────────────────────────────────┬────────────────────────────────────┤
│▌Line 2 stopped                    DOWNTIME            │ Investigation [Root cause found]    │
│▌M3 Molding · Over-temperature     00:01:05 [Investigated]│                     Elapsed 00:52 │
│▌alarm at 03:00                                        │┏ROOT CAUSE━━━━━ ▮▮▮ Confidence: High┓│
│                          ● Running ● Warning ● Stopped││Cooling valve CV-2 stuck at 20% open ││
│┌────────────────────────────────────────────────────┐││3 independent signals agree · 1 alt… ││
││                                                    │││Evidence [#2][#3][#4]                ││
││       產線圖（鏡頭拉近 L2-M3，狀態 C）              │││Ruled out  Shift handover at 02:30 … ││
││       寬約 1070px → 高約 535px                      │││Recommended actions                  ││
││                                                    │││1. … 2. … 3. …   [Create work order] ││
│└────────────────────────────────────────────────────┘│└─────────────────────────────────────┘│
│                                                      │ Evidence · 5 queries                 │
│                                                      │① Alarm events            ◆▲   ▸      │
│                                                      │② Mold temperature 214 °C [Cited]  ▸  │
│                                                      │③ Coolant flow… 41% [Cited]        ▸  │
│                                                      │④ Cooling valve… 20% [Cited]       ▸  │
│                                                      │⑤ Shift & maint… Handover [Ruled out] │
├──────────────────────────────────────────────────────┴────────────────────────────────────┤
│ Scenario: [Line 2 over-temperature ▾]  Reset                           Agent: gemini-3-flash │ 48
└───────────────────────────────────────────────────────────────────────────────────────────┘
```

**L（1366×768／1280×720，矮螢幕修飾生效，畫的是調查中第 4 步）**：Banner 改成三區，按鈕移到第三行靠右（剛好在計時器正下方，視線動線不變）。精簡列實際上是兩行（§1.8），這裡簡化成一行。

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ LineSleuth  Demo Plant · Night shift     Scenario time 03:00:14  Demo scenario│ 56
├────────────────────────────────────────────┬─────────────────────────────────┤
│▌Line 2 stopped                  DOWNTIME    │ Investigation [Investigating]   │
│▌M3 Molding · Over-temperature   00:00:14    │                  Elapsed 00:31  │
│▌alarm at 03:00                              │ ① Alarm events  Over-temp… ▸    │ ← 精簡
│▌                         [⟳ Investigating…] │ ② Mold temperature 214 °C  ▸    │
│                  ● Running ● Warning ● Stop │ ③ Coolant flow… 41%        ▸    │
│┌──────────────────────────────────────────┐│┌───────────────────────────────┐│
││                                          │││Cooling valve CV-2 position ✓ ▾││ ← 最新一張完整
││  產線圖（鏡頭拉近）                        │││20%  Below normal range since …││
││  1280 寬：左欄 730px → 圖高 365px          │││┌─────────────────────────────┐││
││  1366 寬：左欄 783px → 圖高 391px          ││││ command_vs_actual 72px      │││
││                                          │││└─────────────────────────────┘││
│└──────────────────────────────────────────┘││get_sensor_window · 02:30–03:00 ││
│                                            ││View source rows (62)           ││
│                                            │└───────────────────────────────┘│
├────────────────────────────────────────────┴─────────────────────────────────┤
│ Scenario: [Line 2 over-temperature ▾]  Reset                     Agent: …    │ 40
└──────────────────────────────────────────────────────────────────────────────┘
```

**M（1024–1279）**：跟 L 一樣，面板固定 420px。全景時產線圖的字大約 13px，偏小；按下 Investigate 拉近後會到 16px 以上。M 不是 demo 斷點，這個程度可以接受。

**S（<1024，以 758px 為例）**：單欄，整頁捲動；面板內不捲動。

```
┌──────────────────────────────────────┐
│ LineSleuth  Demo Plant · Night shift  │  TopBar 可以折成兩行（高度 auto），不隱藏任何字
│ Scenario time 03:00:14  Demo scenario │
├──────────────────────────────────────┤
│▌Line 2 stopped                        │
│▌M3 Molding · Over-temperature alarm   │
│▌at 03:00                              │
│▌DOWNTIME                              │
│▌00:00:14            [🔍 Investigate]  │  ← 計時器和按鈕同一行，按鈕一定完整可點
├──────────────────────────────────────┤
│             ● Running ● Warning ● Stop│
│ 產線圖 全寬 726px → 高 363px            │  全景時機台名稱約 17px
├──────────────────────────────────────┤
│ Investigation [Not started]           │
│ No investigation yet. …               │  面板高度 auto，跟著內容長
├──────────────────────────────────────┤
│ Scenario: [ … ▾ ]  Reset              │
└──────────────────────────────────────┘
```

- S 的調查流程：新卡出現時，如果使用者還沒自己捲過頁面，整頁自動捲到最新那張卡（`block: "nearest"`）；結論出現時捲到結論卡頂端。產線圖上的亮燈要往上捲才看得到，S 不是 demo 斷點，可以接受。
- `<600`：Banner 四個區塊直排，Investigate 按鈕寬 100%。工單 modal 改成單欄，QR 240×240。

### 3.3 Banner 結構

請把 HTML 攤平成四個直接子元素（ID 都不變）：`h1#alert-title`、`p#alert-sub`、`div#downtime-box`、`button#investigate`。

```css
.alert { display: grid; column-gap: var(--space-5); row-gap: var(--space-2); align-items: center;
         grid-template-columns: minmax(0, 1fr) auto auto;
         grid-template-areas: "title timer action" "sub timer action"; }            /* XL */
#alert-title { grid-area: title; } #alert-sub { grid-area: sub; }
#downtime-box { grid-area: timer; } #investigate { grid-area: action; }

@media (max-width: 1599.98px) {                                                      /* L、M */
  .alert { grid-template-columns: minmax(0, 1fr) auto;
           grid-template-areas: "title timer" "sub timer" "action action"; }
  #investigate { justify-self: end; }
}
@media (max-width: 1023.98px) {                                                      /* S */
  .alert { grid-template-columns: minmax(0, 1fr) auto;
           grid-template-areas: "title title" "sub sub" "timer action"; }
}
@media (max-width: 599.98px) {
  .alert { grid-template-columns: 1fr; grid-template-areas: "title" "sub" "timer" "action"; }
  #investigate { width: 100%; justify-self: stretch; }
}
```

- 正常情境沒有計時器（`#downtime-box` 隱藏），grid 空出來的區域不影響版面。
- 按鈕寬度要能放下最長的文案 `Investigating…`＋spinner，而且不換行；`Investigate Line 1` 只出現在沒有計時器的情境，空間夠用。

### 3.4 面板：結論放頂端、證據列在下面

DOM 順序改成：

```html
<div id="panel-body" class="panel-body">
  <div id="empty">…</div>
  <div id="result"></div>                                    <!-- 結論卡／灰卡／失敗訊息 -->
  <div id="evidence-head" class="subhead hidden">Evidence · 5 queries</div>
  <div id="cards" class="evidence-list" aria-live="polite"></div>
</div>
```

```css
.panel-body   { display: flex; flex-direction: column; gap: var(--space-3); min-height: 0; overflow: hidden; }
#result       { flex: none; max-height: 72%; overflow-y: auto; }   /* 保險：結論卡再長也留空間給證據列 */
.evidence-list{ flex: 1 1 auto; min-height: 0; overflow-y: auto; padding-right: var(--space-2); }
@media (max-width: 1023.98px) { .panel-body, #result, .evidence-list { overflow: visible; max-height: none; } }
```

- 調查中 `#result` 是空的，證據列占滿整個面板。
- 結論出現：`#result` 在頂端長出來（不隨證據列捲動）；`#evidence-head` 顯示；證據列捲回頂端（smooth，reduced-motion 時直接跳）。
- 面板表頭在 M 寬度放不下時可以折行（`flex-wrap: wrap`），`Elapsed` 掉到第二行。

### 3.5 空間驗算（確認不會捲動）

| 螢幕（F11 全螢幕、縮放 100%） | 面板內容區高 | 結論卡 | 證據列可見 | 左欄：Banner＋圖例＋圖 |
|---|---|---|---|---|
| 1920×1080（XL） | 808 | 完整版約 420 | 5 列全部（5×60＋間距＝332）→ 共 796 ≤ 808 | 約 110＋28＋535 ≤ 912 |
| 1366×768（L＋矮） | 556 | compact 約 312 | 約 3 列（剩 206） | 152＋28＋391 ≤ 640 |
| 1280×720（L＋矮） | 508 | compact 約 312 | 約 2.5 列（剩 160） | 152＋28＋365 ≤ 592 |
| 1280×720 視窗化（可視高約 600） | 388 | compact 約 312 | 約 1 列 | 圖依高度縮小 |

- 調查進行中（1280×720）：4 列精簡（4×64）＋1 張完整（約 240）＝ 496 ≤ 508，最後一步出現時 5 張全部看得到。
- 產線圖在 L 是寬度受限（算出來的圖高比可用高度小），所以 Banner 從一行變三行，並不會壓縮到圖。

### 3.6 結論卡 compact 版（矮螢幕修飾）

```
┌━━ROOT CAUSE━━━━━━━━━━━━━━━━━━━━━━━━ ▮▮▮ Confidence: High ┐  小標和信心同一行
│ Cooling valve CV-2 stuck at 20% open                      │  --fs-2xl（L 30px），最多 2 行
│ 3 independent signals agree · 1 alternative ruled out     │  16px secondary
│ Evidence [#2] [#3] [#4]                                   │
│ Ruled out  Shift handover at 02:30 — no parameter changes │  最多 2 行
│ (#5)                                                      │
│ [▸ Recommended actions (3)]            [Create work order]│  同一行
└───────────────────────────────────────────────────────────┘
```

- 內距 `--space-4`。`Recommended actions` 收成 disclosure 按鈕（`aria-expanded`），展開後清單出現在按鈕列上方，這時 `#result` 自己內部捲動。旁白不念處置步驟，工單上也有，所以預設收起來。
- Low 信心的 `Low confidence — verify on site before acting.` 提示條照舊放在最上面。
- 完整版（高度 ≥960）：和 v1 §3.7 一樣，只有兩處調整：小標和信心放同一行；`Create work order` 放在處置清單右下，和清單底部對齊。
- 灰卡也放在同一個位置，內容照 v1 §3.8，不需要 compact 版（高度大約 320）。

### 3.7 758px 實測問題對照

| 主持人看到的 | 原因（現行 `app.css`） | v2 修法 |
|---|---|---|
| Investigate 被右側面板蓋住、點不到 | `.main` 在任何寬度都是 7fr/5fr；左欄只剩約 390px，`.alert` 是不換行的 flex，計時器（64px 字約 270px）加上按鈕（240px）溢出到右欄，右欄面板比較晚畫，蓋在上面 | <1024 改單欄；Banner 改 grid（§3.3）；`min-width: 0` |
| Downtime 數字溢出 | `--fs-display` 在所有寬度都是 64px，容器又不會縮 | 依斷點縮成 64/44/40，`nowrap`，放在固定的 grid 區域 |
| 產線圖字太小 | 1200 寬的 SVG 被縮到約 390px（0.33 倍），20px 的字只剩約 6.5px | 單欄全寬（0.6 倍）＋v2 字級放大＋調查時鏡頭拉近 |
| 結論後面板在小框內捲動、證據卡擁擠 | 5 張完整卡加結論卡全疊在同一個捲動區，結論在最底下 | 結論放頂端固定、證據收成精簡列、矮螢幕用 compact 結論 |

---

## 4. 收尾：Before / After（Recap）

### 4.1 觸發與流程

1. 結論（root cause）→ `Create work order` → 工單 modal（QR）。評審掃碼。
2. modal 底部按鈕列改成：`Done`（文字按鈕，關閉）＋ `Show summary`（outline 琥珀按鈕，放右邊）。
3. 按 `Show summary`，或在調查完成（root_cause）後隨時按鍵盤 `S` → 關掉 modal，開啟 Recap 全螢幕層。
4. `Close` 或 Esc 關閉，焦點回到開啟它的按鈕。
5. **不會自動彈出**：結論的那一刻是 demo 的高潮（格 ④），不能被蓋掉。
6. 灰卡、失敗、調查中：`S` 沒有反應，也沒有 `Show summary`。

### 4.2 數字從哪裡來

| 項目 | 來源 | 規則 |
|---|---|---|
| After（這次實測） | 調查結束後 `inv.elapsed_s`（伺服器 monotonic 時鐘，從收到 Investigate 到 finalize） | 和面板最終的 `Elapsed` **用同一個函式** `fmtElapsed()` 四捨五入到整數秒：`<60` → `52 s`；`≥60` → `1 min 12 s`。面板的 `Elapsed mm:ss` 在結束後也改用四捨五入，兩處數字必須相同。 |
| Before（人工基準） | 環境變數 `MANUAL_BASELINE_MIN`（分鐘，數字）＋ `MANUAL_BASELINE_SOURCE`（來源說明，≤120 字） | 後端讀取後放進 `/api/config` 的 `manual_baseline: {minutes, source}`；**兩個都有而且合法（1–480 分鐘）才回傳，否則回 `null`**，並在 log 寫一行 warning。只有數字沒有來源，視同沒設定。 |
| 查詢數、引用、排除 | `steps`（done＋cached）、`conclusion.cited_evidence`、`conclusion.ruled_out` | cached 的步驟數大於 0 時，要在明細後面加上 `· {k} cached` |
| 工單號 | `inv.work_order_id` | 有才顯示 |

- `.env.example` 請加這兩行，**值留空**，註解寫「只能填訪談或實測得到的數字，並在 SOURCE 註明出處」。程式碼、HTML、`.env.example` 裡都不能寫入任何預設的基準分鐘數（包括 40）。
- 由 Sandy／Felix 在訪談後提供數值和來源文字（storyboard §6 D6）。例：`MANUAL_BASELINE_MIN=35`、`MANUAL_BASELINE_SOURCE=Median of 3 plant-manager interviews, Sep 2026`。

### 4.3 版面

最大寬 1040px、寬 92vw；surface-1、radius-lg、`--shadow-modal`；遮罩 `rgba(0,0,0,0.7)`；內距 `--space-7`（矮螢幕 `--space-6`）。

**有設定基準**

```
┌──────────────────────────────────────────────────────────────────────────┐
│ INVESTIGATION SUMMARY                                                     │ 16px/600 warn 全大寫
│ Line 2 · M3 Molding                                                       │ 18px secondary
│ Cooling valve CV-2 stuck at 20% open                                      │ --fs-xl / 700
│                                                                           │
│ BEFORE  Manual investigation (baseline)                                   │ 16px/600 ＋ 18px secondary
│ 35 min  ████████████████████████████████████████████████████████████████ │ 數字 56px/700 primary；長條 --recap-before
│         Source: Median of 3 plant-manager interviews, Sep 2026            │ 16px secondary
│                                                                           │
│ AFTER   LineSleuth, this investigation (measured)                         │
│ 52 s    ██                                                                │ 數字 56px/700 success；長條 --recap-after
│         5 queries · 3 evidence cited · 1 ruled out · Work order WO-0001   │
│         Measured by the server from Investigate to conclusion.            │ 16px muted
│                                                                           │
│ Every conclusion backed by evidence.                              [Close] │
└──────────────────────────────────────────────────────────────────────────┘
```

- 每一列 grid：`grid-template-columns: 200px minmax(0, 1fr)`（S：單欄，數字在上、長條在下）。
- 長條高 `--recap-bar-h` 24px、radius 4px。兩條共用同一個刻度：100% ＝ max(Before 秒數, After 秒數)；After 最少 8px，確保看得到。如果 After 比 Before 長，照實畫，不做特別處理。

**沒有設定基準**（`manual_baseline` 為 `null`）

```
│ BEFORE  Manual investigation (baseline)                                   │
│ —       Not yet measured for this plant.                                  │ 「—」56px muted；文案 18px secondary
│                                                                           │
│ AFTER   LineSleuth, this investigation (measured)                         │
│ 52 s    5 queries · 3 evidence cited · 1 ruled out · Work order WO-0001   │ 沒有任何長條
│         Measured by the server from Investigate to conclusion.            │
```

- 沒有基準時兩邊都**不畫長條**：只有一邊的長條沒有比較意義，還會讓人以為另一邊是 0。
- offline fixture 模式：Recap 最上面加一條實心琥珀 `OFFLINE FIXTURE — not a Gemini run`（遮罩會蓋住頁面頂端的 fixture banner，所以要在這裡再標一次）。

### 4.4 工單 modal 調整

- 底部按鈕列：左 `Done`（`.btn-text`），右 `Show summary`（`.btn-outline`）。建立工單失敗時不顯示 `Show summary`（改用 `S` 開啟）。
- 矮螢幕：modal 最高 `calc(100vh − 48px)`，內容可以捲動；QR 維持 320（1280×720 下 modal 高約 490，放得下）。

---

## 5. 動畫時序

**easing token**：`--ease-standard: cubic-bezier(0.4, 0, 0.2, 1)`（移動、補間）；`--ease-decelerate: cubic-bezier(0, 0, 0.2, 1)`（進場）；`--ease-accelerate: cubic-bezier(0.4, 0, 1, 1)`（離場）。JS 補間用 easeInOutCubic 近似 standard。

**總原則**：除了脈動以外，沒有任何動畫超過 800ms。會一直循環的只有調查中的 marching ants，結論一出現就停。每一項都有 reduced-motion 的替代：直接顯示最終狀態。

| # | 觸發（t = 0） | 元素 | 動作 | 開始 | 時長 | easing | reduced-motion |
|---|---|---|---|---|---|---|---|
| M1 | 按 Investigate | 按鈕 | 換成 `Investigating…`＋spinner | 0 | 立即 | — | 相同；spinner 不轉 |
| M2 | 同上 | 產線圖 viewBox | 全景 → 焦點 | +150ms | 700ms | standard | 立即切換 |
| M3 | 同上 | 焦點機台框 | 出現＋marching ants | +150ms | 1s 循環 | linear | 靜態虛線 |
| M4 | 同上 | 非焦點車道 | opacity 1 → 0.5 | +150ms | 240ms | standard | 立即 |
| M5 | 新步驟出現 | 新卡 | opacity 0→1、translateY 8→0 | 0 | 240ms | decelerate | 立即 |
| M6 | 同上 | 前面的卡 | 完整 → 精簡，交叉淡入 | 0 | 150ms | standard | 立即 |
| M7 | 卡片 done／cached | 完整圖資料線 | 由左往右揭開（clip rect `scaleX 0→1`，transform-origin left） | +120ms | 600ms | decelerate | 直接完整 |
| M8 | 同上 | marker、關鍵點、標籤 | 淡入 | +720ms | 200ms | decelerate | 立即 |
| M9 | 同上（events） | 事件形狀 | scale 0.6→1＋淡入，每個間隔 80ms | +120ms | 200ms | decelerate | 立即 |
| M10 | 結論 root_cause | 狀態 chip | 換文字、換顏色 | 0 | 立即 | — | 相同 |
| M11 | 同上 | 證據卡 | 全部收成精簡列 | 0 | 150ms | standard | 立即 |
| M12 | 同上 | 結論卡 | opacity 0→1、translateY −8→0 | 0 | 320ms | decelerate | 立即 |
| M13 | 同上 | 地圖焦點框 | 藍虛線 → 琥珀實線（stroke 顏色漸變） | 0 | 240ms | standard | 立即 |
| M14 | 同上 | 閥門 pill、圖示、字 | 琥珀淡入 | +300ms | 200ms | standard | 立即 |
| M15 | 同上 | `ROOT CAUSE` 標籤 | 淡入 | +300ms | 240ms | decelerate | 立即 |
| M16 | 同上 | 閥門脈動環 | scale (1,1)→(1.2,2.1)、opacity 0.9→0，共 3 次 | +500ms | 1200ms × 3（約 +4.1s 結束） | decelerate | 不顯示 |
| M17 | 同上 | 精簡列的 `Cited`／`Ruled out` | 淡入 | +300ms | 150ms | standard | 立即 |
| M18 | 結論 insufficient | 灰卡 | 同 M12 | 0 | 320ms | decelerate | 立即 |
| M19 | 同上 | 焦點框 | 淡出 | 0 | 150ms | standard | 立即 |
| M20 | 同上 | viewBox | 焦點 → 全景；車道取消淡化 | +150ms | 700ms | standard | 立即 |
| M21 | 同上 | 車道灰虛線＋徽章 | 出現＋徽章淡入 | +850ms | 240ms | decelerate | 立即 |
| M22 | Show summary／`S` | 遮罩 | opacity 0→1 | 0 | 200ms | linear | 立即 |
| M23 | 同上 | Recap 卡 | opacity 0→1、scale 0.98→1 | 0 | 240ms | decelerate | 立即 |
| M24 | 同上 | Before 長條 | 寬度 0→最終 | +200ms | 800ms | decelerate | 直接最終寬度 |
| M25 | 同上 | After 長條＋數字 | 寬度 0→最終；數字淡入 | +1000ms | 400ms | decelerate | 立即 |
| M26 | Close／Esc | Recap | 淡出 | 0 | 150ms | accelerate | 立即 |
| M27 | Reset／切換情境 | 地圖全部狀態 | 清除；viewBox 回全景 | 0 | 400ms | standard | 立即 |

- M7 只在卡片**第一次**畫圖時播放；resize 重畫、精簡／完整切換時不重播。
- M13–M16 寫在 SVG 的 CSS delay 裡（§2.2），JS 只在 t=0 換 class。
- 長條成長用 `transform: scaleX()`（transform-origin left），不要動畫 `width`。
- 旁白節奏：M13→M15 大約 0.5 秒完成，剛好在簡報者說完「Root cause: cooling valve CV-2 stuck」之前亮起來。

---

## 6. CSS token 增修

直接加進 `app.css` 的 `:root`（v1 token 全部保留）。媒體查詢順序：L → M → S → 矮螢幕 → 手機（v1 的 `max-width: 599px`）→ reduced-motion。

```css
:root {
  /* ---- v2 版面 ---- */
  --topbar-h: 72px;
  --bottombar-h: 48px;
  --gutter: var(--space-6);
  --gap: var(--space-5);
  --main-pad-y: var(--space-5);
  --panel-pad: var(--space-5);
  --cols: minmax(0, 7fr) minmax(0, 5fr);
  --btn-primary-h: 64px;
  --btn-primary-minw: 240px;
  --rows-max-h: 280px;
  --compact-h: 60px;
  --step-col: 40px;

  /* ---- v2 證據小圖 ---- */
  --chart-h: 96px;
  --chart-mini-w: 120px;
  --chart-mini-h: 32px;
  --chart-series: var(--color-info);            /* #5AA9FF 正常段 */
  --chart-series-abnormal: var(--color-warn);   /* #F5A524 越限／偏離之後 */
  --chart-limit: #C4C9D2;                       /* SOP 上下限虛線與標籤 */
  --chart-baseline: #A3AAB8;                    /* 基準點線與標籤 */
  --chart-command: #C4C9D2;                     /* 指令開度虛線 */
  --chart-band: rgba(163, 170, 184, 0.12);      /* 正常帶／基準帶（裝飾） */
  --chart-gap-fill: rgba(245, 165, 36, 0.22);   /* 指令與實際的差距 */
  --chart-marker: var(--color-warn);            /* since 標記 */
  --chart-missing: #8A93A3;                     /* 缺值斜線與 No data */
  --chart-axis: #4A5263;                        /* events 軸線（裝飾） */
  --chart-event-critical: var(--color-danger);
  --chart-event-warning: var(--color-warn);
  --chart-event-notable: var(--color-warn);
  --chart-event-info: #A3AAB8;
  --chart-halo: var(--color-surface-2);         /* 圖內文字描邊＝卡片底色 */

  /* ---- v2 根因（產線圖）與 Recap ---- */
  --rc-accent: var(--color-warn);
  --rc-accent-bg: rgba(245, 165, 36, 0.22);
  --rc-tag-text: var(--color-text-on-accent);
  --recap-before: #6B7280;
  --recap-after: var(--color-success);
  --recap-bar-h: 24px;

  /* ---- v2 動態 ---- */
  --ease-standard: cubic-bezier(0.4, 0, 0.2, 1);
  --ease-decelerate: cubic-bezier(0, 0, 0.2, 1);
  --ease-accelerate: cubic-bezier(0.4, 0, 1, 1);
  --motion-enter: 320ms;
  --motion-draw: 600ms;
  --motion-zoom: 700ms;
  --motion-bar: 800ms;
  --motion-pulse: 1200ms;
}

/* L：1280–1599 */
@media (max-width: 1599.98px) {
  :root {
    --gutter: var(--space-5); --gap: var(--space-4);
    --cols: minmax(0, 1fr) clamp(440px, 38vw, 560px);
    --fs-display: 44px; --fs-2xl: 30px; --fs-xl: 24px; --fs-lg: 20px;
    --btn-primary-h: 56px; --btn-primary-minw: 232px;
    --chart-h: 72px; --chart-mini-w: 96px; --chart-mini-h: 28px;
    --compact-h: 56px; --step-col: 36px;
  }
}
/* M：1024–1279 */
@media (max-width: 1279.98px) {
  :root { --gutter: var(--space-4); --cols: minmax(0, 1fr) 420px; --fs-display: 40px; --fs-2xl: 28px; --btn-primary-minw: 220px; }
}
/* S：<1024，單欄、整頁捲動 */
@media (max-width: 1023.98px) {
  :root { --cols: minmax(0, 1fr); }
  .app { height: auto; min-height: 100dvh; grid-template-rows: auto auto 1fr auto; }
  .topbar { flex-wrap: wrap; row-gap: var(--space-2); padding-block: var(--space-2); }
}
/* 矮螢幕（投影機、視窗化瀏覽器） */
@media (min-width: 1024px) and (max-height: 959.98px) {
  :root { --topbar-h: 56px; --bottombar-h: 40px; --main-pad-y: var(--space-4); --panel-pad: var(--space-4); --rows-max-h: 200px; }
}
@media (prefers-reduced-motion: reduce) {
  :root { --motion-fast: 0ms; --motion-base: 0ms; --motion-enter: 0ms; --motion-draw: 0ms;
          --motion-zoom: 0ms; --motion-bar: 0ms; --motion-pulse: 0ms; }
}
```

使用方式（對應現行 `app.css`）：`.app` 的 grid rows 改用 `var(--topbar-h)`、`var(--bottombar-h)`；`.main` 改用 `grid-template-columns: var(--cols); gap: var(--gap); padding: var(--main-pad-y) var(--gutter);`；`.panel` padding 改用 `var(--panel-pad)`；`.btn-primary` 用 `--btn-primary-h`、`--btn-primary-minw`；`.rows-scroll` 用 `--rows-max-h`；`.card-row` 的第一欄用 `--step-col`。

另外需要一個 `.sr-only`（視覺隱藏、讀屏可讀），給 §2.6 的 live region 用。

---

## 7. 可及性

### 7.1 新增色彩組合的對比（WCAG 2.1 AA）

| 前景 | 背景 | 對比（計算值） | 用途 | 結果 |
|---|---|---|---|---|
| `--chart-series` #5AA9FF | surface-2 #1F232C | ≈ 6.4 | 資料線（非文字 ≥3） | 通過 |
| `--chart-series-abnormal` #F5A524 | surface-2 | ≈ 7.7 | 異常段、marker 標籤 | 通過 |
| `--chart-limit` #C4C9D2 | surface-2 | ≈ 9.5 | SOP 線＋16px 標籤 | 通過 |
| `--chart-baseline` #A3AAB8 | surface-2 | ≈ 6.8 | 基準線＋標籤 | 通過 |
| `--chart-missing` #8A93A3 | surface-2 | ≈ 5.1 | `No data` 16px | 通過 |
| `--chart-event-critical` #F2555A | surface-2 | ≈ 4.7 | 菱形＋標籤 | 通過 |
| `--rc-tag-text` #0F1115 | warn #F5A524 | ≈ 9.3 | `ROOT CAUSE` 標籤 | 通過 |
| warn 閥門字 | rc-accent-bg 疊在車道底（≈ #483921） | ≈ 5.5 | `CV-2 valve` 20px | 通過 |
| grey-accent #B8BEC9 | grey-card #23262D | ≈ 8.1 | 車道徽章 | 通過 |
| grey-border #6B7280 | 車道底 #171A21 | ≈ 3.6 | 灰色虛線外框（非文字） | 通過 |
| `--recap-before` #6B7280 | surface-1 #171A21 | ≈ 3.6 | Before 長條（非文字） | 通過 |
| success #3DD68C | surface-1 | ≈ 8.5 | After 數字與長條 | 通過 |
| 淡化車道（opacity 0.5） | — | — | 背景情境 | 豁免（資訊同時寫在 banner 和 `<desc>`） |

`--chart-band`、`--chart-gap-fill`、`--chart-axis` 是裝飾，不承載資訊，不需要 3:1。

### 7.2 不只靠顏色

| 資訊 | 顏色之外的訊號 |
|---|---|
| 根因 vs 停線 | `ROOT CAUSE` 文字；琥珀**實線**框 vs 紅色粗外框＋`STOPPED` 文字 |
| Low 信心 | 標籤外框樣式（不是實心）、不脈動；結論卡上的文字提示 |
| 灰卡車道 | **虛線**外框＋`No root cause found` |
| 圖上的異常段 | `since HH:MM` 標記線和文字；關鍵點圓點 |
| 事件嚴重度 | 形狀（◆ ▲ ■ ○）＋文字標籤 |
| 指令 vs 實際 | 虛線 vs 實線＋`Commanded`／`Actual` 文字 |
| Before／After | `BEFORE`／`AFTER` 文字＋數值 |

### 7.3 讀屏、鍵盤、動態

- 完整圖：`<svg role="img" aria-label="…">`，內容直接組卡片文字：`{title}: {key_value} {key_detail}. Chart of {n} readings, {x_start}–{x_end}.`；events：`{title}: {所有 label，用逗號串起來 或 empty_label}.`。這樣不會和卡片說法不一致。迷你圖一律 `aria-hidden="true"`。
- `#status-chip` 加 `role="status"`，結論和灰卡出現時會被讀出來；地圖的變化用 §2.6 的 `#plant-live` 念一句。
- Recap：`role="dialog" aria-modal="true" aria-labelledby`；開啟時焦點放在 `Close`；焦點鎖在對話框內；Esc 關閉；關閉後焦點回到觸發它的元素。
- Tab 順序：Investigate → 結論卡（引用 chip → `Recommended actions` disclosure → Create work order）→ 證據精簡列（依步驟）→ 情境切換 → Reset。
- 快捷鍵：沿用 `R`／`1`／`2`，新增 `S`（Summary）。焦點在 select 上或有按 Ctrl／Meta／Alt 時不觸發（沿用現有判斷）。
- 最小字：大螢幕 16px。例外只有兩個：原始列表格 14px（沿用 v1），以及全景時產線圖的次要標籤（機台編號、閥門名稱，1280 寬約 12px），拉近後都在 16px 以上。
- S 斷點的點擊區 ≥ 44×44px。
- `prefers-reduced-motion`：CSS 變數歸零；JS 的 `tweenViewBox`、畫線揭開、長條成長都要先檢查 `reduceMotion()`。

---

## 8. 驗收清單（共 52 條）

測試條件：Chrome 最新版、縮放 100%；「F11」代表全螢幕。視窗尺寸用 DevTools 的 Device Toolbar 設定。

> **Eddie 實作標記（2026-09-24）**：`[x]`＝程式已實作；`[ ]`＝未做或量測未達標，後面寫原因。標「待目視」的要主持人在真的瀏覽器確認。「headless」＝我用 headless Chrome（無 fixture 黃條，模擬 Gemini 模式）量版面，不等於目視驗收。
> 規格外的改動：① 修掉 v1 的版面 bug：Gemini 模式下 fixture 黃條隱藏時，`.app` 的 grid 列會整個錯位（面板高度變 0），改成明確指定列；② 圖例移到產線圖上方（照 §3.2 示意）；③ 根因與 Ruled out 沒有做「最多 2 行」截斷，避免把模型文字藏起來，太長時 `#result` 自己捲動；④ 結論出現的那一刻伺服器就停表（`inv.finished`），Recap 的 After 不含收尾時間。

**A. 版面與斷點**
- [ ] A1　1920×1080（F11）：整頁沒有捲軸；主線結論出現後，結論卡和 5 列精簡證據全部看得到，面板內不需要捲動。 — **Eddie**：未完全達標：headless 量測（無 fixture 黃條）整頁不捲動、結論卡完整，但精簡列只看得到 3／5 列。完整版結論卡實際約 536px（40px 根因在 667px 寬折成 2 行、處置清單 5 行），比 §3.5 估的 420 高。要達標需 Dana 決定：例如 compact 版改成 `max-height: 1199.98px` 以下都用，或接受 3 列
- [x] A2　1366×768（F11）：整頁沒有捲軸；結論卡（含 `Create work order`）不捲動就完整可見；證據列至少看得到 2 列，其餘在面板內捲動。 — **Eddie**：headless：不捲動、`Create work order` 完整可見、證據列 2 列。待目視
- [x] A3　1280×720（F11）：同 A2。 — **Eddie**：headless：同 A2（2 列）。為了達標，矮螢幕時面板標題改 20px 讓表頭維持一行、`Evidence`／`Ruled out` 標籤改成同行（§3.6 示意）。待目視
- [x] A4　1280×720 非全螢幕（可視高度約 600）：整頁沒有捲軸，`Create work order` 不捲動就看得到。 — **Eddie**：headless 1280×600：不捲動、`Create work order` 可見；證據列只剩標題（§3.5 估約 1 列）。矮螢幕時 `#result` 上限改為 `calc(100% - 44px)`，否則 72% 會把按鈕切掉。待目視
- [x] A5　758px 寬：單欄堆疊；`Investigate` 完整可見可點（DevTools console 執行 `document.elementFromPoint(按鈕中心點)` 回傳的是按鈕本身或它的子元素）；沒有橫向捲軸。 — **Eddie**：headless 758×900：單欄、`elementFromPoint` 命中按鈕、無橫向捲軸。待目視
- [x] A6　寬度 1600、1599、1280、1279、1024、1023、758、599、360 各截一張圖：沒有任何元素重疊或溢出容器，`Downtime` 數字完整顯示在自己的區域內。 — **Eddie**：headless 抽查 1920／1600／1366／1280／1100／1024／758／390 無橫向溢出；1599、1279、1023、599、360 未截圖。待目視
- [x] A7　各斷點的 token 值（計時器字級、面板寬、按鈕高、圖高）符合 §3.1 表格。 — **Eddie**：headless 量到：計時器 64／44／40px、按鈕高 64／56、完整圖高 96／72
- [x] A8　大螢幕文字 ≥16px（原始列表格、全景地圖次要標籤除外）；DevTools 抽查 5 處。 — **Eddie**：待目視
- [ ] A9　1280 寬全景：機台名稱和 `RUNNING`／`STOPPED` 字實際高度 ≥16px。 — **Eddie**：未達標（估算）：1280 全景縮放約 0.61 倍，機台名 28px≈17px 可以，但 `RUNNING`／`STOPPED` 26px≈15.8px 略低於 16。字級在 Dana 的 SVG 裡，我沒改；建議狀態字 26→27

**B. 產線圖**
- [x] B1　app 使用的是 `line-layout-v2.svg`（viewBox `0 0 1200 600`），v1 的 ID 都還能用（現有測試全部通過）。 — **Eddie**：已複製成 `app/static/line-layout.svg`；pytest 全過
- [x] B2　按 Investigate 後 1 秒內鏡頭開始拉近，大約 0.7 秒完成；主線對準 L2-M3，正常情境對準 L1-M3；拉近過程中 Plant 區高度不變。 — **Eddie**：+150ms 開始、700ms 補間；正常情境對準 L1-M3。待目視
- [x] B3　拉近後（1280 寬），`CV-2 valve` 和 `L2-M3` 實際字高 ≥16px；非焦點車道變淡。 — **Eddie**：拉近後縮放約 0.95，閥門字約 19px。待目視
- [x] B4　主線結論出現後 0.6 秒內：L2-M3 框變成琥珀實線，CV-2 變成琥珀 pill，出現 `ROOT CAUSE`；脈動剛好 3 次、大約 4 秒後停止，靜態高亮保留。 — **Eddie**：JS 在 t=0 換 class，時序用 SVG 內的 CSS。待目視
- [x] B5　L2-M3 本體仍然是紅色 `STOPPED`，Line 2 狀態文字仍然是 `Stopped`。 — **Eddie**：headless 確認
- [x] B6　灰卡：鏡頭拉回全景；大約 0.85 秒後 Line 1 外框變灰色虛線，出現 `No root cause found`；沒有任何機台變色，沒有 `ROOT CAUSE`，沒有脈動。 — **Eddie**：headless：L1 加 `is-inconclusive`、沒有任何 `ROOT CAUSE`。待目視
- [x] B7　Reset、切換情境（含鍵盤 `R`／`1`／`2`）：高亮、鏡頭、淡化、灰框全部清除，回到全景。 — **Eddie**：headless：Reset 後 viewBox 回 `0 0 1200 600`、所有標記清除
- [x] B8　調查失敗或被取消：焦點框移除、回到全景，不出現任何根因標記。 — **Eddie**：headless 看過失敗狀態（速率上限）回全景、無標記。待目視
- [x] B9　Low 信心（用回歸情境或 mock）：`ROOT CAUSE` 是外框樣式，閥門不脈動。 — **Eddie**：已接 `is-low-confidence`；fixture 沒有 Low 情境，需用 mock 或回歸情境目視
- [x] B10　結論出現時，`<desc>` 已更新，`#plant-live` 念出一句話（Windows 用 NVDA 或 Narrator 抽查一次）。 — **Eddie**：已更新 `<desc>` 並寫入 `#plant-live`（storyboard §5.9 文案）；讀屏軟體未測

**C. 證據小圖**
- [x] C1　主線 5 張卡的圖種正確：#1 events（02:54 ▲、03:00 ◆，形狀不同）、#2 series_limit（`SOP limit 205 °C` 虛線＋`since` 標記＋最高點圓點）、#3 series_baseline（`Baseline …` 線＋`since 02:41`＋最新值圓點）、#4 command_vs_actual（`Commanded 80%` 虛線、`Actual` 實線、差距填色）、#5 events（02:30 ○ `Handover 02:30`）。 — **Eddie**：headless 逐張截圖確認五張圖種與標籤。待目視
- [x] C2　圖上出現的數字，都能在該卡的原始列或卡片文字裡找到（Quinn 抽查 #2、#3、#4）。 — **Eddie**：所有點都是原始列值＋row_id（pytest 驗證）；Quinn 抽查
- [x] C3　關鍵點圓點的時間和值，就是 `View source rows` 高亮的那一列。 — **Eddie**：pytest：`key_point.row_id` 在 `highlight_row_ids` 裡、值等於卡片數字
- [x] C4　後端測試：`chart` 裡的每個 row_id 都在 rows 裡；`key_point.row_id` 在 `highlight_row_ids` 裡；`limit.value` 等於 SOP 上下限。 — **Eddie**：`tests/test_queries.py` 新增 6 條
- [x] C5　正常情境 4 張卡：線全部是藍色、沒有 `since` 標記；#1 顯示軸線加 `No alarms`。 — **Eddie**：待目視
- [x] C6　缺值（N02 情境或測試資料）：缺的時段斷線、有斜線底紋和 `No data`，沒有把兩端連起來。 — **Eddie**：已實作斷線＋斜線＋`No data`；後端 pytest 驗證 N02 缺值不補。N02 不是 UI 可選情境，需 mock 目視
- [x] C7　整段沒有資料（key_value `No data`）：圖區是同高度的虛線框加 `No data`。 — **Eddie**：同 C6
- [x] C8　running 時是同高度 skeleton；error 不畫圖；cached 照常畫圖而且保留 `Cached` chip；`list_sensors` 卡沒有圖也沒有空白區。 — **Eddie**：待目視
- [x] C9　拖動視窗大小，停下 150ms 內完整圖重畫，文字和圓點不變形。 — **Eddie**：headless：改視窗寬後圖寬 381→488，和容器一致
- [x] C10　沒有引入任何圖表函式庫（`requirements*.txt`、HTML 的 `<script>` 都沒有新增）；圖是內嵌 SVG。 — **Eddie**：沒有新增任何套件或 `<script>`
- [x] C11　交班紀錄的原文不會出現在圖的標籤裡（用 R07 的 injection 字串驗證）。 — **Eddie**：標籤是固定模板；pytest 用 R07 驗證

**D. 面板與卡片密度**
- [x] D1　調查中：新卡出現時，前面沒被手動展開的卡都收成精簡列，最新一張完整顯示。 — **Eddie**：待目視
- [x] D2　精簡列可以用滑鼠、Enter、Space 展開和收合，`aria-expanded` 會跟著變。 — **Eddie**：原生 `<button>`，Enter／Space 可用，`aria-expanded` 同步。待目視
- [x] D3　結論出現：結論卡在面板頂端，捲動證據列時結論卡不動；證據列全部收合（原始列展開中的那張除外）。 — **Eddie**：headless 確認
- [x] D4　點引用 chip `#3`：捲到 #3、展開、閃一次 info 外框。 — **Eddie**：headless 確認
- [x] D5　高度 ≤959：結論卡是 compact 版，`Recommended actions (3)` 可以展開，`Create work order` 和它在同一行。 — **Eddie**：headless 確認；1280 寬時 `Recommended actions (3)` 按鈕文字會折成 2 行。待目視
- [x] D6　灰卡同樣在頂端；`Checked` 清單和下面的證據列一一對應。 — **Eddie**：待目視

**E. Before／After 收尾**
- [x] E1　工單 modal 有 `Done` 和 `Show summary`；按 `Show summary` 或 `S` 會開 Recap；Esc／`Close` 關閉，焦點回到原本的位置。 — **Eddie**：headless：Esc 關閉後焦點回到 `Create work order`
- [x] E2　Recap 的 After 秒數和面板最後的 `Elapsed` 是同一個整數秒。 — **Eddie**：headless：`2 s` 與 `Elapsed 00:02` 一致（同一個四捨五入函式）
- [x] E3　沒設 `MANUAL_BASELINE_MIN` 或 `MANUAL_BASELINE_SOURCE`：Before 顯示 `—` 和 `Not yet measured for this plant.`，沒有長條，畫面上任何地方都沒有人工基準的分鐘數（例如「40 min」）。 — **Eddie**：headless 確認；沒有長條
- [x] E4　兩個都有設定（例：35／來源文字）：顯示 `35 min` 和 `Source: …`，長條比例正確，After 長條最短 8px。 — **Eddie**：headless 用測試用環境變數確認：`35 min`、`Source: …`、After 長條 8px
- [x] E5　只設 MIN、沒設 SOURCE，或 MIN 超出 1–480：`/api/config` 回 `manual_baseline: null`，畫面和 E3 一樣。 — **Eddie**：pytest 參數化驗證
- [x] E6　在 `app/` 全文搜尋 `40 min`、`40 minutes`、`90 sec`：找不到任何寫死的字串。 — **Eddie**：pytest `test_no_hard_coded_manual_baseline_in_app`
- [x] E7　offline fixture 模式：Recap 頂端有 `OFFLINE FIXTURE — not a Gemini run`；有 cached 步驟時，明細後面有 `· {k} cached`。 — **Eddie**：fixture 標示 headless 確認；`· {k} cached` 已實作，未實際觸發
- [x] E8　灰卡、失敗、調查中：沒有 `Show summary`，按 `S` 沒反應。 — **Eddie**：待目視

**F. 動畫與可及性**
- [x] F1　DevTools → Rendering → 模擬 `prefers-reduced-motion: reduce`：沒有鏡頭補間、沒有畫線揭開、沒有脈動、沒有長條成長、沒有 marching ants，最終狀態直接出現。 — **Eddie**：CSS 變數歸零、JS 補間／畫線／長條都先檢查 `reduceMotion()`。待目視
- [x] F2　主線錄一段畫面逐格檢查：時序符合 §5 表格（誤差 ±100ms 以內）。 — **Eddie**：已照 §5 表實作，需錄影逐格驗。差異：M19 焦點框淡出沒有做（SVG 的 `.focus` 是直接隱藏）；M6 只做新顯示那一側的淡入
- [x] F3　DevTools 模擬 achromatopsia（全色盲）截圖：仍然分得出根因、停線、灰卡、事件嚴重度。 — **Eddie**：待目視
- [x] F4　用 WebAIM 抽查 §7.1 表格中的 3 組對比，都符合。 — **Eddie**：色碼照 §6 原樣複製；待 WebAIM 抽查
- [x] F5　每張完整卡的圖有 `role="img"` 和 aria-label，內容就是卡片標題＋關鍵值＋說明；迷你圖是 `aria-hidden`。 — **Eddie**：headless 確認 aria-label 與卡片文字一致；迷你圖 `aria-hidden`
- [x] F6　Recap 是 `role="dialog"`＋`aria-modal`，焦點鎖在對話框內。 — **Eddie**：待目視
- [x] F7　Tab 順序符合 §7.3。 — **Eddie**：照 DOM 順序。待目視

**G. 回歸**
- [x] G1　手機工單頁（390×844）外觀和 v1 一樣；`python -m pytest` 全部通過。 — **Eddie**：pytest 110 passed、1 skipped；手機工單頁 CSS 沒動，390×844 待目視

---

## 9. 建議實作順序

先修主持人實測的問題（1→3），做完隨時可以 demo；接著做小圖（4→5）；再做收尾（6）；最後才加動畫（7→8）。

| 順序 | 項目 | 誰 | 估時 | 依賴 | 時間不夠時 |
|---|---|---|---|---|---|
| 1 | 斷點 token、Banner grid、矮螢幕修飾、S 單欄（§3.1–3.3、§6） | Eddie | 3h | — | 不能砍 |
| 2 | 換上 SVG v2，接根因／灰卡 class、`RC_TARGET`、`<desc>`／live region（先不做拉近） | Eddie | 1.5h | 1 | 不能砍 |
| 3 | 面板：結論置頂、精簡列與收合規則、結論 compact 版（§1.8、§3.4、§3.6） | Eddie | 3h | 1 | 不能砍 |
| 4 | 後端 `card.chart` 與三條測試（§1.3） | Eddie | 3h | — | 不能砍（沒有資料就沒有圖） |
| 5 | 前端小圖：四種圖＋迷你圖＋空值／缺值狀態（§1.4–1.7） | Eddie | 4h | 4 | 可以降級：先做 `series_limit` 和 `events`；另外兩種先用 `series_limit` 的畫法（不畫指令線和基準線） |
| 6 | Recap、`MANUAL_BASELINE_*` 環境變數、`/api/config`、modal 按鈕（§4） | Eddie | 2h | — | 不能砍（老闆指定） |
| 7 | 鏡頭拉近（§2.4） | Eddie | 1h | 2 | 可以砍：v2 字級已經放大，全景也看得清楚 |
| 8 | 動畫 M5–M9、M22–M26 與 reduced-motion 檢查 | Eddie | 1.5h | 3、5、6 | 可以砍：全部改成直接出現（SVG 內的 M13–M16 已經寫好，不用另外做） |
| 9 | 驗收：Quinn 跑 §8；Dana 在 1280×720 和 1366×768 投影機實機看一次 | Quinn、Dana | 2h | 全部 | — |

合計大約 21 小時，其中不能砍的部分大約 15.5 小時。建議在 10/13（Agent 和三個畫面串通）之前完成 1–3 和 6，10/16 部署前完成 4–5。

---

## 10. 對其他文件的影響

**我已經更新**
- `docs/design/ui-spec.md`：開頭加上 v2 說明；§3.2、§3.3、§3.4、§3.5、§3.6、§3.7、§3.9、§4.1、§5、§6 在需要的地方標註「→ v2」，並改正和 v2 衝突的句子（`is-fault`、sparkline 選配、<1100 不支援、產線圖不做動畫）；新增 §3.10a Recap 指引。
- `docs/design/storyboard.md`：格 ②③④⑤、灰卡加演 C 的畫面描述；格 ⑤ 的收尾改用 Recap（大螢幕和錄影都不再用寫死的「40 min → 90 sec」字卡）；§5 新增 v2 文案（§5.8 圖、§5.9 產線圖、§5.10 Recap）；§6 新增 D6、D7。
- 新檔 `docs/design/line-layout-v2.svg`。

**需要其他人更新**（我沒有動）
- Paula：PRD F1 驗收條件「不做動畫」→ 改成「除了調查鏡頭拉近和根因脈動以外不做動畫，reduced-motion 時全部關閉」（storyboard D7）。
- Sandy：pitch 投影片 slide 11 和 pitch-script 的結尾，要和 Recap 的原則一致：app 畫面上只出現實測秒數，人工基準要附來源；投影片沿用 `*pending validation`。
- Sandy／Felix：訪談後提供 `MANUAL_BASELINE_MIN` 和 `MANUAL_BASELINE_SOURCE`（storyboard D6）。
- Eddie：`.env.example`、`docs/engineering/deploy.md` 補上兩個環境變數的說明。
- Quinn：把 §8 併進 `docs/qa/test-plan.md`。
