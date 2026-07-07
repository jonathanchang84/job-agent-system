# api.py or added into a simple webhook route
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from supabase import create_client

app = FastAPI()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

class JobPayload(BaseModel):
    url: str
    title: str
    company: str
    description: str

@app.post("/api/add-job")
def add_job_from_browser(data: JobPayload):
    try:
        # Check if the URL already exists
        duplicate_check = supabase.table("job_tracker").select("id").eq("job_url", data.url).execute()
        
        payload = {
            "company_name": data.company,
            "role_title": data.title,
            "job_url": data.url,
            "job_description": data.description,
            "status": "Discovered",
            "source": "LINKEDIN"
        }
        
        if duplicate_check.data:
            # Update the existing row with the description if it was blank
            supabase.table("job_tracker").update(payload).eq("job_url", data.url).execute()
        else:
            # Insert a completely new row
            supabase.table("job_tracker").insert(payload).execute()
            
        return {"status": "success", "message": "Job details successfully pushed to dashboard!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))