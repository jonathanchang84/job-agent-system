import streamlit as st
import pandas as pd
import os
from supabase import create_client
from cv_manager import read_docx
from run_full_pipeline import run_pipeline
import search_engine as engine

st.set_page_config(page_title="Job Application Agent", layout="wide", page_icon="🚀")

@st.cache_resource
def init_supabase():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if url and key:
        return create_client(url, key)
    return None

supabase = init_supabase()

st.title("🚀 Autonomous Job Application Agent")

# ==========================================
# SIDEBAR CONTROLS: THE AUTONOMOUS SWITCH
# ==========================================
st.sidebar.header("Agent Execution")

if st.sidebar.button("🔥 Run Fully Automated Pipeline"):
    status_box = st.sidebar.empty()
    
    with st.spinner("Executing pipeline context..."):
        try:
            status_box.info("⚡ Generating search targets using Gemini...")
            queries = engine.generate_search_queries()
            
            status_box.info(f"📡 Scraping listings and reading full text details for: {', '.join(queries)}")
            raw_df = engine.execute_uk_job_search(queries)
            
            if not raw_df.empty:
                status_box.info(f"💾 Securing {len(raw_df)} listings inside database...")
                engine.save_matches_to_supabase(raw_df)
                
                status_box.info("🤖 Chaining Engine: Running AI CV and Cover Letter optimization...")
                optimized_count = run_pipeline()
                st.sidebar.success(f"Complete! Added listings and optimized {optimized_count} asset profiles.")
            else:
                st.sidebar.warning("No new job openings found over the last window interval.")
            
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Pipeline error: {e}")

st.sidebar.markdown("---")
st.sidebar.header("Profile Administration")
uploaded_file = st.sidebar.file_uploader("Upload Master CV (.docx)", type=["docx"])
if uploaded_file and st.sidebar.button("💾 Push Master CV"):
    with open("temp_master_cv.docx", "wb") as f:
        f.write(uploaded_file.getbuffer())
    cv_text = read_docx("temp_master_cv.docx")
    supabase.table("user_profile").upsert({"id": 1, "master_cv_text": cv_text}).execute()
    st.sidebar.success("Master CV Synced!")
    st.rerun()

# ==========================================
# DASHBOARD RENDERING
# ==========================================
st.header("📋 Application Dashboard")

if supabase:
    try:
        response = supabase.table("job_tracker").select("*").execute()
        df = pd.DataFrame(response.data if response.data else [])
    except:
        df = pd.DataFrame()
else:
    df = pd.DataFrame()

if not df.empty:
    for col in ["company_name", "role_title", "status", "source", "job_url", "job_description", "tailored_cv", "tailored_cover_letter"]:
        if col not in df.columns:
            df[col] = None

    display_cols = ["company_name", "role_title", "status", "source", "job_url"]
    event = st.dataframe(df[display_cols], use_container_width=True, selection_mode="single-row", on_select="rerun")

    if event and hasattr(event, "selection") and event.selection.get("rows"):
        selected_index = event.selection["rows"][0]
        job = df.iloc[selected_index]
        
        st.markdown("---")
        st.subheader(f"🔍 Optimization Suite: {job.get('company_name')}")
        
        left_col, right_col = st.columns(2)
        
        with left_col:
            st.markdown("### 📝 Target Job Description Spec")
            st.text_area(
                "Scraped Job Spec Context", 
                value=job.get('job_description') or 'No description captured.', 
                height=350,
                disabled=True
            )
                    
        with right_col:
            st.markdown("### ✨ AI Generation Output")
            cv_tab, cl_tab = st.tabs(["📄 Optimized CV", "✉️ Custom Cover Letter"])
            
            with cv_tab:
                if job.get('tailored_cv'):
                    st.text_area("Your Tailored Target CV Content", value=job.get('tailored_cv'), height=300)
                else:
                    st.warning("Assets are currently pending pipeline calculation.")
                    
            with cl_tab:
                if job.get('tailored_cover_letter'):
                    st.text_area("Your Tailored Cover Letter Content", value=job.get('tailored_cover_letter'), height=300)
                else:
                    st.warning("Assets are currently pending pipeline calculation.")
else:
    st.info("Your pipeline data core is currently empty.")