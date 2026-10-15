"""
Sugar Cosmetics · Instagram Performance Analytics
=================================================
A recruiter- and business-friendly Streamlit dashboard that turns post-level Instagram
data into decisions: KPIs, trends, content/timing/hashtag performance, funnel & growth,
statistically-checked "levers", strategic recommendations and an optional AI analyst.

Run:   streamlit run app.py
Data:  data/sugar_cosmetics_instagram_data.csv  (or upload a CSV / XLSX in the sidebar)
"""
from __future__ import annotations

import itertools
import os
from io import BytesIO
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

try:  # scipy is optional - significance tests are skipped gracefully without it
    from scipy import stats
except ImportError:  # pragma: no cover
    stats = None

# ----------------------------------------------------------------------------
# 1. PAGE CONFIG & THEME
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="Sugar Cosmetics | Instagram Analytics",
    page_icon="💄",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _is_dark() -> bool:
    try:
        return st.context.theme.type == "dark"
    except Exception:  # older Streamlit / no theme info
        return False


DARK_MODE = _is_dark()
ACCENT = "#F06292" if DARK_MODE else "#C2185B"      # highlight (best / selected)
SOFT = "#F3A6C4"                                     # secondary highlight
BASE = "#5B6272" if DARK_MODE else "#B9BEC8"         # neutral bars
INK = "#F3F4F6" if DARK_MODE else "#1F2430"          # primary text
MUTED = "#9CA3AF" if DARK_MODE else "#6B7280"        # secondary text
GRID = "#2F3441" if DARK_MODE else "#E7E9EE"
CARD = "#1B1F2A" if DARK_MODE else "#FFFFFF"
TINT = "#2A1620" if DARK_MODE else "#FDF2F7"
NEUTRAL_BG = "#232734" if DARK_MODE else "#F5F6F8"
SEQ = ["#FBE4EE", "#F3A6C4", "#DE5F92", "#C2185B", "#7A0E39"]   # one-hue sequential scale
FONT = "Inter, Segoe UI, Helvetica, Arial, sans-serif"

DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
DATA_DIR = Path(__file__).parent / "data"
DATA_CANDIDATES = [DATA_DIR / "sugar_cosmetics_instagram_data.csv", DATA_DIR / "sugar_cosmetics_clean.csv"]

st.markdown(
    f"""
    <style>
      html, body, [class*="css"] {{ font-family: {FONT}; }}
      .block-container {{ padding-top: 1.4rem; max-width: 1400px; }}
      h2, h3 {{ letter-spacing: -0.3px; }}
      div[data-testid="stMetric"] {{
          background: {CARD}; border: 1px solid {GRID}; border-left: 5px solid {ACCENT};
          border-radius: 12px; padding: 12px 16px; box-shadow: 0 1px 2px rgba(16,24,40,.05);
      }}
      div[data-testid="stMetricLabel"] p {{
          color: {MUTED}; font-size: .76rem; text-transform: uppercase; letter-spacing: .04em;
      }}
      div[data-testid="stMetricValue"] {{ font-size: 1.55rem; }}
      .hero {{
          background: linear-gradient(90deg, #1F1F2E, #C2185B); color: #fff;
          padding: 22px 28px; border-radius: 16px; margin-bottom: 16px;
          display: flex; align-items: center; gap: 18px;
      }}
      .hero h1 {{ margin: 0; font-size: 1.85rem; color: #fff; letter-spacing: -0.5px; }}
      .hero p  {{ margin: 4px 0 0; opacity: .92; font-size: .92rem; }}
      .logo {{ flex: 0 0 58px; width: 58px; height: 58px; background: #fff; border-radius: 16px;
               display: flex; align-items: center; justify-content: center; }}
      .insight {{
          border-left: 4px solid {ACCENT}; background: {TINT}; padding: 10px 16px;
          border-radius: 6px; margin: 6px 0 14px 0; font-size: .95rem;
      }}
      .caveat {{
          border-left: 4px solid #9CA3AF; background: {NEUTRAL_BG}; padding: 10px 16px;
          border-radius: 6px; margin: 6px 0 14px 0; font-size: .88rem; color: {MUTED};
      }}
      .rec-card {{
          border: 1px solid {GRID}; border-radius: 12px; padding: 14px 18px;
          margin-bottom: 12px; background: {CARD};
      }}
      .rec-card h4 {{ margin: 2px 0 6px 0; font-size: 1.02rem; }}
      .rec-card span.body {{ color: {MUTED}; font-size: .93rem; }}
      .rec-tag {{ color: {ACCENT}; font-weight: 700; font-size: .75rem; letter-spacing: .08em; }}
    </style>
    """,
    unsafe_allow_html=True,
)

_chart_ids = itertools.count()  # unique chart keys; resets on every script run


# ----------------------------------------------------------------------------
# 2. HELPERS
# ----------------------------------------------------------------------------
def human(n: float) -> str:
    """12345678 -> 12.35M"""
    for div, suffix in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if abs(n) >= div:
            return f"{n / div:,.2f}{suffix}"
    return f"{n:,.0f}"


def style(fig: go.Figure, height: int = 380, legend: bool = False) -> go.Figure:
    """One consistent look for every chart."""
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=44, b=10),
        font=dict(family=FONT, size=13, color=INK),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=legend,
        legend_title_text="",
        title=dict(font=dict(size=15, color=INK), x=0, xanchor="left"),
        hoverlabel=dict(font_size=13),
    )
    fig.update_xaxes(showgrid=False, linecolor=GRID, ticks="", title_font=dict(color=MUTED))
    fig.update_yaxes(gridcolor=GRID, zeroline=False, ticks="", title_font=dict(color=MUTED))
    return fig


def plot(fig: go.Figure, height: int = 380, legend: bool = False) -> None:
    st.plotly_chart(style(fig, height, legend), width="stretch", key=f"chart_{next(_chart_ids)}")


def highlight_colors(values, best: str = "max") -> list[str]:
    """Neutral bars with the best one in the accent colour."""
    v = list(values)
    idx = int(np.argmax(v)) if best == "max" else int(np.argmin(v))
    return [ACCENT if i == idx else BASE for i in range(len(v))]


def insight(text: str) -> None:
    st.markdown(f'<div class="insight">💡 {text}</div>', unsafe_allow_html=True)


def caveat(text: str) -> None:
    st.markdown(f'<div class="caveat">ℹ️ {text}</div>', unsafe_allow_html=True)


def pct_spread(series: pd.Series) -> float:
    """Gap between best and worst group as % of the overall average."""
    return float((series.max() - series.min()) / series.mean() * 100)


def tags_of(s: str) -> list[str]:
    return [t.strip() for t in str(s).split(",") if t.strip()]


def secret(name: str, default=None):
    try:
        return st.secrets[name]
    except Exception:  # no secrets.toml or key missing
        return os.getenv(name, default)


# Free LLM providers - all expose an OpenAI-compatible chat endpoint, so one tiny helper covers them.
# Model names on free tiers change from time to time; override with the LLM_MODEL secret if needed.
PROVIDERS = {
    "groq": dict(key="GROQ_API_KEY", url="https://api.groq.com/openai/v1/chat/completions",
                 model="llama-3.3-70b-versatile"),
    "gemini": dict(key="GEMINI_API_KEY",
                   url="https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
                   model="gemini-2.5-flash"),
    "openrouter": dict(key="OPENROUTER_API_KEY", url="https://openrouter.ai/api/v1/chat/completions",
                       model="meta-llama/llama-3.3-70b-instruct:free"),
}


def llm_config():
    """Pick the provider from LLM_PROVIDER, or the first one that has an API key configured."""
    names = [secret("LLM_PROVIDER", "").lower()] if secret("LLM_PROVIDER") else list(PROVIDERS)
    for name in names:
        cfg = PROVIDERS.get(name)
        if cfg and secret(cfg["key"]):
            return name, cfg, secret(cfg["key"]), secret("LLM_MODEL", cfg["model"])
    return None


