# 變更說明：QA bug 修正（BUG-001～008）

- 日期：2026-09-24，Eddie（工程）
- 依據：`docs/qa/bugs.md`。給 Paula 更新使用手冊用；技術細節看 `docs/engineering/deploy.md` 5.1、5.2。
- 前端畫面、文案、版面**都沒改**。

## 使用者看得到的變化

| # | 誰會遇到 | 以前 | 現在 |
|---|---|---|---|
| 1 | 所有人 | 正常資料上，模型若硬給根因並引用兩張「正常」卡，會出現 Low 信心的根因、可建工單 | 一律變灰卡「Insufficient evidence」（BUG-001）。灰卡畫面本身不變 |
| 2 | 所有人 | 查詢時段拉到 03:05 時，卡片寫「5 min of data missing」 | 03:00（情境當下）之後的分鐘不算缺值，不再出現這段字；真的缺值（如 N02）照樣顯示（BUG-002） |
| 3 | 所有人 | 任何人按 Reset 會取消**全場**正在跑的調查；有人在跑時別人按 Investigate 得到 409 | Reset **只取消自己這個瀏覽器**開的調查；不同人可以同時調查（公開使用者全服務同時最多 3 個） |
| 4 | 簡報者 | 無 | 新增**簡報者模式**：投影用的瀏覽器先開一次 `網址/?key=<金鑰>`，之後不受速率上限、不會被擋、別人取消不了（BUG-004）。金鑰由老闆保管 |
| 5 | 所有人 | 模擬資料的加熱功率可能顯示 102% | 百分比感測器最高 100%（BUG-007） |

## 新的錯誤訊息（英文介面原文，出現在紅色失敗框）

| 訊息 | 什麼時候 | 使用者該怎麼做 |
|---|---|---|
| `Your investigation is still running. Press Reset first.` | 同一個瀏覽器還有調查在跑又按 Investigate（例如重新整理頁面後） | 按 Reset（或鍵盤 R）再按 Investigate |
| `Too many investigations are running right now. Try again in a minute.` | 全服務已有 3 個公開調查在跑 | 等一分鐘再試 |
| `Rate limit reached. Try again later.` | 同一個 IP 一小時超過 20 次 | 等一小時；簡報者用簡報者模式 |
| `Service hourly limit reached. Try again later.` | 全服務一小時超過 60 次（費用上限） | 等一小時 |

## 新設定（`.env.example`、Cloud Run 環境變數）

| 設定 | 預設 | 用途 |
|---|---|---|
| `PRESENTER_KEY` | 空（關閉） | 簡報者金鑰，機密，放 Secret Manager；至少 16 字元 |
| `GLOBAL_RATE_LIMIT_PER_HOUR` | 60 | 全服務每小時可開始的調查數，費用天花板（Felix 依每次成本調整） |
| `TRUSTED_PROXY_HOPS` | 1 | 從 `X-Forwarded-For` 取真 IP 的位置；Cloud Run 用 1 |
| `MAX_CONCURRENT_INVESTIGATIONS` | 3 | 公開使用者同時進行的調查上限 |

其他行為：被 409 拒絕的請求不再扣速率配額（BUG-005）；模型輸出格式錯誤時不會再把字串拆成單一字元顯示（BUG-006）；`line` 參數只收 1/2/3 的數字（BUG-008）。這三項使用者一般看不到。

## 手冊建議補充（Paula）

1. **Demo 當天準備**：上台前在投影電腦開一次 `/?key=...`，開 `/api/config` 確認 `"presenter": true`；不要在投影畫面上輸入金鑰；換瀏覽器／無痕視窗／清 cookie 要重開。
2. **Reset 的說明**改成「重置畫面並取消你自己這次的調查」。
3. 評審掃 QR 或自己試用不會再影響簡報者大螢幕（test-plan 第 6 節「QR 出現後不要讓評審回首頁操作」這條限制可以放寬，請 Quinn 實測後決定）。
4. 若 PRD 或手冊寫了「同時只允許一個調查」，請改成「每個瀏覽器同時一個，全服務同時最多 3 個」。

## 需要其他人跟進

- Quinn：`docs/qa/test-plan.md` 的「目前結果」與各案例狀態請更新；上線後照 deploy.md 5.1 實測偽造標頭。
- Felix：拿到每次調查成本（ENH-002）後，定 `GLOBAL_RATE_LIMIT_PER_HOUR`。
- Dana：畫面沒改。要不要在底列顯示「presenter」小標示由你決定（`/api/config` 已有 `presenter` 欄位）。
