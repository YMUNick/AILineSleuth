# 30 秒社群短版：分鏡與素材指引（01 生成圖 prompt＋真錄屏／實拍指引）

- v0.1，2026-09-24，Dana（設計）。依據 `docs/pitch/demo-video-storyboard.md` v0.3 的 2.4（C 版 30 秒）與第 7 節影片視覺規格；色彩 token 同 7.3／`docs/design/ui-spec.md`、`docs/design/ui-v2-spec.md`。
- v0.2，2026-09-24，Dana（設計）：依 `docs/meetings/2026-09-24-部署後下一步.md` 定案改版。只保留 01 夜班工廠的生成圖 prompt（右下角標 `Illustration / 示意`）；05 改成真手機實拍掃 QR 的拍攝指引；02、03、04、06 改成雲端部署版真錄屏指引，07 改成停在 PPT 封面；字幕的秒數改成實測約 12 秒（與 `demo-video-storyboard.md` 第 0 節第 3 點一致），刪掉 v0.1 的截圖遮 OFFLINE FIXTURE 步驟（PPT 已換成雲端真截圖）。
- 用途：30 秒 C 版的**分鏡與素材指引**。7 格裡只有 01 是生成圖，其他全部是真的：真錄屏、真手機實拍、PPT 封面。
- 素材存放：生成圖與實拍素材放 `docs/pitch/storyboard-30s/`（資料夾不存在就自己建），檔名 `sb30-01.png`、`sb30-05-phone.mp4`；錄屏母帶照 `demo-video-storyboard.md` 5.5 放 Drive，不進 repo。

## 0. 先講清楚的四件事

1. **錄的都是真的**：app 畫面只用雲端部署版錄，網址 `https://linesleuth-547147056278.asia-southeast1.run.app`（真 Gemini，畫面上沒有 OFFLINE FIXTURE 黃條）。不用生成圖取代 app 畫面，也不用本機 fixture 模式。
2. **唯一的生成圖是 01**，成片右下角一定要標 `Illustration / 示意`，避免評審以為是實拍工廠。
3. **錄 16:9，成片裁 1:1**：錄影一律 1920×1080；C 版成片是 1080×1080，裁切位置照 `demo-video-storyboard.md` 2.4。拍攝和錄屏時，重點都要落在畫面**中間的正方形區域**（左右各留約 22% 可裁掉的邊）。
4. **字幕只用已驗證的數字**：唯一可用的秒數是實測「約 12 秒找到根因」（`docs/qa/runs/README.md`，gemini-2.5-flash 回歸集中位數 12.6 秒），字幕必須保留 `measured`。**絕對不出現**：40 分鐘、90 秒、停線損失金額、回歸分數、任何 before/after 對比、任何 Ask。

---

## 1. 分鏡總表（30 秒，7 格）

| 格 | 時間碼 | 畫面 | 燒入字幕（英文，短） | 素材來源 | 參考截圖（`docs/pitch/deck/assets/`） |
|---|---|---|---|---|---|
| sb30-01 | 0:00–0:03 | 情境：中小代工廠夜班，Line 2 塔燈亮紅，主管獨自站在控制台前（背影） | `3 a.m. Line 2 stops.` | **生成圖**（第 3 節 prompt），右下角 `Illustration / 示意` | — |
| sb30-02 | 0:03–0:06 | Line 2 紅框、L2-M3 `STOPPED`、`Downtime` 在跳；按下琥珀色 `Investigate`，L2-M3 出現藍色虛線聚焦圈 | `One click. No prompt.` | 真錄屏（主線 take） | `01-overview.png` → `02-investigating.png` |
| sb30-03 | 0:06–0:13 | 面板特寫：證據卡逐張長出、sparkline 越過 SOP 虛線變琥珀；`Elapsed` 下方 `WAITING TIME CUT` | `Every number traces back to the data.` | 真錄屏（主線 take） | `02-investigating.png` |
| sb30-04 | 0:13–0:18 | 前半 L2-M3 琥珀實線框、`CV-2 valve`、`ROOT CAUSE`；後半結論卡 `Confidence: High` | `Root cause found. With evidence.` | 真錄屏（主線 take） | `03-root-cause.png`、`04-conclusion.png` |
| sb30-05 | 0:18–0:21 | 真手機對著大螢幕的 QR 掃碼，手機打開工單頁 | `Work order on the technician's phone.` | **真手機實拍**（第 4 節） | `06-wo-modal.png`（大螢幕）、`06-work-order-phone.png`（手機） |
| sb30-06 | 0:21–0:27 | 灰卡 `Insufficient evidence`、`Checked` 四項；Line 1 灰色虛線＋`No root cause found`；沒有機台變色、沒有 `Create work order` | `No evidence? No guess.` | 真錄屏（灰卡 take） | `07-insufficient.png` |
| sb30-07 | 0:27–0:30 | 片尾停在 PPT 封面，靜止到最後一格，不淡出成黑畫面 | 無（封面本身） | PPT 封面（`docs/pitch/LineSleuth-demo.pptx` 第 1 頁） | — |

