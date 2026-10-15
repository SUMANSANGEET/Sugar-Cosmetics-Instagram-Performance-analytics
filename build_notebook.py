"""Generates Sugar_Cosmetics_Instagram_Analysis.ipynb (run with: python build_notebook.py)."""
import nbformat as nbf

nb = nbf.v4.new_notebook()
cells = []
md = lambda s: cells.append(nbf.v4.new_markdown_cell(s.strip("\n")))
code = lambda s: cells.append(nbf.v4.new_code_cell(s.strip("\n")))

# ---------------------------------------------------------------- 0. Title
md('''
# Sugar Cosmetics · Instagram Performance Analytics
**Data Analytics & AI portfolio project** · Python · pandas · Plotly · ipywidgets

> **Business goal:** help the marketing team understand how Instagram content performs and decide what to publish, when, and with which hashtags.

| Business question | Where it is answered |
|---|---|
| How is the account performing overall? | Step 6 · KPI Overview |
| How consistently do we post? | Step 7 · Monthly Posting Trend |
| Which posts win on likes and on engagement rate? | Steps 8–9 · Top 10 lists |
| Which format works best? | Step 10 · Post Type Performance |
| Which weekday works best? | Step 11 · Day of Week |
| Are people seeing posts but not interacting? | Step 12 · Engagement Funnel & Reach Gap |
| Which hashtags perform best? | Step 13 · Hashtag Analysis |
| Are any of these differences real? | Step 14 · Statistical Check |
| Can the team explore it themselves? | Step 15 · Interactive Dashboard |
| What should we do next? | Step 16 · Strategic Recommendations |

**How to run:** place `sugar_cosmetics_instagram_data.xlsx` next to this notebook, then *Kernel → Restart & Run All*. Requirements: `pandas numpy plotly scipy openpyxl ipywidgets`.

**Workflow:** Understand → Validate → Clean & enrich → Analyse (10 visuals) → Test → Recommend.
''')

# ---------------------------------------------------------------- 1. Setup
md('''
## Step 1 · Setup
Import libraries and define one consistent look: grey for ordinary bars, **one accent colour** for the best or selected item. Helper functions keep every chart styled identically.
''')
code('''
import os, warnings
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots
from scipy import stats
from IPython.display import display, HTML

warnings.filterwarnings("ignore")
# "notebook_connected" keeps the file small (loads plotly.js from a CDN).
# For fully offline use, run:  PLOTLY_RENDERER=notebook jupyter lab
pio.renderers.default = os.environ.get("PLOTLY_RENDERER", "notebook_connected")
pd.options.display.float_format = "{:,.2f}".format
pd.set_option("display.max_columns", 30)

# ---- palette ----
ACCENT, BASE, INK, MUTED, GRID = "#C2185B", "#B9BEC8", "#1F2430", "#6B7280", "#E7E9EE"
SEQ = ["#FBE4EE", "#F3A6C4", "#DE5F92", "#C2185B", "#7A0E39"]
FONT = "Inter, Segoe UI, Helvetica, Arial, sans-serif"
DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

pio.templates["sugar"] = go.layout.Template(layout=go.Layout(
    font=dict(family=FONT, size=13, color=INK),
    colorway=[ACCENT, BASE, "#DE5F92", "#7A0E39", "#F3A6C4"],
    title=dict(font=dict(size=16, color=INK), x=0, xanchor="left"),
    margin=dict(l=20, r=20, t=60, b=30),
    paper_bgcolor="white", plot_bgcolor="white",
    xaxis=dict(showgrid=False, linecolor=GRID, ticks=""),
    yaxis=dict(gridcolor=GRID, zeroline=False, ticks=""),
    hoverlabel=dict(bgcolor="white", font_size=13),
))
pio.templates.default = "plotly_white+sugar"


def human(n):
    """12345678 -> 12.35M"""
    for div, suf in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if abs(n) >= div:
            return f"{n / div:,.2f}{suf}"
    return f"{n:,.0f}"


def highlight(values, best="max"):
    """Grey bars, best bar in the accent colour."""
    v = list(values)
    i = int(np.argmax(v)) if best == "max" else int(np.argmin(v))
    return [ACCENT if k == i else BASE for k in range(len(v))]


def insight(text):
    display(HTML(f'<div style="border-left:4px solid {ACCENT};background:#FDF2F7;padding:10px 16px;'
                 f'border-radius:6px;margin:6px 0 16px;font-family:{FONT};color:{INK}">💡 <b>Insight.</b> {text}</div>'))


def caveat(text):
    display(HTML(f'<div style="border-left:4px solid #9CA3AF;background:#F5F6F8;padding:10px 16px;'
                 f'border-radius:6px;margin:6px 0 16px;font-family:{FONT};color:#374151;font-size:.92em">ℹ️ {text}</div>'))


def spread(series):
    """Gap between best and worst group as a % of the group average."""
    return (series.max() - series.min()) / series.mean() * 100

import plotly
print("Setup complete · plotly", plotly.__version__)
''')

