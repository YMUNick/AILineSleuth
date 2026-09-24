# Demo 影片分鏡：LineSleuth（v0.3 草稿）

- 草稿 v0.1，2026-09-24，Paula（PM）。老闆交代：先把分鏡討論定，再動手做影片。
- v0.2，2026-09-24，Sandy（業務）：S01 hook 加上地點（Southeast Asia），開場不再先靜止 2 秒；S02、S04、S08、S10 各改一句旁白，讓非母語評審更好懂；S11 從 16 秒延長到 18 秒並重寫：預設只講我們服務誰和怎麼收費，不描述競品，對比句標 `[to verify]`。多出的 2 秒從 S02、S04 各挪 1 秒，總長仍是 2:55。2.2 補上 SRT 必須燒進畫面時的短標語精簡規則。另外回覆第 6 節 S-1～S-5（標「Sandy 回覆」），並更新第 1 節 C 版規格、第 4 節競品列、5.7 時程。
- v0.3，2026-09-24，Dana（設計）：回覆第 6 節 D-1～D-6 與 Sandy 追加的兩件（D-7 S11 地圖與中性兩欄、D-8 S02 原話字卡），標「Dana 回覆」；新增第 7 節「影片視覺規格」；2.2 每一鏡補上「畫面執行」（素材、入點狀態、構圖與推近目標、疊加層、出點）；剪接標示改名為 `WAITING TIME CUT`；字卡字體改成和簡報一致（Arial／Calibri）；2.4 補 1:1 裁切位置；2.5 替代畫面 ②、④ 改用第 7 節版型；5.6 素材 #6–#8 更新。建議 S05／S06 對調成照時間順序（見 S05，待 Paula 決定，2.1 時間碼未改）。
- 2026-09-24，Paula（PM）：依 `docs/meetings/2026-09-24-部署後下一步.md` 定案，2.4 C 版片尾改成停在 PPT 封面，並註明 C 版分鏡以 `storyboard-30s-image-prompts.md` v0.2 為準。
- 依據：`docs/meetings/2026-09-24-駭客松主題方向.md`、`docs/prd.md`、`docs/design/storyboard.md`（現場五格分鏡、UI 文案定稿）、`docs/pitch/pitch-script.md`、`docs/pitch/one-pager.md`、`docs/pitch/submission-summary.md`
- 畫面以 **UI 改版 v2** 為準（Dana 的 `docs/design/ui-v2-spec.md`，規格已定稿、實作中，以及 `docs/design/line-layout-v2.svg`）：① 證據卡 sparkline ② 根因找到後 L2-M3／CV-2 高亮並標 `ROOT CAUSE` ③ 窄螢幕版面修正 ④ 結尾 before/after 對比。v2 規格定稿後，本文件的畫面描述跟著對齊；UI 文案一律以 `storyboard.md` §5 為準。
- 搭配：`docs/pitch/pitch-deck.md`（投影片編號）、`docs/manual/user-manual.md` §3.8 簡報者模式、§4.2 快捷鍵、`docs/qa/test-plan.md` §6 現場備援

## 標記說明

| 標記 | 意思 | 規則 |
|---|---|---|
| `[pending interviews]` | 等訪談驗證 | 只能換成真實訪談數字或已授權原話；沒有就用該鏡的「無數字替代句」 |
| `[to measure]` | 等實測 | 換成回歸集或實測結果；沒有就用替代句 |
| `[to verify]` | 等查證 | 對照公開資料或實際部署設定 |
| `{…}` | 從錄到的那一次 take 讀值 | 必須和畫面上顯示的一致 |

標記只給內部看，**不能出現在成片畫面、SRT 或影片說明欄**。

## 0. 三條底線（所有版本共用）

1. **錄的都是真的**：只用 Cloud Run 部署版、`gemini` 模式、映像內建 DuckDB 示範資料錄影（可換 BigQuery，但影片不能說已支援 BigQuery）。畫面不能出現 OFFLINE FIXTURE 黃條。每個採用的 take 都要記下 `query_id` 和 `Elapsed`，評審問「是不是寫死的」時拿得出 Cloud Logging 紀錄（對應 `judge-qa.md` Q12）。
2. **只剪等待，不改結果**：繳交版可以剪掉等待時間（跳接，不變速），剪接處要標示；`Elapsed` 永遠是真實時間。備援版不剪也不變速。出現 `Cached` chip 就重錄，不能剪掉或遮住。
3. **沒驗證的數字不出現**：40 分鐘、停線損失都要照第 4 節處理。已驗證可用的只有實測值：約 12 秒找到根因（中位數 12.6 秒）、回歸 10/10（出處 `docs/qa/runs/README.md`）。「90 秒」已停用。影片**沒有 Ask 段**，結尾只放聯絡方式和 prototype 連結。

---

## 1. 影片用途與版本

原則：**同一場錄影錄一次，剪成三個版本**。素材共用，避免老闆重複錄。

| 版本 | 長度 | 觀眾／場合 | 目標 | 聲音 | 畫面 | 期限 | 優先 |
|---|---|---|---|---|---|---|---|
| **A 繳交版** | 上限假設 3:00，目標 2:55（**待確認官方規定**） | 書面審查的評審，看的時候我們不在旁邊 | 不用人解說也看得懂：痛點 → 一鍵調查 → 可回查的證據 → 根因＋工單 → 灰卡 → Google Cloud → 服務對象；看完願意打開 prototype 網址 | 英文旁白＋音樂＋英文 SRT | 16:9，1920×1080 | 10/16 剪完，10/17 繳交 | P0 必做 |
| **B 現場備援版** | 主線 90 秒＋灰卡 30 秒（兩個檔） | 現場 live demo（含 12/4 決賽），網路斷、Gemini 逾時、429 時切換 | 和 live demo 逐格同步，講者照 `pitch-script.md` 繼續講 | 無旁白、無音樂；保留分鏡 caption | 16:9，1920×1080 | 10/16（上線前檢查清單第 ⑤ 項） | P0 必做 |
| **C 社群短版** | 30 秒 | LinkedIn 等社群；東南亞／台灣的工廠主管和潛在夥伴 | 3 秒抓住注意；靜音自動播放也看得懂根因和灰卡 | 音樂＋燒入字幕，不用旁白 | 1:1，1080×1080（S-5 已定：9:16 先不做） | 繳交後再做 | P2 選做 |

**待確認官方規定**（老闆查官網或問主辦，查到後回填本節）
- 影片長度上限、檔案格式與解析度
- 繳交方式：直接上傳檔案，還是 YouTube／Drive 連結；可否設為不公開
- 語言與字幕要求；能不能用背景音樂（版權）
- 影片是否必須包含 prototype 實際操作畫面
- 截止前能不能在社群公開發布（會影響 C 版的發布時間）

---

## 2. 分鏡表

### 2.1 繳交版總表（A，目標 2:55）

| 鏡 | 時間碼 | 秒 | 畫面類型 | 重點 | 對應功能 |
|---|---|---|---|---|---|
| S01 | 0:00–0:10 | 10 | 螢幕錄影 | 03:00 東南亞代工廠 Line 2 亮紅燈，Downtime 在跳 | F1 |
| S02 | 0:10–0:20 | 10 | 簡報頁 | 痛點：夜班主管一個人翻 Excel／PLC log | Slide 2 |
| S03 | 0:20–0:28 | 8 | 螢幕錄影 | 按下唯一的 Investigate，聚焦 L2-M3 | F2、v2 聚焦 |
| S04 | 0:28–0:57 | 29 | 螢幕錄影 | 證據卡逐張長出，每張有 sparkline | F3、F4、v2 ① |
| S05 | 0:57–1:07 | 10 | 螢幕錄影 | 點開原始列，看到 query ID | F4 |
| S06 | 1:07–1:23 | 16 | 螢幕錄影 | 結論卡＋信心標籤；產線圖 CV-2 高亮並標 `ROOT CAUSE` | F5、v2 ② |
| S07 | 1:23–1:38 | 15 | 螢幕錄影＋手機畫面 | 建立工單 → QR → 手機開出工單 | F7 |
| S08 | 1:38–1:46 | 8 | 螢幕錄影 | before/after 對比卡 | v2 ④ |
| S09 | 1:46–2:12 | 26 | 螢幕錄影 | 灰卡「Insufficient evidence」 | F8、F6 |
| S10 | 2:12–2:29 | 17 | 簡報頁 | Built on Google Cloud＋回歸集 | Slide 7、F3 |
| S11 | 2:29–2:47 | 18 | 簡報頁 | 服務對象（東南亞、台灣中小代工廠）、收費方式、下一步 | Slide 8／9／10 |
| S12 | 2:47–2:55 | 8 | 字卡 | 結尾：聯絡方式與 prototype 連結 | — |

旁白用每秒約 2.5 字的速度估算，和 `storyboard.md`、`pitch-script.md` 一致。每一鏡的旁白都比秒數短 1–3 秒，留給點擊和轉場。

### 2.2 逐鏡分鏡（繳交版）

「字幕」指燒進畫面的短標語；完整旁白另外做成 SRT（見 5.4）。

每一鏡的「畫面執行」是 Dana 在 v0.3 補的，剪輯時照做即可：構圖代號 K0–K4 見 7.7（用 K 是為了不和 PRD 的功能編號 F1–F8 搞混），疊加位置 BL（左下資訊區）、TL 見 7.2，各圖層樣式見 7.5。座標都以 1920×1080 的 app 畫面（CSS px）為準，錄 2 倍母帶時全部 ×2；10/13 試錄後由 Dana 依實際畫面微調。

Sandy 註：如果上傳平台不支援 CC、SRT 必須燒進畫面，短標語只留 S01、S04、S09、S11 四則，其他刪掉，免得非母語評審同時要看兩層字。

---

#### S01　03:00 停線（0:00–0:10）F1

- **畫面**：螢幕錄影。一開場就是產線畫面，沒有 logo 動畫（沿用 storyboard 原則）。Line 1、Line 3 綠燈；**L2-M3 Molding 紅框 `STOPPED`**；紅色 banner `Line 2 stopped` / `M3 Molding · Over-temperature alarm at 03:00`；`Downtime` 每秒跳動。
- **動作**：0:00 就開始慢慢推近（約 1.1 倍）到紅色機台和 banner，不先靜止。左下角小字 lower-third `Simulated plant data`，先講清楚是模擬資料。
- **畫面執行（Dana）**
  - 素材：主線 take 的開頭。腳本按 `1` 重置後立刻開錄，入點取重置後第 1 秒，`Downtime` 從個位數秒開始跳。這一鏡沒有游標。
  - 入點狀態：全景；面板是 `Not started` 空狀態；TopBar 的 `Scenario time 03:00:0x`、`Demo scenario` chip 和底列 `Agent: … · data: bigquery` 都在畫面裡。
  - 構圖：K1 慢推 1.0→1.1（0:00–0:09.5），錨點在 banner 標題和 L2-M3 之間（約 (560, 320)）；推完後 banner、`Downtime`、L2-M3 仍然完整在框內。
  - 疊加：BL 堆疊。下層小標示 `Simulated plant data`（0:00–0:10 全程）；上層短標語 `03:00 — Line 2 stops.`（0:01.5–0:09.5）。
  - 出點：0:10，200ms 交叉淡化到 S02。
- **旁白**：It's 3 a.m. at a small contract factory in Southeast Asia. Line 2 just stopped, and the night supervisor is alone.（21 字，約 8.4 秒，0:01 開始講）
- **字幕**：`03:00 — Line 2 stops.`
- **音效／音樂**：警報「嗶」兩聲放在 0:00，音量要小，不要刺耳；低沉 pad 同時淡入。
- **Sandy 註**
  - 前 10 秒只回答三件事：誰、在哪、出了什麼事。加上 `in Southeast Asia`，讓 JAPAC 評審一開頭就知道是他們的區域；台灣放到 S11 一起講。前 3 秒要有聲音和動態，靜止畫面容易被當成影片還沒開始。
  - Google Cloud 不必塞進 hook：0:00 開場就是真的 app 畫面，0:28 的 S04 就會唸到 Gemini on Vertex AI，已經夠早（BigQuery 只能說「可換」，不在旁白裡唸）。
  - `on their own` 改成 `alone`：意思一樣，非母語評審比較好懂。

#### S02　痛點（0:10–0:20）Slide 2

- **畫面**：簡報頁，使用 Slide 2 的視覺：大大的 `03:00`、紅點、一疊 Excel／CSV 檔案圖示。如果有受訪者授權的原話，改成原話字卡（附對方同意的稱呼，授權規則見 S-3）。
- **動作**：檔案圖示一個一個疊上去（簡單的位移動畫就好）。
- **畫面執行（Dana）**
  - 素材：`s02-problem`（Slide 2 影片版，版面見 7.4），底圖一張、四張檔案卡各一張透明 PNG。有授權原話時整鏡改用 `s02-quote`（原話卡，見 7.4、D-8），檔案卡動畫就不用做。
  - 版面：左邊 `03:00`（紅）＋`Line 2 stops.`＋一行 `Excel sheets. PLC exports. Shift logs.`，這一行就是本鏡的短標語，直接排在頁面上，不另外疊一層。右邊四張檔案卡。投影片上的 `X*`、`~40 min*` 兩個 bullet 和底部註腳都拿掉（標記不能入鏡）。
  - 動作：底圖 0:10 就在。旁白唸到 `Excel`、`PLC`、`shift logs` 時各出現一張檔案卡（淡入＋上移 8px，300ms），第四張 `alarms_L2.csv` 在第三張之後 0.6 秒出現，之後整頁靜止。這一鏡不推近。
  - 有數字版（第 4 節允許時才用）：在 `Excel sheets…` 那一行下面加 `~{minutes} min to find the cause`（Arial Bold 40px，主要文字色，規則同 7.4 數字卡）＋來源小字；沒有來源文字就不能放。
  - 出點：0:20，200ms 交叉淡化回 app（S03）。
