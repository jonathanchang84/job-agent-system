import os
import json
import pandas as pd
from google import genai
from jobspy import scrape_jobs
from supabase import create_client

# Safely look for dotenv if it's there; if not, ignore it on Streamlit Cloud
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass

# Client Configurations (Pulls directly from Streamlit Secrets or Environment)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize Gemini client safely
if GEMINI_API_KEY:
    ai_client = genai.Client(api_key=GEMINI_API_KEY)
else:
    ai_client = genai.Client()  # Falls back to standard client routing

try:
    if SUPABASE_URL and SUPABASE_KEY:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    else:
        supabase = None
except Exception:
    supabase = None

CV_PROFILE = """
Jonathan Chang - Dartford, UK
Director - Crew Product Lead (Real Estate Finance) at UBS.
Expertise: 10+ years in financial services, Product Strategy, AI/ML integrations, 
Warehouse Lending, Securities, Mortgages, Core Banking, Agile Transformation.
"""

def generate_search_queries():
    prompt = f"""
    Based on this executive candidate summary: {CV_PROFILE}
    Identify the top 3 most relevant, high-paying job title strings to search for on UK job boards.
    Return ONLY a JSON array of strings. Do not include markdown formatting or backticks.
    """
    try:
        response = ai_client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        clean_text = response.text.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(clean_text)
    except Exception:
        return ["Director of Product", "Head of Product", "Product Lead"]

def execute_uk_job_search(queries):
    all_results = []
    for query in queries:
        try:
            jobs = scrape_jobs(
                site_name=["linkedin", "indeed", "zip_recruiter"],
                search_term=query,
                location="United Kingdom",
                results_per_site=10,
                hours_old=48, 
                country_inference="uk"
            )
            if not jobs.empty:
                all_results.append(jobs)
        except Exception:
            pass
            
    if all_results:
        return pd.concat(all_results, ignore_index=True)
    return pd.DataFrame()

def save_matches_to_supabase(df):
    if not supabase:
        return
    for _, row in df.iterrows():
        url = row.get('job_url') or row.get('url')
        if not url:
            continue
        try:
            duplicate_check = supabase.table("job_tracker").select("id").eq("job_url", url).execute()
            if not duplicate_check.data:
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