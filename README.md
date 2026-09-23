# LineSleuth（暫定名 / working name）

**Language / 語言**：English and 繁體中文 side by side. Each section gives the English text first, then 繁體中文. Commands and settings are listed only once and apply to both.
本文件為中英對照：每一段先英文、後繁體中文；指令與設定只列一次，兩種語言共用。

## About / 簡介

**English**: An incident-investigation copilot for night-shift supervisors at small and mid-sized contract manufacturers in Southeast Asia and Taiwan. Press Investigate once: Gemini finds evidence in BigQuery through fixed query functions, works out the root cause and opens a work order, cutting a line-stoppage investigation from 40 minutes `[待訪談驗證]` to 90 seconds `[待實測]`, with every conclusion traceable to its evidence.

**繁體中文**：給東南亞和台灣中小代工廠夜班主管用的異常調查 Copilot：一按 Investigate，Gemini 用固定查詢函式在 BigQuery 找證據、推出根因、開出工單，把停線調查從 40 分鐘 `[待訪談驗證]` 縮到 90 秒 `[待實測]`，而且每個結論都查得到證據。

**English**: Entry for AI Builder Cup 2026 (Manufacturing theme); submission target 10/17. Numbers marked `[待訪談驗證]` (pending interviews) or `[待實測]` (pending measurement) are targets, not verified facts.

**繁體中文**：參賽：AI Builder Cup 2026（製造業主題），目標 10/17 繳交。標 `[待訪談驗證]`、`[待實測]` 的數字是目標值，尚未驗證。

## Documentation index / 文件索引

| Area / 領域 | Documents / 文件 | English | 繁體中文 | Doc language / 文件語言 |
|---|---|---|---|---|
| Product / 產品 | [docs/prd.md](docs/prd.md) | Product requirements: positioning, MVP flow, features F1–F8, out-of-scope list, demo script | 產品需求 PRD：定位、MVP 流程、功能 F1–F8、不做清單、Demo 劇本 | 中文 |
| Roadmap | [docs/roadmap.md](docs/roadmap.md) | Milestones 9/24–10/18, stop-loss points, owner's to-dos | 9/24–10/18 里程碑、停損點、老闆必做事項 | 中文 |
| Manual / 使用手冊 | [docs/manual/user-manual.md](docs/manual/user-manual.md) | User manual: setup, 90-second walkthrough, presenter mode, troubleshooting, known issues | 使用手冊：安裝、90 秒操作流程、簡報者模式、疑難排解、已知問題（第 12 節為繁中重點） | English（§12 中文） |
| Pitch / 簡報 | [Pitch script](docs/pitch/pitch-script.md), [Pitch deck outline](docs/pitch/pitch-deck.md), [Judge Q&A](docs/pitch/judge-qa.md), [Submission summary](docs/pitch/submission-summary.md) | 3-minute pitch script, slide outline, judge questions and answers, text for the submission form | 3 分鐘講稿、簡報大綱、評審問答、繳交表單文字 | English |
| Design / 設計 | [Storyboard](docs/design/storyboard.md), [UI spec](docs/design/ui-spec.md), [UI v2 spec](docs/design/ui-v2-spec.md), [Line layout v2](docs/design/line-layout-v2.svg) | Demo storyboard with the final English UI copy, UI specification (v1, and v2: evidence charts, root cause on the map, breakpoints, Before/After), plant layout graphic | 分鏡稿（含最終英文 UI 文案）、UI 規格（v1，以及 v2：證據小圖、產線圖根因亮燈、斷點、前後對比）、產線配置圖 | 中文 |
| Engineering / 工程 | [Architecture](docs/engineering/architecture.md), [Deploy](docs/engineering/deploy.md), [Bug-fix changes](docs/engineering/changes-bugfix.md) | System architecture, Cloud Run deployment steps, change notes for BUG-001 to BUG-008 | 架構、Cloud Run 部署步驟、BUG-001～008 變更說明 | 中文 |
| QA / 測試 | [Test plan](docs/qa/test-plan.md), [Bug list](docs/qa/bugs.md), [Organizer inquiry draft](docs/qa/organizer-inquiry-draft.md) | Test plan, bug list with fix status, draft questions to the organizers | 測試計畫、bug 清單（含修正狀態）、寄給主辦的詢問信草稿 | 中文 |
| Finance / 財務 | [ROI model notes](docs/finance/roi-model.md), [ROI model (CSV)](docs/finance/roi-model.csv) | How the ROI model works, and the spreadsheet itself | ROI 試算說明、ROI 試算表 | 中文 |
| Sales / 業務 | [Interview guide](docs/sales/interview-guide.md), [Outreach message](docs/sales/outreach-message.md) | Plant-manager interview guide, outreach message templates | 廠長訪談題綱、邀約訊息範本 | 中文 |
| Meetings / 會議 | [2026-09-24 theme direction](docs/meetings/2026-09-24-駭客松主題方向.md) | Meeting notes: competition theme direction | 會議紀錄 2026-09-24：駭客松主題方向 | 中文 |

