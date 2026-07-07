import os
import json
import pandas as pd
from dotenv import load_dotenv
from google import genai
from jobspy import scrape_jobs
from supabase import create_client

# Force-reload environment variables directly from the file
load_dotenv(override=True)

# Client Configurations
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

ai_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    print(f"Warning: Could not initialize Supabase client: {e}")
    supabase = None

# Candidate executive summary used to guide the search engine
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
            model="gemini-2.5-flash",
            contents=prompt
        )
        # Handle structural cleaning if the model accidentally returns markdown wrappers
        clean_text = response.text.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(clean_text)
    except Exception as e:
        print(f"Error generating search targets: {e}")
        return ["Director of Product", "Head of Product", "Product Lead"]

def execute_uk_job_search(queries):
    """Triggers JobSpy across LinkedIn, Indeed, and ZipRecruiter for UK positions."""
    all_results = []
    
    for query in queries:
        print(f"🔍 Scraping listings for: '{query}'...")
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
        except Exception as e:
            print(f"Error scraping query '{query}': {e}")
            
    if all_results:
        return pd.concat(all_results, ignore_index=True)
    return pd.DataFrame()

def save_matches_to_supabase(df):
    """Filters duplicates and pushes clean matches into the Supabase database."""
    if not supabase:
        print("Error: Supabase client is uninitialized.")
        return

    count = 0
    for _, row in df.iterrows():
        url = row.get('job_url') or row.get('url')
        if not url:
            continue
            
        try:
            # FIX: Removed the errant backslash character from the string matching criteria
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
                count += 1
        except Exception as e:
            print(f"Could not check or save row to Supabase: {e}")
            
    if count > 0:
        print(f"Successfully processed and stored {count} pristine new opportunities in Supabase.")

if __name__ == "__main__":
    print("Step 1: Consulting Gemini for strategic search targets...")
    target_queries = generate_search_queries()
    print(f"Targeting parameters set to: {target_queries}")
    
    print("\nStep 2: Activating scraper network...")
    raw_listings_df = execute_uk_job_search(target_queries)
    
    if not raw_listings_df.empty:
        print("\nStep 3: Streaming clean matches into your cloud dashboard...")
        save_matches_to_supabase(raw_listings_df)
    else:
        print("\nNo new entries detected across platforms in this 48-hour window.")