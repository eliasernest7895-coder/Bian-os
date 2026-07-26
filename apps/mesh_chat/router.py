from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from core.database import get_session
from apps.mesh_chat.models import MeshMessage, MeshBlockFeed

router = APIRouter(prefix="/mesh-chat", tags=["MeshChat Sovereign Messaging & Safety"])

@router.get("/status")
async def mesh_chat_status():
    return {
        "engine": "MeshChat Engine",
        "encryption": "E2EE Local",
        "on_device_moderation": "Active (Anti-Gore / Anti-Illegal)",
        "protocol": "Gossip P2P Mesh"
    }

@router.post("/blocks/", response_model=MeshBlockFeed)
def publish_block(block: MeshBlockFeed, session: Session = Depends(get_session)):
    # Simulación del Filtro de Moderación On-Device
    if block.safety_score < 0.5:
        raise HTTPException(
            status_code=400, 
            detail="Contenido rechazado por el filtro de seguridad local (Violación de políticas de contenido)."
        )
    
    session.add(block)
    session.commit()
    session.refresh(block)
    return block

@router.get("/blocks/", response_model=list[MeshBlockFeed])
def list_blocks(session: Session = Depends(get_session)):
    return session.exec(select(MeshBlockFeed)).all()