def ask_llm(question: str, context: str) -> str:
    import requests
    name, cfg, api_key, model = llm_config()
    resp = requests.post(
        cfg["url"], timeout=60,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": model, "max_tokens": 700, "temperature": 0.2,
              "messages": [
                  {"role": "system", "content": "You are a social-media analyst. Answer only from the aggregates "
                   "given; state clearly when differences are too small to be meaningful. Be concise."},
                  {"role": "user", "content": f"{context}\n\nQuestion: {question}"}]})
    if resp.status_code == 429:
        raise RuntimeError("Free-tier rate limit reached - wait a minute and try again.")
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def ci95(sd: pd.Series, n: pd.Series) -> pd.Series:
    return 1.96 * sd / np.sqrt(n)


# ----------------------------------------------------------------------------
# 3. DATA LOADING & CLEANING
# ----------------------------------------------------------------------------
REQUIRED = ["Post_Date", "Post_Type", "Campaign_Type", "Engagement_Source", "Audience_Emotion", "Hashtags",
            "Impressions", "Reach", "Likes", "Comments", "Shares", "Saves", "Profile_Visits", "Follows"]
NUMERIC = ["Impressions", "Reach", "Likes", "Comments", "Shares", "Saves", "Profile_Visits", "Follows"]
CATEGORICAL = ["Post_Type", "Campaign_Type", "Engagement_Source", "Audience_Emotion"]


@st.cache_data(show_spinner="Loading data…")
def load_data(path: str | None, upload: bytes | None, upload_name: str) -> pd.DataFrame:
    if upload is not None:
        buf = BytesIO(upload)
        df = pd.read_excel(buf) if upload_name.lower().endswith("xlsx") else pd.read_csv(buf)
    else:
        df = pd.read_csv(path)
    df.columns = [str(c).strip().replace(" ", "_") for c in df.columns]

    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(missing))

    df["Post_Date"] = pd.to_datetime(df["Post_Date"], errors="coerce")
    for c in NUMERIC:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.drop_duplicates().dropna(subset=["Post_Date", "Reach"])
    df = df[df["Reach"] > 0].reset_index(drop=True)
    df[[c for c in NUMERIC if c != "Reach"]] = df[[c for c in NUMERIC if c != "Reach"]].fillna(0)
    for c in CATEGORICAL:
        df[c] = df[c].fillna("Unknown").astype(str).str.strip()
    df["Hashtags"] = df["Hashtags"].fillna("").astype(str)

    df["Record_ID"] = df.index + 1
    df["Engagements"] = df[["Likes", "Comments", "Shares", "Saves"]].sum(axis=1)
    df["ER"] = df["Engagements"] / df["Reach"] * 100                                  # engagement rate %
    df["Reach_Rate"] = df["Reach"] / df["Impressions"].replace(0, np.nan) * 100
    df["Profile_Visit_Rate"] = df["Profile_Visits"] / df["Reach"] * 100
    df["Follow_Conv"] = df["Follows"] / df["Profile_Visits"].replace(0, np.nan) * 100
    df["Hashtag_Count"] = df["Hashtags"].map(lambda s: len(tags_of(s)))
    df["Month"] = df["Post_Date"].dt.to_period("M").dt.to_timestamp()
    df["Weekday"] = pd.Categorical(df["Post_Date"].dt.day_name(), DAY_ORDER, ordered=True)
    df["Label"] = ("#" + df["Record_ID"].astype(str) + " · " + df["Post_Date"].dt.strftime("%d %b %y")
                   + " · " + df["Post_Type"] + " · " + df["Campaign_Type"])
    return df


def hashtag_table(d: pd.DataFrame) -> pd.DataFrame:
    ex = d.assign(Hashtag=d["Hashtags"].map(tags_of)).explode("Hashtag").dropna(subset=["Hashtag"])
    g = ex.groupby("Hashtag").agg(Records=("Record_ID", "size"), Avg_ER=("ER", "mean"), SD=("ER", "std"),
                                  Avg_Reach=("Reach", "mean"), Avg_Likes=("Likes", "mean"))
    g["CI95"] = ci95(g["SD"].fillna(0), g["Records"])
    return g.reset_index().sort_values("Avg_ER", ascending=False)


# --- data source (sidebar) ---------------------------------------------------
with st.sidebar.expander("📁 Data source", expanded=False):
    uploaded = st.file_uploader("Upload your own data (CSV / XLSX)", type=["csv", "xlsx"])

default_path = next((p for p in DATA_CANDIDATES if p.exists()), None)
if uploaded is None and default_path is None:
    st.error("Dataset not found. Place the CSV in the `data/` folder or upload a file from the sidebar.")
    st.stop()
try:
    raw = load_data(None if uploaded else str(default_path),
                    uploaded.getvalue() if uploaded else None,
                    uploaded.name if uploaded else "")
except ValueError as err:
    st.error(str(err))
    st.stop()
if raw.empty:
    st.error("The dataset has no usable rows after cleaning.")
    st.stop()

# ----------------------------------------------------------------------------
# 4. SIDEBAR FILTERS (apply to every tab)
# ----------------------------------------------------------------------------
sig = f"{uploaded.name if uploaded else default_path.name}_{len(raw)}"
dmin, dmax = raw["Post_Date"].min().date(), raw["Post_Date"].max().date()
OPTS = {
    "type": sorted(raw["Post_Type"].unique()),
    "camp": sorted(raw["Campaign_Type"].unique()),
    "src": sorted(raw["Engagement_Source"].unique()),
    "emo": sorted(raw["Audience_Emotion"].unique()),
}
all_tags = sorted({t for s in raw["Hashtags"].unique() for t in tags_of(s)})
DEFAULTS = {f"dates_{sig}": (dmin, dmax), f"type_{sig}": OPTS["type"], f"camp_{sig}": OPTS["camp"],
            f"src_{sig}": OPTS["src"], f"emo_{sig}": OPTS["emo"], f"tags_{sig}": []}
for k, v in DEFAULTS.items():
    st.session_state.setdefault(k, v)


def reset_filters() -> None:
    for k, v in DEFAULTS.items():
        st.session_state[k] = v


st.sidebar.markdown("## 🎛️ Filters")
st.sidebar.button("↺ Reset all filters", on_click=reset_filters, width="stretch")
dates = st.sidebar.date_input("Date range", min_value=dmin, max_value=dmax, key=f"dates_{sig}")
f_type = st.sidebar.multiselect("Post type", OPTS["type"], key=f"type_{sig}")
f_camp = st.sidebar.multiselect("Campaign type", OPTS["camp"], key=f"camp_{sig}")
f_src = st.sidebar.multiselect("Engagement source", OPTS["src"], key=f"src_{sig}")
f_emo = st.sidebar.multiselect("Audience emotion", OPTS["emo"], key=f"emo_{sig}")
f_tags = st.sidebar.multiselect("Hashtag (posts containing any selected)", all_tags, key=f"tags_{sig}",
                                placeholder="All hashtags")

if not isinstance(dates, (tuple, list)) or len(dates) != 2:
    st.info("Select an end date to apply the date range.")
    st.stop()
start, end = dates


def apply_filters(d: pd.DataFrame, s, e) -> pd.DataFrame:
    m = ((d["Post_Date"] >= pd.Timestamp(s)) & (d["Post_Date"] < pd.Timestamp(e) + pd.Timedelta(days=1))
         & d["Post_Type"].isin(f_type) & d["Campaign_Type"].isin(f_camp)
         & d["Engagement_Source"].isin(f_src) & d["Audience_Emotion"].isin(f_emo))
    out = d[m]
    if f_tags:
        wanted = set(f_tags)
        out = out[out["Hashtags"].map(lambda s_: not wanted.isdisjoint(tags_of(s_)))]
    return out


df = apply_filters(raw, start, end)
span = (end - start).days + 1
prev_start = start - pd.Timedelta(days=span)
# previous period is only used when it is fully covered by the data (otherwise deltas would mislead)
prev = apply_filters(raw, prev_start, start - pd.Timedelta(days=1)) if prev_start >= dmin else raw.iloc[0:0]

