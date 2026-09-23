# LineSleuth User Manual

- Product: LineSleuth (working name, pending decision PRD Q7)
- Version: draft v0.2, 2026-09-24, prototype for AI Builder Cup 2026 (Manufacturing). v0.2 reflects Eddie's fixes for BUG-001 to BUG-008.
- Owner: Paula (PM). Visual polish: Dana (Design).
- Sources: `docs/prd.md`, `docs/design/storyboard.md` (final English UI copy), `docs/engineering/architecture.md`, `docs/engineering/deploy.md`, `docs/engineering/changes-bugfix.md`, `README.md`, `.env.example`, `docs/qa/bugs.md`, `docs/qa/test-plan.md`
- Language: English for judges in Singapore. A Traditional Chinese summary for the team is in Section 12.

## Placeholder legend

Read this first. Numbers in this manual are **not** facts until the marker is removed.

| Marker | Meaning | Who removes it |
|---|---|---|
| `[待訪談驗證]` | Pending interview validation. Business numbers (for example "40 minutes", cost per hour of downtime) are assumptions until plant managers confirm them. | Sandy / Felix after interviews |
| `X` | Placeholder amount. Do not replace with an assumed value. | Felix |
| `[待實測]` | Pending measurement. Performance numbers (for example "90 seconds") are product targets, not measured results. Also used for bug fixes that can only be verified on the deployed Cloud Run service (BUG-003, BUG-004). | Quinn after regression, rehearsal and the post-deployment checks in `docs/engineering/deploy.md` §6 |

---

## 1. What is LineSleuth

LineSleuth is an investigation copilot for **night-shift supervisors at small contract manufacturers** in Southeast Asia and Taiwan: plants without MES, where machine data still lives in Excel sheets and PLC CSV exports.

When a line stops, the supervisor presses **one button**. LineSleuth then:

1. Lets Gemini (Vertex AI) investigate by choosing from **five fixed, tested queries** on the plant data. Gemini never writes SQL.
2. Shows every query as an **evidence card**. Every number on a card traces back to the source rows.
3. Returns a **root cause with a confidence label** (High / Medium / Low), the evidence it used, and what it ruled out.
4. Says **"Insufficient evidence"** instead of guessing when the data does not support a conclusion.
5. Lets the supervisor create an English **work order** that a technician opens on their phone by scanning a QR code.

Goal: cut a stoppage investigation from 40 minutes `[待訪談驗證]` to 90 seconds `[待實測]`.

### 1.1 What the prototype is (and is not)

| The prototype is | The prototype is not |
|---|---|
| One demo plant with 3 lines, simulated data only | Connected to any real PLC, MES or sensor |
| Two demo scenarios: a Line 2 stoppage and a healthy Line 1 | A multi-plant or multi-line production system |
| Live queries and live Gemini reasoning on a fixed dataset | A scripted video (except in OFFLINE FIXTURE mode, see 3.3) |
| English UI and work orders | Localised (Vietnamese / Thai are roadmap only) |
| Open access, no login | Secured for real customer data |

---

## 2. Who should read what

| Role | What they do with LineSleuth | Read |
|---|---|---|
| **Night-shift supervisor** (product user, the person in our story) | Sees a stopped line, presses Investigate, reads the evidence and conclusion, decides whether to create a work order | Sections 4, 5, 6 |
| **Demo presenter** (the person running the live demo for judges) | Starts the app, runs the 90-second main story and the grey-card test, recovers from problems | Sections 3, 5, 7, 8, 10 |
| Maintenance technician / judge with a phone (secondary) | Scans the QR code and reads the work order | Section 5, step ⑤ |
| Developer | Installs, configures and deploys | Section 3, then `README.md` and `docs/engineering/` |

---

## 3. Quick start

### 3.1 Requirements

- Windows, macOS or Linux with **Python 3.11**
- For `gemini` mode: a Google Cloud project with Vertex AI enabled, and the Google Cloud CLI (`gcloud`)
- A phone on the same network, if you want to test the QR code locally

### 3.2 Run locally

