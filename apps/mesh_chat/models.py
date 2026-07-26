from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class MeshMessage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    sender_node: str
    recipient_node: str
    content: str
    is_encrypted: bool = True
    is_flagged_unsafe: bool = False  # Activado por el filtro de seguridad
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class MeshBlockFeed(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    author_node: str
    title: str
    body_content: str
    media_path: Optional[str] = None
    is_status_24h: bool = False      # True para estado efímero, False para bloque permanente
    safety_score: float = 1.0         # 1.0 = Limpio, < 0.5 = Bloqueado por moderación local
    created_at: datetime = Field(default_factory=datetime.utcnow)