- 實測字幕選項（可替換 sb30-03 的字幕）：`About 12 seconds to a root cause` ＋第二行小字 `(measured median)`。這是回歸集中位數，不是這次 take 的秒數，所以 `measured` 不能拿掉，也不能配任何 before 數字。要不要加模型名稱 `gemini-2.5-flash`，由 Sandy 決定。
- 參考截圖只用來對照「錄到的畫面應該長這樣」，不直接當成片素材（例外：錄屏失敗時的救急見第 5 節最後一點）。

---

## 2. 共用風格前綴（只給 sb30-01 用）

```text
STYLE BLOCK — apply to this frame.
Format: one clean digital storyboard frame, 16:9 landscape, 1920x1080. Keep the main subject inside the central square area (the middle 56% of the width), because the final video will be cropped to 1:1.
Visual style: modern semi-realistic digital illustration with clean lines and soft cinematic lighting, like a professional pre-production storyboard; not a photo, not anime, not 3D render, no film grain, no lens flare.
Palette (strict): deep industrial dark background #0F1115, dark surfaces #171A21 / #1F232C, text off-white #E8EAED, secondary text #A3AAB8. Amber accent #F5A524 = our highlight. Red #F2555A = ONLY for a stopped line / stop alarm. Green #3DD68C = only for running status. Do not introduce other accent colors.
Typography for any overlay text: plain Arial-like bold sans-serif. Render text exactly as given, letter by letter; no extra words.
Setting: small contract manufacturer in Southeast Asia or Taiwan — a modest, tidy, well-lit plastic injection molding plant; ordinary modern equipment, safety signage without readable brand names. Avoid stereotypes: no sweatshop imagery, no dirty or chaotic factory, no conical hats, no exaggerated ethnic features; workers look professional and competent, wearing plain work uniforms and safety gear.
Hard rules: no real brand logos or trademarks anywhere; no recognizable real person's face — people are shown from behind, in profile, silhouetted, or with face turned away; no numbers or text other than the ones I explicitly give; no watermarks.
```

---

## 3. sb30-01　0:00–0:03　夜班停線（生成圖）

```text
Frame ID: SB30-01 · 0:00–0:03

Scene: 3 a.m. inside a small plastic injection molding plant in Southeast Asia. Night shift, mostly empty. Three production lines in a row; the middle one (Line 2) has a stack light glowing red #F2555A, casting a soft red glow on the floor and the machine. Lines 1 and 3 show small green status lights.
Subject: one night-shift supervisor standing alone at a simple control desk with a laptop, seen from behind at a three-quarter angle, face not visible, plain dark work jacket and safety glasses pushed up on the head. Posture: pausing, alert, about to act — calm concern, not panic.
Camera: wide establishing shot, slightly low angle, eye line toward the red light.
Lighting: cool dim overhead industrial lights, the red stack light as the key accent, laptop screen giving a faint cool glow on the supervisor's shoulder. Quiet, late-night mood.
Laptop screen content: abstract dark dashboard shapes only, no readable text.
Keep the bottom-right corner and the lower-center area plain and dark with no objects or text — labels and captions will be added in editing.
No text of any kind in the image.
```

生成後處理（剪輯時疊上，不讓模型畫字，避免字壞掉）：

- **右下角標示 `Illustration / 示意`**：用 `demo-video-storyboard.md` 7.5 的「小標示」樣式（灰框、無填色），放在 1:1 裁切後仍看得到的位置：來源座標右緣約 x 1480、下緣約 y 1040（中間正方形的右下角），不是 1920 畫面的最右下角，否則裁 1:1 會被切掉。
- 右上角小標示 `Simulated plant data`（同 2.4）。
- 燒入字幕 `3 a.m. Line 2 stops.`，樣式照 7.6 C 版，不要壓到右下角標示。
- 成片可加 1.0→1.1 慢推（3 秒內）。

