import streamlit as st
import pandas as pd
import os
from supabase import create_client
from cv_manager import read_docx
from run_full_pipeline import run_pipeline, generate_asset_with_retry

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
# SIDEBAR CONTROLS
# ==========================================
st.sidebar.header("Automation Engine")

if st.sidebar.button("🔍 1. Scrape & Auto-Pull Full Specs"):
    import search_engine as engine
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

if st.sidebar.button("🤖 2. Batch Process All Missing"):
    with st.spinner("AI processing all incomplete entries..."):
        try:
            count = run_pipeline()
            st.sidebar.success(f"Optimized assets for {count} positions!")
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Halted: {e}")

st.sidebar.markdown("---")
st.sidebar.header("Profile Administration")

try:
    cv_check = supabase.table("user_profile").select("master_cv_text").eq("id", 1).execute()
    has_cv = len(cv_check.data[0]["master_cv_text"].strip()) > 0 if cv_check.data else False
except Exception:
    has_cv = False

if has_cv:
    st.sidebar.success("✅ Active Master CV Linked in Database")
    master_cv_text = cv_check.data[0]["master_cv_text"]
else:
    st.sidebar.warning("⚠️ No Active Master CV Found in Database")
    master_cv_text = ""

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
            current_text_box_value = st.text_area(
                "Scraped Job Spec Context", 
                value=job.get('job_description') or '', 
                height=350,
                key=f"desc_{job['id']}"
            )
            
            if st.button("✨ Force Tailor This Selected Job Right Now", type="primary"):
                if not master_cv_text:
                    st.error("Cannot run optimization: Master CV is missing.")
                elif not current_text_box_value.strip():
                    st.error("Please ensure you paste or save a job description spec on the left before tailoring.")
                else:
                    with st.spinner("Talking directly to Gemini for this specific job..."):
                        try:
                            role_title = job.get('role_title') or 'Executive Position'
                            company = job.get('company_name') or 'Target Enterprise'
                            
                            cv_prompt = f"Tailor this Master CV to match this job context perfectly. Optimize for maximum leadership and technical competency mapping:\n\n[Role]: {role_title} at {company}\n[Spec]: {current_text_box_value}\n[CV Framework]: {master_cv_text}"
                            cl_prompt = f"Write a high-impact outcome-focused executive cover letter tailored matching this job spec. Max 1 page:\n\n[Role]: {role_title} at {company}\n[Spec]: {current_text_box_value}\n[CV Framework]: {master_cv_text}"
                            
                            new_cv = generate_asset_with_retry(cv_prompt)
                            new_cl = generate_asset_with_retry(cl_prompt)
                            
                            supabase.table("job_tracker").update({
                                "job_description": current_text_box_value,
                                "tailored_cv": new_cv,
                                "tailored_cover_letter": new_cl,
                                "status": "Ready to Apply"
                            }).eq("id", job["id"]).execute()
                            
                            st.success("Assets built and saved perfectly!")
                            st.rerun()
                        except Exception as err:
                            st.error(f"Direct compilation error: {err}")
                    
        with right_col:
            st.markdown("### ✨ AI Generation Output")
            cv_tab, cl_tab = st.tabs(["📄 Optimized CV", "✉️ Custom Cover Letter"])
            
            with cv_tab:
                if job.get('tailored_cv'):
                    st.text_area("Your Tailored Target CV Content", value=job.get('tailored_cv'), height=300)
                else:
                    st.warning("No CV built yet. Hit 'Force Tailor This Selected Job Right Now' below the spec window to generate.")
                    
            with cl_tab:
                if job.get('tailored_cover_letter'):
                    st.text_area("Your Tailored Cover Letter Content", value=job.get('tailored_cover_letter'), height=300)
                else:
                    st.warning("No Cover Letter built yet. Hit 'Force Tailor This Selected Job Right Now' below the spec window to generate.")
else:
    st.info("Your pipeline data core is currently empty.")