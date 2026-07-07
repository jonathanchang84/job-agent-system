import streamlit as st
import pandas as pd
import os
from docxtpl import DocxTemplate
from io import BytesIO
from run_full_pipeline import run_pipeline
from cv_manager import read_docx
from supabase import create_client

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# Function to generate high-quality DOCX from your template
def generate_from_template(context):
    doc = DocxTemplate("template_cv.docx")
    doc.render(context)
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

# Dashboard Logic
if menu == "Dashboard":
    # ... (dataframe loading code)
    if event.selection.rows:
        job = df.iloc[event.selection.rows[0]]
        
        # Prepare context for the template
        context = {
            'summary': job.get('augmented_cv_text', ''),
            # Add other keys based on your template placeholders
        }
        
        c1, c2 = st.columns(2)
        with c1:
            st.download_button(
                label="Download CV",
                data=generate_from_template(context),
                # FIXED: Naming now uses job title
                file_name=f"Jonathan Chang CV - {job['role_title']}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )