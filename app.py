import streamlit as st
import pandas as pd
import os
from supabase import create_client
from cv_manager import read_docx
from run_full_pipeline import run_pipeline

# Ensure page configuration is set first
st.set_page_config(page_title="Job Application Agent", layout="wide")

# Initialize Supabase (Use st.cache_resource or simple initialization)
@st.cache_resource
def init_supabase():
    url = os.getenv("SUPABASE_URL")
    key = os-getenv("SUPABASE_KEY")
    if not url or not key:
        st.error("Missing Supabase credentials in environment variables.")
        return None
    return create_client(url, key)

supabase = init_supabase()

st.title("🚀 Job Application Agent")

# Sidebar Actions
st.sidebar.header("Automation Engine")
if st.sidebar.button("🤖 2. Batch Update Missing Assets"):
    with st.spinner("AI is batch processing..."):
        try:
            count = run_pipeline()
            st.sidebar.success(f"Generated assets for {count} jobs.")
            st.rerun()  # Refresh data after pipeline run
        except Exception as e:
            st.sidebar.error(f"Pipeline failed: {e}")

# Data Fetching
if supabase:
    try:
        response = supabase.table("job_tracker").select("*").execute()
        # Fallback to empty list if no data returned
        data = response.data if response.data else []
        df = pd.DataFrame(data)
    except Exception as e:
        st.error(f"Failed to fetch data from Supabase: {e}")
        df = pd.DataFrame()
else:
    df = pd.DataFrame()

# Dashboard Rendering
st.header("📋 Application Dashboard")

if not df.empty:
    # Key Fix: Explicitly define selection parameters according to recent Streamlit spec
    # 'on_select="rerun"' captures interaction and triggers a script rerun automatically
    event = st.dataframe(
        df, 
        use_container_width=True,
        selection_mode="single-row", 
        on_select="rerun"
    )

    # Robust conditional check to avoid NameError or AttributeError
    if event and hasattr(event, "selection") and event.selection.get("rows"):
        selected_row_index = event.selection["rows"][0]
        job = df.iloc[selected_row_index]
        
        # UI Container for selected job details
        st.markdown("---")
        st.subheader(f"🔍 Details for: {job.get('company_name', 'Unknown Company')}")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(**Role:** {job.get('job_title', 'N/A')})
            st.write(**Status:** {job.get('status', 'N/A')})
        with col2:
            st.write(**Applied Date:** {job.get('applied_date', 'N/A')})
            
        # TODO: Insert your CV/Cover Letter Display and Download logic here
        
else:
    st.info("No job applications found in the tracker. Add some records to Supabase to get started!")