import os
from dotenv import load_dotenv
import streamlit as st
import pandas as pd
from supabase import create_client

# Force-load configuration
load_dotenv(override=True)

st.set_page_config(page_title="Executive Job Agent", page_icon="💼", layout="wide")

# Setup Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL") or st.secrets.get("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def fetch_tracked_jobs():
    try:
        response = supabase.table("job_tracker").select("*").execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()

st.title("💼 Executive Job Agent Pipeline")
df = fetch_tracked_jobs()

if df.empty:
    st.info("No jobs found. Run `python3 search_engine.py` to find leads and `python3 agent_tailor.py` to tailor them.")
else:
    # Sidebar Filters
    status_filter = st.sidebar.selectbox("Filter by Status", ["All"] + sorted(df["status"].unique().tolist()))
    if status_filter != "All":
        df = df[df["status"] == status_filter]

    # Two-column layout
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.subheader("Job Opportunities")
        event = st.dataframe(
            df[["id", "company_name", "role_title", "status"]],
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single"
        )

    with col_right:
        st.subheader("AI Asset Inspector")
        selected_rows = event.get("selection", {}).get("rows", [])
        
        if selected_rows:
            job = df.iloc[selected_rows[0]]
            st.markdown(f"### {job['role_title']} at {job['company_name']}")
            
            # Use tabs for clean organization
            tab1, tab2, tab3 = st.tabs(["📄 Augmented CV", "✉️ Cover Letter", "🔗 Pitch"])
            
            with tab1:
                st.text_area("Optimized Resume", job.get("augmented_cv_text", "No CV data yet"), height=300)
            with tab2:
                st.text_area("Cover Letter", job.get("tailored_cover_letter", "No letter generated"), height=300)
            with tab3:
                st.text_area("Outreach Pitch", job.get("tailored_pitch", "No pitch generated"), height=150)
            
            if st.button("Mark as Applied ✅"):
                supabase.table("job_tracker").update({"status": "Applied"}).eq("id", int(job['id'])).execute()
                st.rerun()
        else:
            st.info("Select a row in the table to view the AI-tailored assets.")