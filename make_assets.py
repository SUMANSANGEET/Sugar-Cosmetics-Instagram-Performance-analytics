"""Builds docs/facts.json and PNG charts used by the report, guide and deck."""
import json
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats

A, B, INK, MUT, GRID = "#C2185B", "#B9BEC8", "#1F2430", "#6B7280", "#E7E9EE"
df = pd.read_csv("data/sugar_cosmetics_clean.csv", parse_dates=["Post Date", "Month"])
ER = "Engagement Rate (%)"
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.edgecolor": GRID, "axes.labelcolor": MUT,
                     "xtick.color": MUT, "ytick.color": MUT, "axes.spines.top": False, "axes.spines.right": False})


def save(fig, name):
    fig.tight_layout()
    fig.savefig(f"docs/charts/{name}.png", dpi=200, facecolor="white")
    plt.close(fig)


def hl(v, best="max"):
    i = int(np.argmax(v)) if best == "max" else int(np.argmin(v))
    return [A if k == i else B for k in range(len(v))]


f = {}
tot = df["Total Engagement"].sum()
f["kpi"] = dict(
    records=len(df), likes=int(df.Likes.sum()), comments=int(df.Comments.sum()), shares=int(df.Shares.sum()),
    saves=int(df.Saves.sum()), reach=int(df.Reach.sum()), impressions=int(df.Impressions.sum()), engagement=int(tot),
    avg_er=df[ER].mean(), pooled_er=tot / df.Reach.sum() * 100, reach_rate=df.Reach.sum() / df.Impressions.sum() * 100,
    profile_visits=int(df["Profile Visits"].sum()), follows=int(df.Follows.sum()),
    pv_rate=df["Profile Visits"].sum() / df.Reach.sum() * 100,
    follow_conv=df.Follows.sum() / df["Profile Visits"].sum() * 100,
    like_share=df.Likes.sum() / tot * 100, comment_share=df.Comments.sum() / tot * 100,
    save_share=df.Saves.sum() / tot * 100, share_share=df.Shares.sum() / tot * 100,
    per_1000_reach=tot / df.Reach.sum() * 1000)


def grp(col, order=None):
    g = df.groupby(col, observed=True).agg(
        n=("Record ID", "size"), likes=("Likes", "mean"), comments=("Comments", "mean"), shares=("Shares", "mean"),
        saves=("Saves", "mean"), reach=("Reach", "mean"), er=(ER, "mean"), sd=(ER, "std")).reset_index()
    g["ci"] = 1.96 * g.sd / np.sqrt(g.n)
    if order:
        g[col] = pd.Categorical(g[col], order, ordered=True)
        g = g.sort_values(col)
    else:
        g = g.sort_values("er", ascending=False)
    return g


pt, dw, cp, src, emo = (grp("Post Type"), grp("Day of Week", DAYS), grp("Campaign Type"),
                        grp("Engagement Source"), grp("Audience Emotion"))
ex = df.assign(Hashtag=df.Hashtags.str.split(", ")).explode("Hashtag")
ht = ex.groupby("Hashtag").agg(n=("Record ID", "size"), er=(ER, "mean"), sd=(ER, "std"), reach=("Reach", "mean")).reset_index()
ht["ci"] = 1.96 * ht.sd / np.sqrt(ht.n)
ht = ht.sort_values("er", ascending=False)
hc = df.groupby("Hashtag Count").agg(n=("Record ID", "size"), er=(ER, "mean")).reset_index()
mo = df.groupby("Month").agg(n=("Record ID", "size"), er=(ER, "mean")).reset_index()
pvals = {c: float(stats.f_oneway(*[g[ER].values for _, g in df.groupby(c)]).pvalue)
         for c in ["Post Type", "Day of Week", "Campaign Type", "Engagement Source", "Audience Emotion"]}
