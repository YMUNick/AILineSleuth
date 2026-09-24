# 部署：Cloud Run（老闆照做，Eddie 沒有實際執行過任何 gcloud 指令）

- 建立：2026-09-24，Eddie（工程）
- 以下指令會**建立雲端資源、可能產生費用**，請確認 Felix 的預算上限拍板後再跑。
- 變數先設好（Git Bash）：

```bash
export PROJECT_ID=your-gcp-project-id
export REGION=asia-southeast1          # 新加坡，決賽現場延遲最低
export SERVICE=linesleuth
export SA=linesleuth-run@${PROJECT_ID}.iam.gserviceaccount.com
gcloud config set project $PROJECT_ID
```

## 0. 第一天：預算警示（先做這個）

1. Console → Billing → Budgets & alerts → Create budget。
2. 範圍選這個專案；金額填老闆拍板的上限（PRD Q3）。
3. 門檻加三條：**50%、90%、100%**（actual spend），通知寄到老闆信箱。
4. 注意：預算警示**只通知、不會停機**。真正擋費用的是下面的 `max-instances=1`、程式內的速率限制（`RATE_LIMIT_PER_HOUR` 每 IP、`GLOBAL_RATE_LIMIT_PER_HOUR` 全服務，見 5.1）和 Investigate 按鈕在調查中不能重按。
5. 達 90% 時照 `docs/roadmap.md` 停損點 ③：調低 `GLOBAL_RATE_LIMIT_PER_HOUR`（和 `RATE_LIMIT_PER_HOUR`）、改用錄影 demo。

## 1. 開 API

```bash
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com \
  aiplatform.googleapis.com bigquery.googleapis.com secretmanager.googleapis.com logging.googleapis.com
```

## 2. 服務帳號（最小權限）

```bash
gcloud iam service-accounts create linesleuth-run --display-name "LineSleuth Cloud Run"
gcloud projects add-iam-policy-binding $PROJECT_ID --member serviceAccount:$SA --role roles/aiplatform.user
gcloud projects add-iam-policy-binding $PROJECT_ID --member serviceAccount:$SA --role roles/bigquery.jobUser
```

資料集層級權限（感測器資料唯讀、只能寫工單表）在第 3 步建好 dataset 後設定：

- dataset `linesleuth_demo` 給 `roles/bigquery.dataViewer`
- 表 `work_orders` 給 `roles/bigquery.dataEditor`（Console → 該表 → Share）

## 3. BigQuery 資料

```bash
gcloud auth application-default login
python -m app.data.generate
python -m scripts.load_bigquery --project $PROJECT_ID --dataset linesleuth_demo --location $REGION
```

## 4. Secret Manager

Vertex AI 和 BigQuery 都用服務帳號身分，不需要 API key。唯一的機密是**簡報者金鑰 `PRESENTER_KEY`**（BUG-004，用法見 5.2）。
金鑰直接產生後灌進 Secret Manager，不經過剪貼簿或 shell 歷史：

```bash
python -c "import secrets; print(secrets.token_urlsafe(24), end='')" | gcloud secrets create PRESENTER_KEY --data-file=-
gcloud secrets add-iam-policy-binding PRESENTER_KEY --member serviceAccount:$SA --role roles/secretmanager.secretAccessor
gcloud secrets versions access latest --secret PRESENTER_KEY   # 要用時再讀出來，存進密碼管理器
```

外洩時：`gcloud secrets versions add PRESENTER_KEY --data-file=-`（同樣用上面的 python 產生）後重新部署，舊的簡報者 cookie 立即失效。
不要把任何金鑰寫進程式碼、Dockerfile 或 `.env.example`。

## 5. 部署

```bash
gcloud run deploy $SERVICE --source . --region $REGION \
  --service-account $SA \
  --min-instances 1 --max-instances 1 \
  --no-cpu-throttling \
  --cpu 1 --memory 1Gi --timeout 120 --concurrency 40 \
  --allow-unauthenticated \
  --set-secrets PRESENTER_KEY=PRESENTER_KEY:latest \
  --set-env-vars AGENT_MODE=gemini,QUERY_BACKEND=bigquery,GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GOOGLE_CLOUD_LOCATION=global,GEMINI_MODEL=gemini-3-flash-preview,GEMINI_TEMPERATURE=0,BQ_DATASET=linesleuth_demo,RATE_LIMIT_PER_HOUR=20,GLOBAL_RATE_LIMIT_PER_HOUR=60,TRUSTED_PROXY_HOPS=1,MAX_CONCURRENT_INVESTIGATIONS=3,GEMINI_MAX_RETRIES=2,GEMINI_RETRY_BACKOFF_S=2
```

參數理由：