st.sidebar.markdown("---")
st.sidebar.metric("Records in view", f"{len(df):,}", f"{len(df) / len(raw) * 100:.0f}% of dataset", delta_color="off")
st.sidebar.caption("Engagement = likes + comments + shares + saves  \nEngagement rate = engagement ÷ reach × 100")
if not df.empty:
    st.sidebar.download_button("⬇️ Download filtered data", df.to_csv(index=False).encode(),
                               "sugar_cosmetics_filtered.csv", "text/csv", width="stretch")


def delta_pct(cur: float, old: float):
    if prev.empty or not old:
        return None
    return f"{(cur / old - 1) * 100:+.1f}% vs prev. period"


def delta_pp(cur: float, old: float):
    if prev.empty or pd.isna(old):
        return None
    return f"{cur - old:+.2f} pp vs prev. period"


# ----------------------------------------------------------------------------
# 5. HEADER
# ----------------------------------------------------------------------------
INSTAGRAM_LOGO = """
<svg width="42" height="42" viewBox="0 0 48 48" role="img" aria-label="Instagram logo" xmlns="http://www.w3.org/2000/svg">
  <defs><linearGradient id="ig" x1="0%" y1="100%" x2="100%" y2="0%">
    <stop offset="0%" stop-color="#FFDC80"/><stop offset="35%" stop-color="#F77737"/>
    <stop offset="65%" stop-color="#E1306C"/><stop offset="100%" stop-color="#833AB4"/></linearGradient></defs>
  <rect x="4" y="4" width="40" height="40" rx="12" fill="url(#ig)"/>
  <rect x="12" y="12" width="24" height="24" rx="7" fill="none" stroke="#fff" stroke-width="3"/>
  <circle cx="24" cy="24" r="6" fill="none" stroke="#fff" stroke-width="3"/>
  <circle cx="32" cy="16" r="2" fill="#fff"/>
</svg>"""
st.markdown(
    f"""<div class="hero"><div class="logo">{INSTAGRAM_LOGO}</div><div>
    <h1>Sugar Cosmetics · Instagram Performance Analytics</h1>
    <p>{start:%d %b %Y} → {end:%d %b %Y} &nbsp;|&nbsp; {len(df):,} records &nbsp;|&nbsp;
    Engagement rate = (likes + comments + shares + saves) ÷ reach &nbsp;|&nbsp; every view responds to the sidebar filters</p>
    </div></div>""",
    unsafe_allow_html=True,
)

if df.empty:
    st.warning("No records match the current filters. Please widen your selection.")
    st.stop()

# ----------------------------------------------------------------------------
# 6. SHARED CALCULATIONS (computed once, reused by several tabs)
# ----------------------------------------------------------------------------
ht = hashtag_table(df)
avg_er = df["ER"].mean()
tot_reach, tot_imp = df["Reach"].sum(), df["Impressions"].sum()
tot_eng = df["Engagements"].sum()
pv_total, fl_total = df["Profile_Visits"].sum(), df["Follows"].sum()
pv_rate = pv_total / tot_reach * 100
follow_rate = fl_total / pv_total * 100 if pv_total else 0.0
q_reach, q_er = df["Reach"].quantile(0.75), df["ER"].quantile(0.25)
gap_mask = (df["Reach"] >= q_reach) & (df["ER"] <= q_er)
interactions_per_1k = tot_eng / tot_reach * 1000

LEVERS = [("Post_Type", "Post format"), ("Campaign_Type", "Campaign type"), ("Weekday", "Day of week"),
          ("Engagement_Source", "Engagement source"), ("Audience_Emotion", "Audience emotion"),
          ("Hashtag_Count", "Number of hashtags")]


def verdict(gap: float, significant: bool) -> str:
    if significant and gap >= 5:
        return "Meaningful"
    return "Significant, but small" if significant else "Within noise"


def lever_table(d: pd.DataFrame, hashtags: pd.DataFrame) -> pd.DataFrame:
    """For each strategy lever: best vs worst group, relative gap and a significance check."""
    rows, overall = [], d["ER"].mean()
    for col, label in LEVERS:
        g = d.groupby(col, observed=True)["ER"].agg(["mean", "count"])
        g = g[g["count"] >= 2]
        if len(g) < 2:
            continue
        groups = [x.values for _, x in d.groupby(col, observed=True)["ER"] if len(x) >= 2]
        p = float(stats.f_oneway(*groups).pvalue) if stats and len(groups) > 1 else np.nan
        gap = (g["mean"].max() - g["mean"].min()) / overall * 100
        suffix = " hashtag(s)" if col == "Hashtag_Count" else ""
        rows.append(dict(Lever=label, Best=f"{g['mean'].idxmax()}{suffix}", Best_ER=g["mean"].max(),
                         Worst=f"{g['mean'].idxmin()}{suffix}", Worst_ER=g["mean"].min(), Gap=gap, P=p,
                         Verdict=verdict(gap, (not np.isnan(p)) and p < 0.05)))
    if len(hashtags) > 1:  # hashtags overlap between records, so compare confidence intervals instead of ANOVA
        b, w = hashtags.iloc[0], hashtags.iloc[-1]
        gap = (b["Avg_ER"] - w["Avg_ER"]) / overall * 100
        rows.append(dict(Lever="Hashtag", Best=b["Hashtag"], Best_ER=b["Avg_ER"], Worst=w["Hashtag"],
                         Worst_ER=w["Avg_ER"], Gap=gap, P=np.nan,
                         Verdict=verdict(gap, (b["Avg_ER"] - b["CI95"]) > (w["Avg_ER"] + w["CI95"]))))
    return pd.DataFrame(rows)


levers = lever_table(df, ht)
meaningful = levers[levers["Verdict"] == "Meaningful"] if not levers.empty else levers


def partial_months(s, e) -> dict:
    s, e, out = pd.Timestamp(s), pd.Timestamp(e), {}
    if s.day > 1:
        out[s.to_period("M").to_timestamp()] = f"partial month (starts {s:%d %b})"
    if not e.is_month_end:
        key = e.to_period("M").to_timestamp()
        out[key] = out.get(key, "partial month") if key in out else f"partial month (ends {e:%d %b})"
    return out


PARTIAL = partial_months(start, end)


def lift_chart(frame: pd.DataFrame, col: str, title: str) -> go.Figure:
    g = frame.groupby(col, observed=True)["ER"].mean()
    lift = ((g / frame["ER"].mean() - 1) * 100).reset_index(name="Lift")
    lift[col] = lift[col].astype(str)
    fig = go.Figure(go.Bar(x=lift[col], y=lift["Lift"], marker_color=[ACCENT if v >= 0 else BASE for v in lift["Lift"]],
                           text=lift["Lift"].map("{:+.2f}%".format), textposition="outside", cliponaxis=False,
                           hovertemplate="%{x}<br>%{y:+.2f}% vs average<extra></extra>"))
    fig.update_layout(title=title, yaxis_title="Engagement-rate lift vs overall average (%)")
    return fig


# ----------------------------------------------------------------------------
# 7. TABS
# ----------------------------------------------------------------------------
tabs = st.tabs(["📊 Executive Summary", "📈 Trends", "🎬 Content", "🕒 Timing", "🔻 Funnel & Growth",
                "#️⃣ Hashtags", "👥 Audience", "🏆 Top Posts", "🧭 Explorer", "🎯 Strategy & AI"])

