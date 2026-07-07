import time
import os
import streamlit as st
from google import genai
from google.genai.errors import APIError
from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
ai_client = genai.Client()

def generate_asset_with_retry(prompt, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = ai_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            return response.text
        except APIError as e:
            if e.code == 429:
                wait_time = (2 ** attempt) + 2
                time.sleep(wait_time)
            else:
                raise e
    raise Exception("❌ Gemini API Limit Reached.")

def run_pipeline():
    response = supabase.table("job_tracker").select("*").execute()
    jobs = response.data if response.data else []
    
    profile_resp = supabase.table("user_profile").select("master_cv_text").eq("id", 1).execute()
    master_cv = profile_resp.data[0]['master_cv_text'] if profile_resp.data else ""

    if not master_cv:
        st.error("Pipeline stopped: Master CV is empty inside the database profile.")
        return 0

    success_count = 0
    for job in jobs:
        raw_desc = job.get('job_description', '')
        if not raw_desc or len(str(raw_desc).strip()) < 10:
            continue

        role_title = job.get('role_title') or job.get('job_title') or 'Executive Position'
        company = job.get('company_name') or 'Target Enterprise'

        cv_prompt = f"""
        You are an elite executive career coach. Tailor the following Master CV text perfectly to match the target position.
        Emphasize leadership metrics, cross-functional execution, and direct capability mapping.
        
        [Target Role]: {role_title} at {company}
        [Context/Spec]: {raw_desc}
        [Master CV Profile]: {master_cv}
        """
        
        cl_prompt = f"""
        Write a compelling, high-impact executive Cover Letter matching this candidate's Master CV to the target position.
        Keep it to one page, outcome-focused, and address it to the hiring team at {company}.
        
        [Target Role]: {role_title} at {company}
        [Context/Spec]: {raw_desc}
        [Master CV Profile]: {master_cv}
        """
        
        try:
            tailored_cv = generate_asset_with_retry(cv_prompt)
            time.sleep(1.0)
            tailored_cl = generate_asset_with_retry(cl_prompt)
            
            supabase.table("job_tracker").update({
                "tailored_cv": tailored_cv,
                "tailored_cover_letter": tailored_cl,
                "status": "Ready to Apply"
            }).eq("id", job["id"]).execute()
            
            success_count += 1
            time.sleep(1.0)
        except Exception as e:
            st.error(f"Error compiling assets for {company}: {e}")
            time.sleep(2.0)
            continue

    return success_count