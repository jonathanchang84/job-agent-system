import streamlit as st
import pandas as pd
import os
from docx import Document
from io import BytesIO
from run_full_pipeline import run_pipeline
from cv_manager import read_docx
from supabase import create_client

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

st.set_page_config(page_title="Executive Job Agent", layout="wide")

def create_docx(text):
    doc = Document()
    doc.add_paragraph(text)
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

st.sidebar.title("Navigation")
menu = st.sidebar.radio("Go to", ["Dashboard", "Manage Master CV"])

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
        event = st.dataframe(df, selection_mode="single-row", on_select="rerun", key="job_table")
        if event.selection.rows:
            job = df.iloc[event.selection.rows[0]]
            st.write(f"### {job['role_title']} at {job['company_name']}")
            
            c1, c2 = st.columns(2)
            with c1:
                cv_text = job.get('augmented_cv_text', 'No CV generated.')
                st.text_area("Tailored CV", cv_text, height=300)
                st.download_button("Download CV", create_docx(cv_text), 
                                   f"Jonathan Chang CV - {job['company_name']}.docx")
            with c2:
                cl_text = job.get('tailored_cover_letter', 'No Cover Letter generated.')
                st.text_area("Cover Letter", cl_text, height=300)
                st.download_button("Download Cover Letter", create_docx(cl_text), 
                                   f"Jonathan Chang Covering Letter - {job['company_name']}.docx")