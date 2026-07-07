import streamlit as st
import pandas as pd
from run_full_pipeline import generate_docx

# ... (rest of your app logic)

if event.selection.rows:
    job = df.iloc[event.selection.rows[0]]
    
    # Map AI-generated text to your template tags
    context = {
        'summary': job.get('augmented_cv_text', 'Summary not available'),
        'experience': [
            {'role': job.get('role_title'), 'company': job.get('company_name'), 'dates': 'N/A', 'description': 'Tailored experience here...'}
        ]
    }
    
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="Download Full CV",
            data=generate_docx(context),
            # Filename now uses the job title as requested
            file_name=f"Jonathan Chang CV - {job['role_title']}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )