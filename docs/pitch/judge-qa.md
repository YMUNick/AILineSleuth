# Judge Q&A: LineSleuth

- Draft v0.1, 2026-09-24, Paula (PM)
- Sources: `docs/meetings/2026-09-24-駭客松主題方向.md` (risks and challenges raised by Sandy and Quinn), `docs/prd.md`, `docs/engineering/architecture.md`, `docs/qa/test-plan.md`, `docs/qa/bugs.md`, `docs/finance/roi-model.md`
- Placeholders: `[待訪談驗證]` pending interviews, `X` placeholder amount, `[待實測]` pending measurement, `[待查證]` pending a public source.

## Answering rules

1. **30 seconds maximum per answer.** Answer first, then one piece of proof, then stop.
2. **Never state an unverified number as fact.** Say "we haven't validated that yet; here is how we're measuring it."
3. **Point to the screen.** Where possible, show the evidence card, the source rows or the grey card instead of describing them.
4. **Be respectful about competitors**, especially Google's own products. Our story is "a different customer", not "a better product".
5. **Admit limits.** "That's not in the prototype; it's on the roadmap" is a good answer.

## Index

| # | Category | Question |
|---|---|---|
| Q1 | Competition | How is this different from Siemens Industrial Copilot? |
| Q2 | Competition | What about Cognite? |
| Q3 | Competition | Why wouldn't a factory just use Google's Manufacturing Data Engine? |
| Q4 | Competition | Couldn't someone build this with ChatGPT or Gemini and a spreadsheet? |
| Q5 | Data | Your demo uses simulated data. Where does real data come from? |
| Q6 | Data | How long does it take to onboard a factory? |
| Q7 | Trust | How do you stop Gemini from hallucinating a root cause? |
| Q8 | Trust | What happens if the root cause is wrong? |
| Q9 | Trust | How is the confidence label calculated? |
| Q10 | Trust | What if two things fail at the same time? |
| Q11 | Trust | Could someone trick it with text in the logs (prompt injection)? |
| Q12 | Product | Is the demo scripted? |
| Q13 | Product | Aren't five fixed queries too limiting? |
| Q14 | Business | How do you make money, and how much will you charge? |
| Q15 | Business | Did you talk to real customers? |
| Q16 | Business | Who buys, and how do you reach them? |
| Q17 | Business | What does one investigation cost you? |
| Q18 | Privacy | Will factories trust you with their production data? |
| Q19 | Privacy | Anyone with the link can open a work order. Is that safe? |
| Q20 | Google Cloud | Why Google Cloud and Gemini? |
| Q21 | Product | Do you support Vietnamese or Thai? |
| Q22 | Team | Can a team this small build and support this? |

---

## Competition

### Q1. How is this different from Siemens Industrial Copilot?

**Answer**
> Siemens Industrial Copilot is a strong product for large plants that already run Siemens automation and MES. Our customer is a 50-to-300-person contract manufacturer that has no MES; its data is in Excel and PLC CSV exports. We do one job for them: when a line stops at night, find the cause with evidence. And we price per line per month, not as an enterprise rollout.

**Notes**: check Siemens' current public positioning before the final `[待查證]`. The plant size range is from the PRD and still needs interview confirmation `[待訪談驗證]`.

### Q2. What about Cognite?

**Answer**
> Cognite is an industrial data platform built for large asset-heavy companies with data teams. Our customers don't have a data team, or even a data platform. We start from the files they already export, and we give the night supervisor one button, not a platform.

**Notes**: `[待查證]` against Cognite's current website before use.

### Q3. Why wouldn't a factory just use Google's Manufacturing Data Engine?

**Answer**
> MDE is the right destination once a factory has connected machines and wants a full data platform. Most of our customers aren't there yet. LineSleuth runs on the same Google Cloud stack: BigQuery, Vertex AI, Cloud Run. So a customer who starts with us is already on the path to MDE. We see it as the platform they grow into, not a competitor.

**Notes**: judges may be Googlers. Never position MDE as weaker. `[待查證]` MDE's current scope before use.

### Q4. Couldn't someone build this with ChatGPT or Gemini and a spreadsheet?

