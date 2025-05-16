from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import fitz

load_dotenv()  # ✅ Load variables from .env

app = FastAPI()

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Models
class ResumeRequest(BaseModel):
    full_name: str
    email: str
    job_title: str
    skills: list
    experiences: list

class EmailRequest(BaseModel):
    email: str
    resume: str

# Generate Resume
@app.post("/generate_resume/")
async def generate_resume(data: ResumeRequest):
    resume_prompt = f"""
    You are a professional career coach and resume writer. 
    Create an ATS-optimized, clean 1-page resume for the following person:
    - Full Name: {data.full_name}
    - Email: {data.email}
    - Target Job Title: {data.job_title}
    - Key Skills: {', '.join(data.skills)}
    - Work Experience Highlights:
    {' '.join(f"- {exp}" for exp in data.experiences)}

    Requirements:
    - Start with a brief 3–4 line Professional Summary
    - Skills section: 2 columns, bullet points
    - Experience section: Bullet points per job
    - Keep formatting simple
    - Use impactful keywords
    - Ensure ATS-friendly format.

    Output only the resume text, cleanly formatted.
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": resume_prompt}],
        temperature=0.7,
        max_tokens=1000
    )

    resume_text = response.choices[0].message.content
    return {"resume": resume_text}

# Generate Cover Letter
@app.post("/generate_cover_letter/")
async def generate_cover_letter(data: ResumeRequest):
    prompt = f"""
    You are a professional career coach. Write a personalized, concise, and compelling cover letter for the following person:

    - Full Name: {data.full_name}
    - Target Job Title: {data.job_title}
    - Email: {data.email}
    - Skills: {', '.join(data.skills)}
    - Experience Highlights:
    {' '.join(f"- {exp}" for exp in data.experiences)}

    Guidelines:
    - Use a warm, confident tone
    - Mention the job title
    - Focus on value, not repetition of resume
    - No more than 4 paragraphs
    - Address it generally (e.g. Dear Hiring Manager)

    Output only the cover letter text.
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=800
    )

    letter = response.choices[0].message.content
    return {"resume": letter}

# Send Resume via Email (SendGrid SDK)
@app.post("/send_resume_email/")
async def send_resume_email(data: EmailRequest):
    try:
        message = Mail(
            from_email=os.getenv("EMAIL_SENDER"),
            to_emails=data.email,
            subject="Your AI-Generated Resume",
            plain_text_content=data.resume
        )
        sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY").strip())
        sg.send(message)
        return {"message": "✅ Resume sent to your inbox!"}
    except Exception as e:
        return {"message": f"❌ Failed to send email: {e}"}

# Upload LinkedIn PDF and extract fields
@app.post("/upload_linkedin_pdf/")
async def upload_linkedin_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        return {"error": "Only PDF files are supported."}

    content = await file.read()

    try:
        doc = fitz.open(stream=content, filetype="pdf")
        full_text = ""
        for page in doc:
            full_text += page.get_text() + "\n"
    except Exception as e:
        return {"error": f"Failed to parse PDF: {str(e)}"}

    lines = full_text.splitlines()

    # Clean name: first non-empty line
    name = next((line.strip() for line in lines if line.strip()), "Unknown")

    # Filter experience lines
    experience_keywords = [
        "engineer", "manager", "developer", "consultant", "intern",
        "specialist", "analyst", "architect", "lead", "officer"
    ]
    experiences = [
        line.strip() for line in lines
        if any(keyword in line.lower() for keyword in experience_keywords)
    ][:5]

    # Extract skills: look for "skills" header
    skills_section = ""
    for i, line in enumerate(lines):
        if "skills" in line.lower():
            if i + 1 < len(lines):
                skills_section = lines[i + 1]
            break

    skills = [s.strip() for s in skills_section.replace("|", ",").split(",") if s.strip()]

    return {
        "full_name": name,
        "job_title": experiences[0] if experiences else "",
        "experiences": experiences,
        "skills": skills
    }
