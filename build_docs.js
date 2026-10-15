// Builds: Project Flow & Insights (docx), Business Summary (docx -> pdf), Streamlit Guide (docx)
const fs = require("fs");
const D = require("docx");
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun, HeadingLevel, AlignmentType,
  WidthType, ShadingType, BorderStyle, LevelFormat, PageBreak, Footer, PageNumber } = D;

const F = JSON.parse(fs.readFileSync("docs/facts.json"));
const K = F.kpi;
const ACC = "C2185B", INK = "1F2430", MUT = "6B7280", SOFT = "FDF2F7", GREY = "F3F4F6", LINE = "E5E7EB";
const W = 9360; // content width (US Letter, 1" margins)
const fmtM = (n) => (n >= 1e9 ? (n / 1e9).toFixed(2) + "B" : (n / 1e6).toFixed(2) + "M");
const n0 = (n) => Math.round(n).toLocaleString("en-US");
const p2 = (n) => n.toFixed(2) + "%";
const img = (name, w, h) => new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { before: 120, after: 120 },
  children: [new ImageRun({ type: "png", data: fs.readFileSync(`docs/charts/${name}.png`), transformation: { width: w, height: h },
    altText: { title: name, description: name, name } })],
});
const P = (t, o = {}) => new Paragraph({ spacing: { after: 120, line: 276 }, ...o,
  children: Array.isArray(t) ? t : [new TextRun({ text: t, color: o.color || INK, size: o.size || 22, bold: o.bold, italics: o.italics })] });
const R = (text, o = {}) => new TextRun({ text, color: INK, size: 22, ...o });
const H1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { before: 320, after: 140 }, children: [new TextRun({ text: t })] });
const H2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 220, after: 100 }, children: [new TextRun({ text: t })] });
const B = (t, lvl = 0) => new Paragraph({ numbering: { reference: "bul", level: lvl }, spacing: { after: 70, line: 264 },
  children: Array.isArray(t) ? t : [R(t)] });
const N = (t) => new Paragraph({ numbering: { reference: "num", level: 0 }, spacing: { after: 80 }, children: Array.isArray(t) ? t : [R(t)] });
const code = (lines) => lines.map((l, i) => new Paragraph({
  spacing: { after: 0, line: 252 }, shading: { type: ShadingType.CLEAR, fill: "F3F4F6" },
  border: { left: { style: BorderStyle.SINGLE, size: 18, color: ACC, space: 6 } }, indent: { left: 120 },
  children: [new TextRun({ text: l === "" ? " " : l, font: "Consolas", size: 18, color: INK })],
})).concat([new Paragraph({ spacing: { after: 80 }, children: [] })]);
const callout = (label, text, fill = SOFT, bar = ACC) => new Table({
  width: { size: W, type: WidthType.DXA }, columnWidths: [W],
  rows: [new TableRow({ cantSplit: true, children: [new TableCell({
    width: { size: W, type: WidthType.DXA }, shading: { type: ShadingType.CLEAR, fill },
    margins: { top: 100, bottom: 100, left: 180, right: 160 },
    borders: { top: { style: BorderStyle.NONE }, bottom: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE },
      left: { style: BorderStyle.SINGLE, size: 24, color: bar } },
    children: [new Paragraph({ spacing: { after: 0, line: 264 }, children: [new TextRun({ text: label + "  ", bold: true, color: bar, size: 21 }), new TextRun({ text, size: 21, color: INK })] })],
  })] })],
});
const gap = () => new Paragraph({ spacing: { after: 100 }, children: [] });
const bd = { style: BorderStyle.SINGLE, size: 4, color: LINE };
const borders = { top: bd, bottom: bd, left: bd, right: bd };
function table(head, rows, widths, opts = {}) {
  const cell = (t, i, header, ri) => new TableCell({
    width: { size: widths[i], type: WidthType.DXA }, borders,
    shading: { type: ShadingType.CLEAR, fill: header ? ACC : (ri % 2 ? "FAFAFB" : "FFFFFF") },
    margins: { top: 70, bottom: 70, left: 110, right: 110 },
    children: [new Paragraph({ spacing: { after: 0 }, alignment: opts.align && opts.align[i] || AlignmentType.LEFT,
      children: [new TextRun({ text: String(t), bold: header || (opts.boldFirst && i === 0), color: header ? "FFFFFF" : INK, size: opts.size || 20 })] })],
  });
  return new Table({
    width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA }, columnWidths: widths,
    rows: [new TableRow({ tableHeader: true, children: head.map((h, i) => cell(h, i, true)) }),
      ...rows.map((r, ri) => new TableRow({ cantSplit: true, children: r.map((c, i) => cell(c, i, false, ri)) }))],
  });
}
const kpiRow = (items) => {
  const cw = Math.floor(W / items.length);
  return new Table({
    width: { size: cw * items.length, type: WidthType.DXA }, columnWidths: items.map(() => cw),
    rows: [new TableRow({ children: items.map(([v, l]) => new TableCell({
      width: { size: cw, type: WidthType.DXA }, shading: { type: ShadingType.CLEAR, fill: GREY },
      borders: { top: { style: BorderStyle.SINGLE, size: 18, color: ACC }, bottom: { style: BorderStyle.NONE }, left: { style: BorderStyle.SINGLE, size: 8, color: "FFFFFF" }, right: { style: BorderStyle.SINGLE, size: 8, color: "FFFFFF" } },
      margins: { top: 100, bottom: 100, left: 100, right: 100 },
      children: [new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 20 }, children: [new TextRun({ text: v, bold: true, size: 30, color: ACC })] }),
        new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 0 }, children: [new TextRun({ text: l, size: 17, color: MUT })] })],
    })) })],
  });
};

