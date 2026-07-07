import os
import streamlit as st
import pandas as pd
from supabase import create_client
from cv_manager import read_docx

# Setup
SUPABASE_URL = os.getenv("SUPABASE_URL") or st.secrets.get("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Executive Job Agent", layout="wide")

menu = st.sidebar.radio("Navigation", ["Dashboard", "Manage Master CV"])

if menu == "Manage Master CV":
    # ... (Keep your existing Manage Master CV code here) ...
    st.header("Manage Master CV")
    uploaded_file = st.file_uploader("Upload your Master CV (.docx)", type=["docx"])
    if uploaded_file:
        if st.button("Save to Database"):
            cv_text = read_docx(uploaded_file)
            supabase.table("user_profile").upsert({"id": 1, "master_cv_text": cv_text}).execute()
            st.success("Master CV saved!")

elif menu == "Dashboard":
    st.title("💼 Executive Pipeline")
    
    # Fetch Data
    response = supabase.table("job_tracker").select("*").execute()
    df = pd.DataFrame(response.data) if response.data else pd.DataFrame()

    if df.empty:
        st.info("No jobs discovered yet.")
    else:
        # Create two columns: Left for list, Right for Inspector
        col1, col2 = st.columns([3, 2])

        with col1:
            st.subheader("Discovered Opportunities")
            # We display all relevant info here
            event = st.dataframe(
                df[["company_name", "role_title", "status", "source", "job_url"]],
                use_container_width=True,
                selection_mode="single-row",
                on_select="rerun"
            )

        with col2:
            st.subheader("AI Asset Inspector")
            # Logic to check if a row was selected
            if event.selection.rows:
                idx = event.selection.rows[0]
                job = df.iloc[idx]
                
                st.markdown(f"### {job['role_title']}")
                st.write(f"**Company:** {job['company_name']}")
                st.write(f"**Source:** {job['source']}")
                st.link_button("View Original Job Posting", job['job_url'])
                
                # Placeholder for the AI Tailoring action
                if st.button("🚀 Generate Tailored Assets"):
                    st.write("Tailoring triggered for: " + job['company_name'])
                    # We will integrate the actual agent_tailor.py call here next
            else:
                st.warning("Select a row in the table to view details and options.")