# 30 秒社群短版：分鏡圖生成 prompt（ChatGPT 圖像生成用）

- v0.1，2026-09-24，Dana（設計）。依據 `docs/pitch/demo-video-storyboard.md` v0.3 的 2.4（C 版 30 秒）與第 7 節影片視覺規格；色彩 token 同 7.3／`docs/design/ui-spec.md`、`docs/design/ui-v2-spec.md`。
- 用途：**內部分鏡圖**，讓老闆和團隊在剪輯前先看到 30 秒的節奏和畫面。成片的 app 畫面仍然照第 0 節「錄的都是真的」，用 Cloud Run＋`gemini` 模式實際錄影，不用生成圖取代。
- 生成出來的圖放在 `docs/pitch/storyboard-30s/`，檔名 `sb30-01.png`～`sb30-07.png`。

## 0. 先講清楚的三件事

1. **UI 畫面以真實截圖為主**。圖像模型很容易把 UI 小字畫壞（字母錯亂、數字變形、按鈕文字亂拼）。有 UI 的格子（02、03、04、06）一律上傳對應截圖當參考圖，只讓模型做「放進分鏡框、加鏡頭標示和字幕條」；如果生成後字還是壞掉，**直接用截圖本身當那一格**，旁邊手寫鏡頭標示就好。生成圖只真正負責情境格（01 夜班工廠、05 手機掃 QR）。
2. **和 2.4 的差異（請 Paula／老闆決定）**：2.4 目前 30 秒全部是 app 畫面。老闆這次要情境格，所以我在 0–3 秒加了一格夜班工廠（01），18–21 秒加了一格手機掃 QR（05），其他格照 2.4 的順序和字幕，秒數往後擠。如果成片最後真的要用情境畫面，建議角落加小標示 `Illustration`（7.5 小標示樣式），和 `Simulated plant data` 同一個位置，避免評審以為是實拍工廠。
3. **16:9 分鏡，成片是 1:1**：分鏡圖依老闆交代固定 16:9；C 版成片是 1080×1080（2.4、7.1）。所以每個 prompt 都要求主體放在畫面**中間的正方形區域**（左右各留約 22% 當可裁掉的邊），之後裁 1:1 才不會切到重點。

### 截圖上傳前的處理（必做）

目前 `docs/pitch/deck/assets/` 的截圖是 OFFLINE FIXTURE 模式拍的，上傳前用小畫家處理：

- 右下角 `Agent: OFFLINE FIXTURE` 用 #0F1115 實心色塊蓋掉。
- `06-work-order-phone.png` 最上方黃色 `OFFLINE FIXTURE…` 橫條用 #171A21 實心色塊蓋掉（和 7.10 狀態列遮罩同色）。
- 右上 `Elapsed 00:0x` 是 fixture 的時間，不是實測值。分鏡圖裡可以留著（內部用），但**不要**把這個數字寫進字幕；成片的 `Elapsed` 以實際錄影那一次為準。

---

## 1. 分鏡總表（30 秒，7 格）

| 格 | 時間碼 | 畫面 | 燒入字幕（英文，短） | 對應 app 狀態／素材 | 生成方式 |
|---|---|---|---|---|---|
| sb30-01 | 0:00–0:03 | 情境：東南亞／台灣中小代工廠夜班，Line 2 塔燈亮紅，一位主管獨自站在控制台前（背影或側影） | `3 a.m. Line 2 stops.` | —（情境）；接下一格的 `Line 2 stopped` | 純生成 |
| sb30-02 | 0:03–0:06 | app 全景：Line 2 紅框、L2-M3 `STOPPED`、`Downtime` 在跳；游標按下琥珀色 `Investigate`，L2-M3 出現藍色虛線聚焦圈 | `One click. No prompt.` | `01-overview.png` → `02-investigating.png`（S01＋S03） | 截圖參考 |
| sb30-03 | 0:06–0:13 | 面板特寫：證據卡逐張長出、sparkline（溫度曲線越過 SOP 虛線變琥珀）；`Elapsed` 下方 `WAITING TIME CUT` 標示 | `Every number traces back to the data.` | `02-investigating.png`（S04） | 截圖參考 |
| sb30-04 | 0:13–0:18 | 前半 L2-M3 特寫：琥珀實線框、`CV-2 valve` 琥珀膠囊、`ROOT CAUSE` 標籤；後半結論卡 `Confidence: High` | `Root cause found. With evidence.` | `03-root-cause.png`（S06） | 截圖參考 |
| sb30-05 | 0:18–0:21 | 情境：技術員在機台旁用手機掃 QR，手機上是工單頁（`WO-…`、`ROOT CAUSE`） | `Work order on the technician's phone.` | `06-work-order-phone.png`（S07，需先蓋掉黃條） | 生成＋截圖參考 |
| sb30-06 | 0:21–0:27 | 灰卡：`Insufficient evidence`、`Checked` 四項；Line 1 灰色虛線＋`No root cause found`；沒有任何機台變色、沒有 `Create work order` | `No evidence? No guess.` | `07-insufficient.png`（S09） | 截圖參考 |
| sb30-07 | 0:27–0:30 | 結尾卡：`LineSleuth`（`Sleuth` 琥珀）、tagline、聯絡方式、QR 佔位 | 無（字卡本身） | `c-end-1080`（7.4 (4)） | 生成（字少，可控） |

