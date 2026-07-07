import os
import json
from dotenv import load_dotenv
from google import genai
from supabase import create_client

# Force-load local configuration parameters
load_dotenv(override=True)

# Initialize Supabase Client
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# Initialize Gemini Client
ai_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Your Master CV Context
MASTER_CV = """
JONATHAN CHANG
Director - Crew Product Lead (Real Estate Finance) at UBS
Executive Summary: 10+ years in Financial Services product leadership. Expert in Product Strategy, 
Warehouse Lending, Mortgage Securities, and Core Banking Agile transformations.

Key Experience:
- UBS: Leading product teams to overhaul Real Estate Finance architectures and ML-driven risk validation tools.
- HSBC: Managed core commercial banking cross-border payment rails and asset backed security infrastructure.
Skills: Agile Frameworks, Financial Modeling, AI/ML Product Integration, Stakeholder Management, UK Regulatory Compliance.
"""

def fetch_discovered_jobs():
    """Retrieves all rows that have been discovered but not yet optimized by AI."""
    try:
        # Corrected syntax: .select() must come before .eq()
        response = supabase.table("job_tracker").select("*").eq("status", "Discovered").execute()
        return response.data or []
    except Exception as e:
        print(f"Error fetching records: {e}")
        return []

def augment_cv_and_assets(role_title, company_name):
    """Instructs Gemini to adapt the Master CV and build customized cover text."""
    
    prompt = f"""
    You are an elite executive talent agent. Your task is to augment a Master CV to perfectly align with a target job specification without inventing false historical data.

    Master CV Source of Truth:
    {MASTER_CV}

    Target Position: {role_title} at {company_name}

    Perform the following optimizations:
    1. Re-prioritize bullet points in the CV to match the high-priority requirements of the job.
    2. Subtle adjustment of phrasing to incorporate key corporate banking, real estate finance, or technical terminology matching the target role title.
    3. Draft a tailored cover letter and a direct pitch message.

    Return your response ONLY as a raw, single JSON block matching this structural format exactly. Do not include markdown formatting or backticks:
    {{
        "augmented_cv": "The complete rewritten text of the CV optimized for this role...",
        "cover_letter": "A concise 3-paragraph executive cover letter...",
        "pitch": "A compelling short outreach pitch..."
    }}
    """

    try:
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        clean_text = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(clean_text)
    except Exception as e:
        print(f"Error executing AI augmentation suite: {e}")
        return None

def run_pipeline():
    jobs = fetch_discovered_jobs()
    if not jobs:
        print("Pipeline clear. No new 'Discovered' roles require processing.")
        return

    print(f"Beginning optimization execution for {len(jobs)} active leads...")
    
    for job in jobs:
        job_id = job['id']
        title = job['role_title']
        company = job['company_name']

        print(f"-> Processing target alignment: {title} at {company}...")
        payload = augment_cv_and_assets(title, company)

        if payload:
            try:
                supabase.table("job_tracker").update({
                    "original_cv_text": MASTER_CV,
                    "augmented_cv_text": payload.get("augmented_cv"),
                    "tailored_cover_letter": payload.get("cover_letter"),
                    "tailored_pitch": payload.get("pitch"),
                    "status": "Ready to Apply"
                }).eq("id", job_id).execute()
                print(f"   Success: Augmented CV and application assets staged for ID {job_id}")
            except Exception as e:
                print(f"   Failed to write assets back to database: {e}")

if __name__ == "__main__":
    run_pipeline()