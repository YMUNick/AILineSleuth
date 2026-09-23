# UI 規格：LineSleuth（MVP）

- 建立：2026-09-24，Dana（設計）
- 依據：`docs/prd.md`（F1–F8）、`docs/meetings/2026-09-24-駭客松主題方向.md`
- 搭配：`docs/design/storyboard.md`（分鏡與文案定稿）、`docs/design/line-layout.svg`（產線圖）
- 沒有 Figma，這份就是設計稿。工程師照 token 與尺寸實作即可；數字寫死在這裡，不要自己調。
- 只有一套深色主題（大螢幕與手機共用），不做淺色模式。

## 0. 設計原則（衝突時照這個順序取捨）

1. **三公尺外看得懂**：評審看的是投影或大螢幕。大螢幕上最小字 16px，正文 18px 以上。
2. **顏色不是唯一訊號**：每個狀態都同時有「顏色＋文字」（例如紅色機台一定寫 `STOPPED`），色弱與投影偏色也看得懂。
3. **一個畫面一個主動作**：Investigate 是唯一的主按鈕；Create work order 只在結論出現後才出現。
4. **誠實**：cached、scenario time、demo scenario 都要明白標示，不假裝即時或真實。
5. **灰卡是刻意的結果，不是錯誤**：灰卡文字全亮度、標題清楚，不能做成像 disabled 的淡灰。

## 1. 設計 Token（CSS 變數）

直接貼進全域 CSS。所有元件只准引用變數，不寫死色碼。

```css
:root {
  /* ---- 底色與表面 ---- */
  --color-bg:            #0F1115; /* 頁面底 */
  --color-surface-1:     #171A21; /* 面板 */
  --color-surface-2:     #1F232C; /* 卡片 */
  --color-surface-3:     #282D38; /* 卡片 hover／展開的原始列表頭 */
  --color-border:        #2E3440; /* 一般分隔線（裝飾用，不承載資訊） */
  --color-border-strong: #4A5263; /* 需要被看見的邊框（輸入、卡片外框） */

  /* ---- 文字 ---- */
  --color-text-primary:   #E8EAED;
  --color-text-secondary: #A3AAB8;
  --color-text-muted:     #8A93A3; /* 最低可用的文字色，不能再更淡 */
  --color-text-on-accent: #0F1115; /* 琥珀／綠／藍實心底上的文字 */

  /* ---- 語意色 ---- */
  --color-warn:        #F5A524; /* 琥珀：警示、主按鈕、結論強調 */
  --color-warn-bg:     rgba(245, 165, 36, 0.14);
  --color-danger:      #F2555A; /* 停線 */
  --color-danger-bg:   rgba(242, 85, 90, 0.16);
  --color-success:     #3DD68C; /* 正常運轉、查詢完成 */
  --color-success-bg:  rgba(61, 214, 140, 0.14);
  --color-info:        #5AA9FF; /* 調查中、引用、連結、信心標籤 */
  --color-info-bg:     rgba(90, 169, 255, 0.14);

  /* ---- 灰卡（Insufficient evidence） ---- */
  --color-grey-card:   #23262D;
  --color-grey-border: #6B7280; /* 虛線外框 */
  --color-grey-text:   #C4C9D2;
  --color-grey-accent: #B8BEC9; /* 標題與圖示 */

  /* ---- 機台狀態（產線 SVG 用，也可給 legend） ---- */
  --machine-body:        #1F232C;
  --machine-stroke:      #4A5263;
  --machine-normal:      var(--color-success);
  --machine-warn:        var(--color-warn);
  --machine-stopped:     var(--color-danger);
  --machine-stopped-bg:  #2A1618;
  --machine-idle:        #6B7280;
  --machine-focus:       var(--color-info);

  /* ---- 字體 ---- */
  --font-sans: "Inter", system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  --font-mono: ui-monospace, "SFMono-Regular", Consolas, monospace; /* 只用在函式名稱、SQL 欄位名 */

  /* 字級（大螢幕） */
  --fs-xs:      14px; /* 只給大螢幕以外（手機 meta）或原始列表格 */
  --fs-sm:      16px; /* meta、函式名稱、時間範圍 */
  --fs-md:      18px; /* 正文 */
  --fs-lg:      22px; /* 卡片標題 */
  --fs-xl:      28px; /* 證據關鍵數值、面板標題 */
  --fs-2xl:     40px; /* 結論根因 */
  --fs-display: 64px; /* 停線計時器 */

  --fw-regular: 400;
  --fw-medium:  500;
  --fw-semibold: 600;
  --fw-bold:    700;

  --lh-tight: 1.2;
  --lh-normal: 1.5;

  /* ---- 間距（4px 基準） ---- */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 24px;
  --space-6: 32px;
  --space-7: 48px;
  --space-8: 64px;

  /* ---- 圓角 ---- */
  --radius-sm:   6px;  /* tag、chip */
  --radius-md:   10px; /* 卡片、按鈕 */
  --radius-lg:   16px; /* 面板、modal */
  --radius-pill: 999px;

  /* ---- 陰影與動態 ---- */
  --shadow-modal: 0 24px 64px rgba(0, 0, 0, 0.6);
  --focus-ring: 0 0 0 3px var(--color-info);
  --motion-fast: 150ms;
  --motion-base: 240ms;
}

/* 數字一律等寬，計時器與數值不會跳動 */
body { font-family: var(--font-sans); font-feature-settings: "tnum" 1, "cv11" 1; background: var(--color-bg); color: var(--color-text-primary); }

@media (prefers-reduced-motion: reduce) {
  :root { --motion-fast: 0ms; --motion-base: 0ms; }
}
```

