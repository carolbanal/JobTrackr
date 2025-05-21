import os
from serpapi import GoogleSearch
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import urllib.parse

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
        cleaned.append({
            "title": job.get("title", "N/A"),
            "company": job.get("company_name", "N/A"),
            "location": job.get("location", "N/A"),
            "description": job.get("description", ""),
            "source": "Indeed (via SerpAPI)",
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
        location = "Remote (OnlineJobs.ph)"  # Default for this site

        jobs.append({
            "title": title_tag.text.strip() if title_tag else "N/A",
            "company": company_tag.text.strip() if company_tag else "N/A",
            "location": location,
            "description": description_tag.text.strip() if description_tag else "",
            "source": "OnlineJobs.ph",
        })

    return jobs

