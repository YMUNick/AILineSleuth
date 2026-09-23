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
4. 注意：預算警示**只通知、不會停機**。真正擋費用的是下面的 `max-instances=1`、程式內的速率限制（`RATE_LIMIT_PER_HOUR`）和 Investigate 按鈕在調查中不能重按。
5. 達 90% 時照 `docs/roadmap.md` 停損點 ③：調低 `RATE_LIMIT_PER_HOUR`、改用錄影 demo。

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

目前**沒有任何金鑰**：Vertex AI 和 BigQuery 都用服務帳號身分，不需要 API key，這是最安全的做法。
Secret Manager 先保留給之後可能出現的機密（例如外部通知服務的 token）。需要時：

```bash
printf "the-secret" | gcloud secrets create SOME_SECRET --data-file=-
gcloud secrets add-iam-policy-binding SOME_SECRET --member serviceAccount:$SA --role roles/secretmanager.secretAccessor
# 部署時加：--set-secrets SOME_SECRET=SOME_SECRET:latest
```

不要把任何金鑰寫進程式碼、Dockerfile 或 `.env.example`。

## 5. 部署

```bash
gcloud run deploy $SERVICE --source . --region $REGION \
  --service-account $SA \
  --min-instances 1 --max-instances 1 \
  --no-cpu-throttling \
  --cpu 1 --memory 1Gi --timeout 120 --concurrency 40 \
  --allow-unauthenticated \
  --set-env-vars AGENT_MODE=gemini,QUERY_BACKEND=bigquery,GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GOOGLE_CLOUD_LOCATION=global,GEMINI_MODEL=gemini-3-flash-preview,GEMINI_TEMPERATURE=0,BQ_DATASET=linesleuth_demo,RATE_LIMIT_PER_HOUR=20
```

參數理由：

| 參數 | 為什麼 |
|---|---|
| `--min-instances 1` | 避免冷啟動（PRD 非功能需求）。代價是常駐計費，請 Felix 算進預算。 |
| `--max-instances 1` | 調查狀態放在記憶體，多實例會找不到調查；同時也是費用上限。 |
| `--no-cpu-throttling` | 調查在背景執行緒跑，回應送出後 CPU 不能被降速，否則證據卡會卡住。 |
| `--timeout 120` | 單次請求上限；調查本身是背景執行，不受影響。 |

部署完拿到網址後，把 QR 用的網址補上（決賽可改成短網址）：

```bash
URL=$(gcloud run services describe $SERVICE --region $REGION --format 'value(status.url)')
gcloud run services update $SERVICE --region $REGION --update-env-vars PUBLIC_BASE_URL=$URL
```

## 6. 上線後檢查

1. 開 `$URL`，確認**沒有** OFFLINE FIXTURE 黃條，底列顯示 `Agent: <模型名>`。
2. 按 Investigate 跑主線與正常情境各一次。
3. Cloud Logging 查 `jsonPayload` 或文字 `"event": "query"`，確認每次函式呼叫都有記錄。
4. 本機對雲端資料跑回歸集：`AGENT_MODE=gemini QUERY_BACKEND=bigquery python -m scripts.run_regression --repeat 3`，≥ 9/10 且灰卡案例全過才算上線（PRD 第 9 節）。
5. 冷啟動實測、速率限制實測交給 Quinn 的上線前檢查清單。

## 7. 關掉（比賽結束）

```bash
gcloud run services update $SERVICE --region $REGION --min-instances 0
# 或整個刪掉：gcloud run services delete $SERVICE --region $REGION
```