- **旁白（有數字版）**：Finding the cause takes about 40 minutes `[pending interviews]` of digging through Excel sheets, PLC exports and shift logs. Every hour of downtime costs X `[pending interviews]`.
- **旁白（原話版）**：One plant manager told us: "[quote]" `[pending interviews]`（原話 15 字以內）
- **旁白（無數字替代，預設）**：Finding the cause means digging through Excel sheets, PLC exports and shift logs, while every minute of downtime costs money.（20 字，約 8 秒）
- **字幕**：`Excel sheets. PLC exports. Shift logs.`（有數字版才另加 `~40 min to find the cause`；原話版由原話字卡取代）
- **音效／音樂**：音樂維持低音量；檔案疊上去時配輕微紙張或點擊聲。
- **Sandy 註**：原稿的 `they dig through` 用單數 they 指主管，非母語評審容易聽成「一群人」，所以改用「找原因」當主詞，也短了 4 字，這一鏡因此縮成 10 秒。X 只能用受訪者自己講的金額和幣別。

#### S03　一顆按鈕（0:20–0:28）F2、v2 聚焦

- **畫面**：螢幕錄影，回到產線畫面。
- **動作**：游標移到琥珀色 `Investigate` 並按下 → 按鈕變 `Investigating…` → L2-M3 出現藍色虛線聚焦圈，產線圖聚焦到 L2-M3，其他產線變暗（v2）→ 面板 chip `Investigating`，`Elapsed` 開始跑，第一張卡出現 `Querying…`。lower-third 顯示 3 秒：`LineSleuth — root-cause investigations for small factories`。
- **畫面執行（Dana）**
  - 素材：主線 take，接在 S01 那段後面，入點取假游標出現前 0.5 秒。S01 和 S03 中間隔著 S02 簡報頁，`Downtime` 的秒數接不上是正常的，不需要標示（還沒開始調查，也沒有 `Elapsed`）。
  - 構圖：K0 全景，整鏡不做後製推近。這一鏡的鏡頭運動就是 app 自己的聚焦拉近（按下後 +150ms 開始，700ms 完成），不要再疊一個後製推近。
  - 游標：從面板中間（約 (1500, 600)）出現，0.6 秒移到 `Investigate`，停 0.3 秒讓 hover 狀態入鏡，點擊（白色波紋）。拉近完成後移到產線圖左下的空白處，2 秒後淡出。
  - 疊加：BL。雙行 lower-third `LineSleuth` / `Root-cause investigations for small factories`（0:20.5–0:23.5，對齊 "This is LineSleuth"），接著換成短標語 `One click. No prompt.`（0:23.7–0:27.7）。
  - 出點：面板第一張卡的 skeleton `Querying…` 出現後，0:28 接 S04（同一段畫面，直接接續）。
- **旁白**：This is LineSleuth. One button: no chat box, no prompt to write.
- **字幕**：`One click. No prompt.`
- **音效／音樂**：按鈕點擊聲；音樂進入主節奏。

#### S04　證據卡時間軸（0:28–0:57）F3、F4、v2 ①

- **畫面**：螢幕錄影，右側 Investigation 面板。後製把面板放大約 1.3 倍，讓 sparkline 看得清楚（和 app 本身的聚焦縮放是否會疊在一起，見開放問題 D-4；v0.3 定為 1.25 倍，見下方畫面執行）。
- **動作**：卡片由上往下逐張出現，每張出現時停留約 4–5 秒：
  1. `Alarm events`：事件時間軸 sparkline，03:00 的警報點是紅色
  2. `Mold temperature`：溫度曲線，加上 SOP 上限虛線，曲線在 02:52 之後超過上限（琥珀色）
  3. `Coolant flow vs. baseline`：流量線和基準線，02:41 之後往下掉
  4. `Cooling valve CV-2 position`：commanded 和 actual 兩條線，02:41 之後分開
  5. `Shift & maintenance log`：02:30 交班，數值正常色
  - 卡和卡之間的等待時間可以剪掉（跳接）；剪接處在 `Elapsed` 正下方出現 `WAITING TIME CUT` 標示（v0.3 由 `Trimmed · real time in Elapsed` 改名，樣式與位置見 7.5），`Elapsed` 保持入鏡。
- **畫面執行（Dana）**
  - 素材：同一 take，從第一張卡 `Querying…` 到第 5 張卡畫完線。
  - 構圖：0:28.0–0:28.8 從 K0 推到 K2（1.25 倍，面板在右、聚焦中的 L2-M3 在左），之後整鏡固定，不跟著每張卡移動。最新的完整卡會出現在精簡列下方（約來源 y 450–720），一定在框內；面板表頭的 chip 和 `Elapsed` 全程在框內。app 的聚焦拉近在 S03 已經停了，這裡推近不會和它同時動。
  - 每張卡：畫線動畫（M7、M8，約 0.9 秒）播完後，至少再停 3.5 秒才能接下一個跳接。
  - 跳接點：只能剪在「上一張卡已經停夠、下一張卡還是 skeleton `Querying…`」的區間；卡片從 skeleton 變成完成的那一刻不能剪掉。一律硬切，不用交叉淡化（淡化會疊出兩個 `Elapsed` 數字）。每個剪接點都疊 `WAITING TIME CUT`。
  - 疊加：BL 短標語 `5 fixed queries. Gemini never writes SQL.`（0:29–0:35，對齊旁白第一句）；剪接點的 `WAITING TIME CUT`。
  - 出點：第 5 張卡（`Shift & maintenance log`）畫完線後停 2 秒，0:57 接下一鏡。
- **旁白**：Gemini on Vertex AI doesn't write SQL. It picks from five fixed, tested queries, and every step becomes an evidence card. The alarm fired at 3:00. Mold temperature climbed past the SOP limit. Coolant flow fell far below its baseline. Valve CV-2 was commanded to open, but it stayed almost closed. And the 2:30 shift handover? Checked, and ruled out.（63 字，約 25 秒；本鏡縮成 29 秒仍留 4 秒給卡片出現）
- **字幕**：`5 fixed queries. Gemini never writes SQL.`
- **音效／音樂**：每張卡出現時一聲很輕的「tick」。
- **備註**：旁白刻意不唸感測器數值。數字交給畫面上的卡片和 sparkline 呈現；模擬資料之後如果調整，只要重錄畫面，不用重錄旁白。
- **Sandy 註**：`commanded open, but it stayed stuck nearly closed` 同一句有 stayed 又有 stuck，聽起來卡卡的；改成 `commanded to open, but it stayed almost closed`，字數不變，而且 `commanded` 對得上卡片上的 `Commanded 80%` 標籤。`stuck` 留到 S06 根因再講。

#### S05　回查原始列（0:57–1:07）F4

- **畫面**：螢幕錄影，放大到 `Coolant flow vs. baseline` 卡。
- **動作**：點 `View source rows (12)` → 原始列表格展開，`02:41` 那一列的 flow 欄琥珀底高亮 → 後製推近到表格下方的 `Source: linesleuth_demo.sensor_readings · 12 rows · query {query_id}`，停 3 秒 → 點 `Hide source rows`。
- **畫面執行（Dana）**
  - 錄影時機：**結論出現、脈動結束之後**才操作，不管剪輯時這一鏡放在 S06 前面還是後面，錄法都一樣。調查進行中去點，展開的 #3 會把後面的新卡擠出畫面；卡在第 5 張和結論之間點，結論隨時會落地、面板會重新排版，時間抓不準。
  - 腳本動作：點結論卡裡的引用 chip `#3` → app 自動捲到 #3、展開、閃一次藍框 → 點 `View source rows (12)` → 如果 `02:41` 那一列或表格下方的 `Source:` 行不在可見範圍，在證據列裡捲到兩者都看得到 → 停 4 秒 → 點 `Hide source rows`。
  - 構圖：K3（1.5 倍，約 1280×720 的視窗，以展開的 #3 卡和原始列表格為中心），14px 的表格字等於放大到約 21px。`Source: … · query {query_id}` 那一行加琥珀重點框 3 秒；不再第二次推近，框出來就夠了。
  - 游標：點擊時出現，最後一下點完就移到產線圖區並淡出。
  - 疊加：BL 短標語 `Every number traces back to the source rows.`（表格展開後出現，停 4 秒）。
  - **建議照時間順序剪（請 Paula 決定）**：S04 → S06 → S05。先講結論、再點引用回查原始列，是「主張 → 證據」的順序，也符合第 0 節「只剪等待，不改結果」的精神（不打亂事件先後）。對調後時間碼是 S06 0:57–1:13、S05 1:13–1:23，其他鏡不變，旁白不用改。
  - 如果維持目前順序（S05 在 S06 前面）：入點取 #3 已經展開之後（點 chip 的動作不能入鏡），K3 視窗不能包含面板頂端的結論卡和產線圖，以免提前揭曉根因；#3 卡上的 `Cited in conclusion` tag 會入鏡，可以接受。
- **旁白**：Every number traces back to its source rows, and every query is logged, so any investigation can be replayed.
- **字幕**：`Every number traces back to the source rows.`
- **音效／音樂**：點擊聲；表格展開時音樂稍微壓低，讓畫面說話。

#### S06　根因與信心（1:07–1:23）F5、v2 ②

- **畫面**：螢幕錄影，前半段看產線圖，後半段看面板。
- **動作**：
  - 產線圖（聚焦在 L2-M3）：聚焦圈從藍色虛線變成琥珀色實線；`CV-2 valve` 變成琥珀色膠囊並脈衝 3 次；M3 出現 `ROOT CAUSE` 標籤（依 `line-layout-v2.svg` 的時序）。
  - 面板：結論卡出現，`Root cause`、`Cooling valve CV-2 stuck at 20% open`、`Confidence: High`、`3 independent signals agree · 1 alternative ruled out`；證據卡 #2、#3、#4 加上 `Cited in conclusion`，#5 加上 `Ruled out`；chip 變成 `Root cause found`，`Elapsed` 停止。
  - 後製：畫面先停在產線圖 6 秒，再平移到結論卡。
- **畫面執行（Dana）**
  - 素材：同一 take，結論落地前約 2 秒到落地後約 15 秒（在 S05 的點擊之前）。
  - 入點：
    - 接在 S04 後面（建議順序）：K2 構圖下跳接，剪掉第 5 張卡到結論之間的等待（疊 `WAITING TIME CUT`），入點落在結論出現前約 2 秒 → 800ms 推到 K4 → 結論在 K4 裡落地。
    - 接在 S05 後面（目前順序）：直接硬切進 K4，入點在結論出現前 1 秒。
  - 前段（約 6 秒）K4 產線圖特寫：1.5 倍，以 L2-M3 為中心，CV-2 閥門和 `ROOT CAUSE` 標籤都在框內。要拍到藍色虛線框轉成琥珀實線、CV-2 變琥珀並脈動 3 次（約 4.1 秒）；脈動結束後再停 1 秒。L2-M3 本體保持紅色 `STOPPED`。
  - 後段：800ms 平移到 K2，停到本鏡結束。這時畫面上要看得到結論卡（`Root cause`、`Confidence: High`、理由列）、chip `Root cause found`、停住的 `Elapsed`、精簡列上的 `Cited`／`Ruled out`，左邊是琥珀高亮的 L2-M3。
  - 疊加：BL 短標語 `Root cause + confidence + what was ruled out.`（進入 K2 後出現，停到結束前 0.3 秒）。
  - v2 沒上線時：K4 構圖不變，後製加琥珀外框＋`ROOT CAUSE` 標籤（見 7.5「後製根因標籤」）。
- **旁白**：Root cause: cooling valve CV-2 stuck, highlighted right on the line. Confidence is high: three independent signals agree, and the shift handover is ruled out, not ignored. Our server scores that confidence, not the model.
- **字幕**：`Root cause + confidence + what was ruled out.`
- **音效／音樂**：CV-2 第一次脈衝時一聲輕柔 chime（只響一次，不要跟著 3 次脈衝響）。

#### S07　工單上手機（1:23–1:38）F7