**Answer**
> They could get an answer, but not one a supervisor can trust at 3 a.m. A chatbot writes its own queries and can invent numbers. In LineSleuth the model can only call five tested queries, every number is computed from the source rows, confidence is scored by our server, and on healthy data it says "Insufficient evidence". Let me show you the grey card.

**Notes**: switch to the app and press `2` if time allows.

---

## Data

### Q5. Your demo uses simulated data. Where does real data come from?

**Answer**
> From the files our customers already have: PLC CSV exports, alarm logs, shift logs in Excel. Onboarding means mapping those into the same four tables the demo uses. The simulated data follows that exact schema, so the queries don't change. Our next step is a pilot with a design-partner factory on one line's de-identified data.

**Notes**: be honest that no real factory data has been tested yet. The schema is in `docs/engineering/architecture.md` §3. Mention a design partner only if one has actually agreed `[待訪談驗證]`.

### Q6. How long does it take to onboard a factory?

**Answer**
> It depends on how clean their exports are. That's exactly why we charge a one-time onboarding fee: part of the job is organising their Excel and CSV files. We're measuring the real effort with our first design partners; we don't want to quote a number we haven't seen yet.

**Notes**: the person-day values in `roi-model.csv` are assumptions. Do not quote them `[待訪談驗證]`.

---

## Trust and hallucination

### Q7. How do you stop Gemini from hallucinating a root cause?

**Answer**
> Four layers. One: Gemini never writes SQL; it can only call five fixed queries, and parameters are checked against a whitelist. Two: the numbers on each card are computed by our code from source rows, and you can open those rows. Three: a root cause must cite at least two evidence cards, and the confidence label is calculated by our server, not chosen by the model. Four: if the evidence isn't there, it says "Insufficient evidence". We test this with a regression set of 10 known root causes, including 3 distractors, and require at least 9 out of 10 before deploying.

**Notes**: say the actual regression score only when measured: `[待實測]` / 10. Server-side rules are in `app/agent/conclusion.py`.

### Q8. What happens if the root cause is wrong?

**Answer**
> A person stays in the loop. The work order is only created when the supervisor clicks, the evidence is attached so the technician can check it, and the work order itself says "Verify on site before acting." Low-confidence results carry a visible warning. And in testing, a wrong answer with high confidence is our worst failure type: one occurrence blocks a release.

**Notes**: the "wrong + High blocks release" rule is in `docs/qa/test-plan.md` §2.3 item 5.

### Q9. How is the confidence label calculated?

**Answer**
> By the server, from the cited evidence cards. Right now: three or more abnormal signals is High, two is Medium, fewer is Low. The model's own opinion of its confidence is ignored.

**Notes**: the rule is provisional until PRD Q4 is closed. If it changes, update this answer. BUG-001 is fixed: if none of the cited cards shows an abnormal signal, the server turns the result into a grey card, so a model cannot push a root cause through on healthy data. Claim "normal data always gives a grey card" only after the grey-card cases pass the live regression run `[待實測]`.

### Q10. What if two things fail at the same time?

**Answer**
> Every abnormal signal still shows up as its own evidence card on the timeline, so the supervisor sees both. The conclusion picks the most direct cause. Handling multiple root causes in one conclusion is on our roadmap.

**Notes**: answer taken from `docs/qa/test-plan.md` §3.2.

### Q11. Could someone trick it with text in the logs (prompt injection)?

**Answer**
> There's no text box, so the only way in is through the data, like an operator note. The system prompt treats all log text as untrusted data, the model can only call fixed queries, and the server enforces the evidence rules on whatever it returns. One of our regression cases hides an "ignore all previous instructions" line in an operator note, and the correct answer is still required.

**Notes**: regression case R07. Say "passes" only once R07 has passed 3/3 live `[待實測]`.

---

## Product

### Q12. Is the demo scripted?

**Answer**
> No. The dataset is fixed and simulated, but every time we press Investigate, Gemini chooses the queries live, the queries run live on BigQuery, and each call is logged in Cloud Logging with its query ID. You can see the query ID under the source rows. We do keep a recorded backup video in case the venue network fails.

**Notes**: only true in `gemini` mode. Confirm there is no OFFLINE FIXTURE bar before going on stage.

### Q13. Aren't five fixed queries too limiting?

