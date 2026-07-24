from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class PhotoAsset(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str
    file_size_bytes: int
    mime_type: str
    local_path: str
    is_processed: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