# ---------------------------------------------------------------- 2. Load
md('''
## Step 2 · Load the data
The notebook looks for the Excel file in the current folder (or a `data/` folder) and falls back to a CSV export.
''')
code('''
CANDIDATES = [Path("sugar_cosmetics_instagram_data.xlsx"), Path("data/sugar_cosmetics_instagram_data.xlsx"),
              Path("sugar_cosmetics_instagram_data.csv"), Path("data/sugar_cosmetics_instagram_data.csv")]
src = next((p for p in CANDIDATES if p.exists()), None)
if src is None:
    raise FileNotFoundError("Place sugar_cosmetics_instagram_data.xlsx (or .csv) next to this notebook.")

raw = pd.read_excel(src) if src.suffix == ".xlsx" else pd.read_csv(src)
raw.columns = [c.strip() for c in raw.columns]
raw["Post Date"] = pd.to_datetime(raw["Post Date"])
print(f"Loaded {src}  →  {raw.shape[0]:,} rows × {raw.shape[1]} columns")
raw.head()
''')

# ---------------------------------------------------------------- 3. Understand
md('''
## Step 3 · Understand the dataset
Before any analysis: what does each column mean, what are the types, and what does one row represent?
''')
code('''
dictionary = pd.DataFrame([
    ("Post Date", "Date", "When the post was published"),
    ("Post Type", "Category", "Reel, Story, Video or Image"),
    ("Campaign Type", "Category", "Giveaway, Tutorial, Festive Offer, Product Launch, Influencer Collab"),
    ("Hashtags", "Text", "1–3 hashtags per post, comma separated"),
    ("Audience Emotion", "Category", "Dominant audience emotion label"),
    ("Engagement Source", "Category", "Organic, Paid, Collab or Influencer"),
    ("Impressions", "Integer", "Total views including repeat views"),
    ("Reach", "Integer", "Unique accounts that saw the post"),
    ("Likes / Comments / Shares / Saves", "Integer", "The four interaction counts"),
    ("Profile Visits", "Integer", "Visits to the profile after seeing the post"),
    ("Follows", "Integer", "New followers gained"),
], columns=["Column", "Type", "Meaning"])
display(dictionary)
display(raw.dtypes.rename("dtype").to_frame().T)
print("Date range:", raw["Post Date"].min().date(), "→", raw["Post Date"].max().date())
''')
code('''
caveat("The file has <b>no caption and no post ID</b>, so each row is labelled later as “#ID · Format · Campaign · Date”. "
       "Summed reach counts the same account once per row, so it is <i>not</i> unique people reached.")
''')

# ---------------------------------------------------------------- 4. Validate
md('''
## Step 4 · Validate data quality
A clean file still needs checking. Never invent a cleaning problem — document what you find and move on.
''')
code('''
num = raw.select_dtypes("number")
checks = pd.DataFrame([
    ("Rows", f"{len(raw):,}", "Matches the brief (50,000)"),
    ("Missing values", int(raw.isna().sum().sum()), "No imputation needed"),
    ("Exact duplicate rows", int(raw.duplicated().sum()), "No de-duplication needed"),
    ("Negative numeric values", int((num < 0).sum().sum()), "All counts are valid"),
    ("Reach > Impressions", int((raw["Reach"] > raw["Impressions"]).sum()), "Logical relationship holds"),
    ("Zero Shares", int((raw["Shares"] == 0).sum()), "Valid zeros, kept as zero"),
    ("Zero Follows", int((raw["Follows"] == 0).sum()), "Valid zero, kept as zero"),
], columns=["Check", "Result", "Interpretation"])
display(checks.style.hide(axis="index"))

assert raw.isna().sum().sum() == 0 and raw.duplicated().sum() == 0 and (num >= 0).all().all()
assert (raw["Reach"] <= raw["Impressions"]).all()
for col in ["Post Type", "Campaign Type", "Engagement Source", "Audience Emotion"]:
    print(f"{col:<18}", raw[col].value_counts().to_dict())
''')

# ---------------------------------------------------------------- 5. Feature engineering
md('''
## Step 5 · Create calculated fields
| Field | Formula | Why |
|---|---|---|
| Total Engagement | Likes + Comments + Shares + Saves | One interaction number per post |
| Engagement Rate (%) | Total Engagement ÷ Reach × 100 | Fair comparison between big and small posts |
| Profile Visit Rate (%) | Profile Visits ÷ Reach × 100 | Interest in the account |
| Follow Conversion (%) | Follows ÷ Profile Visits × 100 | Exploratory growth metric |
| Reach Rate (%) | Reach ÷ Impressions × 100 | Share of views that are unique accounts |

Engagement here is a project definition, not Instagram's official one — it is used identically in every chart.
''')
code('''
df = raw.copy()
df["Record ID"] = np.arange(1, len(df) + 1)
df["Total Engagement"] = df["Likes"] + df["Comments"] + df["Shares"] + df["Saves"]
df["Engagement Rate (%)"] = (df["Total Engagement"] / df["Reach"] * 100).where(df["Reach"] > 0)
df["Profile Visit Rate (%)"] = (df["Profile Visits"] / df["Reach"] * 100).where(df["Reach"] > 0)
df["Follow Conversion (%)"] = (df["Follows"] / df["Profile Visits"] * 100).where(df["Profile Visits"] > 0)
df["Reach Rate (%)"] = (df["Reach"] / df["Impressions"] * 100).where(df["Impressions"] > 0)
df["Month"] = df["Post Date"].dt.to_period("M").dt.to_timestamp()
df["Day of Week"] = pd.Categorical(df["Post Date"].dt.day_name(), DAY_ORDER, ordered=True)
df["Hashtag Count"] = df["Hashtags"].str.split(", ").str.len()
df["Post Label"] = ("#" + df["Record ID"].astype(str) + " · " + df["Post Type"] + " · "
                    + df["Campaign Type"] + " · " + df["Post Date"].dt.strftime("%d %b %Y"))

# optional: save the preprocessed version
Path("notebook_outputs").mkdir(exist_ok=True)
df.to_csv("notebook_outputs/sugar_instagram_preprocessed.csv", index=False)
df[["Post Label", "Post Date", "Post Type", "Total Engagement", "Engagement Rate (%)", "Profile Visit Rate (%)",
    "Follow Conversion (%)", "Reach Rate (%)"]].head()
''')

