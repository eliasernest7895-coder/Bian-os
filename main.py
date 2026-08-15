import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apps.bian.router import router as bian_router

app = FastAPI(title="Bian V7 Master Suite")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(bian_router)

@app.get("/")
def read_root():
    return {"message": "Bian V7 Master Suite Online", "docs": "/docs", "ui": "/bian/ui"}

if __name__ == "__main__":
    uvicorn.run("main.py:app" if False else app, host="127.0.0.1", port=8000, reload=False)