| 參數 | 為什麼 |
|---|---|
| `--min-instances 1` | 避免冷啟動（PRD 非功能需求）。代價是常駐計費，請 Felix 算進預算。 |
| `--max-instances 1` | 調查狀態放在記憶體，多實例會找不到調查；同時也是費用上限。 |
| `--no-cpu-throttling` | 調查在背景執行緒跑，回應送出後 CPU 不能被降速，否則證據卡會卡住。 |
| `--timeout 120` | 單次請求上限；調查本身是背景執行，不受影響。 |
| `--set-secrets PRESENTER_KEY=...` | 簡報者金鑰（5.2）。第 4 步沒建 secret 的話部署會失敗；暫時不用就拿掉這行。 |
| `GLOBAL_RATE_LIMIT_PER_HOUR=60` | 全服務每小時上限（5.1），真正的費用天花板。60 是暫定值，Felix 拿到每次調查成本後重算。 |
| `TRUSTED_PROXY_HOPS=1` | 直接用 `*.run.app` 網址時是 1（5.1）。 |
| `GEMINI_MAX_RETRIES=2`、`GEMINI_RETRY_BACKOFF_S=2` | Gemini 逾時／429／5xx 的重試上限，**整個調查合計** 2 次（等 2 秒、4 秒），用完調查就 failed，不會無限重試。一次調查最多呼叫 Gemini `MAX_AGENT_TURNS`＋2 次。細節見 `architecture.md` §6。 |

部署完拿到網址後，把 QR 用的網址補上（決賽可改成短網址）：

```bash
URL=$(gcloud run services describe $SERVICE --region $REGION --format 'value(status.url)')
gcloud run services update $SERVICE --region $REGION --update-env-vars PUBLIC_BASE_URL=$URL
```

### 5.1 速率限制與 X-Forwarded-For 可信位置（BUG-003）

- Cloud Run 前面是 **Google Front End（GFE）**。GFE 會把它看到的連線來源 IP **附加在 `X-Forwarded-For` 最後面**；用戶端自己送來的值會原樣留在前面，**可以偽造**。所以程式取「從右邊數第 `TRUSTED_PROXY_HOPS` 個」當用戶端 IP（`app/main.py` `_client_ip()`），前面的值一律不信。
  - 直接用 `https://<service>-<hash>.<region>.run.app`：只經過 GFE → `TRUSTED_PROXY_HOPS=1`（預設）。
  - 若之後改走外部 Application Load Balancer（例如自訂網域 + LB）：LB 的格式是 `<用戶端自填>,<client-ip>,<LB-IP>` → 設 `2`。
  - `0`＝完全不看這個標頭，只適合 uvicorn 前面沒有任何代理的情況（Cloud Run 上**不要**用）。
- Dockerfile 的 `--proxy-headers --forwarded-allow-ips="*"` 會讓 uvicorn 把 `request.client.host` 改成 `X-Forwarded-For` 的**第一個**值（可偽造），所以程式**不**拿它做速率限制；保留這組參數只是為了讓 `X-Forwarded-Proto` 生效（QR 網址用 https、cookie 加 Secure）。
- `RATE_LIMIT_PER_HOUR`（每 IP）擋單一來源；`GLOBAL_RATE_LIMIT_PER_HOUR`（不分 IP）是**真正的費用天花板**：就算攻擊者換很多真 IP，每小時最多也只會開這麼多次調查。每小時最大 Gemini 花費 ≈ 這個值 × 每次調查成本。被 409 拒絕的請求不扣配額（BUG-005）；簡報者（5.2）不計入也不受限。
- **上線後必須實測一次**（Quinn 檢查清單 ④；Eddie 沒在 Cloud Run 上看過實際標頭格式）。這會跑一次真的 N01 調查，花一次 Gemini 費用：

  ```bash
  curl -s -o /dev/null -w "%{http_code}\n" -X POST $URL/api/investigations \
    -H "Content-Type: application/json" -H "X-Forwarded-For: 1.2.3.4" -d '{"scenario_id":"N01"}'
  ```

  到 Cloud Logging 找這次的 `"event": "start"` 紀錄：
  - `client` 應該是**你自己的對外 IP**（和同一筆 request log 的 `httpRequest.remoteIp` 相同），`xff_entries` 應該是 `2`（偽造的 1.2.3.4 ＋ GFE 附加的真 IP）→ 通過。
  - `client` 是 `1.2.3.4` → GFE 沒有照預期附加，**不要上線**，回報 Eddie。
  - `client` 是 Google 的 IP（例如 `35.191.x.x`、`130.211.x.x`）且 `xff_entries` 是 `3` → 前面多一層代理，改 `TRUSTED_PROXY_HOPS=2` 後重測。

