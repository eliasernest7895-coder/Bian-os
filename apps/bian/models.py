from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class ProcessedImage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    image_path: str
    prompt_analysis: Optional[str] = Field(default="Analizado por IA Local")
    processed_at: datetime = Field(default_factory=datetime.utcnow)

class PrintServiceJob(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    document_name: str
    paper_size: str = Field(default="Carta") # Carta, Oficio, A4, Tabloide
    color_mode: str = Field(default="Color") # Color, BN
    copies: int = Field(default=1)
    status: str = Field(default="pending") # pending, processing, completed
    created_at: datetime = Field(default_factory=datetime.utcnow)

class PhotoStudioSession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_title: str
    preset_lighting: str = Field(default="Estudio Pro / Rembrant")
    export_format: str = Field(default="PNG_HD")
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CinemaProject(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_name: str
    aspect_ratio: str = Field(default="21:9 CinemaScope")
    fps: int = Field(default=24)
    lut_preset: str = Field(default="Teal & Orange NPU")
    created_at: datetime = Field(default_factory=datetime.utcnow)
