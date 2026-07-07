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

# Sidebar Navigation
menu = st.sidebar.radio("Navigation", ["Dashboard", "Manage Master CV"])

# --- TAB: Manage Master CV ---
if menu == "Manage Master CV":
    st.header("Manage Master CV")
    uploaded_file = st.file_uploader("Upload your Master CV (.docx)", type=["docx"])
    
    if uploaded_file:
        cv_text = read_docx(uploaded_file)
        if st.button("Save to Database"):
            supabase.table("user_profile").upsert({"id": 1, "master_cv_text": cv_text}).execute()
            st.success("Master CV saved!")
            
    profile = supabase.table("user_profile").select("master_cv_text").eq("id", 1).execute()
    if profile.data:
        st.subheader("Stored CV Preview")
        st.text_area("Content", profile.data[0]['master_cv_text'], height=200)

# --- TAB: Dashboard ---
elif menu == "Dashboard":
    st.title("💼 Executive Pipeline")
    
    try:
        response = supabase.table("job_tracker").select("*").execute()
        df = pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading jobs: {e}")
        df = pd.DataFrame()

    if df.empty:
        st.info("No jobs discovered yet.")
    else:
        # Standard display logic
        st.dataframe(df[["company_name", "role_title", "status"]], use_container_width=True)
        st.warning("Select a row or click a specific job to tailor assets.")