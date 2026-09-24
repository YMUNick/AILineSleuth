# Pitch Script: LineSleuth, 3 minutes (English)

- Draft v0.1, 2026-09-24, Paula (PM)
- Sources: pitch lines agreed in `docs/meetings/2026-09-24-駭客松主題方向.md` (Sandy), storyboard narration in `docs/design/storyboard.md` (Dana), `docs/prd.md`
- Pairs with: `docs/pitch/pitch-deck.md` (slide numbers below), `docs/pitch/judge-qa.md`, `docs/manual/user-manual.md` Section 8 (presenter checklist)
- Pace: about 2.5 words per second, the same pace as the storyboard. Spoken text is about 420 words, which leaves about 10 seconds for clicks and slide changes.

## Placeholder legend

| Marker | Meaning | Rule |
|---|---|---|
| `[待訪談驗證]` | Pending interview validation | Replace only with a number or quote from a real interview (`docs/sales/interview-guide.md`). If there is still no number on pitch day, use the fallback line given in that segment. |
| `X` | Placeholder amount | Never fill with the assumed values in `docs/finance/roi-model.csv` |
| `[待實測]` | Pending measurement | Replace with measured regression / rehearsal results |

Do not read the markers aloud. They exist so nobody presents an unverified number as fact.

## Roles on stage

| Role | Does |
|---|---|
| Speaker | Delivers every line below |
| Driver (second finalist, if two attend) | Clicks the app, hands a phone to judges for the QR code, switches to the backup video if needed. If presenting alone, the speaker drives. |

---

## Timeline overview

| # | Time | Sec | Section | On screen | Storyboard frame |
|---|---|---|---|---|---|
| 1 | 0:00–0:20 | 20 | Opening and pain | Slide 2, then live app | ① |
| 2 | 0:20–0:25 | 5 | Solution: one button | Live app | ② |
| 3 | 0:25–1:05 | 40 | Evidence cards + Google Cloud tech | Live app | ③ |
| 4 | 1:05–1:20 | 15 | Root cause and confidence | Live app | ④ |
| 5 | 1:20–1:35 | 15 | Work order on a phone | Live app + phone | ⑤ |
| 6 | 1:35–2:00 | 25 | Trust test: Insufficient evidence | Live app | Extra (grey card) |
| 7 | 2:00–2:20 | 20 | Differentiation | Slide 8 | — |
| 8 | 2:20–2:35 | 15 | Business model | Slide 9 | — |
| 9 | 2:35–2:50 | 15 | Roadmap | Slide 10 | — |
| 10 | 2:50–3:00 | 10 | Closing | Slide 11 | Caption card |

---

## 1. Opening and pain (0:00–0:20, 20 s)

**Screen**: Slide 2 "3 a.m." At about 0:15 the driver switches to the live app, already loaded on `Line 2 over-temperature` and reset with `R`, so Line 2 is red and `Downtime` is running.

> It's 3 a.m. at a small contract factory in Southeast Asia. Line 2 just stopped. Every hour of downtime burns X `[待訪談驗證]`. The night supervisor is alone, and finding out why takes about 40 minutes `[待訪談驗證]` of digging through Excel and PLC logs.
> Here's Line 2, live.

**Fallback if no interview numbers by pitch day**
- Replace the "X" sentence with: "Every minute of downtime costs money."
- Replace "takes about 40 minutes" with: "can take up to 40 minutes". The slide must then show `*pending validation` next to the number (storyboard rule).
- If an interviewee approved a quote, say it here instead: "One plant manager told us: '[quote]'." Use it only with the quote permission recorded in the interview sheet.

## 2. Solution: one button (0:20–0:25, 5 s)

**Screen**: live app, storyboard frame ②. Click `Investigate` on "one button".

> This is LineSleuth. One button. No chat box, no prompt to write.

**Check**: the button turns into `Investigating…` and the first card shows `Querying…`.

## 3. Evidence cards and Google Cloud tech (0:25–1:05, 40 s)

**Screen**: live app, storyboard frame ③. Cards appear one by one. Around 0:50 open `View source rows` on the coolant flow card for about 3 seconds, then `Hide source rows`.

> Gemini doesn't write SQL. It picks from five fixed, tested queries, and every step becomes an evidence card.
> It all runs on Google Cloud: one Cloud Run service, Gemini on Vertex AI with function calling, and every query logged in Cloud Logging. The demo data sits in DuckDB inside the service, and the data layer can be swapped for BigQuery.
> The alarm fired at 3:00. Mold temperature went past the SOP limit. Coolant flow dropped to about 41 percent. Valve CV-2 has been stuck at 20 percent since 2:41.
> *(open source rows)* And every number traces back to the raw source rows. Right here.
> It also checked the 2:30 shift handover.

**Notes**
- The tech sentence goes first on purpose: it fills the seconds while the first cards load.
- Read the numbers **off the screen**. The storyboard values (41 percent, 20 percent, 2:41) are illustrative, and live values may differ slightly.
- If a card shows `Cached`, do not mention it. If a judge asks later, answer honestly: "That query timed out, so it shows the last verified result."

**Filler if the cards are slow** (after 45 s)
> Each query is logged, so we can replay any investigation step by step.

