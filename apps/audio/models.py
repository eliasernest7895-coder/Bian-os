from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class AudioTrack(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    artist: str = "Desconocido"
    file_path: str
    sample_rate_hz: int = Field(default=44100) # ej. 44100Hz, 48000Hz, 96000Hz
    bit_depth: int = Field(default=16)        # ej. 16-bit, 24-bit Hi-Res
    duration_seconds: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)

class HardwareAudioProfile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    device_dac_max_hz: int = Field(default=48000) # Límite del DAC físico
    low_latency_mode: bool = True
    dsp_equalizer_active: bool = True
    buffer_size_ms: int = Field(default=10)        # Evita micro-cortes