These are the commands from `README.md` (Eddie's section). Run them from the project root.

```bash
py -3.11 -m venv .venv
.venv/Scripts/python -m pip install -r requirements-dev.txt
cp .env.example .env                      # edit GOOGLE_CLOUD_PROJECT; without GCP set AGENT_MODE=offline_fixture
.venv/Scripts/python -m app.data.generate # generate the simulated data (fixed seed; also auto-generated at start-up if missing)
.venv/Scripts/python -m uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000.

For `gemini` mode, sign in once before starting the server:

```bash
gcloud auth application-default login
```

### 3.3 Choose an agent mode: `offline_fixture` vs `gemini`

Set `AGENT_MODE` in `.env`.

| | `offline_fixture` | `gemini` |
|---|---|---|
| Needs Google Cloud | No | Yes (`gcloud auth application-default login`, project with Vertex AI) |
| Queries | Real, run on the local simulated data | Real, on local data or BigQuery (see 3.4) |
| Which queries to run, and the conclusion text | **Scripted** in `app/agent/offline_fixture.py` | **Decided live by Gemini** |
| Scenarios that work | Only the two demo scenarios | All scenarios (the UI shows the two demo scenarios) |
| How the screen looks | Yellow **OFFLINE FIXTURE** bar at the top; bottom bar `Agent: OFFLINE FIXTURE`; the phone work order also shows the bar | No yellow bar; bottom bar `Agent: <model name> · data: <backend>` |
| Use it for | UI work and rehearsing the click path without GCP | Demo, regression tests, submission |
| Allowed in front of judges | **Never** | Yes |

> Important: OFFLINE FIXTURE mode must never be used for the demo or the submission. The competition requires a working prototype, and our core claim is that every conclusion is produced live from evidence.

### 3.4 Choose a data backend: `local` vs `bigquery`

Set `QUERY_BACKEND` in `.env`.

| | `local` | `bigquery` |
|---|---|---|
| Where the data lives | In-memory DuckDB built from `app/data/generated/*.csv` | BigQuery dataset `linesleuth_demo`, loaded with `scripts/load_bigquery.py` |
| Source line under "View source rows" | `Source: linesleuth_demo (local DuckDB).…` | `Source: linesleuth_demo.…` |
| Work orders after a server restart | Lost | Kept (read back from the `work_orders` table) |
| Use it for | Development, tests | Deployed demo and submission |

### 3.5 Key settings

| Setting | Default | What it does |
|---|---|---|
| `AGENT_MODE` | `gemini` | See 3.3 |
| `QUERY_BACKEND` | `local` | See 3.4 |
| `GEMINI_MODEL` | `gemini-3-flash-preview` | Model ID. **Not yet verified**: confirm the current ID in Vertex AI Model Garden before the demo. |
| `STEP_TIMEOUT_S` | `20` | A query slower than this falls back to the last verified result (`Cached`) or fails |
| `INVESTIGATION_TIMEOUT_S` | `90` | An investigation longer than this ends as `Investigation failed`. It is never replaced by a made-up answer. |
| `RATE_LIMIT_PER_HOUR` | `20` | Maximum investigations started per IP address per hour |
| `GLOBAL_RATE_LIMIT_PER_HOUR` | `60` | Maximum investigations started per hour by all public users together. This is the real cost ceiling; Felix sets the final value once the cost per investigation is measured (ENH-002). |
| `TRUSTED_PROXY_HOPS` | `1` | Which `X-Forwarded-For` entry is treated as the user's real IP, counted from the right. Keep `1` on Cloud Run; `2` only behind an external load balancer (see `deploy.md` 5.1). |
| `MAX_CONCURRENT_INVESTIGATIONS` | `3` | Maximum public investigations running at the same time across the service. Each browser can run one at a time in any case. |
| `PRESENTER_KEY` | empty (off) | **Secret.** Turns on presenter mode (see 3.8). At least 16 characters. On Cloud Run it is stored in Secret Manager, never in `.env.example` or the container image. |
| `PUBLIC_BASE_URL` | empty | Base URL encoded in the work-order QR code (see 3.6) |

All settings with comments are in `.env.example`. Rejected requests (for example "still running") do not count toward the rate limits. The presenter's browser is not counted toward any of the limits above.

### 3.6 Test the QR code on your phone (local network)

A phone cannot open `localhost`. To scan the work order QR code locally:

1. Find your computer's LAN IP address (for example `192.168.1.23`).
2. In `.env`, set `PUBLIC_BASE_URL=http://<your LAN IP>:8000`.
3. Start the server with `--host 0.0.0.0` added to the uvicorn command.
4. Connect the phone to the same Wi-Fi network.

### 3.7 Deployed version (Cloud Run)

Deployment is described step by step in `docs/engineering/deploy.md` (budget alerts first). After deployment, check:

- There is **no** yellow OFFLINE FIXTURE bar.
- The bottom bar reads `Agent: <model name> · data: bigquery`.
- `PUBLIC_BASE_URL` is set to the Cloud Run URL (or a short URL), so the QR code opens on phones.
- Quinn has run the two post-deployment checks in `deploy.md` §6 (items 5 and 6): the forged-header rate-limit test (BUG-003) and the presenter / Reset test from a second device (BUG-004). Until both pass, treat the related behaviour in this manual as `[待實測]`.

### 3.8 Presenter mode (demo day)

Presenter mode protects the big screen during a live demo. The browser that drives the projector is:

- not limited by the per-IP or service-wide rate limits (a shared venue IP or many rehearsals will not trigger `Rate limit reached`);
- never blocked because other people are running investigations;
- never cancelled when someone else presses `Reset`.

**Set it up before going on stage**

1. Make sure `PRESENTER_KEY` is set (locally in `.env`; on Cloud Run in Secret Manager, see `deploy.md` §4 and 5.2). The key is kept by the boss.
2. On the presenter's computer, in the browser you will project, open `<app URL>/?key=<PRESENTER_KEY>` once. The server stores the key in a cookie and sends you back to `/`, so the key does not stay in the address bar.
3. In the same browser, open `<app URL>/api/config` and check that it shows `"presenter": true`. A wrong key gives no error message; it simply shows `"presenter": false`.
4. Repeat steps 2 and 3 on every backup device you might switch to.

**Rules**

- Never type the key on the projected screen. Never put a `?key=` URL in a QR code, chat or slide.
- Presenter mode belongs to one browser. A different browser, an incognito window or cleared cookies need step 2 again. The cookie lasts 7 days.
- If the key leaks, Eddie's steps in `deploy.md` §4 replace it; the old presenter cookie stops working immediately, so repeat step 2 afterwards.
- The screen looks the same in presenter mode. There is no visible badge today (Dana may add one); `/api/config` is the only check.
- Cloud Run behaviour of presenter mode (cookies on the deployed HTTPS site, phones) is `[待實測]` until Quinn's check in `deploy.md` §6 item 6.

---

## 4. Screen tour

### 4.1 Main screen (big screen)

| Area | Location | What it shows |
|---|---|---|
| Top bar | Top | `LineSleuth` · `Demo Plant · Night shift`; `Scenario time` clock; `Demo scenario` chip |
| Alert banner | Top left | Red when a line is stopped (`Line 2 stopped`, machine, alarm, time, `Downtime` timer, `Investigate` button). Green when all lines run (`All lines running` / `No active alarms`). |
| Plant map | Left | Lines 1–3, machines M1 Feeder, M2 Dryer, M3 Molding, M4 Inspection. Legend: `Running` / `Warning` / `Stopped`. |
| Investigation panel | Right | Status chip, `Elapsed` timer, evidence cards, then the conclusion card or the grey card |
| Bottom bar | Bottom | `Scenario:` dropdown, `Reset`, and the agent mode / data backend |

### 4.2 Keyboard shortcuts

| Key | Action |
|---|---|
| `1` | Switch to `Line 2 over-temperature` (main story) and reset |
| `2` | Switch to `Normal data (Line 1)` (grey-card test) and reset |
| `R` | Reset the current scenario |
| `Esc` | Close the work order dialog |

Shortcuts do not work while the `Scenario:` dropdown has focus, or when Ctrl / Alt / Cmd is held.

### 4.3 Investigation status chip

| Chip | Meaning |
|---|---|
| `Not started` | Nothing has been run since the last reset |
| `Investigating` | Gemini is choosing and running queries |
| `Root cause found` | A conclusion card is shown |
| `Insufficient evidence` | A grey card is shown (see 6.2) |
| `Investigation failed` | Something went wrong; press Reset and try again (see Section 10) |

---

## 5. Step by step: the 90-second investigation

The steps follow the five storyboard frames in `docs/design/storyboard.md`. Times are the demo budget for a live Gemini run `[待實測]`.

| Step | Time | What happens | Feature |
|---|---|---|---|
| ① | 0:00–0:10 | Line 2 stops at 03:00; red machine, downtime timer running | F1 |
| ② | 0:10–0:15 | Press `Investigate` | F2 |
| ③ | 0:15–1:00 | Evidence cards appear one by one; open the source rows of one card | F3, F4 |
| ④ | 1:00–1:15 | Conclusion card with confidence label and ruled-out alternatives | F5 |
| ⑤ | 1:15–1:30 | `Create work order` → QR code → work order on a phone | F7 |
| Extra | +30 s | Switch to healthy data → `Investigate Line 1` → grey card | F8, F6 |

The card values quoted below come from the storyboard and are illustrative. Live values come from the simulated data and may differ slightly. Read them off the screen.

### Step ① The line stops

**You see**
- The plant map with Line 1 and Line 3 green (`RUNNING`), and **Line 2 · M3 Molding red (`STOPPED`)**.
- A red banner: `Line 2 stopped` / `M3 Molding · Over-temperature alarm at 03:00`.
- `Downtime` counting up next to the amber `Investigate` button.
- `Scenario time` starts at about 03:00:20. It is simulated plant time, not your local time.
- The Investigation panel is empty: `No investigation yet.`

**Presenter tip**: press `R` just before you switch to the app, so `Downtime` starts near `00:00:08` instead of showing how long the page has been open.

### Step ② Press Investigate

**Do**: click `Investigate`. There is no chat box and nothing to type.

**You see** (within about 1 second)
- The button turns grey and reads `Investigating…`. It cannot be pressed again during the run, which prevents duplicate runs and extra cost.
- A blue dashed outline around L2-M3: the machine under investigation.
- The chip changes to `Investigating` and `Elapsed 00:01` starts.
- The first card shows `Querying…`.

### Step ③ Read the evidence cards

**You see**: cards appear from top to bottom, one per query. Each card shows:

| Part | Example |
|---|---|
| Title | `Coolant flow vs. baseline` |
| Key value (amber = abnormal, red = alarm, white = normal) | `41%` |
| Detail | `of baseline since 02:41` |
| Query name · time range · row count | `compare_to_baseline · 02:30–03:00 · 12 rows` |
| State | `✓ Done`, `Cached` or `Failed` |
| Link | `View source rows (12)` |

Typical cards in the main story: `Alarm events`, `Mold temperature`, `Coolant flow vs. baseline`, `Cooling valve CV-2 position`, `Shift & maintenance log`. Gemini decides the order and the exact time ranges, so they can vary between runs.

**Do**: click `View source rows (n)` on the coolant flow card.
- A table of the raw rows opens. The rows behind the number are **highlighted in amber**.
- The footer reads `Source: <dataset.table> · <n> rows · query <query_id>`. The query ID matches the entry in Cloud Logging.
- Click `Hide source rows` to close it.

**Why it matters**: numbers on the cards are calculated by our code from the source rows. They are not written by the model. The model can only point to a card by its number.

**Tip**: if you scroll the panel with the mouse wheel, automatic scrolling stops for the rest of this run.

### Step ④ Read the conclusion

**You see** a conclusion card below the evidence:

| Part | Example |
|---|---|
| Root cause | `Cooling valve CV-2 stuck at 20% open` |
| Confidence | `Confidence: High` with three bars |
| Reason | `3 independent signals agree · 1 alternative ruled out` |
| Evidence | Buttons `#2` `#3` `#4`. Click one to jump to and highlight that card. |
| Ruled out | `Shift handover at 02:30 — no parameter changes (#5)` |
| Recommended actions | For example: open CV-2 manually per SOP 4.2; inspect the CV-2 actuator; restart Line 2 after mold temperature is below the limit |
| Button | `Create work order` |

Also on screen: the chip reads `Root cause found`; `Elapsed` stops at the real duration; cited cards get the tag `Cited in conclusion` and ruled-out cards get `Ruled out`; valve `CV-2` turns red on the plant map; the main button reads `Investigated`.

See 6.1 for how to read confidence labels.

### Step ⑤ Create the work order and open it on a phone

**Do**: click `Create work order`. A human decides when to create the work order; it is never created automatically.

**You see** a dialog:
- Left: a QR code, `Scan to open on your phone`, and the short URL (for typing by hand if scanning fails).
- Right: `Work order created`, `WO-<number>`, `Line 2 · M3 Molding`, the root cause, `Priority: High`.
- `Done` (or `Esc`) closes the dialog.

**On the phone**: scan the QR code. The page `/wo/<id>` opens without login and shows:

| Field | Content |
|---|---|
| Header | `WO-<number>`, `Open`, `Priority: High` |
| Line / Machine | `Line 2 · M3 Molding` |
| Detected | `03:00 (scenario time)` |
| Root cause, Confidence | Same as the conclusion card |
| Evidence, Ruled out, Recommended actions | Same as the conclusion card |
| SOP reference | For example `SOP 4.2 — Mold over-temperature` |
| Created | `<date time> UTC by LineSleuth` |
| Footer | `AI-generated from plant data. Verify on site before acting.` |

The phone page and the big screen use the same stored conclusion, so their text matches word for word. Pressing `Create work order` twice for the same investigation returns the same work order; it does not create a duplicate.

---

## 6. Reading the result

### 6.1 Confidence labels

Confidence is **calculated by the server from the evidence cards**, not chosen by the model.

| Label | Current rule (provisional, PRD Q4 still open) | What the supervisor should do |
|---|---|---|
| High | 3 or more cited cards show an abnormal signal | Act on the recommended actions, still following site safety rules |
| Medium | 2 cited cards show an abnormal signal | Check the cited cards before acting |
| Low | Only 1 cited card shows an abnormal signal | The card shows `Low confidence — verify on site before acting.` Treat it as a lead, not an answer. |

A root cause is only shown if it cites **at least 2 valid evidence cards** and **at least one of them shows an abnormal signal**. Otherwise the server turns the result into a grey card, whatever the model says. On healthy data, where every card is normal, the model therefore cannot push through a root cause (server-side rule added in the BUG-001 fix).

### 6.2 The "Insufficient evidence" grey card

**What you see**
- A grey card with a dashed border and a question-mark icon, titled `Insufficient evidence`.
- `No root cause found. LineSleuth will not guess.`
- `Checked`: a list of what was examined, for example
  - `Alarm events — none in window`
  - `Mold temperature — within normal range`
  - `Coolant flow — within normal range`
  - `Shift & maintenance log — no changes`
- `Recommended next step`: `Manual inspection of Line 1 by the shift supervisor.`
- The chip reads `Insufficient evidence`. There is **no** confidence label, **no** `Create work order` button, and no machine changes colour.

**What it means**
- LineSleuth ran its queries, and the data it checked does not support any root cause strongly enough.
- It is handing the decision back to a person rather than inventing an answer.

**What it does not mean**
- It does **not** mean "the line is fine". It means "nothing in the data I checked explains a problem". A fault could still exist in something the data does not cover (for example a mechanical issue with no sensor).
- It is **not** an error. An error shows `Investigation failed` instead.

**What to do**
1. Read the `Checked` list to see what has already been ruled out. You do not need to re-check those items.
2. Follow the recommended next step: inspect the line on site.
3. If you find the cause, record it manually. The prototype does not create a work order from a grey card.

**When you will see it**
- On healthy data: this is the expected result and the trust test we show judges on purpose.
- When data is missing: missing readings are never treated as a root cause.
- When the model proposes a root cause with fewer than 2 valid evidence cards, or cites only cards that look normal: the server overrides it.
- When the model returns a malformed answer (for example a missing or wrongly typed root cause): the server treats it as missing and shows the grey card instead of broken text.

### 6.3 How the grey card differs from other results

| Result | Looks like | Meaning | Next step |
|---|---|---|---|
| Root cause, High / Medium | Conclusion card, 3 or 2 bars | Evidence supports a cause | Review, then `Create work order` |
| Root cause, Low | Conclusion card with the Low warning | Weak evidence | Verify on site before acting |
| Insufficient evidence | Grey dashed card | Checked data does not support a cause | Manual inspection |
| Investigation failed | Red message `Investigation failed. Press Reset and try again.` | Technical failure (timeout, rate limit, authentication, etc.) | See Section 10 |
| `Cached` chip on a card | Amber chip; tooltip `Live query timed out. Showing last verified result.` | That single query timed out; the card shows the last verified result for the same query | Say so honestly if asked. Never present it as live. |
| `Failed` on a card | `Query failed` | That single query failed and had no cached result | The investigation continues with the other cards |

---

## 7. Switching scenarios and resetting

### 7.1 Scenarios

| Option in `Scenario:` | Shortcut | Story | Expected result |
|---|---|---|---|
| `Line 2 over-temperature` | `1` | Cooling valve CV-2 sticks at 02:41, mold overheats, line stops at 03:00 | Root cause: CV-2 stuck, High confidence, shift handover ruled out |
| `Normal data (Line 1)` | `2` | Everything within normal range; a shift handover at 02:30 | Grey card `Insufficient evidence` |

### 7.2 Switch scenario

1. Close the work order dialog if it is open (`Done` or `Esc`).
2. Choose the scenario in the `Scenario:` dropdown at the bottom left, or press `1` / `2`.
3. The screen resets automatically: plant map, banner, panel and timers.
4. On healthy data the button reads `Investigate Line 1`.

### 7.3 Reset

- Click `Reset` or press `R`.
- Reset clears the screen and cancels **your own** running investigation (the one started from this browser). It never affects other people's investigations.
- After an investigation finishes, the button stays `Investigated` (disabled). **To run again you must reset first.**
- If you reload the page while your investigation is still running and press `Investigate`, you get `Your investigation is still running. Press Reset first.` Press `R`, then `Investigate`.
- Datasets are fixed, but every new run queries and reasons live again, so results can take a different amount of time.

### 7.4 Several people using it at once

| Who | How many investigations at once | Who can cancel it |
|---|---|---|
| Any browser (public user) | 1 per browser; up to `MAX_CONCURRENT_INVESTIGATIONS` (default 3) public investigations across the whole service | Only the same browser, with `Reset` |
| Presenter's browser (presenter mode, 3.8) | 1, not counted toward the public limit | Only the presenter's browser |

What this means for the live demo:

- Judges who scan the QR code and try the main page on their phones no longer cancel or block the presenter's investigation. If the service is busy, **they** see `Too many investigations are running right now. Try again in a minute.`; the presenter does not.
- Without presenter mode, the presenter is a normal public user: other people cannot cancel the run, but the presenter can still hit the rate limits or the concurrency limit. Always set up presenter mode (3.8) for the demo.
- This behaviour is tested locally but is `[待實測]` on Cloud Run. Until Quinn completes `deploy.md` §6 item 6 and updates the test plan, keep the old precaution: ask judges to stay on the work order page during the live demo.

---

## 8. Presenter checklist

### 8.1 Ten minutes before the demo

- [ ] Presenter mode is on in the projecting browser (3.8): `/api/config` shows `"presenter": true`. Set it up off screen, before you connect the projector. Do the same on every backup device.
- [ ] Open the deployed URL. No yellow OFFLINE FIXTURE bar. Bottom bar shows `Agent: <model name> · data: bigquery`.
- [ ] Warm up: run `Line 2 over-temperature` once and `Normal data (Line 1)` once. This also fills the query cache used if a live query times out.
- [ ] Use your own phone hotspot, not venue Wi-Fi, to avoid venue network problems. (Presenter mode already stops a shared venue IP from hitting the rate limit.)
- [ ] The backup video (90-second main story + 30-second grey card) is stored **on the laptop**, one click away.
- [ ] A second phone is ready to scan the QR code, and the short URL is visible under the QR code.
- [ ] Press `1` to load the main story, then `R` just before you start.

### 8.2 When to switch to the backup video

| Situation | Action |
|---|---|
| Step ③ goes past 45 seconds | Keep talking with the filler line in the pitch script |
| Step ③ goes past 60 seconds | Switch to the backup video |
| `Investigation failed`, rate limit message, or no network | Switch to the backup video |
| The video cannot play either | Use the storyboard screenshots at the end of the deck |

---

## 9. FAQ

**Does LineSleuth write its own SQL?**
No. Gemini can only choose one of five fixed query functions (`get_alarm_events`, `get_sensor_window`, `compare_to_baseline`, `get_shift_log`, `list_sensors`) and fill in checked parameters. Invalid parameters are rejected, not guessed.

**Is the demo pre-recorded or scripted?**
In `gemini` mode, no. The dataset is fixed and simulated, but the queries and the Gemini reasoning run live each time you press Investigate. Only OFFLINE FIXTURE mode is scripted, and it is clearly labelled and never used for the demo.

**Why do I sometimes see different cards or times between runs?**
Gemini decides which queries to run and with which time ranges. The expected root cause should stay the same; our regression set runs each scenario 3 times to check consistency.

**Is the data real?**
No. All plant data is simulated and generated with a fixed seed. No customer data is used.

**Can a supervisor type a question?**
No. There is intentionally no chat box. The only input is the scenario.

**Why is there no work order button on the grey card?**
Without a supported root cause, a work order would spread a guess. The grey card sends the supervisor to inspect on site instead.

**Can two people use it at once?**
Yes. Each browser can run one investigation at a time, and up to 3 public investigations can run across the service at once. `Reset` only cancels your own investigation. The presenter's browser has its own protected slot. See 7.4.

**Does it support Vietnamese or Thai?**
Not in the prototype. The UI and work orders are English. Local-language work orders are on the roadmap.

**How long does an investigation take?**
Target: conclusion within 60 seconds, hard limit 90 seconds `[待實測]`. After 90 seconds the run ends as `Investigation failed`.

---

## 10. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Yellow `OFFLINE FIXTURE` bar at the top | `AGENT_MODE=offline_fixture` | Set `AGENT_MODE=gemini` and restart. Never demo in this mode. |
| `Investigation failed` right after pressing Investigate, in `gemini` mode | Not signed in to Google Cloud, wrong project, or model ID not available | Run `gcloud auth application-default login`; check `GOOGLE_CLOUD_PROJECT` and `GEMINI_MODEL` in Vertex AI Model Garden |
| `Investigation failed` after a long wait | A Gemini turn took over 20 seconds, or the whole run exceeded 90 seconds. Gemini turns have no cached fallback. | Press `R` and try again; in a live demo, switch to the backup video |
| Message `Rate limit reached. Try again later.` | More than `RATE_LIMIT_PER_HOUR` investigations from this IP in the last hour (rehearsals count; a shared venue IP counts for everyone) | Wait up to an hour. The presenter should use presenter mode (3.8), which is never rate limited. |
| Message `Service hourly limit reached. Try again later.` | All public users together started more than `GLOBAL_RATE_LIMIT_PER_HOUR` investigations in the last hour (the cost ceiling) | Wait up to an hour. Presenter mode is not affected. |
| Message `Your investigation is still running. Press Reset first.` | This browser already has a running investigation, for example after reloading the page | Press `R`, then Investigate again |
| Message `Too many investigations are running right now. Try again in a minute.` | `MAX_CONCURRENT_INVESTIGATIONS` public investigations are already running | Wait a minute and try again. Presenter mode is not affected. See 7.4. |
| `/api/config` shows `"presenter": false` in the presenter's browser | Wrong key, `PRESENTER_KEY` not set on the server, a different browser or incognito window, cleared cookies, or the key was replaced | Open `/?key=<PRESENTER_KEY>` again in this browser (3.8) |
| `Investigate` button stays grey (`Investigated`) | The previous run has finished | Press `R` |
| The phone cannot open the QR link locally | The QR contains `localhost`, or the phone is on another network | Set `PUBLIC_BASE_URL`, start with `--host 0.0.0.0`, use the same Wi-Fi (3.6); allow port 8000 through the firewall |
| The phone cannot open the QR link on Cloud Run | `PUBLIC_BASE_URL` not set, or venue network blocks it | Set `PUBLIC_BASE_URL` (see `deploy.md` §5); type the short URL; or show the presenter's own phone |
| `Work order not found` on the phone | The server restarted with the `local` backend (work orders are kept in memory), or the link was mistyped | Use the `bigquery` backend for demos; create the work order again |
| `Could not create work order. Try again.` | Temporary backend error | Click `Try again` |
| A card shows `Cached` | That query timed out (over 20 seconds) and the last verified result was used | Normal fallback. Say so honestly if asked. |
| A card shows a percentage above 100% | Simulated data generated before the BUG-007 fix is still in use | Re-run `python -m app.data.generate`; for the `bigquery` backend, reload with `scripts.load_bigquery` afterwards |
| Source line under "View source rows" says `(local DuckDB)` | Running on the `local` backend | Use `QUERY_BACKEND=bigquery` for the demo |
| Downtime timer shows a large number at the start | The page was loaded long ago | Press `R` just before presenting |
| Font looks different | Inter font could not load (offline) | Cosmetic only |

---

## 11. Limitations and known issues

### 11.1 Prototype limitations (by design, MVP scope)

| Limitation | Why | Roadmap |
|---|---|---|
| Simulated data only; no PLC / MES / sensor connection | MVP scope; no customer data in the prototype | Excel / PLC CSV import with design partners |
| Two demo scenarios on one plant (10 more scenarios exist only for regression tests) | One story, done well | Multi-line |
| One root cause per investigation | `submit_conclusion` accepts one cause; other abnormal cards stay visible on the timeline | Multi-root-cause |
| English only | Judges and MVP scope | Vietnamese / Thai work orders |
| No login; work order links are open to anyone with the URL; the presenter is recognised only by a shared key stored in a browser cookie | MVP scope; acceptable only for simulated data | Accounts and permissions before any real data |
| One investigation per browser, up to 3 public investigations at once; state is kept in memory; a single Cloud Run instance | Simplicity and cost cap | Per-user accounts |
| Rate limits are a cost ceiling, not a spending stop; budget alerts only notify | Prototype on a small budget | Final `GLOBAL_RATE_LIMIT_PER_HOUR` once the cost per investigation is measured (ENH-002) |
| A slow Gemini turn (over 20 s) has no cached fallback; only individual queries do | Queries and Gemini must run live | ENH-003 |
| Query cache is in memory and empty after a restart | Simplicity | — |
| Confidence rule is provisional | PRD Q4 still open | Final rule by 10/8 |
| Gemini model ID and BigQuery backend not yet verified on Google Cloud | No GCP access yet (as of 2026-09-24) | Verify on the day GCP is opened |
| Performance numbers (first card ≤ 10 s, conclusion ≤ 60 s, cold start) not measured | No deployment yet | `[待實測]` |

### 11.2 Known issues

Sources: `docs/qa/bugs.md` (Quinn) and `docs/engineering/changes-bugfix.md` (Eddie), both 2026-09-24.

**All eight bugs Quinn reported (BUG-001 to BUG-008) are fixed** and covered by automated tests (`pytest`: 87 passed, 1 skipped for live Gemini). They are no longer known issues. What still needs checking:

| Item | Status | What is still open | Owner |
|---|---|---|---|
| BUG-003 real client IP on Cloud Run (rate limit cannot be bypassed with a forged header) | Fixed, `[待實測]` on Cloud Run | The fix assumes Cloud Run appends the real IP at the end of `X-Forwarded-For`. Verify with the forged-header test in `deploy.md` 5.1 / §6 item 5. If it fails, do not go live. | Quinn |
| BUG-004 presenter mode and "Reset cancels only your own investigation" on Cloud Run | Fixed, `[待實測]` on Cloud Run | Cookie behaviour on the deployed HTTPS site and on real phones. Verify with `deploy.md` §6 item 6. Until then keep the precaution in 7.4. | Quinn |
| Test plan and demo precautions | Pending | `docs/qa/test-plan.md` results and the "judges must not return to the main page" rule (§6) are updated by Quinn after the live tests | Quinn |
| Regression results with live Gemini | `[待實測]` | The fixes were tested offline; the live regression set (`--repeat 3`) still has to pass on BigQuery | Quinn / Eddie |

Fixed in this round, for reference (users mostly will not notice):

| ID | What changed for users |
|---|---|
| BUG-001 | A root cause citing only normal cards now becomes a grey card (see 6.1) |
| BUG-002 | Minutes after the scenario time (03:00) no longer show as `min of data missing`; real gaps are still shown |
| BUG-003 | The rate limit uses the IP appended by Google's proxy; a service-wide hourly cap was added (3.5) |
| BUG-004 | Presenter mode (3.8); Reset only cancels your own investigation; several people can use the app at once (7.4) |
| BUG-005 | Rejected "still running" requests no longer use up the rate limit |
| BUG-006 | Malformed model output no longer shows as broken text; it is treated as missing |
| BUG-007 | Simulated percentage sensors stay within 0–100% (regenerate the data, see Section 10) |
| BUG-008 | Stricter internal check on the line number (not visible) |

Open improvements ENH-001 to ENH-005 in `docs/qa/bugs.md` (regression thresholds, token logging, Gemini timeout fallback, BigQuery timeout, adversarial scenarios) were not part of this round.

---

## 12. 繁中重點（給團隊）

- **定位**：給沒有 MES、資料還在 Excel／PLC CSV 的中小代工廠夜班主管；一個按鈕，Gemini 從 5 個固定查詢函式挑選執行，不寫 SQL。
- **兩種模式**：`offline_fixture` 只給沒有 GCP 時做 UI，畫面有黃色 OFFLINE FIXTURE 條，**絕對不能 demo 或繳交**；`gemini` 才是真的即時推論。demo 前確認底列顯示 `Agent: <模型名> · data: bigquery`。
- **操作五步**：產線亮紅燈 → 按 Investigate → 證據卡逐張出現（點開 View source rows 看原始列高亮）→ 結論＋信心標籤＋排除項 → Create work order → 手機掃 QR 看英文工單。
- **灰卡**：代表「查過的資料不足以支持任何根因」，**不是**「產線沒問題」、也不是錯誤；照 Checked 清單略過已查項目，改人工巡檢；灰卡不會產工單。
- **重置**：調查結束後按鈕會停在 Investigated，要按 `R` 才能再跑；`1` 主線、`2` 正常資料。Reset 現在只取消**自己這個瀏覽器**的調查；每個瀏覽器同時 1 個、全服務公開調查同時最多 3 個。
- **簡報者模式**（3.8）：上台前在投影用瀏覽器開一次 `網址/?key=<金鑰>`，再開 `/api/config` 確認 `"presenter": true`；不受速率上限、別人擋不住也取消不了。金鑰由老闆保管，不可出現在投影畫面、QR 或簡報；換瀏覽器／無痕／清 cookie 要重開，備用裝置也要各開一次。
- **新設定**（3.5）：`GLOBAL_RATE_LIMIT_PER_HOUR`（全服務每小時上限，費用天花板，Felix 依成本定）、`TRUSTED_PROXY_HOPS`（Cloud Run 用 1）、`MAX_CONCURRENT_INVESTIGATIONS`（預設 3）、`PRESENTER_KEY`（放 Secret Manager）。
- **Bug 狀態**：BUG-001～008 已全部修好，不再列為已知問題。BUG-003、004 的 Cloud Run 行為標 `[待實測]`，要等 Quinn 照 `deploy.md` §6 第 5、6 點實測；實測前 demo 仍請評審停在工單頁。
- **數字紀律**：「40 分鐘」與停線損失標 `[待訪談驗證]`，「90 秒」標 `[待實測]`，金額用 X；訪談和實測完成前不可移除標記。
