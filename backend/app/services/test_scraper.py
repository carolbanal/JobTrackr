import os
from scrape_jobs import scrape_indeed_jobs, scrape_onlinejobs_ph
from supabase import create_client, Client
from dotenv import load_dotenv
import time

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise ValueError("❌ Supabase environment variables (SUPABASE_URL or SUPABASE_ANON_KEY) are not set.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

def save_jobs_to_html(jobs, filename="job_debug.html"):
    with open(filename, "w", encoding="utf-8") as f:
        f.write("<html><head><title>Job Scraper Debug</title></head><body>")
        f.write("<h1>Scraped Job Listings</h1><ul>")
        for job in jobs:
            f.write("<li>")
            f.write(f"<strong>Title:</strong> {job['title']}<br>")
            f.write(f"<strong>Company:</strong> {job['company']}<br>")
            f.write(f"<strong>Location:</strong> {job['location']}<br>")
            f.write(f"<strong>Description:</strong> {job['description']}<br>")
            f.write(f"<strong>Source:</strong> {job['source']}<br>")
            f.write(f"<strong>Scraped At:</strong> {job['scraped_at']}<br>")
            f.write(f"<strong>Posted At:</strong> {job['posted_at']}<br>")
            f.write(f"<strong>Salary:</strong> {job.get('salary', '')}<br>")
            f.write(f"<strong>Link:</strong> <a href='{job.get('link', '#')}' target='_blank'>{job.get('link', '')}</a><br>")
            f.write("</li><hr>")
        f.write("</ul></body></html>")

def remove_duplicates(jobs):
    seen = set()
    unique_jobs = []
    for job in jobs:
        key = (job['title'].lower(), job['company'].lower(), job['location'].lower())
        if key not in seen:
            seen.add(key)
            unique_jobs.append(job)
    return unique_jobs

def job_exists(title, company, location):
    response = supabase.table("jobs") \
        .select("id") \
        .ilike("title", title) \
        .ilike("company", company) \
        .ilike("location", location) \
        .limit(1) \
        .execute()
    return len(response.data) > 0

def insert_jobs(jobs):
    for job in jobs:
        if job_exists(job["title"], job["company"], job["location"]):
            print(f"⚠️ Skipped duplicate: {job['title']} at {job['company']}")
            continue

        # Prepare data dict
        data = {
            "title": job["title"],
            "company": job["company"],
            "location": job["location"],
            "description": job["description"],
            "source": job["source"],
            "query": job.get("query"),
            "scraped_at": job.get("scraped_at"),
            "posted_at": job.get("posted_at"),
            "salary": job.get("salary"),
            "link": job.get("link")
        }

        # Convert datetime objects to ISO 8601 strings
        if data.get("scraped_at") and hasattr(data["scraped_at"], "isoformat"):
            data["scraped_at"] = data["scraped_at"].isoformat()
        if data.get("posted_at") and hasattr(data["posted_at"], "isoformat"):
            data["posted_at"] = data["posted_at"].isoformat()

        try:
            response = supabase.table("jobs").insert(data).execute()
            if not response.data:
                print(f"❌ Failed to insert job: {data['title']} at {data['company']}")
            else:
                print(f"✅ Inserted job: {data['title']} at {data['company']}")
        except Exception as e:
            print(f"❌ Error inserting job: {data['title']} at {data['company']} — {e}")


if __name__ == "__main__":
    queries = [
        "data scientist",
        "data engineer",
        "data analyst",
        "machine learning engineer",
        "business intelligence analyst",
    ]

    all_jobs = []
    print("Scraping jobs from Indeed and OnlineJobs.ph...")

    for q in queries:
        print(f"\n🔍 Query: {q}")

        # Indeed
        indeed_jobs = scrape_indeed_jobs(query=q, limit=10)
        for job in indeed_jobs:
            job["query"] = q
        all_jobs.extend(indeed_jobs)

        # OnlineJobs.ph
        online_jobs = scrape_onlinejobs_ph(query=q, limit=10)
        for job in online_jobs:
            job["query"] = q
        all_jobs.extend(online_jobs)

        time.sleep(1)  # ✅ Add sleep between queries to reduce load

    print(f"\nTotal jobs before deduplication: {len(all_jobs)}")
    all_jobs = remove_duplicates(all_jobs)
    print(f"Total unique jobs: {len(all_jobs)}")

    save_jobs_to_html(all_jobs)
    print(f"✅ Saved to job_debug.html")

    insert_jobs(all_jobs)

    print(f"🏁 Finished scraping and inserting {len(all_jobs)} unique jobs.")
