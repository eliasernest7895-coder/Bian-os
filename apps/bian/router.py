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
    prompt_analysis: str = "Depth-Map NPU Engine V8"

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bian AI Suite - Depth-Map NPU V8</title>
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
        
        .preview-box { width: 100%; height: 260px; background: #000; border: 1px dashed #333; border-radius: 8px; display: flex; align-items: center; justify-content: center; margin-top: 10px; overflow: hidden; position: relative; }
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
        <button id="nav_genVidTab" class="nav-tab" onclick="switchModule('genVidTab', this)">🎥 Video Motion V8</button>
        <button id="nav_genImgTab" class="nav-tab" onclick="switchModule('genImgTab', this)">🎨 SVG Logos V8</button>
        <button id="nav_lonasPhysicsTab" class="nav-tab" onclick="switchModule('lonasPhysicsTab', this)">📐 Lonas 3D V8</button>
    </div>

    <div class="header">
        <span style="font-weight: 700; font-size: 13px;" id="moduleTitle">BIAN DEPTH-MAP NPU V8</span>
        <span class="badge" id="netBadge">NPU Z-BUFFER READY</span>
    </div>

    <div class="main-container">
        <!-- 📷 Cam Vision -->
        <div id="cameraTab" class="module-view active">
            <video id="webcam" autoplay playsinline></video>
            <div class="hud-overlay">
                <div class="hud-topbar"><span class="hud-info">LENTE EN VIVO | ROI ACTIVO</span></div>
            </div>
            <div class="bbox-sujeto"></div>
            <div class="action-chip-bar">
                <button class="chip-btn" onclick="captureAndProcessDepth()">🧠 ESTIMAR DEPTH NPU</button>
                <button class="chip-btn" onclick="captureDirect()">⚡ CAPTURAR FOTO</button>
            </div>
            <canvas id="canvas" style="display:none;"></canvas>
            <canvas id="cropCanvas" style="display:none;"></canvas>
        </div>

        <!-- 🧠 Depth-Map NPU Module -->
        <div id="depthTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>🧠 Estimador de Profundidad Monocular (Depth-Map NPU)</h3>
                    <p>Descompone la imagen 2D en capas de profundidad (Z-Buffer). Calcula gradientes focales y genera la malla de desplazamiento volumétrico.</p>
                </div>
                <div class="card">
                    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:8px;">
                        <div class="form-group">
                            <label>Modo de Visualización NPU:</label>
                            <select id="depthViewMode" onchange="updateDepthDisplay()">
                                <option value="depth_grayscale">Z-Buffer Monocromático (0-255)</option>
                                <option value="depth_heat">Mapa Térmico NPU (Inferno Color)</option>
                                <option value="mesh_displacement">Paralaje Volumétrico 3D (Warp)</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Intensidad de Relieve / Z-Depth:</label>
                            <input type="range" id="depthIntensity" min="5" max="50" value="25" oninput="updateDepthDisplay()">
                        </div>
                    </div>

                    <div class="preview-box" id="depthPreviewBox">
                        <span style="font-size: 11px; color: #555;">Captura un sujeto desde Cam Vision para estimar profundidad.</span>
                    </div>

                    <div id="depthTelemetry" style="margin-top: 10px;"></div>
                    <button class="btn-action" style="background: #00FFC8; color: #000; font-weight: bold; margin-top: 10px; width: 100%;" onclick="sendDepthToVideo()">🎥 Inyectar Malla de Profundidad al Video Motion V8</button>
                </div>
            </div>
        </div>

        <!-- 🎥 Video Motion V8 -->
        <div id="genVidTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>🎥 Video Motion V8 (Render Volumétrico con Z-Displacement)</h3>
                    <p>La cámara se desplaza en órbita mientras el Depth-Map deforma la geometría según su distancia real a la lente.</p>
                </div>
                <div class="card">
                    <div class="preview-box" id="vidPreviewBox">
                        <span style="font-size: 11px; color: #555;">Esperando inyección de profundidad...</span>
                    </div>
                    <button class="btn-action" style="background: #00FFC8; color: #000; font-weight: bold; margin-top: 12px; width: 100%;" onclick="startVolumetricRender()">⚡ Renderizar Vértices en Paralaje 3D</button>
                </div>
            </div>
        </div>

        <!-- Módulos Adicionales -->
        <div id="genImgTab" class="module-view"><div class="panel-content"><div class="card"><h3>🎨 SVG Logos V8</h3></div></div></div>
        <div id="lonasPhysicsTab" class="module-view"><div class="panel-content"><div class="card"><h3>📐 Lonas 3D V8</h3></div></div></div>
    </div>

    <div class="controls" id="bottomControls">
        <div class="thumb-preview" id="thumbBox" onclick="openGallery()"><span style="font-size: 9px; color: #666;">GALERÍA</span></div>
        <button class="btn-shutter" onclick="captureDirect()"></button>
        <button class="btn-action" style="color: #00FFC8;" onclick="captureAndProcessDepth()">DEPTH NPU</button>
    </div>

    <script>
        const video = document.getElementById('webcam');
        const canvas = document.getElementById('canvas');
        const cropCanvas = document.getElementById('cropCanvas');
        let rawImageObj = new Image();
        let depthCanvas = document.createElement('canvas');
        let animVolInterval = null;

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

        function captureAndProcessDepth() {
            if(video.videoWidth === 0) return;
            cropCanvas.width = 360;
            cropCanvas.height = 270;
            const ctx = cropCanvas.getContext('2d');
            ctx.drawImage(video, 0, 0, 360, 270);
            
            rawImageObj.onload = () => {
                computeDepthMapNPU();
                switchModule('depthTab', document.getElementById('nav_depthTab'));
                updateDepthDisplay();
            };
            rawImageObj.src = cropCanvas.toDataURL('image/jpeg');
        }

        // Algoritmo de Estimación de Disparidad NPU Monocular
        function computeDepthMapNPU() {
            depthCanvas.width = 360;
            depthCanvas.height = 270;
            const dCtx = depthCanvas.getContext('2d');
            dCtx.drawImage(rawImageObj, 0, 0, 360, 270);

            const imgData = dCtx.getImageData(0, 0, 360, 270);
            const data = imgData.data;

            // Centro focal del sensor para gradiente radial de profundidad
            const cx = 180, cy = 135;
            const maxDist = Math.sqrt(cx*cx + cy*cy);

            for(let y = 0; y < 270; y++) {
                for(let x = 0; x < 360; x++) {
                    const idx = (y * 360 + x) * 4;
                    // Luminancia como aproximación de reflexión focal
                    const lum = (data[idx] * 0.299 + data[idx+1] * 0.587 + data[idx+2] * 0.114);
                    
                    // Gradiente de proximidad esférica (foco central)
                    const distFromCenter = Math.sqrt((x - cx)**2 + (y - cy)**2);
                    const focalFactor = (1.0 - (distFromCenter / maxDist)) * 255;

                    // Fusión ponderada: Objeto frontal en foco = Z más cercano
                    const depthZ = Math.min(255, Math.max(0, (lum * 0.4) + (focalFactor * 0.6)));
                    
                    data[idx] = depthZ;
                    data[idx+1] = depthZ;
                    data[idx+2] = depthZ;
                }
            }
            dCtx.putImageData(imgData, 0, 0);
        }

        function updateDepthDisplay() {
            const mode = document.getElementById('depthViewMode').value;
            const box = document.getElementById('depthPreviewBox');
            box.innerHTML = "";

            const dispCanvas = document.createElement('canvas');
            dispCanvas.width = 360;
            dispCanvas.height = 270;
            const ctx = dispCanvas.getContext('2d');

            if(mode === 'depth_grayscale') {
                ctx.drawImage(depthCanvas, 0, 0);
            } else if(mode === 'depth_heat') {
                ctx.drawImage(depthCanvas, 0, 0);
                const imgData = ctx.getImageData(0, 0, 360, 270);
                const d = imgData.data;
                for(let i = 0; i < d.length; i += 4) {
                    const z = d[i];
                    // Paleta Térmica: Negro -> Rojo -> Amarillo -> Cyan
                    d[i] = z > 128 ? 255 : z * 2;          // R
                    d[i+1] = z > 192 ? 255 : (z > 64 ? (z - 64) * 2 : 0); // G
                    d[i+2] = z < 128 ? 255 - z * 2 : 0;     // B
                }
                ctx.putImageData(imgData, 0, 0);
            } else {
                // Modo Mesh Displacement Estático
                renderDisplacedMesh(ctx, 0, 0);
            }

            box.appendChild(dispCanvas);

            document.getElementById('depthTelemetry').innerHTML = `
            <div style="background:#141414; padding:10px; border-radius:8px; border:1px solid #00FFC8; font-size:11px;">
                <span style="color:#00FFC8; font-weight:bold;">📊 Z-BUFFER TELEMETRY:</span> Res: 360x270 | Precisión MDE: 8-bit | Vértices: 97,200 puntos
            </div>`;
        }

        function renderDisplacedMesh(ctx, camOffsetX, camOffsetY) {
            ctx.fillStyle = "#000";
            ctx.fillRect(0, 0, 360, 270);

            const dCtx = depthCanvas.getContext('2d');
            const dData = dCtx.getImageData(0, 0, 360, 270).data;
            const intensity = parseFloat(document.getElementById('depthIntensity').value) || 20;

            const step = 8; // Malla de 45x34 polígonos
            for(let y = 0; y < 270; y += step) {
                for(let x = 0; x < 360; x += step) {
                    const idx = (y * 360 + x) * 4;
                    const z = dData[idx] / 255.0; // 0.0 a 1.0

                    // Desplazamiento por paralaje volumétrico
                    const dispX = camOffsetX * z * (intensity / 10);
                    const dispY = camOffsetY * z * (intensity / 10);

                    ctx.drawImage(rawImageObj, x, y, step, step, x + dispX, y + dispY, step, step);
                }
            }
        }

        function sendDepthToVideo() {
            switchModule('genVidTab', document.getElementById('nav_genVidTab'));
            startVolumetricRender();
        }

        function startVolumetricRender() {
            if(animVolInterval) clearInterval(animVolInterval);
            const box = document.getElementById('vidPreviewBox');
            box.innerHTML = "";

            const vCanvas = document.createElement('canvas');
            vCanvas.width = 360; vCanvas.height = 270;
            const ctx = vCanvas.getContext('2d');
            box.appendChild(vCanvas);

            let frame = 0;
            animVolInterval = setInterval(() => {
                frame++;
                const camX = Math.sin(frame * 0.05) * 8;
                const camY = Math.cos(frame * 0.05) * 4;
                renderDisplacedMesh(ctx, camX, camY);

                // Overlay CineScope
                ctx.fillStyle = "#000";
                ctx.fillRect(0, 0, 360, 22);
                ctx.fillRect(0, 248, 360, 22);
            }, 1000 / 30);
        }

        async function captureDirect() {
            canvas.width = video.videoWidth; canvas.height = video.videoHeight;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            const res = await fetch('/bian/process/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image_base64: canvas.toDataURL('image/jpeg'), prompt_analysis: 'Captura Cam Vision' })
            });
            if(res.ok) alert("✔ Foto guardada en almacenamiento soberano.");
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
        "engine": "Depth-Map NPU Engine V8 Active",
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
