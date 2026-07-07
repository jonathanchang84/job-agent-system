import time
import os
import json
from google import genai
from google.genai.errors import APIError
from supabase import create_client
from docxtpl import DocxTemplate

# 1. INITIALIZE CLIENTS
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
ai_client = genai.Client()

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

def tailor_single_job(job_id):
    """
    Tailors a single job application by pulling candidate context, 
    generating JSON structures matching template_cv.docx, and compiling the file.
    """
    # Fetch job details
    job = supabase.table("job_tracker").select("*").eq("id", job_id).execute().data[0]
    
    # Fetch Master Profile text (Aligning with agent_tailor.py intention)
    profile_data = supabase.table("user_profile").select("master_cv_text").eq("id", 1).execute().data
    master_cv = profile_data[0]['master_cv_text'] if profile_data else "Jonathan Chang - Executive Summary"

    prompt = f"""
    You are an expert executive resume writer. 
    Tailor this Master CV background to fit the target Job Description.
    
    MASTER CV CONTEXT:
    {master_cv}
    
    TARGET JOB DESCRIPTION:
    Role: {job.get('role_title')} at {job.get('company_name')}
    Description Details: {job.get('job_description', 'N/A')}
    
    Format the output as a strict JSON object matching these specific docxtpl tag keys:
    {{
        "summary": "A highly targeted executive summary paragraph...",
        "skills": "Bullet-separated critical technical keywords matched to the description...",
        "experience": [
            {{
                "role": "Tailored Title or exact match matching profile",
                "dates": "Dates of employment",
                "company": "Company Name",
                "location": "Location",
                "description": "Tailored, high-impact achievements matching the target keywords."
            }}
        ]
    }}
    
    Return ONLY pure JSON. Do not include markdown wraps or backticks.
    """
    
    # Call Gemini
    raw_json_text = generate_asset_with_retry(prompt)
    clean_json = raw_json_text.strip().replace("```json", "").replace("```", "")
    context_data = json.loads(clean_json)
    
    # Compile the Document using docxtpl
    template_path = "template_cv.docx"
    output_filename = f"Tailored_CV_{job_id}.docx"
    
    if os.path.exists(template_path):
        doc = DocxTemplate(template_path)
        doc.render(context_data)
        doc.save(output_filename)
        
        # Read file contents as bytes to store back or use in download pipelines
        with open(output_filename, "rb") as f:
            file_bytes = f.read()
            
        # Update database with tailored raw data structure
        supabase.table("job_tracker").update({
            "tailored_cv": json.dumps(context_data),
            "status": "Ready to Apply"
        }).eq("id", job_id).execute()
        
        return output_filename
    else:
        raise FileNotFoundError("Could not find template_cv.docx in project root.")

def run_pipeline():
    """
    Batch operational loop for automation workflows.
    """
    response = supabase.table("job_tracker").select("id").eq("status", "Discovered").execute()
    jobs_to_update = response.data if response.data else []
    
    success_count = 0
    for job in jobs_to_update:
        try:
            tailor_single_job(job["id"])
            success_count += 1
            time.sleep(2.0) # Compliance cooling spacer
        except Exception as e:
            print(f"❌ Error processing job ID {job.get('id')}: {e}")
            continue
            
    return success_count