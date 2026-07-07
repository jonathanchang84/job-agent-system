import os
import streamlit as st
import pandas as pd
from supabase import create_client
from cv_manager import read_docx
from google import genai

# Setup
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
ai_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

st.set_page_config(page_title="Executive Job Agent", layout="wide")

def run_augmentation_logic(job_id, role_title, company_name):
    """Internal function to process AI logic triggered by UI."""
    profile = supabase.table("user_profile").select("master_cv_text").eq("id", 1).execute()
    if not profile.data:
        return None
    
    master_cv = profile.data[0]['master_cv_text']
    prompt = f"Augment this CV: {master_cv} for {role_title} at {company_name}. Return JSON with 'augmented_cv', 'cover_letter', 'pitch'."
    
    response = ai_client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
    return response.text # You would parse this as JSON

# --- UI Sections ---
menu = st.sidebar.radio("Navigation", ["Dashboard", "Manage Master CV"])

if menu == "Manage Master CV":
    # ... (Keep your existing CV Upload logic here)
    pass

else:
    st.title("💼 Executive Pipeline")
    df = pd.DataFrame(supabase.table("job_tracker").select("*").execute().data)
    
    # ... (Keep your table view logic here)
    
    if "selected_job" in st.session_state:
        job = st.session_state.selected_job
        
        # ADD THIS BUTTON
        if st.button("🚀 Generate Tailored Assets"):
            with st.spinner("AI is crafting your application..."):
                assets = run_augmentation_logic(job['id'], job['role_title'], job['company_name'])
                # Logic to update database and st.rerun()
                st.success("Assets generated!")