"""
Part 3 — Auto Cover Letter + Resume Summary Generator
------------------------------------------------------
Reads matched_jobs.csv → generates custom cover letter
+ resume summary for each job using Nvidia free API
→ saves everything to tracker.xlsx

HOW TO RUN:
    python cover_letter.py

SETUP:
    1. pip install openai pandas openpyxl
    2. Paste your Nvidia API key below
"""

from openai import OpenAI
import pandas as pd
import os
from dotenv import load_dotenv
import time
from datetime import datetime

load_dotenv("keys.env")
# ── CONFIG ──────────────────────────────────────────────────────
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")

MODEL      = "mistralai/mistral-large-3-675b-instruct-2512"
INPUT_FILE = "good_matches.csv"
OUTPUT_FILE= "tracker.xlsx"

YOUR_RESUME = """
Name: Rohit Jaiswal
Location: Bengaluru, India
Experience: 3+ years at Cognizant Technology Solutions

Skills: Python, SQL, Pandas, NumPy, FastAPI, MySQL, PostgreSQL,
        Scikit-learn, Git, Excel, Jupyter Notebook, Azure AZ-900

Work Experience:
- Software Engineer / Data & Analytics at Cognizant (Oct 2022 - Present)
  - Analyzed website data using SQL and Python to find patterns
  - Wrote SQL queries on MySQL and PostgreSQL for reporting and validation
  - Used error logs and system metrics to find root cause of bugs
  - Worked in small team of 2-5 people on OUP India website

- Software Engineer Intern at Cognizant (Jan 2022 - May 2022)
  - Built Pension Management System using Python and SQL
  - Automated calculations and generated reports using Pandas

Projects:
- Customer Churn Prediction: Logistic Regression on Kaggle dataset,
  cleaned data with Pandas, evaluated with accuracy + confusion matrix
- Operations Analytics: SQL scripts to detect metric spikes
- Pension Management System: Stored procedures + automated reporting

Education: B.Tech Electronics Engineering, KIIT University, CGPA 8.11

Certifications: Azure AZ-900, HackerRank 5-Star SQL, 8-Week Data Analytics
"""
# ───────────────────────────────────────────────────────────────


# Init Nvidia client
client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=NVIDIA_API_KEY
)


def call_nvidia(prompt, max_tokens=400):
    """Single API call to Nvidia — returns text response"""
    try:
        completion = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=max_tokens,
            stream=False
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {e}"


def generate_summary(job_title, job_description):
    """3-sentence custom resume summary for this job"""
    prompt = f"""
You are helping Rohit Jaiswal customize his resume summary for a job.

JOB TITLE: {job_title}

JOB DESCRIPTION:
{job_description[:1500]}

ROHIT'S RESUME:
{YOUR_RESUME}

Write a 3-sentence professional summary tailored to this job.
Rules:
- Simple plain English, no fancy words
- Only mention skills Rohit actually has
- Naturally include keywords from job description
- Do not lie or exaggerate
- Return ONLY the summary, nothing else, no labels
"""
    return call_nvidia(prompt, max_tokens=200)


def generate_cover_letter(job_title, company, job_description):
    """Short 3-paragraph cover letter for this job"""
    prompt = f"""
You are helping Rohit Jaiswal write a cover letter.

JOB TITLE: {job_title}
COMPANY: {company}

JOB DESCRIPTION:
{job_description[:1500]}

ROHIT'S RESUME:
{YOUR_RESUME}

Write a short cover letter with exactly 3 paragraphs:
Paragraph 1: Why Rohit is interested in this company and role (2 sentences)
Paragraph 2: How his experience matches what they need (2-3 sentences)
Paragraph 3: Short confident closing (1-2 sentences)

Rules:
- Simple plain English, not too formal
- Only mention skills Rohit actually has
- Sound like a real person not a template
- Under 200 words total
- Return ONLY the cover letter, no labels or extra text
"""
    return call_nvidia(prompt, max_tokens=400)


