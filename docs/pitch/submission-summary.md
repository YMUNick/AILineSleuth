# Submission Summary: LineSleuth

- Draft v0.1, 2026-09-24, Paula (PM). Final wording due 10/16 (`docs/roadmap.md` W4); submission 10/17.
- Use: copy into the AI Builder Cup 2026 submission form. Field names and word limits in the form are not known yet; adjust lengths to the form.
- Placeholders: `[待訪談驗證]` pending interviews, `X` placeholder amount, `[待實測]` pending measurement. **Every marker must be replaced or its sentence removed before submitting.** Markers must never appear in the submitted text.

## Before you submit

- [ ] "40 minutes" and "X per hour" replaced with interview numbers, or those phrases removed (fallbacks below each version)
- [ ] "90 seconds" replaced with the measured median time, or changed to "under two minutes" only if measurements support it
- [ ] Regression score filled in from the latest `--repeat 3` run on BigQuery
- [ ] Cloud Run URL works, in `gemini` mode, with no OFFLINE FIXTURE bar
- [ ] Product name confirmed (PRD Q7); "working name" removed if confirmed
- [ ] Team members match the formal registration

## Project details

| Field | Content |
|---|---|
| Project name | LineSleuth (working name) |
| Theme | Manufacturing |
| Tagline | One button from line stoppage to root cause, with evidence you can check. |
| Google Cloud products | Cloud Run, BigQuery, Vertex AI (Gemini function calling), Cloud Logging, IAM, Cloud Billing budget alerts. Add Secret Manager only if the presenter key (`PRESENTER_KEY`) is actually stored there at submission (setup in `docs/engineering/deploy.md` §4). |
| Live prototype URL | `[Cloud Run URL]` |
| Demo video | `[video link]` |
| Team | `[registered members]` |

---

## Short version (about 100 words)

LineSleuth is an investigation copilot for night-shift supervisors at small contract manufacturers in Southeast Asia and Taiwan: plants without MES, whose data still lives in Excel and PLC exports. When a line stops, the supervisor presses one button. Gemini on Vertex AI investigates by calling five fixed, tested BigQuery queries; it never writes SQL. Every step appears as an evidence card that traces back to source rows, and the result is a root cause with a server-scored confidence label, or "Insufficient evidence" instead of a guess. One click creates a work order that technicians open by QR. Goal: 40 minutes `[待訪談驗證]` to 90 seconds `[待實測]`.

**Fallback last sentence** (if numbers are not validated): "Goal: turn a long manual investigation into a one-button check backed by evidence."

---

## Long version (about 300 words)

**Problem.** At 3 a.m. a line stops at a small contract factory. The night-shift supervisor is alone and spends about 40 minutes `[待訪談驗證]` digging through Excel sheets, PLC exports and shift logs to find out why, while every hour of downtime costs X `[待訪談驗證]`. Industrial AI platforms such as Siemens Industrial Copilot, Cognite and Google's Manufacturing Data Engine serve large plants that already run MES. Small contract manufacturers in Southeast Asia and Taiwan, many riding the "China plus one" shift, are not there yet.

**Solution.** LineSleuth gives the supervisor one button and no chat box. Gemini on Vertex AI investigates through function calling over five fixed, tested BigQuery queries; it never writes SQL. Each query becomes an evidence card whose numbers are computed from source rows the user can open. The conclusion shows the root cause, the cited evidence, what was ruled out, SOP-based actions, and a confidence label scored by the server, not the model. When the data does not support a cause, LineSleuth says "Insufficient evidence", lists what it checked and recommends a manual inspection instead of guessing. One click creates an English work order that a technician opens by scanning a QR code.

**Built on Google Cloud.** One Cloud Run service in Singapore, BigQuery for plant data and work orders, Vertex AI Gemini function calling at temperature 0, Cloud Logging for every query, least-privilege IAM, budget alerts, and per-IP plus service-wide rate limits.

**Status.** A working prototype on simulated data: one plant, a Line 2 stoppage and a healthy-data scenario. Queries and reasoning run live on every request. A regression set of 10 known root causes, 3 with distractors, scores `[待實測]`/10 (pass bar: 9/10).

**Business model and next steps.** A one-time onboarding fee plus a monthly subscription per production line. Next: design-partner pilots on de-identified data, Excel and PLC CSV import, and Vietnamese and Thai work orders.

**Fallback for the first paragraph** (if numbers are not validated): replace the second sentence with "The night-shift supervisor is alone and has to dig through Excel sheets, PLC exports and shift logs to find out why, while the line stays down."