const styles = {
  default: { document: { run: { font: "Calibri", size: 22 } } },
  paragraphStyles: [
    { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 32, bold: true, color: ACC, font: "Calibri" }, paragraph: { spacing: { before: 320, after: 140 }, outlineLevel: 0, keepNext: true } },
    { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 25, bold: true, color: INK, font: "Calibri" }, paragraph: { spacing: { before: 220, after: 100 }, outlineLevel: 1, keepNext: true } },
  ],
};
const numbering = { config: [
  { reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 270 } } } },
    { level: 1, format: LevelFormat.BULLET, text: "–", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 1000, hanging: 270 } } } }] },
  { reference: "num", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 340 } } } }] },
] };
const footer = (t) => new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [
  new TextRun({ text: t + "  ·  Page ", size: 17, color: MUT }), new TextRun({ children: [PageNumber.CURRENT], size: 17, color: MUT })] })] });
const page = { size: { width: 12240, height: 15840 }, margin: { top: 1300, bottom: 1200, left: 1440, right: 1440 } };
const title = (t, sub) => [
  new Paragraph({ spacing: { before: 200, after: 60 }, children: [new TextRun({ text: t, bold: true, size: 48, color: INK })] }),
  new Paragraph({ spacing: { after: 160 }, border: { bottom: { style: BorderStyle.SINGLE, size: 12, color: ACC, space: 6 } }, children: [new TextRun({ text: sub, size: 23, color: MUT })] }),
];

const pt = F.post_type, dw = F.weekday, ht = F.hashtag, cp = F.campaign;
const bestPT = pt[0], bestDW = [...dw].sort((a, b) => b.er - a.er)[0], worstDW = [...dw].sort((a, b) => a.er - b.er)[0];
const pv = F.pvalues;
const pfmt = (p) => p.toFixed(2);

