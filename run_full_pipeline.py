def run_pipeline():
    # ... inside your function after the loop ...
    updated_count = len(results)
    return updated_count

# Then in app.py:
if st.sidebar.button("2. Batch Update Missing Assets"):
    with st.spinner("AI is batch processing..."):
        count = run_pipeline()
        st.sidebar.success(f"Generated assets for {count} jobs.")