**Hard stop**: past 60 seconds in this segment, the driver switches to the backup video at frame ④ and the speaker continues the script unchanged.

## 4. Root cause and confidence (1:05–1:20, 15 s)

**Screen**: live app, storyboard frame ④. Point at the conclusion card, then at the `Ruled out` line.

> Root cause: cooling valve CV-2 stuck. Confidence is high, because three independent signals agree, and the shift change is ruled out, not ignored. That confidence is scored by our server from the evidence, not by the model.

## 5. Work order on a phone (1:20–1:35, 15 s)

**Screen**: live app, storyboard frame ⑤. Click `Create work order`; the driver hands a phone to a judge, or invites judges to scan.

> One click creates the work order. Scan it, and the technician has it on their phone, with the evidence attached. Look at the clock: *(read `Elapsed`)* seconds from alarm to work order.

**Notes**
- Say the real `Elapsed` number. Our measured median is 12.6 s per investigation (gemini-2.5-flash, `docs/qa/runs/README.md`); never quote a number the screen does not show.
- Never say "BigQuery is supported": the demo runs on DuckDB, and BigQuery is only "swappable".
- BUG-004 is fixed: with presenter mode on (manual 3.8), judges using the main page cannot cancel or block the big screen. Until Quinn verifies this on Cloud Run `[待實測]`, still ask judges to stay on the work order page (see manual 7.4).
- If the QR does not open: point to the short URL under the QR code, or show the driver's phone.

## 6. Trust test: Insufficient evidence (1:35–2:00, 25 s)

**Screen**: live app, storyboard extra frames. Click `Done`, press `2` (`Normal data (Line 1)`), click `Investigate Line 1`.

> Now the harder test. What if nothing is actually wrong?
> Same investigation, same five queries, on healthy data from Line 1.
> *(grey card appears)* It says "Insufficient evidence", shows exactly what it checked, and hands it back to a human. It won't make up a root cause. That's why a supervisor can trust it.

**If the grey card is slow**: move on to Segment 7 **with the app still on screen**, and come back with the last three sentences as soon as the grey card appears. Never skip the grey card; it is our trust proof.

## 7. Differentiation (2:00–2:20, 20 s)

**Screen**: Slide 8 (comparison).

> Siemens Industrial Copilot, Cognite and Google's Manufacturing Data Engine are powerful platforms for large plants that already run MES. We serve the small contract manufacturers whose data still lives in Excel and PLC CSV files, and "China plus one" is moving more production into Southeast Asia.

**Notes**
- Respectful tone. Google MDE is a Google product; frame it as "the platform they can grow into", not as a weaker product (see `judge-qa.md` Q3).
- Before the final, add one public source for the China+1 trend to the slide footnote `[待查證]`.

## 8. Business model (2:20–2:35, 15 s)

**Screen**: Slide 9.

> We charge a one-time onboarding fee to turn their Excel and PLC exports into clean data, plus a monthly subscription per production line, priced below the downtime it saves `[待訪談驗證]`.

**Notes**
- Say amounts only if they come from interviews: "X per line per month". Otherwise, keep the sentence without numbers.
- Pricing logic, if asked: subscription is a share of measured savings. The share and all inputs are assumptions in `docs/finance/roi-model.md`.

## 9. Roadmap (2:35–2:50, 15 s)

**Screen**: Slide 10, including the Vietnamese work order mock-up labelled "concept".

> Next: pilots with design-partner factories on their own de-identified data, direct Excel and PLC CSV import, and work orders in Vietnamese and Thai for operators on the floor. Later: multiple lines and multiple root causes.

## 10. Closing (2:50–3:00, 10 s)

**Screen**: Slide 11, caption card `Stoppage → root cause in ~12 s` / `Every conclusion backed by evidence.`

> From line stoppage to root cause in about twelve seconds, measured, and every conclusion comes with its evidence. We're LineSleuth. Thank you.

**Notes**
- "About twelve seconds" = measured median 12.6 s per investigation (gemini-2.5-flash, 10 root causes × 3 runs, `docs/qa/runs/README.md`).
- Only if interviews have validated the manual baseline, you may add before it: "Today that takes about forty minutes `[待訪談驗證]`." If there are still 0 interviews on 10/1, never say forty minutes.

---

## Timing contingency

| Situation | Action | Who |
|---|---|---|
| Behind by 10 s or more at 1:35 | Cut the roadmap to one sentence: "Next: pilots with design partners and Vietnamese and Thai work orders." | Speaker |
| Behind by 20 s or more at 2:00 | Also shorten Segment 8 to: "Onboarding fee, plus a monthly subscription per line." | Speaker |
| Segment 3 past 60 s, `Investigation failed`, rate limit message, network down | Switch to the backup video at the matching frame; keep speaking the script | Driver |
| Video will not play | Slide 5 fallback screenshots | Driver |

## Rehearsal checklist

- [ ] Three timed full runs, one with the network disconnected on purpose (test plan L4).
- [ ] Every `[待訪談驗證]` and `[待實測]` either replaced with a real number or switched to its fallback line.
- [ ] Words counted after edits: 450 words maximum.
- [ ] Presenter checklist in `docs/manual/user-manual.md` Section 8 done 10 minutes before going on stage, including presenter mode (`/api/config` shows `"presenter": true` on the projecting browser, set up off screen).