# ----------------------------- Executive summary ------------------------------
with tabs[0]:
    st.subheader("How is the account performing overall?")
    c = st.columns(5)
    c[0].metric("Total posts", f"{len(df):,}", delta_pct(len(df), len(prev)))
    c[1].metric("Total likes", human(df["Likes"].sum()), delta_pct(df["Likes"].sum(), prev["Likes"].sum()))
    c[2].metric("Total comments", human(df["Comments"].sum()), delta_pct(df["Comments"].sum(), prev["Comments"].sum()))
    c[3].metric("Total reach", human(tot_reach), delta_pct(tot_reach, prev["Reach"].sum()))
    c[4].metric("Avg engagement rate", f"{avg_er:.2f}%",
                delta_pp(avg_er, prev["ER"].mean() if not prev.empty else np.nan))
    c = st.columns(5)
    c[0].metric("Impressions", human(tot_imp), help="Total views, including repeat views by the same account")
    c[1].metric("Total engagement", human(tot_eng))
    c[2].metric("Shares + saves", human(df["Shares"].sum() + df["Saves"].sum()),
                help="Deeper-intent signals than likes")
    c[3].metric("New follows", human(fl_total))
    c[4].metric("Profile visit → follow", f"{follow_rate:.1f}%", help="Follows ÷ profile visits")
    if prev.empty:
        st.caption("Period-over-period deltas appear when the selected range has an equally long, fully "
                   "covered period before it (e.g. select the most recent months).")
    else:
        st.caption(f"Deltas compare with the previous equal-length period "
                   f"({prev_start:%d %b %Y} → {(start - pd.Timedelta(days=1)):%d %b %Y}).")

    # Auto-generated takeaways
    like_share = df["Likes"].sum() / tot_eng * 100
    if len(meaningful):
        top = meaningful.sort_values("Gap", ascending=False).iloc[0]
        lever_msg = (f"<b>{top['Lever']}</b> shows the clearest difference: <b>{top['Best']}</b> "
                     f"({top['Best_ER']:.2f}%) vs {top['Worst']} ({top['Worst_ER']:.2f}%) - a {top['Gap']:.1f}% gap.")
    elif not levers.empty:
        mx = levers.sort_values("Gap", ascending=False).iloc[0]
        lever_msg = (f"No format, day, campaign, source, emotion or hashtag is a clear winner - the largest gap is "
                     f"only {mx['Gap']:.1f}% ({mx['Lever']}). Reach, not tactics, drives total engagement.")
    else:
        lever_msg = "Not enough groups in the current selection to compare strategy levers."
    st.markdown("##### Key takeaways")
    insight(lever_msg)
    insight(f"Likes make up <b>{like_share:.0f}%</b> of interactions; every 1,000 accounts reached generate "
            f"~<b>{interactions_per_1k:,.0f}</b> interactions. Comments, saves and shares - the deeper signals - "
            "are the main quality lever.")
    insight(f"<b>{pv_rate:.1f}%</b> of reach visits the profile and <b>{follow_rate:.1f}%</b> of visitors follow; "
            f"<b>{gap_mask.mean() * 100:.1f}%</b> of records were widely seen but under-engaged (top-25% reach, bottom-25% engagement).")

    left, right = st.columns([3, 2])
    with left:
        m = df.groupby("Month").agg(Reach=("Reach", "sum"), Engagements=("Engagements", "sum")).reset_index()
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_bar(x=m["Month"], y=m["Reach"], name="Reach", marker_color=SOFT, secondary_y=False,
                    hovertemplate="%{x|%b %Y}<br>Reach: %{y:,.0f}<extra></extra>")
        fig.add_scatter(x=m["Month"], y=m["Engagements"], name="Engagements", mode="lines+markers",
                        line=dict(color=ACCENT, width=3), secondary_y=True,
                        hovertemplate="%{x|%b %Y}<br>Engagements: %{y:,.0f}<extra></extra>")
        fig.update_layout(title="Reach vs engagements by month")
        fig.update_xaxes(tickformat="%b %y")
        fig.update_yaxes(showgrid=False, secondary_y=True)
        plot(fig, 360, legend=True)
    with right:
        parts = pd.DataFrame({"Interaction": ["Likes", "Comments", "Saves", "Shares"],
                              "Count": [df["Likes"].sum(), df["Comments"].sum(), df["Saves"].sum(), df["Shares"].sum()]})
        parts["Share"] = parts["Count"] / tot_eng * 100
        parts = parts.sort_values("Share")
        fig = go.Figure(go.Bar(x=parts["Share"], y=parts["Interaction"], orientation="h",
                               marker_color=highlight_colors(parts["Share"]),
                               text=parts["Share"].map("{:.1f}%".format), textposition="outside", cliponaxis=False,
                               hovertemplate="%{y}: %{x:.1f}% of interactions<extra></extra>"))
        fig.update_layout(title="What makes up engagement?")
        fig.update_xaxes(visible=False, range=[0, 115])
        plot(fig, 360)
    if PARTIAL:
        caveat("Partial months in this selection: " + "; ".join(f"{k:%b %Y} is a {v}" for k, v in PARTIAL.items())
               + ". Monthly totals for those months are lower for that reason only.")
    with st.expander("Definitions & data notes"):
        days = max((df["Post_Date"].max() - df["Post_Date"].min()).days + 1, 1)
        st.markdown(
            f"- **Engagement rate** = (likes + comments + shares + saves) ÷ reach × 100, averaged across records.\n"
            f"- **Records** are rows in the file - about **{len(df) / days:,.0f} per calendar day** here, so each row "
            "may be an aggregated record rather than one literal Instagram post.\n"
            "- **Total reach** sums post-level reach; it is not the count of unique people.\n"
            "- Rows with missing dates/reach, zero reach, or exact duplicates are removed on load.\n"
            "- **Gap** = (best group − worst group) ÷ average. Gaps under 5% or without statistical support are "
            "treated as noise."
        )

# ----------------------------------- Trends -----------------------------------
with tabs[1]:
    st.subheader("How consistent is publishing, and how is engagement moving?")
    mo = df.groupby("Month").agg(Posts=("Record_ID", "size"), ER=("ER", "mean"), Follows=("Follows", "sum")).reset_index()
    mo["Note"] = mo["Month"].map(lambda k: PARTIAL.get(k, "full month"))
    c1, c2 = st.columns(2)
    with c1:
        fig = go.Figure(go.Bar(x=mo["Month"], y=mo["Posts"], customdata=mo["Note"],
                               marker_color=[SOFT if k in PARTIAL else ACCENT for k in mo["Month"]],
                               hovertemplate="%{x|%b %Y}<br>Posts: %{y:,}<br>%{customdata}<extra></extra>"))
        fig.update_layout(title="Posts per month (lighter bars = partial months)")
        fig.update_xaxes(tickformat="%b %y")
        plot(fig, 360)
    with c2:
        fig = go.Figure()
        fig.add_scatter(x=mo["Month"], y=mo["ER"], mode="lines+markers", line=dict(color=ACCENT, width=2.5),
                        marker=dict(size=8), name="Avg ER",
                        hovertemplate="%{x|%b %Y}<br>Engagement rate: %{y:.2f}%<extra></extra>")
        fig.add_hline(y=avg_er, line_dash="dot", line_color=MUTED, annotation_text=f"Period avg {avg_er:.2f}%",
                      annotation_font_color=MUTED)
        fig.update_layout(title="Average engagement rate by month (%)")
        fig.update_yaxes(range=[0, max(mo["ER"].max() * 1.2, avg_er * 1.2)], title="Engagement rate (%)")
        fig.update_xaxes(tickformat="%b %y")
        plot(fig, 360)
    full = mo[~mo["Month"].isin(PARTIAL)]
    if len(full) > 1:
        cv = full["Posts"].std() / full["Posts"].mean() * 100
        insight(f"Across full months the team publishes ~{full['Posts'].mean():,.0f} posts a month (variation ±{cv:.0f}%). "
                f"Busiest month: {mo.loc[mo['Posts'].idxmax(), 'Month']:%b %Y}; quietest full month: "
                f"{full.loc[full['Posts'].idxmin(), 'Month']:%b %Y}.")
    mode = st.radio("Content mix over time", ["Share of posts (%)", "Number of posts"], horizontal=True)
    t = df.groupby(["Month", "Post_Type"]).size().reset_index(name="Posts")
    fig = px.area(t, x="Month", y="Posts", color="Post_Type", color_discrete_sequence=[ACCENT, SOFT, BASE, "#7A0E39", "#DE5F92"],
                  groupnorm="percent" if mode.startswith("Share") else None, title="Content mix over time")
    fig.update_xaxes(tickformat="%b %y", title=None)
    fig.update_yaxes(title="% of posts" if mode.startswith("Share") else "Posts")
    plot(fig, 380, legend=True)

