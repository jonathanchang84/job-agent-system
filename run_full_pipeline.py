import json
import os
from google import genai
from supabase import create_client

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
ai_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def run_pipeline():
    # Fetch Master CV
    profile = supabase.table("user_profile").select("master_cv_text").eq("id", 1).execute()
    master_cv = profile.data[0]['master_cv_text'] if profile.data else ""
    
    # Fetch jobs that need assets (where augmented_cv_text is NULL)
    jobs = supabase.table("job_tracker").select("*").is_("augmented_cv_text", "null").execute().data
    if not jobs: return

    # Single Prompt for all jobs
    prompt = f"CV: {master_cv}\n\nJobs to process: {json.dumps(jobs)}\n\nReturn a JSON object where keys are the job IDs and values contain 'augmented_cv', 'cover_letter', and 'pitch'."
    
    response = ai_client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
    results = json.loads(response.text.strip().replace("```json", "").replace("```", ""))
    
    for job_id, assets in results.items():
        supabase.table("job_tracker").update({
            "augmented_cv_text": assets["augmented_cv"],
            "tailored_cover_letter": assets["cover_letter"],
            "tailored_pitch": assets["pitch"],
            "status": "Ready"
        }).eq("id", int(job_id)).execute()

if __name__ == "__main__":
    run_pipeline()