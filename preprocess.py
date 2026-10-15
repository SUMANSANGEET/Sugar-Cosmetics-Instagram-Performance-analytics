"""Step 1 - validate, clean and enrich the raw Sugar Cosmetics Instagram data.

Usage:  python preprocess.py sugar_cosmetics_instagram_data.xlsx
Outputs: data/sugar_cosmetics_clean.csv  (read by app.py)
         data/sugar_cosmetics_preprocessed.xlsx  (Clean Data + Data Quality Report sheets)
         data/data_quality_report.csv
"""
import sys
import pandas as pd

RAW = sys.argv[1] if len(sys.argv) > 1 else "sugar_cosmetics_instagram_data.xlsx"
df = pd.read_excel(RAW) if RAW.endswith(("xlsx", "xls")) else pd.read_csv(RAW)
df.columns = [c.strip() for c in df.columns]
df["Post Date"] = pd.to_datetime(df["Post Date"])

# ---- validation (document the findings; the file needs no imputation) ----
num = df.select_dtypes("number")
report = pd.DataFrame([
    ("Rows", len(df)), ("Columns", df.shape[1]),
    ("Missing values (total)", int(df.isna().sum().sum())),
    ("Exact duplicate rows", int(df.duplicated().sum())),
    ("Negative numeric values", int((num < 0).sum().sum())),
    ("Reach > Impressions (invalid)", int((df["Reach"] > df["Impressions"]).sum())),
    ("Zero values - Shares", int((df["Shares"] == 0).sum())),
    ("Zero values - Follows", int((df["Follows"] == 0).sum())),
    ("Date range start", str(df["Post Date"].min().date())),
    ("Date range end", str(df["Post Date"].max().date())),
    ("Distinct post types", df["Post Type"].nunique()),
], columns=["Check", "Result"])
print(report.to_string(index=False))

# ---- calculated fields ----
df["Record ID"] = range(1, len(df) + 1)
df["Total Engagement"] = df.Likes + df.Comments + df.Shares + df.Saves
df["Engagement Rate (%)"] = (df["Total Engagement"] / df.Reach * 100).where(df.Reach > 0).round(3)
df["Profile Visit Rate (%)"] = (df["Profile Visits"] / df.Reach * 100).where(df.Reach > 0).round(3)
df["Follow Conversion (%)"] = (df.Follows / df["Profile Visits"] * 100).where(df["Profile Visits"] > 0).round(2)
df["Reach Rate (%)"] = (df.Reach / df.Impressions * 100).where(df.Impressions > 0).round(3)
df["Month"] = df["Post Date"].dt.to_period("M").dt.to_timestamp()
df["Month Label"] = df["Post Date"].dt.strftime("%b %Y")
df["Day of Week"] = df["Post Date"].dt.day_name()
df["Hashtag Count"] = df.Hashtags.str.split(", ").str.len()
df["Post Label"] = ("#" + df["Record ID"].astype(str) + " · " + df["Post Type"] + " · "
                    + df["Campaign Type"] + " · " + df["Post Date"].dt.strftime("%d %b %Y"))

df.to_csv("data/sugar_cosmetics_clean.csv", index=False)
report.to_csv("data/data_quality_report.csv", index=False)
with pd.ExcelWriter("data/sugar_cosmetics_preprocessed.xlsx") as xw:
    df.to_excel(xw, sheet_name="Clean Data", index=False)
    report.to_excel(xw, sheet_name="Data Quality Report", index=False)
print("Saved cleaned data:", df.shape)
