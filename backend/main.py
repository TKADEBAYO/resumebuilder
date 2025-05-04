from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
import os


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class ResumeRequest(BaseModel):
    full_name: str
    email: str
    job_title: str
    skills: list
    experiences: list


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
    {" ".join(f"- {exp}" for exp in data.experiences)}

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