- 字幕選項（可替換 sb30-03 或疊在 sb30-04 下方一行小字）：`About 12 seconds per investigation (measured, gemini-2.5-flash)`。來源：`docs/qa/runs/README.md`，2026-09-24 gemini-2.5-flash 全集 10 個根因 × 3 次的中位數 12.6 s（R01 單題中位數 10.8 s）。注意：這是回歸集中位數，不是影片那一次 take 的秒數，所以必須保留 `measured` 字樣，也不能配任何 before 數字做對比。另外 A 版規則是旁白不唸模型名稱；社群短版字幕要不要保留 `gemini-2.5-flash`，請 Sandy 決定。
- 畫面上**絕對不出現**：40 分鐘、停線損失金額、90 秒、回歸分數、任何 Ask。
- 聯絡方式只出現在 sb30-07：`Hung Che Nick Lai · hongchelai@gmail.com`。

---

## 2. 共用風格前綴（每個 prompt 開頭都貼這段）

```text
STYLE BLOCK — apply to every frame in this series.
Format: one clean digital storyboard frame, 16:9 landscape, 1920x1080. Thin 1px grey (#4A5263) frame border. Top-left tiny label in plain sans-serif: the frame ID and timecode I give you. Keep the main subject inside the central square area (the middle 56% of the width), because the final video will be cropped to 1:1.
Visual style: modern semi-realistic digital illustration with clean lines and soft cinematic lighting, like a professional pre-production storyboard; not a photo, not anime, not 3D render, no film grain, no lens flare.
Palette (strict): deep industrial dark background #0F1115, dark surfaces #171A21 / #1F232C, text off-white #E8EAED, secondary text #A3AAB8. Amber accent #F5A524 = our highlight and the root cause. Red #F2555A = ONLY for a stopped line / stop alarm. Green #3DD68C = only for running status. Do not introduce other accent colors.
Typography for any overlay text: plain Arial-like bold sans-serif. Burned-in caption bar: centered in the lower part of the frame, off-white bold text on a dark #0F1115 box at 85% opacity with rounded corners. Render caption text exactly as given, letter by letter; no extra words.
Setting: small contract manufacturer in Southeast Asia or Taiwan — a modest, tidy, well-lit plastic injection molding plant; ordinary modern equipment, safety signage without readable brand names. Avoid stereotypes: no sweatshop imagery, no dirty or chaotic factory, no conical hats, no exaggerated ethnic features; workers look professional and competent, wearing plain work uniforms and safety gear.
Hard rules: no real brand logos or trademarks anywhere (machines, phones, clothing, screens); no recognizable real person's face — people are shown from behind, in profile, silhouetted, or with face turned away; no numbers other than the ones I explicitly give; no watermarks.
```

---

## 3. 每格 prompt

每格的用法：新訊息先貼第 2 節的 STYLE BLOCK，換行，再貼該格 prompt；標「上傳截圖」的格子，同一則訊息附上對應截圖。

### sb30-01　0:00–0:03　夜班停線（純生成）

```text
Frame ID: SB30-01 · 0:00–0:03

Scene: 3 a.m. inside a small plastic injection molding plant in Southeast Asia. Night shift, mostly empty. Three production lines in a row; the middle one (Line 2) has a stack light glowing red #F2555A, casting a soft red glow on the floor and the machine. Lines 1 and 3 show small green status lights.
Subject: one night-shift supervisor standing alone at a simple control desk with a laptop, seen from behind at a three-quarter angle, face not visible, plain dark work jacket and safety glasses pushed up on the head. Posture: pausing, alert, about to act — calm concern, not panic.
Camera: wide establishing shot, slightly low angle, eye line toward the red light. Storyboard annotation arrow in amber #F5A524 in a corner: "SLOW PUSH-IN 1.0→1.1".
Lighting: cool dim overhead industrial lights, the red stack light as the key accent, laptop screen giving a faint cool glow on the supervisor's shoulder. Quiet, late-night mood.
Laptop screen content: abstract dark dashboard shapes only, no readable text.
Top-right small outlined label (grey border, no fill): "Simulated plant data".
Burned-in caption: "3 a.m. Line 2 stops."
```

