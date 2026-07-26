from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from core.database import get_session
from apps.echo.models import EchoSignal

router = APIRouter(prefix="/echo", tags=["Echo P2P Mesh Engine"])

@router.get("/mesh-status")
async def mesh_status():
    return {
        "node_id": "Echo-Core-Local",
        "mesh_network": "Active P2P Bridge",
        "transceiver": "Wi-Fi Direct / Local Sockets",
        "internet_required": False
    }

@router.post("/signals/", response_model=EchoSignal)
def emit_signal(signal: EchoSignal, session: Session = Depends(get_session)):
    session.add(signal)
    session.commit()
    session.refresh(signal)
    return signal

@router.get("/signals/", response_model=list[EchoSignal])
def list_signals(session: Session = Depends(get_session)):
    return session.exec(select(EchoSignal)).all()

