from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

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
        sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
        sg.send(message)
        return {"message": "✅ Resume sent to your inbox!"}
    except Exception as e:
        return {"message": f"❌ Failed to send email: {e}"}
