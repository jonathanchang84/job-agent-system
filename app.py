import streamlit as st
import pandas as pd
import os
import json
from supabase import create_client
from cv_manager import read_docx
from run_full_pipeline import run_pipeline, tailor_single_job

# Ensure page configuration is set first
st.set_page_config(page_title="Job Application Agent", layout="wide")

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

# Sidebar - Main Core Actions
st.sidebar.header("Automation Control Room")
if st.sidebar.button("🤖 Run Job Discovery Scraper"):
    with st.spinner("Executing live UK job scrape..."):
        # Executes background workflow script directly
        os.system("python search_engine.py")
        st.sidebar.success("Scraper executed. Refreshing dashboard data!")
        st.rerun()

if st.sidebar.button("📦 Batch Tailor 'Discovered' Jobs"):
    with st.spinner("AI is processing unmapped leads..."):
        try:
            count = run_pipeline()
            st.sidebar.success(f"Successfully processed {count} jobs.")
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Pipeline failure: {e}")

# Data Fetching
if supabase:
    try:
        response = supabase.table("job_tracker").select("*").order("id", desc=True).execute()
        df = pd.DataFrame(response.data if response.data else [])
    except Exception as e:
        st.error(f"Database sync failed: {e}")
        df = pd.DataFrame()
else:
    df = pd.DataFrame()

# Dashboard View Layout
st.header("📋 Application Lead Management")

if not df.empty:
    # Render interactive data matrix
    event = st.dataframe(
        df[["id", "company_name", "role_title", "status", "source"]], 
        use_container_width=True,
        selection_mode="single-row", 
        on_select="rerun"
    )

    # Monitor Selection Matrix State Updates
    if event and hasattr(event, "selection") and event.selection.get("rows"):
        selected_row_index = event.selection["rows"][0]
        job = df.iloc[selected_row_index]
        job_id = int(job['id'])
        
        st.markdown("---")
        st.subheader(f"💼 Focused Lead Context: {job.get('role_title')} @ {job.get('company_name')}")
        
        # Display Core Context Meta Blocks
        meta_col1, meta_col2, meta_col3 = st.columns(3)
        with meta_col1:
            st.info(f"**Origin Platform:** {job.get('source', 'LINKEDIN')}")
        with meta_col2:
            st.warning(f"**Current Status:** {job.get('status', 'Discovered')}")
        with meta_col3:
            st.success(f"**Application URL:** [View External Posting]({job.get('job_url', '#')})")

        # Split Section view for analysis
        view_col1, view_col2 = st.columns(2)
        
        with view_col1:
            st.markdown("### 📝 Original Job Parameters")
            # Editable or viewer field for description metrics
            desc_text = job.get('job_description') or "No description saved yet. Paste one here to update."
            updated_desc = st.text_area("Job Description Data", value=desc_text, height=350)
            
            if st.button("💾 Save Description Updates", key=f"save_{job_id}"):
                supabase.table("job_tracker").update({"job_description": updated_desc}).eq("id", job_id).execute()
                st.success("Description details locked down successfully!")
                st.rerun()

        with view_col2:
            st.markdown("### 🛠️ AI Generation & Document Management")
            
            # Button to explicitly generate files for *just* this row
            if st.button("✨ Tailor Assets For This Position Only", key=f"tailor_{job_id}"):
                with st.spinner("Recalibrating CV structures via Gemini..."):
                    try:
                        file_output = tailor_single_job(job_id)
                        st.success(f"Successfully configured customized document assets: {file_output}")
                        st.rerun()
                    except Exception as err:
                        st.error(f"Asset optimization halted: {err}")

            st.markdown("---")
            # Render download block if data structures exist
            if job.get('tailored_cv'):
                st.markdown("#### ✅ Asset Status: Customized Output Ready")
                
                generated_file_name = f"Tailored_CV_{job_id}.docx"
                
                # Verify local file presence or check storage blocks
                if os.path.exists(generated_file_name):
                    with open(generated_file_name, "rb") as word_file:
                        st.download_button(
                            label="📥 Download Tailored Word Document (.docx)",
                            data=word_file,
                            file_name=f"{job.get('company_name').replace(' ', '_')}_Tailored_CV.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            key=f"dl_{job_id}"
                        )
                else:
                    st.warning("Data record states tailored assets exist, but the local workspace copy was purged. Re-run optimization above.")
            else:
                st.info("No generated assets mapped yet. Click 'Tailor Assets' above to create custom variations.")
else:
    st.info("No application leads tracked inside the primary pipeline workspace database.")