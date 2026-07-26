from fastapi import FastAPI
import uvicorn
from core.database import create_db_and_tables
from apps.bian.router import router as bian_router
from apps.space.router import router as space_router
from apps.fitch.router import router as fitch_router
from apps.audio.router import router as audio_router

app = FastAPI(
    title="Suite Estrada Core Engine",
    version="1.1.0",
    description="Backend soberano 100% local para la Suite Estrada."
)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# Routers de la Suite
app.include_router(bian_router)
app.include_router(space_router)
app.include_router(fitch_router)
app.include_router(audio_router)

@app.get("/")
async def root():
    return {
        "status": "online",
        "mode": "offline_sovereign",
        "engine": "Snapdragon Optimized",
        "active_modules": ["bian", "space", "fitch", "audio"]
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
