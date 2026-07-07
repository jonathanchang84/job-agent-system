import streamlit as st
import pandas as pd
import os
from supabase import create_client
from cv_manager import read_docx
from run_full_pipeline import run_pipeline
import subprocess

# Ensure page configuration is set first
st.set_page_config(page_title="Job Application Agent", layout="wide", page_icon="🚀")

# Initialize Supabase
@st.cache_resource
def init_supabase():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        st.error("Missing Supabase credentials in environment variables.")
        return None
    return create_client(url, key)

supabase = init_supabase()

st.title("🚀 Job Application Agent")

# ==========================================
# SIDEBAR: AUTOMATION ENGINE
# ==========================================
st.sidebar.header("Automation Engine")

# Button 1: Pull New Jobs (Runs your search engine scraper script)
if st.sidebar.button("🔍 1. Scrape & Pull New Jobs"):
    with st.spinner("Activating scraper network and Gemini search queries..."):
        try:
            # Executes search_engine.py as a background subprocess
            result = subprocess.run(["python", "search_engine.py"], capture_output=True, text=True)
            if result.returncode == 0:
                st.sidebar.success("Scraper executed successfully! Data refreshed.")
                st.rerun()
            else:
                st.sidebar.error(f"Scraper error:\n{result.stderr}")
        except Exception as e:
            st.sidebar.error(f"Failed to trigger scraper script: {e}")

# Button 2: Batch Tailor Assets
if st.sidebar.button("🤖 2. Batch Update Missing Assets"):
    with st.spinner("AI is batch processing pipeline tasks..."):
        try:
            count = run_pipeline()
            st.sidebar.success(f"Generated tailored assets for {count} jobs.")
            st.rerun()  
        except Exception as e:
            st.sidebar.error(f"Pipeline execution halted: {e}")

st.sidebar.markdown("---")

# ==========================================
# SIDEBAR: PUSH / UPLOAD MASTER CV
# ==========================================
st.sidebar.header("Profile Administration")
uploaded_file = st.sidebar.file_uploader("Upload Master CV (.docx)", type=["docx"])

if uploaded_file is not None:
    if st.sidebar.button("💾 Push Master CV to Database"):
        with st.spinner("Parsing and syncing profile data..."):
            try:
                # Read text using your cv_manager utility
                # Write to a temporary file so python-docx can process it
                with open("temp_master_cv.docx", "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                cv_text = read_docx("temp_master_cv.docx")
                
                # Push/Upsert into your 'user_profile' table at ID 1
                payload = {"id": 1, "master_cv_text": cv_text}
                supabase.table("user_profile").upsert(payload).execute()
                
                st.sidebar.success("Master CV pushed and synced successfully!")
                
                # Clean up temp file
                if os.path.exists("temp_master_cv.docx"):
                    os.remove("temp_master_cv.docx")
            except Exception as e:
                st.sidebar.error(f"Failed to push CV: {e}")

# ==========================================
# MAIN DASHBOARD VISUALS
# ==========================================
st.header("📋 Application Dashboard")

if supabase:
    try:
        response = supabase.table("job_tracker").select("*").execute()
        data = response.data if response.data else []
        df = pd.DataFrame(data)
    except Exception as e:
        st.error(f"Failed to fetch data from Supabase: {e}")
        df = pd.DataFrame()
else:
    df = pd.DataFrame()

if not df.empty:
    # Ensure all required fallback columns exist in the DataFrame dynamically
    for col in ["company_name", "role_title", "job_title", "status", "source", "job_url", "job_description", "tailored_cv"]:
        if col not in df.columns:
            df[col] = None

    # Merge job_title into role_title column if necessary
    if "job_title" in df.columns:
        df["role_title"] = df["role_title"].fillna(df["job_title"])

    display_columns = ["company_name", "role_title", "status", "source", "job_url"]
    
    # Selection Mode tracking via Streamlit state
    event = st.dataframe(
        df[display_columns], 
        use_container_width=True,
        selection_mode="single-row", 
        on_select="rerun"
    )

    # Detailed Context Drilldown
    if event and hasattr(event, "selection") and event.selection.get("rows"):
        selected_row_index = event.selection["rows"][0]
        job = df.iloc[selected_row_index]
        
        st.markdown("---")
        st.subheader(f"🔍 Deep-Dive Details for: {job.get('company_name') or 'Unknown Enterprise'}")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Role:** {job.get('role_title') or 'N/A'}")
            st.write(f"**Current Pipeline Status:** `{job.get('status') or 'N/A'}`")
        with col2:
            st.write(f"**Platform Source:** {job.get('source') or 'N/A'}")
            if job.get('job_url'):
                st.write(f"**Job URL:** [View Original Posting]({job.get('job_url')})")
                
        desc_col, ai_col = st.columns(2)
        with desc_col:
            st.markdown("### 📝 Target Job Description")
            st.info(job.get('job_description') or "No description saved.")
            
        with ai_col:
            st.markdown("### ✨ Tailored AI CV Output")
            tailored_output = job.get('tailored_cv')
            if tailored_output:
                st.text_area("Generated Document Content", value=tailored_output, height=400)
            else:
                st.warning("No custom assets generated for this target position yet. Hit 'Batch Update Missing Assets' on the sidebar to build it.")
else:
    st.info("The application pipeline is currently empty. Use the sidebar buttons to pull positions or upload a Master CV.")