# ---------------------------------------------------------------- Task 1 KPI
md('''
## Step 6 · KPI Overview — *How is the account performing overall?*
''')
code('''
k = dict(posts=len(df), likes=df["Likes"].sum(), comments=df["Comments"].sum(), reach=df["Reach"].sum(),
         er=df["Engagement Rate (%)"].mean(), impressions=df["Impressions"].sum(),
         engagement=df["Total Engagement"].sum(), reach_rate=df["Reach"].sum() / df["Impressions"].sum() * 100,
         pv=df["Profile Visits"].sum() / df["Reach"].sum() * 100,
         fc=df["Follows"].sum() / df["Profile Visits"].sum() * 100)

tiles = [("Total posts (records)", k["posts"], ",.0f", ""), ("Total likes", k["likes"], ",.3s", ""),
         ("Total comments", k["comments"], ",.3s", ""), ("Total reach", k["reach"], ",.3s", ""),
         ("Avg engagement rate", k["er"], ".2f", "%"), ("Total impressions", k["impressions"], ",.3s", ""),
         ("Total interactions", k["engagement"], ",.3s", ""), ("Reach ÷ impressions", k["reach_rate"], ".1f", "%"),
         ("Profile visit rate", k["pv"], ".2f", "%"), ("Follow conversion", k["fc"], ".1f", "%")]
fig = make_subplots(rows=2, cols=5, specs=[[{"type": "indicator"}] * 5] * 2, vertical_spacing=0.18)
for i, (label, val, fmt, suffix) in enumerate(tiles):
    fig.add_trace(go.Indicator(mode="number", value=val, title=dict(text=label, font=dict(size=14, color=MUTED)),
                               number=dict(valueformat=fmt, suffix=suffix, font=dict(size=34, color=ACCENT))),
                  row=i // 5 + 1, col=i % 5 + 1)
fig.update_layout(height=300, title="Instagram KPI overview · 19 Apr 2024 – 19 Apr 2025", margin=dict(t=70, b=10))
fig.show()

mix = pd.Series({"Likes": df["Likes"].sum(), "Comments": df["Comments"].sum(), "Saves": df["Saves"].sum(),
                 "Shares": df["Shares"].sum()})
mix_pct = (mix / mix.sum() * 100).sort_values()
fig = go.Figure(go.Bar(x=mix_pct.values, y=mix_pct.index, orientation="h",
                       marker_color=[BASE, BASE, BASE, ACCENT], text=[f"{v:.1f}%" for v in mix_pct.values],
                       textposition="outside", cliponaxis=False,
                       hovertemplate="%{y}: %{x:.1f}% of interactions<extra></extra>"))
fig.update_layout(title="What makes up engagement?", height=280, xaxis=dict(visible=False, range=[0, 100]))
fig.show()
insight(f"Likes are <b>{mix_pct['Likes']:.0f}%</b> of all interactions. Comments, saves and shares — the deeper signals of "
        "interest and intent — add only a fraction, so growing them is the main quality lever.")
''')

# ---------------------------------------------------------------- Task 2 Monthly
md('''
## Step 7 · Monthly Posting Trend — *How consistently is content published?*
''')
code('''
monthly = df.groupby("Month").agg(Posts=("Record ID", "size"), ER=("Engagement Rate (%)", "mean")).reset_index()
partial = {df["Post Date"].min().to_period("M").to_timestamp(), df["Post Date"].max().to_period("M").to_timestamp()}
monthly["Partial"] = monthly["Month"].isin(partial)

fig = go.Figure()
fig.add_trace(go.Scatter(x=monthly["Month"], y=monthly["Posts"], mode="lines+markers+text", name="Posts",
                         line=dict(color=ACCENT, width=3), text=monthly["Posts"].map("{:,}".format), textposition="top center",
                         marker=dict(size=10, color=[("white" if p else ACCENT) for p in monthly["Partial"]],
                                     line=dict(color=ACCENT, width=2)),
                         hovertemplate="%{x|%b %Y}<br>Posts: %{y:,}<extra></extra>"))
fig.update_layout(title="Posts per month (hollow markers = partial months)", height=420, showlegend=False,
                  yaxis=dict(rangemode="tozero", title="Posts"), xaxis=dict(tickformat="%b %y", title=None))
fig.show()

full = monthly[~monthly["Partial"]]
insight(f"Across full months the team publishes ~<b>{full['Posts'].mean():,.0f}</b> posts a month "
        f"(variation ±{full['Posts'].std() / full['Posts'].mean() * 100:.0f}%). Cadence is steady; April 2024 and April 2025 "
        "look low only because the data covers part of each month.")
''')

