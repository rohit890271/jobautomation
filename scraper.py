"""
Job Scraper — LinkedIn + Naukri
--------------------------------
Scrapes Data Analyst jobs from LinkedIn and Naukri
and saves them to jobs.csv

HOW TO RUN:
    python scraper.py

REQUIREMENTS:
    pip install selenium beautifulsoup4 pandas webdriver-manager

BROWSER:
    Works with Microsoft Edge or Brave.
    Set BROWSER = "edge" or "brave" below.
"""

import os

from selenium import webdriver
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.chrome.options import Options as ChromeOptions
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
from datetime import datetime

# ── CONFIG — change these as you like ──────────────────────────
SEARCH_ROLE     = "Data Analyst"
SEARCH_LOCATION = "Bengaluru"
LINKEDIN_PAGES  = 5      # each page = ~25 jobs
NAUKRI_PAGES    = 5      # each page = ~20 jobs
OUTPUT_FILE     = "jobs.csv"

# SET YOUR BROWSER HERE — "edge" or "brave"
BROWSER = "edge"

# Only change this if you use Brave
# Find your path:
#   Windows: C:/Program Files/BraveSoftware/Brave-Browser/Application/brave.exe
#   Mac:     /Applications/Brave Browser.app/Contents/MacOS/Brave Browser
#   Linux:   /usr/bin/brave-browser
BRAVE_PATH = "C:/Program Files/BraveSoftware/Brave-Browser/Application/brave.exe"
# ───────────────────────────────────────────────────────────────


def get_driver():
    """
    Set up browser driver.
    Supports Microsoft Edge and Brave.
    Runs silently in the background — no window pops up.
    """

    if BROWSER == "edge":
        # ── MICROSOFT EDGE ──
        # Edge driver is auto downloaded — nothing to install manually
        options = EdgeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        # Anti-bot detection features
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_argument("--disable-web-resources")
        options.add_argument("--disable-extensions")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-plugins")
        # User agent to appear as real browser
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
        )
        driver = webdriver.Edge(options=options)

    elif BROWSER == "brave":
        # ── BRAVE BROWSER ──
        # Brave is built on Chrome so we use ChromeDriver
        options = ChromeOptions()
        options.binary_location = BRAVE_PATH
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
        driver = webdriver.Chrome(options=options)

    else:
        raise ValueError(f"Unknown browser: {BROWSER}. Use 'edge' or 'brave'.")

    return driver


def random_sleep(min_sec=5, max_sec=12):
    """Wait a random time to avoid bot detection. Default: 5-12 seconds"""
    time.sleep(random.uniform(min_sec, max_sec))


# ── LINKEDIN SCRAPER ────────────────────────────────────────────

