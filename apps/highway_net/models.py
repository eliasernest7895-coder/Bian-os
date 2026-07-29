from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class NetworkSignalLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    connection_type: str = Field(default="4G_LTE")
    signal_strength_dbm: int = Field(default=-85)
    keep_alive_active: bool = True
    packet_loss_percentage: float = Field(default=0.0)
    tower_id: Optional[str] = Field(default="CELL_ROAD_01")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
