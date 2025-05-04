
# AI Resume Builder

A simple AI-powered app that builds professional, ATS-optimized resumes based on user input.

## How to Deploy

### Backend (Render)
1. Deploy `/backend/` to Render.
2. Set environment variable `OPENAI_API_KEY` in Render.
3. Start command:
    uvicorn backend.main:app --host 0.0.0.0 --port 10000

### Frontend (Vercel)
1. Deploy `/frontend/` to Vercel.
2. Update fetch URL inside `index.html` to point to your Render backend URL.

### Coming Soon Page
1. Deploy `/coming_soon/coming_soon.html` as static site if needed to collect emails.

Enjoy!
