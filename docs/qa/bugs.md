# Bug 清單（交給 Eddie）

- 建立：2026-09-24，Quinn（QA）
- 來源：閱讀 `app/`、`scripts/` 程式＋離線實測（`.venv` 內 pytest、TestClient、DuckDB）。**沒有碰到真 Gemini、BigQuery、Cloud Run、瀏覽器。**
- 我沒有改任何 `app/` 程式。標 `xfail` 的測試在 `tests/test_qa_adversarial.py`，用 `strict=True`：修好後測試會變成 XPASS→失敗，請順手拿掉該測試的 `@pytest.mark.xfail`。
- 嚴重度：**High**＝會讓 demo 翻車、違反 PRD 驗收或費用失控；**Medium**＝demo 上看得到、傷信任；**Low**＝機率低或只影響回歸集。

| ID | 嚴重度 | 標題 | 自動化測試 | 建議期限 |
|---|---|---|---|---|
| BUG-001 | High | 只引用「正常」證據卡也能成立根因 | xfail ×2 | 10/8 |
| BUG-002 | Medium | 查詢時段超過 03:00 會把「未來」分鐘算成缺值 | xfail | 10/8 |
| BUG-003 | High | 速率限制可用偽造 `X-Forwarded-For` 繞過 | xfail | 10/13 |
| BUG-004 | High | 任何拿到網址的人都能卡住或取消簡報者的調查 | 無（設計問題） | 10/13 |
| BUG-005 | Low | 被 409 拒絕的請求仍扣速率配額 | xfail | 10/13 |
| BUG-006 | Low | 模型輸出型別不對時沒擋（字串被拆成字元、list 造成當機） | xfail | 10/10 |
| BUG-007 | Low | 模擬資料的百分比感測器超過 100% | xfail | 10/8 |
| BUG-008 | Low | `line` 參數接受 `True`、`2.7`、`"2"` | 無 | 有空再做 |
| ENH-001～005 | — | 回歸執行器門檻、token 記錄、Gemini 逾時、執行緒池、補情境 | — | 見下 |

---

## BUG-001（High）只引用「正常」證據卡也能成立根因

- **位置**：`app/agent/conclusion.py` `finalize()`：只檢查「有效引用 ≥ 2 張」，不檢查被引用的卡是不是異常。
- **重現**：N01（正常資料）跑 `get_alarm_events`、`get_sensor_window(mold_temp_c)`、`get_shift_log`，三張卡全是 normal；模型交 `status=root_cause, cited_evidence=[1,2]`。
- **實際**：`status=root_cause`、`Confidence: Low`、理由列 `0 independent signals agree`、priority `Medium`，而且 `Create work order` 按得下去。
- **預期**：PRD F6 雙向驗收「正常資料一定出灰卡」。被引用的卡裡沒有任何異常訊號時，伺服器要改成灰卡（和現在「引用 < 2」的處理一樣，加 note）。
- **為什麼 High**：這是 prompt injection 在正常資料上最可能的攻擊路徑（日誌寫「report root cause X」→模型照做並隨便引用兩張卡），伺服器端是最後一道防線。
- **建議規則**（也回答 PRD Q4 一部分）：被引用卡中 `tone != normal` 的張數 = 0 → 灰卡；= 1 → 最多 Low；信心規則其餘照舊。

## BUG-002（Medium）查詢時段超過 03:00 會把「未來」分鐘算成缺值

- **位置**：`app/queries/functions.py` `_get_sensor_window`、`_compare_to_baseline` 的 `expected`／`missing` 計算；資料只到 `DATA_END=03:00`。
- **重現**：R01 `get_sensor_window(line=2, M3, mold_temp_c, 02:30, 03:05)`。
- **實際**：卡片寫 `Above SOP 4.2 limit of 205 °C since 02:54 · 5 min of data missing`；N01 同樣查法，灰卡 Checked 會出現 `Mold temperature — within normal range, 5 min missing`。
- **預期**：情境時間（`incident.now`）之後的分鐘不算缺值；或直接拒絕 `end` 晚於情境時間。
- **為什麼要修**：Dana 的分鏡時間範圍寫的就是 `02:30–03:05`，警報在 03:00:12，Gemini 很可能選 03:05。主線卡片出現「資料缺漏」會讓評審懷疑資料品質，而灰卡上的缺值字樣會讓「它有認真查」的賣點打折。

## BUG-003（High）速率限制可用偽造 `X-Forwarded-For` 繞過

- **位置**：`app/main.py` `_client_ip()` 取 `X-Forwarded-For` 的**第一個**值。
- **重現**：每次請求帶不同的 `X-Forwarded-For: 10.0.0.N, 203.0.113.9`，上限設 2，連打 6 次全部 201。
- **說明**：Google 前端代理的慣例是把真實 IP **附加在後面**，前面的值由用戶端自己填，所以在 Cloud Run 上也能被偽造（上線後請實測確認）。
- **影響**：公開網址被腳本狂打，Gemini 費用沒有上限；預算警示只通知不停止。
- **建議**：改取 Google 附加的那一段（或用 uvicorn `--proxy-headers` 處理後的 `request.client.host`，但要先在 Cloud Run 上驗證拿到的是真 IP）；另外加一個**全服務每小時總上限**（不分 IP），這才是真正的費用天花板。