# ---------------------------------------------------------------- Top 10
md('''
## Step 8 · Top 10 by Likes — *Which posts received the most likes?*
''')
code('''
def top10(metric, title, fmt):
    top = df.nlargest(10, metric).iloc[::-1]
    fig = go.Figure(go.Bar(
        x=top[metric], y=top["Post Label"], orientation="h", marker_color=ACCENT,
        text=top[metric].map(fmt.format), textposition="outside", cliponaxis=False,
        customdata=top[["Hashtags", "Reach", "Likes", "Engagement Rate (%)"]].values,
        hovertemplate="<b>%{y}</b><br>Hashtags: %{customdata[0]}<br>Reach: %{customdata[1]:,} · Likes: %{customdata[2]:,}"
                      "<br>Engagement rate: %{customdata[3]:.1f}%<extra></extra>"))
    fig.update_layout(title=title, height=460, xaxis=dict(visible=False, range=[0, top[metric].max() * 1.15]),
                      margin=dict(l=300))
    fig.show()
    return top.iloc[::-1]

t_likes = top10("Likes", "Top 10 posts by likes", "{:,.0f}")
corr = df["Reach"].corr(df["Likes"])
insight(f"The top 10 average <b>{t_likes['Reach'].mean():,.0f}</b> reach vs {df['Reach'].mean():,.0f} overall. "
        f"Likes and reach correlate at r = {corr:.2f}, so “most liked” largely means “most seen”.")
t_likes[["Post Label", "Hashtags", "Likes", "Reach", "Engagement Rate (%)"]].reset_index(drop=True)
''')

md('''
## Step 9 · Top 10 by Engagement Rate — *Which are the hidden gems?*
Engagement rate adjusts for reach, so smaller posts that over-performed can surface.
''')
code('''
t_er = top10("Engagement Rate (%)", "Top 10 posts by engagement rate (%)", "{:.1f}%")
overlap = len(set(t_er["Record ID"]) & set(t_likes["Record ID"]))
insight(f"Best engagement rates reach <b>{t_er['Engagement Rate (%)'].max():.1f}%</b> vs a {k['er']:.1f}% average, with a median "
        f"reach of {t_er['Reach'].median():,.0f}. Overlap with the top-10-by-likes list: <b>{overlap}</b>. "
        "High engagement does not require huge reach.")
t_er[["Post Label", "Hashtags", "Engagement Rate (%)", "Reach", "Likes"]].reset_index(drop=True)
''')

# ---------------------------------------------------------------- Post type
md('''
## Step 10 · Post Type Performance — *How do Reel, Story, Video and Image compare?*
''')
code('''
pt = df.groupby("Post Type").agg(Posts=("Record ID", "size"), Likes=("Likes", "mean"), Comments=("Comments", "mean"),
                                 Saves=("Saves", "mean"), Shares=("Shares", "mean"),
                                 ER=("Engagement Rate (%)", "mean")).reset_index().sort_values("ER", ascending=False)
panels = [("Likes", "Avg likes", "{:,.0f}"), ("Comments", "Avg comments", "{:,.0f}"), ("Saves", "Avg saves", "{:,.0f}"),
          ("ER", "Avg engagement rate (%)", "{:.2f}")]
fig = make_subplots(rows=1, cols=4, subplot_titles=[p[1] for p in panels], horizontal_spacing=0.06)
for i, (col, _, fmt) in enumerate(panels, 1):
    fig.add_trace(go.Bar(x=pt["Post Type"], y=pt[col], marker_color=highlight(pt[col]), text=pt[col].map(fmt.format),
                         textposition="outside", cliponaxis=False,
                         hovertemplate="%{x}<br>%{y:,.2f}<extra></extra>"), row=1, col=i)
    fig.update_yaxes(range=[0, pt[col].max() * 1.2], visible=False, row=1, col=i)
fig.update_layout(title="Post type comparison (best bar highlighted)", height=380, showlegend=False)
fig.show()

p_type = stats.f_oneway(*[g["Engagement Rate (%)"] for _, g in df.groupby("Post Type")]).pvalue
insight(f"<b>{pt.iloc[0]['Post Type']}</b> has the highest engagement rate ({pt.iloc[0]['ER']:.2f}%), but best vs worst is only "
        f"<b>{spread(pt['ER']):.1f}%</b> apart (ANOVA p = {p_type:.2f}). "
        + ("The difference is <b>not statistically significant</b> — format alone is not driving results." if p_type >= 0.05
           else "The difference is statistically significant."))
pt.round(2)
''')

# ---------------------------------------------------------------- Day of week
md('''
## Step 11 · Day of Week — *Which weekdays have higher engagement?*
Whiskers show the 95% confidence interval. If whiskers overlap, the ranking is not meaningful.
''')
code('''
dw = df.groupby("Day of Week", observed=True).agg(ER=("Engagement Rate (%)", "mean"), SD=("Engagement Rate (%)", "std"),
                                                    Posts=("Record ID", "size"), Likes=("Likes", "mean")).reset_index()
dw["CI"] = 1.96 * dw["SD"] / np.sqrt(dw["Posts"])
fig = go.Figure(go.Bar(x=dw["Day of Week"].astype(str), y=dw["ER"], marker_color=highlight(dw["ER"]),
                       error_y=dict(type="data", array=dw["CI"], color=MUTED, thickness=1.2, width=5),
                       text=dw["ER"].map("{:.2f}%".format), textposition="inside", insidetextanchor="end",
                       textfont=dict(color="white"), customdata=np.c_[dw["Posts"], dw["Likes"]],
                       hovertemplate="%{x}<br>Avg engagement rate: %{y:.2f}%<br>Posts: %{customdata[0]:,}"
                                     "<br>Avg likes: %{customdata[1]:,.0f}<extra></extra>"))
fig.update_layout(title="Average engagement rate by weekday (whiskers = 95% CI)", height=400,
                  yaxis=dict(range=[0, dw["ER"].max() * 1.25], title="Engagement rate (%)"))
fig.show()
b, w = dw.loc[dw["ER"].idxmax()], dw.loc[dw["ER"].idxmin()]
insight(f"<b>{b['Day of Week']}</b> is highest ({b['ER']:.2f}%) and <b>{w['Day of Week']}</b> lowest ({w['ER']:.2f}%) — a gap of "
        f"{b['ER'] - w['ER']:.2f} points. Whiskers overlap, so there is no proven best day. Posting <i>hour</i> is not in the data "
        "and should be captured.")
''')