# ----------------------------------- Content ----------------------------------
with tabs[2]:
    st.subheader("Which formats and campaigns perform best?")
    pt = df.groupby("Post_Type").agg(Posts=("Record_ID", "size"), Likes=("Likes", "mean"), Comments=("Comments", "mean"),
                                     Saves=("Saves", "mean"), Shares=("Shares", "mean"), ER=("ER", "mean")
                                     ).reset_index().sort_values("ER", ascending=False)
    fig = make_subplots(rows=1, cols=4, horizontal_spacing=0.06,
                        subplot_titles=["Avg likes", "Avg comments", "Avg saves", "Avg engagement rate (%)"])
    for i, (col, f) in enumerate([("Likes", "{:,.0f}"), ("Comments", "{:,.0f}"), ("Saves", "{:,.0f}"), ("ER", "{:.2f}")], 1):
        fig.add_trace(go.Bar(x=pt["Post_Type"], y=pt[col], marker_color=highlight_colors(pt[col]),
                             text=pt[col].map(f.format), textposition="outside", cliponaxis=False,
                             hovertemplate="%{x}<br>%{y:,.2f}<extra></extra>"), row=1, col=i)
        fig.update_yaxes(range=[0, pt[col].max() * 1.22], visible=False, row=1, col=i)
    fig.update_annotations(font=dict(size=13, color=MUTED))
    plot(fig, 360)
    row = levers[levers["Lever"] == "Post format"]
    if len(row):
        r = row.iloc[0]
        stat = "" if np.isnan(r["P"]) else f" (ANOVA p = {r['P']:.3f})"
        insight(f"<b>{r['Best']}</b> has the highest engagement rate ({r['Best_ER']:.2f}%), the best-to-worst format gap is "
                f"{r['Gap']:.1f}%{stat}. Verdict: <b>{r['Verdict'].lower()}</b>.")
    c1, c2 = st.columns(2)
    with c1:
        plot(lift_chart(df, "Post_Type", "Engagement-rate lift by post type"), 360)
    with c2:
        plot(lift_chart(df, "Campaign_Type", "Engagement-rate lift by campaign type"), 360)
    h = df.pivot_table(index="Campaign_Type", columns="Post_Type", values="ER", aggfunc="mean")
    fig = px.imshow(h, text_auto=".2f", aspect="auto", color_continuous_scale=SEQ[:4],
                    title="Avg engagement rate (%) · campaign × post type")
    fig.update_coloraxes(showscale=False)
    fig.update_xaxes(title=None)
    fig.update_yaxes(title=None)
    plot(fig, 360)
    with st.expander("View table"):
        st.dataframe(pt.round(2), hide_index=True, width="stretch")

# ----------------------------------- Timing -----------------------------------
with tabs[3]:
    st.subheader("Does the day of the week matter?")
    dw = df.groupby("Weekday", observed=True).agg(ER=("ER", "mean"), SD=("ER", "std"), Posts=("Record_ID", "size"),
                                                  Likes=("Likes", "mean")).reset_index()
    dw["CI"] = ci95(dw["SD"].fillna(0), dw["Posts"])
    c1, c2 = st.columns([3, 2])
    with c1:
        fig = go.Figure(go.Bar(
            x=dw["Weekday"].astype(str), y=dw["ER"], marker_color=highlight_colors(dw["ER"]),
            error_y=dict(type="data", array=dw["CI"], color=MUTED, thickness=1.2, width=4),
            text=dw["ER"].map("{:.2f}%".format), textposition="inside", insidetextanchor="end", textfont=dict(color="white"),
            customdata=np.c_[dw["Posts"], dw["Likes"], dw["CI"]],
            hovertemplate="%{x}<br>Avg engagement rate: %{y:.2f}% (±%{customdata[2]:.2f})"
                          "<br>Posts: %{customdata[0]:,}<br>Avg likes: %{customdata[1]:,.0f}<extra></extra>"))
        fig.update_layout(title="Average engagement rate by weekday (whiskers = 95% confidence interval)")
        fig.update_yaxes(range=[0, dw["ER"].max() * 1.25], title="Engagement rate (%)")
        plot(fig, 380)
    with c2:
        fig = go.Figure(go.Bar(x=dw["Weekday"].astype(str), y=dw["Posts"], marker_color=BASE,
                               hovertemplate="%{x}<br>Posts: %{y:,}<extra></extra>"))
        fig.update_layout(title="Posting volume by weekday")
        fig.update_yaxes(title="Posts")
        plot(fig, 380)
    b, w = dw.loc[dw["ER"].idxmax()], dw.loc[dw["ER"].idxmin()]
    overlap = (b["ER"] - b["CI"]) <= (w["ER"] + w["CI"])
    insight(f"<b>{b['Weekday']}</b> is the strongest day ({b['ER']:.2f}%) and <b>{w['Weekday']}</b> the weakest "
            f"({w['ER']:.2f}%) - a gap of {b['ER'] - w['ER']:.2f} points. "
            + ("The confidence whiskers overlap, so there is no proven 'best day to post'; keep a consistent schedule "
               "and test timing once hour-of-day data is captured." if overlap else
               "The confidence ranges do not overlap, so the weekday effect is statistically supported."))
    h = df.pivot_table(index="Weekday", columns="Post_Type", values="ER", aggfunc="mean", observed=True)
    fig = px.imshow(h, text_auto=".2f", aspect="auto", color_continuous_scale=SEQ[:4],
                    title="Avg engagement rate (%) · weekday × post type")
    fig.update_coloraxes(showscale=False)
    fig.update_xaxes(title=None)
    fig.update_yaxes(title=None, autorange="reversed")
    plot(fig, 400)

# ------------------------------- Funnel & growth ------------------------------
with tabs[4]:
    st.subheader("Are people seeing posts but not interacting - and do they follow?")
    stages = ["Impressions", "Reach", "Likes", "Comments", "Shares", "Saves"]
    vals = [df[s].sum() for s in stages]
    c1, c2 = st.columns([3, 2])
    with c1:
        fig = go.Figure(go.Funnel(
            y=stages, x=vals, textinfo="text", text=[f"{human(v)} · {v / vals[0] * 100:.1f}%" for v in vals],
            marker=dict(color=[SEQ[1], SEQ[1], SEQ[2], SEQ[3], SEQ[3], SEQ[3]]), connector=dict(line=dict(color=GRID)),
            hovertemplate="%{y}: %{x:,.0f}<br>%{percentInitial:.2%} of impressions<extra></extra>"))
        fig.update_layout(title="Engagement funnel (totals · % of impressions)")
        plot(fig, 420)
    with c2:
        st.markdown("**Audience-growth indicators**")
        st.metric("Profile visits", human(pv_total), f"{pv_rate:.1f}% of reach", delta_color="off")
        st.metric("New follows", human(fl_total), f"{follow_rate:.1f}% of profile visits", delta_color="off")
        st.metric("Reach ÷ impressions", f"{tot_reach / tot_imp * 100:.1f}%" if tot_imp else "n/a",
                  help="Share of impressions that are unique accounts - the rest are repeat views")
    insight(f"Of every 100 impressions, {vals[1] / vals[0] * 100:.0f} are unique accounts and ~{vals[2] / vals[0] * 100:.0f} become "
            f"likes; comments, shares and saves are each at most {max(vals[3:]) / vals[0] * 100:.1f}%. The biggest drop-off is from "
            "'seeing' to the <i>deeper</i> actions.")
    caveat("The funnel is indicative: likes, comments, shares and saves are counted per interaction, not per person.")

    st.markdown("#### Reach without interaction")
    d = df.sample(min(4000, len(df)), random_state=7).copy()
    d["Segment"] = np.where((d["Reach"] >= q_reach) & (d["ER"] <= q_er), "High reach, low engagement", "Other records")
    fig = px.scatter(d, x="Reach", y="ER", color="Segment", opacity=0.55, render_mode="svg",  # svg: no WebGL needed
                     color_discrete_map={"High reach, low engagement": ACCENT, "Other records": BASE},
                     labels={"ER": "Engagement rate (%)"}, hover_data={"Post_Type": True, "Campaign_Type": True},
                     title=f"Reach vs engagement rate (sample of {len(d):,} records)")
    fig.update_traces(marker=dict(size=6))
    fig.add_vline(x=q_reach, line_dash="dot", line_color=MUTED)
    fig.add_hline(y=q_er, line_dash="dot", line_color=MUTED)
    c1, c2 = st.columns([3, 2])
    with c1:
        plot(fig, 400, legend=True)
    with c2:
        st.metric("Top-25% reach but bottom-25% engagement", f"{int(gap_mask.sum()):,}",
                  f"{gap_mask.mean() * 100:.1f}% of records", delta_color="off")
        if gap_mask.any():
            st.markdown("**Which formats they come from**")
            share = df.loc[gap_mask, "Post_Type"].value_counts(normalize=True).mul(100).round(0).astype(int)
            st.dataframe(share.astype(str).add("%").rename("Share").to_frame(), width="stretch")
    insight("Engagement rate is almost flat across reach levels - more reach brings proportionally more interactions, not better "
            "ones. The high-reach / low-engagement group is the clearest optimisation target.")

