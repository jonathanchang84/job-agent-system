import os
import streamlit as st
import pandas as pd
from supabase import create_client
from cv_manager import read_docx

# Setup
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

st.set_page_config(page_title="Executive Job Agent", layout="wide")

# Navigation
menu = st.sidebar.radio("Navigation", ["Dashboard", "Manage Master CV"])

if menu == "Manage Master CV":
    st.header("Upload Master CV (.docx)")
    uploaded_file = st.file_uploader("Upload your latest Master CV", type=["docx"])
    
    if uploaded_file:
        cv_text = read_docx(uploaded_file)
        if st.button("Save to Database"):
            # Upsert into user_profile (ID 1)
            supabase.table("user_profile").upsert({"id": 1, "master_cv_text": cv_text}).execute()
            st.success("Master CV stored successfully!")
            
    # Preview existing
    profile = supabase.table("user_profile").select("master_cv_text").eq("id", 1).execute()
    if profile.data:
        st.subheader("Current Master CV Preview")
        st.text_area("Content", profile.data[0]['master_cv_text'], height=200)

else:
    # Dashboard Code (Insert your existing dashboard logic here)
    st.title("💼 Executive Pipeline")
    # ... rest of your dashboard code