在 ChatGPT 的做法：開新對話，一則訊息貼第 2 節 STYLE BLOCK＋本節 prompt，比例選橫式 16:9。檢查：主體在中間正方形、紅色只在 Line 2、沒有 logo、沒有可辨識的臉、圖裡沒有任何字。不合格就回覆 `Regenerate. Keep everything the same but fix: …`，只講要修的那一點。定稿存成 `docs/pitch/storyboard-30s/sb30-01.png`。

---

## 4. sb30-05　0:18–0:21　真手機實拍掃 QR

目標：一個鏡頭裡**同時看得到大螢幕上的 QR 和手機打開的工單頁**，證明「掃了就開」是真的。不用生成圖。

**器材**
- 掃碼手機：型號不限，老闆自己的手機就可以。
- 拍攝機：另一支手機或相機，固定在腳架或靠在桌上，不要手持晃動；橫拍 16:9，1920×1080、30 fps。
- 大螢幕：筆電或外接螢幕，顯示雲端部署版建立工單後的 modal（QR＋`WO-…`＋`Priority: High`，對照 `06-wo-modal.png`）。

**流程**（一次拍完，不剪、不變速，照 7.10）
1. 在主線 take 裡按 `Create work order`，modal 停住（主線 take 本來就留 20 秒給掃碼）。
2. 拍攝機開錄 → 掃碼手機用內建相機對準大螢幕 QR → 點開連結 → 工單頁出現（對照 `06-work-order-phone.png`，看得到 `WO-…`、`ROOT CAUSE`）→ 停 2 秒。
3. 手機上的 `WO-…` 必須和大螢幕 modal 是同一張工單。掃碼到開頁超過 4 秒就重拍。

**構圖**
- 過肩或側後方角度：只拍到手、袖子、肩膀，不拍臉。
- 大螢幕在後方、手機在前方，兩者都要在**中間正方形區域**內（成片要裁 1:1）。
- 手機螢幕朝向鏡頭約 15–30 度斜角，工單頁頂部的 `WO-…` 看得出來即可，不要求小字全部可讀（細節交給字幕）。
- 大螢幕上的 QR 在開頁前要清楚入鏡至少 1 秒；手機擋住 QR 的時間只限掃碼那一下。

**光線**
- 關掉或調暗頂燈，讓兩個螢幕成為主光源，接近夜班氣氛；房間不要全黑，手要看得出輪廓。
- 大螢幕和手機亮度都調到最高，拍攝機曝光鎖在螢幕上（點螢幕區長按鎖定 AE/AF），避免螢幕過曝成一片白。
- 避開窗戶和燈具在螢幕上的反光；螢幕出現摩爾紋時，拍攝機稍微拉遠或改一點角度。

**避免拍到個資**
- 掃碼手機開勿擾模式、關掉所有通知；桌布換成純色或先進 app 再開錄，不要露出主畫面、相簿、聯絡人、行事曆。
- 手機狀態列（時間、電量、電信商）照 7.10 在剪輯時用 #171A21 色塊蓋掉。
- 大螢幕只開全螢幕的 app，不能露出網址列、分頁、書籤、工作列、Email、聊天視窗；網址不能帶 `?key=`。
- 背景不能有名片、證件、白板字、便利貼、門牌、窗外可辨識的街景；螢幕和玻璃上不能倒映出臉。
- 拍完先整段看一次，確認上面幾項都沒入鏡，再交給剪輯。

**成片**：取工單頁出現前後 3 秒；裁 1:1 以手機和 QR 為中心；燒入字幕 `Work order on the technician's phone.`。如果實拍始終看不清楚，備案是用 A 版 S07 的手機螢幕錄影放進 7.10 的手機外框（仍然是真畫面）。

---

## 5. 真錄屏指引（sb30-02、03、04、06）

**錄影來源**
- 網址：`https://linesleuth-547147056278.asia-southeast1.run.app`（雲端部署版、真 Gemini）。畫面上**不能**出現 OFFLINE FIXTURE 黃條；底列 `Agent:` 不能是 OFFLINE FIXTURE，出現就停錄、檢查部署設定。
- 30 秒版和 A 版共用同一場錄影的母帶（`demo-video-storyboard.md` 第 1 節「錄一次，剪三個版本」），不另外錄。

