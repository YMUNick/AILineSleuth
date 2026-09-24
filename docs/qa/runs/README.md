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
