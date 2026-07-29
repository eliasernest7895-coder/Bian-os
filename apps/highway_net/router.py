from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from core.database import get_session
from apps.highway_net.models import NetworkSignalLog

router = APIRouter(prefix="/highway-net", tags=["HighwayNet Signal Stabilizer"])

@router.get("/lock-status")
async def signal_lock_status():
    return {
        "engine": "HighwayNet Engine",
        "modem_state": "High Performance / Anti-Sleep Active",
        "protocol_lock": "4G/5G Preferred",
        "keep_alive_socket": "Running (0% Artificial Latency)",
        "status": "Stabilized"
    }

@router.post("/logs/", response_model=NetworkSignalLog)
def log_signal(log: NetworkSignalLog, session: Session = Depends(get_session)):
    session.add(log)
    session.commit()
    session.refresh(log)
    return log

@router.get("/logs/", response_model=list[NetworkSignalLog])
def list_signal_logs(session: Session = Depends(get_session)):
    return session.exec(select(NetworkSignalLog)).all()
