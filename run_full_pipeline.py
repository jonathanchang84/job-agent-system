import time
import os
from google import genai
from google.genai.errors import APIError
from supabase import create_client

# Initialize clients Safely
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
ai_client = genai.Client()

def generate_asset_with_retry(prompt, model_name="gemini-2.5-flash", max_retries=3):
    """Wraps the Gemini API call to catch 429 rate limit errors and back off."""
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
                print(f"⚠️ Rate limit hit (429). Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise e
    raise Exception("❌ Failed to generate asset after maximum retries.")

def run_pipeline():
    """Main loop function that processes jobs where tailored assets are missing."""
    # Fetch entries where tailored_cv is currently null
    response = supabase.table("job_tracker").select("*").is_("tailored_cv", "null").execute()
    jobs_to_update = response.data if response.data else []
    
    success_count = 0
    
    # Pull down the Master CV text for asset priming
    profile_resp = supabase.table("user_profile").select("master_cv_text").eq("id", 1).execute()
    master_cv = profile_resp.data[0]['master_cv_text'] if profile_resp.data else ""

    for job in jobs_to_update:
        job_description = job.get('job_description') or 'No description provided.'
        # Unified tracking fallback check for variable naming types
        role_title = job.get('role_title') or job.get('job_title') or 'Product Position'
        company = job.get('company_name') or 'Target Company'

        prompt = f"""
        You are an elite executive career coach. Tailor the following Master CV text perfectly to match the provided job description.
        Emphasize leadership metrics, exact methodology match, and technical execution.
        
        [Target Role]: {role_title} at {company}
        [Target Job Description]: {job_description}
        [Master CV Profile]: {master_cv}
        
        Return the customized CV fully structured and formatted nicely.
        """
        
        try:
            tailored_cv_text = generate_asset_with_retry(prompt)
            
            # Update data entry safely
            supabase.table("job_tracker").update({
                "tailored_cv": tailored_cv_text,
                "status": "Ready to Apply"
            }).eq("id", job["id"]).execute()
            
            success_count += 1
            time.sleep(1.5) # Anti-rate-throttling delay
            
        except Exception as e:
            print(f"❌ Error processing job ID {job.get('id')}: {e}")
            continue

    return success_count