手機工單頁覆寫字級（見 §4）：

```css
@media (max-width: 599px) {
  :root {
    --fs-sm: 14px; --fs-md: 16px; --fs-lg: 18px;
    --fs-xl: 22px; --fs-2xl: 26px;
  }
}
```

Inter 用 Google Fonts 載入 400/500/600/700 四個字重，`display=swap`。

## 2. 對比檢查（WCAG 2.1 AA）

規則：一般文字 ≥ 4.5:1；大字（≥ 24px，或 ≥ 18.66px 粗體）≥ 3:1；非文字元件（機台外框、狀態燈、按鈕邊界、focus ring）≥ 3:1。以下為計算值（四捨五入），實作後用 DevTools 或 WebAIM 抽查。

| 前景 | 背景 | 對比 | 用途 | 結果 |
|---|---|---|---|---|
| text-primary `#E8EAED` | bg `#0F1115` | ≈ 15.6 | 正文 | AA/AAA |
| text-primary | surface-2 `#1F232C` | ≈ 13.0 | 卡片正文 | AA/AAA |
| text-secondary `#A3AAB8` | surface-2 | ≈ 6.8 | 次要文字 | AA |
| text-muted `#8A93A3` | surface-2 | ≈ 5.1 | meta（最淡） | AA |
| text-secondary | surface-3 `#282D38` | ≈ 5.9 | 原始列表頭 | AA |
| text-muted | surface-3 | ≈ 4.4 | — | **不合格：surface-3 上禁用 muted** |
| warn `#F5A524` | bg | ≈ 9.3 | 琥珀文字、標籤 | AA |
| text-on-accent `#0F1115` | warn `#F5A524` | ≈ 9.3 | Investigate 按鈕字 | AA |
| danger `#F2555A` | bg | ≈ 5.6 | STOPPED 文字 | AA |
| danger | surface-2 | ≈ 4.7 | 卡片內紅字 | AA |
| danger | machine-stopped-bg `#2A1618` | ≈ 5.1 | 停線機台內文字 | AA |
| success `#3DD68C` | surface-2 | ≈ 8.4 | RUNNING、完成勾 | AA |
| info `#5AA9FF` | surface-2 | ≈ 6.4 | 引用 chip、連結 | AA |
| grey-text `#C4C9D2` | grey-card `#23262D` | ≈ 9.1 | 灰卡正文 | AA |
| grey-accent `#B8BEC9` | grey-card | ≈ 8.1 | 灰卡標題 | AA |
| grey-border `#6B7280` | grey-card | ≈ 3.1 | 灰卡虛線框（非文字） | ≥3:1 |
| border-strong `#4A5263` | bg | ≈ 2.3 | 裝飾邊框 | 不承載資訊，所以不需 3:1 |

注意：
- `--color-border` 與 `--color-border-strong` 都**不能**當唯一的狀態訊號。
- 半透明底（`*-bg`）上只能放 text-primary 或同語意色實色文字；已在 surface-2 上疊算過仍 ≥ 4.5。
- QR code 一律黑碼白底（見 §3.9），不套深色主題，否則手機掃不到。

