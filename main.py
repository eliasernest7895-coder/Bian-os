from fastapi import FastAPI
from apps.bian.router import router as bian_router

app = FastAPI(title="Bian V7 Master Suite")

app.include_router(bian_router, prefix="/bian")

@app.get("/")
async def root():
    return {"message": "Bian V7 Master Suite Online", "docs": "/docs", "ui": "/bian/ui"}