# ----------------------------------- Hashtags ---------------------------------
with tabs[5]:
    st.subheader("Which hashtags are linked to stronger performance?")
    c1, c2 = st.columns(2)
    with c1:
        s = ht.sort_values("Avg_ER")
        fig = go.Figure(go.Bar(
            x=s["Avg_ER"], y=s["Hashtag"], orientation="h", marker_color=highlight_colors(s["Avg_ER"]),
            error_x=dict(type="data", array=s["CI95"], color=MUTED, thickness=1.2, width=4),
            text=s["Avg_ER"].map("{:.2f}%".format), textposition="inside", insidetextanchor="end", textfont=dict(color="white"),
            customdata=s["Records"], hovertemplate="%{y}<br>Avg engagement rate: %{x:.2f}%<br>Records: %{customdata:,}<extra></extra>"))
        fig.update_layout(title="Avg engagement rate by hashtag (whiskers = 95% CI)")
        fig.update_xaxes(range=[0, s["Avg_ER"].max() * 1.2], visible=False)
        plot(fig, max(340, 28 * len(s) + 120))
    with c2:
        s = ht.sort_values("Records")
        fig = go.Figure(go.Bar(x=s["Records"], y=s["Hashtag"], orientation="h", marker_color=BASE,
                               text=s["Records"].map("{:,.0f}".format), textposition="outside", cliponaxis=False,
                               hovertemplate="%{y}<br>Used in %{x:,} records<extra></extra>"))
        fig.update_layout(title="Usage: records containing each hashtag")
        fig.update_xaxes(range=[0, s["Records"].max() * 1.2], visible=False)
        plot(fig, max(340, 28 * len(s) + 120))
    best_h = ht.iloc[0]
    insight(f"<b>{best_h['Hashtag']}</b> leads with {best_h['Avg_ER']:.2f}%, and all hashtags sit within "
            f"{ht['Avg_ER'].max() - ht['Avg_ER'].min():.2f} points of each other. "
            + ("Their confidence ranges overlap - no hashtag is a proven winner; keep the brand tags and A/B test one change at a time."
               if (levers[levers['Lever'] == 'Hashtag']['Verdict'] != 'Meaningful').all() else
               "The best-vs-worst gap is statistically supported and large enough to act on."))

    c1, c2 = st.columns(2)
    with c1:
        hc = df.groupby("Hashtag_Count").agg(ER=("ER", "mean"), Records=("Record_ID", "size")).reset_index()
        fig = go.Figure(go.Bar(x=hc["Hashtag_Count"].astype(str) + " hashtag(s)", y=hc["ER"],
                               marker_color=highlight_colors(hc["ER"]), text=hc["ER"].map("{:.2f}%".format),
                               textposition="outside", cliponaxis=False, customdata=hc["Records"],
                               hovertemplate="%{x}<br>Avg ER: %{y:.2f}%<br>Records: %{customdata:,}<extra></extra>"))
        fig.update_layout(title="Does the number of hashtags matter?")
        fig.update_yaxes(range=[0, hc["ER"].max() * 1.25], visible=False)
        plot(fig, 380)
    with c2:
        min_n = st.slider("Minimum records per hashtag combination", 10, 500, 100, step=10)
        combo = (df.groupby("Hashtags").agg(Records=("Record_ID", "size"), Avg_ER=("ER", "mean"), Avg_Reach=("Reach", "mean"))
                 .query("Records >= @min_n").sort_values("Avg_ER", ascending=False).head(10).reset_index())
        if combo.empty:
            st.info("No hashtag combination meets that minimum - lower the threshold.")
        else:
            fig = px.bar(combo, x="Avg_ER", y="Hashtags", orientation="h", color="Avg_Reach",
                         color_continuous_scale=SEQ[:4], title="Top hashtag combinations by engagement rate",
                         labels={"Avg_ER": "Avg engagement rate (%)", "Avg_Reach": "Avg reach"})
            fig.update_yaxes(autorange="reversed", title=None)
            plot(fig, 330)

# ----------------------------------- Audience ---------------------------------
with tabs[6]:
    st.subheader("Who engages, where do they come from, and do they follow?")
    c1, c2 = st.columns(2)
    with c1:
        e = df.groupby("Audience_Emotion").agg(ER=("ER", "mean"), SD=("ER", "std"), N=("Record_ID", "size")).reset_index()
        e["CI"] = ci95(e["SD"].fillna(0), e["N"])
        e = e.sort_values("ER")
        fig = go.Figure(go.Bar(x=e["ER"], y=e["Audience_Emotion"], orientation="h", marker_color=highlight_colors(e["ER"]),
                               error_x=dict(type="data", array=e["CI"], color=MUTED, thickness=1.2, width=4),
                               text=e["ER"].map("{:.2f}%".format), textposition="inside", insidetextanchor="end",
                               textfont=dict(color="white"), customdata=e["N"],
                               hovertemplate="%{y}<br>Avg ER: %{x:.2f}%<br>Records: %{customdata:,}<extra></extra>"))
        fig.update_layout(title="Engagement rate by audience emotion (95% CI)")
        fig.update_xaxes(range=[0, e["ER"].max() * 1.2], visible=False)
        plot(fig, 380)
    with c2:
        sr = df.groupby("Engagement_Source").agg(Reach=("Reach", "mean"), ER=("ER", "mean"), Follows=("Follows", "mean"),
                                                 N=("Record_ID", "size")).reset_index()
        fig = px.scatter(sr, x="Reach", y="ER", size="Follows", color="Engagement_Source", text="Engagement_Source", render_mode="svg",
                         color_discrete_sequence=[ACCENT, SOFT, BASE, "#7A0E39", "#DE5F92", "#9CA3AF"],
                         labels={"ER": "Avg engagement rate (%)", "Reach": "Avg reach"}, size_max=45,
                         title="Source quality: reach vs engagement (bubble = avg follows)")
        fig.update_traces(textposition="top center")
        plot(fig, 380)
    c1, c2 = st.columns(2)
    with c1:
        g = df.groupby("Month").agg(Follows=("Follows", "sum")).reset_index()
        g["Cumulative"] = g["Follows"].cumsum()
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_bar(x=g["Month"], y=g["Follows"], name="New follows", marker_color=SOFT, secondary_y=False,
                    hovertemplate="%{x|%b %Y}<br>New follows: %{y:,.0f}<extra></extra>")
        fig.add_scatter(x=g["Month"], y=g["Cumulative"], name="Cumulative", mode="lines+markers",
                        line=dict(color=ACCENT, width=3), secondary_y=True,
                        hovertemplate="%{x|%b %Y}<br>Cumulative: %{y:,.0f}<extra></extra>")
        fig.update_layout(title="Follower growth (follows attributed to posts)")
        fig.update_xaxes(tickformat="%b %y")
        fig.update_yaxes(showgrid=False, secondary_y=True)
        plot(fig, 380, legend=True)
    with c2:
        fc = df.groupby("Campaign_Type")["Follow_Conv"].mean().reset_index().sort_values("Follow_Conv")
        fig = go.Figure(go.Bar(x=fc["Follow_Conv"], y=fc["Campaign_Type"], orientation="h",
                               marker_color=highlight_colors(fc["Follow_Conv"]), text=fc["Follow_Conv"].map("{:.1f}%".format),
                               textposition="outside", cliponaxis=False,
                               hovertemplate="%{y}<br>Follow conversion: %{x:.1f}%<extra></extra>"))
        fig.update_layout(title="Profile-visit → follow conversion by campaign (%)")
        fig.update_xaxes(visible=False, range=[0, fc["Follow_Conv"].max() * 1.2])
        plot(fig, 380)
    top_e = df.groupby("Audience_Emotion")["ER"].mean().sort_values(ascending=False)
    insight(f"<b>{top_e.index[0]}</b> content earns the highest engagement rate ({top_e.iloc[0]:.2f}%), versus "
            f"{top_e.index[-1]} ({top_e.iloc[-1]:.2f}%). Check the whiskers before acting - overlapping ranges mean the "
            "difference is not reliable.")

