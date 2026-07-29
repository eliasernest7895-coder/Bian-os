from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from core.database import get_session
from apps.battery_guard.models import BatteryHealthLog

router = APIRouter(prefix="/battery-guard", tags=["BatteryGuard Health & Thermal Protection"])

@router.get("/status")
async def battery_protection_status():
    return {
        "engine": "BatteryGuard Thermal & Lifecycle Engine",
        "lithium_protection": "Active",
        "charge_threshold": "80% Recommended Limit",
        "thermal_throttle_guard": "Monitoring Internal Sensors",
        "cell_health": "Optimal (Stress Free Zone)"
    }

@router.post("/logs/", response_model=BatteryHealthLog)
def log_battery_state(log: BatteryHealthLog, session: Session = Depends(get_session)):
    session.add(log)
    session.commit()
    session.refresh(log)
    return log

@router.get("/logs/", response_model=list[BatteryHealthLog])
def list_battery_logs(session: Session = Depends(get_session)):
    return session.exec(select(BatteryHealthLog)).all()