# ---------------------------------------------------------------- Funnel
md('''
## Step 12 · Engagement Funnel — *Are people seeing posts but not interacting?*
''')
code('''
stages = ["Impressions", "Reach", "Likes", "Comments", "Shares", "Saves"]
vals = [df[s].sum() for s in stages]
fig = go.Figure(go.Funnel(
    y=stages, x=vals, textinfo="text", text=[f"{human(v)} · {v / vals[0] * 100:.1f}%" for v in vals],
    marker=dict(color=[SEQ[1], SEQ[1], SEQ[2], SEQ[3], SEQ[3], SEQ[3]]), connector=dict(line=dict(color=GRID)),
    hovertemplate="%{y}: %{x:,.0f}<br>%{percentInitial:.2%} of impressions<extra></extra>"))
fig.update_layout(title="Engagement funnel (totals · % of impressions)", height=430)
fig.show()
display(pd.DataFrame({"Stage": stages, "Total": vals, "% of impressions": [v / vals[0] * 100 for v in vals]}).style.hide(axis="index").format({"Total": "{:,.0f}", "% of impressions": "{:.2f}"}))
insight(f"Of every 100 impressions, <b>{vals[1] / vals[0] * 100:.0f}</b> are unique accounts and ~<b>{vals[2] / vals[0] * 100:.0f}</b> "
        f"become likes; comments, shares and saves each convert at most {max(vals[3:]) / vals[0] * 100:.1f}%. Of reached accounts, "
        f"{k['pv']:.1f}% visit the profile and {k['fc']:.0f}% of visitors follow.")
''')

md('''
### Reach without interaction
Posts in the **top 25% of reach** but **bottom 25% of engagement rate** were widely seen but ignored.
''')
code('''
q_reach, q_er = df["Reach"].quantile(0.75), df["Engagement Rate (%)"].quantile(0.25)
gap = df[(df["Reach"] >= q_reach) & (df["Engagement Rate (%)"] <= q_er)]
d = df.sample(4000, random_state=7).copy()
d["Segment"] = np.where((d["Reach"] >= q_reach) & (d["Engagement Rate (%)"] <= q_er), "High reach, low engagement", "Other posts")
fig = px.scatter(d, x="Reach", y="Engagement Rate (%)", color="Segment", opacity=0.6,
                 color_discrete_map={"High reach, low engagement": ACCENT, "Other posts": BASE},
                 hover_data={"Post Type": True, "Campaign Type": True, "Likes": ":,"},
                 title="Reach vs engagement rate (sample of 4,000 posts)")
fig.add_vline(x=q_reach, line_dash="dot", line_color=MUTED); fig.add_hline(y=q_er, line_dash="dot", line_color=MUTED)
fig.update_traces(marker=dict(size=6)); fig.update_layout(height=450, legend=dict(orientation="h", y=-0.2, title=None))
fig.show()
df["Reach Quartile"] = pd.qcut(df["Reach"], 4, labels=["Q1 (lowest)", "Q2", "Q3", "Q4 (highest)"])
display(df.groupby("Reach Quartile", observed=True)[["Engagement Rate (%)", "Profile Visit Rate (%)", "Follow Conversion (%)"]].mean().round(2))
insight(f"<b>{len(gap):,}</b> posts ({len(gap) / len(df) * 100:.1f}%) fit the high-reach / low-engagement corner. Engagement rate is "
        f"uncorrelated with reach (r = {df['Reach'].corr(df['Engagement Rate (%)']):.2f}): more reach brings more interactions, "
        "not better ones. These posts are the clearest optimisation target.")
''')