- **畫面**：左側約 2/3 是螢幕錄影，右側是手機外框，裡面放手機螢幕錄影。
- **動作**：點 `Create work order` → modal 出現 QR、`Work order created`、`WO-{id}`、`Priority: High` → 右側手機：相機對準 QR → 點開連結 → 工單頁由上往下捲到 `ROOT CAUSE`、`EVIDENCE`、`RECOMMENDED ACTIONS`，最後停在頁尾 `AI-generated from plant data. Verify on site before acting.`
- **連續性**：手機上的 `WO-{id}` 必須和大螢幕 modal 是**同一次 take 產生的同一張工單**。
- **畫面執行（Dana）**
  - 素材：主線 take（點 `Create work order` → modal）＋同一張工單的手機螢幕錄影（錄法見 7.10）。
  - 1:23–1:25：K2。游標點結論卡的 `Create work order` → 遮罩＋置中 modal（QR、`Work order created`、`WO-{id}`、`Priority: High`）。
  - 1:25–1:25.5：切成左右版面（500ms，一次完成）。桌面畫面裁成以 modal 為中心的 1260×709 視窗，1:1 顯示在畫面 (96, 186)，modal 的字維持原尺寸；手機外框從右邊淡入並左移 40px，停在 (1406, 104)。
  - 手機（和桌面同步）：約 1:26 相機對準 QR → 約 1:28 點開連結 → 工單頁出現時，桌面 modal 和手機上的 `WO-{id}` 同時加琥珀重點框 1.5 秒，證明是同一張工單 → 一次慢慢往下捲到頁尾 `AI-generated from plant data. Verify on site before acting.`，停到 1:37.5。
  - 手機畫面不剪、不變速。從掃碼到開出工單頁超過 4 秒就重錄手機，不要用剪的。
  - 1:37.5–1:38：手機外框淡出，桌面畫面放回全幅 K0（500ms），接 S08。
  - 游標：點完 `Create work order` 就停在 modal 外面並淡出，不能擋住 QR。
  - 疊加：TL 短標語 `Work order on the technician's phone.`（工單頁出現後 7 秒），放在桌面畫面上方的空白處（左上角 (96, 70)），不壓到桌面畫面和手機。
  - 手機外框用通用造型（沒有品牌外型、瀏海或按鍵），手機狀態列用外框頂部的色塊遮掉（見 7.10）。
- **旁白**：One click creates the work order. The technician scans the QR code and has the root cause, the evidence and the SOP steps on their phone.
- **字幕**：`Work order on the technician's phone.`
- **音效／音樂**：掃到 QR 時「嗶」一聲。

#### S08　Before / After（1:38–1:46）v2 ④

- **畫面**：螢幕錄影，app 裡的 before/after 對比卡（位置與文案依 `ui-v2-spec.md`）。after 是這次 take 的實測秒數；before 是設定值提供的人工基準，**沒驗證就不顯示數字**。
- **動作**：卡片出現，後製推近到 after 數字，停 3 秒。
- **畫面執行（Dana）**
  - 素材：主線 take，游標點 modal 的 `Show summary` → Recap 全螢幕層（v2 §4）。
  - 狀態：預設是「沒設基準」的 Recap。Before 列是 `—`＋`Not yet measured for this plant.`，After 列是 `{after}`（綠）＋明細 `{q} queries · {c} evidence cited · {r} ruled out · Work order WO-{id}`，兩邊都沒有長條。只有第 4 節允許、`MANUAL_BASELINE_*` 有設定時，才會出現 Before 分鐘數、來源和長條。
  - 構圖：K0。Recap 開啟動畫（240ms；有長條時要等長條播完，約 1.4 秒）結束後，緩推 1.0→1.1（約 4 秒），中心對準 After 列，整張 Recap 卡始終完整在框內；最後 2 秒靜止。不另外加重點框，不做數字跳動。
  - 游標：點完 `Show summary` 就淡出。
  - 疊加：無。
  - v2 Recap 沒上線時：改用數字卡 `This run`（7.4），數字＝這次 take 最後的 `Elapsed`；不做空白的 Before 格。
- **旁白（before 已驗證）**：By hand, it takes about {before} minutes, plant managers told us `[pending interviews]`. This run took {after} seconds `[to measure]`.（16 字，約 6.4 秒）
  - Sandy 註：原稿 `Manual search: about…` 是電報體，而且沒有講數字從哪來。改成直接講出處（受訪的廠長），和 Recap 卡的 `Source:` 同一個來源；只有一位受訪者時改成 `a plant manager told us`。
- **旁白（before 未驗證，預設）**：On this run, LineSleuth went from one click to a root cause in {after} seconds `[to measure]`.
- **旁白（完全無數字替代）**：From a long manual search to one click, with the evidence attached.
- **字幕**：無，對比卡本身就是字幕。
- **音效／音樂**：音樂小幅上揚。
- **備註**
  - {after} 一定要等於畫面上的 `Elapsed`。
  - **不能刻意挑最快的 take**：採用的 take，`Elapsed` 不能低於 Quinn 實測的中位數 12.6 秒（gemini-2.5-flash，`docs/qa/runs/README.md`；10/8 雲端驗證若不同以新值為準），這樣這個數字才有代表性。
  - 影片不使用「40 min → 90 sec」舊口號，只呈現實測值（約 12 秒）。

#### S09　灰卡：沒有證據就不下結論（1:46–2:12）F8、F6

- **畫面**：螢幕錄影，整個畫面。
- **動作**：
  1. 按 `Done` 關掉 modal → 按 `2`（`Normal data (Line 1)`）→ 畫面重置：全部綠燈，綠色 banner `All lines running` / `No active alarms`。
  2. 點 `Investigate Line 1` → 證據卡逐張出現，sparkline 都在正常範圍內（溫度低於 SOP 上限、流量貼著基準線）。等待時間可剪，規則同 S04。
  3. 灰卡出現：虛線框、問號、`Insufficient evidence`、`No root cause found. LineSleuth will not guess.`、`Checked` 清單四項、`Recommended next step` / `Manual inspection of Line 1 by the shift supervisor.`；chip 變灰色 `Insufficient evidence`。
  4. 產線圖：Line 1 外框變成灰色虛線，出現 `No root cause found` 標記（v2）；**沒有**任何機台變色、**沒有** `Create work order`。
  5. 後製推近灰卡，整張卡（含 `Checked` 清單）完整停留至少 4 秒。
- **畫面執行（Dana）**
  - 素材：灰卡 take（另外錄的 take）。入點是按 `2` 之後的綠色全景，不用拍到關 modal、按鍵的過程（剪輯上從 S08 的 Recap 直接硬切過來）。
  - 1:46–1:49，K0：全部 `RUNNING`、綠色 banner `All lines running` / `No active alarms`、底列 `Scenario: Normal data (Line 1)`、面板 `Not started`。
  - 約 1:49：游標移到 `Investigate Line 1` 點擊 → app 拉近到 L1-M3（700ms）。app 停下後 0.3 秒，後製從 K0 推到 K2（800ms）。游標停放後淡出。
  - 證據卡：跳接和 `WAITING TIME CUT` 的規則同 S04，但正常資料的卡不需要逐張讀（看得出「線都很平靜」就好），每張畫線後停 1.5 秒就可以跳接。秒數預算：綠色全景 3 秒＋點擊與推近約 2 秒＋4 張卡約 10 秒＋灰卡落地 1.1 秒＋推近 0.8 秒＋灰卡特寫 5 秒＋拉回 0.8 秒＋全景約 3.3 秒 ＝ 26 秒。
  - 灰卡落地（音樂留白 1 秒）：後製鏡頭先不動，等 app 把產線圖拉回全景、Line 1 的灰色虛線和 `No root cause found` 徽章出現（約 1.1 秒）。
  - 接著推到 K3 灰卡特寫（1.5 倍；整張灰卡含 `Checked` 四項和 `Recommended next step` 都在框內），停至少 5 秒，對齊旁白 "shows exactly what it checked, and hands the decision back to a human"。
  - 再拉回 K0（800ms），停到 2:12，對齊 "No made-up root cause, no work order"：畫面上看得到 Line 1 灰色虛線＋`No root cause found`、沒有任何機台變色、面板上沒有 `Create work order`。
  - 疊加：BL 短標語 `No evidence, no conclusion.`（拉回 K0 後出現，停到 2:11.7）。
- **旁白**：Now the harder test. What if nothing is actually wrong? Same five queries, on healthy data from Line 1. LineSleuth says "Insufficient evidence", shows exactly what it checked, and hands the decision back to a human. No made-up root cause, no work order. That's why a supervisor can trust it.
- **字幕**：`No evidence, no conclusion.`
- **音效／音樂**：灰卡出現的瞬間音樂抽掉約 1 秒（留白），再輕輕回來。這是全片的情緒重點。

#### S10　Built on Google Cloud（2:12–2:29）Slide 7、F3

- **畫面**：簡報頁 Slide 7 的架構圖（Browser / Phone → Cloud Run → Vertex AI Gemini、DuckDB 示範資料（可換 BigQuery） → Cloud Logging），使用 Google Cloud 官方產品圖示。
- **動作**：依旁白順序逐一點亮產品圖示。選做：插入 3 秒 Cloud Logging 畫面，顯示和 S05 同一個 `query_id` 的紀錄（專案 ID 要遮掉；v0.3 改成實心色塊，不用馬賽克，見 7.5）。
- **畫面執行（Dana）**
  - 素材：`s10-architecture`（Slide 7 影片版，版面見 7.4），一張「全部變暗」的底圖＋每個方塊「點亮」狀態各一張透明 PNG。
  - 版面：同 Slide 7，拿掉底部 4 個 chip 和註腳（旁白沒講，17 秒內也沒人讀得完）；四個 Google Cloud 方塊左側加官方產品圖示。Cloud Run 副標在部署區域查證前只寫 `UI + API`，查證後才加 `asia-southeast1` `[to verify]`。有回歸分數時，底部放一條 `Regression set: {score}/10 known root causes` `[to measure]`（分數用綠色，見 7.3）。
  - 動作：開場所有方塊 35% 不透明，`Browser · Phone` 是 100%。旁白唸到 `Cloud Run`、`demo data`、`Gemini on Vertex AI`、`Cloud Logging` 時，對應方塊和連過去的箭頭亮到 100%（300ms）。全部亮完就靜止，不推近。
  - 選做 Cloud Logging 插入（3 秒）：旁白唸到 Cloud Logging 時，在頁面上疊一張截圖卡（寬 1400、深色外框，和簡報的截圖框同樣式；後面的頁面壓暗 60%）。截圖只裁 log 那一列，`query_id` 加琥珀重點框；專案 ID、專案編號、服務帳號、IP 全部用實心色塊蓋掉。Cloud Console 是白底，截圖只裁需要的那一小塊，不要整頁白畫面入鏡。
  - 疊加：無，`Built on Google Cloud` 就是頁面標題。
- **旁白（有分數版）**：It all runs on Google Cloud: Cloud Run in Singapore, demo data in DuckDB that can be swapped for BigQuery, Gemini on Vertex AI with function calling, and Cloud Logging for every query. We retest every prompt change on ten known cases. Score: ten out of ten.（實測 10/10，出處 `docs/qa/runs/README.md`；10/8 雲端驗證若不同以新值為準）
- **旁白（無分數替代）**：同上，但刪掉最後一句 "Score: … out of ten."
- **Sandy 註**：`We rerun ten known root causes` 聽起來像在「重跑根因」，改成 `retest every prompt change on ten known cases`，意思比較清楚。有分數版約 41 字（16.4 秒），超過「比秒數短 1–3 秒」的原則，請 Paula 決定要刪哪幾個字；我建議不要刪 `with function calling` 和 `Cloud Logging`，Google Cloud 評審最在意這兩個。
- **字幕**：`Built on Google Cloud`；有分數時另加 `Regression set: {score}/10 known root causes`
- **音效／音樂**：音樂穩定，不加音效。
- **備註**：部署區域要以實際部署設定為準（`deploy.md`）；模型名稱不要唸，只說 "Gemini"（同 `pitch-deck.md` Slide 7 的規則）。

#### S11　服務對象與下一步（2:29–2:47）Slide 8／9／10 合成頁

- **畫面**：一張合成簡報頁，分三塊：
  - 上方：「我們服務誰」客群卡 `Small contract manufacturers · Southeast Asia & Taiwan · No MES · Excel + PLC CSV`，旁邊放簡單的區域地圖（台灣＋東南亞，不畫產能移轉箭頭）。
  - 中間：`Onboarding fee + per line / month`（**不放金額**）。
  - 下方：越南文工單示意圖，標 `Concept — not in prototype`。（v0.3 Dana：預設改成語言 chip，示意圖要有越南語母語者校對過才用，見 D-7）
  - 改用「對比版」旁白時，上方才改成兩欄：左 `Built for plants that run MES`，右放我們的客群。**不放競品名稱或 logo，不用 ✗／✓，也不用紅綠配色**；兩欄字級相同，只把 LineSleuth 欄標成琥珀色（見 S-2）。
