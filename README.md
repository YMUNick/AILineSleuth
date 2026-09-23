# LineSleuth（暫定名）

給東南亞和台灣中小代工廠夜班主管用的異常調查 Copilot：一按 Investigate，Gemini 用固定查詢函式在 BigQuery 找證據、推出根因、開出工單，把停線調查從 40 分鐘縮到 90 秒，而且每個結論都查得到證據。

參賽：AI Builder Cup 2026（製造業主題），目標 10/17 繳交。

## 文件索引

- [產品需求 PRD](docs/prd.md)：定位、MVP 流程、功能 F1–F8、不做清單、Demo 劇本
- [Roadmap](docs/roadmap.md)：9/24–10/18 里程碑、停損點、老闆必做事項
- [會議紀錄 2026-09-24](docs/meetings/2026-09-24-駭客松主題方向.md)
- 業務：[訪談題綱](docs/sales/interview-guide.md)、[邀約訊息](docs/sales/outreach-message.md)
- 財務：[ROI 試算說明](docs/finance/roi-model.md)、[ROI 試算表](docs/finance/roi-model.csv)
- 設計（待建立）：`docs/design/storyboard.md`
- 測試（待建立）：`docs/qa/test-plan.md`

## 本機啟動（Eddie）

需要 Python 3.11。架構見 [docs/engineering/architecture.md](docs/engineering/architecture.md)，部署見 [docs/engineering/deploy.md](docs/engineering/deploy.md)。

```bash
py -3.11 -m venv .venv
.venv/Scripts/python -m pip install -r requirements-dev.txt
cp .env.example .env                      # 改 GOOGLE_CLOUD_PROJECT；沒有 GCP 先把 AGENT_MODE 改成 offline_fixture
.venv/Scripts/python -m app.data.generate # 產生模擬資料（固定 seed，啟動時缺檔也會自動產生）
.venv/Scripts/python -m uvicorn app.main:app --reload --port 8000
```

打開 http://localhost:8000 。鍵盤 `1` 主線、`2` 正常資料、`R` 重置。

- `AGENT_MODE=offline_fixture`：沒有 GCP 也能走完畫面，但結論是寫死的，畫面頂端會有黃色 **OFFLINE FIXTURE** 條，**不能拿來 demo 或繳交**。
- `AGENT_MODE=gemini`：真的呼叫 Vertex AI Gemini，需要先 `gcloud auth application-default login`。
- 測試：`.venv/Scripts/python -m pytest -q`；回歸集（需 Gemini）：`.venv/Scripts/python -m scripts.run_regression --repeat 3`
- 手機掃 QR 測試：`.env` 設 `PUBLIC_BASE_URL=http://<電腦區網 IP>:8000`，uvicorn 加 `--host 0.0.0.0`。
