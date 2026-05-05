"""
filter.py — Upgraded Job Filter
---------------------------------
Reads jobs.csv → scores → filters → saves good_matches.csv

HOW TO RUN:
    python filter.py
"""

import pandas as pd
import re
from datetime import datetime, timedelta

# ── CONFIG ──────────────────────────────────────────────────────
MIN_SCORE        = 3      # lowered from 4 — catches more matches
MAX_EXP_YEARS    = 5      # skip jobs needing 6+ years
DAYS_CUTOFF      = 30     # skip jobs older than 30 days (0 = off)
MIN_SALARY_LPA   = 4      # skip jobs below this salary (0 = off)
# ───────────────────────────────────────────────────────────────

# ── EXPANDED KEYWORDS ───────────────────────────────────────────
KEYWORDS = [
    "sql", "python", "pandas", "numpy", "data analyst", "data analysis",
    "mysql", "postgresql", "postgres", "excel", "spreadsheet",
    "scikit-learn", "scikit", "machine learning", "ml", "logistic regression",
    "random forest", "decision tree", "predictive", "statistical",
    "power bi", "tableau", "looker", "metabase", "superset",
    "analytics", "reporting", "dashboard", "kpi", "metrics",
    "etl", "data pipeline", "data warehouse", "bigquery", "redshift",
    "data cleaning", "data wrangling", "data modelling",
    "fastapi", "jupyter", "git", "azure", "cloud",
    "business intelligence", "bi", "visualization", "insight",
    "a/b testing", "cohort", "funnel", "retention", "churn",
    "data driven", "data-driven", "analytical", "report", "query"
]

BONUS_TITLES = [
    "data analyst", "data scientist", "analytics analyst",
    "business analyst", "bi analyst", "product analyst",
    "marketing analyst", "growth analyst", "operations analyst",
    "junior analyst", "associate analyst"
]

PENALTY_TITLES = [
    "senior", "lead", "manager", "head", "director",
    "principal", "architect", "vp ", "chief"
]

BLACKLIST_TITLES = [
    "intern", "fresher", "trainee", "apprentice"
]
# ───────────────────────────────────────────────────────────────


def check_salary(salary_str):
    if pd.isna(salary_str) or str(salary_str).strip() == "":
        return 0
    s = str(salary_str).lower().replace(",", "")
    numbers = re.findall(r'\d+(?:\.\d+)?', s)
    if not numbers:
        return 0
    nums = [float(n) for n in numbers]
    max_num = max(nums)
    if any(x in s for x in ['lac', 'lakh', 'lpa', 'l.p.a']):
        return max_num
    if max_num > 100000:
        return round(max_num / 100000, 1)
    return 0


def check_experience(exp_str):
    if pd.isna(exp_str) or str(exp_str).strip() == "":
        return 0
    s = str(exp_str).lower()
    numbers = re.findall(r'\d+', s)
    if not numbers:
        return 0
    return int(numbers[0])


def is_recent(date_str, days=30):
    if days == 0:
        return True
    if pd.isna(date_str) or str(date_str).strip() in ["", "N/A"]:
        return True
    try:
        for fmt in ["%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%d/%m/%Y"]:
            try:
                posted = datetime.strptime(str(date_str).strip(), fmt)
                return (datetime.today() - posted).days <= days
            except:
                continue
        s = str(date_str).lower()
        if "hour" in s or "just" in s or "today" in s:
            return True
        if "day" in s:
            n = re.findall(r'\d+', s)
            return int(n[0]) <= days if n else True
        if "week" in s:
            n = re.findall(r'\d+', s)
            return int(n[0]) * 7 <= days if n else True
        if "month" in s:
            n = re.findall(r'\d+', s)
            return int(n[0]) * 30 <= days if n else True
        return True
    except:
        return True


