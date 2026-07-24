from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from core.database import get_session
from apps.fitch.models import FitchLedgerItem

router = APIRouter(prefix="/fitch", tags=["Fitch Engine Relacional"])

@router.get("/status")
async def fitch_status():
    return {
        "app": "FITCH",
        "engine": "Relational Data Ledger",
        "mode": "Offline Sovereign Node",
        "integrity": "100%"
    }

@router.post("/ledger/", response_model=FitchLedgerItem)
def create_ledger_item(item: FitchLedgerItem, session: Session = Depends(get_session)):
    session.add(item)
    session.commit()
    session.refresh(item)
    return item

@router.get("/ledger/", response_model=list[FitchLedgerItem])
def list_ledger_items(session: Session = Depends(get_session)):
    items = session.exec(select(FitchLedgerItem)).all()
    return items

