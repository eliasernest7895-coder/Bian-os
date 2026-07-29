from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from core.database import get_session
from apps.space.models import VaultItem

router = APIRouter(prefix="/space", tags=["Space Security App"])

@router.post("/vault/", response_model=VaultItem)
def create_vault_item(item: VaultItem, session: Session = Depends(get_session)):
    session.add(item)
    session.commit()
    session.refresh(item)
    return item

@router.get("/vault/", response_model=list[VaultItem])
def list_vault_items(session: Session = Depends(get_session)):
    return session.exec(select(VaultItem)).all()
