import streamlit as st
import pandas as pd
from docx import Document
from io import BytesIO

# Helper to create a docx in memory
def create_docx(text):
    doc = Document()
    doc.add_paragraph(text)
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

# ... inside your app.py ...
elif menu == "Dashboard":
    st.title("💼 Executive Pipeline")
    data = supabase.table("job_tracker").select("*").execute().data
    df = pd.DataFrame(data) if data else pd.DataFrame()
    
    if not df.empty:
        event = st.dataframe(df, selection_mode="single-row", on_select="rerun", key="job_table")
        if event.selection.rows:
            job = df.iloc[event.selection.rows[0]]
            job_name = f"{job['role_title']} at {job['company_name']}"
            
            st.write(f"### {job_name}")
            
            # Create two columns for the assets
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Tailored CV")
                cv_text = job.get('augmented_cv_text', '')
                st.text_area("CV Preview", cv_text, height=300)
                st.download_button(
                    label="Download CV",
                    data=create_docx(cv_text),
                    file_name=f"Jonathan Chang CV - {job['company_name']}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
                
            with col2:
                st.subheader("Cover Letter")
                cl_text = job.get('tailored_cover_letter', '')
                st.text_area("CL Preview", cl_text, height=300)
                st.download_button(
                    label="Download Cover Letter",
                    data=create_docx(cl_text),
                    file_name=f"Jonathan Chang Covering Letter - {job['company_name']}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )