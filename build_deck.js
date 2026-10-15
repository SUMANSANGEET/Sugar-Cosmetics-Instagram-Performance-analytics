// Builds the stakeholder deck: deliverables/Sugar_Cosmetics_Instagram_Stakeholder_Deck.pptx
const fs = require("fs");
const pptxgen = require("pptxgenjs");
const SK = "/root/.claude/skills/synced/6963891d-ec1a-4743-a690-683690f65799_14775023-551e-41ab-afa5-3100eea37d70/pptx";
const { applyTheme } = require(SK + "/scripts/apply_theme.js");

const F = JSON.parse(fs.readFileSync("docs/facts.json"));
const K = F.kpi;
const THEME = {
  name: "Sugar Insights", headFontFace: "Cambria", bodyFontFace: "Calibri",
  colors: { dk1: "1F2430", lt1: "FFFFFF", dk2: "3A1030", lt2: "F5F6F8", accent1: "C2185B", accent2: "B9BEC8", accent3: "F3A6C4",
    accent4: "7A0E39", accent5: "6B7280", accent6: "DE5F92", hlink: "C2185B", folHlink: "7A0E39" },
};
const ACC = "C2185B", BASE = "B9BEC8", INK = "1F2430", MUT = "6B7280", SOFT = "FDF2F7", DARK = "3A1030", GREYBG = "F5F6F8";

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5
pres.theme = { headFontFace: "Cambria", bodyFontFace: "Calibri" };
pres.title = "Instagram Performance Analytics — Sugar Cosmetics";
pres.author = "Suman";
const C = pres.SchemeColor;

pres.defineSlideMaster({
  title: "DARK", background: { color: DARK },
  objects: [], slideNumber: undefined,
  slideNumber: undefined,
});
pres.defineSlideMaster({
  title: "CONTENT", background: { color: "FFFFFF" },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.4, w: 12.1, h: 1.0, fontFace: "Cambria", fontSize: 30, bold: true, color: INK, valign: "top", align: "left", margin: 0 }, text: "" } },
    { text: { text: "Sugar Cosmetics · Instagram Performance Analytics", options: { x: 0.6, y: 7.0, w: 8, h: 0.3, fontSize: 10, color: MUT, fontFace: "Calibri", margin: 0 } } },
  ],
  slideNumber: { x: 12.2, y: 7.0, w: 0.5, h: 0.3, fontSize: 10, color: MUT, align: "right" },
});

const n0 = (n) => Math.round(n).toLocaleString("en-US");
const fm = (n) => (n >= 1e9 ? (n / 1e9).toFixed(2) + "B" : (n / 1e6).toFixed(2) + "M");
const p2 = (n) => n.toFixed(2) + "%";
const shadow = () => ({ type: "outer", color: "000000", opacity: 0.10, blur: 8, offset: 2, angle: 90 });

function card(s, x, y, w, h, name) {
  s.addShape(pres.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.08, fill: { color: "FFFFFF" }, line: { color: "E5E7EB", width: 0.75 }, shadow: shadow(), objectName: name });
}
function stat(s, x, y, w, big, label, name, color = ACC) {
  card(s, x, y, w, 1.45, name + " card");
  s.addText(big, { x: x + 0.15, y: y + 0.18, w: w - 0.3, h: 0.7, fontSize: 36, bold: true, color, fontFace: "Cambria", align: "left", margin: 0, isTextBox: true, objectName: name + " value" });
  s.addText(label, { x: x + 0.15, y: y + 0.9, w: w - 0.3, h: 0.45, fontSize: 14, color: MUT, margin: 0, valign: "top", isTextBox: true, objectName: name + " label" });
}
function insightBox(s, text, y = 6.2) {
  s.addShape(pres.ShapeType.roundRect, { x: 0.6, y, w: 12.1, h: 0.65, rectRadius: 0.06, fill: { color: SOFT }, line: { color: SOFT, width: 0.5 }, objectName: "Insight box" });
  s.addText(text, { x: 0.8, y, w: 11.7, h: 0.65, fontSize: 14, color: INK, valign: "middle", margin: 0, isTextBox: true, objectName: "Insight text" });
}
const chartBase = (title) => ({
  showTitle: true, title, titleFontSize: 14, titleColor: INK, titleFontFace: "Calibri",
  catAxisLabelColor: MUT, valAxisLabelColor: MUT, catAxisLabelFontSize: 12, valAxisLabelFontSize: 11,
  catAxisLabelFontFace: "Calibri", valAxisLabelFontFace: "Calibri",
  valGridLine: { color: "E7E9EE", size: 0.5 }, catGridLine: { style: "none" }, showLegend: false,
  dataLabelFontSize: 12, dataLabelColor: INK, dataLabelFontFace: "Calibri", showValue: true,
});
const hlColors = (vals) => { const i = vals.indexOf(Math.max(...vals)); return vals.map((_, k) => (k === i ? ACC : BASE)); };

const pt = F.post_type, dw = F.weekday, ht = [...F.hashtag].sort((a, b) => b.er - a.er), cp = F.campaign;

// ---------- 1. Title ----------
{
  const s = pres.addSlide({ masterName: "DARK" });
  s.addText("Instagram Performance Analytics", { x: 0.8, y: 2.0, w: 11.5, h: 1.0, fontSize: 48, bold: true, color: "FFFFFF", fontFace: "Cambria", margin: 0, isTextBox: true, objectName: "Deck title" });
  s.addText("What 50,000 Sugar Cosmetics posts tell us about engagement, and where to focus next", { x: 0.8, y: 3.15, w: 10.5, h: 0.9, fontSize: 22, color: "F3A6C4", margin: 0, valign: "top", isTextBox: true, objectName: "Deck subtitle" });
  s.addText("Stakeholder briefing  ·  Data window 19 Apr 2024 – 19 Apr 2025  ·  Prepared by Suman", { x: 0.8, y: 6.3, w: 11, h: 0.4, fontSize: 14, color: "D9C2D0", margin: 0, isTextBox: true, objectName: "Deck byline" });
  s.addNotes("Open with the headline: performance is healthy and steady, but the data does not show a single winning format, day or hashtag. The opportunity is reach, deeper engagement and follower conversion.");
}

// ---------- 2. Executive summary ----------
{
  const s = pres.addSlide({ masterName: "CONTENT" });
  s.addText("Healthy and steady, but no proven winner", { placeholder: "title" });
  stat(s, 0.6, 1.6, 2.85, p2(K.avg_er), "Average engagement rate", "KPI ER");
  stat(s, 3.65, 1.6, 2.85, fm(K.reach), "Total reach (summed across posts)", "KPI reach");
  stat(s, 6.7, 1.6, 2.85, "< 1.2%", "Best-to-worst gap on every lever tested", "KPI gap");
  stat(s, 9.75, 1.6, 2.95, K.follow_conv.toFixed(0) + "%", "Of profile visitors follow the account", "KPI follow");
  const pts = [
    ["What we found", `Engagement rate holds at about ${K.avg_er.toFixed(1)}% every month. Reel, Story, Video and Image differ by only ${(pt[0].er - pt[3].er).toFixed(2)} points, and no gap is statistically significant.`],
    ["Where the opportunity is", `Reach drives volume, likes are ${K.like_share.toFixed(0)}% of interactions, and ${F.gap.pct.toFixed(1)}% of posts were widely seen but barely engaged with.`],
    ["What to do", "Scale reach, deepen engagement beyond likes, lift profile-to-follow conversion, and A/B test before shifting the content mix."],
  ];
  pts.forEach(([h, t], i) => {
    const y = 3.4 + i * 1.15;
    s.addText(h, { x: 0.6, y, w: 3.0, h: 0.9, fontSize: 18, bold: true, color: ACC, fontFace: "Cambria", margin: 0, valign: "top", isTextBox: true, objectName: `Summary head ${i + 1}` });
    s.addText(t, { x: 3.7, y, w: 9.0, h: 0.9, fontSize: 16, color: INK, margin: 0, valign: "top", isTextBox: true, objectName: `Summary text ${i + 1}` });
  });
  s.addNotes("Four numbers carry the story. The best-to-worst gaps across every lever are all about one percent or less, so effort should go to reach, depth of engagement and conversion.");
}

// ---------- 3. Account health ----------
{
  const s = pres.addSlide({ masterName: "CONTENT" });
  s.addText("Posting and engagement are consistent month to month", { placeholder: "title" });
  const m = F.monthly;
  s.addChart(pres.charts.LINE, [{ name: "Posts", labels: m.map((r) => r.month.slice(0, 3) + " " + r.month.slice(-2)), values: m.map((r) => r.n) }], {
    x: 0.6, y: 1.5, w: 8.2, h: 4.5, ...chartBase("Posts (records) per month"), chartColors: [ACC], lineSize: 3, lineDataSymbolSize: 8,
    dataLabelPosition: "t", dataLabelFormatCode: "#,##0", valAxisMinVal: 0, valAxisMaxVal: 5000, valAxisLabelFormatCode: "#,##0",
  });
  const items = [[fm(K.likes), "Likes"], [fm(K.comments), "Comments"], [fm(K.engagement), "Total interactions"], [fm(K.impressions), "Impressions"]];
  items.forEach(([v, l], i) => {
    const x = 9.1 + (i % 2) * 1.85, y = 1.6 + Math.floor(i / 2) * 1.6;
    card(s, x, y, 1.7, 1.4, `Mini ${l} card`);
    s.addText(v, { x: x + 0.1, y: y + 0.2, w: 1.5, h: 0.55, fontSize: 24, bold: true, color: ACC, fontFace: "Cambria", margin: 0, isTextBox: true, objectName: `Mini ${l} value` });
    s.addText(l, { x: x + 0.1, y: y + 0.8, w: 1.5, h: 0.45, fontSize: 14, color: MUT, margin: 0, valign: "top", isTextBox: true, objectName: `Mini ${l} label` });
  });
  s.addText("April 2024 and April 2025 are partial months (data runs 19 Apr to 19 Apr).", { x: 9.1, y: 4.9, w: 3.6, h: 0.8, fontSize: 12, italic: true, color: MUT, margin: 0, valign: "top", isTextBox: true, objectName: "Partial month note" });
  insightBox(s, "Cadence is a strength: about 4,100 records a month with no seasonal gaps, and engagement rate stays near 18.5% throughout.");
  s.addNotes("The first and last bars look low only because the file starts and ends on 19 April.");
}

// ---------- 4. Format & weekday ----------
{
  const s = pres.addSlide({ masterName: "CONTENT" });
  s.addText("Format and weekday barely move engagement", { placeholder: "title" });
  const pv = pt.map((r) => r.er);
  s.addChart(pres.charts.BAR, [{ name: "Engagement rate (%)", labels: pt.map((r) => r["Post Type"]), values: pv }], {
    x: 0.6, y: 1.5, w: 5.9, h: 4.5, ...chartBase("Avg engagement rate by post type (%)"), barDir: "col", chartColors: hlColors(pv), invertedColors: hlColors(pv),
    dataLabelPosition: "outEnd", dataLabelFormatCode: "0.00", valAxisMinVal: 0, valAxisMaxVal: 25, valAxisLabelFormatCode: "0", barGapWidthPct: 60,
  });
  const dv = dw.map((r) => r.er);
  s.addChart(pres.charts.BAR, [{ name: "Engagement rate (%)", labels: dw.map((r) => r["Day of Week"].slice(0, 3)), values: dv }], {
    x: 6.8, y: 1.5, w: 5.9, h: 4.5, ...chartBase("Avg engagement rate by weekday (%)"), barDir: "col", chartColors: hlColors(dv), invertedColors: hlColors(dv),
    dataLabelPosition: "outEnd", dataLabelFormatCode: "0.00", valAxisMinVal: 0, valAxisMaxVal: 25, valAxisLabelFormatCode: "0", barGapWidthPct: 40,
  });
  insightBox(s, `Reel (${p2(pt[0].er)}) and Wednesday (${p2(Math.max(...dv))}) lead, but gaps are ${F.spreads.post_type.toFixed(1)}% and ${F.spreads.weekday.toFixed(1)}% and not significant (p = ${F.pvalues["Post Type"].toFixed(2)} and ${F.pvalues["Day of Week"].toFixed(2)}).`);
  s.addNotes("Axes start at zero deliberately: the honest picture is that the bars are the same height. Hour of posting is not in the data and should be captured.");
}

// ---------- 5. Hashtags & campaigns ----------
{
  const s = pres.addSlide({ masterName: "CONTENT" });
  s.addText("Hashtags and campaigns perform alike too", { placeholder: "title" });
  const hv = ht.map((r) => r.er);
  s.addChart(pres.charts.BAR, [{ name: "Engagement rate (%)", labels: ht.map((r) => r.Hashtag), values: hv }], {
    x: 0.6, y: 1.5, w: 5.9, h: 4.5, ...chartBase("Avg engagement rate by hashtag (%)"), barDir: "bar", chartColors: hlColors(hv), invertedColors: hlColors(hv),
    dataLabelPosition: "outEnd", dataLabelFormatCode: "0.00", valAxisMinVal: 0, valAxisMaxVal: 25, valAxisLabelFormatCode: "0", valAxisHidden: true, valGridLine: { style: "none" }, catAxisOrientation: "maxMin", barGapWidthPct: 50,
  });
  const cv = cp.map((r) => r.er);
  s.addChart(pres.charts.BAR, [{ name: "Engagement rate (%)", labels: cp.map((r) => r["Campaign Type"]), values: cv }], {
    x: 6.8, y: 1.5, w: 5.9, h: 4.5, ...chartBase("Avg engagement rate by campaign (%)"), barDir: "bar", chartColors: hlColors(cv), invertedColors: hlColors(cv),
    dataLabelPosition: "outEnd", dataLabelFormatCode: "0.00", valAxisMinVal: 0, valAxisMaxVal: 25, valAxisLabelFormatCode: "0", valAxisHidden: true, valGridLine: { style: "none" }, catAxisOrientation: "maxMin", barGapWidthPct: 50,
  });
  insightBox(s, `${ht[0].Hashtag} and ${cp[0]["Campaign Type"]} lead on paper, yet gaps are only ${F.spreads.hashtag.toFixed(1)}% and ${F.spreads.campaign.toFixed(1)}%. Keep the brand and values hashtags; test, don't reallocate.`);
  s.addNotes("Hashtag test is indicative because a post with several hashtags counts once per tag.");
}