def process_jobs(df):
    """Loop through jobs, generate summary + cover letter for each"""
    results = []
    total = len(df)

    print(f"\n🤖 Processing {total} jobs...\n")

    for i, row in df.iterrows():
        title   = str(row.get("title",       "N/A"))
        company = str(row.get("company",     "N/A"))
        desc    = str(row.get("description", ""))
        score   = row.get("match_score", 0)
        link    = str(row.get("apply_link",  "N/A"))
        source  = str(row.get("source",      "N/A"))
        skills  = str(row.get("matched_skills", ""))
        priority= str(row.get("priority",    ""))

        print(f"  [{i+1}/{total}] {title} @ {company}")

        # Generate summary
        print(f"         → writing summary...")
        summary = generate_summary(job_title=title, job_description=desc)
        time.sleep(1)  # avoid rate limit

        # Generate cover letter
        print(f"         → writing cover letter...")
        cover = generate_cover_letter(
            job_title=title, company=company, job_description=desc
        )
        time.sleep(1)  # avoid rate limit

        # Mark error if something went wrong
        status = "Error" if "Error:" in summary or "Error:" in cover else "Ready to Apply"

        results.append({
            "title":          title,
            "company":        company,
            "source":         source,
            "match_score":    score,
            "priority":       priority,
            "matched_skills": skills,
            "apply_link":     link,
            "custom_summary": summary,
            "cover_letter":   cover,
            "applied":        "No",
            "status":         status,
            "date_added":     datetime.today().strftime("%Y-%m-%d"),
            "notes":          ""
        })

        print(f"         ✅ done\n")

    return results


def save_tracker(results):
    """Save to Excel with 3 sheets"""
    df = pd.DataFrame(results)

    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:

        # Sheet 1 — all jobs
        df.to_excel(writer, sheet_name="All Jobs", index=False)

        # Sheet 2 — ready to apply only
        ready = df[df["status"] == "Ready to Apply"]
        ready.to_excel(writer, sheet_name="Ready to Apply", index=False)

        # Sheet 3 — high priority only
        high = df[df["match_score"] >= 6]
        high.to_excel(writer, sheet_name="High Priority", index=False)

        # Widen columns on main sheet
        ws = writer.sheets["All Jobs"]
        ws.column_dimensions["A"].width = 35   # title
        ws.column_dimensions["B"].width = 25   # company
        ws.column_dimensions["G"].width = 50   # apply link
        ws.column_dimensions["H"].width = 60   # summary
        ws.column_dimensions["I"].width = 80   # cover letter
        ws.column_dimensions["J"].width = 12   # applied
        ws.column_dimensions["K"].width = 18   # status

    print(f"\n✅ Saved: {OUTPUT_FILE}")
    print(f"   Sheets: All Jobs | Ready to Apply | High Priority")


def main():
    print("=" * 55)
    print("  PART 3 — AUTO COVER LETTER GENERATOR")
    print(f"  Model: {MODEL}")
    print("=" * 55)

    # Check API key
    if "YOUR_NEW_KEY_HERE" in NVIDIA_API_KEY:
        print("\n❌ API key not set!")
        print("   Paste your nvapi- key in cover_letter.py")
        return

    # Check input file
    if not os.path.exists(INPUT_FILE):
        print(f"\n❌ {INPUT_FILE} not found.")
        print("   Run scraper.py → filter.py first.")
        return

    # Load matched jobs
    df = pd.read_csv(INPUT_FILE)

    # Skip already applied
    if "applied" in df.columns:
        df = df[df["applied"] != "Yes"]

    # ── Only process Medium & High priority jobs (score >= 7) ──
    MIN_SCORE = 7
    all_count = len(df)
    df = df[df["match_score"] >= MIN_SCORE]
    df = df.sort_values("match_score", ascending=False)

    print(f"\n📂 Total jobs in file  : {all_count}")
    print(f"🔥 Processing (4+)     : {len(df)}  ← writing cover letters for THESE only")
    print(f"⏱️  Est. time           : ~{len(df)*3} seconds")

    if len(df) == 0:
        print("\n❌ No jobs found (score >= 4). Run scraper again for fresh jobs!")
        return

    # Process only high-priority jobs
    results = process_jobs(df)

    # Save
    save_tracker(results)

    # Summary
    success = sum(1 for r in results if r["status"] == "Ready to Apply")
    errors  = sum(1 for r in results if r["status"] == "Error")

    print("\n" + "=" * 55)
    print(f"  ✅ DONE!")
    print(f"  Processed : {len(results)} jobs")
    print(f"  Success   : {success}")
    print(f"  Errors    : {errors}")
    print(f"  Saved to  : {OUTPUT_FILE}")
    print("=" * 55)
    print("\n📋 NEXT STEPS:")
    print("  1. Open tracker.xlsx")
    print("  2. Go to 'High Priority' sheet")
    print("  3. Copy cover letter → apply → mark applied = Yes")
    print("  4. Run tomorrow for fresh jobs\n")


if __name__ == "__main__":
    main()