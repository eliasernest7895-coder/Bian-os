from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class MusicProject(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    genre: str = Field(default="Reggaeton / Hybrid")
    bpm: int = Field(default=96)
    lyrics: Optional[str] = Field(default="")
    mastering_preset: str = Field(default="Commercial Punch / Loudness")
    is_mastered: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