# ----------------------------------- Top posts --------------------------------
with tabs[7]:
    st.subheader("Which records stand out?")
    c1, c2, c3 = st.columns(3)
    rank_by = c1.selectbox("Rank by", ["Likes", "ER", "Reach", "Comments", "Shares", "Saves", "Follows"],
                           format_func=lambda x: "Engagement rate (%)" if x == "ER" else x)
    top_n = c2.slider("Show top", 5, 25, 10)
    min_reach = c3.number_input("Minimum reach", 0, int(df["Reach"].max()), 0, step=100,
                                help="Filter out tiny-reach records, which can show inflated engagement rates")
    pool = df[df["Reach"] >= min_reach]
    if pool.empty:
        st.info("No records meet the minimum reach.")
    else:
        top = pool.nlargest(top_n, rank_by).iloc[::-1]
        nice = "Engagement rate (%)" if rank_by == "ER" else rank_by
        fig = go.Figure(go.Bar(
            x=top[rank_by], y=top["Label"], orientation="h", marker_color=ACCENT,
            text=top[rank_by].map("{:.1f}%".format if rank_by == "ER" else "{:,.0f}".format),
            textposition="outside", cliponaxis=False,
            customdata=np.c_[top["Hashtags"], top["Audience_Emotion"], top["Engagement_Source"], top["Reach"],
                             top["Likes"], top["ER"]],
            hovertemplate="<b>%{y}</b><br>Hashtags: %{customdata[0]}<br>Emotion: %{customdata[1]} · Source: %{customdata[2]}"
                          "<br>Reach: %{customdata[3]:,} · Likes: %{customdata[4]:,}"
                          "<br>Engagement rate: %{customdata[5]:.1f}%<extra></extra>"))
        fig.update_layout(title=f"Top {top_n} records by {nice.lower()}")
        fig.update_xaxes(visible=False, range=[0, top[rank_by].max() * 1.18])
        fig.update_yaxes(title=None)
        plot(fig, max(380, 38 * top_n + 90))
        if rank_by == "ER":
            insight(f"The best engagement rates reach {top['ER'].max():.1f}% vs a {avg_er:.1f}% average, typically at a reach of "
                    f"~{top['Reach'].median():,.0f} - high engagement does not require huge reach.")
        else:
            corr = df[[rank_by, "Reach"]].corr().iloc[0, 1]
            insight(f"Top records average a reach of {top['Reach'].mean():,.0f} vs {df['Reach'].mean():,.0f} overall; correlation between "
                    f"{rank_by.lower()} and reach is {corr:.2f}, so 'most {rank_by.lower()}' largely means 'most seen'.")
        st.dataframe(
            top.iloc[::-1][["Label", "Hashtags", "Likes", "Comments", "Shares", "Saves", "Reach", "ER"]],
            hide_index=True, width="stretch",
            column_config={"ER": st.column_config.NumberColumn("Eng. rate (%)", format="%.2f"),
                           "Likes": st.column_config.NumberColumn(format="%d"),
                           "Reach": st.column_config.NumberColumn(format="%d")})
        caveat("The dataset has no caption or post-ID column, so records are labelled by ID · date · format · campaign.")

# ----------------------------------- Explorer ---------------------------------
with tabs[8]:
    st.subheader("Build your own view")
    METRICS = {
        "Avg engagement rate (%)": ("ER", "mean", "{:.2f}"),
        "Avg likes": ("Likes", "mean", "{:,.0f}"),
        "Avg reach": ("Reach", "mean", "{:,.0f}"),
        "Avg saves": ("Saves", "mean", "{:,.0f}"),
        "Avg shares": ("Shares", "mean", "{:,.0f}"),
        "Avg follow conversion (%)": ("Follow_Conv", "mean", "{:.1f}"),
        "Total engagement": ("Engagements", "sum", "{:,.0f}"),
        "Number of posts": ("Record_ID", "count", "{:,.0f}"),
    }
    DIMS = {"Post type": "Post_Type", "Campaign type": "Campaign_Type", "Engagement source": "Engagement_Source",
            "Audience emotion": "Audience_Emotion", "Day of week": "Weekday"}
    c1, c2, c3 = st.columns(3)
    metric_name = c1.selectbox("Metric", list(METRICS))
    dim_label = c2.selectbox("Compare by", list(DIMS))
    dim = DIMS[dim_label]
    members = sorted(df[dim].astype(str).unique(), key=lambda x: DAY_ORDER.index(x) if dim == "Weekday" else x)
    focus = c3.selectbox("Trend for", ["All (filtered)"] + members)
    col, agg, f = METRICS[metric_name]

    k = st.columns(4)
    k[0].metric("Records", f"{len(df):,}")
    k[1].metric("Avg engagement rate", f"{avg_er:.2f}%")
    k[2].metric("Total engagement", human(tot_eng))
    k[3].metric("Total reach", human(tot_reach))

    a, b = st.columns(2)
    with a:
        g = df.groupby(dim, observed=True)[col].agg(agg).reset_index()
        g = g.sort_values(dim) if dim == "Weekday" else g.sort_values(col, ascending=False)
        fig = go.Figure(go.Bar(x=g[dim].astype(str), y=g[col], marker_color=highlight_colors(g[col]),
                               text=g[col].map(f.format), textposition="outside", cliponaxis=False,
                               hovertemplate="%{x}<br>%{y:,.2f}<extra></extra>"))
        fig.update_layout(title=f"{metric_name} by {dim_label.lower()}")
        fig.update_yaxes(range=[0, g[col].max() * 1.2], visible=False)
        plot(fig, 360)
    with b:
        tr = df if focus == "All (filtered)" else df[df[dim].astype(str) == focus]
        t = tr.groupby("Month")[col].agg(agg).reset_index()
        fig = go.Figure(go.Scatter(x=t["Month"], y=t[col], mode="lines+markers", line=dict(color=ACCENT, width=2.5),
                                   marker=dict(size=8), hovertemplate="%{x|%b %Y}<br>%{y:,.2f}<extra></extra>"))
        fig.update_layout(title=f"{metric_name} over time - {focus}")
        fig.update_yaxes(rangemode="tozero", title=None)
        fig.update_xaxes(tickformat="%b %y", title=None)
        plot(fig, 360)

    st.markdown("##### Two-way heatmap")
    h1, h2 = st.columns(2)
    row_label = h1.selectbox("Rows", list(DIMS), index=2)
    col_label = h2.selectbox("Columns", list(DIMS), index=0)
    if row_label == col_label:
        st.info("Pick two different dimensions for the heatmap.")
    else:
        hm = df.pivot_table(index=DIMS[row_label], columns=DIMS[col_label], values=col, aggfunc=agg, observed=True)
        fig = px.imshow(hm, text_auto=".2f" if agg == "mean" and "ER" in col else ",.0f", aspect="auto",
                        color_continuous_scale=SEQ[:4], title=f"{metric_name}: {row_label.lower()} × {col_label.lower()}")
        fig.update_coloraxes(showscale=False)
        fig.update_xaxes(title=None)
        fig.update_yaxes(title=None)
        plot(fig, 400)
    caveat("Pick a metric and a dimension to compare groups, choose one group to see its monthly trend, then cross two "
           "dimensions in the heatmap. All views respect the sidebar filters.")