pvals["Hashtag"] = float(stats.f_oneway(*[g[ER].values for _, g in ex.groupby("Hashtag")]).pvalue)
spread = lambda s: (s.max() - s.min()) / s.mean() * 100
q_r, q_e = df.Reach.quantile(.75), df[ER].quantile(.25)
gap = df[(df.Reach >= q_r) & (df[ER] <= q_e)]
t_l, t_e = df.nlargest(10, "Likes"), df.nlargest(10, ER)
f.update(
    post_type=pt.round(3).to_dict("records"),
    weekday=dw.round(3).astype({"Day of Week": str}).to_dict("records"),
    campaign=cp.round(3).to_dict("records"), source=src.round(3).to_dict("records"),
    emotion=emo.round(3).to_dict("records"), hashtag=ht.round(3).to_dict("records"),
    hashtag_count=hc.round(3).to_dict("records"),
    monthly=[dict(month=m.strftime("%b %Y"), n=int(n), er=round(e, 3)) for m, n, e in zip(mo.Month, mo.n, mo.er)],
    pvalues=pvals,
    spreads=dict(post_type=spread(pt.er), weekday=spread(dw.er), hashtag=spread(ht.er), campaign=spread(cp.er)),
    gap=dict(n=len(gap), pct=len(gap) / len(df) * 100, reach_q75=q_r, er_q25=q_e),
    top_likes=t_l[["Post Label", "Likes", "Reach", ER]].round(2).to_dict("records"),
    top_er=t_e[["Post Label", "Likes", "Reach", ER]].round(2).to_dict("records"),
    top_likes_avg_reach=t_l.Reach.mean(), avg_reach=df.Reach.mean(), top_er_median_reach=t_e.Reach.median(),
    corr_reach_likes=df.Reach.corr(df.Likes), corr_reach_er=df.Reach.corr(df[ER]),
    records_per_day=len(df) / ((df["Post Date"].max() - df["Post Date"].min()).days + 1))
json.dump(f, open("docs/facts.json", "w"), indent=1, default=float)

# ---------------- charts ----------------
fig, ax = plt.subplots(figsize=(8, 3.6))
ax.plot(mo.Month, mo.n, color=A, lw=2.5, marker="o")
ax.set_ylim(0, mo.n.max() * 1.2)
ax.scatter([mo.Month.iloc[0], mo.Month.iloc[-1]], [mo.n.iloc[0], mo.n.iloc[-1]], s=90, facecolor="white",
           edgecolor=A, zorder=5, lw=2)
for m, n in zip(mo.Month, mo.n):
    ax.annotate(f"{n:,}", (m, n), textcoords="offset points", xytext=(0, 9), ha="center", fontsize=8.5, color=MUT)
ax.annotate("partial month", (mo.Month.iloc[0], mo.n.iloc[0]), xytext=(8, -18), textcoords="offset points", fontsize=8.5, color=MUT)
ax.annotate("partial month", (mo.Month.iloc[-1], mo.n.iloc[-1]), xytext=(-60, -18), textcoords="offset points", fontsize=8.5, color=MUT)
ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%b %y"))
ax.set_ylabel("Posts per month")
ax.yaxis.grid(True, color=GRID)
ax.set_axisbelow(True)
save(fig, "monthly_posts")


def bars(data, col, lab, name, fmt="{:.2f}%", horizontal=False, ci=None, fs=(7, 3.6)):
    fig, ax = plt.subplots(figsize=fs)
    x = data[col].astype(str).tolist()
    v = data[lab].values
    if horizontal:
        ax.barh(x, v, color=hl(v), xerr=ci, error_kw=dict(ecolor=MUT, lw=1, capsize=3))
        ax.invert_yaxis()
        for i, val in enumerate(v):
            ax.text(val * 0.5, i, fmt.format(val), va="center", ha="center", color="white", fontweight="bold", fontsize=10)
        ax.spines["left"].set_visible(False)
        ax.set_xlim(0, v.max() * 1.15)
    else:
        ax.bar(x, v, color=hl(v), yerr=ci, error_kw=dict(ecolor=MUT, lw=1, capsize=3))
        for i, val in enumerate(v):
            ax.text(i, val * 0.5, fmt.format(val), ha="center", color="white", fontweight="bold", fontsize=10)
        ax.set_ylim(0, v.max() * 1.25)
        ax.yaxis.grid(True, color=GRID)
        ax.set_axisbelow(True)
    save(fig, name)