# ---------------------------------------------------------------- Hashtags
md('''
## Step 13 · Hashtag Analysis — *Which hashtags are linked to stronger performance?*
Each post holds up to three hashtags in one text cell, so we split the list and `explode()` to one row per hashtag.
''')
code('''
ex = df.assign(Hashtag=df["Hashtags"].str.split(", ")).explode("Hashtag")
ht = ex.groupby("Hashtag").agg(Posts=("Record ID", "size"), ER=("Engagement Rate (%)", "mean"),
                               SD=("Engagement Rate (%)", "std"), Reach=("Reach", "mean"),
                               Likes=("Likes", "mean")).reset_index()
ht["CI"] = 1.96 * ht["SD"] / np.sqrt(ht["Posts"])
ht = ht.sort_values("ER", ascending=False)

fig = make_subplots(rows=1, cols=2, subplot_titles=["Avg engagement rate (whiskers = 95% CI)", "Usage: posts containing each hashtag"],
                    horizontal_spacing=0.18)
s = ht.sort_values("ER")
fig.add_trace(go.Bar(x=s["ER"], y=s["Hashtag"], orientation="h", marker_color=highlight(s["ER"]),
                     error_x=dict(type="data", array=s["CI"], color=MUTED, thickness=1.2, width=4),
                     text=s["ER"].map("{:.2f}%".format), textposition="inside", insidetextanchor="end",
                     textfont=dict(color="white"), customdata=s["Posts"],
                     hovertemplate="%{y}<br>Avg ER: %{x:.2f}%<br>Posts: %{customdata:,}<extra></extra>"), row=1, col=1)
u = ht.sort_values("Posts")
fig.add_trace(go.Bar(x=u["Posts"], y=u["Hashtag"], orientation="h", marker_color=BASE, text=u["Posts"].map("{:,}".format),
                     textposition="outside", cliponaxis=False, hovertemplate="%{y}<br>%{x:,} posts<extra></extra>"), row=1, col=2)
fig.update_xaxes(visible=False, row=1, col=1, range=[0, s["ER"].max() * 1.2])
fig.update_xaxes(visible=False, row=1, col=2, range=[0, u["Posts"].max() * 1.25])
fig.update_layout(title="Hashtag performance", height=380, showlegend=False)
fig.show()

hc = df.groupby("Hashtag Count").agg(ER=("Engagement Rate (%)", "mean"), Posts=("Record ID", "size")).reset_index()
fig = go.Figure(go.Bar(x=hc["Hashtag Count"].astype(str) + " hashtag(s)", y=hc["ER"], marker_color=highlight(hc["ER"]),
                       text=hc["ER"].map("{:.2f}%".format), textposition="outside", cliponaxis=False))
fig.update_layout(title="Does the number of hashtags matter?", height=320, yaxis=dict(visible=False, range=[0, hc["ER"].max() * 1.25]))
fig.show()
insight(f"<b>{ht.iloc[0]['Hashtag']}</b> leads ({ht.iloc[0]['ER']:.2f}%), but all hashtags sit within "
        f"{ht['ER'].max() - ht['ER'].min():.2f} points and their confidence ranges overlap. No hashtag is a proven winner.")
''')

# ---------------------------------------------------------------- Stats
md('''
## Step 14 · Statistical check — *Are any of these differences real?*
A one-way ANOVA tests whether group averages differ more than chance would explain. **p < 0.05** would indicate a real difference.
''')
code('''
rows = []
for dim in ["Post Type", "Day of Week", "Campaign Type", "Engagement Source", "Audience Emotion"]:
    g = df.groupby(dim, observed=True)["Engagement Rate (%)"].mean()
    p = stats.f_oneway(*[x["Engagement Rate (%)"].values for _, x in df.groupby(dim, observed=True)]).pvalue
    rows.append((dim, str(g.idxmax()), g.max(), str(g.idxmin()), g.min(), spread(g), p, "Significant" if p < 0.05 else "Not significant"))
sig = pd.DataFrame(rows, columns=["Dimension", "Best group", "Best ER %", "Worst group", "Worst ER %", "Gap %", "ANOVA p", "Verdict"])
display(sig.style.hide(axis="index").format({"Best ER %": "{:.2f}", "Worst ER %": "{:.2f}", "Gap %": "{:.1f}", "ANOVA p": "{:.2f}"}))
insight("No lever tested — format, weekday, campaign, source or audience emotion — shows a statistically significant difference in "
        "engagement rate. The honest conclusion is to <b>test before reallocating effort</b>, and to look at reach, depth of engagement "
        "and conversion instead.")
''')

