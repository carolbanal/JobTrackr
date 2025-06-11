import os
from serpapi import GoogleSearch
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import urllib.parse
from datetime import datetime, timezone
from dateutil import parser
from dateparser import parse as fuzzy_parse 

load_dotenv()

def scrape_indeed_jobs(query="python developer", location="Philippines", limit=10):
    api_key = os.getenv("SERPAPI_KEY")
    if not api_key:
        raise ValueError("SERPAPI_KEY is not set in environment variables")

    search = GoogleSearch({
        "engine": "google_jobs",
        "q": query,
        "location": location,
        "api_key": api_key,
    })

    results = search.get_dict()

    if "jobs_results" not in results:
        print(f"❌ No jobs found or SerpAPI error for query: {query}")
        return []

    jobs = results["jobs_results"][:limit]

    cleaned = []
    for job in jobs:
        posted_raw = job.get("detected_extensions", {}).get("posted_at")
        try:
            posted_at = fuzzy_parse(posted_raw).astimezone(timezone.utc) if posted_raw else None
        except:
            posted_at = None

        # Get direct apply link from apply_options if available
        apply_options = job.get("apply_options", [])
        if apply_options and isinstance(apply_options, list):
            # Take the first apply option's link as the direct link
            direct_link = apply_options[0].get("link")
        else:
            # Fallback to your previous search_url if no apply link found
            direct_link = "https://www.google.com/search?q=" + urllib.parse.quote(f"{job.get('title', '')} {job.get('company', '')} site:indeed.com")

        cleaned.append({
            "title": job.get("title", "N/A"),
            "company": job.get("company_name", "N/A"),
            "location": job.get("location", "N/A"),
            "description": job.get("description", ""),
            "salary": job.get("detected_extensions", {}).get("salary", "N/A"),
            "source": "Indeed (via SerpAPI)",
            "link": direct_link,
            "scraped_at": datetime.now(timezone.utc),
            "posted_at": posted_at
        })

    return cleaned

def scrape_onlinejobs_ph(query="python", limit=10):
    encoded_query = urllib.parse.quote_plus(query)
    url = f"https://www.onlinejobs.ph/jobseekers/jobsearch?jobkeyword={encoded_query}"

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; JobTrackrBot/1.0; +http://jobtrackr.me)"
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to fetch OnlineJobs.ph page for query: {query}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    listings = soup.select("div.job-item")
    jobs = []

    for listing in listings[:limit]:
        title_tag = listing.select_one("div.job-title > a")
        company_tag = listing.select_one("div.job-employer")
        description_tag = listing.select_one("div.job-desc")
        salary_tag = listing.select_one("div.salary")

        link = f"https://www.onlinejobs.ph{title_tag['href']}" if title_tag and title_tag.get("href") else ""
        posted_raw = listing.get("data-temp-2")
        try:
            posted_at = parser.parse(posted_raw) if posted_raw else None
        except:
            posted_at = None

        jobs.append({
            "title": title_tag.text.strip() if title_tag else "N/A",
            "company": company_tag.text.strip() if company_tag else "N/A",
            "location": "Remote (OnlineJobs.ph)",
            "description": description_tag.text.strip() if description_tag else "",
            "salary": salary_tag.text.strip() if salary_tag else "N/A",
            "source": "OnlineJobs.ph",
            "link": link,
            "scraped_at": datetime.now(timezone.utc),
            "posted_at": posted_at
        })

    return jobs
