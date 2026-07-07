import os
from dotenv import load_dotenv
import streamlit as st
import pandas as pd
from supabase import create_client

# Force-reload environment variables locally
load_dotenv(override=True)

# Page Configuration
st.set_page_config(
    page_title="Executive Job Tracker",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Supabase Client
# (Checks local environment first via os.getenv, then falls back to Streamlit Secrets on the Cloud)
SUPABASE_URL = os.getenv("SUPABASE_URL") or (st.secrets.get("SUPABASE_URL") if "SUPABASE_URL" in st.secrets else None)
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or (st.secrets.get("SUPABASE_KEY") if "SUPABASE_KEY" in st.secrets else None)

@st.cache_resource
def init_supabase():
    if not SUPABASE_URL or not SUPABASE_KEY:
        st.error("Missing Supabase credentials. Check your local .env file or Streamlit Cloud Secrets.")
        return None
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.error(f"Failed to connect to Supabase: {e}")
        return None

supabase = init_supabase()

def fetch_tracked_jobs():
    """Pull records directly from your Supabase table and sort via Pandas."""
    if not supabase:
        return pd.DataFrame()
    try:
        response = supabase.table("job_tracker").select("*").execute()
        if response.data:
            df_raw = pd.DataFrame(response.data)
            if "id" in df_raw.columns:
                df_raw = df_raw.sort_values(by="id", ascending=False)
            return df_raw
    except Exception as e:
        st.error(f"Error fetching data: {e}")
    return pd.DataFrame()

# --- Dashboard Header ---
st.title("💼 Executive Job Agent Dashboard")
st.markdown("Real-time pipeline tracking high-yield product leadership opportunities.")
st.write("---")

# Fetch Data
df = fetch_tracked_jobs()

if df.empty:
    st.info("No jobs found in your database yet. Run `python3 search_engine.py` to seed data.")
else:
    # --- Metrics Bar ---
    total_jobs = len(df)
    discovered_count = len(df[df["status"] == "Discovered"]) if "status" in df.columns else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Total Opportunities Discovered", value=total_jobs)
    with col2:
        st.metric(label="Status: Discovered/New", value=discovered_count)
    with col3:
        st.metric(label="Target Market", value="UK (London / Remote)")

    st.write("---")

    # --- Sidebar Filters ---
    st.sidebar.header("Filter Controls")
    
    # Filter by Company
    if "company_name" in df.columns:
        companies = ["All"] + sorted(df["company_name"].dropna().unique().tolist())
        selected_company = st.sidebar.selectbox("Select Company", companies)
        if selected_company != "All":
            df = df[df["company_name"] == selected_company]

    # Filter by Source Platform
    if "source" in df.columns:
        sources = ["All"] + sorted(df["source"].dropna().unique().tolist())
        selected_source = st.sidebar.selectbox("Job Source Platform", sources)
        if selected_source != "All":
            df = df[df["source"] == selected_source]

    # Filter by Status
    if "status" in df.columns:
        statuses = ["All"] + sorted(df["status"].dropna().unique().tolist())
        selected_status = st.sidebar.selectbox("Application Status", statuses)
        if selected_status != "All":
            df = df[df["status"] == selected_status]

    # --- Main Data View ---
    st.subheader("Discovered Leads")
    
    # Clean up dataframe view for presentation and include the 'source' column
    display_cols = ["id", "company_name", "role_title", "source", "status", "job_url"]
    actual_cols = [col for col in display_cols if col in df.columns]
    
    st.dataframe(
        df[actual_cols],
        column_config={
            "job_url": st.column_config.LinkColumn("Application Link"),
            "company_name": "Company",
            "role_title": "Job Title",
            "source": "Source Platform",
            "status": "Status"
        },
        use_container_width=True,
        hide_index=True
    )