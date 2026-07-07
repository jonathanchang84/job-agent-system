import os
import json
from dotenv import load_dotenv
from google import genai
from jobspy import scrape_jobs
import pandas as pd
from supabase import create_client

# Force-reload environment variables directly from the file
load_dotenv(override=True)

# Client Configurations
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

ai_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Create Supabase client safely
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    print(f"Warning: Could not initialize Supabase client: {e}")
    supabase = None

# Candidate profile snippet
CV_PROFILE = """
Jonathan Chang - Dartford, UK
Director - Crew Product Lead (Real Estate Finance) at UBS.
Expertise: 10+ years in financial services, Product Strategy, AI/ML integrations, 
Warehouse Lending, Securities, Mortgages, Core Banking, Agile Transformation.
"""

def generate_search_queries():
    """Uses Gemini to identify the exact top 3 high-yield target roles for your seniority."""
    prompt = f"""
    Based on this executive candidate summary:
    {CV_PROFILE}
    
    Identify the top 3 most relevant, high-paying job title strings to search for on UK job boards.
    Return ONLY a JSON array of strings. Do not include markdown formatting or backticks.
    Example: ["Director of Product", "Head of Product", "Product Lead"]
    """
    
    try:
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        clean_text = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(clean_text)
    except Exception:
        return ["Director of Product Banking", "Head of Product Wealth Management", "Product Lead Real Estate Finance"]

def execute_uk_job_search(target_titles):
    """Scrapes LinkedIn, Indeed, and Reed individually and tags them with their source platform."""
    found_jobs = []
    platforms = ["linkedin", "indeed", "reed"]
    
    for title in target_titles:
        for platform in platforms:
            print(f"Searching {platform.upper()} market for: '{title}'...")
            try:
                jobs = scrape_jobs(
                    site_name=[platform],
                    search_term=title,
                    location="London, United Kingdom",
                    results_per_sheet=8,
                    hours_old=48, 
                    country_tier="uk"
                )
                if not jobs.empty:
                    # Explicitly tag the source platform inside the dataframe
                    jobs['source_platform'] = platform.upper()
                    found_jobs.append(jobs)
                    print(f"-> Found {len(jobs)} matches on {platform.upper()}!")
            except Exception as e:
                print(f"-> Skipping {platform.upper()} for '{title}' due to network edge.")
            
    if found_jobs:
        return pd.concat(found_jobs, ignore_index=True)
    return pd.DataFrame()

def save_matches_to_supabase(df):
    """Pushes discovered leads safely into your tracker while avoiding duplicates."""
    if not supabase:
        print("Supabase client is not connected. Skipping database insertion.")
        return

    count = 0
    for _, row in df.iterrows():
        url = row.get('job_url', '')
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
                    "source": row.get('source_platform', 'LINKEDIN')  # Adds the source platform field
                }
                supabase.table("job_tracker").insert(payload).execute()
                count += 1
        except Exception as e:
            print(f"Could not check or save row to Supabase: {e}")
            break
            
    if count > 0:
        print(f"Successfully processed and stored {count} pristine new opportunities in Supabase.")

if __name__ == "__main__":
    print("Step 1: Consulting Gemini for strategic search targets...")
    queries = generate_search_queries()
    print(f"Targeting parameters set to: {queries}")
    
    print("\nStep 2: Activating scraper network...")
    raw_listings_df = execute_uk_job_search(queries)
    
    if not raw_listings_df.empty:
        print("\nStep 3: Streaming clean matches into your cloud dashboard...")
        save_matches_to_supabase(raw_listings_df)
    else:
        print("\nNo new entries detected across platforms in this 48-hour window.")