import streamlit as st
import pandas as pd
from run_full_pipeline import run_pipeline
from cv_manager import read_docx
# ... keep your other imports

st.set_page_config(page_title="Executive Job Agent", layout="wide")

# 1. Sidebar Navigation
st.sidebar.title("Navigation")
menu = st.sidebar.radio("Go to", ["Dashboard", "Manage Master CV"])

# 2. Sidebar Batch Controls (Always visible in sidebar)
st.sidebar.markdown("---")
st.sidebar.subheader("Batch Controls")
if st.sidebar.button("1. Trigger Job Search & Sync"):
    # Call your search logic here
    st.sidebar.success("Search triggered.")

if st.sidebar.button("2. Batch Update Missing Assets"):
    with st.spinner("AI is batch processing..."):
        run_pipeline()
        st.sidebar.success("Assets generated.")

# 3. Main View Router
if menu == "Manage Master CV":
    st.header("Manage Master CV")
    # ... your existing upload code ...

elif menu == "Dashboard":
    st.title("💼 Executive Pipeline")
    # ... your existing table view and inspector code ...