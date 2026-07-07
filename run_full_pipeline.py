import time
import os
from google import genai  # Modern google-genai SDK
from google.genai.errors import APIError
from supabase import create_client

# 1. INITIALIZE CLIENTS
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
ai_client = genai.Client() # Automatically picks up GEMINI_API_KEY from env

# 2. PASTE THE RETRY HELPER HERE (Top level of the file)
def generate_asset_with_retry(prompt, model_name="gemini-2.5-flash", max_retries=3):
    """Wraps the Gemini API call to catch 429 errors and wait."""
    for attempt in range(max_retries):
        try:
            response = ai_client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            return response.text
        except APIError as e:
            if e.code == 429:
                wait_time = (2 ** attempt) + 2
                print(f"⚠️ Rate limit (429). Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise e
    raise Exception("❌ Failed to generate asset after maximum retries.")

# 3. USE IT INSIDE YOUR MAIN PIPELINE FUNCTION
def run_pipeline():
    """
    This is the function app.py imports and triggers.
    """
    # Fetch rows from Supabase where assets are missing
    # (e.g., tailored_cv IS NULL or cover_letter IS NULL)
    response = supabase.table("job_tracker").select("*").is_("tailored_cv", "null").execute()
    jobs_to_update = response.data if response.data else []
    
    success_count = 0
    
    for job in jobs_to_update:
        # Construct your specific prompt using the job details
        prompt = f"Tailor a CV for a {job.get('job_title')} position at {job.get('company_name')} using this description: {job.get('job_description')}"
        
        try:
            # CALL THE RETRY HELPER HERE
            tailored_cv_text = generate_asset_with_retry(prompt)
            
            # ... (Your existing logic to parse text, generate .docx with docxtpl, and upload) ...
            
            # Update Supabase marking it complete
            supabase.table("job_tracker").update({"tailored_cv": tailored_cv_text}).eq("id", job["id"]).execute()
            
            success_count += 1
            
            # PASTE THE COOLDOWN PAUSE HERE (At the end of the loop iteration)
            time.sleep(1.5) 
            
        except Exception as e:
            print(f"❌ Error processing job ID {job.get('id')}: {e}")
            continue # Move to next job instead of crashing the entire batch
            
    return success_count