- **動作**：三塊依旁白順序出現。
- **畫面執行（Dana）**
  - 素材：`s11-default`（預設版）或 `s11-compare`（對比版），各自是一張底圖＋下排兩張卡各一張透明 PNG。版面座標見 7.4。
  - 標題列：小標 `WHO WE SERVE`，標題 `For plants that run on Excel, not MES.`。這一句就是本鏡的短標語，排在頁面上，不另外疊一層。
  - 上排（預設版）：左邊點陣地圖卡（只畫陸地的點，不畫國界、海域線、其他國名；Vietnam、Thailand、Malaysia、Taiwan 四個琥珀點＋標籤，和 Slide 3 的四個地區一致）；右邊客群卡三行：`Small contract manufacturers`／`Southeast Asia & Taiwan`／`No MES · data in Excel sheets and PLC CSV exports`。
  - 上排（對比版）：拿掉地圖，改成等寬兩張卡。左卡灰色小標 `INDUSTRIAL AI PLATFORMS`＋`Built for plants that run MES`；右卡琥珀小標 `LINESLEUTH`＋上緣 4px 琥珀線＋`Built for plants with no MES`／`Data in Excel and PLC files`＋四個地區 chip。兩卡同大小、正文同字級。
  - 下排（兩版相同）：左卡 `HOW THEY PAY`／`Onboarding fee + per line / month`（不放金額）；右卡 `NEXT`／語言 chip `EN`（實線，下方小字 `In prototype`）、`VI`、`TH`（虛線）＋小字 `Vietnamese and Thai work orders · not in prototype yet`。
  - 動作：上排和標題 2:29 就在；`HOW THEY PAY` 卡在旁白唸到 "They pay" 時出現；`NEXT` 卡在唸到 "Next:" 時出現（淡入＋上移 8px，300ms）。不推近。
  - 出點：2:47，300ms 交叉淡化到 S12。
- **旁白（預設）**：LineSleuth is built for small contract manufacturers in Southeast Asia and Taiwan, where there's no MES and the data lives in Excel and PLC files. They pay an onboarding fee, then a monthly fee per line. Next: Vietnamese and Thai work orders.（42 字，約 16.8 秒）
- **旁白（對比版，Sandy 查證後才用）**：Industrial AI platforms are built for plants that already run MES `[to verify]`. We're for the small factories that don't, with data in Excel and PLC files. They pay an onboarding fee, then a monthly fee per line. Next: Vietnamese and Thai work orders.（42 字，約 16.8 秒）
- **字幕**：`For plants that run on Excel, not MES.`
- **音效／音樂**：音樂開始往結尾收。
- **備註**：這一鏡只講產品和商業模式，不講「我們在找什麼」，所以不會變成 Ask。
- **Sandy 註**
  - **要不要放、放多長**：要放，一鏡 18 秒就夠。書面評審看不到 Q&A，影片如果沒講「誰付錢、怎麼付」，看起來就只是技術 demo；但片長的主力還是要留給可運作的原型。原稿 36 字剛好塞進 16 秒；加上地區和「誰付錢」之後變成 42 字，所以延長 2 秒。
  - **收費只講結構**（導入費＋每條產線月費），不講金額、回本月數、「比停線損失便宜」，這些都還是 `[pending interviews]`。`They pay` 的主詞就是工廠，讓評審一聽就知道誰付錢。
  - **差異化的主戰場不在這一鏡**：和一般 chatbot 的差別（固定查詢、原始列可回查、灰卡）S04、S05、S09 已經用畫面證明；這裡只補「客群不同」。原稿的 `Industrial AI platforms serve big plants with MES` 是在描述別人，還沒查證，而且 Google MDE 也會被一起算進去，所以預設版只講我們服務誰，不描述別人。
  - **不講 "China plus one"**：來源還是 `[to verify]`，而且至少要 4 秒才講得清楚，留給現場 pitch Segment 7。JAPAC 故事靠 S01 的 `Southeast Asia`、這一鏡的地區和越南文／泰文工單就夠了。

#### S12　結尾字卡（2:47–2:55）

- **畫面**：全幅字卡，深色底、琥珀色重點、Arial／Calibri（和簡報一致；v0.3 由 Inter 改，理由見 D-6）：
  - `LineSleuth`
  - `Every conclusion backed by evidence.`
  - `Hung Che Nick Lai · hongchelai@gmail.com`
  - `Live prototype: [Cloud Run URL]`＋QR code `[佔位]`
  - 小字：`Simulated plant data · AI Builder Cup 2026`
  - 如果正式隊友已經確定，加一行 `Team: [registered members]`
- **動作**：字卡淡入後靜止 5 秒以上，讓評審有時間掃 QR 或抄網址。
- **畫面執行（Dana）**
  - 素材：`s12-end`（結尾聯絡卡，版面見 7.4）。
  - 動作：從 S11 300ms 交叉淡化進來後完全靜止，一直到片尾。最後一格就是這張卡，不淡出成黑畫面：評審按暫停或播完停住時，看到的就是聯絡方式和 QR。
  - QR 只放公開的 prototype 網址，**絕對不能**帶 `?key=`。10/15 換成正式網址後，用手機實際掃一次（成片全螢幕播放、YouTube 一般大小視窗各一次）。
- **旁白**：LineSleuth. Every conclusion comes with its evidence.
- **字幕**：無，字卡本身就是字幕。
- **音效／音樂**：音樂收尾，字卡出現 1 秒後淡出。

### 2.3 現場備援版（B）：和 live demo 逐格同步

- **內容**：兩個檔。`backup-main-90s.mp4` 是 `storyboard.md` 的五格；`backup-grey-30s.mp4` 是灰卡加演。和繳交版用同一場錄影的素材。
- **不剪、不變速、無旁白、無音樂**。講者照 `pitch-script.md` 繼續講；caption 沿用 `storyboard.md` 的錄影版字幕。
- 需要挑一次第 ③ 格在 45 秒內跑完的 take。如果 Quinn 實測的中位數超過 45 秒 `[to measure]`，備援版改成「剪等待＋標示」，並回頭調整 `pitch-script.md` 的秒數。
- 角落放小字 `Recorded on the deployed app · {date}`；切換時講者補一句，讓評審知道這是錄影（見開放問題 S-4）。
- 視覺（Dana）：全片 K0 全景，不推近（要和現場 live demo 看起來一樣）。角落小字用 7.5 的「小標示」樣式，放 BL 下層，內容合併成一行 `Recorded on the deployed app · {date} · Simulated plant data`，全程顯示；caption 用 7.5 的短標語樣式，放 BL 上層。第 ⑤ 格的手機畫面用 7.10 的外框縮成 0.8 倍，放右下（右緣 x 1824、下緣 y 1026），只會蓋到 modal 後面的遮罩區。

| 格 | 檔案時間 | 畫面 | 對應 pitch-script 段落 |
|---|---|---|---|
| ① | main 0:00–0:10 | Line 2 紅燈、Downtime | 1（尾段） |
| ② | main 0:10–0:15 | 按 Investigate、聚焦 L2-M3 | 2 |
| ③ | main 0:15–1:00 | 證據卡＋sparkline；約 0:40 點開原始列 | 3 |
| ④ | main 1:00–1:15 | 結論卡＋CV-2 高亮 `ROOT CAUSE` | 4 |
| ⑤ | main 1:15–1:30 | 工單 QR＋手機畫面（右下角疊圖）＋before/after 卡 | 5 |
| 灰卡 | grey 0:00–0:30 | 按 `2` → `Investigate Line 1` → 灰卡 | 6 |

- 嵌進簡報：Slide 5 放 main，Slide 6 放 grey，一鍵就能切換；檔案存在**筆電本機**和 USB 各一份，不用雲端串流（`test-plan.md` §6）。
- 上表的格時間碼另外印給 driver，方便直接拖到第 ④ 格。

### 2.4 社群短版（C，30 秒，選做）

| 秒 | 畫面 | 燒入字幕 | 裁切（Dana，從 A 版母帶裁 1:1，座標為 1920×1080 來源） |
|---|---|---|---|
| 0–3 | L2-M3 紅燈、Downtime 在跳 | `3 a.m. Line 2 stops.` | 左欄 1080×1080（x 20–1100），1.0 倍；banner 和整張產線圖都在框內。右上加小標示 `Simulated plant data`（避開下方字幕區） |
| 3–6 | 按 Investigate、聚焦 L2-M3 | `One click. No prompt.` | 810×810，同時框到 `Investigate` 和 L2-M3（約 x 300–1110、y 40–850），1.33 倍 |
| 6–15 | 證據卡 sparkline 快剪（標 `WAITING TIME CUT`） | `Every number traces back to the data.` | 810×810，約 x 1100–1910、y 96–906：面板表頭的 `Elapsed` 和最新一張完整卡都在框內（`WAITING TIME CUT` 要指得到 `Elapsed`），1.33 倍 |
| 15–20 | CV-2 高亮、`ROOT CAUSE`、結論卡 | `Root cause found. With evidence.` | 前 2.5 秒 720×720 以 L2-M3 為中心（1.5 倍）；後 2.5 秒 810×810 以結論卡為中心 |
| 20–26 | 灰卡＋Line 1 灰色虛線 | `No evidence? No guess.` | 前 3.5 秒 810×810 以灰卡為中心；後 2.5 秒左欄 1080×1080（Line 1 灰色虛線＋徽章） |
| 27–30 | 片尾停在 PPT 封面（`docs/pitch/LineSleuth-demo.pptx` 第 1 頁），靜止到最後一格，不淡出成黑畫面 | 無（封面本身） | 不裁切：16:9 封面置中，上下補 #0F1115 底色（letterbox） |

- **9/24 第三次會議定案（Paula 同步）**：C 版片尾改成停在 PPT 封面，取代原本的結尾字卡 `c-end-1080`。C 版的格數、時間碼、素材來源（01 生成圖標「示意」、05 真手機實拍、其餘真錄屏）以 `docs/pitch/storyboard-30s-image-prompts.md` v0.2 為準；本表只保留各段的 1:1 裁切位置供參照。A 版 S12 結尾字卡不變。
- 只用音樂和燒入字幕；不出現任何未驗證數字，也不出現 before/after 數字。
- 畫面從母帶裁切平移，不另外錄窄版面（D-5 已定）。每一段只取一個大元素特寫，字交給燒入字幕（樣式見 7.6 C 版）。裁切段落之間一律硬切；同一段內不做推近。

### 2.5 v2 沒有上線時的替代畫面

錄影前（10/13）v2 若有任何一項還沒上線，就用下表替代，不要為了影片延後錄製。

| v2 項目 | 用到的鏡頭 | 替代方式 |
|---|---|---|
| ① sparkline | S04、S09、C 版 | 用 v1 卡片（只有數值）；旁白不變；後製推近到數值 |
| ② CV-2 高亮＋`ROOT CAUSE` | S06 | 用 v1 的 `CV-2` 變紅（`is-fault`）；後製加琥珀外框＋`ROOT CAUSE` 標籤（7.5「後製根因標籤」，和 v2 同一個樣子），不用箭頭、不用紅色標註（v0.3 Dana 改：紅色只代表停線） |
| ③ 窄螢幕 | C 版 | 從 1080p 母帶裁切 |
| ④ before/after 卡 | S08、B 版 ⑤ | 後製字卡：只放這次 take 畫面上的 `Elapsed`（標 `This run`）；before 的規則同第 4 節。版型用 7.4 數字卡，不做空白的 before 格 |
| 聚焦縮放 | S03、S06 | 後製推近代替 |

---

## 3. 灰卡「Insufficient evidence」入鏡規則

灰卡是我們的信任賣點（PRD F6、會議共識），三個版本都要有。

| 規則 | 原因 |
|---|---|
| 繳交版給它 26 秒，是只次於證據卡的長鏡頭 | 評審最常質疑「AI 會不會亂掰」，這一鏡直接回答 |
| 必須是真的在正常資料上跑出來的結果，不能用設計稿或截圖 | 灰卡是 Gemini＋伺服器規則真的判斷出來的；假的就失去意義 |
| `Checked` 清單要完整入鏡並停留 ≥ 4 秒 | 「查了什麼」比「沒找到」更有說服力 |
| 要拍到「沒有 `Create work order`、沒有機台變色」 | 證明它不只是換個顏色，而是真的不下結論 |
| 旁白要講 "hands the decision back to a human" | 呼應 Quinn 的「一鍵放大錯誤」顧慮：人仍然在迴路裡 |
| 灰卡出現時音樂留白 1 秒 | 用聲音標出這是重點 |

---

## 4. 未驗證數字的處理

| 數字 | 出現在 | 標記 | 有數字時 | 預設（無數字）版本 | 誰提供 | 最晚 |
|---|---|---|---|---|---|---|
| 調查時間「約 40 分鐘」 | S02、S08 | `[pending interviews]` | 旁白＋字幕帶出數字；before/after 卡顯示 before | S02 無數字句；S08 只講 after 或用完全無數字句 | Sandy（訪談）、Felix（數字表） | 10/15 |
| 每小時停線損失 X | S02 | `[pending interviews]` | 只能用受訪者的原話 | "every minute costs money" | Sandy、Felix | 10/15 |
| 調查秒數（取代舊的「90 秒」） | S08 | 已實測：中位數 12.6 秒（`docs/qa/runs/README.md`） | S08 用這次 take 的實測 `Elapsed`，並符合「不低於中位數」 | 完全無數字句 | Quinn（10/8 雲端再驗） | 10/16 |
| 回歸集分數 | S10 | 已實測：10/10（`docs/qa/runs/README.md`） | "Score: ten out of ten." | 刪掉那一句 | Quinn（10/8 雲端再驗） | 10/16 |
| 部署區域「Singapore」 | S10 | `[to verify]` | 照講 | 刪掉 "in Singapore" | 老闆（看部署設定） | 10/16 |
| 競品描述 | S11（影片一律不點名，S-2 已定） | `[to verify]` | Sandy 查完三家官網的公開定位後，才可以改用 S11「對比版」那一句（仍然不點名） | S11 預設版：只講我們服務誰，不描述別人 | Sandy | 10/15 |

