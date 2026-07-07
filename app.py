import streamlit as st
import pandas as pd
from run_full_pipeline import run_pipeline
from cv_manager import read_docx
from supabase import create_client
import os

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

st.set_page_config(page_title="Executive Job Agent", layout="wide")

# Sidebar Navigation
st.sidebar.title("Navigation")
menu = st.sidebar.radio("Go to", ["Dashboard", "Manage Master CV"])

# Sidebar Batch Controls
st.sidebar.markdown("---")
st.sidebar.subheader("Batch Controls")
if st.sidebar.button("1. Trigger Job Search & Sync"):
    st.sidebar.info("Search logic triggered.") 

if st.sidebar.button("2. Batch Update Missing Assets"):
    with st.spinner("AI is batch processing..."):
        count = run_pipeline()
        st.sidebar.success(f"Generated assets for {count} jobs.")

# Main View
if menu == "Manage Master CV":
    st.header("Manage Master CV")
    uploaded_file = st.file_uploader("Upload CV (.docx)", type=["docx"])
    if uploaded_file and st.button("Save"):
        cv_text = read_docx(uploaded_file)
        supabase.table("user_profile").upsert({"id": 1, "master_cv_text": cv_text}).execute()
        st.success("CV Saved!")

elif menu == "Dashboard":
    st.title("💼 Executive Pipeline")
    data = supabase.table("job_tracker").select("*").execute().data
    df = pd.DataFrame(data) if data else pd.DataFrame()
    
    if not df.empty:
        event = st.dataframe(df, selection_mode="single-row", on_select="rerun")
        if event.selection.rows:
            job = df.iloc[event.selection.rows[0]]
            st.write(f"### {job['role_title']} at {job['company_name']}")
            st.text_area("Cover Letter", job.get('tailored_cover_letter', ''))
    else:
        st.write("No jobs found.")