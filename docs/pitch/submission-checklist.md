# 繳交物清單：AI Builder Cup 2026（製造業主題）

- v0.1，2026-09-24，Paula（PM）。依據：第四次會議（`docs/meetings/2026-09-24-隊友到位後下一步.md`）、主持人 9/24 從官網抓下的規定（首頁、FAQ、Themes 頁）。
- 官方來源：https://aibuildercup.com/ 、https://aibuildercup.com/Faqs.html 、https://aibuildercup.com/themes.html
- **Terms & Conditions 尚未細讀**（[Google Doc](https://docs.google.com/document/d/e/2PACX-1vRm7ChZ6Ij9fG7uFDkxzUMpwgVeBmnQ6cMDnAIEEX84AiLBOOQ9cYbl3S5OzFBbcVb8TF55s-eVpiXb/pub)）。本清單以上面三頁為準；T&C 讀完若有衝突，以 T&C 為準並更新本檔。負責：隊友，9/26 前。
- Themes 頁的繳交物內容是抓取工具摘要的，**隊友要在頁面上逐字核對一次**（尤其「PDF presentation」與影片放置方式）。

## 0. 關鍵日期

| 日期 | 事項 | 官方原文 |
|---|---|---|
| **10/11（日）** | 團隊報名截止（2–4 人） | "Form a team of 2 to 4 members by October 11" / "It closes on October 11" |
| 10/17（六） | 我們的繳交目標日 | — |
| **10/18（日）** | 官方原型繳交截止（留作緩衝，不排新工作） | "prototype submission deadline Oct 18, 2026" |

## 1. 四項必交物

| # | 官方原文（FAQ） | 我們的對應檔案／網址 | 狀態 | 負責 | 截止 |
|---|---|---|---|---|---|
| 1 | "a video demo under 3 minutes"；Themes 頁：約 3 分鐘，以 YouTube、Vimeo 或 Google Drive 連結提供 | A 繳交版 2:55，分鏡 `docs/pitch/demo-video-storyboard.md`；連結填進 `docs/pitch/submission-summary.md` 的 `[video link]` | **待做**：素材 9/29–10/1 錄，10/2–10/10 剪 | 老闆（錄素材、上傳）、Dana（剪輯）、隊友（核英文字幕） | 10/10 定剪；10/16 上傳並測連結 |
| 2 | "the public GitHub repository of your prototype" | https://github.com/YMUNick/AILineSleuth （已是 public） | **已完成**：MIT LICENSE、`.gitignore` 已補；git 歷史密鑰掃描 0 筆；重新 clone 的乾淨副本 pytest 233 passed（2026-09-24） | Eddie | 繳交前再掃一次 |
| 3 | "a working deployed link of your prototype"；Themes 頁：部署在 Google Cloud（"Cloud Run or Firebase"） | https://linesleuth-547147056278.asia-southeast1.run.app | **已完成**（已上線、真 Gemini）；待 Quinn 9/25–28 雲端五項驗證 | Eddie、Quinn | 9/28 驗證；10/17–10/18 維持可開 |
| 4 | "a deck explaining your solution in detail"；Themes 頁：**PDF presentation**，涵蓋 problem、benefits、scalability | `docs/pitch/LineSleuth-demo.pptx`（大綱 `docs/pitch/pitch-deck.md`）；另有 `docs/pitch/one-pager.pdf` | **草稿 PDF 已匯出**：`docs/pitch/LineSleuth-demo.pdf`（13 頁，2026-09-24 由主持人用 PowerPoint 匯出）；**待補** scalability 與逐字引用 problem statement，10/10 定稿後重新匯出 | 主持人（匯出）、Paula（核對內容） | 10/10 定稿後重匯 |

## 2. 重點落差

| # | 落差 | 處理 | 負責 | 截止 |
|---|---|---|---|---|
| ① | **Deck 官方要 PDF，目前只有 pptx。** `one-pager.pdf` 是一頁式簡介，不能代替 deck | 10/10 PPT 凍結後，用 PowerPoint「另存新檔 → PDF」重新匯出 `docs/pitch/LineSleuth-demo.pdf`（草稿版已於 9/24 匯出）；打開檢查字型、截圖、頁碼沒跑掉 | 老闆 | 10/10 |
| ② | **Deck 要涵蓋 scalability。** 目前 11 頁＋附錄裡，擴展只散在 Slide 10 Roadmap，沒有獨立說明 | 凍結前（10/10）在 Slide 10 補一句擴展說明（例如：換 BigQuery、多產線、越南／泰文工單）；只改文字，不改版面 | Paula（文字）、Dana（放入） | 10/9 |
| ③ | **影片 2:55 在 "under 3 minutes" 內，但緩衝只有 5 秒** | 定剪後量實際片長，含片頭黑畫面與片尾字卡**不得超過 2:55**；YouTube 顯示長度也要再看一次。超過就砍 S11 或 S12，不砍 demo | Dana | 10/10 |
| ④ | **影片要用 YouTube／Vimeo／Google Drive 連結**，不是上傳檔案 | 預設用 YouTube「不公開（unlisted）」；上傳後用未登入的無痕視窗測一次能播。若用 Drive，權限設「知道連結的人可檢視」。能否不公開：官方未規定，待 T&C | 老闆 | 10/16 |
| ⑤ | **要明確標示所選的製造業 problem statement** | 在繳交表單、deck 第 1–3 頁、README 至少一處，逐字引用官方原文（見下方第 3 節）；PPT 已凍結，補在 Slide 3 標題下一行，屬文字修改 | Paula（文字）、Dana（放入） | 10/9 |
| ⑥ | **資格：10/11 團隊報名截止；任一隊員是學生，整隊失格** | 隊友今天報名；確認兩人都是在職、21 歲以上、JAPAC 地區、非學生（含在職專班、夜間部都要問清楚）；隊員名單與表單一致 | 隊友、老闆 | 9/24 報名；10/11 最晚 |

資格原文："working professionals, entrepreneurs, and startups only with age 21+"；"based out of JAPAC region strictly"；"If any member of a team is a student, the entire team will be disqualified"；"fresh projects built during the hackathon timeline"；"must be built using Google Cloud's tech stack"。

## 3. 我們選的 problem statement

官方原文（Manufacturing 主題頁）：

> "Build an AI-powered solution that addresses challenges related to efficiency, quality, reliability, supply and demand, or sustainability across manufacturing and industrial operations."

另一條要求：要展示 AI 如何把營運資料轉成 "meaningful insights, recommendations, or actions"。

我們的對應（建議寫法）：**Reliability ＋ efficiency**：夜班停線時，把 PLC、感測器、保養與班表資料轉成有證據的根因（insight）、SOP 建議（recommendation）與工單（action）。不要宣稱 quality、supply and demand、sustainability。

## 4. 對照評分權重

| 評分項（權重） | 我們的證據 | 還弱的地方 |
|---|---|---|
| Technical Merit & Gen AI Implementation（**40%**） | Vertex AI Gemini function calling，只能呼叫 5 個固定查詢、不寫 SQL；temperature 0；真 Gemini 回歸 10/10 根因、2/2 證據不足、3 次一致（`docs/qa/runs/README.md`）；信心標籤由伺服器計分；Cloud Run、IAM、預算警示、速率與每日上限 | 資料是示範用 DuckDB，BigQuery 只是可替換、不能寫已支援；雲端五項驗證（冷啟動、injection、每日上限、A1）尚未跑完；Google Cloud 使用面只有 Cloud Run＋Vertex AI |
| Problem Alignment & Impact（**25%**） | 直接對應 problem statement 的 reliability／efficiency；把資料轉成 insight→recommendation→action（根因、SOP、工單）；實測約 12 秒（中位數 12.6 秒） | **訪談 0 場**，「人工約 40 分鐘」與停線成本都是 `[待訪談驗證]`；10/8 前拿不到就全部改無數字版 |
| Innovation & Creativity（**25%**） | 一顆按鈕、沒有聊天框；每張證據卡可回查原始列；「證據不足」灰卡不硬猜；手機掃 QR 開工單 | 競品對比句尚標 `[to verify]`；「不硬猜」要在影片裡清楚演出來，否則評審只看到另一個 copilot |
| User Experience & Solution Design（**10%**） | UI v2（證據小圖、產線圖根因亮燈、響應式）、1920×1080 截圖、手機工單頁、A1 達標 | 沒有真使用者測試；隊友首次使用紀錄（`docs/first-run-log.md`）還沒做 |

**取捨**：40% 的技術分是我們最強的一塊，影片前半要讓評審看到 function calling 與證據卡回查；最弱的是問題契合的「真人數字」，這靠訪談，不靠加功能。功能維持凍結。

## 5. 官方未規定（查到再補）

| 項目 | 狀態 | 我們的暫定做法 |
|---|---|---|
| 影片解析度、格式 | 官方未規定 | 照分鏡 7.1：MP4（H.264）1920×1080、30 fps |
| 影片能否不公開（unlisted） | 官方未規定，待 T&C | 預設 YouTube unlisted |
| 影片縮圖／封面尺寸 | 官方未規定 | 用 YouTube 縮圖規格 1280×720（這是 YouTube 的規格，不是比賽規定）；Dana 10/11 後出圖 |
| Deck 頁數 | 官方未規定 | 維持現有 11 頁＋附錄 |
| Deck PDF 檔案大小上限 | 官方未規定 | 匯出後若超過 20 MB，改用「最小檔案大小」再匯一次 |
| 繳交表單位置、欄位、字數限制 | 官方未規定 | 文字先照 `docs/pitch/submission-summary.md`（短版約 100 字、長版約 300 字），拿到表單後再裁 |
| 是否要另附書面說明 | 官方未規定 | 用 README＋submission-summary 備妥 |

## 6. 繳交當天核對（10/17）

- [ ] 影片連結用無痕視窗能播，片長 ≤ 2:55
- [ ] GitHub repo 為 public，未登入能開；無金鑰（Quinn 繳交前安全清單全過）
- [ ] Cloud Run 網址能開、`gemini` 模式、沒有 OFFLINE FIXTURE 黃條；min-instances=1 已暖機
- [ ] Deck PDF 已上傳，含 problem、benefits、scalability 三塊，並逐字引用 problem statement
- [ ] 表單的隊員名單與正式報名一致，兩人都不是學生
- [ ] 所有 `[待訪談驗證]`、`X`、`[待實測]` 標記已替換或刪句（見 `docs/pitch/submission-summary.md`）
