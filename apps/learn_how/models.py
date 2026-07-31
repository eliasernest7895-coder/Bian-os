from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class TutorialGuide(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    category: str = Field(default="Social & Dynamics") # Social & Dynamics, DIY & Manufacturing, Life Hacks, Tech
    author_alias: str = Field(default="Comunidad Estrada")
    difficulty_level: str = Field(default="Principiante") # Principiante, Intermedio, Avanzado
    summary: str
    steps_json: str # Guardará los pasos detallados en formato estructurado
    likes_count: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
