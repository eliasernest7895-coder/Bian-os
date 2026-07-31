from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class FakeCallPreset(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    caller_name: str = Field(default="Maria Smith")
    caller_number: str = Field(default="123456789")
    trigger_delay_seconds: int = Field(default=10) # Tiempo de espera para activar
    audio_script_payload: Optional[str] = Field(default="voice_profile_default.wav")
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
