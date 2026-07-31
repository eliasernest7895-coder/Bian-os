from fastapi import FastAPI
import uvicorn
from core.database import create_db_and_tables
from apps.bian.router import router as bian_router
from apps.space.router import router as space_router
from apps.fitch.router import router as fitch_router
from apps.audio.router import router as audio_router
from apps.echo.router import router as echo_router
from apps.mesh_chat.router import router as mesh_chat_router
from apps.highway_net.router import router as highway_net_router
from apps.mainstream.router import router as mainstream_router
from apps.battery_guard.router import router as battery_guard_router
from apps.studio_studio.router import router as studio_studio_router
from apps.learn_how.router import router as learn_how_router

app = FastAPI(
    title="Suite Estrada Core Engine",
    version="1.8.0",
    description="Backend soberano 100% local para la Suite Estrada."
)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# Routers Activos de la Suite (11/12 - 91.6% de la Suite)
app.include_router(bian_router)
app.include_router(space_router)
app.include_router(fitch_router)
app.include_router(audio_router)
app.include_router(echo_router)
app.include_router(mesh_chat_router)
app.include_router(highway_net_router)
app.include_router(mainstream_router)
app.include_router(battery_guard_router)
app.include_router(studio_studio_router)
app.include_router(learn_how_router)

@app.get("/")
async def root():
    return {
        "status": "online",
        "mode": "offline_sovereign",
        "engine": "Snapdragon Optimized",
        "active_modules": [
            "bian", "space", "fitch", "audio", 
            "echo", "mesh_chat", "highway_net", "mainstream",
            "battery_guard", "studio_studio", "learn_how"
        ]
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
