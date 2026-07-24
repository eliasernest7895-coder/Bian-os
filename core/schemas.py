from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class DeviceMetrics(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    cpu_usage_pct: float
    ram_free_mb: float

class BianAssetCreate(BaseModel):
    filename: str
    file_size_bytes: int
    mime_type: str
    local_path: str

class SpaceSecurityStatus(BaseModel):
    kernel_shield_active: bool = True
    crypted_vault_locked: bool = True
    active_threats_detected: int = 0

class FitchTransactionSchema(BaseModel):
    amount: float
    category: str
    description: Optional[str] = None
    is_offline_synced: bool = True