### sb30-02　0:03–0:06　一顆按鈕（上傳截圖）

附上：`01-overview.png`（已蓋掉 OFFLINE FIXTURE）。如果想同時表現按下後的聚焦狀態，改附 `02-investigating.png`，並把第二段的描述換成「L2-M3 has a blue dashed focus ring」。

```text
Frame ID: SB30-02 · 0:03–0:06

Use the attached screenshot as the exact UI. Place it as a flat screen recording filling the frame (no laptop bezel, no perspective, no tilt). Keep every piece of UI text exactly as in the screenshot and legible; do not redraw, translate, re-spell or add any UI text or numbers.
Composition: slight zoom (about 1.33x) framing both the amber "Investigate" button and the red "Molding L2-M3 STOPPED" card in the central square area.
Storyboard overlays only (drawn on top, clearly as annotations):
- A white arrow mouse cursor on the amber Investigate button with a single thin white click ripple ring.
- A small amber annotation note in a corner: "CLICK → app zooms to L2-M3 (blue dashed focus)".
Burned-in caption: "One click. No prompt."
```

### sb30-03　0:06–0:13　證據卡（上傳截圖）

附上：`02-investigating.png`（已蓋掉 OFFLINE FIXTURE）。

```text
Frame ID: SB30-03 · 0:06–0:13

Use the attached screenshot as the exact UI; keep all UI text legible and unchanged, do not redraw or invent any text or numbers.
Composition: close-up crop (about 1.33x) on the right-hand "Investigation" panel: the panel header with the status chip and Elapsed must stay in frame, plus the "Mold temperature" evidence card with its sparkline where the blue line rises past the dashed SOP limit and turns amber.
Storyboard overlays only:
- Directly below the Elapsed text, a small dark label with a 1px grey border: first line "WAITING TIME CUT" in amber bold small caps, second line "Elapsed shows the real time ↑" in off-white.
- A small amber annotation in a corner: "HARD CUTS between cards · no speed-up".
No mouse cursor in this frame.
Burned-in caption: "Every number traces back to the data."
```

（若採用實測字幕選項，把最後一行換成：`Burned-in caption: "About 12 seconds per investigation" and a smaller second line "(measured, gemini-2.5-flash)"`。）

### sb30-04　0:13–0:18　根因（上傳截圖）

附上：`03-root-cause.png`（已蓋掉 OFFLINE FIXTURE）。

```text
Frame ID: SB30-04 · 0:13–0:18

Use the attached screenshot as the exact UI; keep all UI text legible and unchanged, do not redraw or invent any text or numbers.
Show this frame as a two-panel storyboard split side by side, separated by a thin grey line:
- Left panel "A (0:13–0:15.5)": close-up (about 1.5x) on the red-bordered Line 2 lane: the "Molding L2-M3 STOPPED" card with its amber solid outline, the amber "CV-2 valve" pill and the amber "ROOT CAUSE" tag.
- Right panel "B (0:15.5–0:18)": close-up on the conclusion card in the right panel: "ROOT CAUSE", "Cooling valve CV-2 stuck at 20% open", "Confidence: High", and "3 independent signals agree · 1 alternative ruled out".
Small amber annotation: "HARD CUT A → B".
No mouse cursor. Mood: clarity, a moment of relief.
Burned-in caption across the bottom of the whole frame: "Root cause found. With evidence."
```

### sb30-05　0:18–0:21　手機上的工單（生成＋截圖參考）

附上：`06-work-order-phone.png`（已蓋掉頂端黃色 OFFLINE FIXTURE 橫條）。這一格手機螢幕很小，字壞掉的機率最高：生成後如果手機上的字糊掉，剪輯時直接把真實截圖貼進手機螢幕區即可，分鏡圖只要看得出構圖。

```text
Frame ID: SB30-05 · 0:18–0:21

Scene: next to the stopped molding machine on Line 2 (soft red stack light in the blurred background), a maintenance technician holds a generic smartphone. Shot over the shoulder from behind; only the hands, sleeve and shoulder are visible, no face. Plain work gloves or bare hands, neutral work uniform.
Phone: generic modern phone with a plain dark #282D38 body, no notch, no camera bump, no buttons, no brand logo.
Phone screen: use the attached screenshot as the screen content — a dark work order page. Keep the header "WO-0001", "Priority: High" and "ROOT CAUSE" legible if possible; do not invent any other text. If you cannot keep it legible, show the page as a simplified dark layout with the same structure rather than garbled text.
Camera: medium close-up, phone screen facing the viewer, shallow depth of field, phone in the central square area. Small amber annotation: "SCAN QR → work order opens".
Lighting: phone screen as a soft key light on the hand, warm amber #F5A524 accent on the "Priority: High" chip, dim cool factory ambient.
Burned-in caption: "Work order on the technician's phone."
```