// ======================= 1. PROJECT FLOW & INSIGHTS =======================
const flow = [
  ...title("Instagram Performance Analytics — Project Flow & Insights", "Sugar Cosmetics  ·  Data Analytics & AI portfolio project  ·  Data window 19 Apr 2024 – 19 Apr 2025"),
  callout("Headline.", `Sugar Cosmetics' Instagram content performs consistently: ${p2(K.avg_er)} average engagement rate across ${n0(K.records)} records. But no post format, weekday, hashtag or campaign type is a statistically proven winner — the gaps between best and worst are all under ${Math.ceil(Math.max(...Object.values(F.spreads)))}%. The real levers are reach, deeper engagement (comments, saves, shares) and profile-to-follow conversion.`),
  gap(),
  H1("1. Business objective and questions"),
  P("The marketing team publishes steadily but cannot tell which content, timing and hashtags to invest in. This project answers five business questions from the data:"),
  B("Which post type earns the most likes, comments, saves and shares?"),
  B("Which weekdays and months are associated with stronger performance?"),
  B("Which hashtags are linked to better engagement or reach?"),
  B("Are people seeing posts but not interacting?"),
  B("What should the team publish — and test — next?"),

  H1("2. Data understanding and validation"),
  P("Source: sugar_cosmetics_instagram_data (.xlsx and .csv — verified identical). One row = one post-level record."),
  table(["Check", "Result", "Meaning"], [
    ["Rows × columns", "50,000 × 14", "10 text/category fields, 8 numeric metrics"],
    ["Missing values", "0", "No imputation required"],
    ["Exact duplicate rows", "0", "No de-duplication required"],
    ["Negative numbers", "0", "All counts valid"],
    ["Reach greater than impressions", "0", "Logical relationship holds"],
    ["Zero values", "Shares: 9, Follows: 1", "Valid counts — kept as zero, not imputed"],
    ["Date range", "19 Apr 2024 – 19 Apr 2025", "First and last months are partial"],
    ["Categories", "4 post types, 5 campaigns, 4 sources, 5 emotions, 5 hashtags", "Spellings consistent"],
  ], [2700, 2900, 3760], { boldFirst: true }),
  gap(),
  callout("Data caveats.", `The file has no caption or post ID, so records are labelled "#ID · Format · Campaign · Date". With about ${Math.round(F.records_per_day)} records per day, a row is unlikely to be one literal Instagram post, and the flat distributions suggest synthetic or aggregated data. Treat the findings as a validated method and framework; re-run on the brand's real Instagram Insights export before acting.`, GREY, MUT),

  H1("3. Project flow — from raw file to recommendations"),
  table(["#", "Stage", "Tool", "Output"], [
    ["1", "Understand the business problem", "Brief, stakeholder questions", "Objectives, questions, KPI list"],
    ["2", "Understand the dataset", "Python (pandas)", "Data dictionary, quality report"],
    ["3", "Clean and validate", "preprocess.py", "Validated CSV + preprocessed Excel"],
    ["4", "Create calculated fields", "preprocess.py", "Total Engagement, Engagement Rate, Month, Day of Week"],
    ["5", "Build the 10 visualizations", "Plotly in Streamlit", "10 titled, insight-annotated views"],
    ["6", "Build the interactive dashboard", "Streamlit sidebar filters", "Post type / month / campaign / source / hashtag filters"],
    ["7", "Interpret and recommend", "Analysis + statistical test", "Insights doc, business summary, deck"],
  ], [500, 2900, 2500, 3460]),

  H1("4. KPI definitions"),
  table(["KPI", "Formula", "Note"], [
    ["Total Engagement", "Likes + Comments + Shares + Saves", "Project definition, not Instagram's official one"],
    ["Engagement Rate (%)", "Total Engagement ÷ Reach × 100", "Per record; headline = average of records"],
    ["Profile Visit Rate (%)", "Profile Visits ÷ Reach × 100", "Interest in the account"],
    ["Follow Conversion (%)", "Follows ÷ Profile Visits × 100", "Exploratory — attribution rules unverified"],
    ["Reach Rate (%)", "Reach ÷ Impressions × 100", "Share of views that are unique accounts"],
  ], [2400, 3600, 3360], { boldFirst: true }),
  P("Summed reach counts the same account once per record, so it is not the number of unique people reached.", { italics: true, color: MUT, size: 20 }),

  new Paragraph({ children: [new PageBreak()] }),
  H1("5. Findings by analysis"),
  H2("Task 1 — KPI Overview"),
  kpiRow([[n0(K.records), "Posts (records)"], [fmtM(K.likes), "Likes"], [fmtM(K.comments), "Comments"], [fmtM(K.reach), "Total reach"], [p2(K.avg_er), "Avg engagement rate"]]),
  gap(),
  P(`Total engagement is ${fmtM(K.engagement)} on ${(K.impressions / 1e9).toFixed(2)}B impressions. Likes make up ${K.like_share.toFixed(0)}% of all interactions; comments ${K.comment_share.toFixed(0)}%, saves ${K.save_share.toFixed(1)}%, shares ${K.share_share.toFixed(1)}%. Every 1,000 accounts reached produce about ${Math.round(K.per_1000_reach)} interactions.`),
  H2("Task 2 — Monthly Posting Trend"),
  img("monthly_posts", 560, 252),
  P("Publishing is steady at roughly 4,000–4,300 records a month. April 2024 and April 2025 look low only because the data covers just part of each month. Consistency is a strength; there is no seasonal posting gap."),
  H2("Task 3 — Top 10 by Likes"),
  img("top_likes", 540, 284),
  P(`The top 10 average ${n0(F.top_likes_avg_reach)} reach against ${n0(F.avg_reach)} overall. Likes and reach are strongly correlated (r = ${F.corr_reach_likes.toFixed(2)}), so "most liked" largely means "most seen". Influencer Collab and Giveaway campaigns appear repeatedly.`),
  H2("Task 4 — Top 10 by Engagement Rate"),
  img("top_er", 540, 284),
  P(`These hidden gems reach ${F.top_er[0]["Engagement Rate (%)"].toFixed(1)}% engagement against the ${K.avg_er.toFixed(1)}% average, with a median reach of ${n0(F.top_er_median_reach)} — below average. High engagement does not need huge reach, and none of them appear in the top-10-by-likes list.`),
  H2("Task 5 — Post Type Performance"),
  img("post_type_er", 440, 227),
  table(["Post type", "Records", "Avg likes", "Avg comments", "Avg saves", "Avg shares", "Eng. rate"],
    pt.map((r) => [r["Post Type"], n0(r.n), n0(r.likes), n0(r.comments), n0(r.saves), n0(r.shares), p2(r.er)]),
    [1700, 1200, 1300, 1500, 1200, 1200, 1260], { boldFirst: true, align: [0, 2, 2, 2, 2, 2, 2].map((x) => (x ? AlignmentType.RIGHT : AlignmentType.LEFT)) }),
  gap(),
  P(`${bestPT["Post Type"]} leads on engagement rate (${p2(bestPT.er)}), but the best-to-worst gap is only ${F.spreads.post_type.toFixed(1)}% and the difference is not statistically significant (ANOVA p = ${pfmt(pv["Post Type"])}). Format alone is not what drives results.`),
  H2("Task 6 — Day of Week"),
  img("weekday_er", 520, 234),
  P(`${bestDW["Day of Week"]} is highest (${p2(bestDW.er)}) and ${worstDW["Day of Week"]} lowest (${p2(worstDW.er)}) — a ${(bestDW.er - worstDW.er).toFixed(2)}-point gap. Confidence whiskers overlap (p = ${pfmt(pv["Day of Week"])}), so there is no proven best day. Hour of posting is not in the data and should be captured.`),
  H2("Task 7 — Engagement Funnel"),
  img("funnel", 540, 263),
  P(`${K.reach_rate.toFixed(0)} of every 100 impressions are unique accounts and about ${(K.likes / K.impressions * 100).toFixed(0)} become likes. Comments, shares and saves each convert under 1.5% of impressions — the big drop-off is from seeing to deeper actions. Of reached accounts, ${K.pv_rate.toFixed(1)}% visit the profile and ${K.follow_conv.toFixed(0)}% of visitors follow.`),
  H2("Reach without interaction"),
  img("reach_vs_er", 480, 247),
  P(`${n0(F.gap.n)} records (${F.gap.pct.toFixed(1)}%) combine top-quartile reach (≥ ${n0(F.gap.reach_q75)}) with bottom-quartile engagement (≤ ${F.gap.er_q25.toFixed(1)}%). Overall, engagement rate is uncorrelated with reach (r = ${F.corr_reach_er.toFixed(2)}): more reach brings more interactions, not better ones. These records are the clearest optimisation target.`),
  H2("Task 8 — Hashtag Analysis"),
  img("hashtag_er", 440, 227),
  P(`${ht[0].Hashtag} leads (${p2(ht[0].er)}) but all five hashtags sit within ${(ht[0].er - ht[ht.length - 1].er).toFixed(2)} points of each other and their confidence ranges overlap. Posts with 2 hashtags score marginally highest, again within noise.`),
  H2("Statistical check"),
  table(["Dimension", "Best group", "Gap (best vs worst)", "ANOVA p-value", "Verdict"], [
    ["Post type", pt[0]["Post Type"], F.spreads.post_type.toFixed(1) + "%", pfmt(pv["Post Type"]), "Not significant"],
    ["Weekday", bestDW["Day of Week"], F.spreads.weekday.toFixed(1) + "%", pfmt(pv["Day of Week"]), "Not significant"],
    ["Campaign", cp[0]["Campaign Type"], F.spreads.campaign.toFixed(1) + "%", pfmt(pv["Campaign Type"]), "Not significant"],
    ["Hashtag", ht[0].Hashtag, F.spreads.hashtag.toFixed(1) + "%", pfmt(pv.Hashtag) + "*", "Not significant"],
  ], [1700, 2000, 1900, 1700, 2060], { boldFirst: true }),
  P("* Indicative: a post carrying several hashtags counts once per hashtag, so groups overlap.", { size: 18, italics: true, color: MUT }),

  H1("6. Strategic recommendations"),
  table(["Action", "What to do", "Evidence"], [
    ["Scale reach", "Invest in amplification: influencer collabs, boosted proven creatives, Reels/Stories distribution.", `Engagement rate is flat as reach grows; ~${Math.round(K.per_1000_reach)} interactions per 1,000 reached.`],
    ["Fix 'seen but ignored'", "Audit high-reach, low-engagement posts for weak hooks and missing calls-to-action; add polls, questions, giveaways.", `${F.gap.pct.toFixed(1)}% of records (${n0(F.gap.n)}).`],
    ["Deepen engagement", "Create save-worthy tutorials and share-worthy festive/challenge content.", `Likes are ${K.like_share.toFixed(0)}% of interactions.`],
    ["Convert visitors", "Strengthen bio, highlights, pinned posts and link-in-bio offers; add 'follow for shade drops' end frames.", `${K.pv_rate.toFixed(1)}% visit profile; ${K.follow_conv.toFixed(0)}% of visitors follow.`],
    ["Test, don't guess", "Run 4-week A/B tests: Reel vs Image, 2 vs 3 hashtags, morning vs evening. Act only on significant results.", "All format/day/hashtag gaps are within noise."],
    ["Keep the base", "Maintain steady cadence, balanced format mix and the five brand/value hashtags.", "Posting volume and engagement are consistent month to month."],
    ["Close data gaps", "Capture post ID, caption, posting hour, carousel format, ad spend and follower count.", "Needed for timing, caption, ROI and growth analysis."],
  ], [1900, 4300, 3160], { boldFirst: true }),
  H2("Content and campaign ideas"),
  B("Tutorial Reels series (\"5-minute festive look\") — built for saves and shares."),
  B("Influencer collab takeovers with a giveaway mechanic — built for reach plus comments."),
  B("Festive Offer Stories with poll and quiz stickers — interaction at scale."),
  B("Vegan and cruelty-free brand-values content — on-brand, consistently performing hashtag themes."),
  B("Profile-visit nudges in the last frame of high-reach posts."),
];

