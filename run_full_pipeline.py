import json
import os
from google import genai
from supabase import create_client
from docxtpl import DocxTemplate
from io import BytesIO

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
ai_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def generate_docx(context):
    doc = DocxTemplate("template_cv.docx")
    doc.render(context)
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

def run_pipeline():
    # Fetch job and profile logic remains the same...
    # After generating content, save to Supabase as usual.
    pass