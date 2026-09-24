# Real Gemini regression runs

All runs: project `ailinesleuth-2026`, `QUERY_BACKEND=local` (DuckDB), `GEMINI_TEMPERATURE=0`,
`GEMINI_MAX_RETRIES=4`, `GEMINI_RETRY_BACKOFF_S=5`, `STEP_TIMEOUT_S=40`.

| Date | Model | Scope | Result | Median time / investigation | Retries (429 / timeout) |
|---|---|---|---|---|---|
| 2026-09-24 | gemini-3.8-flash | R01, N01 × 10, `--pause 20` | GATE FAIL: R01 10/10, N01 9/10 (1 over time budget) | R01 45 s, N01 136 s (max 201 s) | 28 |
| 2026-09-24 | gemini-2.5-flash | R01, N01 × 10, `--pause 20` | GATE PASS: 20/20 | R01 10.8 s, N01 11.6 s | 0 |
| 2026-09-24 | gemini-2.5-flash | Full set (10 root causes incl. 3 distractors + 2 healthy) × 3, `--pause 5` | **GATE PASS: 10/10 root causes, 2/2 insufficient evidence, no inconsistency, 0 failures** | 12.6 s (max 18.6 s) | 0 |

Median tokens per investigation (gemini-2.5-flash, R01/N01 × 10) for `docs/finance/roi-model.csv` row 15:
R01 input 5,686 / output 284 / thinking 1,749; N01 input 15,710 / output 277 / thinking 1,323.

An earlier unpaced run on gemini-3.8-flash (not kept) had every completed investigation correct
but 10 of 20 failed on 429 / timeouts. Not yet covered: BigQuery backend, Cloud Run, phone QR scan.

## Cloud Run smoke test (2026-09-24)

Service `linesleuth`, region `asia-southeast1`, URL https://linesleuth-547147056278.asia-southeast1.run.app,
`AGENT_MODE=gemini`, `GEMINI_MODEL=gemini-2.5-flash`, `QUERY_BACKEND=local` (DuckDB baked into the image; BigQuery not switched on yet),
min-instances 0 / max-instances 1, presenter key in Secret Manager.

| Scenario | Result | Elapsed | Tokens (total) |
|---|---|---|---|
| R01 | root cause `cv_valve_stuck_closed`, confidence High | 12.3 s | 7,719 |
| N01 | insufficient evidence | 11.4 s | 17,310 |

Deck screenshots in `docs/pitch/deck/assets/` were re-captured from this deployment (real Gemini, no fixture banner).
Found: Cloud Run's front end reserves `/healthz` (returns 404); `/health` added as the health route.
Not yet: phone QR scan on a real device, BigQuery backend, X-Forwarded-For spoof check (deploy.md 5.1).

## Redeploy after meeting 3 (2026-09-24, revision linesleuth-00005)

- A1 on the live service at 1280×720: 5 evidence rows visible in the first screen after the conclusion (bar: 3).
- `DAILY_INVESTIGATION_LIMIT=200` set on the service; in-process counter resets when the instance scales to zero (min 0), so a GCP-side Vertex AI quota is still needed as the hard cap.
- `/health` returns 200.
