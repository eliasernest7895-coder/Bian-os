from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class EchoSignal(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    source_node: str = Field(default="S23_Ultra")
    signal_type: str = Field(default="p2p_command")  # p2p_command, walkie_talkie_clip, local_alert
    payload: str                                       # Comando o ruta de clip de audio
    target_node: Optional[str] = Field(default="broadcast")
    processed: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)