// ======================= 2. BUSINESS SUMMARY =======================
const summary = [
  ...title("Business Summary — Sugar Cosmetics Instagram Performance", "Executive brief for the marketing team  ·  19 Apr 2024 – 19 Apr 2025  ·  50,000 post-level records"),
  callout("Bottom line.", "Instagram performance is healthy and steady, but no format, day or hashtag stands out as a proven winner. Growth will come from more reach, deeper engagement and better follower conversion — not from re-allocating effort between formats."),
  gap(),
  kpiRow([[n0(K.records), "Posts (records)"], [fmtM(K.reach), "Total reach"], [fmtM(K.likes), "Likes"], [fmtM(K.comments), "Comments"], [p2(K.avg_er), "Avg engagement"]]),
  gap(),
  H1("What we found"),
  B([R("Performance is consistent. ", { bold: true }), R(`Posting is steady at about 4,100 records a month and engagement rate stays near ${K.avg_er.toFixed(1)}% every month.`)]),
  B([R("No format is a clear winner. ", { bold: true }), R(`Reel (${p2(pt[0].er)}), Story, Video and Image are within ${(pt[0].er - pt[3].er).toFixed(2)} points; the difference is not statistically significant.`)]),
  B([R("No proven best day or hashtag. ", { bold: true }), R(`${bestDW["Day of Week"]} (${p2(bestDW.er)}) edges ${worstDW["Day of Week"]} (${p2(worstDW.er)}); hashtags differ by ${(ht[0].er - ht[4].er).toFixed(2)} points. Both are within noise.`)]),
  B([R("Reach, not format, drives volume. ", { bold: true }), R(`Likes track reach closely (r = ${F.corr_reach_likes.toFixed(2)}); engagement rate does not (r = ${F.corr_reach_er.toFixed(2)}).`)]),
  B([R("Most interaction is shallow. ", { bold: true }), R(`Likes are ${K.like_share.toFixed(0)}% of interactions; comments, saves and shares together are ${(100 - K.like_share).toFixed(0)}%.`)]),
  B([R("Audience growth has a clear funnel. ", { bold: true }), R(`${K.pv_rate.toFixed(1)}% of reach visits the profile and ${K.follow_conv.toFixed(0)}% of visitors follow.`)]),
  B([R("A fixable gap exists. ", { bold: true }), R(`${F.gap.pct.toFixed(1)}% of records (${n0(F.gap.n)}) were widely seen but earned little engagement.`)]),
  img("funnel", 470, 229),
  H1("What to do next"),
  N([R("Scale reach ", { bold: true }), R("through influencer collabs and boosting the strongest creatives.")]),
  N([R("Rescue high-reach, low-engagement posts ", { bold: true }), R("with stronger hooks and clear calls-to-action.")]),
  N([R("Build save- and share-worthy content ", { bold: true }), R("— tutorials, festive offers, challenges — to move beyond likes.")]),
  N([R("Optimise the profile ", { bold: true }), R("(bio, highlights, link-in-bio) to lift follow conversion.")]),
  N([R("Run 4-week A/B tests ", { bold: true }), R("on format, hashtag count and posting time before changing the content mix.")]),
  N([R("Capture richer data ", { bold: true }), R("(post ID, caption, posting hour, ad spend, follower count).")]),
  gap(),
  callout("Data note.", `The dataset has no captions or post IDs and shows about ${Math.round(F.records_per_day)} records per day with unusually flat distributions, which suggests synthetic or aggregated data. Treat these results as a validated framework and confirm them on the brand's live Instagram Insights export.`, GREY, MUT),
];

