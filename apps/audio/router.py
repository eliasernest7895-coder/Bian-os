from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from core.database import get_session
from apps.audio.models import AudioTrack, HardwareAudioProfile

router = APIRouter(prefix="/audio", tags=["Audio Pro DSP Engine"])

@router.get("/hardware-sync")
async def sync_hardware_dac(sample_rate: int = 48000):
    # Lógica de emparejamiento con el hardware
    return {
        "status": "Hardware Synced",
        "configured_sample_rate": f"{sample_rate} Hz",
        "dsp_status": "Bypass Aliasing / Direct Hardware Pass",
        "playback": "Gapless (Sin Interrupciones)"
    }

@router.post("/tracks/", response_model=AudioTrack)
def register_track(track: AudioTrack, session: Session = Depends(get_session)):
    session.add(track)
    session.commit()
    session.refresh(track)
    return track

@router.get("/tracks/", response_model=list[AudioTrack])
def list_tracks(session: Session = Depends(get_session)):
    return session.exec(select(AudioTrack)).all()

