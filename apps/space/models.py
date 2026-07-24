from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class SpaceVaultItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    item_name: str
    encrypted_payload: str
    security_level: int = Field(default=1) # 1: Alto, 2: Búnker
    created_at: datetime = Field(default_factory=datetime.utcnow)

