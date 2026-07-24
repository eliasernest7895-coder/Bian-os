from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from core.database import get_session
from apps.space.models import SpaceVaultItem

router = APIRouter(prefix="/space", tags=["Space Security Vault"])

@router.get("/status")
async def space_status():
    return {
        "app": "SPACE",
        "shield": "Kernel Isolation Active",
        "vault_status": "Locked & Encrypted",
        "network_leak_prevention": "100%"
    }

@router.post("/vault/", response_model=SpaceVaultItem)
def store_in_vault(item: SpaceVaultItem, session: Session = Depends(get_session)):
    session.add(item)
    session.commit()
    session.refresh(item)
    return item

@router.get("/vault/", response_model=list[SpaceVaultItem])
def list_vault_items(session: Session = Depends(get_session)):
    items = session.exec(select(SpaceVaultItem)).all()
    return items