10/16 剪輯前沒有拿到數字的，一律用預設版本，不等。

---

## 5. 製作方式建議

### 5.1 錄影

| 項目 | 建議 | 備註 |
|---|---|---|
| 桌面畫面 | **Playwright 自動化錄製，1920×1080**：固定視窗大小（viewport 1920×1080，縮放 1.0），腳本照本文件的點擊順序操作，同一個動作可以穩定重錄。先錄 10 秒測試畫質；文字不夠清楚就改用 OBS 錄 Playwright 開的有頭瀏覽器（需要 ≥ 1920×1080 的螢幕，或外接螢幕） | 自動化不受筆電螢幕解析度限制，也能順便輸出 pitch deck Slide 5 要用的 5 張分鏡截圖 |
| 游標 | Playwright 不會錄到系統游標，所以錄影時由腳本注入一個假游標和點擊波紋，**只存在錄影腳本裡，不改 app 程式碼** | 備案：老闆手動操作，用 OBS 錄（游標自然會入鏡） |
| 瀏覽器狀態 | 錄影用的瀏覽器事先開好簡報者模式（manual §3.8），避免碰到速率限制；**金鑰網址不能入鏡**，所以要先在畫面外設好 cookie，錄影時不顯示網址列 | 關掉系統通知、書籤列、擴充功能圖示 |
| 手機畫面 | **首選：手機內建螢幕錄影**，錄「相機掃 QR → 開連結 → 工單頁捲動」，剪輯時放進手機外框。選做：2 秒實拍手拿手機掃筆電螢幕的空鏡（手機亮度調高，避免摩爾紋）。**備案（模擬）**：Playwright 用手機尺寸（390×844）開 `/wo/{id}` 錄影 | 手機開勿擾模式，狀態列不能露出個人資訊；不管用哪種，都必須是同一次 take 的同一張工單（同一個 WO id）。這也回答了 `storyboard.md` D5：由老闆自己的手機錄 |
| take 數 | 主線、灰卡各錄 3 次，選一次沒有 `Cached`、第 ③ 格 ≤ 45 秒、`Elapsed` 不低於中位數的 | 記下每次 take 的 `query_id`、`Elapsed`、WO id |

### 5.2 旁白

- **首選：老闆本人英文錄音**。評審聽到的是創辦人本人的聲音，也和決賽現場由誰講一致。每一鏡錄成一個檔（48 kHz WAV），比較好對時間；安靜房間，嘴巴距離麥克風約一個拳頭，用手機錄音也可以。
- **備案：TTS**（例如 Google Cloud Text-to-Speech 的英文語音，和我們的 Google Cloud 故事一致）。費用應該很低，但**待 Felix 確認**。用 TTS 時，句子之間的停頓要手動調整，不然會聽起來很趕。
- 語速每分鐘約 150 字（每秒 2.5 字）；超過該鏡秒數就刪字，不要加快語速。

### 5.3 剪輯

- **首選：DaVinci Resolve（免費版）**，可以匯入／匯出 SRT、有響度表、多軌時間軸都有。
- **備案：Clipchamp**（Windows 內建），上手快、有自動字幕，適合 C 版。
- 老闆已經熟悉的剪輯軟體優先，比賽期間不要為了影片學新工具。
- 每一個「剪掉等待」的剪接點都要加 `WAITING TIME CUT` 標示（v0.3 改名，樣式見 7.5；繳交版與 C 版才有，B 版沒有剪接）。

### 5.4 字幕（SRT）

- 英文，內容**逐字照旁白**；每行 ≤ 42 個字元、每則最多 2 行、每則顯示 1–7 秒。
- 檔名 `linesleuth-submission.en.srt`；上傳平台支援 CC 就另外上傳 SRT，不支援就燒進畫面。
- SRT 裡不能出現任何 `[pending interviews]`、`[to measure]`、`[to verify]`、`{…}`，出現就是還沒處理完。
- 格式範例（時間碼要照剪好的成片重新對）：

```
1
00:00:00,500 --> 00:00:04,200
It's 3 a.m. at a small contract factory.

2
00:00:04,200 --> 00:00:08,600
Line 2 just stopped, and the night supervisor
is on their own.
```

### 5.5 輸出規格

| 版本 | 規格 | 聲音 |
|---|---|---|
| A 繳交版 | MP4（H.264），1920×1080，30 fps | AAC 48 kHz；整體響度約 −14 LUFS，峰值 ≤ −1 dBTP；音樂比旁白低約 18 dB |
| B 備援版 | MP4（H.264），1920×1080，30 fps，兩個檔 | 無音軌 |
| C 社群版 | MP4（H.264），1080×1080（或 1080×1920） | 只有音樂，靜音播放也看得懂 |

影片檔**不要放進 repo**，母帶和成品存在 Drive 或外接硬碟。

### 5.6 素材清單

| # | 素材 | 誰準備 | 期限 |
|---|---|---|---|
| 1 | Cloud Run 部署版（`gemini` 模式、DuckDB 示範資料、v2 UI），記下版本 | 老闆（Eddie 規格） | 10/13 |
| 2 | 產品名定案（PRD Q7）；錄完之後改名就要重錄 | 老闆 | 10/13 |
| 3 | Playwright 錄影腳本（1080p、假游標、點擊順序照本文件、同時截 5 張分鏡圖） | 老闆（Eddie 規格） | 10/13 |
| 4 | 主線、灰卡各 3 個 take，含原始列點開畫面；take 紀錄表（`query_id`、`Elapsed`、WO id） | 老闆 | 10/14 |
| 5 | 手機螢幕錄影（掃碼 → 工單頁），和主線 take 是同一張工單 | 老闆 | 10/14 |
| 6 | 簡報頁 PNG 1920×1080（分層）：Slide 2 影片版、Slide 7 影片版、S11 合成頁（預設版＋對比版）；原話卡只在拿到授權後做 | Dana（`pitch-deck.md` 視覺；清單見 7.11） | 10/6 初稿、10/13 定稿 |
| 7 | 字卡與圖層：短標語、lower-third、小標示、`WAITING TIME CUT` 標示、重點框、數字卡、結尾字卡（含 QR 佔位）、C 版結尾卡、手機外框 | Dana（清單見 7.11） | 10/6 初稿、10/13 定稿 |
| 8 | Google Cloud 官方產品圖示（照品牌規範使用，不改色、不變形） | Dana | 10/6 |
| 9 | 背景音樂 1 首＋音效（點擊、tick、chime、掃碼嗶聲），附授權紀錄 | 老闆 | 10/13 |
| 10 | 旁白錄音（每鏡一檔）或 TTS 輸出 | 老闆 | 10/15 |
| 11 | 最終數字：40 分鐘、X、回歸分數、實測中位數；沒有就走預設版本 | Sandy、Felix、Quinn | 10/15–10/16 |
| 12 | SRT、影片縮圖（1280×720，上 YouTube 時用） | 老闆 | 10/16 |

### 5.7 分工與時程

和 `roadmap.md` 的慣例一樣：各角色負責規格和檢查，實際錄影、錄音、剪輯都由老闆動手。

| 誰 | 負責 |
|---|---|
| Paula | 本文件、旁白稿、第 4 節數字規則；10/16 對照成片逐鏡檢查 |
| Dana | v2 畫面驗收、字卡／圖層／手機外框、剪接標示樣式、S11 合成頁 |
| Eddie | 錄影腳本規格；錄影期間凍結部署版本，不要在錄影當天上新版 |
| Sandy | 旁白用字（S02、S11）、要不要點名競品、受訪者原話授權、C 版的發布平台 |
| Felix | 40 分鐘與 X 的數字來源；TTS 費用 |
| Quinn | 錄影前檢查（沒有 fixture 黃條、底列 `Agent: <model> · data: bigquery`、沒有 `Cached`、金鑰沒入鏡）；成片檢查（標記全部清空、after 數字＝畫面 `Elapsed`、剪接處都有標示、片長在上限內、QR 可以掃）；保存採用 take 的 Cloud Logging 紀錄 |
| 老闆 | 錄影、旁白、剪輯、上傳、繳交 |

| 日期 | 事項 |
|---|---|
| 10/1 | Dana 回覆第 6 節開放問題 → 本文件出 v0.3（Sandy 已在 v0.2 回覆） |
| 10/8 | 旁白稿鎖定（數字除外） |
| 10/13 | Agent＋三畫面在 Cloud Run 串通（roadmap 里程碑），當天先試錄一次，檢查時間和 1080p 的可讀性 |
| 10/14–10/15 | **正式錄影**（A、B、C 共用素材）、錄旁白 |
| 10/16 | 剪輯、SRT、Quinn 成片檢查；B 版放進筆電和簡報 |
| 10/17 | 上傳並繳交 |
| 10/18 之後 | C 社群版（選做） |

**需要老闆決定**：`roadmap.md` 目前把備援錄影排在 10/16，那天還要部署和定稿文案，太擠。我建議把正式錄影提前到 10/14–10/15，10/16 只剪輯和補錄。老闆同意後我再更新 roadmap。

---

## 6. 開放問題（請 Sandy、Dana 在 10/1 前回覆）

### 給 Sandy

| # | 問題 | 我的建議 | Sandy 回覆（v0.2） |
|---|---|---|---|
| S-1 | 旁白要用老闆本人的聲音還是 TTS？ | 本人。評審看得出是不是創辦人自己講的；口音不是問題，講得慢、講清楚就好 | **同意用本人。** 評審也在看「這個人能不能把產品賣出去」，創辦人自己講最有說服力，也和 12/4 決賽是同一個聲音。先試錄 S01、S09 給我聽，哪裡卡住就刪字，不要換 TTS。TTS 只在錄音品質救不回來（噪音、時間不夠）時才用 |
| S-2 | S11 要不要點名 Siemens／Cognite／Google MDE？ | 影片裡不點名。影片是永久紀錄，而競品描述目前全部是 `[to verify]`；現場 pitch 再照 `pitch-script.md` 點名 | **同意不點名**，再補三個理由：Google MDE 是主辦方自家產品，放在影片裡和其他平台並列，容易被看成在比較；18 秒不夠把三家講得公道；我們真正的差異（固定查詢、可回查、灰卡）S04、S05、S09 已經用畫面證明。S11 預設只講我們服務誰；對比句要等我 10/15 前查完三家官網才用。點名留給現場 pitch Segment 7 和 `judge-qa.md` Q1–Q3 |
| S-3 | 10/15 前有沒有機會拿到受訪者**授權**的原話？ | 有的話 S02 改用原話字卡，比數字更有力 | **目前還沒有，不保證拿得到。** 訪談目標是 9/30 前做 2–3 場（`docs/sales/interview-guide.md`），但訪談表只問了「比賽簡報」的引用授權。影片是公開的永久紀錄，我會另外補問「公開影片」並留文字紀錄。用的條件：原話 15 字以內；原文不是英文時，英文翻譯要給對方看過，字卡加小字 `Translated from Mandarin`（依實際語言改）；稱呼用對方選的（例：`Plant manager, contract manufacturer, Vietnam`）。10/13 前沒拿到書面確認就用預設句，不等 |
| S-4 | 現場切到備援錄影時，角落標 `Recorded on the deployed app`，講者補一句 "Network's slow, so here's a recording of the same run from our deployed app." 會不會削弱說服力？ | 要講。這樣 `judge-qa.md` Q12「是不是寫死的」的回答才站得住 | **同意要講，而且要講得很自然。** 評審都知道現場網路會出狀況，藏起來再被問到才會扣分。句子縮短成 "The network's slow, so here's the same run, recorded on our deployed app." 只講一次、不道歉，接著照稿講。Q&A 時網路如果恢復，就主動說 "Happy to run it live now."（呼應 Q12） |
| S-5 | C 社群版發在哪裡（LinkedIn？）、1:1 還是 9:16、什麼時候發（繳交後，或等決賽名單公布後）？ | LinkedIn、1:1、繳交後；先確認官方對公開發布沒有限制 | **LinkedIn、1:1，繳交截止（10/18）之後才發**，也要先確認官方沒有限制公開發布。我們的潛在買家（工廠主管、老闆）和 Google Cloud 的人都在 LinkedIn 上，和 `judge-qa.md` Q16 的通路一致。9:16 先不做。如果進決賽，名單公布後再發一次。貼文文字由我另外寫，會標明模擬資料，不放任何未驗證數字 |

### 給 Dana

