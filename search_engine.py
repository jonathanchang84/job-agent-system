import os
import json
import pandas as pd
from google import genai
from jobspy import scrape_jobs
from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    ai_client = genai.Client(api_key=GEMINI_API_KEY)
else:
    ai_client = genai.Client()

try:
    if SUPABASE_URL and SUPABASE_KEY:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    else:
        supabase = None
except Exception:
    supabase = None

def generate_search_queries():
    try:
        profile_resp = supabase.table("user_profile").select("master_cv_text").eq("id", 1).execute()
        cv_context = profile_resp.data[0]["master_cv_text"] if profile_resp.data else "Executive Product Leader"
    except Exception:
        cv_context = "Executive Product Leader"

    prompt = f"""
    Based on this candidate background: {cv_context[:1000]}
    Identify the top 3 most relevant high-level job search strings for UK job boards (e.g., 'Director of Product').
    Return ONLY a raw JSON array of strings. Do not include markdown or backticks.
    """
    try:
        response = ai_client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        clean_text = response.text.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(clean_text)
    except Exception:
        return ["Director of Product", "Head of Product"]

def execute_uk_job_search(queries):
    all_results = []
    for query in queries:
        try:
            # CRITICAL: Added linkedin_fetch_description=True to automate full description gathering
            jobs = scrape_jobs(
                site_name=["linkedin", "indeed", "zip_recruiter"],
                search_term=query,
                location="United Kingdom",
                results_per_site=5,
                hours_old=72, 
                country_inference="uk",
                linkedin_fetch_description=True  # Force fetching full descriptions automatically
            )
            if not jobs.empty:
                all_results.append(jobs)
        except Exception:
            pass
            
    if all_results:
        return pd.concat(all_results, ignore_index=True)
    return pd.DataFrame()

def save_matches_to_supabase(df):
    if not supabase or df.empty:
        return
    for _, row in df.iterrows():
        url = row.get('job_url') or row.get('url')
        if not url:
            continue
        try:
            duplicate_check = supabase.table("job_tracker").select("id").eq("job_url", url).execute()
            if not duplicate_check.data:
                # Store the full scraped description directly
                payload = {
                    "company_name": row.get('company', 'Unknown Enterprise'),
                    "role_title": row.get('title', 'Product Position'),
                    "job_url": url,
                    "status": "Discovered",
                    "source": row.get('source_platform', 'LINKEDIN'),
                    "job_description": row.get('description', '') 
                }
                supabase.table("job_tracker").insert(payload).execute()
        except Exception:
            pass