## Run locally / 本機啟動（Eddie）

**English**: Requires Python 3.11. Architecture: [docs/engineering/architecture.md](docs/engineering/architecture.md). Deployment: [docs/engineering/deploy.md](docs/engineering/deploy.md).

**繁體中文**：需要 Python 3.11。架構見 [docs/engineering/architecture.md](docs/engineering/architecture.md)，部署見 [docs/engineering/deploy.md](docs/engineering/deploy.md)。

```bash
py -3.11 -m venv .venv
.venv/Scripts/python -m pip install -r requirements-dev.txt
cp .env.example .env                      # 改 GOOGLE_CLOUD_PROJECT；沒有 GCP 先把 AGENT_MODE 改成 offline_fixture
.venv/Scripts/python -m app.data.generate # 產生模擬資料（固定 seed，啟動時缺檔也會自動產生）
.venv/Scripts/python -m uvicorn app.main:app --reload --port 8000
```

| Line / 行 | English | 繁體中文 |
|---|---|---|
| 1 | Create a Python 3.11 virtual environment | 建立 Python 3.11 虛擬環境 |
| 2 | Install dependencies, including test tools | 安裝套件（含測試工具） |
| 3 | Copy the settings template, then set `GOOGLE_CLOUD_PROJECT`. Without GCP, first change `AGENT_MODE` to `offline_fixture` | 複製設定檔範本，改 `GOOGLE_CLOUD_PROJECT`；沒有 GCP 先把 `AGENT_MODE` 改成 `offline_fixture` |
| 4 | Generate the simulated data (fixed seed; also generated automatically at start-up if the files are missing) | 產生模擬資料（固定 seed，啟動時缺檔也會自動產生） |
| 5 | Start the server | 啟動伺服器 |

**English**: Open http://localhost:8000 . Keyboard: `1` main story, `2` normal data, `R` reset, `S` Before/After summary (after a root cause is found).

**繁體中文**：打開 http://localhost:8000 。鍵盤 `1` 主線、`2` 正常資料、`R` 重置、`S` 收尾對比畫面（找到根因後才有作用）。

### Modes, tests and other commands / 模式、測試與其他指令

| Command or setting / 指令或設定 | English | 繁體中文 |
|---|---|---|
| `AGENT_MODE=offline_fixture` | Walk through the screens without GCP, but conclusions are scripted. A yellow **OFFLINE FIXTURE** bar appears at the top. **Never use it for the demo or the submission.** | 沒有 GCP 也能走完畫面，但結論是寫死的，畫面頂端會有黃色 **OFFLINE FIXTURE** 條，**不能拿來 demo 或繳交**。 |
| `AGENT_MODE=gemini`<br>`gcloud auth application-default login` | Calls Vertex AI Gemini for real. Sign in with the `gcloud` command first. | 真的呼叫 Vertex AI Gemini，需要先執行左欄的 `gcloud` 登入。 |
| `.venv/Scripts/python -m pytest -q` | Run the tests | 執行測試 |
| `.venv/Scripts/python -m scripts.run_regression --repeat 3` | Run the regression set (needs Gemini) | 回歸集（需 Gemini） |
| `.env`: `PUBLIC_BASE_URL=http://<電腦區網 IP>:8000`<br>uvicorn: `--host 0.0.0.0` | Test the work-order QR code with a phone: set `PUBLIC_BASE_URL` to your computer's LAN IP and add `--host 0.0.0.0` to the uvicorn command | 手機掃 QR 測試：`.env` 設 `PUBLIC_BASE_URL`，uvicorn 加 `--host 0.0.0.0` |
| `python -m app.data.generate`<br>`scripts.load_bigquery` | After changing `app/data/generate.py`, regenerate the data. Local CSV files are not updated automatically; for BigQuery, re-run `scripts.load_bigquery` as well. | 改過 `app/data/generate.py` 後要重跑產生資料（本機 CSV 不會自動更新；BigQuery 要重跑 `scripts.load_bigquery`）。 |