**Answer**
> For a night-shift investigation, that's a feature. Alarms, sensor windows, comparison to baseline, shift and maintenance logs, and sensor limits cover the questions a supervisor actually asks. Fixed queries make it testable and repeatable. Adding a new query is a small, tested code change, not a prompt tweak.

---

## Business

### Q14. How do you make money, and how much will you charge?

**Answer**
> A one-time onboarding fee to prepare the factory's data, plus a monthly subscription per production line. We'll price the subscription below the downtime and labour it saves. We're setting the actual price from interviews, where we ask plant managers what one hour of downtime costs them and what they would pay to try it.

**Notes**: say "X per line per month" only with an interview-backed number `[待訪談驗證]`.

### Q15. Did you talk to real customers?

**Answer (fill in)**
> We interviewed [N] `[待訪談驗證]` plant managers in [countries]. The most common pain was "[quote]" `[待訪談驗證]`.

**Notes**: if interviews did not happen, say so plainly: "Not yet at the scale we want. We're recruiting design partners now." Quote people only with recorded permission.

### Q16. Who buys, and how do you reach them?

**Answer**
> The buyer is usually the plant manager or the owner `[待訪談驗證]`. We reach them through Taiwanese business associations in Southeast Asia and LinkedIn, which is also how we found our interviewees. Starting with one line keeps the first purchase small enough for them to approve themselves.

**Notes**: confirm the buyer role from interviews before claiming it. Drop "which is also how we found our interviewees" if the interviews came through other channels or did not happen.

### Q17. What does one investigation cost you?

**Answer**
> We're measuring it now. Each investigation is a handful of Gemini calls plus very small BigQuery queries. We've set budget alerts from day one, a per-IP limit, and a service-wide hourly cap on investigations, so the worst case per hour is bounded. We're adding token logging so every investigation's cost is visible.

**Notes**: the cost per investigation is `待估算` (ENH-002 adds token logging). Do not guess a number. The service-wide cap is `GLOBAL_RATE_LIMIT_PER_HOUR` (default 60, Felix sets the final value); the per-IP limit is `RATE_LIMIT_PER_HOUR`. Say "cannot be bypassed" only after Quinn's forged-header test on Cloud Run passes (BUG-003, `deploy.md` 5.1) `[待實測]`.

---

## Privacy and security

### Q18. Will factories trust you with their production data?

**Answer**
> The prototype uses simulated data only. For real customers, the plan is: each factory gets its own dataset in a Google Cloud region close to them, like Singapore; the service account can only read sensor data and write work orders; no API keys in code; and pilots start with de-identified data from one line.

**Notes**: do not claim how Vertex AI handles customer data (for example training use) without checking Google's current terms `[待查證]`.

### Q19. Anyone with the link can open a work order. Is that safe?

**Answer**
> For simulated demo data, yes, and that's deliberate so you can scan it without signing up. Before any real data, accounts and permissions come first; it's on our roadmap before pilots.

---

## Google Cloud

### Q20. Why Google Cloud and Gemini?

**Answer**
> Four reasons. Gemini's function calling lets us restrict the model to our tested queries. BigQuery is serverless, so small factories don't need a database team. Cloud Run keeps the whole app as one small service, deployed in Singapore close to our customers. And Google Cloud gives our customers a growth path to the Manufacturing Data Engine later.

**Notes**: if asked about the exact Gemini model, answer with the verified `GEMINI_MODEL` value only.

---

## Other

### Q21. Do you support Vietnamese or Thai?

**Answer**
> The interface and work orders are English in the prototype. Vietnamese and Thai work orders for floor operators are on our roadmap; you can see a concept on the roadmap slide.

**Notes**: do not promise dates or a live translation demo (`docs/qa/test-plan.md` §3.4).

### Q22. Can a team this small build and support this?

**Answer**
> We kept the scope deliberately small: one service, five queries, one job. That's what made it possible to ship a working, tested prototype. For real deployments, our first hires are an onboarding engineer and a manufacturing domain expert.

**Notes**: the hiring plan is a PM suggestion, not a decision; the boss confirms or replaces it before the final. Adjust to the actual registered team. Do not describe an advisor as a team member unless they are formally registered (see `docs/qa/organizer-inquiry-draft.md`).
