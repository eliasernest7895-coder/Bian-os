from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from core.database import get_session
from apps.mainstream.models import TemporalEvent

router = APIRouter(prefix="/mainstream", tags=["Mainstream Temporal Engine"])

@router.get("/observer")
async def observe_timeline():
    return {
        "engine": "Mainstream Quantum-Temporal Predictor",
        "observer_state": "Active",
        "continuum": {
            "past": "Recorded in Immutable SQLite Ledger",
            "present": "Live Event Bus Active",
            "future": "Monte Carlo Probability Matrix Enabled"
        }
    }

@router.post("/events/", response_model=TemporalEvent)
def record_temporal_event(event: TemporalEvent, session: Session = Depends(get_session)):
    session.add(event)
    session.commit()
    session.refresh(event)
    return event

@router.get("/events/", response_model=list[TemporalEvent])
def list_timeline(session: Session = Depends(get_session)):
    return session.exec(select(TemporalEvent)).all()