# ------------------------------- Strategy & AI --------------------------------
with tabs[9]:
    st.subheader("What should the marketing team do next?")

    if levers.empty:
        st.info("Not enough groups in the current selection to score strategy levers.")
    else:
        if len(meaningful):
            st.markdown(f"##### Headline: {len(meaningful)} lever(s) show a meaningful, statistically supported difference")
        else:
            st.markdown("##### Headline: no single format, day, hashtag or campaign is a clear winner in this data")
        sc = levers.sort_values("Gap")
        color_map = {"Meaningful": ACCENT, "Significant, but small": SOFT, "Within noise": BASE}
        fig = go.Figure(go.Bar(
            x=sc["Gap"], y=sc["Lever"], orientation="h", marker_color=sc["Verdict"].map(color_map),
            text=[f"{g:.1f}% · {v}" for g, v in zip(sc["Gap"], sc["Verdict"])], textposition="outside", cliponaxis=False,
            customdata=np.c_[sc["Best"], sc["Worst"], sc["P"].fillna(-1)],
            hovertemplate="<b>%{y}</b><br>Best: %{customdata[0]}<br>Worst: %{customdata[1]}"
                          "<br>Gap: %{x:.1f}%<extra></extra>"))
        fig.update_layout(title="Lever scorecard - how much does each choice move engagement rate?")
        fig.update_xaxes(range=[0, max(sc["Gap"].max() * 1.6, 8)], title="Best-vs-worst gap (% of average engagement rate)")
        fig.update_yaxes(title=None)
        plot(fig, 360)
        show = levers.assign(P=levers["P"].map(lambda p: "CI test" if pd.isna(p) else ("<0.001" if p < 0.001 else f"{p:.3f}")))
        with st.expander("View scorecard table"):
            st.dataframe(show.rename(columns={"Best_ER": "Best ER (%)", "Worst_ER": "Worst ER (%)", "Gap": "Gap (%)", "P": "p-value"})
                         .round(2), hide_index=True, width="stretch")
        st.caption("Meaningful = gap ≥ 5% and statistically significant (ANOVA p < 0.05; hashtags use non-overlapping 95% CIs). "
                   "Small or noisy gaps should be A/B tested, not acted on.")

    recs = []
    for _, r in meaningful.sort_values("Gap", ascending=False).iterrows() if len(meaningful) else []:
        recs.append(("DOUBLE DOWN", f"Lean into {r['Lever'].lower()}: {r['Best']}",
                     f"{r['Best']} delivers {r['Best_ER']:.2f}% engagement vs {r['Worst_ER']:.2f}% for {r['Worst']} - a "
                     f"{r['Gap']:.1f}% gap that is statistically supported. Shift budget and creative effort toward it."))
    recs += [
        ("SCALE", "Grow reach - it is the lever that moves total engagement",
         f"Every 1,000 accounts reached produce ~{interactions_per_1k:,.0f} interactions, and engagement rate stays flat as reach grows. "
         "Invest in amplification: influencer & collab posts, paid boosts of proven creatives, and Reels/Stories distribution."),
        ("FIX", "Rescue 'seen but ignored' content",
         f"{gap_mask.mean() * 100:.1f}% of records combine top-quartile reach with bottom-quartile engagement. Audit them for weak hooks, "
         "missing calls-to-action and off-brief creative; add comment-driving prompts (polls, questions, giveaways)."),
        ("DEEPEN", "Move audiences from likes to comments, saves and shares",
         f"Likes are {df['Likes'].sum() / tot_eng * 100:.0f}% of interactions. Build save-worthy content (tutorials, shade guides, how-to Reels) "
         "and share-worthy content (festive offers, challenges) - these signal purchase intent and organic virality."),
        ("CONVERT", "Turn profile visits into followers",
         f"{pv_rate:.1f}% of reach visits the profile and {follow_rate:.0f}% of those visitors follow. Improve bio, pinned posts, "
         "highlights and link-in-bio offers - a 1-point lift in follow conversion is a cheap, direct growth win."),
        ("TEST", "Replace guesswork with controlled experiments",
         "Run 4-week A/B tests: same creative as Reel vs Image; 2 vs 3 hashtags; morning vs evening slots. "
         "Decide only on results that are statistically significant."),
        ("KEEP", "Maintain steady cadence and the current hashtag core",
         f"Keep {', '.join(ht['Hashtag'].head(3))} in rotation, hold monthly volume steady and preserve a balanced format mix."),
        ("MEASURE", "Close the data gaps",
         "Capture a unique post ID, caption, posting hour, carousel format, ad spend and follower count. These unlock caption analysis, "
         "best-time-to-post, true ROI per post and follower-growth tracking."),
    ]
    st.markdown("##### Recommended actions")
    left, right = st.columns(2)
    for i, (tag, title, body) in enumerate(recs):
        (left if i % 2 == 0 else right).markdown(
            f'<div class="rec-card"><span class="rec-tag">{tag}</span><h4>{title}</h4><span class="body">{body}</span></div>',
            unsafe_allow_html=True)

    st.markdown("##### Content & campaign ideas")
    st.markdown(
        "- **Tutorial Reels series** ('5-minute festive look') - built for saves and shares\n"
        "- **Influencer collab takeovers** with a giveaway mechanic - built for reach plus comments\n"
        "- **Festive offer Stories** with poll/quiz stickers - built for interaction at scale\n"
        "- **Vegan & cruelty-free brand-values content** - on-brand and consistent with the top hashtag themes\n"
        "- **Profile-visit nudges** ('Follow for shade drops') in the last frame of high-reach posts"
    )

    st.markdown("##### 🤖 Ask the data (optional AI analyst · free LLM)")
    cfg = llm_config()
    q = st.text_input("Ask a question about the filtered data",
                      placeholder="Which campaign should we double down on, and why?")
    if q:
        if not cfg:
            st.info("Add a free API key to Streamlit secrets (or as an environment variable) to enable this: "
                    "`GROQ_API_KEY` (console.groq.com), `GEMINI_API_KEY` (aistudio.google.com) or "
                    "`OPENROUTER_API_KEY` (openrouter.ai). Everything else in the dashboard works without it.")
        else:
            ctx = "\n\n".join([
                f"KPIs: records={len(df)}, likes={df['Likes'].sum()}, comments={df['Comments'].sum()}, reach={tot_reach}, "
                f"avg_ER={avg_er:.2f}%, follow_conversion={follow_rate:.1f}%",
                *[f"Avg ER by {c}:\n{df.groupby(c, observed=True)['ER'].mean().round(3).to_string()}"
                  for c in ["Post_Type", "Campaign_Type", "Weekday", "Engagement_Source", "Audience_Emotion"]],
                f"Avg ER by hashtag:\n{ht.set_index('Hashtag')['Avg_ER'].round(3).to_string()}",
                f"Lever scorecard:\n{levers[['Lever', 'Best', 'Worst', 'Gap', 'Verdict']].round(2).to_string(index=False)}"
                if not levers.empty else ""])
            try:
                with st.spinner(f"Analysing with {cfg[0].title()}…"):
                    st.markdown(ask_llm(q, ctx))
                st.caption(f"Answered by {cfg[3]} via {cfg[0].title()} from aggregated numbers only - "
                           "no row-level data is sent.")
            except Exception as ex:  # noqa: BLE001
                st.error(f"AI request failed: {ex}")

    caveat("Treat these as a method and a decision framework; validate with the brand's live Instagram Insights export "
           "before reallocating spend.")

st.markdown("---")
st.caption("Built with Streamlit · Plotly · Pandas  |  Sugar Cosmetics Instagram Analytics  |  P Suman Sangeet")