bars(pt, "Post Type", "er", "post_type_er", ci=pt.ci.values)
bars(dw.assign(**{"Day of Week": dw["Day of Week"].astype(str).str[:3]}), "Day of Week", "er", "weekday_er",
     ci=dw.ci.values, fs=(8, 3.6))
hs = ht.sort_values("er")
bars(hs, "Hashtag", "er", "hashtag_er", horizontal=True, ci=hs.ci.values)
bars(cp.sort_values("er"), "Campaign Type", "er", "campaign_er", horizontal=True)

# funnel
st_ = ["Impressions", "Reach", "Likes", "Comments", "Shares", "Saves"]
vals = [df[s].sum() for s in st_]
fig, ax = plt.subplots(figsize=(8, 3.9))
cols = ["#F3A6C4", "#F3A6C4", "#DE5F92", "#C2185B", "#C2185B", "#C2185B"]
for i, (s, v) in enumerate(zip(st_, vals)):
    w = max(v / vals[0], 0.012)
    ax.barh(i, w, left=(1 - w) / 2, color=cols[i], height=0.72)
    lbl = f"{v / 1e6:,.1f}M  ·  {v / vals[0] * 100:.1f}%"
    if i < 2:
        ax.text(0.5, i, lbl, ha="center", va="center", color=INK, fontsize=10, fontweight="bold")
    else:
        ax.text((1 - w) / 2 + w + 0.02, i, lbl, ha="left", va="center", color=INK, fontsize=10, fontweight="bold")
ax.set_yticks(range(6))
ax.set_yticklabels(st_)
ax.invert_yaxis()
ax.set_xlim(0, 1)
ax.set_xticks([])
[s.set_visible(False) for s in ax.spines.values()]
ax.tick_params(left=False)
save(fig, "funnel")

# engagement mix
mix = pd.DataFrame({"k": ["Likes", "Comments", "Saves", "Shares"],
                    "v": [f["kpi"]["like_share"], f["kpi"]["comment_share"], f["kpi"]["save_share"], f["kpi"]["share_share"]]})
fig, ax = plt.subplots(figsize=(5, 3))
ax.barh(mix.k, mix.v, color=[A, B, B, B])
ax.invert_yaxis()
ax.set_xlim(0, 100)
ax.set_xticks([])
ax.spines["left"].set_visible(False)
for i, v in enumerate(mix.v):
    ax.text(v + 1.5, i, f"{v:.1f}%", va="center", fontsize=10, color=INK)
save(fig, "engagement_mix")


def top(d, col, name, fmt):
    d = d.iloc[::-1]
    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.barh(d["Post Label"], d[col], color=A)
    for i, v in enumerate(d[col]):
        ax.text(v * 1.01, i, fmt.format(v), va="center", fontsize=9, color=INK)
    ax.set_xlim(0, d[col].max() * 1.12)
    ax.set_xticks([])
    ax.spines["left"].set_visible(False)
    ax.tick_params(left=False, labelsize=8.5)
    save(fig, name)


top(t_l, "Likes", "top_likes", "{:,.0f}")
top(t_e, ER, "top_er", "{:.1f}%")

# reach vs engagement-rate scatter
s = df.sample(3000, random_state=7)
fig, ax = plt.subplots(figsize=(7, 3.6))
g = (s.Reach >= q_r) & (s[ER] <= q_e)
ax.scatter(s.Reach[~g], s[ER][~g], s=8, color=B, alpha=.5)
ax.scatter(s.Reach[g], s[ER][g], s=10, color=A, alpha=.8, label="High reach, low engagement")
ax.axvline(q_r, color=MUT, ls=":")
ax.axhline(q_e, color=MUT, ls=":")
ax.set_xlabel("Reach")
ax.set_ylabel("Engagement rate (%)")
ax.legend(frameon=False, loc="upper right", fontsize=9)
save(fig, "reach_vs_er")
print(json.dumps({k: f[k] for k in ["kpi", "pvalues", "spreads", "gap", "records_per_day", "corr_reach_likes", "corr_reach_er"]}, indent=1, default=float))
