import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api import auth, agent, profile, resumes, jobs, applications, interviews, session

AGENT_URLS = [u.strip() for u in settings.agent_urls.split(",")]

app = FastAPI(title="AI Job Copilot")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(agent.router)
app.include_router(profile.router)
app.include_router(resumes.router)
app.include_router(jobs.router)
app.include_router(applications.router)
app.include_router(interviews.router)
app.include_router(session.router)


@app.get("/health")
def health():
    return {"status": "ok"}
