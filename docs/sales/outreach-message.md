# 廠長訪談邀約訊息範本（LinkedIn／台商協會）

- 建立：2026-09-24，Sandy（業務）
- 草稿，由老闆本人修改後自行寄送。
- 用法：`[ ]` 內替換成對方資訊；第一句一定要個人化（怎麼找到他、為什麼找他）。LinkedIn 連線邀請限 300 字元，先用短版，對方接受後再傳完整版。
- 時程：9/30 前完成訪談，建議 9/25–9/26 發出，同時發 5–8 位，預期回覆 2–3 位。

## 中文版（台商協會／LinkedIn）

**短版（連線邀請）**

> [稱呼]您好，我是[老闆名字]，在看到您[在台商協會／LinkedIn 上]的[工廠／經歷]。我正在做幫中小代工廠「半夜停線快速找原因」的工具，想請教您 20 分鐘實際經驗，不推銷，方便嗎？

**完整版**

> [稱呼]您好，
>
> 我是[老闆名字]，[一句自我介紹]。透過[管道]看到您在[地點]負責[產品／產線]。
>
> 我正在做一個給中小代工廠夜班主管用的工具：停線時，自動從 Excel／PLC 資料找出可能原因並附上證據。目前是原型階段，也會拿去參加 Google 的 AI Builder Cup。
>
> 想請教您 20 分鐘（線上或電話皆可），聊聊停線後找原因的實際狀況。不推銷，工廠名稱不會公開。
>
> 9/30 前您哪個時段方便？謝謝！
> [老闆名字]｜[聯絡方式]

## English version (LinkedIn)

**Short (connection request)**

> Hi [Name], I'm [Your name]. I saw your work at [factory/company] in [location]. I'm building a tool that helps small contract manufacturers find root causes fast when a line stops at night. Could I ask you 20 minutes about your real experience? Not a sales pitch.

**Full**

> Hi [Name],
>
> I'm [Your name], [one-line intro]. I found you via [channel] and saw you run [product/line] at [location].
>
> I'm building a copilot for night-shift supervisors at small contract manufacturers: when a line stops, it pulls evidence from Excel / PLC data and suggests the likely root cause. It's an early prototype, and I'm also entering it in Google's AI Builder Cup.
>
> Would you have 20 minutes (video or phone) before Sept 30 to share how your team investigates line stoppages today? No sales pitch, and your company name won't be made public.
>
> Thanks!
> [Your name] | [Contact]

## 升級版：附 demo 網址（2026-09-24 會議後新增）

- 草稿，老闆修改後自行寄送；可當第一封，也可當跟進訊息。
- 目的：讓對方先看 30 秒，再回答「你們現在要多久」，這個回答就是「40 分鐘」`[待訪談驗證]` 的第一手證據。記下對方原話與可否引用。
- Demo 是模擬資料、免登入；網址用手機也能開。實測約 12 秒找到根因（中位數 12.6 秒，出處 `docs/qa/runs/README.md`）。Cloud Run 閒置時第一次開可能要多等幾秒。
- 不要寫「支援 BigQuery」、不要寫 40 分鐘，讓對方自己講數字。

**中文版**

> [稱呼]您好，我是[老闆名字]，[一句自我介紹／怎麼找到您]。
>
> 我做了一個給中小代工廠夜班主管用的停線調查工具：按一個鈕，它就從產線資料找證據、推出根因、開出工單，每個結論都能回查原始資料。
>
> 想請您花 30 秒看它查一次停線，再告訴我你們現在要多久：
> https://linesleuth-547147056278.asia-southeast1.run.app
> （模擬資料、免登入，按 Investigate 即可，手機也能開）
>
> 如果願意，再給我 20 分鐘聊聊您工廠停線後怎麼找原因。不推銷，工廠名稱不會公開。10/1 前哪個時段方便？謝謝！
> [老闆名字]｜[聯絡方式]

**English**

> Hi [Name], I'm [Your name], [one-line intro / how I found you].
>
> I've built a line-stoppage investigation tool for night-shift supervisors at small contract manufacturers: one button, and it pulls evidence from plant data, finds the root cause and opens a work order, with every conclusion traceable to its source rows.
>
> Could you spend 30 seconds watching it investigate one stoppage, then tell me how long it takes your team today?
> https://linesleuth-547147056278.asia-southeast1.run.app
> (Simulated data, no sign-up. Just press Investigate. Works on a phone.)
>
> If you're open to it, I'd love 20 minutes before Oct 1 to hear how your plant handles stoppages. No sales pitch, and your company name won't be made public. Thanks!
> [Your name] | [Contact]

## 跟進（3 天沒回）

> 中文：[稱呼]您好，再打擾一次。若這週不方便，下週 10 分鐘也很有幫助；或您是否能推薦一位適合聊的產線主管？謝謝！
>
> English: Hi [Name], just following up. Even 10 minutes next week would help a lot, or could you point me to a production supervisor who might be open to a quick chat? Thanks!