## 3. 元件規格

### 3.1 頂部列 TopBar（高 72px）

- 背景 surface-1，下緣 1px border。左右 padding `--space-6`。
- 左：wordmark `LineSleuth`（22px / 700），右側小字 `Demo Plant · Night shift`（16px / text-secondary）。
- 中：情境時鐘 `Scenario time 03:00:14`（標籤 16px muted；時間 28px / 600 tnum）。一定要寫「Scenario time」，不假裝是現在時間。
- 右：`Demo scenario` 小 chip（info-bg 底、info 字，radius-sm）。

### 3.2 產線 SVG 與機台狀態（F1）

- 檔案：`docs/design/line-layout.svg`。**必須 inline 進 HTML**（不能用 `<img>`），JS 才改得到 class。
- 每台機台是 `<g id="L{線}-M{機}" class="machine is-normal">`，例：`L2-M3`。
- 每條線是 `<g id="L{線}" class="lane">`，停線時加 `is-stopped`（線框變紅、狀態字變紅粗體）；線狀態文字 `id="L{線}-status"`。
- 每台機台狀態文字 `id="L{線}-M{機}-state"`，JS 改 class 時要**同時**改這段文字。
- 各線 M3 有冷卻閥標記 `id="L{線}-M3-CV{線}"`（例 `L2-M3-CV2`），class `valve`；結論指到它時加 `is-fault`。

| class | 外框 | 狀態燈 | 機台底 | 狀態文字（textContent） | 何時用 |
|---|---|---|---|---|---|
| `is-normal` | machine-stroke 2px | success | machine-body | `RUNNING` | 預設 |
| `is-warn` | warn 3px | warn | machine-body | `WARNING` | 選用：異常前兆（MVP 可不用） |
| `is-stopped` | danger 4px | danger | machine-stopped-bg | `STOPPED` | 03:00 停線機台 |
| `is-idle` | idle 2px 虛線 | idle | machine-body | `IDLE` | 選用 |
| `is-focus` | 外加 info 3px 虛線框 | 不變 | 不變 | 不變 | 調查進行中，疊加在其他 class 上 |

- 不做動畫（PRD F1）。唯一的例外：`is-stopped` 的狀態燈可以 1 Hz 閃爍，但 `prefers-reduced-motion` 時關閉。若時間緊就不做。
- 線狀態 `L2-status` 文字：`Running` / `Stopped · 00:12`（計時放在 Alert banner，不必每秒改 SVG，這裡只寫 `Stopped`）。
- 右下 legend（HTML，不放 SVG 裡）：三個圓點＋文字 `Running` `Warning` `Stopped`，16px。

### 3.3 Alert banner（產線圖上方，高 96px）

| 狀態 | 底 | 左側文字 | 右側 |
|---|---|---|---|
| 停線 | danger-bg，左邊 6px danger 實線 | 標題 `Line 2 stopped`（28/700）＋副標 `M3 Molding · Over-temperature alarm at 03:00`（18/regular） | 計時器 `Downtime` 標籤＋`00:00:12`（64/700 tnum, danger）＋ Investigate 按鈕 |
| 正常 | surface-2，左邊 6px success | `All lines running`＋`No active alarms` | Investigate 按鈕（文案見分鏡：`Investigate Line 1`） |

- 計時器從情境的停線時間開始算，每秒更新；調查完成後**不停**（停線還在繼續，這才是真的）。

### 3.4 Investigate 按鈕（F2）

- 高 64px，最小寬 240px，padding 0 `--space-6`，radius-md。
- 預設：warn 實心底，text-on-accent 字，22px / 700，左側放大鏡 icon 24px。
- Hover：亮度 +8%（`filter: brightness(1.08)`）。
- Focus：`--focus-ring`（鍵盤操作與簡報遙控器要看得見）。
- 按下後 ≤ 1 秒切到 **Investigating**：底改 surface-3，字改 text-secondary，左側 spinner，文案 `Investigating…`，`aria-busy="true"`，`disabled`。
- 調查結束（結論或灰卡）後：按鈕文案變 `Investigated`，維持 disabled，直到按 Reset（F8）。避免重複觸發燒錢。
- 整個畫面只有這一個實心琥珀按鈕，其他按鈕一律 outline 或文字按鈕。