| # | 問題 | 我的建議 | Dana 回覆（v0.3） |
|---|---|---|---|
| D-1 | `ui-v2-spec.md` 什麼時候定稿？影片需要用到 sparkline、CV-2 高亮、before/after 卡、聚焦縮放；10/13 前沒上線的，2.5 節的替代畫面可以接受嗎？ | 10/13 前沒上線就照替代畫面錄，不延後錄影 | **規格已經定稿（9/24 版凍結，之後只修錯、不加功能），現在卡在實作；替代畫面可以接受，但我改了兩處。** app 目前還沒有任何 v2 項目（`app/static/app.js` 裡沒有小圖、Recap、聚焦拉近）。影片需要的優先順序：① sparkline（S04、S09 兩個最長的鏡頭都靠它）> ② 根因亮燈（S06）> ④ Recap（S08）> 聚焦拉近（可以砍，用後製推近代替）。**有一個時程衝突要老闆決定**：`ui-v2-spec.md` §9 把小圖（第 4、5 項）排在「10/16 部署前」，但正式錄影在 10/14–15。要讓影片用到 sparkline，就要請 Eddie 把 4、5 提前到 10/13，排在 7、8（拉近、動畫）前面；做不到就照 2.5 錄。2.5 改的兩處：② 不用紅色箭頭，改用琥珀外框＋`ROOT CAUSE` 標籤（紅色只代表停線）；④ 改用 7.4 的數字卡。10/13 試錄時，我照 `ui-v2-spec.md` §8 的 A1、B2–B6、C1、C5、E1–E3 在 1920×1080 驗收一次。 |
| D-2 | before 未驗證、卡片只顯示 after 時，版面會不會看起來像少了一半？需不需要加文案（例如 `This run`）？ | 只顯示 after，加 `This run`，不放空白的 before 格 | **app 裡的 Recap 不加 `This run`，也不藏 Before 列；只有後製替代卡才用 `This run`。** 影片錄的是真實的 Recap：沒設基準時，Before 列本來就是 `—`＋`Not yet measured for this plant.`，兩邊都不畫長條；After 的標籤 `LineSleuth, this investigation (measured)` 意思已經等於 This run。這一列不是「少了一半」，而是「我們不亂報數字」的證據，和 S09 灰卡是同一個態度；兩列左右對齊，版面不會缺角。後製只做 1.0→1.1 緩推，中心對準 After 列，整張卡保持在框內。v2 Recap 沒上線、改用後製數字卡時，才照你的建議只放 after＋`This run`，也不做空白的 before 格：後製自己做一個空格，看起來像我們在挖洞。 |
| D-3 | 繳交版剪掉等待時間的標示（`Trimmed · real time in Elapsed`）要用什麼樣式、放在哪裡？還是你寧可全程不剪、改刪旁白？ | 剪掉並加標示；全程不剪兩次調查會吃掉超過一半片長 | **同意剪掉並標示；標示改名，也改位置。** 文字改成兩行：`WAITING TIME CUT`／`Elapsed shows the real time ↑`。原本的 `Trimmed · real time in Elapsed` 對非母語評審太擠，也看不出 Elapsed 是畫面上哪個東西。位置不放畫面右上角（S04 的構圖裡右上角正好就是 `Elapsed`，會把它蓋掉），改成貼在 `Elapsed` 正下方、右緣對齊，箭頭指著它，讓觀眾把「剪掉」和「真實時間」連起來。每個剪接點顯示 2 秒；兩個剪接點相隔不到 4 秒就連著顯示，不要一閃一閃。剪接一律硬切，不用交叉淡化（淡化會疊出兩個 `Elapsed` 數字）。樣式見 7.5；本文件裡的舊名我都換掉了。 |
| D-4 | 在 1080p 下，sparkline 和原始列看得清楚嗎？後製放大會不會和 app 本身的聚焦縮放疊在一起，變成「雙重縮放」？ | 產線圖用 app 的聚焦縮放，面板才用後製放大，兩者不要同時發生 | **要讀的字，在成片上等效至少 20px；雙重縮放用「時間錯開」來解決。** 1080p 全景下 app 最小字是 16px，評審如果用一般大小的播放視窗看，會縮到 11px 左右，所以要讀的畫面一律推近：面板 1.25 倍（16→20px），原始列表格 14px 推 1.5 倍（→21px）。推近不想變糊，建議母帶用 2 倍像素錄（CSS 仍是 1920×1080，deviceScaleFactor 2，版面斷點不變，見 7.9）；做不到的話，推近上限 1.5 倍。同意你的原則，再加一條硬規則：app 自己的鏡頭在動的時候（按 Investigate 後 +150～850ms、灰卡出現後 0～1.1 秒），後製鏡頭不准動，等 app 停了才推。後製推近時畫面裡照樣看得到 app 的聚焦狀態，這不算雙重縮放，只要兩者不同時動就好。構圖預設見 7.7。 |
| D-5 | v2 窄螢幕版面能不能直接拿來錄 1:1／9:16 的社群版，還是從 1080p 母帶裁切？ | 能直接錄就直接錄，字會比較清楚 | **不直接錄，從母帶裁切。** 1080×1080 的視窗落在 v2 的 M 斷點（兩欄、面板 420px），不是單欄版面；而且社群影片在手機上大概只有 360px 寬，不管用哪種錄法，app 的字都會縮成三分之一。真正有用的是「每一段只裁一個大元素的特寫」，要傳達的話交給燒入字幕。從母帶裁切還有兩個好處：不用多錄一場；WO 編號和 `query_id` 和繳交版是同一個 take。有 2 倍母帶時，裁切特寫也不會糊。各段裁切位置已經補在 2.4 表格。 |
| D-6 | 字卡、lower-third、`Trimmed` 標示、手機外框、結尾字卡、S11 合成頁，10/13 前能不能交？ | 樣式沿用 app：深色底、琥珀色、Inter 字體，不另外做新視覺 | **可以：10/6 出初稿，10/13 試錄後定稿。字體改成和簡報一致，不用 Inter。** 字卡、字幕、圖層一律用 Arial（標題、數字、字幕）＋Calibri（內文），顏色用 `docs/pitch/deck/build-deck.js` 的色票（和 `ui-spec.md` 是同一組 hex），字級＝簡報的 pt × 2（換算成 1080p 的 px）。理由：S02、S10、S11 本身就是從簡報匯出的頁面，字卡如果用 Inter，影片裡會同時出現三種字體；Inter 只留在 app 畫面裡，那是真實的產品。Windows 內建 Arial 和 Calibri，不用另外裝字型。深色底、琥珀強調、不另做新視覺，這部分同意。交付清單和檔名見 7.11。 |

### Sandy 追加給 Dana（v0.2 之後）

| # | 問題 | Dana 回覆（v0.3） |
|---|---|---|
| D-7 | S11 的區域地圖要怎麼畫？對比版的「中性兩欄」要怎麼排，才不會看起來像在打競品？ | **預設版左圖右文；對比版拿掉地圖，改成等寬兩欄。** 地圖用點陣風格：只畫陸地的點，不畫國界、海域線，也不標其他國名，只點亮 Vietnam、Thailand、Malaysia、Taiwan 四個琥珀點＋標籤（和 Slide 3 的四個地區一致）。這樣可以避開地圖邊界的政治爭議，也比寫實地圖好做；底圖用 Natural Earth（公有領域）的陸地資料自己轉成點陣，不用找授權。對比版兩欄：兩張卡同大小、正文同字級；左卡灰色小標 `INDUSTRIAL AI PLATFORMS`，右卡琥珀小標 `LINESLEUTH`＋上緣 4px 琥珀線（和結論卡同一個語彙）。差別只在小標顏色和那條琥珀線，沒有 ✗／✓、沒有紅綠、沒有 logo，左卡的字也不做淡化。對比版放不下地圖，地區改成右卡裡的四個地區 chip。另外我建議砍掉下方的越南文工單示意圖，改成語言 chip：`EN`（實線，現在就有）、`VI`、`TH`（虛線，下一步），旁邊小字 `not in prototype yet`。示意圖要有人校對越南文，錯一個字，在越南評審眼中比不放還糟；10/13 前如果有越南語母語者校對過，才換回示意圖（仍標 `Concept — not in prototype`）。版面座標見 7.4。 |
| D-8 | S02 如果拿到授權原話，原話字卡長什麼樣子？ | **一張卡只放一句原話，除了淡入不加任何動畫。** 版型見 7.4「原話卡」：左上一個琥珀大引號，原話用 Arial Bold 60px、最多 3 行，下面是 `— {對方選的稱呼}`（Calibri 34px，次要文字色）；翻譯過的再加一行 `Translated from Mandarin`（依實際語言改；Calibri 26px，muted 色）。原話整句一次出現，不做打字機效果；停留時間＝旁白唸完再加 1.5 秒。不放照片、公司名、logo，不改寫原話，連標點也照對方確認過的版本。原話裡如果有數字，那就是受訪者自己講的數字，照 S-3 的授權規則處理；稱呼本身就是出處，不另外加來源行。原話卡取代 Slide 2 影片版，檔案卡的疊入動畫就不用做。SRT 燒入時，這一段的字幕和卡上的字一樣，不重複燒（見 7.6）。 |

---

## 7. 影片視覺規格（Dana，v0.3）

適用 A 繳交版；B、C 版不同的地方寫在各小節。app 畫面本身不調色、不修改，錄到什麼就是什麼；這一節只規範「我們疊上去的東西」和「鏡頭怎麼拍」。

### 7.1 基本規格

| 項目 | 規格 |
|---|---|
| 成片解析度 | A、B：1920×1080（16:9）；C：1080×1080 |
| 影格率 | 30 fps（同 5.5）。時間軸影格率要等於桌面母帶的影格率，不做 25↔30 轉換，否則 app 的拉近、脈動、畫線動畫會抖。Playwright 內建錄影的影格率不一定是 30，10/13 試錄時用 `ffprobe` 確認；如果是 25，時間軸和成片都改成 25 fps |
| 母帶 | 建議 2 倍像素：瀏覽器 CSS 視窗仍是 1920×1080、deviceScaleFactor 2，錄成 3840×2160。版面斷點完全不變，推近到 1.5 倍也不會糊。做不到就錄 1920×1080，推近上限 1.5 倍 |
| 色彩 | sRGB／Rec.709；不套 LUT、不加濾鏡、不調飽和度。畫面顏色要和 app 實際顏色一樣，因為顏色本身有意義（紅＝停線、琥珀＝根因、灰＝證據不足） |
| 可讀性 | 成片上所有「要讓人讀」的字，等效至少 20px（以 1920×1080 計），app 畫面靠推近做到（7.7）；我們疊上去的字最小 22px。唯一例外是 S07 的手機畫面（7.10） |
| 字體 | 字卡、疊加層、字幕：Arial（標題、數字、字幕）＋Calibri（內文），和 `docs/pitch/deck/build-deck.js` 一致。app 畫面裡的 Inter 是產品本身，不動 |

### 7.2 安全框與版面區域（1920×1080）

| 區域 | 範圍 | 規則 |
|---|---|---|
| 動作安全框（93%） | x 67–1853、y 38–1042 | 從 pptx 匯出的簡報頁（邊界 86px）內容都在這裡面 |
| 標題安全框（90%） | x 96–1824、y 54–1026 | 我們疊上去的字和圖層全部要在這裡面 |
| 字幕保留區 | x 320–1600、y 870–1026 | 只給 SRT 燒入字幕或播放器 CC 用，其他圖層不准放；構圖時 app 的重點元件也不要落在這一區 |
| BL 左下資訊區 | 左下角錨點 (96, 846)，往上堆疊；寬 ≤ 1100 | 下層放小標示，上層放 lower-third 或短標語，兩層間距 12px。app 畫面的這一角通常是 Line 3 或產線圖左下角，是最不重要的區域 |
| TL 左上 | 左上角錨點 (96, 70) | 只有 S07 用（桌面畫面縮小後上方是空白） |
| `Elapsed` 下方 | 見 7.5 | 只放 `WAITING TIME CUT` |

- app 畫面本身可以滿版到邊：線上播放沒有 overscan，安全框只管我們疊上去的東西。
- 不放在畫面右上角：S04、S06、S09 的構圖裡，右上角就是面板表頭的 chip 和 `Elapsed`。
- C 版（1080×1080）：標題安全框四邊各 54px；燒入字幕區 y 760–960、左右置中；小標示放右上。

### 7.3 顏色 token

和 `build-deck.js` 的 `C` 物件、`docs/design/ui-spec.md` 的 token 是同一組 hex，不新增顏色。

| 簡報名／app 名 | Hex | 影片裡的用途 |
|---|---|---|
| `bg`／`--color-bg` | #0F1115 | 字卡底色；疊加層底框（85% 不透明） |
| `s1`／surface-1 | #171A21 | 字卡上的卡片、地圖卡、手機狀態列遮罩 |
| `s2`／surface-2 | #1F232C | 次層卡片、檔案卡、chip、分數條 |
| `s3`／surface-3 | #282D38 | 手機外框本體、陸地點、遮蔽用實心色塊 |
| `border` | #2E3440 | 裝飾用分隔線、卡片外框 |
| `borderStrong` | #4A5263 | 需要被看見的框（小標示外框、虛線 chip、截圖卡外框） |
| `text` | #E8EAED | 主要文字、字幕 |
| `text2` | #A3AAB8 | 次要文字、lower-third 第二行、受訪者稱呼 |
| `muted` | #8A93A3 | 來源小字、註記；最淡只到這個顏色 |
| `amber` | #F5A524 | 我們的強調：小標、短標語左側色條、重點框、根因、`Sleuth` |
| `red` | #F2555A | 只用在「停線」：S02 的 `03:00`。我們加的標註一律不用紅 |
| `green` | #3DD68C | 只用在實測數字（After 秒數、回歸分數） |
| `blue` | #5AA9FF | 只出現在 Slide 7 的 Google Cloud 方塊標題（沿用簡報）；疊加層不用藍，因為藍色在 app 裡代表「調查中／引用」 |
| `grey` | #B8BEC9 | 對比版左卡的小標 |

