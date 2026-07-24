from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class FitchLedgerItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    amount: float
    category: str
    is_synced: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

