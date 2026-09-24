# 公開資料報表：製造業停機成本與找原因時間

> 資料蒐集：主持人（2026-09-24）｜整理：Sandy（業務）
> 規則：只使用主持人查到的資料，不新增任何數字或來源。每筆都保留出處與查證等級。

## 1. 結論

**公開資料能證明的：**
- 非計畫停機對製造業來說是很貴的問題，而且越來越貴。Siemens 2022 報告（已核對原文）說 Fortune Global 500 每年因此損失約營收 11%，而且所有受訪產業每小時停機成本都比兩年前高至少 50%。
- 每小時停機成本依產業差很多：FMCG 平均約 $39,000，汽車超過 $2m。

**公開資料不能證明的：**
- **這些數字來自大型製造與工業企業，不能直接套到我們的目標客戶（中小代工廠）。** 在 pitch 裡一律要標註「大型企業數據」，不能說成我們客戶的損失。
- **沒有找到「中小廠找原因平均要多久」的可靠公開數字。** 「MTTR 有 60–70% 是組織延誤」這類說法只出自廠商部落格，原始研究不明。所以我們的 **40 分鐘仍然只能標「待訪談驗證」**，不能當成已證實的數字。
- 沒有東南亞／台灣中小廠停機成本的數字。OECD 等政策報告只講數位化落差，而且數字還沒核對原文。

## 2. 主表

查證等級：A 已核原文｜B 轉述大型報告｜C 廠商部落格／來源不明｜D 待核對

