from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from core.database import get_session
from apps.bian.models import PhotoAsset

router = APIRouter(prefix="/bian", tags=["Bian AI Photo App"])

@router.post("/assets/", response_model=PhotoAsset)
def create_photo_asset(photo: PhotoAsset, session: Session = Depends(get_session)):
    session.add(photo)
    session.commit()
    session.refresh(photo)
    return photo

@router.get("/assets/", response_model=list[PhotoAsset])
def list_photo_assets(session: Session = Depends(get_session)):
    photos = session.exec(select(PhotoAsset)).all()
    return photos