對比：主要文字在 #0F1115 上約 15:1，琥珀約 9.3:1，muted 約 6:1，都符合 WCAG AA。

### 7.4 字卡版型

共通：底色 #0F1115 滿版；字級＝簡報的 pt × 2（換算成 1080p 的 px）；左右邊界，從簡報匯出的頁面沿用簡報的 86px，影片專用的卡用 96px；除了 7.7 允許的淡入和逐塊出現，字卡上沒有其他動畫。

| 層級 | 字體 | 大小 | 顏色 | 對應簡報 |
|---|---|---|---|---|
| 小標（kicker） | Arial Bold，全大寫，字距 6px | 22px | amber | 11pt |
| 卡內小標 | Arial Bold，全大寫，字距 4px | 28px | muted（對比版左卡用 grey） | 14pt |
| 頁面標題 | Arial Bold | 68px | text | 34pt |
| 大數字 | Arial Bold | 160px | 依 7.3（實測 green、訪談 text） | 80pt |
| 超大時間 `03:00` | Arial Bold | 220px | red | 110pt |
| 卡片標題 | Arial Bold | 44px | text（價格結構用 amber） | 22pt |
| 內文 | Calibri | 36–40px | text／text2 | 18–20pt |
| 小字 | Calibri | 28px | text2／muted | 14pt |
| 最小（來源、註記） | Calibri | 24px | muted | 12pt |

**(1) 標題卡（簡報頁）**：S02 影片版、S10、S11 用。沿用簡報 `base()` 的位置：小標 (86, 65)、標題 (86, 108)，內容區從 y 274 開始；簡報底部的註腳區（y 1008）在影片版一律空著，因為標記不能入鏡。

- **Slide 2 影片版 `s02-problem`**
  - 左：`03:00`（220px red）在 (86, 187)；`Line 2 stops.`（Arial Bold 72px text）在 (86, 482)；`Excel sheets. PLC exports. Shift logs.`（Calibri 40px text2）在 (86, 648)。
  - 右：四張檔案卡，490×115、s2 底、1px border、圓角 14，位置 (1066, 230)、(1195, 360)、(1109, 504)、(1325, 634)；檔名 Calibri 32px text2，左內距 36px。
  - 拿掉：`X*`、`~40 min*`、`The night supervisor is alone` 三個 bullet 和註腳。
- **Slide 7 影片版 `s10-architecture`**
  - 方塊位置同簡報：`Browser · Phone` (86, 432)、`Cloud Run` (619, 432)，各 403×151；`Vertex AI Gemini` (1195, 266)、`DuckDB · demo data`（副標 `swappable for BigQuery`，同 Slide 7） (1195, 432)、`Cloud Logging` (1195, 598)，各 634×151。
  - 四個 Google Cloud 方塊：左內距 24px 放官方產品圖示 56×56，標題和副標往右移 80px。
  - 拿掉底部 chip 列和註腳。回歸分數條（只在有實測分數時）：(86, 828)，1748×86，s2 底，Arial Bold 36px：`Regression set: ` text＋`{score}/10` green＋` known root causes` text。
- **S11 合成頁 `s11-default`／`s11-compare`**
  - 標題列：小標 `WHO WE SERVE`；標題 `For plants that run on Excel, not MES.`。
  - 上排（y 274–700），預設版：
    - 地圖卡 (86, 274)，760×426，s1 底、1px border。點陣地圖：陸地點直徑 6px、間距 14px、s3 色；範圍約東經 92–125 度、北緯 0–27 度，等比例置中。四個地區點直徑 18px amber，外加 2px bg 描邊；標籤 Calibri 28px text。不畫國界、海域線，不標其他國名。
    - 客群卡 (886, 274)，948×426，s1 底：`Small contract manufacturers`（Arial Bold 44px text）／`Southeast Asia & Taiwan`（Calibri 36px amber）／`No MES · data in Excel sheets and PLC CSV exports`（Calibri 32px text2）。
  - 上排，對比版：
    - 左卡 (86, 274)，854×426，s1 底、1px borderStrong：卡內小標 `INDUSTRIAL AI PLATFORMS`（grey）＋`Built for plants that run MES`（Arial Bold 44px text）。
    - 右卡 (980, 274)，854×426，s1 底、1px border＋上緣 4px amber：卡內小標 `LINESLEUTH`（amber）＋`Built for plants with no MES`（Arial Bold 44px text）＋`Data in Excel and PLC files`（Calibri 36px text2）＋四個地區 chip（s2 底、圓角 8、Calibri 28px amber）。
    - 兩卡正文同字級；左卡不淡化；不放任何名稱、logo、✗／✓、紅綠。
  - 下排（y 740–960，兩版相同）：
    - 左卡 (86, 740)，854×220，s1 底：卡內小標 `HOW THEY PAY`＋`Onboarding fee + per line / month`（Arial Bold 44px amber，不放金額）。
    - 右卡 (980, 740)，854×220，s1 底：卡內小標 `NEXT`；語言 chip `EN`（s3 底、1px borderStrong 實線、Arial Bold 32px text，下方 Calibri 24px muted `In prototype`）、`VI`、`TH`（透明底、2px borderStrong 虛線、Arial Bold 32px text2）；小字 `Vietnamese and Thai work orders · not in prototype yet`（Calibri 28px muted）。
    - 如果改用越南文工單示意圖（D-7 的條件），就放在右卡裡取代 chip 列，標 `Concept — not in prototype`。

**(2) 數字卡**

- 用在：S08 替代卡（`This run`）；S02 有數字版（嵌在頁面裡，規則相同）；其他經第 4 節允許的數字。
- 版面置中：小標 y 300（22px amber）；大數字 y 360–540（160px）；說明 y 580（Calibri 40px text2）；來源 y 660（Calibri 28px muted）。
- 顏色：實測值（After 秒數、回歸分數）用 green；訪談得到的數字用 text；不用紅，也不用琥珀（琥珀留給「原因」和強調）。
- **來源行必填**，沒有來源行就不能做數字卡。實測值寫 `Measured by the server from Investigate to conclusion.`（和 Recap 同一句）；訪談數字寫 `Source: {MANUAL_BASELINE_SOURCE}` 的同一句話。
- 不做數字跳動；整張卡淡入後靜止。
- S08 替代卡內容：小標 `THIS RUN`；數字 `{after}`（格式同 Recap：`{s} s` 或 `{m} min {s} s`，必須等於畫面上最後的 `Elapsed`）；說明 `From one click to a root cause`；來源 `Measured by the server from Investigate to conclusion.`。

**(3) 原話卡 `s02-quote`**（D-8）

- 左對齊 x 96。琥珀引號 `“`（Arial Bold 180px）在 (96, 170)。
- 原話：Arial Bold 60px、行高 76px、text 色，從 y 330 開始，寬 ≤ 1500px、最多 3 行（15 字以內大約 2 行）。用對方確認過的原文或授權譯文，一字不改。
- 稱呼：原話下方 48px，`— {對方選的稱呼}`（Calibri 34px text2）。
- 翻譯註記（有翻譯才放）：稱呼下方 12px，`Translated from {language}`（Calibri 26px muted）。
- 不放照片、公司名、logo；不做打字機效果；整張淡入 300ms 後靜止，停到旁白唸完再加 1.5 秒。

**(4) 結尾聯絡卡 `s12-end`（1920×1080）**

- 置中排列，由上到下：
  - `Line`＋`Sleuth`：Arial Bold 108px，`Line` 用 text、`Sleuth` 用 amber（同簡報封面），y 200。
  - `Every conclusion backed by evidence.`：Calibri 56px text2，y 350。
  - 聯絡卡：(310, 480)，1300×320，s1 底、1px border、圓角 20。
    - 左側文字從 x 350 開始：`Hung Che Nick Lai`（Calibri Bold 40px text）／`hongchelai@gmail.com`（Calibri 36px text2）／`Live prototype: [Cloud Run URL]`（Calibri 32px text2）；正式隊友確定後加 `Team: [registered members]`（Calibri 28px text2）。
    - 右側：白底 QR 方塊 280×280（QR 240＋20px 留白），放在 (1290, 500)；QR 黑色 #000000，容錯等級 M。網址確定前用佔位方塊（1px borderStrong 虛線框，中間 `QR`）。
  - 小字 `Simulated plant data · AI Builder Cup 2026`：Calibri 24px muted，置中，y 960。
- 不放 Ask，不放任何未驗證數字。
- C 版 `c-end-1080`（1080×1080）：wordmark 96px（y 170）；tagline Calibri 44px（y 300，可以折兩行）；QR 320×320 置中（y 420）；網址 Calibri 28px（y 770）；`Hung Che Nick Lai · hongchelai@gmail.com`（Calibri 30px，y 820）；不放小字（同 2.4）。

### 7.5 疊加圖層

共通：底框是 #0F1115、85% 不透明、圓角 8px；進場淡入＋上移 8px（200ms，decelerate），離場淡出 200ms；每個圖層最短停留＝max（2 秒，字數 × 0.3 秒＋1 秒）；同一時間畫面上最多兩個疊加層（字幕／CC 不算）。

| 圖層 | 用在 | 字 | 底框與裝飾 | 位置與時間 |
|---|---|---|---|---|
| 短標語 | S01、S03–S07、S09；B 版 caption（S02、S10、S11 的排在頁面裡） | Arial Bold 44px text；單行，≤ 45 字元、寬 ≤ 1100px | 內距 14/24；左側 6px 琥珀色條 | BL 上層（S07 用 TL）；時間見 2.2 |
| lower-third（雙行） | S03 | 第 1 行 `Line`＋`Sleuth`（琥珀），Arial Bold 36px；第 2 行 `Root-cause investigations for small factories`，Calibri 28px text2 | 同短標語（含琥珀色條），內距 16/24 | BL 上層，和短標語輪流出現 |
| 小標示 | S01 `Simulated plant data`；B 版全程 `Recorded on the deployed app · {date} · Simulated plant data`；C 版 0–3 秒 | Calibri 26px text2 | 內距 8/14；1px borderStrong 外框；沒有琥珀色條（這是說明，不是強調） | BL 下層（C 版放右上） |
| `WAITING TIME CUT` | S04、S06、S09、C 版的每個剪接點 | 第 1 行 `WAITING TIME CUT`，Arial Bold 22px amber、字距 3px；第 2 行 `Elapsed shows the real time ↑`，Arial 24px text | 內距 8/14；1px borderStrong 外框 | 畫面上 `Elapsed` 文字的正下方 12px，右緣對齊 `Elapsed` 右緣（不超出 x 1824）；每次 2 秒，相隔不到 4 秒的剪接點連續顯示 |
| 重點框 | S05 的 `Source:` 行；S07 兩邊的 `WO-{id}`；S10 Cloud Logging 的 `query_id` | — | 3px amber 圓角矩形（圓角 8），比目標外擴 6px；無填色、無光暈 | 貼著目標，停 1.5–3 秒；同一時間最多一個（S07 兩個同時出現是例外） |
| 後製根因標籤 | 只在 2.5 ② 替代時（v2 沒上線） | `ROOT CAUSE`，Arial Bold 22px #0F1115，字距 2px | 琥珀實心 pill（內距 6/12、圓角 6）；L2-M3 外圍加 4px 琥珀實線框 | 標籤在 L2-M3 框右上角外側；結論出現後 0.3 秒淡入，不做脈動 |
| 遮蔽色塊 | S10 Cloud Logging 截圖 | — | s3 實心矩形、不寫字；不用馬賽克或模糊（有機會被還原） | 蓋住專案 ID、專案編號、服務帳號、IP、個人 email |
| 截圖卡 | S10 選做插入 | — | 寬 1400、2px borderStrong 外框、圓角 12；後面的頁面壓暗 60% | 畫面置中，3 秒 |

短標語全文（照 2.2）：S01 `03:00 — Line 2 stops.`、S03 `One click. No prompt.`、S04 `5 fixed queries. Gemini never writes SQL.`、S05 `Every number traces back to the source rows.`、S06 `Root cause + confidence + what was ruled out.`、S07 `Work order on the technician's phone.`、S09 `No evidence, no conclusion.`。SRT 必須燒入時只留 S01、S04、S09（S11 那一句本來就排在頁面上）。

### 7.6 字幕

