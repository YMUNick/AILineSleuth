# Pitch Deck Outline: LineSleuth

- Draft v0.1, 2026-09-24, Paula (PM). Visual design: Dana.
- Pairs with: `docs/pitch/pitch-script.md` (timing), `docs/pitch/judge-qa.md`, `docs/design/storyboard.md` (UI copy, caption cards), `docs/design/ui-spec.md` (colours, type)
- Style: dark background, amber for alerts and key numbers, Inter font, 2D flat visuals (same as the app). One idea per slide, and 25 words or fewer of slide text.
- Placeholders: `[待訪談驗證]` pending interviews, `X` placeholder amount, `[待實測]` pending measurement, `[待查證]` pending a public source. Any unvalidated number shown on a slide carries a visible `*pending validation` footnote.

## Two uses of this deck

| Use | Slides shown |
|---|---|
| **Live 3-minute pitch** (final, Singapore) | 1 → 2 → live app (demo) → 8 → 9 → 10 → 11. Slides 5 and 6 are fallbacks if the live app fails. |
| **Submission deck** (read by judges without us) | All 11 slides plus appendix |

## Slide list

| # | Title | Live pitch time |
|---|---|---|
| 1 | LineSleuth | Before 0:00 |
| 2 | 3 a.m. Line 2 stops | 0:00–0:15 |
| 3 | Who we serve | Submission only |
| 4 | One button: evidence, root cause, work order | Submission only |
| 5 | Live demo | 0:15–1:35 (app on screen; slide is fallback) |
| 6 | No evidence, no conclusion | 1:35–2:00 (app on screen; slide is fallback) |
| 7 | Built on Google Cloud | Submission only (spoken during the demo) |
| 8 | How we're different | 2:00–2:20 |
| 9 | Business model | 2:20–2:35 |
| 10 | Roadmap | 2:35–2:50 |
| 11 | Stoppage → root cause in ~12 s | 2:50–3:00 |
| A1 | Validation status | Appendix / Q&A |
| A2 | Known limitations | Appendix / Q&A |

---

## Slide 1: LineSleuth

**Key points**
- `LineSleuth`
- Tagline: "Root-cause investigations for small factories, with evidence you can check."
- Team names, AI Builder Cup 2026 · Manufacturing

**Suggested visual**: the plant map from `docs/design/line-layout.svg`, dimmed, with Line 2 M3 in red.

**Speaker notes**: on screen while we are introduced. Nothing to say.

---

## Slide 2: 3 a.m. Line 2 stops

**Key points**
- `03:00 — Line 2 stops.`
- Every hour of downtime: X `[待訪談驗證]`
- Finding the cause: 40 min `[待訪談驗證]` of Excel and PLC logs
- The night supervisor is alone

**Suggested visual**: large clock `03:00`, red status dot, a messy stack of Excel / CSV file icons. If an interviewee allowed a quote, show it in quotation marks with their approved attribution (for example "Plant manager, contract manufacturer, Vietnam").

**Speaker notes**: script Segment 1. If the numbers are still unvalidated, remove the X line and add `*pending validation` to "40 min". Switch to the live app at about 0:15.

---

## Slide 3: Who we serve

**Key points**
- Small contract manufacturers in Southeast Asia and Taiwan (about 50–300 staff)
- No MES; data in Excel sheets and PLC CSV exports
- At night, one supervisor decides alone; engineers are off site
- "China plus one" is moving production into Vietnam, Thailand, Malaysia `[待查證]`

**Suggested visual**: map of Taiwan and Southeast Asia with arrows from China; a persona card "Night-shift supervisor" with three pain points.

**Speaker notes**: submission only. Target plant size comes from the PRD and still needs interview confirmation `[待訪談驗證]`. Add a public source for China+1 before use.

---

## Slide 4: One button: evidence, root cause, work order

**Key points**
- Press **Investigate**: no chat box, no prompt
- Gemini picks from **5 fixed, tested queries**, never writes SQL
- Every step is an **evidence card** that traces back to source rows
- Root cause + **confidence label** + what was ruled out
- One click: **work order** on the technician's phone via QR

**Suggested visual**: the three app screens side by side (plant map with alert → evidence timeline → conclusion card and phone work order), numbered ① ② ③.

**Speaker notes**: submission only. In the live pitch this is shown by the app itself.

---

## Slide 5: Live demo

**Key points**
- Transition title: `Live: Line 2, 03:00`
- Fallback content: five screenshots, one per storyboard frame, each with its caption:
  1. `03:00 — Line 2 stops.`
  2. `One click. No prompt.`
  3. `Every number traces back to a source data row.` (demo data is DuckDB, swappable for BigQuery; never say BigQuery is supported)
  4. `Root cause + confidence + what was ruled out.`
  5. `Before → after*`, footnote: before-time pending interviews; after-time measured median 12.6 s per investigation (gemini-2.5-flash, `docs/qa/runs/README.md`)

**Suggested visual**: screenshot strip; a small link or QR to the backup video.

**Speaker notes**: script Segments 2–5. Only shown if the live app fails. The backup video is stored on the laptop, not streamed.

---

## Slide 6: No evidence, no conclusion

**Key points**
- On healthy data, LineSleuth answers **"Insufficient evidence"**
- It lists what it checked and hands the decision back to a human
- Guardrails:
  - Gemini can only call fixed queries with checked parameters
  - Numbers on cards come from source rows, not from the model
  - A root cause needs 2 or more evidence cards; confidence is scored by the server
  - Logs are treated as untrusted data (prompt-injection tested)

**Suggested visual**: the grey card (dashed border, question mark, `Checked` list) next to a High-confidence conclusion card. Caption: `No evidence, no conclusion.`

