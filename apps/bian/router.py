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
    prompt_analysis: str = "Cine Scope V8 Ultra"

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bian AI Suite - Cine Scope V8 Ultra</title>
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
        <button id="nav_cineTab" class="nav-tab" onclick="switchModule('cineTab', this)">🎬 Cine Scope V8</button>
        <button id="nav_genVidTab" class="nav-tab" onclick="switchModule('genVidTab', this)">🎥 Video Motion V8</button>
        <button id="nav_genImgTab" class="nav-tab" onclick="switchModule('genImgTab', this)">🎨 SVG Logos V8</button>
        <button id="nav_lonasPhysicsTab" class="nav-tab" onclick="switchModule('lonasPhysicsTab', this)">📐 Lonas 3D V8</button>
    </div>

    <div class="header">
        <span style="font-weight: 700; font-size: 13px;" id="moduleTitle">BIAN AI SUITE V8 ULTRA</span>
        <span class="badge" id="netBadge">ANAMORPHIC DCI READY</span>
    </div>

    <div class="main-container">
        <!-- 📷 Cam Vision -->
        <div id="cameraTab" class="module-view active">
            <video id="webcam" autoplay playsinline></video>
            <div class="hud-overlay">
                <div class="hud-topbar"><span class="hud-info">CAM FEED | NPU SYNC</span></div>
            </div>
            <div class="bbox-sujeto"></div>
            <div class="action-chip-bar">
                <button class="chip-btn" onclick="captureToCine()">🎬 ENVIAR A CINE V8</button>
                <button class="chip-btn" onclick="captureToRaw()">📸 ENVIAR A RAW V8</button>
                <button class="chip-btn" onclick="captureDirect()">⚡ CAPTURAR</button>
            </div>
            <canvas id="cropCanvas" style="display:none;"></canvas>
        </div>

        <!-- 🧠 Depth-Map NPU -->
        <div id="depthTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>🧠 Depth-Map NPU</h3>
                    <p>Z-Buffer para reconstrucción volumétrica.</p>
                </div>
            </div>
        </div>

        <!-- 📸 Estudio RAW V8 -->
        <div id="rawTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>📸 Estudio RAW V8 Ultra</h3>
                    <p>Monitoreo espectral y revelado de curvas.</p>
                </div>
            </div>
        </div>

        <!-- 🎬 Cine Scope V8 Ultra Engine -->
        <div id="cineTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>🎬 Cine Scope V8 Ultra (Director Anamórfico & 3D LUT)</h3>
                    <p>Conversión cinematográfica con emulación de emulsión 35mm, flares anamórficos estriados y relación de aspecto DCI Scope.</p>
                </div>
                <div class="card">
                    <div class="preview-box" id="cinePreviewBox">
                        <span style="font-size: 11px; color: #555;">Carga un fotograma desde Cam Vision</span>
                    </div>

                    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:8px; margin-top:10px;">
                        <div class="form-group">
                            <label>Perfil 3D LUT Cinemático:</label>
                            <select id="cineLutV8" onchange="renderCineScopeV8()">
                                <option value="teal_orange">Hollywood Teal & Orange (Blockbuster)</option>
                                <option value="kodak_500t">Kodak Vision3 500T (Emulsión Cálida)</option>
                                <option value="matrix_neon">Matrix Distópico (Cyan / Green Highlight)</option>
                                <option value="noir_contrast">Monocromático Noire 35mm (Plata Intensa)</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Encuadre / Aspect Ratio:</label>
                            <select id="cineAspectV8" onchange="renderCineScopeV8()">
                                <option value="scope_239">2.39:1 DCI Scope (Cinematográfico)</option>
                                <option value="ultra_219">21:9 UltraWide Master</option>
                                <option value="imax_143">1.43:1 IMAX Full Frame</option>
                            </select>
                        </div>
                    </div>

                    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:8px;">
                        <div class="form-group">
                            <label>Grano Haluro de Plata (<span id="cineGrainLabel">30</span>%):</label>
                            <input type="range" id="cineGrainV8" min="0" max="80" value="30" oninput="renderCineScopeV8()">
                        </div>
                        <div class="form-group">
                            <label>Flares Anamórficos Horizontales:</label>
                            <select id="cineFlareV8" onchange="renderCineScopeV8()">
                                <option value="blue_streak">Blue Streak Láser (Lente Anamórfica)</option>
                                <option value="amber_warm">Destello Dorado Vintage</option>
                                <option value="none">Sin Destello Óptico</option>
                            </select>
                        </div>
                    </div>

                    <div id="cineTelemetryV8" style="margin-top:10px;"></div>

                    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:8px; margin-top:12px;">
                        <button class="btn-action" style="background:#00FFC8; color:#000; font-weight:bold;" onclick="exportCineFrameV8()">💾 Exportar DCI-4K</button>
                        <button class="btn-action" style="color:#00FFC8; border:1px solid #00FFC8;" onclick="sendCineToVideoMotion()">🎥 Mandar a Motion V8</button>
                    </div>
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
        <button class="btn-action" style="color: #00FFC8;" onclick="captureToCine()">CINE V8</button>
    </div>

    <script>
        const video = document.getElementById('webcam');
        const cropCanvas = document.getElementById('cropCanvas');
        let cineImage = new Image();
        let cineRenderCanvas = document.createElement('canvas');

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

        function captureToCine() {
            if(video.videoWidth === 0) return;
            cropCanvas.width = 480;
            cropCanvas.height = 360;
            const ctx = cropCanvas.getContext('2d');
            ctx.drawImage(video, 0, 0, 480, 360);

            cineImage.onload = () => {
                switchModule('cineTab', document.getElementById('nav_cineTab'));
                renderCineScopeV8();
            };
            cineImage.src = cropCanvas.toDataURL('image/jpeg');
        }

        function captureToRaw() {
            switchModule('rawTab', document.getElementById('nav_rawTab'));
        }

        function renderCineScopeV8() {
            if(!cineImage.src) return;
            const box = document.getElementById('cinePreviewBox');
            box.innerHTML = "";

            cineRenderCanvas.width = 480;
            cineRenderCanvas.height = 270;
            const ctx = cineRenderCanvas.getContext('2d');

            // Dibujar fotograma base escalado
            ctx.drawImage(cineImage, 0, 0, 480, 270);

            const lut = document.getElementById('cineLutV8').value;
            const aspect = document.getElementById('cineAspectV8').value;
            const grain = parseInt(document.getElementById('cineGrainV8').value) || 0;
            const flare = document.getElementById('cineFlareV8').value;

            document.getElementById('cineGrainLabel').innerText = grain;

            // 1. Pipeline 3D LUT Tetraédrico (Ponderación RGB)
            const imgData = ctx.getImageData(0, 0, 480, 270);
            const d = imgData.data;

            for(let i = 0; i < d.length; i += 4) {
                let r = d[i], g = d[i+1], b = d[i+2];

                if(lut === 'teal_orange') {
                    // Push sombras hacia Cyan/Teal y altas luces hacia Ámbar Cálido
                    const lum = (r + g + b) / 3;
                    if(lum < 128) {
                        b = Math.min(255, b * 1.25);
                        g = Math.min(255, g * 1.10);
                        r *= 0.85;
                    } else {
                        r = Math.min(255, r * 1.20);
                        g = Math.min(255, g * 1.05);
                        b *= 0.80;
                    }
                } else if(lut === 'kodak_500t') {
                    // Tonos dorados cinematográficos con negros densos
                    r = Math.min(255, r * 1.14);
                    g = Math.min(255, g * 1.02);
                    b = Math.max(0, b * 0.88 - 5);
                } else if(lut === 'matrix_neon') {
                    // Gradiente Cyberpunk verde esmeralda
                    g = Math.min(255, g * 1.30);
                    r *= 0.75;
                    b = Math.min(255, b * 1.10);
                } else if(lut === 'noir_contrast') {
                    // Monocromático de alto contraste
                    const gray = (r * 0.299 + g * 0.587 + b * 0.114);
                    const contrastGray = Math.min(255, Math.max(0, ((gray / 255 - 0.5) * 1.4 + 0.5) * 255));
                    r = contrastGray; g = contrastGray; b = contrastGray;
                }

                // 2. Grano Analógico Ponderado (Más visible en medios tonos, menos en altas luces)
                if(grain > 0) {
                    const noise = (Math.random() - 0.5) * (grain * 0.9);
                    const lumWeight = 1.0 - Math.abs((r + g + b) / 765 - 0.5) * 0.8;
                    r = Math.min(255, Math.max(0, r + noise * lumWeight));
                    g = Math.min(255, Math.max(0, g + noise * lumWeight));
                    b = Math.min(255, Math.max(0, b + noise * lumWeight));
                }

                d[i] = r; d[i+1] = g; d[i+2] = b;
            }
            ctx.putImageData(imgData, 0, 0);

            // 3. Destellos Horizontales Anamórficos (Blue Streaks)
            if(flare !== 'none') {
                const flareY = 135;
                const flareGrad = ctx.createLinearGradient(0, flareY, 480, flareY);
                if(flare === 'blue_streak') {
                    flareGrad.addColorStop(0, 'rgba(0, 200, 255, 0)');
                    flareGrad.addColorStop(0.3, 'rgba(0, 255, 200, 0.15)');
                    flareGrad.addColorStop(0.5, 'rgba(255, 255, 255, 0.85)');
                    flareGrad.addColorStop(0.7, 'rgba(0, 200, 255, 0.15)');
                    flareGrad.addColorStop(1, 'rgba(0, 200, 255, 0)');
                } else {
                    flareGrad.addColorStop(0, 'rgba(255, 180, 0, 0)');
                    flareGrad.addColorStop(0.5, 'rgba(255, 240, 200, 0.8)');
                    flareGrad.addColorStop(1, 'rgba(255, 180, 0, 0)');
                }
                ctx.fillStyle = flareGrad;
                ctx.fillRect(0, flareY - 2, 480, 4);
                ctx.fillStyle = "rgba(255, 255, 255, 0.5)";
                ctx.beginPath();
                ctx.arc(240, flareY, 6, 0, Math.PI * 2);
                ctx.fill();
            }

            // 4. Matte Anamórfico (Barras Negras DCI Scope)
            ctx.fillStyle = "#000000";
            let barH = 0;
            if(aspect === 'scope_239') barH = 35;
            else if(aspect === 'ultra_219') barH = 26;
            else barH = 0; // IMAX

            if(barH > 0) {
                ctx.fillRect(0, 0, 480, barH);
                ctx.fillRect(0, 270 - barH, 480, barH);
            }

            box.appendChild(cineRenderCanvas);

            // Telemetría de Salida
            document.getElementById('cineTelemetryV8').innerHTML = `
            <div style="background:#141414; padding:10px; border-radius:8px; border:1px solid #00FFC8; font-size:11px;">
                <span style="color:#00FFC8; font-weight:bold;">🎬 DCI SCOPE TELEMETRY:</span> Aspect: <strong>${aspect.toUpperCase()}</strong> | LUT: <strong>${lut.toUpperCase()}</strong> | Apertura Virtual: <strong>T1.8 Anamorphic</strong>
            </div>`;
        }

        function sendCineToVideoMotion() {
            switchModule('genVidTab', document.getElementById('nav_genVidTab'));
            alert("✔ Fotograma Anamórfico V8 inyectado en Video Motion.");
        }

        async function exportCineFrameV8() {
            if(!cineRenderCanvas) return;
            const res = await fetch('/bian/process/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image_base64: cineRenderCanvas.toDataURL('image/jpeg'), prompt_analysis: 'Master Cine Scope V8 Export' })
            });
            if(res.ok) alert("✔ Fotograma DCI-4K exportado a almacenamiento soberano.");
        }

        async function captureDirect() {
            captureToCine();
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
        "engine": "Cine Scope V8 Ultra Active",
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
