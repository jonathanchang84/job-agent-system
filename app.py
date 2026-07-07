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

st.title("🚀 Job Application Agent")

# ==========================================
# SIDEBAR CONTROLS & CV STATE VISUALIZATION
# ==========================================
st.sidebar.header("Automation Engine")

if st.sidebar.button("🔍 1. Scrape & Auto-Pull Full Specs"):
    with st.spinner("Scraping listings..."):
        try:
            queries = engine.generate_search_queries()
            raw_df = engine.execute_uk_job_search(queries)
            if not raw_df.empty:
                engine.save_matches_to_supabase(raw_df)
                st.sidebar.success(f"Pulled {len(raw_df)} jobs!")
            else:
                st.sidebar.warning("No new jobs found.")
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Scraper error: {e}")

if st.sidebar.button("🤖 2. Batch Update Missing Assets"):
    with st.spinner("AI is optimizing CVs and Cover Letters..."):
        try:
            count = run_pipeline()
            st.sidebar.success(f"Optimized assets for {count} positions!")
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Halted: {e}")

st.sidebar.markdown("---")
st.sidebar.header("Profile Administration")

# LIVE FEEDBACK: Fetch and verify current active database Master CV text
try:
    cv_check = supabase.table("user_profile").select("master_cv_text").eq("id", 1).execute()
    has_cv = len(cv_check.data[0]["master_cv_text"].strip()) > 0 if cv_check.data else False
except Exception:
    has_cv = False

if has_cv:
    st.sidebar.success("✅ Active Master CV Linked in Database")
else:
    st.sidebar.warning("⚠️ No Active Master CV Found in Database")

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
            updated_desc = st.text_area(
                "Scraped Job Spec Context (Feel free to paste text here if empty)", 
                value=job.get('job_description') or '', 
                height=350
            )
            if updated_desc != job.get('job_description'):
                if st.button("💾 Save Pasted Job Spec"):
                    supabase.table("job_tracker").update({"job_description": updated_desc}).eq("id", job["id"]).execute()
                    st.success("Spec saved manually!")
                    st.rerun()
                    
        with right_col:
            st.markdown("### ✨ AI Generation Output")
            cv_tab, cl_tab = st.tabs(["📄 Optimized CV", "✉️ Custom Cover Letter"])
            
            with cv_tab:
                if job.get('tailored_cv'):
                    st.text_area("Your Tailored Target CV Content", value=job.get('tailored_cv'), height=300)
                else:
                    st.warning("No CV built yet. Hit button 2 on the left sidebar to generate.")
                    
            with cl_tab:
                if job.get('tailored_cover_letter'):
                    st.text_area("Your Tailored Cover Letter Content", value=job.get('tailored_cover_letter'), height=300)
                else:
                    st.warning("No Cover Letter built yet. Hit button 2 on the left sidebar to generate.")
else:
    st.info("Your pipeline data core is currently empty.")