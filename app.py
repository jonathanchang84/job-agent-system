import streamlit as st
import pandas as pd
import os
from supabase import create_client
from run_full_pipeline import run_pipeline

# Ensure page configuration is explicitly set first
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

# Sidebar Action Hub
st.sidebar.header("Automation Engine")
if st.sidebar.button("🤖 Batch Update Missing Assets"):
    with st.spinner("AI is batch processing pipeline tasks..."):
        try:
            count = run_pipeline()
            st.sidebar.success(f"Generated tailored assets for {count} jobs.")
            st.rerun()  # Instantly refresh table UI components
        except Exception as e:
            st.sidebar.error(f"Pipeline execution halted: {e}")

# Data Fetching Logic
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

# Dashboard UI Rendering
st.header("📋 Application Dashboard")

if not df.empty:
    # Essential cleanup for visual layout
    display_columns = ["company_name", "role_title", "status", "source", "job_url"]
    # Ensure columns exist before filtering display
    actual_columns = [col for col in display_columns if col in df.columns]
    
    # Selection Mode utilizing up-to-date Streamlit interactive state
    event = st.dataframe(
        df[actual_columns], 
        use_container_width=True,
        selection_mode="single-row", 
        on_select="rerun"
    )

    # Context Drilldown Rendering Check
    if event and hasattr(event, "selection") and event.selection.get("rows"):
        selected_row_index = event.selection["rows"][0]
        # Match filtered row index back to source row in our master dataframe
        job = df.iloc[selected_row_index]
        
        st.markdown("---")
        st.subheader(f"🔍 Deep-Dive Details for: {job.get('company_name', 'Unknown Enterprise')}")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Role:** {job.get('role_title', 'N/A')}")
            st.write(f"**Current Pipeline Status:** `{job.get('status', 'N/A')}`")
        with col2:
            st.write(f"**Platform Source:** {job.get('source', 'N/A')}")
            if job.get('job_url'):
                st.write(f"**Job URL:** [View Original Posting]({job.get('job_url')})")
                
        # Split layout for Job Description vs AI Output
        desc_col, ai_col = st.columns(2)
        with desc_col:
            st.markdown("### 📝 Target Job Description")
            st.info(job.get('job_description') or "No full description saved.")
            
        with ai_col:
            st.markdown("### ✨ Tailored AI CV Output")
            tailored_output = job.get('tailored_cv')
            if tailored_output:
                st.text_area("Generated Document Content", value=tailored_output, height=400)
            else:
                st.warning("No custom assets generated for this target position yet. Hit 'Batch Update Missing Assets' on the sidebar to build it.")
else:
    st.info("The application pipeline is currently empty. Run your scraper or input manual tracking records into Supabase to begin.")