**A 版 SRT（上傳平台不支援 CC、必須燒入時）**
- Arial Regular 40px，行高 52px，text 色。
- 每行一個底框：#0F1115、80% 不透明，內距 8/18，圓角 6px。
- 左右置中，最後一行底框的下緣在 y 1002（字幕保留區內）。
- 每行 ≤ 42 字元、每則最多 2 行、每則顯示 1–7 秒（同 5.4）。在片語處斷行，不留單字孤行。S07 例外：每行 ≤ 36 字元，字幕右緣才不會壓到右邊手機底部的頁尾警語。
- 不用斜體、不用全大寫、不加顏色；數字寫法和畫面一致（畫面是 `03:00`、`CV-2` 就照寫）。
- 畫面上已經有同樣內容的字卡時（S02 原話卡、S12 結尾卡），那一段不燒字幕；SRT 檔本身照樣保留逐字內容，給 CC 用。
- 如果平台支援 CC，就不燒入。播放器的 CC 一樣會出現在畫面下方，所以字幕保留區在任何情況都要空著。

**C 版燒入字幕**
- Arial Bold 56px，text 色，底框同上（85% 不透明），左右置中，最後一行下緣在 y 960。
- 每行 ≤ 24 字元，最多 2 行；每則至少停 2.5 秒（靜音自動播放，觀眾是第一次看）。

**B 版**：沒有 SRT，caption 用 7.5 的短標語樣式。

### 7.7 鏡頭、轉場與動態

**構圖預設**（來源座標是 1920×1080 的 app 畫面，CSS px；錄 2 倍母帶時 ×2）

| 代號 | 倍率 | 來源視窗 | 用在 |
|---|---|---|---|
| K0 全景 | 1.0 | 整個畫面 | S03、S08、S09 開頭與結尾、B 版全片 |
| K1 慢推 | 1.0→1.1，整鏡慢慢推 | 錨點依各鏡指定 | S01；S08 用同樣的緩推（錨點是 After 列） |
| K2 面板＋焦點機台 | 1.25 | x 384–1920、y 48–912 | S04、S06 後段、S07 開頭、S09 證據卡段 |
| K3 單卡特寫 | 1.5 | 1280×720，以目標卡為中心（碰到畫面邊就靠邊） | S05（#3 卡＋原始列）、S09（灰卡） |
| K4 產線圖特寫 | 1.5 | 1280×720，以聚焦中的機台為中心（主線是 L2-M3，要含 CV-2 和 `ROOT CAUSE` 標籤） | S06 前段 |

**轉場**
- 同一個 take 的 app 畫面之間：一律硬切。
- app ↔ 簡報頁／字卡：200ms 交叉淡化；S11 → S12：300ms。
- 不從黑畫面淡入、不淡出成黑畫面：第一格就是 app 畫面（S01），最後一格就是結尾卡（S12）。

**後製鏡頭運動**
- 構圖之間的推近、拉遠、平移：800ms，`cubic-bezier(0.4, 0, 0.2, 1)`（和 app 的 `--ease-standard` 同一條曲線）。
- K1 慢推：整鏡慢慢推，推的量很小，觀眾只會感覺「在靠近」。
- 每 4 秒最多一次鏡頭運動；鏡頭停下後至少停 2 秒才能再動。
- **app 自己的鏡頭在動的時候，後製鏡頭不准動**：按 Investigate 後 +150～850ms（拉近）、灰卡出現後 0～1.1 秒（拉回全景＋徽章）、Recap 開啟的 240ms（有長條時約 1.4 秒）。
- 推近倍率上限：2 倍母帶 2.0 倍；1080p 母帶 1.5 倍。

**簡報頁與字卡上的動態**
- 逐塊出現：淡入＋上移 8px，300ms，`cubic-bezier(0, 0, 0.2, 1)`（同 app 的 `--ease-decelerate`），在旁白唸到對應的詞時觸發；全部出現後靜止。
- S10 的點亮：不透明度 35% → 100%，300ms。

**禁止**（會降低可讀性，或和「錄的都是真的」衝突）：變速（快轉、慢動作、速度曲線）、3D 翻轉、旋轉、甩鏡、縮放模糊、動態模糊、晃動、glitch、漏光、粒子、彈跳或彈性曲線、打字機效果、逐字動畫、數字跳動、簡報頁上的 Ken Burns、動態背景、貼圖和 emoji。

### 7.8 游標與點擊

兩種錄法（Playwright、OBS）都用錄影腳本注入的假游標，系統游標不入鏡（OBS 要取消「擷取游標」）。假游標只存在錄影腳本裡，不改 app（同 5.1）。按鍵（`1`、`2`）不做任何畫面提示。

| 項目 | 規格 |
|---|---|
| 外觀 | 標準箭頭，高 36px（CSS px）；白色 #FFFFFF 填色＋2px #0F1115 描邊＋陰影 `0 2px 4px rgba(0,0,0,0.5)`；移到按鈕上也維持箭頭，不換成手指 |
| 移動 | 每段 500–800ms、ease-in-out，直線或微弧；速度不超過每秒 1500px；不瞬移 |
| 點擊前 | 在目標上停 300ms，讓按鈕的 hover 狀態入鏡 |
| 點擊 | 游標縮成 0.9 倍 100ms；點擊點出現一圈白色波紋：3px 白色（90% 不透明）圓環，半徑 10→32px、不透明度 0.9→0，400ms，只出現一次。不用琥珀色（琥珀在 app 裡代表根因） |
| 點擊後 | 停 600ms 再移開，停到不擋重點的位置（產線圖左下的空白處，或 modal 外面） |
| 閒置 | 停放 2 秒後淡出（200ms）；下一次要動的前 300ms 再淡入 |
| 不出現的鏡頭 | S01、S02、S04、S06、S10、S11、S12 |

**點擊順序**（錄影腳本照這個跑）
- 主線 take：按 `1` → 開錄（S01）→ 約 12 秒後點 `Investigate`（S03）→ 等 5 張卡和結論出現，這段不做任何操作（S04、S06）→ 脈動結束 2 秒後，點結論卡的引用 chip `#3` → `View source rows (12)` →（必要時在證據列裡捲動）→ 停 4 秒 → `Hide source rows`（S05）→ `Create work order`，modal 停 20 秒讓手機掃碼（S07）→ `Show summary`，停 8 秒（S08）→ 結束。
- 灰卡 take：按 `2` → 開錄，停 4 秒 → 點 `Investigate Line 1` → 灰卡出現後再錄 12 秒 → 結束。

### 7.9 錄影時的瀏覽器與系統設定（補充 5.1）

| 項目 | 設定 |
|---|---|
| 瀏覽器 | Chrome 穩定版，和 Quinn 驗收用的是同一版 |
| 視窗與縮放 | CSS 視窗 1920×1080；瀏覽器縮放 100%；Windows 顯示縮放 100%（用 4K 螢幕錄 2 倍母帶時設 200%） |
| 瀏覽器外框 | 網址列、分頁列、書籤列、擴充功能圖示、下載列都不能入鏡（網址列會露出金鑰網址）。Playwright 用無頭模式最乾淨；OBS 錄有頭瀏覽器時按 F11 全螢幕 |
| 自動化提示條 | Playwright 開有頭 Chrome 時，畫面上方會出現「Chrome is being controlled by automated test software」提示條：要在啟動設定裡拿掉 `--enable-automation`，或改用無頭模式 |
| Playwright 錄影尺寸 | 一定要明確指定錄影尺寸（1920×1080，或 2 倍母帶的 3840×2160）；不指定的話，Playwright 會把影片縮到 800×800 以內 |
| 捲軸 | 不能入鏡。無頭模式預設不畫捲軸；有頭模式看到捲軸就加啟動參數 `--hide-scrollbars`（先試） |
| 顏色 | 啟動參數 `--force-color-profile=srgb`，避免螢幕色彩設定影響錄出來的顏色 |
| 動畫 | Windows「動畫效果」要開著，Playwright 的 `reducedMotion` 設成 `no-preference`。系統如果設成減少動態，app 會直接跳到最終狀態，拉近、畫線、脈動全部錄不到 |
| 字型 | 開錄前在 console 確認 `document.fonts.check('16px Inter')` 回傳 `true`。Inter 沒載入時會退回 Segoe UI，畫面會和驗收時不一樣 |
| 簡報者模式 | 在畫面外先設好 cookie（manual §3.8），確認 `/api/config` 是 `"presenter": true`；這些步驟都不能入鏡 |
| 系統 | 開勿擾（專注輔助）、關掉所有通知，以及會跳視窗的程式（更新、聊天、雲端同步）；工作列不入鏡 |
| OBS（備案） | 畫布＝輸出＝母帶尺寸，30 fps；錄影品質選「無法區分的品質」（Indistinguishable Quality），先錄 MKV 再轉 MP4；取消擷取游標 |
| 每個 take 之前 | 按 `1`／`2` 重置；跑 Quinn 的錄影前檢查（沒有 fixture 黃條、底列是 `data: bigquery`、沒有 `Cached`） |

### 7.10 手機畫面

| 項目 | 規格 |
|---|---|
| 錄法 | 老闆自己的手機內建螢幕錄影：相機掃 QR → 開連結 → 工單頁捲動（同 5.1）；一定是同一張工單（同一個 WO id） |
| 無頭錄影時怎麼掃 | 無頭模式的 modal 不會顯示在任何螢幕上。腳本在 modal 出現時存一張截圖，在筆電上全螢幕打開給手機掃；那就是這次 take 的 QR，工單還是同一張 |
| 手機設定 | 勿擾模式、亮度調高、系統字級用預設（工單頁才不會被放大變形）、關掉所有通知 |
| 外框 | 通用手機外框，不用任何品牌的外型（不畫瀏海、鏡頭、按鍵、logo）。外框 418×872，#282D38 本體＋1px #4A5263 描邊，圓角 56；螢幕開口 390×844（內縮 14px），圓角 44；陰影 `0 24px 48px rgba(0,0,0,0.5)` |
| 放置 | A 版 S07：外框左上角在 (1406, 104)，桌面畫面在左（見 S07）；B 版第 ⑤ 格：0.8 倍，放右下（右緣 x 1824、下緣 y 1026）；C 版不用手機 |
| 縮放 | 手機錄影等比縮到開口寬 390px，不拉伸；長寬比和開口不同時，調整外框高度，不要裁掉工單內容 |
| 狀態列 | 手機錄影最上方的狀態列（時間、電量、電信商、通知圖示）用實心色塊蓋住（#171A21，和工單頁頁首同色），高度照實際狀態列。這樣也不會出現手機的真實時間和情境的 03:00 對不上 |
| 可讀性 | 手機內容在成片上大約是 CSS 原尺寸（16px 的字約 16px），是全片唯一低於 20px 的例外：這一鏡要傳達的是「工單在手機上」，細節交給旁白和 SRT |
| 剪接 | 手機畫面不剪、不變速；掃碼到開頁超過 4 秒就重錄 |

### 7.11 交付清單（D-6）

檔案放在 Drive 的 `LineSleuth/video/graphics/`，不放進 repo（同 5.5）。文字固定的圖層都做成透明 PNG，任何剪輯軟體都能直接用；會隨 take 變動的內容（數字卡的秒數、B 版日期、S12 的網址和 QR），在數值確定後一天內補做。

| 檔名 | 內容 | 初稿 | 定稿 |
|---|---|---|---|
| `s02-problem-base.png`、`s02-file-1.png`～`-4.png` | Slide 2 影片版底圖＋四張檔案卡 | 10/6 | 10/13 |
| `s02-quote.png` | 原話卡（拿到書面授權才做） | 授權後 1 天 | 10/13 |
| `s10-architecture-base.png`、`s10-lit-*.png`、`s10-score.png` | Slide 7 影片版：全暗底圖、各方塊點亮層、回歸分數條 | 10/6 | 10/13（分數條 10/16） |
| `s11-default-*.png`、`s11-compare-*.png` | S11 兩版：底圖＋下排兩張卡 | 10/6 | 10/13（對比版等 Sandy 10/15 查證完） |
| `s12-end.png`、`c-end-1080.png` | 結尾卡（QR 先用佔位） | 10/6 | 網址確定後，最晚 10/15 |
| `ov-tagline-s01.png`～`-s09.png` | 7 則短標語 | 10/6 | 10/13 |
| `ov-lowerthird-s03.png`、`ov-label-simulated.png`、`ov-label-b.png` | lower-third、小標示（B 版日期在錄完後填） | 10/6 | 10/14 |
| `ov-waiting-cut.png` | `WAITING TIME CUT` 標示 | 10/6 | 10/13 |
| `ov-highlight-*.png` | 重點框（依試錄畫面的實際尺寸做） | 10/13 | 10/14 |
| `ov-rootcause-fallback.png` | 後製根因標籤（只在 v2 沒上線時用） | 10/13 | 10/14 |
| `card-this-run.png` | 數字卡（只在 Recap 沒上線時用；秒數等採用的 take） | 模板 10/6 | 採用 take 後 1 天 |
| `phone-frame.png`、`phone-statusbar-mask.png` | 手機外框、狀態列遮罩 | 10/6 | 10/13 |
| C 版字幕圖層 | C 版燒入字幕 | 繳交後 | — |

- SRT 燒入的樣式（7.6）直接在剪輯軟體裡設定，不做成圖片。
- Google Cloud 圖示照官方規範使用：不改色、不變形、不加陰影。
- 10/13 試錄後，我把所有圖層套在試錄畫面上檢查一次可讀性（全螢幕播放、YouTube 一般大小視窗各一次），並回填 2.2 的確切座標。