### 3.5 Investigation 面板（右欄容器）

- 背景 surface-1，radius-lg，padding `--space-5`。
- 表頭：`Investigation`（28/600）＋狀態 chip＋耗時 `Elapsed 00:42`（18, tnum, text-secondary）。
- 狀態 chip：

| 狀態 | 文案 | 色 |
|---|---|---|
| 未開始 | `Not started` | surface-3 底、text-secondary 字 |
| 進行中 | `Investigating` | info-bg 底、info 字 |
| 有結論 | `Root cause found` | warn-bg 底、warn 字 |
| 灰卡 | `Insufficient evidence` | grey-card 底、grey-accent 字、1px 虛線 grey-border |
| 失敗 | `Investigation failed` | danger-bg 底、danger 字 |

- 空狀態（未開始）：面板中央 18px text-secondary 文字，內容見分鏡。
- 內容區可捲動；新卡片出現時自動捲到最新卡片（使用者手動往上捲時暫停自動捲動）。

### 3.6 證據卡 Evidence card（F4）

結構（由上到下）：

1. **時間軸欄**（左側 40px）：步驟圓圈 32px（數字 16/600），圓圈間 2px 直線（border-strong）。
2. **標題列**：卡片標題 22/600（人話，例 `Coolant flow vs. baseline`）＋右側狀態。
3. **關鍵數值列**：數值 28/700 tnum ＋ 說明 18/regular text-secondary（例 `41%` `of baseline since 02:41`）。數值顏色：異常＝warn，正常＝text-primary。
4. **Meta 列**（16px muted）：函式名稱（font-mono）· 時間範圍 `02:30–03:05` · `12 rows`。
5. **角色 tag**（結論出現後才補上）：`Cited in conclusion`（info）或 `Ruled out`（text-secondary、1px border-strong 外框）。
6. **展開按鈕**：文字按鈕 `View source rows (12)`，info 色 18px，點開變 `Hide source rows`。

外觀：surface-2 底，1px border，radius-md，padding `--space-4` `--space-5`，卡片間距 `--space-3`。

狀態：

| 狀態 | 視覺 | 右側文字 |
|---|---|---|
| running | 標題顯示，數值區 2 行 skeleton（surface-3 條） | spinner＋`Querying…` |
| done | 完整 | success 勾＋`Done` |
| cached | 完整，右側加 chip | `Cached`（warn-bg/warn）＋ tooltip `Live query timed out. Showing last verified result.` |
| error | 數值區改一行 danger 文字 `Query failed` | `Failed` |

原始列展開區（回查 BigQuery）：

- surface-1 底，表格 14px（`--fs-xs`，這是唯一允許 14px 的大螢幕區域，因為評審會走近看或我們會放大），表頭 surface-3 底配 text-secondary 字（不能用 muted，對比不足）。
- 最多顯示 8 列，超過內部捲動；欄位名用 font-mono。
- **卡片關鍵數值對應的那一列（或那一格）用 warn-bg 高亮**，評審一眼看出「數字從這裡來」。
- 表下方一行 muted：`Source: {dataset.table} · {row count} rows · query {query_id}`。

進場：opacity 0→1、translateY 8px→0，`--motion-base`。reduced-motion 時直接出現。

選配（時間夠才做）：溫度／流量卡在數值右邊加 160×40 的 sparkline（info 線、warn 虛線表示 SOP 上限）。沒有也不影響 demo。

### 3.7 結論卡 Conclusion card（F5）

- surface-2 底，**上緣 4px warn 實線**，radius-md，padding `--space-5`。
- 內容順序：
  1. 小標 `Root cause`（16/600, warn, 全大寫, letter-spacing 0.06em）
  2. 根因 40/700：`Cooling valve CV-2 stuck at 20% open`
  3. 信心標籤列（見下）
  4. `Evidence` 小標＋引用 chip `#2` `#3` `#4`（info 外框 chip，點擊捲到該證據卡並閃一次 info 外框）
  5. `Ruled out` 小標＋一行：`Shift handover at 02:30 — no parameter changes (#5)`
  6. `Recommended actions` 有序清單 18px
  7. 右下：`Create work order` 按鈕（outline：2px warn 外框、warn 字、高 56px）
- 規則（PRD F5）：引用少於 2 張證據卡時**不渲染結論卡**，改走灰卡。