| 編號 | 數據 | 原文引用 | 來源與年份 | 等級 | 適用範圍 | 可否上簡報 |
|---|---|---|---|---|---|---|
| A1 | Fortune Global 500 非計畫停機成本約年營收 11%，近 $1.5tn（兩年前 $864bn，8%） | "unplanned downtime now costs Fortune Global 500 companies 11% of their yearly turnover – almost $1.5tn" | Siemens/Senseye《The True Cost of Downtime 2022》，© Siemens 2023，涵蓋 2021–22（[PDF](https://assets.new.siemens.com/siemens/assets/api/uuid:3d606495-dbe0-43e4-80b1-d04e27ada920/dics-b10153-00-7600truecostofdowntime2022-144.pdf)） | A | 全球最大型企業 | 附註後可（標註「Fortune Global 500」） |
| A2 | 典型大型工廠每年因非計畫停機損失 $129 million（兩年內增加 65%） | "$129 million annual cost to a typical large plant through unplanned downtime (up 65% in two years)" | 同 A1 | A | 大型工廠 | 附註後可（標註「大型工廠」） |
| A3 | 所有受訪產業每小時停機成本都比兩年前高至少 50% | "In every sector surveyed, an hour's unplanned downtime now costs the manufacturer at least 50% more than it did two years ago" | 同 A1 | A | 大型製造與工業企業，趨勢 | 可 |
| A4 | 每小時停機成本：FMCG 平均約 $39,000；汽車超過 $2m（2019–20 為 $1.3m）；Oil & Gas 近 $500,000 | 主持人擷取原文數字（產業別每小時成本） | 同 A1 | A | 大型企業，分產業 | 附註後可（標註「大型企業、產業平均」） |
| A5 | 汽車業平均每月 16 次非計畫停機（兩年前 30 次） | 主持人擷取原文數字 | 同 A1 | A | 大型汽車製造商 | 附註後可 |
| B1 | Fortune Global 500 每年約 $1.4 trillion，約營收 11% | 轉述，無原文 | Siemens《True Cost of Downtime 2024》，經 [AEMT 文章](https://www.theaemt.com/resource/the-true-cost-of-downtime-2024-a-comprehensive-analysis.html) 轉述，未讀原始 PDF | B | 全球最大型企業 | 附註後可（標「轉述 Siemens 2024」）；優先用 A1 |
| B2 | 大型工廠每月約 25 次停機、損失 27 小時（2019 為 42 次、39 小時） | 轉述，無原文 | 同 B1 | B | 大型工廠 | 附註後可 |
| B3 | 汽車業每小時最高 $2.3 million | 轉述，無原文 | 同 B1 | B | 大型汽車製造商 | 附註後可；優先用 A4 |
| C1 | MTTR 只有 30–40% 是實際維修，60–70% 是組織延誤（偵測、回應、診斷、驗證） | "Only 30–40% of total MTTR is hands-on repair work, with the remaining 60–70% being organizational delay involving detection, response, diagnosis, and verification" | 搜尋摘要，出自 [Douglas Machine](https://www.douglas-machine.com/what-is-mean-time-to-repair-mttr-and-what-drives-it-up-or-down/)／[Tractian](https://tractian.com/en/glossary/troubleshooting) 等廠商網頁之一，原始研究不明 | C | 不明 | 不可（只當背景參考） |
| C2 | 42% 非計畫停機事件涉及等零件 | "A 2021 Plant Engineering survey found that 42% of unplanned downtime events involved waiting for parts" | 轉述，[Oxmaint](https://oxmaint.com/industries/manufacturing-plant/unplanned-downtime-root-cause-analysis-manufacturing) | C | 不明 | 不可 |
| C3 | 47% 延長維修時間來自缺零件，而不是診斷 | "47% of extended repair time comes from parts unavailability, not diagnostic gaps" | 轉述，來源不明 | C | 不明 | 不可（注意：這筆反而暗示瓶頸不一定在「找原因」，訪談要問清楚） |
| C4 | 5 Whys 約 15–30 分鐘、魚骨圖 1–2 小時 | 經驗說法 | Oxmaint 網頁（同 C2） | C | 不明 | 不可 |
| C5 | 中型製造商每小時停機約 $25,000 | 轉述 | [manufacturingleadgeneration.com](https://manufacturingleadgeneration.com/manufacturing-downtime-statistics/) 等統計彙整網頁，原始出處不明 | C | 中型製造商（定義不明） | 不可 |
| D1 | 東南亞 SME 與大企業數位化差距大（摘要稱 email 45% vs 86%，網站 26% vs 62%） | 搜尋摘要，數字待核對原文 | [OECD D4SME 2024／2025](https://www.oecd.org/content/dam/oecd/en/publications/reports/2025/04/sme-digitalisation-for-competitiveness_3116862a/197e3077-en.pdf)、[ASEAN SME Policy Index 2024](https://asean.org/wp-content/uploads/2024/09/Full-Report_ASEAN-SME-Policy-Index-2024_20-Sept-2024.pdf)、[ERIA 2024](https://www.eria.org/uploads/The-Digital-Divide-Amongst-MSMEs-in-ASEAN.pdf) | D | 東南亞 SME | 不可（核對原文前）；核對後可用來說明「中小廠數位化落後」 |

## 3. 建議 pitch 用法

只用 A 級，數字照原文，不改寫：

1. "Unplanned downtime now costs Fortune Global 500 companies 11% of their yearly turnover – almost $1.5tn." *(Siemens/Senseye, The True Cost of Downtime 2022)*
2. "Even in FMCG, the lowest-cost sector in the report, an hour of unplanned downtime costs large manufacturers around $39,000 on average — and in every sector, that hourly cost rose at least 50% in two years." *(Siemens/Senseye, The True Cost of Downtime 2022; large enterprises)*
3. "Our customers are smaller contract manufacturers, so their losses per hour are lower — but the trend is the same: every hour on the line matters more than it did two years ago."

**為什麼要打折與標註：** Siemens 資料來自大型製造與工業企業，我們的目標客戶是中小代工廠，產線規模、產值都小很多。簡報上要寫清楚「大型企業數據」，不要換算成「你的工廠每小時損失 $X」。客戶自己的損失，要等訪談時請他們用自己的產值估算。

如果要用 B 級（例如 2024 年的 25 次／27 小時），要加註「轉述自 Siemens 2024，via AEMT」。

## 4. 排除清單

| 數據 | 來源 | 排除理由 |
|---|---|---|
| 重工業每小時 $59 million | Siemens 2024 經 AEMT 轉述 | 跟同報告汽車業最高 $2.3 million／小時差了一個量級以上，看起來是單位轉述錯誤（可能是年度或其他單位），而且我們沒讀到原始 PDF，無法確認。不可使用。 |

## 5. 仍然缺的證據

| 缺口 | 為什麼重要 | 下一步 |
|---|---|---|
| 中小廠「找原因」平均要多久 | 這是我們產品價值的核心；40 分鐘目前只是假設 | 訪談時請廠長／維修人員回想最近 3 次停機，各自花多久找到原因、多久修好、多久等零件 |
| 東南亞／台灣中小廠每小時停機成本 | 沒有它就不能講 ROI | 訪談時問產線每小時產值，請客戶自己估算；之後再找在地公開資料 |
| 瓶頸是在診斷還是等零件 | C3 暗示可能是等零件，如果是這樣我們的價值主張要調整 | 訪談時把「找原因」和「等零件」的時間分開問 |
| D 級數位化落差數字 | 可以支撐「中小廠缺工具」的說法 | 核對 OECD／ASEAN／ERIA 原文後再升級 |
