from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from core.database import get_session
from apps.studio_studio.models import MusicProject

router = APIRouter(prefix="/studio-studio", tags=["StudioStudio DAW & Mastering"])

@router.get("/studio-status")
async def studio_status():
    return {
        "engine": "StudioStudio Virtual Audio Workstation",
        "sampler_rate": "48000 Hz / 24-bit",
        "beatmaker": "Active (Reggaeton & Experimental Grid)",
        "lyric_assistant": "Rhyme & Rhythm Engine Online",
        "mastering_chain": "Pro Limiter & Loudness Maximizer Ready"
    }

@router.post("/projects/", response_model=MusicProject)
def create_project(project: MusicProject, session: Session = Depends(get_session)):
    session.add(project)
    session.commit()
    session.refresh(project)
    return project

@router.get("/projects/", response_model=list[MusicProject])
def list_projects(session: Session = Depends(get_session)):
    return session.exec(select(MusicProject)).all()