**Speaker notes**: script Segment 6 is the live version. For the submission deck, this slide is the trust argument; keep it.

---

## Slide 7: Built on Google Cloud

**Key points**
- **Cloud Run**: one service for UI and API, Singapore region (`asia-southeast1`)
- **DuckDB** (demo data, inside the Cloud Run image): plant data and the work order table; the data layer can be swapped for BigQuery (not "supported" yet)
- **Vertex AI Gemini**: function calling over 5 fixed queries, temperature 0
- **Cloud Logging**: every query and parameter is logged for replay
- **IAM**: least-privilege service account, no API keys in code
- **Secret Manager**: holds the presenter key (`PRESENTER_KEY`); show it only if the key is actually stored there at submission (`docs/engineering/deploy.md` §4)
- **Budget alerts** at 50 / 90 / 100%, plus a per-IP rate limit and a service-wide hourly cap

**Suggested visual**: simple architecture diagram: Browser / Phone → Cloud Run → (Vertex AI Gemini, DuckDB demo data "swappable for BigQuery") → Cloud Logging. Use official Google Cloud product icons.

**Speaker notes**: in the live pitch these words are spoken during Segment 3. Model name on the slide only after it is verified in Model Garden (`GEMINI_MODEL`); otherwise just say "Gemini".

---

## Slide 8: How we're different

**Key points**

| | Siemens Industrial Copilot | Cognite | Google MDE | **LineSleuth** |
|---|---|---|---|---|
| Built for | Large plants in the Siemens ecosystem `[待查證]` | Asset-heavy enterprises with data teams `[待查證]` | Plants building a data platform on Google Cloud `[待查證]` | **Small contract manufacturers without MES** |
| Data it starts from | Automation / MES data `[待查證]` | Industrial data platform `[待查證]` | Connected factory data `[待查證]` | **Excel sheets and PLC CSV exports** |
| Job to be done | Broad industrial assistant | Industrial data operations | Data engine | **One job: why did this line stop, with evidence** |
| Pricing model | Enterprise | Enterprise | Platform | **Onboarding fee + per-line monthly** |

**Suggested visual**: the table, with the LineSleuth column highlighted in amber. Optionally a two-axis chart: "company size" vs "data maturity", LineSleuth in the small / low-maturity corner.

**Speaker notes**: script Segment 7. Every competitor cell must be checked against the vendor's current public material before the final `[待查證]`. Never disparage. For MDE: "the platform our customers can grow into".

---

## Slide 9: Business model

**Key points**
- **Onboarding fee**: X, one-time, covers turning Excel / PLC exports into clean data `[待訪談驗證]`
- **Subscription**: X per production line per month `[待訪談驗證]`
- Priced below the downtime and labour it saves
- Buyer: plant manager or owner `[待訪談驗證]`

**Suggested visual**: two blocks ("One-time" and "Per line / month"); below them the value formula in words: incidents per month × time saved × downtime cost per hour × share of time spent searching `[待訪談驗證]`.

**Speaker notes**: script Segment 8. The formula and inputs are in `docs/finance/roi-model.md`; all inputs are assumptions, so show no numbers unless they come from interviews. Do not show gross margin: our Gemini and GCP costs are still `待估算`.

---

## Slide 10: Roadmap

**Key points**

| Now (prototype) | Next | Later |
|---|---|---|
| One plant, simulated data | Design-partner pilots on de-identified data | Multiple lines and plants |
| Main story + grey-card test | Excel / PLC CSV import | Multiple root causes in one investigation |
| English work order via QR | Vietnamese and Thai work orders | Push notifications to technicians |
| Regression set, 10 known root causes | Accounts and permissions before real data | Early warning before a stoppage |

**Suggested visual**: three columns; on the right a phone mock-up of a **Vietnamese work order**, clearly labelled "Concept — not in prototype".

**Speaker notes**: script Segment 9. No dates on "Next" and "Later"; they depend on design partners. Do not promise Vietnamese support on stage beyond "roadmap".

---

## Slide 11: Stoppage → root cause in ~12 s

**Key points**
- `Stoppage → root cause in ~12 s*`, footnote: measured median 12.6 s per investigation (gemini-2.5-flash, 10 root causes × 3 runs, `docs/qa/runs/README.md`); manual baseline pending interviews
- 40 min stays off the headline: footnote only, marked `[待訪談驗證]`; drop it entirely if there are still 0 interviews on 10/1
- `Every conclusion backed by evidence.`
- Ask: "We're looking for design-partner factories in Southeast Asia and Taiwan."
- Contact / QR to the live prototype

**Suggested visual**: the storyboard caption card, full-screen, dark background, amber arrow.

**Speaker notes**: script Segment 10. Stay on this slide during Q&A.

---

## Appendix A1: Validation status

**Key points**
- Regression set: 10 known root causes, including 3 distractors; pass bar ≥ 9/10, each run 3 times. Result: `[待實測]` / 10
- Healthy-data tests return "Insufficient evidence": `[待實測]`
- Median time to conclusion: 12.6 s (gemini-2.5-flash, full set × 3, `docs/qa/runs/README.md`)
- Plant manager interviews: `[待訪談驗證]` completed

**Suggested visual**: simple scorecard, green / grey ticks.

**Speaker notes**: use in Q&A for "does it really work?" and "did you talk to customers?". Only show measured results.

---

## Appendix A2: Known limitations

**Key points**
- Simulated data; no live PLC / MES connection yet
- One root cause per investigation
- English only
- No login in the prototype; not ready for real customer data

**Suggested visual**: plain list.

**Speaker notes**: being upfront about limits builds trust. Details in `docs/manual/user-manual.md` Section 11.
