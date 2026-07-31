from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from core.database import get_session
from apps.call_assistant.models import FakeCallPreset

router = APIRouter(prefix="/call-assistant", tags=["CallAssistant Social Escape"])

@router.get("/status")
async def escape_engine_status():
    return {
        "engine": "CallAssistant Escape Engine",
        "interface_emulation": "Samsung OneUI Native UI",
        "audio_cloning": "Local Voice Synthesis Ready",
        "trigger_state": "Armed / Ready for Stealth Activation"
    }

@router.post("/presets/", response_model=FakeCallPreset)
def create_preset(preset: FakeCallPreset, session: Session = Depends(get_session)):
    session.add(preset)
    session.commit()
    session.refresh(preset)
    return preset

@router.get("/presets/", response_model=list[FakeCallPreset])
def list_presets(session: Session = Depends(get_session)):
    return session.exec(select(FakeCallPreset)).all()
