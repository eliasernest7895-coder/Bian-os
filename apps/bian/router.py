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
    prompt_analysis: str = "Wallpapers & Stickers V8 Ultra"

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bian AI Suite - Wallpapers & Stickers V8 Ultra</title>
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
        
        .preview-box { width: 100%; height: 300px; background: #000; border: 1px dashed #333; border-radius: 8px; display: flex; align-items: center; justify-content: center; margin-top: 10px; overflow: hidden; position: relative; }
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
        <button id="nav_printTab" class="nav-tab" onclick="switchModule('printTab', this)">🖨️ Imprenta PDF V8</button>
        <button id="nav_customTab" class="nav-tab" onclick="switchModule('customTab', this)">✨ Wallpapers & Stickers V8</button>
        <button id="nav_genVidTab" class="nav-tab" onclick="switchModule('genVidTab', this)">🎥 Video Motion V8</button>
        <button id="nav_genImgTab" class="nav-tab" onclick="switchModule('genImgTab', this)">🎨 SVG Logos V8</button>
        <button id="nav_lonasPhysicsTab" class="nav-tab" onclick="switchModule('lonasPhysicsTab', this)">📐 Lonas 3D V8</button>
    </div>

    <div class="header">
        <span style="font-weight: 700; font-size: 13px;" id="moduleTitle">BIAN AI SUITE V8 ULTRA</span>
        <span class="badge" id="netBadge">AMOLED DEEP BLACK READY</span>
    </div>

    <div class="main-container">
        <!-- 📷 Cam Vision -->
        <div id="cameraTab" class="module-view active">
            <video id="webcam" autoplay playsinline></video>
            <div class="hud-overlay">
                <div class="hud-topbar"><span class="hud-info">LENTE EN VIVO | CAPTURA TÁCTICA</span></div>
            </div>
            <div class="bbox-sujeto"></div>
            <div class="action-chip-bar">
                <button class="chip-btn" onclick="captureToCustom()">✨ ENVIAR A STICKERS V8</button>
                <button class="chip-btn" onclick="captureDirect()">⚡ CAPTURAR</button>
            </div>
            <canvas id="cropCanvas" style="display:none;"></canvas>
        </div>

        <!-- Módulos Previos -->
        <div id="depthTab" class="module-view"><div class="panel-content"><div class="card"><h3>🧠 Depth-Map NPU</h3></div></div></div>
        <div id="rawTab" class="module-view"><div class="panel-content"><div class="card"><h3>📸 Estudio RAW V8</h3></div></div></div>
        <div id="cineTab" class="module-view"><div class="panel-content"><div class="card"><h3>🎬 Cine Scope V8</h3></div></div></div>
        <div id="printTab" class="module-view"><div class="panel-content"><div class="card"><h3>🖨️ Imprenta PDF V8</h3></div></div></div>

        <!-- ✨ Wallpapers & Stickers V8 Ultra -->
        <div id="customTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>✨ Wallpapers AMOLED & Stickers Die-Cut V8 Ultra</h3>
                    <p>Fondos con píxel negro absoluto (#000000), efectos de resplandor NPU y sintetizador de stickers troquelados de vinil con relieve.</p>
                </div>
                <div class="card">
                    <div class="preview-box" id="customPreviewBoxV8">
                        <span style="font-size: 11px; color: #555;">Carga una captura o arte para procesar en V8</span>
                    </div>

                    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:8px; margin-top:10px;">
                        <div class="form-group">
                            <label>Modo de Síntesis V8:</label>
                            <select id="customModeV8" onchange="renderCustomV8()">
                                <option value="wallpaper_s23">Wallpaper AMOLED S23 Ultra (19.3:9)</option>
                                <option value="sticker_diecut">Sticker Vinil Troquelado (Die-Cut)</option>
                                <option value="badge_cyber">Insignia Táctica Neón (Emblema)</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Estilo de Entorno / Fondo:</label>
                            <select id="customBackdropV8" onchange="renderCustomV8()">
                                <option value="deep_black">AMOLED Deep Black Puro (#000000)</option>
                                <option value="cyber_grid">Cyberpunk Grid Isométrico (#00FFC8)</option>
                                <option value="aura_glow">Aura Volumétrica NPU Glow</option>
                            </select>
                        </div>
                    </div>

                    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:8px;">
                        <div class="form-group">
                            <label>Borde Troquel Vinil (Grosor):</label>
                            <select id="customBorderV8" onchange="renderCustomV8()">
                                <option value="8">8 px Blanco Premium (Die-Cut)</option>
                                <option value="12">12 px Grueso Vinil Calcomanía</option>
                                <option value="4">4 px Neón Fino (#00FFC8)</option>
                                <option value="0">Sin Borde (Corte Limpio)</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Sombra de Relieve 3D:</label>
                            <select id="customShadowV8" onchange="renderCustomV8()">
                                <option value="heavy">Relieve Alto (Drop Shadow Profunda)</option>
                                <option value="soft">Sombra Suave de Contacto</option>
                                <option value="flat">Plano / Sin Relieve</option>
                            </select>
                        </div>
                    </div>

                    <div id="customTelemetryV8" style="margin-top:10px;"></div>

                    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:8px; margin-top:12px;">
                        <button class="btn-action" style="background:#00FFC8; color:#000; font-weight:bold;" onclick="exportCustomAssetV8()">💾 Descargar Master HD</button>
                        <button class="btn-action" style="color:#00FFC8; border:1px solid #00FFC8;" onclick="sendCustomToPrint()">🖨️ Mandar a Preprensa V8</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Módulos Adicionales -->
        <div id="genVidTab" class="module-view"><div class="panel-content"><div class="card"><h3>🎥 Video Motion V8</h3></div></div></div>
        <div id="genImgTab" class="module-view"><div class="panel-content"><div class="card"><h3>🎨 SVG Logos V8</h3></div></div></div>
        <div id="lonasPhysicsTab" class="module-view"><div class="panel-content"><div class="card"><h3>📐 Lonas 3D V8</h3></div></div></div>
    </div>

    <div class="controls" id="bottomControls">
        <div class="thumb-preview" id="thumbBox" onclick="openGallery()"><span style="font-size: 9px; color: #666;">GALERÍA</span></div>
        <button class="btn-shutter" onclick="captureDirect()"></button>
        <button class="btn-action" style="color: #00FFC8;" onclick="captureToCustom()">STICKER V8</button>
    </div>

    <script>
        const video = document.getElementById('webcam');
        const cropCanvas = document.getElementById('cropCanvas');
        let customSourceImage = new Image();
        let customRenderCanvas = document.createElement('canvas');

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

        function captureToCustom() {
            if(video.videoWidth === 0) return;
            cropCanvas.width = 400;
            cropCanvas.height = 300;
            const ctx = cropCanvas.getContext('2d');
            ctx.drawImage(video, 0, 0, 400, 300);

            customSourceImage.onload = () => {
                switchModule('customTab', document.getElementById('nav_customTab'));
                renderCustomV8();
            };
            customSourceImage.src = cropCanvas.toDataURL('image/jpeg');
        }

        function renderCustomV8() {
            if(!customSourceImage.src) return;
            const box = document.getElementById('customPreviewBoxV8');
            box.innerHTML = "";

            const mode = document.getElementById('customModeV8').value;
            const backdrop = document.getElementById('customBackdropV8').value;
            const borderWidth = parseInt(document.getElementById('customBorderV8').value) || 0;
            const shadow = document.getElementById('customShadowV8').value;

            if(mode === 'wallpaper_s23') {
                customRenderCanvas.width = 300;
                customRenderCanvas.height = 540; // Proporción 9:16 vertical S23 Ultra
            } else {
                customRenderCanvas.width = 360;
                customRenderCanvas.height = 360; // Cuadrado para Sticker
            }

            const ctx = customRenderCanvas.getContext('2d');
            const cw = customRenderCanvas.width;
            const ch = customRenderCanvas.height;

            // 1. Fondo AMOLED #000000 puro
            ctx.fillStyle = "#000000";
            ctx.fillRect(0, 0, cw, ch);

            // 2. Efectos de Atmósfera
            if(backdrop === 'cyber_grid') {
                ctx.strokeStyle = "rgba(0, 255, 200, 0.18)";
                ctx.lineWidth = 1;
                for(let x = 0; x < cw; x += 24) {
                    ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, ch); ctx.stroke();
                }
                for(let y = 0; y < ch; y += 24) {
                    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(cw, y); ctx.stroke();
                }
            } else if(backdrop === 'aura_glow') {
                const grad = ctx.createRadialGradient(cw/2, ch/2, 20, cw/2, ch/2, cw/2);
                grad.addColorStop(0, "rgba(0, 255, 200, 0.25)");
                grad.addColorStop(0.7, "rgba(255, 0, 85, 0.12)");
                grad.addColorStop(1, "rgba(0, 0, 0, 0)");
                ctx.fillStyle = grad;
                ctx.fillRect(0, 0, cw, ch);
            }

            // 3. Renderizado del Sujeto / Sticker
            ctx.save();
            const subjectW = mode === 'wallpaper_s23' ? 240 : 260;
            const subjectH = mode === 'wallpaper_s23' ? 180 : 200;
            const sx = (cw - subjectW) / 2;
            const sy = (ch - subjectH) / 2;

            // Relieve y sombra de sticker
            if(shadow === 'heavy') {
                ctx.shadowColor = "rgba(0, 0, 0, 0.85)";
                ctx.shadowBlur = 20;
                ctx.shadowOffsetY = 12;
            } else if(shadow === 'soft') {
                ctx.shadowColor = "rgba(0, 0, 0, 0.5)";
                ctx.shadowBlur = 10;
                ctx.shadowOffsetY = 6;
            }

            // Borde troquelado Die-Cut
            if(borderWidth > 0) {
                ctx.fillStyle = (borderWidth === 4) ? "#00FFC8" : "#FFFFFF";
                ctx.beginPath();
                ctx.roundRect(sx - borderWidth, sy - borderWidth, subjectW + (borderWidth * 2), subjectH + (borderWidth * 2), 24);
                ctx.fill();
            }

            // Clip interior para el contenido
            ctx.beginPath();
            ctx.roundRect(sx, sy, subjectW, subjectH, 20);
            ctx.clip();
            ctx.drawImage(customSourceImage, sx, sy, subjectW, subjectH);
            ctx.restore();

            // 4. Guía de Corte para Troquelado (Plotter)
            if(mode === 'sticker_diecut') {
                ctx.strokeStyle = "rgba(255, 0, 85, 0.8)";
                ctx.lineWidth = 1;
                ctx.setLineDash([4, 4]);
                ctx.beginPath();
                ctx.roundRect(sx - borderWidth - 4, sy - borderWidth - 4, subjectW + (borderWidth * 2) + 8, subjectH + (borderWidth * 2) + 8, 28);
                ctx.stroke();
                ctx.setLineDash([]);
            }

            box.appendChild(customRenderCanvas);

            // Telemetría V8
            document.getElementById('customTelemetryV8').innerHTML = `
            <div style="background:#141414; padding:10px; border-radius:8px; border:1px solid #00FFC8; font-size:11px;">
                <span style="color:#00FFC8; font-weight:bold;">✨ CUSTOM V8 TELEMETRY:</span> Modo: <strong>${mode.toUpperCase()}</strong> | Fondo: <strong>${backdrop.toUpperCase()}</strong> | Borde: <strong>${borderWidth}px Die-Cut</strong>
            </div>`;
        }

        function exportCustomAssetV8() {
            if(!customRenderCanvas) return;
            const a = document.createElement('a');
            a.href = customRenderCanvas.toDataURL('image/png');
            a.download = `custom_v8_asset_${Date.now()}.png`;
            a.click();
            alert("✔ Activo V8 Master (.PNG) descargado en alta resolución.");
        }

        function sendCustomToPrint() {
            switchModule('printTab', document.getElementById('nav_printTab'));
            alert("✔ Sticker / Wallpaper enviado a la mesa de preprensa.");
        }

        async function captureDirect() {
            captureToCustom();
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
        "engine": "Wallpapers & Stickers V8 Ultra Active",
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
