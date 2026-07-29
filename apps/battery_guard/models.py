from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class BatteryHealthLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    battery_level: int = Field(default=80)
    temperature_celsius: float = Field(default=32.5)
    voltage_mv: int = Field(default=3850)
    charge_limit_enabled: bool = True
    health_status: str = Field(default="OPTIMAL")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