### Presenter mode (demo day) / 簡報者模式（demo 當天用）

```bash
.venv/Scripts/python -c "import secrets; print(secrets.token_urlsafe(24))"
```

**English**: Set `PRESENTER_KEY` in `.env` (at least 16 characters; generate it with the command above), then open `http://localhost:8000/?key=<金鑰>` (`<金鑰>` = your key) once in the browser used for the presentation. From then on that browser is not rate limited, is never blocked by other people's investigations, and nobody else's Reset can cancel it. It is set up when `/api/config` shows `"presenter": true`. In the cloud the key is stored in Secret Manager; see [deploy.md 5.2](docs/engineering/deploy.md).

**繁體中文**：`.env` 設 `PRESENTER_KEY`（至少 16 字元，用上面的指令產生），在簡報用的瀏覽器開一次 `http://localhost:8000/?key=<金鑰>`。這個瀏覽器之後不受速率上限、不會被別人的調查擋住，別人按 Reset 也取消不了；開 `/api/config` 看到 `"presenter": true` 就是設好了。雲端上金鑰放 Secret Manager，見 [deploy.md 5.2](docs/engineering/deploy.md)。

### Reset and running several investigations / Reset 與同時調查

**English**: Reset now cancels only the investigation started from **the same browser**. Public users can run 1 investigation per browser at a time, and at most `MAX_CONCURRENT_INVESTIGATIONS` across the whole service.

**繁體中文**：Reset 現在只會取消**同一個瀏覽器**開的調查；公開使用者每個瀏覽器同時 1 個、全服務同時最多 `MAX_CONCURRENT_INVESTIGATIONS` 個。

### Rate limits and settings / 速率限制與設定

| Setting / 設定 | Default / 預設 | English | 繁體中文 |
|---|---|---|---|
| `RATE_LIMIT_PER_HOUR` | `20` | Investigations per client IP per hour | 每 IP 每小時可開始的調查數 |
| `GLOBAL_RATE_LIMIT_PER_HOUR` | `60` | Investigations per hour across the whole service: the cost ceiling | 全服務每小時可開始的調查數，費用天花板 |
| `TRUSTED_PROXY_HOPS` | `1` | Which `X-Forwarded-For` entry is the client IP, counted from the right. Keep the default 1 on Cloud Run | 決定取 `X-Forwarded-For` 的哪一段當用戶端 IP（從右數），Cloud Run 用預設 1 |
| `MAX_CONCURRENT_INVESTIGATIONS` | `3` | Public investigations running at the same time | 公開使用者同時進行的調查上限 |
| `PRESENTER_KEY` | empty / 空（off / 關閉） | Presenter key (secret), see Presenter mode above | 簡報者金鑰（機密），見上方簡報者模式 |
| `MANUAL_BASELINE_MIN` | empty / 空 | "Before" minutes on the Recap summary screen (1–480). Only a number from interviews or a measured drill | 收尾畫面 Before 的人工調查分鐘數（1–480），只能填訪談或實測得到的數字 |
| `MANUAL_BASELINE_SOURCE` | empty / 空 | Where that number comes from (max 120 characters), shown as `Source: …` | 這個數字的出處（最多 120 字），畫面顯示為 `Source: …` |

**English**: The Recap (`Show summary` in the work-order window, or `S`) always shows the measured time of this investigation as "After". "Before" appears only when **both** `MANUAL_BASELINE_*` settings are set and valid; otherwise it shows `—` and "Not yet measured for this plant.", with no bars. There is no default number anywhere in the app. `/api/config` returns `manual_baseline` (`null` when not set).

**繁體中文**：收尾畫面（工單視窗的 `Show summary`，或按 `S`）的 After 一律是這次調查的實測時間；Before 只有在兩個 `MANUAL_BASELINE_*` **都**設定且合法時才顯示，否則顯示 `—` 和「Not yet measured for this plant.」，也不畫長條。程式裡沒有任何預設分鐘數。`/api/config` 會回傳 `manual_baseline`（沒設定時是 `null`）。

**English**: All new settings are documented in [.env.example](.env.example); the change notes are in [changes-bugfix.md](docs/engineering/changes-bugfix.md).

**繁體中文**：所有新設定見 [.env.example](.env.example)，變更說明見 [changes-bugfix.md](docs/engineering/changes-bugfix.md)。
