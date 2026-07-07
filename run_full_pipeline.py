import json
import os
from google import genai
from supabase import create_client

# Initialize clients
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
API_KEY = os.getenv("GEMINI_API_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
ai_client = genai.Client(api_key=API_KEY)

def run_pipeline():
    # Fetch Master CV
    profile = supabase.table("user_profile").select("master_cv_text").eq("id", 1).execute()
    master_cv = profile.data[0]['master_cv_text'] if profile.data else ""
    
    # Fetch jobs that need assets
    jobs = supabase.table("job_tracker").select("id, role_title, company_name").is_("augmented_cv_text", "null").execute().data
    if not jobs: return 0

    # Build Prompt
    prompt = f"CV: {master_cv}\n\nJobs: {json.dumps(jobs)}\n\nReturn JSON map of id: {{augmented_cv, cover_letter, pitch}}."
    
    # Use 'gemini-1.5-flash' which is the standard stable alias
    response = ai_client.models.generate_content(
        model='gemini-1.5-flash', 
        contents=prompt
    )
    
    # Parse and Update
    results = json.loads(response.text.strip().replace("```json", "").replace("```", ""))
    
    for job_id, assets in results.items():
        supabase.table("job_tracker").update({
            "augmented_cv_text": assets["augmented_cv"],
            "tailored_cover_letter": assets["cover_letter"],
            "tailored_pitch": assets["pitch"],
            "status": "Ready"
        }).eq("id", int(job_id)).execute()
        
    return len(results)

if __name__ == "__main__":
    run_pipeline()