信心標籤 Confidence label：

- 形式：chip ＝ 三格小條（各 12×6px）＋文字 `Confidence: High`（18/600）。
- High ＝ 三格 info 實心；Medium ＝ 兩格；Low ＝ 一格，其餘格 surface-3。**文字一定要出現**，不只靠格數或顏色。
- 標籤下方一行理由（16, text-secondary），由後端回傳，例 `3 independent signals agree · 1 alternative ruled out`。判定規則等 PRD Q4。
- Low 時結論卡上方多一條 warn-bg 提示：`Low confidence — verify on site before acting.`

### 3.8 灰卡 Insufficient evidence card（F6）

取代結論卡的位置，證據卡照常留在上方。

- 背景 grey-card，**1px 虛線 grey-border**，radius-md，padding `--space-5`。
- 左上 icon：40px 圓形外框（2px grey-accent）內一個問號。
- 標題 `Insufficient evidence`（28/700, grey-accent）。
- 說明（18, grey-text）：`No root cause found. LineSleuth will not guess.`
- `Checked` 清單：每項左邊 success 勾＋項目名稱＋右側結果（text-secondary），例 `Mold temperature — within normal range`。清單項目要和上方證據卡一一對應。
- `Recommended next step`（18/600）＋ `Manual inspection of Line 1 by the shift supervisor.`
- **不顯示**信心標籤、**不顯示** Create work order。
- 右下文字按鈕 `Reset demo`（text-secondary）可選。
- 禁止：opacity 降低、斜線底紋、紅色。這是「負責任的答案」，不是錯誤畫面。

### 3.9 QR 區塊與工單 modal（F7，大螢幕）

- 按 `Create work order` 後出現置中 modal，寬 880px，surface-1，radius-lg，`--shadow-modal`，背後 `rgba(0,0,0,0.6)` 遮罩。
- 左：QR 區塊 ＝ 白底 `#FFFFFF` 方塊 320×320（內含 QR 280×280＋20px quiet zone），radius-md。QR 黑 `#000000`，錯誤修正等級 M。
- QR 下方：`Scan to open on your phone`（22/600）與短網址（18, font-mono, text-secondary），例 `ls.run/wo/0001`，給掃不到的人手打。
- 右：工單摘要：`Work order created`（success 勾＋28/700）、工單號 `WO-0001`、Line/Machine、Root cause、Priority chip。
- 右下：`Done` outline 按鈕，Esc 也能關。
- 工單建立失敗：modal 內改顯示 danger 文字 `Could not create work order. Try again.`＋`Try again` 按鈕。

### 3.10 情境切換與重置（F8）

- 位置：畫面左下角，低調（text-secondary、16px），評審注意力不應該在這裡。
- 內容：`Scenario:` 下拉（`Line 2 over-temperature` / `Normal data (Line 1)`）＋ 文字按鈕 `Reset`。
- 切換情境即自動重置。Reset 需在調查進行中也可按（中止並清空），不跳確認視窗。
- 鍵盤快捷鍵（給簡報者）：`R` = Reset、`1` = 主線情境、`2` = 正常情境。

### 3.11 手機工單頁（F7）

見 §4.2 版面。元件：

- 頁首：`LineSleuth` wordmark（18/700）＋ `Work order`（16, text-secondary）。
- 工單號 `WO-0001`（26/700）＋狀態 chip `Open`（info）＋優先度 chip `Priority: High`（warn-bg / warn）。
- 欄位用「標籤在上、值在下」的清單，不用表格：標籤 14/500 muted，值 16/regular primary。
- `Recommended actions` 用有序清單，每項前面空心 checkbox 樣式（純視覺，MVP 不存勾選狀態——可以砍）。
- 頁尾警語（14, text-secondary，上方 1px border）：`AI-generated from plant data. Verify on site before acting.`
- 點擊區最小 44×44px。不需登入。

## 4. 版面

### 4.1 大螢幕桌機 16:9（設計基準 1920×1080）