def calculate_score(row):
    score = 0
    title = str(row.get("title", "")).lower()
    desc  = str(row.get("description", "")).lower()
    text  = title + " " + desc

    for kw in KEYWORDS:
        if kw in text:
            score += 1

    if any(bt in title for bt in BONUS_TITLES):
        score += 3

    salary = check_salary(row.get("salary", ""))
    if salary > 0 and salary >= MIN_SALARY_LPA:
        score += 1

    if any(w in text for w in ["remote", "hybrid", "work from home", "wfh"]):
        score += 1

    if any(pk in title for pk in PENALTY_TITLES):
        score -= 1

    exp = check_experience(row.get("experience", ""))
    if exp > MAX_EXP_YEARS:
        score -= 2

    return max(0, min(score, 10))


def determine_priority(score):
    if score >= 7:
        return "🔥 HIGH"
    elif score >= 4:
        return "✅ MEDIUM"
    else:
        return "👀 LOW"


def main():
    try:
        df = pd.read_csv("jobs.csv")
    except FileNotFoundError:
        print("❌ jobs.csv not found. Run scraper.py first.")
        return

    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].fillna("")

    total = len(df)
    print("=" * 50)
    print("  UPGRADED JOB FILTER")
    print("=" * 50)
    print(f"  Total jobs loaded : {total}")

    df["match_score"] = df.apply(calculate_score, axis=1)
    df["priority"]    = df["match_score"].apply(determine_priority)
    df.sort_values("match_score", ascending=False, inplace=True)
    df.to_csv("all_jobs_scored.csv", index=False)

    mask = (
        (df["match_score"] >= MIN_SCORE) &
        (df["applied"].astype(str).str.strip().str.lower() == "no") &
        (~df["title"].str.lower().str.contains(
            "|".join(BLACKLIST_TITLES), na=False)) &
        (df["scraped_date"].apply(lambda d: is_recent(d, DAYS_CUTOFF)))
    )

    if MIN_SALARY_LPA > 0:
        salary_ok = df["salary"].apply(
            lambda s: check_salary(s) >= MIN_SALARY_LPA or check_salary(s) == 0
        )
        mask = mask & salary_ok

    good = df[mask].copy()
    good.drop_duplicates(subset=["company", "title"], inplace=True)
    good.to_csv("good_matches.csv", index=False)

    high   = len(good[good["match_score"] >= 7])
    medium = len(good[(good["match_score"] >= 4) & (good["match_score"] < 7)])
    low    = len(good[good["match_score"] < 4])

    print(f"  After filtering   : {len(good)} good matches")
    print(f"  🔥 High  (7-10)   : {high}")
    print(f"  ✅ Medium (4-6)   : {medium}")
    print(f"  👀 Low   (1-3)    : {low}")
    print("=" * 50)

    if "source" in good.columns:
        print("\n📍 BY SOURCE:")
        for src, cnt in good["source"].value_counts().items():
            print(f"   {src}: {cnt} jobs")

    print("\n🏆 TOP 10 MATCHES:\n")
    for _, row in good.head(10).iterrows():
        print(f"  {row['title']} @ {row['company']}")
        print(f"  Score: {row['match_score']}/10 | {row['priority']} | {row.get('source','')}")
        salary = check_salary(row.get('salary',''))
        if salary > 0:
            print(f"  Salary: {salary} LPA")
        print(f"  Link : {row.get('apply_link','N/A')}")
        print()

    print(f"💾 Saved: good_matches.csv ({len(good)} jobs)")
    print(f"💾 Saved: all_jobs_scored.csv ({total} jobs)\n")

    if len(good) < 10:
        print("💡 Still low? Try:")
        print("   - Lower MIN_SCORE = 2 in filter.py")
        print("   - Set DAYS_CUTOFF = 0 to include older jobs")
        print("   - Run scraper.py again for fresh results")
        print("   - Increase LINKEDIN_PAGES/NAUKRI_PAGES in scraper.py\n")


if __name__ == "__main__":
    main()