def scrape_linkedin(role, location, num_pages=5):
    """
    Scrapes LinkedIn jobs without login.
    Uses the public jobs page — no account needed.
    """
    print(f"\n🔵 Starting LinkedIn scraper...")
    driver = get_driver()
    jobs = []

    for page in range(num_pages):
        start = page * 25
        url = (
            f"https://www.linkedin.com/jobs/search/"
            f"?keywords={role.replace(' ', '%20')}"
            f"&location={location.replace(' ', '%20')}"
            f"&start={start}"
        )

        print(f"   📄 Scraping LinkedIn page {page + 1}...")
        driver.get(url)
        random_sleep(8, 15)  # Longer wait for page load

        # Scroll to load all job cards
        for _ in range(3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            random_sleep(3, 6)  # Increased scroll delay

        soup = BeautifulSoup(driver.page_source, "html.parser")
        job_cards = soup.find_all("div", class_="base-card")

        print(f"   ✅ Found {len(job_cards)} jobs on page {page + 1}")

        for card in job_cards:
            try:
                title_tag = card.find("h3", class_="base-search-card__title") or card.find("h3")
                title = title_tag.get_text(strip=True) if title_tag else "N/A"

                company_tag = card.find("h4", class_="base-search-card__subtitle")
                company = company_tag.get_text(strip=True) if company_tag else "N/A"

                location_tag = card.find("span", class_="job-search-card__location")
                job_location = location_tag.get_text(strip=True) if location_tag else "N/A"

                link_tag = card.find("a", class_="base-card__full-link")
                link = link_tag["href"] if link_tag else "N/A"

                date_tag = card.find("time")
                date_posted = date_tag.get_text(strip=True) if date_tag else "N/A"

                if title != "N/A" and company != "N/A":
                    jobs.append({
                        "source":       "LinkedIn",
                        "title":        title,
                        "company":      company,
                        "location":     job_location,
                        "experience":   "N/A",
                        "salary":       "N/A",
                        "date_posted":  date_posted,
                        "apply_link":   link,
                        "description":  "",
                        "scraped_date": datetime.today().strftime("%Y-%m-%d"),
                        "applied":      "No",
                        "status":       "Not Applied"
                    })
            except Exception:
                continue

        random_sleep(10, 20)  # Long delay between pages to avoid detection

    driver.quit()
    print(f"   🎯 LinkedIn total: {len(jobs)} jobs scraped")
    return jobs


# ── NAUKRI SCRAPER ──────────────────────────────────────────────

def scrape_naukri(role, location, num_pages=5):
    """
    Scrapes Naukri.com job listings.
    """
    print(f"\n🔴 Starting Naukri scraper...")
    driver = get_driver()
    jobs = []

    for page in range(1, num_pages + 1):
        url = (
            f"https://www.naukri.com/"
            f"{role.lower().replace(' ', '-')}-jobs-in-"
            f"{location.lower().replace(' ', '-')}-{page}"
        )

        print(f"   📄 Scraping Naukri page {page}...")
        driver.get(url)
        random_sleep(8, 15)  # Longer wait for page load

        for _ in range(4):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            random_sleep(3, 6)  # Increased scroll delay

        soup = BeautifulSoup(driver.page_source, "html.parser")
        job_cards = soup.find_all("article", class_="jobTuple")

        if not job_cards:
            job_cards = soup.find_all("div", class_="srp-jobtuple-wrapper")

        print(f"   ✅ Found {len(job_cards)} jobs on page {page}")

        for card in job_cards:
            try:
                title_tag = card.find("a", class_="title") or card.find("a", class_="jobTitle")
                title = title_tag.get_text(strip=True) if title_tag else "N/A"

                company_tag = card.find("a", class_="subTitle") or card.find("span", class_="companyInfo")
                company = company_tag.get_text(strip=True) if company_tag else "N/A"

                location_tag = card.find("li", class_="location") or card.find("span", class_="locWdth")
                job_location = location_tag.get_text(strip=True) if location_tag else location

                link = title_tag["href"] if title_tag and title_tag.has_attr("href") else "N/A"

                exp_tag = card.find("li", class_="experience")
                experience = exp_tag.get_text(strip=True) if exp_tag else "N/A"

                salary_tag = card.find("li", class_="salary")
                salary = salary_tag.get_text(strip=True) if salary_tag else "N/A"

                desc_tag = card.find("div", class_="job-description")
                description = desc_tag.get_text(strip=True) if desc_tag else ""

                if title != "N/A" and company != "N/A":
                    jobs.append({
                        "source":       "Naukri",
                        "title":        title,
                        "company":      company,
                        "location":     job_location,
                        "experience":   experience,
                        "salary":       salary,
                        "date_posted":  "N/A",
                        "apply_link":   link,
                        "description":  description,
                        "scraped_date": datetime.today().strftime("%Y-%m-%d"),
                        "applied":      "No",
                        "status":       "Not Applied"
                    })
            except Exception:
                continue

        random_sleep(10, 20)  # Long delay between pages to avoid detection

    driver.quit()
    print(f"   🎯 Naukri total: {len(jobs)} jobs scraped")
    return jobs


# ── KEYWORD MATCHER ─────────────────────────────────────────────

YOUR_KEYWORDS = [
    "SQL", "Python", "Pandas", "NumPy", "Data Analyst",
    "MySQL", "PostgreSQL", "Excel", "Power BI", "Tableau",
    "Scikit", "Machine Learning", "FastAPI", "Analytics",
    "ETL", "Dashboard", "Reporting", "Data Pipeline"
]

def score_job(row):
    """Give each job a match score based on your keywords"""
    text = f"{row.get('title', '')} {row.get('description', '')}".lower()
    score = sum(1 for kw in YOUR_KEYWORDS if kw.lower() in text)
    return score


# ── ALREADY HUNTED ─────────────────────────────────────────────

TRACKER_FILE = "tracker.xlsx"

def load_already_applied():
    """
    Reads tracker.xlsx and returns a set of (company, title) pairs
    that have already been applied to. These will be skipped.
    """
    if not os.path.exists(TRACKER_FILE):
        return set()  # No tracker yet — fresh start

    try:
        df = pd.read_excel(TRACKER_FILE, sheet_name="All Jobs")
        applied = df[df["applied"].astype(str).str.strip().str.lower() == "yes"]
        hunted = set(
            zip(
                applied["company"].astype(str).str.strip().str.lower(),
                applied["title"].astype(str).str.strip().str.lower()
            )
        )
        print(f"   🏹 Already hunted: {len(hunted)} jobs will be skipped (from tracker.xlsx)")
        return hunted
    except Exception as e:
        print(f"   ⚠️  Could not read tracker.xlsx: {e}")
        return set()


# ── SAVE + DEDUPLICATE ──────────────────────────────────────────

def save_jobs(new_jobs, output_file):
    """
    Saves jobs to CSV.
    - Checks tracker.xlsx to skip already-applied jobs.
    - If file already exists, adds new jobs and removes duplicates.
    """
    df_new = pd.DataFrame(new_jobs)
    df_new["match_score"] = df_new.apply(score_job, axis=1)

    # ── Filter out already-applied jobs ──
    already_hunted = load_already_applied()
    if already_hunted:
        before = len(df_new)
        df_new = df_new[
            ~df_new.apply(
                lambda row: (
                    str(row["company"]).strip().lower(),
                    str(row["title"]).strip().lower()
                ) in already_hunted,
                axis=1
            )
        ]
        skipped = before - len(df_new)
        if skipped > 0:
            print(f"   🚫 Skipped {skipped} already-applied job(s). Good, no repeat hunting!")

    if os.path.exists(output_file):
        df_existing = pd.read_csv(output_file)
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
    else:
        df_combined = df_new

    df_combined.drop_duplicates(subset=["company", "title"], inplace=True)
    df_combined.sort_values("match_score", ascending=False, inplace=True)
    df_combined.to_csv(output_file, index=False)
    return df_combined


# ── MAIN ────────────────────────────────────────────────────────

def main():
    print("=" * 50)
    print("  JOB SCRAPER — LinkedIn + Naukri")
    print(f"  Role    : {SEARCH_ROLE}")
    print(f"  Location: {SEARCH_LOCATION}")
    print(f"  Browser : {BROWSER.upper()}")
    print("=" * 50)

    all_jobs = []

    try:
        linkedin_jobs = scrape_linkedin(SEARCH_ROLE, SEARCH_LOCATION, LINKEDIN_PAGES)
        all_jobs.extend(linkedin_jobs)
    except Exception as e:
        print(f"⚠️  LinkedIn scraper error: {e}")

    try:
        naukri_jobs = scrape_naukri(SEARCH_ROLE, SEARCH_LOCATION, NAUKRI_PAGES)
        all_jobs.extend(naukri_jobs)
    except Exception as e:
        print(f"⚠️  Naukri scraper error: {e}")

    if not all_jobs:
        print("\n❌ No jobs scraped. Check your internet or try again.")
        return

    df = save_jobs(all_jobs, OUTPUT_FILE)

    print("\n" + "=" * 50)
    print(f"  ✅ DONE!")
    print(f"  Total jobs saved : {len(df)}")
    print(f"  Good matches (4+): {len(df[df['match_score'] >= 4])}")
    print(f"  Saved to         : {OUTPUT_FILE}")
    print("=" * 50)

    print("\n🏆 TOP 10 BEST MATCHES:\n")
    top = df[df["match_score"] >= 4].head(10)
    for _, row in top.iterrows():
        print(f"  {row['title']} @ {row['company']}")
        print(f"  Score: {row['match_score']} | Source: {row['source']}")
        print(f"  Link : {row['apply_link']}")
        print()


if __name__ == "__main__":
    main()