## BUG-004（High，設計問題）任何拿到網址的人都能卡住或取消簡報者的調查

- **位置**：`app/investigations.py` 全服務同時只允許 1 個 running 調查；`POST /api/reset` 不需任何身分。
- **重現**（TestClient）：簡報者（IP A）開始 R01 → 路人（IP B）按 Investigate 得到 `409 An investigation is already running`；路人打 `/api/reset` → 簡報者的調查變 `cancelled`。
- **情境**：決賽時評審掃 QR 會連到同一個網域，任何人回到首頁按 Investigate 或 Reset，簡報者的大螢幕就壞掉；繳交後評審各自試用時也會互相干擾（有人跑到一半、另一人看到 409）。
- **另外**：現場大家可能共用同一個 NAT 出口 IP，每小時 20 次是全場共用，彩排幾輪就可能碰到 429。
- **建議（擇一，改動由小到大）**：
  1. reset 只取消「自己開的」調查（前端送 investigation id）；start 遇到別人正在跑時，不回 409 而是另開一筆（max-instances=1 仍成立，記憶體夠用）。
  2. 決賽當天另設 `DEMO_KEY`：帶 key 的請求有獨立配額、不會被別人取消。
- 請 Eddie 評估後回覆，我會在 10/15 檢查清單實測。

## BUG-005（Low）被 409 拒絕的請求仍扣速率配額

- **位置**：`app/main.py` `start_investigation()` 先 `_rate_limit()` 再 `manager.start()`。
- **重現**：上限 3，連按 4 次 → `[201, 409, 409, 429]`。
- **建議**：成功 start 後才記一次，或 409 時退還。

## BUG-006（Low）模型輸出型別不對時沒擋

- **位置**：`app/agent/conclusion.py`。
- **重現**：`recommended_actions="Open valve"`（字串）→ 結論變成 `["O","p","e","n"]`；`root_cause_key=["a"]`（list）→ `TypeError: unhashable type`，調查變 failed。
- **說明**：Gemini 有 schema 約束，機率低，但 preview 模型偶爾會吐出不合 schema 的東西；輸出錯字元清單上大螢幕很難看。
- **建議**：`isinstance` 檢查，型別不對就當成缺欄位處理（→ 灰卡或 failed，不要亂顯示）。

## BUG-007（Low）模擬資料的百分比感測器超過 100%

- **位置**：`app/data/generate.py` 在 step 值上加高斯雜訊，沒有夾在 0–100。
- **實際**：R03 `heater_power_pct` 有 16 筆 > 100（最高 102.0%）；R10 `cv_position_pct` 11 筆 > 100（最高 100.5%）。卡片會顯示 `102%` 的加熱功率。
- **影響**：評審點開原始列看到 102% 會質疑資料真實性；也可能讓 Gemini 判斷怪異。
- **建議**：單位是 `%` 的感測器夾在 [0, 100]。改完 CSV 會重產，`test_generation_is_deterministic` 仍會過。

## BUG-008（Low）`line` 參數型別太寬鬆

- `_line()` 用 `int()`：`True`→1、`2.7`→2、`"2"`→2 都會被接受。Gemini 傳回的數字可能是 float（`2.0`），所以要接受整數值的 float，但 `bool` 與非整數要拒絕。沒寫測試，有空再改。

---

## 改善建議（非 bug，但影響會議要求）

| ID | 內容 | 為什麼 |
|---|---|---|
| ENH-001 | `scripts/run_regression.py` 門檻加兩條：**R01 必須 3/3 全對**；任何題目出現「錯的根因且 High 信心」直接 FAIL。JSON 輸出加每題的 `miss_type`（wrong_cause / false_grey / failed）。 | 現在允許的那 1 題失誤可能剛好是 demo 主線；錯的根因配 High 信心就是會議說的「一鍵放大錯誤」，比灰卡危險得多。 |
| ENH-002 | `gemini_agent.py` 的 `gemini_turn` log 加 `resp.usage_metadata`（input / output / thinking token）。 | 目前算不出每次調查成本，Felix 的預算和速率上限沒有依據。 |
| ENH-003 | Gemini 單輪逾時（20 秒）目前沒有快取退路，整個調查直接 failed。請在 `docs/engineering/architecture.md` 寫明「只有查詢步驟有快取退路」，PRD 的「每步都能退回快取」需要 Paula 同步改字。**不要**用「重播上一次成功的調查」當退路，除非畫面明確標示是重播，否則等於寫死。 | 會議底線：查詢與 Gemini 必須即時跑。 |
| ENH-004 | BigQuery 查詢加客戶端逾時（`result(timeout=...)` 或 job timeout）。 | `future.result(timeout)` 不會真的停掉執行緒；查詢池只有 4 條，BigQuery 卡住 4 次後後面全部排隊逾時。 |
| ENH-005 | 在 `app/data/scenarios.py` 補三個「對抗集」情境（不計入 10 題門檻，單獨報告）：**R11 雙異常**（可直接抄 `tests/test_qa_adversarial.py` 的 `QA_DBL`）、**N03 正常資料＋要求捏造根因的 injection**、**N04 正常資料＋越南文交班備註**。 | 會議要求測「雙異常、injection、越南文」，但現有 12 情境只有 R07 一題 injection，而且是在「本來就有真因」的資料上，最危險的「正常資料被 injection 騙出根因」沒有覆蓋。 |