**錄影設定**
- 1920×1080（CSS 視窗 1920×1080、瀏覽器縮放 100%）；瀏覽器外框、捲軸、系統游標、通知都不入鏡，細項照 7.9。
- 假游標和點擊波紋照 7.8。

**錄影當天順序**
1. 確認 Cloud Run `min-instances=1`（錄影當天才調，繳交後調回 0）。
2. **先暖機一次**：開網址、完整跑一次 `Investigate`，讓冷啟動發生在錄影之前；這一次不錄、不採用。
3. 按 `1` 重置，開始錄主線 take；按 `2` 重置，錄灰卡 take。
4. 每個採用的 take 記下 `query_id` 和 `Elapsed`。畫面出現 `Cached` chip 就重錄，不能剪掉或遮住。

**每格對照**

| 格 | 從哪個 take 取 | 要錄到的狀態（對照截圖） | 1:1 裁切 |
|---|---|---|---|
| sb30-02 | 主線 take：按 `Investigate` 前 1 秒到聚焦拉近完成 | 起點像 `01-overview.png`（Line 2 紅框、`Downtime` 在跳），按下後像 `02-investigating.png`（藍色虛線聚焦圈、`Investigating`） | 同 2.4 第 2 列 |
| sb30-03 | 主線 take：證據卡逐張出現 | 像 `02-investigating.png`：面板表頭 chip 與 `Elapsed` 在框內、sparkline 畫完。跳接處疊 `WAITING TIME CUT`，一律硬切、不變速 | 同 2.4 第 3 列 |
| sb30-04 | 主線 take：結論落地前後 | 前半像 `03-root-cause.png`（L2-M3 琥珀實線框、`CV-2 valve`、`ROOT CAUSE`），後半像 `04-conclusion.png`（`Confidence: High`、理由列） | 同 2.4 第 4 列 |
| sb30-06 | 灰卡 take：灰卡落地後 | 像 `07-insufficient.png`：`Insufficient evidence`、`Checked` 四項完整、Line 1 灰色虛線＋`No root cause found`、沒有機台變色、沒有 `Create work order` | 同 2.4 第 5 列 |

- 錄屏字幕照第 1 節表格，樣式照 7.6 C 版；同一段內不推近，段落之間硬切（同 2.4）。
- 錄屏失敗時的救急：deck 截圖也是雲端真畫面，可以暫時當靜態格，但要在交付時註明是哪一格，錄影補好後替換。

---

## 6. sb30-07　0:27–0:30　片尾停在 PPT 封面

- 素材：`docs/pitch/LineSleuth-demo.pptx` 第 1 頁（封面），用 PowerPoint「匯出 → PNG」1920×1080。
- 1:1 成片：不要裁切封面，改成把 16:9 封面置中、上下補 #0F1115 底色（letterbox），封面上的字才不會被切掉。
- 從 sb30-06 300ms 交叉淡化進來後完全靜止，停到片尾，不淡出成黑畫面。
- 封面上如果有數字，只能是已驗證的；有 40 分鐘或 90 秒，先請 Sandy 改 PPT 再匯出。
- 這一格取代 v0.1 的 `c-end-1080` 結尾卡；`demo-video-storyboard.md` 2.4 最後一列要不要同步，請 Paula 決定。

---

## 7. 交付與檢查

- 10/3 前交：`sb30-01.png` 定稿（本檔負責的唯一生成圖）。
- 錄影當天（10/17）：主線 take、灰卡 take、`sb30-05-phone.mp4`，照第 4、5 節拍錄。
- 成片前檢查清單：
  - 01 右下角有 `Illustration / 示意`，裁 1:1 後仍看得到
  - 02、03、04、06 沒有 OFFLINE FIXTURE 黃條、沒有 `Cached`、`Elapsed` 是真實時間
  - 05 同時看得到大螢幕 QR 和手機工單頁，沒有臉、通知、網址列或其他個資
  - 07 是 PPT 封面，靜止到最後
  - 全片沒有 40 分鐘、90 秒、停線損失金額、回歸分數；有秒數時只有「約 12 秒（measured）」
