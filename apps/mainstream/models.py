from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class TemporalEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    timeline_dimension: str = Field(default="present") # past, present, future_projection
    event_name: str
    probability_score: float = Field(default=1.0)      # 1.0 para pasado/presente, < 1.0 para predicciones
    data_payload: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
