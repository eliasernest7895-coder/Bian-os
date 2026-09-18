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
    prompt_analysis: str = "Depth-Map NPU & Studio RAW V8 Ultra"

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bian AI Suite - Studio RAW V8 Ultra</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: system-ui, sans-serif; }
        body { background: #000; color: #fff; height: 100vh; overflow: hidden; display: flex; flex-direction: column; }
        
        .module-nav { display: flex; background: #0d0d0d; border-bottom: 1px solid #222; overflow-x: auto; white-space: nowrap; }
        .nav-tab { padding: 12px 14px; font-size: 10px; font-weight: 700; color: #888; border: none; background: none; cursor: pointer; text-transform: uppercase; letter-spacing: 0.5px; }
        .nav-tab.active { color: #00FFC8; border-bottom: 2px solid #00FFC8; background: rgba(0,255,200,0.05); }

        .header { padding: 10px 18px; background: rgba(0,0,0,0.85); display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #111; }
        .badge { color: #00FFC8; font-weight: bold; font-size: 10px; border: 1px solid #00FFC8; padding: 3px 6px; border-radius: 4px; }
        
        .main-container { flex: 1; position: relative; display: flex; overflow: hidden; }
        .module-view { display: none; width: 100%; height: 100%; flex-direction: column; position: relative; }
        .module-view.active { display: flex; }

        video { width: 100%; height: 100%; object-fit: cover; }
        
        .hud-overlay { position: absolute; border: 2px solid #00FFC8; width: 88%; height: 65%; top: 12%; left: 6%; border-radius: 18px; box-shadow: 0 0 25px rgba(0,255,200,0.3); pointer-events: none; display: flex; flex-direction: column; justify-content: space-between; padding: 12px; }
        .hud-topbar { display: flex; justify-content: space-between; align-items: center; pointer-events: auto; }
        .hud-info { font-size: 9px; color: #00FFC8; background: rgba(0,0,0,0.75); padding: 4px 8px; border-radius: 4px; font-weight: bold; }
        
        .bbox-sujeto { position: absolute; top: 22%; left: 22%; width: 56%; height: 42%; border: 2px dashed #00FFC8; border-radius: 50% / 40%; pointer-events: none; }
        .action-chip-bar { position: absolute; bottom: 85px; left: 4%; width: 92%; display: flex; justify-content: space-around; gap: 4px; pointer-events: auto; }
        .chip-btn { background: rgba(0, 0, 0, 0.85); border: 1px solid #00FFC8; color: #00FFC8; padding: 7px 9px; border-radius: 20px; font-size: 10px; font-weight: 700; cursor: pointer; }

        .panel-content { padding: 16px; overflow-y: auto; flex: 1; background: #0a0a0a; }
        .card { background: #121212; border: 1px solid #222; border-radius: 12px; padding: 14px; margin-bottom: 14px; }
        .card h3 { color: #00FFC8; font-size: 14px; margin-bottom: 6px; }
        .card p { color: #aaa; font-size: 11px; line-height: 1.4; }
        .form-group { margin-top: 8px; }
        .form-group label { font-size: 10px; color: #00FFC8; display: block; margin-bottom: 3px; }
        .form-group select, .form-group input { width: 100%; background: #1a1a1a; border: 1px solid #333; color: #fff; padding: 8px; border-radius: 6px; font-size: 12px; }
        
        .preview-box { width: 100%; height: 250px; background: #000; border: 1px dashed #333; border-radius: 8px; display: flex; align-items: center; justify-content: center; margin-top: 10px; overflow: hidden; position: relative; }
        .preview-box canvas { max-width: 100%; max-height: 100%; object-fit: contain; }
        
        .controls { padding: 16px 24px; background: rgba(13,13,13,0.95); display: flex; justify-content: space-around; align-items: center; border-top: 1px solid #222; }
        .btn-shutter { width: 68px; height: 68px; border-radius: 50%; background: #fff; border: 4px solid #00FFC8; cursor: pointer; }
        .thumb-preview { width: 44px; height: 44px; border-radius: 8px; border: 2px solid #00FFC8; background: #111; overflow: hidden; cursor: pointer; display: flex; align-items: center; justify-content: center; }
        .thumb-preview img { width: 100%; height: 100%; object-fit: cover; }
        .btn-action { background: #1E1E1E; color: #fff; border: 1px solid #333; padding: 8px 14px; border-radius: 8px; font-size: 12px; font-weight: 600; cursor: pointer; }
    </style>
</head>
<body>
    <div class="module-nav">
        <button id="nav_cameraTab" class="nav-tab active" onclick="switchModule('cameraTab', this)">📷 Cam Vision</button>
        <button id="nav_depthTab" class="nav-tab" onclick="switchModule('depthTab', this)">🧠 Depth-Map NPU</button>
        <button id="nav_rawTab" class="nav-tab" onclick="switchModule('rawTab', this)">📸 Estudio RAW V8</button>
        <button id="nav_genVidTab" class="nav-tab" onclick="switchModule('genVidTab', this)">🎥 Video Motion V8</button>
        <button id="nav_genImgTab" class="nav-tab" onclick="switchModule('genImgTab', this)">🎨 SVG Logos V8</button>
        <button id="nav_lonasPhysicsTab" class="nav-tab" onclick="switchModule('lonasPhysicsTab', this)">📐 Lonas 3D V8</button>
    </div>

    <div class="header">
        <span style="font-weight: 700; font-size: 13px;" id="moduleTitle">BIAN AI SUITE V8 ULTRA</span>
        <span class="badge" id="netBadge">NPU PRO ENGINE</span>
    </div>

    <div class="main-container">
        <!-- 📷 Cam Vision -->
        <div id="cameraTab" class="module-view active">
            <video id="webcam" autoplay playsinline></video>
            <div class="hud-overlay">
                <div class="hud-topbar"><span class="hud-info">SENSOR EN VIVO | 60 FPS</span></div>
            </div>
            <div class="bbox-sujeto"></div>
            <div class="action-chip-bar">
                <button class="chip-btn" onclick="captureToDepth()">🧠 DEPTH NPU</button>
                <button class="chip-btn" onclick="captureToRaw()">📸 ENVIAR A RAW V8</button>
                <button class="chip-btn" onclick="captureDirect()">⚡ CAPTURAR</button>
            </div>
            <canvas id="cropCanvas" style="display:none;"></canvas>
        </div>

        <!-- 🧠 Depth-Map NPU -->
        <div id="depthTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>🧠 Estimador de Profundidad Monocular (Depth-Map NPU)</h3>
                    <p>Z-Buffer para reconstrucción volumétrica y paralaje 3D.</p>
                </div>
                <div class="card">
                    <div class="preview-box" id="depthPreviewBox">
                        <span style="font-size: 11px; color: #555;">Sin análisis de disparidad activo</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- 📸 Estudio RAW V8 Ultra -->
        <div id="rawTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>📸 Estudio RAW V8 Ultra (Histograma RGB & Colorimetría NPU)</h3>
                    <p>Calibración de curvas dinámicas, balance térmico Kelvin y monitoreo espectral en tiempo real.</p>
                </div>
                <div class="card">
                    <div class="preview-box" id="rawPreviewBox">
                        <span style="font-size: 11px; color: #555;">Carga un activo desde Cam Vision</span>
                    </div>

                    <!-- Canvas para el Histograma RGB -->
                    <div style="margin-top: 10px; background: #050505; border: 1px solid #222; border-radius: 6px; padding: 6px;">
                        <span style="font-size: 9px; color: #00FFC8; font-weight: bold; display: block; margin-bottom: 4px;">📊 HISTOGRAMA RGB ESPECTRAL (NPU MONITOR)</span>
                        <canvas id="histCanvas" width="340" height="70" style="width: 100%; display: block;"></canvas>
                    </div>

                    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:8px; margin-top: 10px;">
                        <div class="form-group">
                            <label>Compensación EV (<span id="evLabel">0.0</span>):</label>
                            <input type="range" id="rawEvV8" min="-20" max="20" value="0" oninput="applyRawGradingV8()">
                        </div>
                        <div class="form-group">
                            <label>Contraste / Micro-textura (<span id="contrastLabel">1.0</span>x):</label>
                            <input type="range" id="rawContrastV8" min="7" max="15" value="10" oninput="applyRawGradingV8()">
                        </div>
                    </div>

                    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:8px;">
                        <div class="form-group">
                            <label>Temperatura Kelvin:</label>
                            <select id="rawKelvinV8" onchange="applyRawGradingV8()">
                                <option value="5500">5500K (Luz de Día Neutra)</option>
                                <option value="3200">3200K (Tungsteno Cálido Gourmet)</option>
                                <option value="7800">7800K (Sombra / Cyber Neón Frío)</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Tinte Cromático (Tint):</label>
                            <select id="rawTintV8" onchange="applyRawGradingV8()">
                                <option value="neutral">Neutro (0.0)</option>
                                <option value="magenta">Inyección Magenta (+15)</option>
                                <option value="emerald">Inyección Esmeralda (-15)</option>
                            </select>
                        </div>
                    </div>

                    <button class="btn-action" style="background: #00FFC8; color: #000; font-weight: bold; margin-top: 12px; width: 100%;" onclick="saveRawExportV8()">💾 Exportar Master Revelado RAW V8</button>
                </div>
            </div>
        </div>

        <!-- Módulos Consolidados -->
        <div id="genVidTab" class="module-view"><div class="panel-content"><div class="card"><h3>🎥 Video Motion V8</h3></div></div></div>
        <div id="genImgTab" class="module-view"><div class="panel-content"><div class="card"><h3>🎨 SVG Logos V8</h3></div></div></div>
        <div id="lonasPhysicsTab" class="module-view"><div class="panel-content"><div class="card"><h3>📐 Lonas 3D V8</h3></div></div></div>
    </div>

    <div class="controls" id="bottomControls">
        <div class="thumb-preview" id="thumbBox" onclick="openGallery()"><span style="font-size: 9px; color: #666;">GALERÍA</span></div>
        <button class="btn-shutter" onclick="captureDirect()"></button>
        <button class="btn-action" style="color: #00FFC8;" onclick="captureToRaw()">RAW V8</button>
    </div>

    <script>
        const video = document.getElementById('webcam');
        const cropCanvas = document.getElementById('cropCanvas');
        let rawImage = new Image();
        let gradedCanvas = document.createElement('canvas');

        navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })
            .then(stream => { video.srcObject = stream; })
            .catch(err => console.error(err));

        function switchModule(tabId, btn) {
            document.querySelectorAll('.module-view').forEach(m => m.classList.remove('active'));
            document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            if(btn) btn.classList.add('active');
            document.getElementById('bottomControls').style.display = (tabId === 'cameraTab') ? 'flex' : 'none';
        }

        function captureToRaw() {
            if(video.videoWidth === 0) return;
            cropCanvas.width = 360;
            cropCanvas.height = 270;
            const ctx = cropCanvas.getContext('2d');
            ctx.drawImage(video, 0, 0, 360, 270);

            rawImage.onload = () => {
                switchModule('rawTab', document.getElementById('nav_rawTab'));
                applyRawGradingV8();
            };
            rawImage.src = cropCanvas.toDataURL('image/jpeg');
        }

        function captureToDepth() {
            switchModule('depthTab', document.getElementById('nav_depthTab'));
        }

        function applyRawGradingV8() {
            if(!rawImage.src) return;
            const box = document.getElementById('rawPreviewBox');
            box.innerHTML = "";

            gradedCanvas.width = 360;
            gradedCanvas.height = 270;
            const ctx = gradedCanvas.getContext('2d');
            ctx.drawImage(rawImage, 0, 0, 360, 270);

            const evVal = parseFloat(document.getElementById('rawEvV8').value) / 10;
            const contrast = parseFloat(document.getElementById('rawContrastV8').value) / 10;
            const kelvin = document.getElementById('rawKelvinV8').value;
            const tint = document.getElementById('rawTintV8').value;

            document.getElementById('evLabel').innerText = (evVal > 0 ? "+" : "") + evVal.toFixed(1);
            document.getElementById('contrastLabel').innerText = contrast.toFixed(1);

            const imgData = ctx.getImageData(0, 0, 360, 270);
            const d = imgData.data;

            // Vectores de canal para el Histograma
            const histR = new Array(256).fill(0);
            const histG = new Array(256).fill(0);
            const histB = new Array(256).fill(0);

            for(let i = 0; i < d.length; i += 4) {
                let r = d[i];
                let g = d[i+1];
                let b = d[i+2];

                // 1. Compensación de Exposición EV
                if(evVal !== 0) {
                    const factor = Math.pow(2, evVal);
                    r *= factor; g *= factor; b *= factor;
                }

                // 2. Curva de Contraste
                r = ((r / 255 - 0.5) * contrast + 0.5) * 255;
                g = ((g / 255 - 0.5) * contrast + 0.5) * 255;
                b = ((b / 255 - 0.5) * contrast + 0.5) * 255;

                // 3. Balance Kelvin
                if(kelvin === "3200") { r *= 1.15; b *= 0.85; }
                else if(kelvin === "7800") { r *= 0.85; b *= 1.18; }

                // 4. Tint
                if(tint === "magenta") { g *= 0.90; r *= 1.05; }
                else if(tint === "emerald") { g *= 1.10; r *= 0.95; }

                // Clamp 0-255
                r = Math.min(255, Math.max(0, Math.round(r)));
                g = Math.min(255, Math.max(0, Math.round(g)));
                b = Math.min(255, Math.max(0, Math.round(b)));

                d[i] = r; d[i+1] = g; d[i+2] = b;

                // Registro del Histograma
                histR[r]++; histG[g]++; histB[b]++;
            }

            ctx.putImageData(imgData, 0, 0);
            box.appendChild(gradedCanvas);

            drawHistogramRGB(histR, histG, histB);
        }

        function drawHistogramRGB(rArr, gArr, bArr) {
            const hCanvas = document.getElementById('histCanvas');
            const hCtx = hCanvas.getContext('2d');
            hCtx.clearRect(0, 0, 340, 70);

            const maxVal = Math.max(...rArr, ...gArr, ...bArr) || 1;

            function drawCurve(arr, color) {
                hCtx.strokeStyle = color;
                hCtx.lineWidth = 1;
                hCtx.beginPath();
                for(let x = 0; x < 256; x++) {
                    const normX = (x / 255) * 340;
                    const normY = 70 - (arr[x] / maxVal) * 65;
                    if(x === 0) hCtx.moveTo(normX, normY);
                    else hCtx.lineTo(normX, normY);
                }
                hCtx.stroke();
            }

            drawCurve(rArr, "rgba(255, 60, 60, 0.85)");
            drawCurve(gArr, "rgba(0, 255, 120, 0.85)");
            drawCurve(bArr, "rgba(60, 160, 255, 0.85)");
        }

        async function saveRawExportV8() {
            if(!gradedCanvas) return;
            const res = await fetch('/bian/process/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image_base64: gradedCanvas.toDataURL('image/jpeg'), prompt_analysis: 'Exportacion Estudio RAW V8' })
            });
            if(res.ok) alert("✔ Master RAW V8 guardado con calibracion de colorometria.");
        }

        async function captureDirect() {
            captureToRaw();
        }

        function openGallery() {}
    </script>
</body>
</html>
"""

@router.get("/ui", response_class=HTMLResponse)
async def get_ui():
    return HTML_CONTENT

@router.get("/status")
async def status():
    return {
        "module": "bian",
        "engine": "Depth-Map & Studio RAW V8 Ultra Active",
        "status": "online"
    }

@router.post("/process/", response_model=ProcessedImage)
def process_image(payload: ImageCaptureRequest, session: Session = Depends(get_session)):
    os.makedirs("storage/bian", exist_ok=True)
    filename = f"storage/bian/photo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    header, encoded = payload.image_base64.split(",", 1)
    data = base64.b64decode(encoded)
    with open(filename, "wb") as f:
        f.write(data)
    db_image = ProcessedImage(image_path=f"/{filename}", prompt_analysis=payload.prompt_analysis)
    session.add(db_image)
    session.commit()
    session.refresh(db_image)
    return db_image

@router.get("/images/", response_model=list[ProcessedImage])
def list_images(session: Session = Depends(get_session)):
    return session.exec(select(ProcessedImage)).all()