// ---------- 6. Funnel ----------
{
  const s = pres.addSlide({ masterName: "CONTENT" });
  s.addText("People see content but rarely go deeper", { placeholder: "title" });
  const st = ["Impressions", "Reach", "Likes", "Comments", "Saves", "Shares"];
  const raw = [K.impressions, K.reach, K.likes, K.comments, K.saves, K.shares];
  const vals = raw.map((v) => +(v / K.impressions * 100).toFixed(1));
  s.addChart(pres.charts.BAR, [{ name: "% of impressions", labels: st, values: vals }], {
    x: 0.6, y: 1.5, w: 7.6, h: 4.5, ...chartBase("Engagement funnel (% of impressions)"), barDir: "bar", chartColors: [BASE, BASE, ACC, ACC, ACC, ACC], invertedColors: [BASE, BASE, ACC, ACC, ACC, ACC],
    dataLabelPosition: "outEnd", dataLabelFormatCode: '0.0"%"', valAxisMinVal: 0, valAxisMaxVal: 120, valAxisHidden: true, valGridLine: { style: "none" }, catAxisOrientation: "maxMin", barGapWidthPct: 40,
  });
  stat(s, 8.6, 1.6, 4.1, K.pv_rate.toFixed(1) + "%", "Of reached accounts visit the profile", "Funnel PV");
  stat(s, 8.6, 3.25, 4.1, K.follow_conv.toFixed(1) + "%", "Of profile visitors follow (exploratory metric)", "Funnel follow");
  s.addText(`Likes are ${K.like_share.toFixed(0)}% of interactions; comments, saves and shares add just ${(100 - K.like_share).toFixed(0)}%.`, { x: 8.6, y: 5.0, w: 4.1, h: 0.9, fontSize: 14, color: INK, margin: 0, valign: "top", isTextBox: true, objectName: "Funnel note" });
  insightBox(s, `${K.reach_rate.toFixed(0)} of every 100 impressions are unique accounts and about 12 become likes. The big drop-off is from seeing to commenting, saving and sharing.`);
  s.addNotes("Comments, saves and shares signal intent and virality, so they are the quality lever. Shares and saves are shown in the order of size.");
}

// ---------- 7. Reach without interaction ----------
{
  const s = pres.addSlide({ masterName: "CONTENT" });
  s.addText("More reach brings more likes, not better engagement", { placeholder: "title" });
  s.addImage({ path: "docs/charts/reach_vs_er.png", x: 0.6, y: 1.5, w: 7.6, h: 3.9, altText: "Scatter of reach against engagement rate; high-reach, low-engagement posts highlighted" });
  stat(s, 8.6, 1.6, 4.1, n0(F.gap.n), `Records (${F.gap.pct.toFixed(1)}%) with top-25% reach but bottom-25% engagement`, "Gap count");
  stat(s, 8.6, 3.25, 4.1, "r = " + F.corr_reach_likes.toFixed(2), `Reach vs likes. Reach vs engagement rate: r = ${F.corr_reach_er.toFixed(2)}`, "Correlation");
  s.addText(`Top engagement-rate posts reach ${F.top_er[0]["Engagement Rate (%)"].toFixed(0)}% with below-average reach (median ${n0(F.top_er_median_reach)}). None of them are in the top 10 by likes.`, { x: 0.6, y: 5.45, w: 7.6, h: 0.65, fontSize: 14, color: MUT, margin: 0, valign: "top", isTextBox: true, objectName: "Hidden gems note" });
  insightBox(s, "Highly visible posts that fail to convert attention into action are the clearest content to fix first.");
  s.addNotes("Each dot is a record; the pink dots are the 6.2% of records in the high-reach, low-engagement corner.");
}