### 5.2 簡報者金鑰與「誰能取消調查」（BUG-004）

- 每個瀏覽器第一次按 Investigate 時，伺服器會發一個隨機的 `ls_sid` cookie（HttpOnly）。**Reset 只會取消這個瀏覽器自己開的調查**；別人按 Reset 或 Investigate 都動不到你的。
- 公開使用者：每個瀏覽器同時只能跑 1 個調查；全服務同時最多 `MAX_CONCURRENT_INVESTIGATIONS`（預設 3）個公開調查，超過回 409 `Too many investigations are running right now`。
- **簡報者**：簡報前在要投影的那台電腦瀏覽器開一次 `$URL/?key=<PRESENTER_KEY>`。伺服器驗證後設 7 天的 HttpOnly cookie，並把網址轉回 `/`（網址列不會留下金鑰）。確認：同一個瀏覽器開 `$URL/api/config` 看到 `"presenter": true`。之後這個瀏覽器：
  - 不受每 IP 與全服務上限影響（會場共用 NAT 也不會 429），也不佔公開同時調查數；
  - 不會因為別人正在跑調查而拿到 409；別人按 Reset 取消不了它。
- 注意：**在上台前設好**，不要在投影畫面上輸入金鑰；不要把帶 `?key=` 的網址做成 QR、貼到聊天或簡報。換瀏覽器、無痕視窗、清 cookie 都要重開一次。備用裝置也要各開一次。
- Cloud Run 的 request log 會記下完整網址（含 `?key=...`）。日誌只有專案成員看得到；決賽前後各換一次金鑰即可。
- 金鑰外洩：照第 4 步換新版本並重新部署，舊 cookie 立即失效。

### 5.3 收尾畫面的人工基準（`MANUAL_BASELINE_MIN`／`MANUAL_BASELINE_SOURCE`，UI v2）

- Recap（工單視窗的 `Show summary` 或按 `S`）的 After 一律是這次調查的實測秒數；Before 只有兩個變數**都**設定、分鐘數在 1–480、出處 ≤120 字時才顯示。任何一個沒設或不合法：`/api/config` 回 `manual_baseline: null`，畫面顯示 `—` 和 `Not yet measured for this plant.`，啟動 log 會有一行 `Recap shows no manual baseline: …` 的 warning（不會擋啟動）。
- **只能填訪談或實測得到的數字**（Sandy／Felix 提供，storyboard D6），並在 SOURCE 寫出處。沒有真實數字就不要設定。程式與 `.env.example` 都沒有預設值。
- 出處文字通常含空白和逗號，而 `--update-env-vars` 預設用逗號分隔，所以要換分隔符號（`^@^` 表示改用 `@`）：

  ```bash
  gcloud run services update $SERVICE --region $REGION \
    --update-env-vars "^@^MANUAL_BASELINE_MIN=<分鐘數>@MANUAL_BASELINE_SOURCE=<出處，例如訪談場次與月份>"
  ```

- 確認：`curl -s $URL/api/config` 看到 `"manual_baseline": {"minutes": …, "source": "…"}`。要拿掉：`--remove-env-vars MANUAL_BASELINE_MIN,MANUAL_BASELINE_SOURCE`。

## 6. 上線後檢查

1. 開 `$URL`，確認**沒有** OFFLINE FIXTURE 黃條，底列顯示 `Agent: <模型名>`。
2. 按 Investigate 跑主線與正常情境各一次。
3. Cloud Logging 查 `jsonPayload` 或文字 `"event": "query"`，確認每次函式呼叫都有記錄；查 `"event": "usage"`，確認每次調查都有 `turns` 和 input／output／thinking token（ENH-002，`architecture.md` §6.1）。出現 `"event": "gemini_retry"` 表示碰到逾時或 429，次數有上限（`GEMINI_MAX_RETRIES`）。
4. 本機對雲端資料跑回歸集：`AGENT_MODE=gemini QUERY_BACKEND=bigquery python -m scripts.run_regression --repeat 3`，≥ 9/10 且灰卡案例全過才算上線（PRD 第 9 節）。
5. 照 5.1 用偽造 `X-Forwarded-For` 打一次，確認 log 裡的 `client` 是真 IP。
6. 照 5.2 在簡報用瀏覽器開 `/?key=...`，`/api/config` 顯示 `"presenter": true`；再用手機（不同瀏覽器）按 Reset，確認大螢幕上的調查沒被取消。
7. 冷啟動實測、速率限制實測交給 Quinn 的上線前檢查清單。

## 7. 關掉（比賽結束）

```bash
gcloud run services update $SERVICE --region $REGION --min-instances 0
# 或整個刪掉：gcloud run services delete $SERVICE --region $REGION
```