```
┌──────────────────────────────────────────────────────────────────────────┐
│ TopBar 72px: LineSleuth · Demo Plant · Night shift | Scenario time 03:00:14 | Demo scenario │
├───────────────────────────────────────────┬──────────────────────────────┤
│ Alert banner 96px                          │ Investigation panel           │
│ Line 2 stopped      Downtime 00:00:12 [Investigate] │ 表頭：Investigation · chip · Elapsed │
├───────────────────────────────────────────┤                               │
│                                           │ ① Evidence card               │
│   產線 SVG（line-layout.svg）              │ ② Evidence card               │
│   寬 100%，等比縮放                        │ ③ …                           │
│                                           │ ─────────────                 │
│                                           │ Conclusion / 灰卡              │
│                          legend ● ● ●     │                               │
├───────────────────────────────────────────┴──────────────────────────────┤
│ Scenario: [Line 2 over-temperature ▾]  Reset                  （左下，低調） │
└──────────────────────────────────────────────────────────────────────────┘
```

- 外距 `--space-6`（32px）；主區 CSS grid：`grid-template-columns: 7fr 5fr; gap: var(--space-5);`。
- 左欄約 1060px：banner＋SVG（SVG 高度由寬度決定，viewBox 1200×640 → 約 565px 高）。
- 右欄約 780px：面板高度填滿 TopBar 與底列之間（約 900px），內部捲動。
- 底列高 48px。
- 小於 1440px 寬（筆電練習用）：同樣兩欄，字級不變，SVG 自動縮小；小於 1100px 不支援（demo 不會用到，別花時間做）。
- 投影前檢查：瀏覽器縮放 100%、全螢幕（F11），不要有書籤列。

### 4.2 手機工單頁（設計基準 390×844，支援 360–430 寬）

```
┌──────────────────────────┐
│ LineSleuth · Work order   │  頁首 56px，surface-1
├──────────────────────────┤
│ WO-0001                   │
│ [Open] [Priority: High]   │
│                           │
│ LINE / MACHINE            │
│ Line 2 · M3 Molding       │
│ DETECTED                  │
│ 03:00 (scenario time)     │
│                           │
│ ROOT CAUSE                │
│ Cooling valve CV-2 stuck  │
│ at 20% open               │
│ [Confidence: High ▮▮▮]    │
│                           │
│ EVIDENCE                  │
│ • Mold temp 214 °C …      │
│ • Coolant flow 41% …      │
│ • CV-2 position 20% …     │
│                           │
│ RECOMMENDED ACTIONS       │
│ ☐ 1. …                    │
│ ☐ 2. …                    │
│ ☐ 3. …                    │
│                           │
│ SOP reference: SOP 4.2    │
│ Created 03:01 by LineSleuth│
├──────────────────────────┤
│ AI-generated … verify …   │  頁尾
└──────────────────────────┘
```

- 單欄，左右 padding `--space-4`，區塊間距 `--space-5`，各區塊之間 1px border 分隔。
- 不放產線圖、不放證據原始列表格（手機上太擠；要看就回大螢幕）。
- 字級套 §1 的手機覆寫；內文最小 14px。
- `<meta name="viewport" content="width=device-width, initial-scale=1">`，禁止橫向捲動。
- 找不到工單：同一版面，標題 `Work order not found`，說明 `This link may be expired or mistyped.`。

## 5. 可及性檢查清單（實作後由 Quinn 順手抽查）

- [ ] 所有狀態同時有顏色與文字（機台、chip、證據卡、信心標籤）
- [ ] Tab 順序：Investigate → 證據卡展開按鈕（依序）→ 引用 chip → Create work order → 情境切換
- [ ] 可見 focus ring（`--focus-ring`）
- [ ] 證據卡容器 `aria-live="polite"`，新卡片會被讀出標題
- [ ] 計時器 `aria-live="off"`（每秒更新不要一直念）
- [ ] 產線 SVG `role="img"` 並有 `<title>`；機台 `<g>` 有 `aria-label`（例 `Line 2 M3 Molding: stopped`），JS 改狀態時一起改
- [ ] `prefers-reduced-motion` 關掉卡片進場與燈號閃爍
- [ ] 手機頁點擊區 ≥ 44px

## 6. 刻意砍掉的東西（不要偷偷加回來）

- 聊天輸入框、自然語言提問
- 儀表板式的 KPI 圖表牆、多產線總覽統計
- 深淺色切換、多語系切換（越南文只在 pitch 示意圖）
- 登入頁、首頁行銷頁（網址打開直接就是產線畫面）
- 工單頁的勾選狀態儲存、指派人、留言
- 產線圖動畫（除 §3.2 可選的狀態燈閃爍）
