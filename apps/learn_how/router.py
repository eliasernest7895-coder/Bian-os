from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from core.database import get_session
from apps.learn_how.models import TutorialGuide

router = APIRouter(prefix="/learn-how", tags=["LearnHow Skill-Sharing Platform"])

@router.get("/categories")
async def get_categories():
    return {
        "engine": "LearnHow Community Knowledge Engine",
        "active_categories": [
            "Habilidades Sociales & Ligue",
            "Fabricación, Electrónica & Taller",
            "Life Hacks & Tips Diarios",
            "Desarrollo & Tecnología"
        ],
        "status": "Ready for Learning"
    }

@router.post("/guides/", response_model=TutorialGuide)
def create_guide(guide: TutorialGuide, session: Session = Depends(get_session)):
    session.add(guide)
    session.commit()
    session.refresh(guide)
    return guide

@router.get("/guides/", response_model=list[TutorialGuide])
def list_guides(session: Session = Depends(get_session)):
    return session.exec(select(TutorialGuide)).all()