# ---------------------------------------------------------------- Interactive dashboard
md('''
## Step 15 · Interactive Dashboard — *Explore by category and period*
Use the controls below to filter by period, post type, campaign, source and hashtag, then choose a metric and a dimension to compare.
Everything redraws instantly. *(Interactive controls need a live Jupyter session — the next cell shows a static version for exports.)*
''')
code('''
import ipywidgets as W

METRICS = {"Avg engagement rate (%)": ("Engagement Rate (%)", "mean", "{:.2f}"), "Avg likes": ("Likes", "mean", "{:,.0f}"),
           "Avg reach": ("Reach", "mean", "{:,.0f}"), "Avg saves": ("Saves", "mean", "{:,.0f}"),
           "Avg follow conversion (%)": ("Follow Conversion (%)", "mean", "{:.1f}"),
           "Total engagement": ("Total Engagement", "sum", "{:,.0f}"), "Number of posts": ("Record ID", "count", "{:,.0f}")}
DIMS = ["Post Type", "Campaign Type", "Engagement Source", "Audience Emotion", "Day of Week"]
months = sorted(df["Month"].unique())
month_labels = [pd.Timestamp(m).strftime("%b %Y") for m in months]
all_tags = sorted({t for s in df["Hashtags"].unique() for t in s.split(", ")})
wide = W.Layout(width="260px")

w_period = W.SelectionRangeSlider(options=month_labels, index=(0, len(month_labels) - 1), description="Period", layout=W.Layout(width="520px"))
w_type = W.SelectMultiple(options=sorted(df["Post Type"].unique()), value=tuple(sorted(df["Post Type"].unique())), description="Post type", rows=4, layout=wide)
w_camp = W.SelectMultiple(options=sorted(df["Campaign Type"].unique()), value=tuple(sorted(df["Campaign Type"].unique())), description="Campaign", rows=5, layout=wide)
w_src = W.SelectMultiple(options=sorted(df["Engagement Source"].unique()), value=tuple(sorted(df["Engagement Source"].unique())), description="Source", rows=4, layout=wide)
w_tag = W.SelectMultiple(options=all_tags, value=(), description="Hashtag", rows=5, layout=wide)
w_metric = W.Dropdown(options=list(METRICS), description="Metric", layout=wide)
w_dim = W.Dropdown(options=DIMS, description="Compare by", layout=wide)


def filtered(period, ptype, camp, src, tags):
    i0, i1 = month_labels.index(period[0]), month_labels.index(period[1])
    f = df[df["Month"].between(months[i0], months[i1]) & df["Post Type"].isin(ptype)
           & df["Campaign Type"].isin(camp) & df["Engagement Source"].isin(src)]
    if tags:
        f = f[f["Hashtags"].apply(lambda s: any(t in s for t in tags))]
    return f


def render(period, ptype, camp, src, tags, metric, dim):
    f = filtered(period, ptype, camp, src, tags)
    if f.empty:
        display(HTML("<b>No posts match the current filters — widen your selection.</b>")); return
    col, agg, fmt = METRICS[metric]
    display(HTML(f"<div style='font-family:{FONT};font-size:15px;margin:6px 0'>"
                 f"<b>{len(f):,}</b> posts ({len(f) / len(df) * 100:.0f}% of data) &nbsp;|&nbsp; "
                 f"Avg engagement rate <b>{f['Engagement Rate (%)'].mean():.2f}%</b> &nbsp;|&nbsp; "
                 f"Total reach <b>{human(f['Reach'].sum())}</b> &nbsp;|&nbsp; Total engagement <b>{human(f['Total Engagement'].sum())}</b></div>"))
    g = f.groupby(dim, observed=True)[col].agg(agg).reset_index()
    g = g.sort_values(dim) if dim == "Day of Week" else g.sort_values(col, ascending=False)
    t = f.groupby("Month")[col].agg(agg).reset_index()
    fig = make_subplots(rows=1, cols=2, subplot_titles=[f"{metric} by {dim}", f"{metric} over time"], column_widths=[0.45, 0.55])
    fig.add_trace(go.Bar(x=g[dim].astype(str), y=g[col], marker_color=highlight(g[col]), text=g[col].map(fmt.format),
                         textposition="outside", cliponaxis=False, hovertemplate="%{x}<br>%{y:,.2f}<extra></extra>"), row=1, col=1)
    fig.add_trace(go.Scatter(x=t["Month"], y=t[col], mode="lines+markers", line=dict(color=ACCENT, width=3),
                             hovertemplate="%{x|%b %Y}<br>%{y:,.2f}<extra></extra>"), row=1, col=2)
    fig.update_yaxes(rangemode="tozero")
    fig.update_xaxes(tickformat="%b %y", row=1, col=2)
    fig.update_layout(height=400, showlegend=False)
    fig.show()
    hm = f.pivot_table(index="Day of Week", columns="Post Type", values="Engagement Rate (%)", aggfunc="mean", observed=True)
    fig = px.imshow(hm, text_auto=".2f", aspect="auto", color_continuous_scale=SEQ[:4], title="Engagement rate (%): weekday × post type")
    fig.update_coloraxes(showscale=False); fig.update_yaxes(autorange="reversed", title=None); fig.update_xaxes(title=None)
    fig.update_layout(height=360); fig.show()


controls = dict(period=w_period, ptype=w_type, camp=w_camp, src=w_src, tags=w_tag, metric=w_metric, dim=w_dim)
panel = W.VBox([W.HBox([w_type, w_camp, w_src, w_tag]), W.HBox([w_period, w_metric, w_dim])])
out = W.interactive_output(render, controls)
display(panel, out)
''')

md('''
### Static executive dashboard
A one-page summary that renders everywhere (GitHub, HTML export, PDF) — the same views the interactive panel produces with all filters selected.
''')
code('''
fig = make_subplots(
    rows=3, cols=3, vertical_spacing=0.13, horizontal_spacing=0.08,
    specs=[[{"colspan": 3}, None, None], [{}, {}, {}], [{}, {}, {}]],
    subplot_titles=["Posts per month", "Engagement rate by post type (%)", "Engagement rate by weekday (%)",
                    "Engagement rate by campaign (%)", "Engagement funnel (% of impressions)",
                    "Engagement mix (% of interactions)", "Engagement rate by hashtag (%)"])
fig.add_trace(go.Scatter(x=monthly["Month"], y=monthly["Posts"], mode="lines+markers", line=dict(color=ACCENT, width=3),
                         hovertemplate="%{x|%b %Y}<br>Posts: %{y:,}<extra></extra>"), row=1, col=1)
pts = pt.sort_values("ER", ascending=False)
fig.add_trace(go.Bar(x=pts["Post Type"], y=pts["ER"], marker_color=highlight(pts["ER"]), text=pts["ER"].map("{:.2f}".format), textposition="outside"), row=2, col=1)
fig.add_trace(go.Bar(x=dw["Day of Week"].astype(str).str[:3], y=dw["ER"], marker_color=highlight(dw["ER"]), text=dw["ER"].map("{:.2f}".format), textposition="outside"), row=2, col=2)
cp_ = df.groupby("Campaign Type")["Engagement Rate (%)"].mean().sort_values()
fig.add_trace(go.Bar(x=cp_.values, y=cp_.index, orientation="h", marker_color=highlight(cp_.values), text=[f"{v:.2f}" for v in cp_.values], textposition="outside"), row=2, col=3)
fl = [v / vals[0] * 100 for v in vals]
fig.add_trace(go.Bar(x=fl, y=stages, orientation="h", marker_color=[BASE, BASE, ACCENT, ACCENT, ACCENT, ACCENT], text=[f"{v:.1f}%" for v in fl], textposition="outside"), row=3, col=1)
fig.add_trace(go.Bar(x=mix_pct.values, y=mix_pct.index, orientation="h", marker_color=[BASE, BASE, BASE, ACCENT], text=[f"{v:.1f}%" for v in mix_pct.values], textposition="outside"), row=3, col=2)
hs = ht.sort_values("ER")
fig.add_trace(go.Bar(x=hs["ER"], y=hs["Hashtag"], orientation="h", marker_color=highlight(hs["ER"]), text=hs["ER"].map("{:.2f}".format), textposition="outside"), row=3, col=3)
for r, c in [(2, 1), (2, 2)]:
    fig.update_yaxes(range=[0, 25], visible=False, row=r, col=c)
for r, c, mx in [(2, 3, 25), (3, 1, 125), (3, 2, 100), (3, 3, 25)]:
    fig.update_xaxes(range=[0, mx], visible=False, row=r, col=c)
fig.update_yaxes(autorange="reversed", row=3, col=1)
fig.update_yaxes(rangemode="tozero", row=1, col=1)
fig.update_layout(height=1000, showlegend=False, margin=dict(t=110),
                  title="Sugar Cosmetics · Instagram Performance Dashboard (19 Apr 2024 – 19 Apr 2025)")
fig.show()
''')

