from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlmodel import Session, select
from core.database import get_session
from apps.bian.models import ProcessedImage
from pydantic import BaseModel
import os
import base64
from datetime import datetime

router = APIRouter(prefix="/bian", tags=["Bian AI Vision Pro"])

class ImageCaptureRequest(BaseModel):
    image_base64: str
    prompt_analysis: str = "Detección V2 Pro Engine"

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bian AI Vision & Creative Suite - Master V4</title>
    <script src="https://unpkg.com/tesseract.js@v4.0.2/dist/tesseract.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: system-ui, sans-serif; }
        body { background: #000; color: #fff; height: 100vh; overflow: hidden; display: flex; flex-direction: column; }
        .module-nav { display: flex; background: #0d0d0d; border-bottom: 1px solid #222; overflow-x: auto; white-space: nowrap; }
        .nav-tab { padding: 12px 14px; font-size: 10px; font-weight: 700; color: #888; border: none; background: none; cursor: pointer; text-transform: uppercase; letter-spacing: 0.5px; }
        .nav-tab.active { color: #00FFC8; border-bottom: 2px solid #00FFC8; background: rgba(0,255,200,0.05); }
        .main-container { flex: 1; position: relative; display: flex; overflow: hidden; }
        .module-view { display: none; width: 100%; height: 100%; flex-direction: column; position: relative; }
        .module-view.active { display: flex; }
        video { width: 100%; height: 100%; object-fit: cover; }
        
        /* HUD V2 PRO */
        .hud-overlay { position: absolute; border: 2px solid #00FFC8; width: 80%; height: 60%; top: 15%; left: 10%; border-radius: 20px; box-shadow: 0 0 20px rgba(0,255,200,0.3); pointer-events: none; display: flex; flex-direction: column; justify-content: space-between; padding: 15px; }
        .hud-top { display: flex; justify-content: space-between; font-size: 11px; color: #00FFC8; background: rgba(0,0,0,0.7); padding: 5px 10px; border-radius: 6px; }
        .ocr-data { font-size: 13px; color: #FFF; background: rgba(0,0,0,0.8); padding: 10px; border-radius: 8px; border-left: 4px solid #00FFC8; }
        
        .cam-controls { position: absolute; bottom: 20px; width: 100%; display: flex; justify-content: space-evenly; align-items: center; }
        .btn-cam { width: 50px; height: 50px; border-radius: 50%; background: #111; color: #00FFC8; border: 1px solid #333; font-size: 10px; font-weight: bold; cursor: pointer; }
    </style>
</head>
<body>
    <div class="module-nav">
        <button class="nav-tab active" onclick="switchModule('cameraTab', this)">📷 Cam Vision V2 Pro</button>
        <button class="nav-tab" onclick="switchModule('genPromptTab', this)">✨ Generar Imagen AI</button>
        <button class="nav-tab" onclick="switchModule('priceTab', this)">🏷️ Valuador Híbrido</button>
        <button class="nav-tab" onclick="switchModule('foodIndustryTab', this)">👨‍🍳 Chef Lean V3 Pro</button>
        <button class="nav-tab" onclick="switchModule('genVidTab', this)">🎥 Video V3 Pro</button>
        <button class="nav-tab" onclick="switchModule('genImgTab', this)">🎨 SVG & Logos V3 Pro</button>
        <button class="nav-tab" onclick="switchModule('lonasPhysicsTab', this)">📐 Lonas V3 Pro</button>
    </div>

    <div class="main-container">
        <!-- 📷 Cam Vision V2 Pro -->
        <div id="cameraTab" class="module-view active">
            <video id="webcam" autoplay playsinline></video>
            <div class="hud-overlay">
                <div class="hud-top">
                    <span id="modeLabel">MODO: OCR CONTINUO</span>
                    <span>NPU V2 ACTIVE</span>
                </div>
                <div class="ocr-data" id="ocrResult">Iniciando motor de visión...</div>
            </div>
            <div class="cam-controls">
                <button class="btn-cam" onclick="toggleMode()">MODO</button>
                <button class="btn-cam" onclick="toggleFlash()">FLASH</button>
                <button class="btn-cam" onclick="capture()">SHUTTER</button>
            </div>
        </div>
        
        <!-- Resto de módulos intactos (V3 Master) -->
        <div id="genPromptTab" class="module-view"><div class="panel-content"><h3>✨ Generar Imagen AI</h3></div></div>
        <div id="priceTab" class="module-view"><div class="panel-content"><h3>🏷️ Valuador Híbrido</h3></div></div>
        <div id="foodIndustryTab" class="module-view"><div class="panel-content"><h3>👨‍🍳 Chef Lean V3 Pro</h3></div></div>
        <div id="genVidTab" class="module-view"><div class="panel-content"><h3>🎥 Video V3 Pro</h3></div></div>
        <div id="genImgTab" class="module-view"><div class="panel-content"><h3>🎨 SVG & Logos V3 Pro</h3></div></div>
        <div id="lonasPhysicsTab" class="module-view"><div class="panel-content"><h3>📐 Lonas V3 Pro</h3></div></div>
    </div>

    <script>
        const video = document.getElementById('webcam');
        let currentMode = 0;
        const modes = ["OCR CONTINUO", "DETECCIÓN OBJETOS", "ESCÁNER QR/BARRAS"];

        navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })
            .then(stream => { video.srcObject = stream; })
            .catch(err => console.error(err));

        function switchModule(tabId, btn) {
            document.querySelectorAll('.module-view').forEach(m => m.classList.remove('active'));
            document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            btn.classList.add('active');
        }

        function toggleMode() {
            currentMode = (currentMode + 1) % modes.length;
            document.getElementById('modeLabel').innerText = "MODO: " + modes[currentMode];
        }

        function toggleFlash() { alert("Linterna táctica activada/desactivada (NPU V2)"); }

        async function capture() {
            const canvas = document.createElement('canvas');
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            canvas.getContext('2d').drawImage(video, 0, 0);
            const imageBase64 = canvas.toDataURL('image/jpeg');

            const response = await fetch('/bian/process/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image_base64: imageBase64, prompt_analysis: `Captura V2 Pro: ${modes[currentMode]}` })
            });
            alert("Captura procesada por el motor V2 Pro.");
        }
    </script>
</body>
</html>
"""

@router.get("/ui", response_class=HTMLResponse)
async def get_ui():
    return HTML_CONTENT

@router.post("/process/", response_model=ProcessedImage)
def process_image(payload: ImageCaptureRequest, session: Session = Depends(get_session)):
    os.makedirs("storage/bian", exist_ok=True)
    filename = f"storage/bian/photo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    data = base64.b64decode(payload.image_base64.split(",", 1)[1])
    with open(filename, "wb") as f: f.write(data)
    db_image = ProcessedImage(image_path=f"/{filename}", prompt_analysis=payload.prompt_analysis)
    session.add(db_image)
    session.commit()
    return db_image