// ---------- 8. Recommendations ----------
{
  const s = pres.addSlide({ masterName: "CONTENT" });
  s.addText("Six actions to grow reach, depth and followers", { placeholder: "title" });
  const recs = [
    ["Scale reach", "Boost proven creatives and expand influencer collabs. Each 1,000 reached yields about " + Math.round(K.per_1000_reach) + " interactions."],
    ["Fix seen-but-ignored", "Audit the " + n0(F.gap.n) + " high-reach, low-engagement posts: stronger hooks, clear calls-to-action, polls and giveaways."],
    ["Deepen engagement", "Build save-worthy tutorials and share-worthy festive and challenge content to move beyond likes."],
    ["Convert visitors", "Refresh bio, highlights, pinned posts and link-in-bio; add 'follow for shade drops' end frames."],
    ["Test, don't guess", "Run 4-week A/B tests on format, hashtag count and posting time. Act only on significant results."],
    ["Close the data gaps", "Capture post ID, caption, posting hour, ad spend and follower count to unlock timing, ROI and growth analysis."],
  ];
  recs.forEach(([h, t], i) => {
    const col = i % 3, row = Math.floor(i / 3);
    const x = 0.6 + col * 4.1, y = 1.55 + row * 2.6;
    card(s, x, y, 3.9, 2.4, `Rec ${i + 1} card`);
    s.addShape(pres.ShapeType.ellipse, { x: x + 0.2, y: y + 0.2, w: 0.5, h: 0.5, fill: { color: ACC }, line: { color: ACC }, objectName: `Rec ${i + 1} badge` });
    s.addText(String(i + 1), { x: x + 0.2, y: y + 0.2, w: 0.5, h: 0.5, fontSize: 16, bold: true, color: "FFFFFF", align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: `Rec ${i + 1} number` });
    s.addText(h, { x: x + 0.85, y: y + 0.2, w: 2.9, h: 0.5, fontSize: 18, bold: true, color: INK, fontFace: "Cambria", margin: 0, valign: "middle", isTextBox: true, objectName: `Rec ${i + 1} title` });
    s.addText(t, { x: x + 0.25, y: y + 0.85, w: 3.45, h: 1.45, fontSize: 14, color: INK, margin: 0, valign: "top", isTextBox: true, objectName: `Rec ${i + 1} text` });
  });
  s.addNotes("Campaign ideas: tutorial Reels series, influencer takeovers with giveaways, festive offer Stories with polls, vegan and cruelty-free values content, profile-visit nudges on high-reach posts.");
}

// ---------- 9. Next steps (dark) ----------
{
  const s = pres.addSlide({ masterName: "DARK" });
  s.addText("Next 4 weeks", { x: 0.8, y: 0.6, w: 11, h: 0.8, fontSize: 36, bold: true, color: "FFFFFF", fontFace: "Cambria", margin: 0, isTextBox: true, objectName: "Next steps title" });
  const steps = [["Week 1", "Audit high-reach, low-engagement posts; add a comment-driving call-to-action to every post."], ["Weeks 2–3", "A/B test: same creative as Reel vs Image; 2 vs 3 hashtags; morning vs evening."], ["Week 4", "Read results, keep only statistically significant winners, refresh profile conversion assets."]];
  steps.forEach(([h, t], i) => {
    const y = 1.8 + i * 1.2;
    s.addText(h, { x: 0.8, y, w: 2.2, h: 0.9, fontSize: 20, bold: true, color: "F3A6C4", fontFace: "Cambria", margin: 0, valign: "top", isTextBox: true, objectName: `Step ${i + 1} label` });
    s.addText(t, { x: 3.1, y, w: 9.3, h: 0.9, fontSize: 18, color: "FFFFFF", margin: 0, valign: "top", isTextBox: true, objectName: `Step ${i + 1} text` });
  });
  s.addShape(pres.ShapeType.roundRect, { x: 0.8, y: 5.5, w: 11.7, h: 1.2, rectRadius: 0.08, fill: { color: "4E1A42" }, line: { color: "4E1A42" }, objectName: "Data note box" });
  s.addText(`Data note: the file has no captions or post IDs and about ${Math.round(F.records_per_day)} records per day with unusually flat distributions, which suggests synthetic or aggregated data. Treat these results as a validated framework and confirm them on the live Instagram Insights export.`, { x: 1.0, y: 5.5, w: 11.3, h: 1.2, fontSize: 14, color: "F0DCE8", margin: 0, valign: "middle", isTextBox: true, objectName: "Data note text" });
}

(async () => {
  fs.mkdirSync("deliverables", { recursive: true });
  const out = "deliverables/Sugar_Cosmetics_Instagram_Stakeholder_Deck.pptx";
  await pres.writeFile({ fileName: out });
  await applyTheme(out, THEME);
  console.log("saved", out);
})();