// ======================= 3. STREAMLIT GUIDE =======================
const guide = [
  ...title("Streamlit Dashboard Guide — End to End", "Sugar Cosmetics Instagram Analytics  ·  from raw Excel to a deployed, interactive dashboard"),
  P("This guide walks through exactly how the dashboard in this project is built, so you can rebuild it from scratch, explain it in an interview and deploy it publicly."),
  H1("Step 1 — Set up the project"),
  P("Create a folder with this structure:"),
  ...code([
    "sugar_dashboard/",
    "├── app.py                     # the Streamlit dashboard",
    "├── preprocess.py              # cleaning + calculated fields",
    "├── make_assets.py             # charts/facts for the report and deck (optional)",
    "├── requirements.txt",
    "├── .streamlit/config.toml     # theme",
    "├── sugar_cosmetics_instagram_data.xlsx   # raw data",
    "└── data/",
    "    ├── sugar_cosmetics_clean.csv          # produced by preprocess.py",
    "    └── sugar_cosmetics_preprocessed.xlsx  # optional Excel deliverable",
  ]),
  P("Create and activate a virtual environment, then install the packages:"),
  ...code(["python -m venv .venv", "source .venv/bin/activate        # Windows: .venv\\Scripts\\activate", "pip install -r requirements.txt"]),
  P("requirements.txt:"),
  ...code(["streamlit>=1.50", "pandas>=2.0", "numpy>=1.26", "plotly>=5.20", "scipy>=1.11", "openpyxl>=3.1"]),
  H1("Step 2 — Clean and enrich the data"),
  P("Run the preprocessing script once. It validates the file, builds the calculated fields and writes the cleaned CSV that the app reads:"),
  ...code(["python preprocess.py sugar_cosmetics_instagram_data.xlsx"]),
  P("What it does:"),
  B("Validates: missing values (0), duplicates (0), negatives (0), reach > impressions (0), zero values (Shares 9, Follows 1)."),
  B("Creates: Total Engagement, Engagement Rate (%), Profile Visit Rate (%), Follow Conversion (%), Reach Rate (%), Month, Day of Week, Hashtag Count, Post Label."),
  B("Saves: data/sugar_cosmetics_clean.csv (used by the app) and data/sugar_cosmetics_preprocessed.xlsx (the optional Excel deliverable)."),
  ...code([
    'df["Total Engagement"] = df.Likes + df.Comments + df.Shares + df.Saves',
    'df["Engagement Rate (%)"] = (df["Total Engagement"] / df.Reach * 100).where(df.Reach > 0)',
    'df["Month"] = df["Post Date"].dt.to_period("M").dt.to_timestamp()',
    'df["Day of Week"] = df["Post Date"].dt.day_name()',
  ]),
  H1("Step 3 — Page setup, theme and styling"),
  P("Every Streamlit app starts with set_page_config. Use a wide layout so charts have room. A single colour palette keeps the dashboard consistent: grey for normal bars and one accent colour for the best or selected item."),
  ...code([
    "st.set_page_config(page_title='Sugar Cosmetics | Instagram Analytics',",
    "                   page_icon='💄', layout='wide', initial_sidebar_state='expanded')",
    "",
    'ACCENT = "#C2185B"   # highlight (best / selected)',
    'BASE   = "#B9BEC8"   # neutral bars',
    'INK    = "#1F2430"   # text',
  ]),
  P("Put the theme in .streamlit/config.toml so the app looks identical locally and when deployed:"),
  ...code(["[theme]", 'base = "light"', 'primaryColor = "#C2185B"', 'backgroundColor = "#FFFFFF"', 'secondaryBackgroundColor = "#F5F6F8"', 'textColor = "#1F2430"']),
  P("A small style() helper applies the same look (fonts, margins, transparent background, light gridlines) to every Plotly chart, so no chart needs custom formatting."),
  H1("Step 4 — Load data with caching"),
  ...code([
    "@st.cache_data(show_spinner='Loading data…')",
    "def load_data():",
    "    df = pd.read_csv(DATA_PATH, parse_dates=['Post Date', 'Month'])",
    "    df['Day of Week'] = pd.Categorical(df['Day of Week'], DAY_ORDER, ordered=True)",
    "    return df",
  ]),
  P("@st.cache_data makes the 50,000-row file load once, not on every click. The ordered categorical keeps weekdays in Monday-to-Sunday order in every chart."),
  H1("Step 5 — Build the sidebar filters"),
  P("Filters live in st.sidebar and are applied to the DataFrame once, before any chart is drawn. Every tab then reads the filtered DataFrame, so one filter updates all ten views."),
  table(["Filter", "Widget", "Purpose"], [
    ["Month range", "st.select_slider", "Focus on a period"],
    ["Post Type", "st.multiselect", "Reel, Story, Video, Image"],
    ["Campaign Type", "st.multiselect", "Giveaway, Tutorial, Festive Offer…"],
    ["Engagement Source", "st.multiselect", "Organic, Paid, Collab, Influencer"],
    ["Hashtag", "st.multiselect", "Posts containing any selected hashtag"],
    ["Reset button", "st.button + session_state", "Restore all defaults in one click"],
  ], [2600, 3000, 3760], { boldFirst: true }),
  ...code([
    "df = raw[raw['Month'].between(months[i0], months[i1])",
    "         & raw['Post Type'].isin(f_type)",
    "         & raw['Campaign Type'].isin(f_campaign)",
    "         & raw['Engagement Source'].isin(f_source)]",
    "if f_tags:",
    "    df = df[df['Hashtags'].apply(lambda s: any(t in s for t in f_tags))]",
    "if df.empty:",
    "    st.warning('No records match the current filters.'); st.stop()",
  ]),
  P("Always handle the empty case — a filter combination with no rows should show a message, not an error."),
  H1("Step 6 — Create the ten tabs"),
  P("st.tabs() gives one tab per analysis. Name them with numbers so they follow the project brief. Each tab follows the same pattern: a question as the subheader, one clean chart, a one-line insight box, and (where useful) a caveat."),
  ...code(["TABS = ['1 · KPI Overview', '2 · Monthly Posting Trend', '3 · Top 10 by Likes', '4 · Top 10 by Engagement Rate',", "        '5 · Post Type Performance', '6 · Day of Week', '7 · Engagement Funnel', '8 · Hashtag Analysis',", "        '9 · Interactive Dashboard', '10 · Strategic Recommendations']", "tabs = st.tabs(TABS)", "with tabs[0]:", "    ..."]),
  table(["Tab", "Chart", "Key code"], [
    ["1 KPI Overview", "Metric cards + monthly line + engagement mix", "st.metric, px.line, px.bar"],
    ["2 Monthly Trend", "Line: posts per month", "groupby('Month').size(), px.line"],
    ["3 Top 10 by Likes", "Horizontal bars", "df.nlargest(10, 'Likes')"],
    ["4 Top 10 by Eng. Rate", "Horizontal bars", "df.nlargest(10, 'Engagement Rate (%)')"],
    ["5 Post Type", "Four small bar panels", "make_subplots(rows=1, cols=4)"],
    ["6 Day of Week", "Bars with 95% CI whiskers", "error_y=dict(array=ci)"],
    ["7 Funnel", "Funnel + reach-vs-engagement scatter", "go.Funnel, px.scatter"],
    ["8 Hashtags", "Bars + usage + hashtag count", "str.split(', ') then explode()"],
    ["9 Interactive", "Metric/dimension pickers, trend, heatmap", "st.selectbox, px.imshow"],
    ["10 Recommendations", "Action cards + campaign ideas", "st.markdown(unsafe_allow_html)"],
  ], [2300, 3700, 3360], { boldFirst: true, size: 19 }),
  H2("Hashtag analysis — explode a list column"),
  P("Each post has up to three hashtags in one text cell. Split and explode to one row per hashtag before grouping:"),
  ...code([
    "ex = df.assign(Hashtag=df['Hashtags'].str.split(', ')).explode('Hashtag')",
    "ht = ex.groupby('Hashtag').agg(Records=('Record ID','size'), Avg_ER=('Engagement Rate (%)','mean'))",
  ]),
  H2("Honest charts: confidence intervals"),
  P("Because the group averages are almost identical, whiskers show the 95% confidence interval (1.96 × standard deviation ÷ √n). Overlapping whiskers tell the audience that the ranking is not meaningful. This is the single most credible thing a junior analyst can show."),
  H1("Step 7 — Run locally"),
  ...code(["streamlit run app.py"]),
  P("The app opens at http://localhost:8501. Test it: change each filter, press Reset, pick a single hashtag, then select a combination that returns no rows."),
  H1("Step 8 — Deploy to Streamlit Community Cloud (free)"),
  N("Create a GitHub repository (public is the simplest) and push the project: app.py, preprocess.py, requirements.txt, .streamlit/config.toml and the data/ folder with sugar_cosmetics_clean.csv."),
  N("Go to share.streamlit.io and sign in with GitHub."),
  N("Click Create app → Deploy a public app from GitHub."),
  N("Choose your repository, the main branch and set the main file path to app.py."),
  N("Open Advanced settings and pick Python 3.11 or 3.12. Click Deploy."),
  N("After a minute or two you get a public URL like https://your-app.streamlit.app. Add it to your resume, LinkedIn and GitHub README."),
  P("Deployment checklist:"),
  B("The CSV is about 12 MB — well inside GitHub's 100 MB file limit."),
  B("Use relative paths (Path(__file__).parent / 'data' / ...), never C:\\ or /home paths."),
  B("Every library you import must be in requirements.txt."),
  B("Commit and push to update the live app; it redeploys automatically."),
  H1("Step 9 — Troubleshooting"),
  table(["Problem", "Fix"], [
    ["FileNotFoundError for the CSV", "Run python preprocess.py first; check the path in DATA_PATH."],
    ["ModuleNotFoundError on the cloud", "Add the missing package to requirements.txt and push."],
    ["App is slow after each click", "Wrap loading and heavy groupbys in @st.cache_data."],
    ["Widgets reset unexpectedly", "Give each widget a unique key= and store defaults in st.session_state."],
    ["Charts overflow on a phone", "Use width='stretch' on charts and keep each chart's height modest."],
    ["Weekdays appear alphabetically", "Convert the column to an ordered Categorical."],
  ], [3400, 5960], { boldFirst: true }),
  H1("Step 10 — Naming conventions and quality checklist"),
  B("Files: lowercase with underscores (preprocess.py, make_assets.py); constants in UPPER_CASE (ACCENT, DAY_ORDER)."),
  B("Columns: human-readable titles with units (\"Engagement Rate (%)\") so chart labels need no editing."),
  B("Tabs: numbered and named after the business question, matching the brief."),
  B("Filter keys: prefix f_ (f_type, f_tags); helpers are small verbs (human, style, insight, caveat)."),
  B("One accent colour for the highlight, grey for everything else; no pie charts; no rainbow palettes."),
  B("Each chart has a title, readable labels, a hover tooltip and a one-line takeaway."),
  H1("Interview talking points"),
  B("\"I validated 50,000 rows first — no missing values, duplicates or invalid reach — and documented it.\""),
  B("\"I defined engagement rate as interactions ÷ reach and used it consistently across every view.\""),
  B("\"The averages looked different, so I tested them. ANOVA p-values were 0.15 to 0.63 — the differences are noise — so I recommended A/B tests instead of declaring a winner.\""),
  B("\"The real opportunities are reach, comments/saves/shares and profile-to-follow conversion.\""),
  B("\"I flagged that the data looks synthetic and that a real Instagram Insights export should confirm the findings.\""),
];

const mk = (children, ft) => new Document({ styles, numbering, creator: "Suman", title: ft,
  sections: [{ properties: { page }, footers: { default: footer(ft) }, children }] });
(async () => {
  fs.mkdirSync("deliverables", { recursive: true });
  await Promise.all([
    [flow, "Project Flow and Insights", "Sugar_Cosmetics_Project_Flow_and_Insights.docx"],
    [summary, "Business Summary", "Sugar_Cosmetics_Business_Summary.docx"],
    [guide, "Streamlit Dashboard Guide", "Sugar_Cosmetics_Streamlit_Dashboard_Guide.docx"],
  ].map(async ([c, t, f]) => fs.writeFileSync("deliverables/" + f, await Packer.toBuffer(mk(c, "Sugar Cosmetics · " + t)))));
  console.log("done");
})();
