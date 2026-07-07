import streamlit as st
import pandas as pd
from run_full_pipeline import run_pipeline # Import the batch logic

# ... (Previous imports and config)

st.sidebar.subheader("Batch Controls")
if st.sidebar.button("1. Trigger Job Search & Sync"):
    with st.spinner("Searching..."):
        # run_search_logic()
        st.success("New jobs added.")

if st.sidebar.button("2. Batch Update Missing Assets"):
    with st.spinner("AI is batch processing..."):
        run_pipeline()
        st.success("Assets generated for all jobs.")