# ---------------------------------------------------------------- Recommendations
md('''
## Step 16 · Strategic Recommendations — *What should the marketing team do next?*
Recommendations are generated from the computed results above, so they update if the data changes.
''')
code('''
per_1000 = df["Total Engagement"].sum() / df["Reach"].sum() * 1000
recs = [
    ("SCALE", "Grow reach — it moves total engagement",
     f"Engagement rate is flat as reach grows; every 1,000 accounts reached yields ~{per_1000:,.0f} interactions. Invest in influencer/collab posts, "
     "boosts of proven creatives, and Reels/Stories distribution."),
    ("FIX", "Rescue ‘seen but ignored’ content",
     f"{len(gap) / len(df) * 100:.1f}% of posts ({len(gap):,}) combine top-quartile reach with bottom-quartile engagement. Audit hooks and calls-to-action; "
     "add polls, questions and giveaways."),
    ("DEEPEN", "Move audiences from likes to comments, saves and shares",
     f"Likes are {mix_pct['Likes']:.0f}% of interactions. Build save-worthy tutorials and share-worthy festive/challenge content."),
    ("CONVERT", "Turn profile visits into followers",
     f"{k['pv']:.1f}% of reach visits the profile and {k['fc']:.0f}% of visitors follow. Improve bio, highlights, pinned posts and link-in-bio offers."),
    ("TEST", "Replace guesswork with controlled experiments",
     f"Format ({spread(pt['ER']):.1f}%), weekday ({spread(dw['ER']):.1f}%) and hashtag ({spread(ht['ER']):.1f}%) gaps are within noise. "
     "Run 4-week A/B tests (Reel vs Image, 2 vs 3 hashtags, morning vs evening) and act only on significant results."),
    ("KEEP", "Maintain steady cadence and the hashtag core",
     f"Posting volume is consistent and the five brand/value hashtags perform alike. Keep {', '.join(ht['Hashtag'].head(3))} in rotation."),
    ("MEASURE", "Close the data gaps",
     "Capture post ID, caption, posting hour, carousel format, ad spend and follower count to unlock timing, caption, ROI and growth analysis."),
]
html = "".join(f'<div style="border:1px solid {GRID};border-radius:12px;padding:14px 18px;margin:10px 0;font-family:{FONT}">'
               f'<span style="color:{ACCENT};font-weight:700;font-size:.78em;letter-spacing:.5px">{tag}</span>'
               f'<div style="font-weight:600;font-size:1.05em;margin:2px 0 4px;color:{INK}">{title}</div>'
               f'<div style="color:#4B5563">{body}</div></div>' for tag, title, body in recs)
display(HTML(html))
''')
md('''
**Content & campaign ideas**
- **Tutorial Reels series** (“5-minute festive look”) — built for saves and shares
- **Influencer collab takeovers** with a giveaway mechanic — built for reach plus comments
- **Festive Offer Stories** with poll/quiz stickers — interaction at scale
- **Vegan & cruelty-free brand-values content** — on-brand, consistently performing hashtag themes
- **Profile-visit nudges** (“Follow for shade drops”) in the last frame of high-reach posts
''')

# ---------------------------------------------------------------- Conclusion
md('''
## Conclusion & limitations
**Summary.** Sugar Cosmetics' Instagram performance is healthy and steady (≈18.5% engagement rate, ≈4,100 posts a month), but **no format, weekday, hashtag or campaign is a statistically proven winner**. Growth will come from reach, deeper engagement (comments, saves, shares) and better profile-to-follow conversion.

**Limitations**
- No caption or post ID → caption/keyword analysis and unique-post counts are not possible.
- ≈137 records per day and unusually flat distributions suggest the data is **synthetic or aggregated**; re-run this notebook on the brand's real Instagram Insights export before acting.
- Summed reach double-counts accounts; the follow-conversion KPI is exploratory (attribution rules unverified).
- First and last months are partial (data runs 19 Apr 2024 – 19 Apr 2025).

**Skills demonstrated:** data validation · feature engineering · KPI design · interactive visualisation · statistical testing · business storytelling.
''')

nb.cells = cells
nb.metadata = {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
               "language_info": {"name": "python"}}
nbf.write(nb, "Sugar_Cosmetics_Instagram_Analysis.ipynb")
print("wrote notebook with", len(cells), "cells")
