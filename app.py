import streamlit as st
import pandas as pd
import os
from docx import Document
from io import BytesIO
from run_full_pipeline import run_pipeline
from cv_manager import read_docx
from supabase import create_client

# Initialize Supabase
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

st.set_page_config(page_title="Executive Job Agent", layout="wide")

def create_docx(text):
    doc = Document()
    doc.add_paragraph(text)
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

# --- Sidebar Navigation ---
st.sidebar.title("Navigation")
menu = st.sidebar.radio("Go to", ["Dashboard", "Manage Master CV"])

# --- Restored Batch Controls ---
st.sidebar.markdown("---")
st.sidebar.subheader("Batch Controls")

if st.sidebar.button("1. Trigger Job Search & Sync"):
    st.sidebar.info("Search logic triggered...")
    # Add your specific search trigger call here

if st.sidebar.button("2. Batch Update Missing Assets"):
    with st.spinner("AI is batch processing..."):
        try:
            count = run_pipeline()
            st.sidebar.success(f"Generated assets for {count} jobs.")
        except Exception as e:
            st.sidebar.error(f"Error: {e}")

# --- Main View ---
if menu == "Manage Master CV":
    st.header("Manage Master CV")
    uploaded_file = st.file_uploader("Upload CV (.docx)", type=["docx"])
    if uploaded_file and st.button("Save to Database"):
        cv_text = read_docx(uploaded_file)
        supabase.table("user_profile").upsert({"id": 1, "master_cv_text": cv_text}).execute()
        st.success("CV Saved!")

elif menu == "Dashboard":
    st.title("💼 Executive Pipeline")
    data = supabase.table("job_tracker").select("*").execute().data
    df = pd.DataFrame(data) if data else pd.DataFrame()
    
    if not df.empty:
        # Show status in the main dataframe
        st.dataframe(df, use_container_width=True, key="job_table")
        
        # Selection logic
        job_id = st.text_input("Enter Job ID to view details")
        if job_id:
            job = df[df['id'] == job_id].iloc[0]
            st.write(f"### {job['role_title']} at {job['company_name']}")
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Tailored CV")
                st.text_area("CV Preview", job.get('augmented_cv_text', ''), height=300)
                st.download_button("Download CV", create_docx(job.get('augmented_cv_text', '')), 
                                   f"Jonathan Chang CV - {job['company_name']}.docx")
            with col2:
                st.subheader("Cover Letter")
                st.text_area("CL Preview", job.get('tailored_cover_letter', ''), height=300)
                st.download_button("Download Cover Letter", create_docx(job.get('tailored_cover_letter', '')), 
                                   f"Jonathan Chang Covering Letter - {job['company_name']}.docx")