### sb30-06　0:21–0:27　灰卡（上傳截圖）

附上：`07-insufficient.png`（已蓋掉 OFFLINE FIXTURE）。

```text
Frame ID: SB30-06 · 0:21–0:27

Use the attached screenshot as the exact UI; keep all UI text legible and unchanged, do not redraw or invent any text or numbers. Do not add any red or amber highlight to any machine: every machine stays green "RUNNING".
Show as a two-panel storyboard split side by side:
- Left panel "A (0:21–0:24.5)": close-up (about 1.5x) on the grey dashed "Insufficient evidence" card, including the question-mark icon, "No root cause found. LineSleuth will not guess.", the full "Checked" list of four items and "Recommended next step".
- Right panel "B (0:24.5–0:27)": the left part of the screen: Line 1 with its grey dashed outline and the "No root cause found" badge, all lines running, no work order button.
Small annotation in grey (not amber): "MUSIC DROPS 1s — emotional beat".
Mood: calm, honest, trustworthy. No mouse cursor.
Burned-in caption across the bottom: "No evidence? No guess."
```

### sb30-07　0:27–0:30　結尾卡（生成）

字很少，模型通常畫得出來；仍然要逐字檢查 email。QR 在分鏡圖只放佔位框，成片用 `c-end-1080` 真實 QR。

```text
Frame ID: SB30-07 · 0:27–0:30

A static end card on a solid #0F1115 background, centered layout inside the central square area, generous empty space, no illustration, no photo.
Top: wordmark "LineSleuth" in large bold sans-serif — "Line" in off-white #E8EAED and "Sleuth" in amber #F5A524, no space between them.
Below: tagline "Every conclusion backed by evidence." in lighter grey #A3AAB8.
Center: a square placeholder box with a 1px dashed grey (#4A5263) border and the letters "QR" in the middle (do not draw a real QR code).
Below the box, one line of small text: "Hung Che Nick Lai · hongchelai@gmail.com" — spell it exactly.
No other text, no numbers, no logos. Small grey annotation in the top-left corner only: "STATIC to the end · no fade to black".
```

---

## 4. 在 ChatGPT 裡的使用步驟

1. **開一個新對話專門生這一組**，第一則訊息先貼第 2 節 STYLE BLOCK，並加一句：`Remember this style block and apply it to every image I ask for in this chat. Always output 16:9 landscape. Reply "OK" only.` 這樣後面每格比較容易一致。
2. **每格一則訊息**：再貼一次 STYLE BLOCK（保險，對話長了模型會忘）＋該格 prompt；有「附上」的格子，同一則訊息上傳處理過的截圖。如果介面有尺寸選項，選橫式 16:9。
3. **重跑到一致再往下**：先生 sb30-01，滿意後在下一格加一句 `Match the lighting, palette and line style of the previous frame (SB30-01).`。檢查清單：
   - 比例是 16:9、主體在中間正方形區域
   - 字幕文字逐字正確（特別是 sb30-07 的 email）
   - 沒有品牌 logo、沒有可辨識的臉
   - 紅色只出現在停線；灰卡那一格沒有任何機台變色
   - 沒有多出來的數字
   不合格就回覆 `Regenerate. Keep everything the same but fix: …`，只講要修的那一點，不要整段重寫，以免其他部分跑掉。
4. **UI 字壞掉就停手**：sb30-02／03／04／06 重跑兩次字還是壞，就不要再跑，直接用處理過的截圖當那一格，在剪輯軟體或簡報裡手動加字幕條和鏡頭標示。
5. **下載命名**：`sb30-01.png`、`sb30-02.png` … `sb30-07.png`，兩位數編號，和第 1 節表格一致；同一格有多個版本時加字尾 `sb30-03-b.png`，選定後把定稿改回無字尾的檔名。
6. **存放位置**：`docs/pitch/storyboard-30s/`（資料夾不存在就自己建）。另外可以把 7 張排成一張總覽圖 `sb30-contact-sheet.png` 放同一個資料夾，會議上一眼看完 30 秒。
7. 生完後把總覽圖丟回會議，請 Paula 決定第 0 節第 2 點（要不要在成片保留情境格），Sandy 決定實測字幕要不要保留模型名稱。
