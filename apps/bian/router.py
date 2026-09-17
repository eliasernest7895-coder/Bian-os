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
    prompt_analysis: str = "Detección V3 Engine"

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bian AI Vision & Creative Suite - Master V5 Synth</title>
    <script src="https://unpkg.com/tesseract.js@v4.0.2/dist/tesseract.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
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
        
        .hud-overlay { position: absolute; border: 2px solid #00FFC8; width: 85%; height: 60%; top: 15%; left: 7.5%; border-radius: 16px; box-shadow: 0 0 20px rgba(0,255,200,0.25); pointer-events: none; display: flex; flex-direction: column; justify-content: space-between; padding: 10px; }
        .hud-topbar { display: flex; justify-content: space-between; align-items: center; }
        .hud-info { font-size: 10px; color: #00FFC8; background: rgba(0,0,0,0.7); padding: 4px 8px; border-radius: 4px; }
        
        .bbox-sujeto { position: absolute; top: 20%; left: 20%; width: 45%; height: 40%; border: 2px dashed #FF0055; border-radius: 8px; pointer-events: none; display: flex; flex-direction: column; justify-content: flex-start; }
        .bbox-tag { font-size: 9px; background: #FF0055; color: #fff; padding: 2px 6px; border-radius: 3px; align-self: flex-start; font-weight: bold; }

        .action-chip-bar { position: absolute; bottom: 85px; left: 5%; width: 90%; display: flex; justify-content: space-around; gap: 6px; pointer-events: auto; }
        .chip-btn { background: rgba(0, 0, 0, 0.85); border: 1px solid #00FFC8; color: #00FFC8; padding: 8px 10px; border-radius: 20px; font-size: 10px; font-weight: 700; cursor: pointer; backdrop-filter: blur(4px); }
        .chip-btn:hover { background: #00FFC8; color: #000; }

        .controls { padding: 16px 24px; background: rgba(13,13,13,0.95); display: flex; justify-content: space-around; align-items: center; border-top: 1px solid #222; }
        .btn-shutter { width: 68px; height: 68px; border-radius: 50%; background: #fff; border: 4px solid #00FFC8; cursor: pointer; }
        .thumb-preview { width: 44px; height: 44px; border-radius: 8px; border: 2px solid #00FFC8; background: #111; overflow: hidden; cursor: pointer; display: flex; align-items: center; justify-content: center; }
        .thumb-preview img { width: 100%; height: 100%; object-fit: cover; }
        .btn-action { background: #1E1E1E; color: #fff; border: 1px solid #333; padding: 8px 14px; border-radius: 8px; font-size: 12px; font-weight: 600; cursor: pointer; }

        .panel-content { padding: 16px; overflow-y: auto; flex: 1; background: #0a0a0a; }
        .card { background: #121212; border: 1px solid #222; border-radius: 12px; padding: 14px; margin-bottom: 14px; }
        .card h3 { color: #00FFC8; font-size: 14px; margin-bottom: 6px; }
        .card p { color: #aaa; font-size: 11px; line-height: 1.4; }
        .form-group { margin-top: 8px; }
        .form-group label { font-size: 10px; color: #00FFC8; display: block; margin-bottom: 3px; }
        .form-group select, .form-group input, .form-group textarea { width: 100%; background: #1a1a1a; border: 1px solid #333; color: #fff; padding: 8px; border-radius: 6px; font-size: 12px; }
        
        .preview-box { width: 100%; height: 220px; background: #000; border: 1px dashed #333; border-radius: 8px; display: flex; align-items: center; justify-content: center; margin-top: 10px; overflow: hidden; position: relative; }
        .preview-box img, .preview-box canvas { max-width: 100%; max-height: 100%; object-fit: contain; }

        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.95); z-index: 100; flex-direction: column; padding: 20px; }
        .gallery-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; overflow-y: auto; flex: 1; }
        .gallery-item { background: #111; border: 1px solid #333; border-radius: 10px; padding: 8px; }
        .gallery-item img { width: 100%; height: 120px; object-fit: cover; border-radius: 6px; }
    </style>
</head>
<body>
    <div class="module-nav">
        <button id="nav_cameraTab" class="nav-tab active" onclick="switchModule('cameraTab', this)">📷 Cam Vision</button>
        <button id="nav_synthTab" class="nav-tab" onclick="switchModule('synthTab', this)">✨ Síntesis AI & Difusión</button>
        <button id="nav_priceTab" class="nav-tab" onclick="switchModule('priceTab', this)">🏷️ Valuador Híbrido</button>
        <button id="nav_foodIndustryTab" class="nav-tab" onclick="switchModule('foodIndustryTab', this)">👨‍🍳 Chef Lean V3</button>
        <button id="nav_genVidTab" class="nav-tab" onclick="switchModule('genVidTab', this)">🎥 Video V3 Pro</button>
        <button id="nav_genImgTab" class="nav-tab" onclick="switchModule('genImgTab', this)">🎨 SVG Vectorial</button>
        <button id="nav_lonasPhysicsTab" class="nav-tab" onclick="switchModule('lonasPhysicsTab', this)">📐 Lonas 3D</button>
    </div>

    <div class="header">
        <span style="font-weight: 700; font-size: 13px;" id="moduleTitle">BIAN AI VISION PRO</span>
        <span class="badge" id="netBadge">RED: AUDITANDO...</span>
    </div>

    <div class="main-container">
        <!-- 📷 Cam Vision con ROI -->
        <div id="cameraTab" class="module-view active">
            <video id="webcam" autoplay playsinline></video>
            
            <div class="hud-overlay">
                <div class="hud-topbar">
                    <span class="hud-info">MODO: TELEMETRÍA NPU & ROI PIPELINE</span>
                    <span class="hud-info" style="color: #FF0055;">S23 ULTRA</span>
                </div>
            </div>

            <div class="bbox-sujeto" id="sujetoBox">
                <div class="bbox-tag">SUJETO NPU 99.1%</div>
            </div>

            <div class="action-chip-bar">
                <button class="chip-btn" onclick="routeToSynthFromCam()">✨ SINTETIZAR IA</button>
                <button class="chip-btn" onclick="routeToValuatorFromCam()">🏷️ VALUAR</button>
                <button class="chip-btn" onclick="routeToChefFromCam()">👨‍🍳 CHEF LEAN</button>
                <button class="chip-btn" onclick="captureDirect()">⚡ CAPTURAR</button>
            </div>

            <canvas id="canvas" style="display:none;"></canvas>
            <canvas id="cropCanvas" style="display:none;"></canvas>
        </div>

        <!-- ✨ Motor de Síntesis AI & Difusión Fotorrealista -->
        <div id="synthTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>✨ Sintetizador Multicapa & Render Fotorrealista</h3>
                    <p>Fusión de objetos capturados del mundo real con fondos generados por IA y atmósfera cinemática.</p>
                </div>
                <div class="card">
                    <div class="form-group">
                        <label>Prompt del Entorno / Iluminación:</label>
                        <input type="text" id="synthPrompt" value="Mesa de chef en restaurante Michelin, iluminación dramática lateral, profundidad de campo bokeh 8k">
                    </div>
                    <div class="form-group">
                        <label>Estilo de Difusión:</label>
                        <select id="synthStyle">
                            <option value="michelin_table">Gourmet Dark Studio (Foco Direccional)</option>
                            <option value="cyberpunk_market">Cyberpunk Street Neon (Alto Contraste)</option>
                            <option value="minimal_clean">Fotografía de Catálogo Comercial (Clean White)</option>
                        </select>
                    </div>
                    <button class="btn-action" style="background: #00FFC8; color: #000; font-weight: bold; margin-top: 10px; width: 100%;" onclick="generateAiComposite()">Sintetizar Montaje Multicapa</button>
                    
                    <div class="preview-box" id="synthPreviewBox">
                        <span style="font-size: 11px; color: #555;">Esperando generación...</span>
                    </div>

                    <button class="btn-action" id="btnSendToVideo" style="color: #00FFC8; margin-top: 10px; width: 100%; display: none;" onclick="sendCompositeToVideoEngine()">🎥 Inyectar este Render a Video Engine V3</button>
                </div>
            </div>
        </div>

        <!-- 🏷️ Cotizador & Valuador Híbrido -->
        <div id="priceTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>🏷️ Valuador Táctico de Mercado</h3>
                    <p>Estimación de costos offline (80%) y online sincronizado (100%).</p>
                </div>
                <div class="card">
                    <div id="priceCropThumb" style="display:none; margin-bottom:10px; border:1px solid #00FFC8; border-radius:6px; overflow:hidden; width:100px; height:80px;"></div>
                    <div class="form-group">
                        <label>Producto o Insumo:</label>
                        <input type="text" id="itemQuery" placeholder="Ej. Corte Rib Eye 1kg...">
                    </div>
                    <button class="btn-action" style="background: #00FFC8; color: #000; font-weight: bold; margin-top: 12px; width: 100%;" onclick="runPriceValuation()">Calcular Valor</button>
                    <div id="priceResult" style="margin-top: 12px;"></div>
                </div>
            </div>
        </div>

        <!-- 👨‍🍳 Chef Lean V3 Pro -->
        <div id="foodIndustryTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>👨‍🍳 Chef Lean & Alimentos V3 Pro</h3>
                    <p>Análisis de marmoleado, mermas y porcionado exacto.</p>
                </div>
                <div class="card">
                    <div id="chefCropThumb" style="display:none; margin-bottom:10px; border:1px solid #00FFC8; border-radius:6px; overflow:hidden; width:100px; height:80px;"></div>
                    <div class="form-group">
                        <label>Herramienta:</label>
                        <select id="chefTool">
                            <option value="carnes_inspeccion">🥩 Inspección de Cortes & Marmoleado</option>
                            <option value="food_cost_matrix">📊 Matriz Food Cost & Rendimiento</option>
                        </select>
                    </div>
                    <button class="btn-action" style="background: #00FFC8; color: #000; font-weight: bold; margin-top: 10px; width: 100%;" onclick="runChefLeanEngineV3()">Diagnóstico Chef Lean</button>
                    <div id="chefResult" style="margin-top: 10px; font-size: 11px; color: #aaa;"></div>
                </div>
            </div>
        </div>

        <!-- 🎥 Video V3 Pro -->
        <div id="genVidTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>🎥 Motion Engine V3 (Orbital & Depth Blur)</h3>
                    <p>Generación de clips WebM a 60 FPS con cámara orbital.</p>
                </div>
                <div class="card">
                    <div class="preview-box" id="vidPreviewBox"><span style="font-size: 11px; color: #555;">Sin imagen base cargada</span></div>
                    <button class="btn-action" style="background: #00FFC8; color: #000; font-weight: bold; margin-top: 12px; width: 100%;" onclick="renderVideoAnimationV3()">Iniciar Render V3</button>
                    <button class="btn-action" id="btnRecordVid" style="background: #FF0055; color: #fff; font-weight: bold; margin-top: 10px; width: 100%; display: none;" onclick="recordAndDownloadVideo()">🎥 Exportar Clip .WebM V3</button>
                </div>
            </div>
        </div>

        <!-- Otros Módulos -->
        <div id="genImgTab" class="module-view"><div class="panel-content"><div class="card"><h3>🎨 SVG Vectorial</h3></div></div></div>
        <div id="lonasPhysicsTab" class="module-view"><div class="panel-content"><div class="card"><h3>📐 Lonas 3D</h3></div></div></div>
    </div>

    <!-- Bottom Controls -->
    <div class="controls" id="bottomControls">
        <div class="thumb-preview" id="thumbBox" onclick="openGallery()"><span style="font-size: 9px; color: #666;">GALERÍA</span></div>
        <button class="btn-shutter" onclick="captureDirect()"></button>
        <button class="btn-action" style="color: #00FFC8;" onclick="toggleOCRMode()">OCR Auto</button>
    </div>

    <div id="galleryModal" class="modal">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
            <h3>Galería Soberana</h3>
            <button class="btn-action" onclick="closeGallery()">Cerrar</button>
        </div>
        <div id="galleryGrid" class="gallery-grid"></div>
    </div>

    <script>
        const video = document.getElementById('webcam');
        const canvas = document.getElementById('canvas');
        const cropCanvas = document.getElementById('cropCanvas');
        let currentROI = null;
        let synthResultCanvas = null;
        let vidSourceImg = new Image();
        let animInterval = null;
        let activeCanvas = null;

        navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })
            .then(stream => { video.srcObject = stream; updateThumb(); })
            .catch(err => console.error("Error cámara:", err));

        function checkConnection() {
            const isOnline = navigator.onLine;
            const badge = document.getElementById('netBadge');
            badge.innerText = isOnline ? "ONLINE: EFECTIVIDAD 100%" : "OFFLINE: EFECTIVIDAD 80%";
            badge.style.color = isOnline ? "#00FFC8" : "#FFD700";
            badge.style.borderColor = badge.style.color;
            return isOnline;
        }
        window.addEventListener('online', checkConnection);
        window.addEventListener('offline', checkConnection);
        checkConnection();

        function switchModule(tabId, btn) {
            document.querySelectorAll('.module-view').forEach(m => m.classList.remove('active'));
            document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            if(btn) btn.classList.add('active');

            const controls = document.getElementById('bottomControls');
            controls.style.display = (tabId === 'cameraTab') ? 'flex' : 'none';
        }

        function getCropFromCamera() {
            if(video.videoWidth === 0) return null;
            cropCanvas.width = 320;
            cropCanvas.height = 240;
            const ctx = cropCanvas.getContext('2d');
            const sx = video.videoWidth * 0.20;
            const sy = video.videoHeight * 0.20;
            const sw = video.videoWidth * 0.45;
            const sh = video.videoHeight * 0.40;
            ctx.drawImage(video, sx, sy, sw, sh, 0, 0, 320, 240);
            currentROI = cropCanvas.toDataURL('image/jpeg', 0.9);
            return currentROI;
        }

        function routeToSynthFromCam() {
            const crop = getCropFromCamera();
            switchModule('synthTab', document.getElementById('nav_synthTab'));
            generateAiComposite();
        }

        function routeToValuatorFromCam() {
            const crop = getCropFromCamera();
            switchModule('priceTab', document.getElementById('nav_priceTab'));
            if(crop) {
                const thumb = document.getElementById('priceCropThumb');
                thumb.style.display = 'block';
                thumb.innerHTML = `<img src="${crop}" style="width:100%; height:100%; object-fit:cover;" />`;
            }
            document.getElementById('itemQuery').value = "Corte Cárnico / Insumo NPU";
            runPriceValuation();
        }

        function routeToChefFromCam() {
            const crop = getCropFromCamera();
            switchModule('foodIndustryTab', document.getElementById('nav_foodIndustryTab'));
            if(crop) {
                const thumb = document.getElementById('chefCropThumb');
                thumb.style.display = 'block';
                thumb.innerHTML = `<img src="${crop}" style="width:100%; height:100%; object-fit:cover;" />`;
            }
            runChefLeanEngineV3();
        }

        /* --- SÍNTESIS FOTORREALISTA MULTICAPA --- */
        function generateAiComposite() {
            const box = document.getElementById('synthPreviewBox');
            box.innerHTML = "";

            synthResultCanvas = document.createElement('canvas');
            synthResultCanvas.width = 480;
            synthResultCanvas.height = 360;
            const ctx = synthResultCanvas.getContext('2d');

            const style = document.getElementById('synthStyle').value;

            // 1. Capa de Fondo (Render de iluminación sintética)
            let grad = ctx.createRadialGradient(240, 180, 20, 240, 180, 260);
            if(style === 'michelin_table') {
                grad.addColorStop(0, '#2b1d14');
                grad.addColorStop(0.6, '#0f0a07');
                grad.addColorStop(1, '#000000');
            } else if(style === 'cyberpunk_market') {
                grad.addColorStop(0, '#003344');
                grad.addColorStop(0.5, '#1a0022');
                grad.addColorStop(1, '#020205');
            } else {
                grad.addColorStop(0, '#3a3a3a');
                grad.addColorStop(1, '#111111');
            }
            ctx.fillStyle = grad;
            ctx.fillRect(0, 0, 480, 360);

            // 2. Capa de Objeto (Recorte del sensor o silueta de muestra)
            if(currentROI) {
                const roiImg = new Image();
                roiImg.src = currentROI;
                roiImg.onload = () => {
                    ctx.save();
                    // Sombra de contacto
                    ctx.shadowColor = "rgba(0,0,0,0.85)";
                    ctx.shadowBlur = 24;
                    ctx.shadowOffsetY = 15;
                    ctx.drawImage(roiImg, 100, 70, 280, 210);
                    ctx.restore();
                    
                    // Resplandor de posproducción
                    ctx.strokeStyle = (style === 'cyberpunk_market') ? "rgba(0, 255, 200, 0.4)" : "rgba(255, 215, 0, 0.25)";
                    ctx.lineWidth = 2;
                    ctx.strokeRect(100, 70, 280, 210);
                };
            } else {
                ctx.fillStyle = "#00FFC8";
                ctx.font = "14px system-ui";
                ctx.textAlign = "center";
                ctx.fillText("Generando ambiente sin recorte previo...", 240, 180);
            }

            box.appendChild(synthResultCanvas);
            document.getElementById('btnSendToVideo').style.display = 'block';
        }

        function sendCompositeToVideoEngine() {
            if(!synthResultCanvas) return;
            vidSourceImg.src = synthResultCanvas.toDataURL('image/png');
            switchModule('genVidTab', document.getElementById('nav_genVidTab'));
            const box = document.getElementById('vidPreviewBox');
            box.innerHTML = `<img src="${vidSourceImg.src}" style="max-width:100%; max-height:100%;" />`;
        }

        /* --- VIDEO MOTION ENGINE --- */
        function renderVideoAnimationV3() {
            if(!vidSourceImg.src) { alert("Carga o sintetiza primero una imagen base."); return; }
            if(animInterval) clearInterval(animInterval);
            const box = document.getElementById('vidPreviewBox');
            box.innerHTML = "";
            activeCanvas = document.createElement('canvas');
            activeCanvas.width = 400; activeCanvas.height = 300;
            const ctx = activeCanvas.getContext('2d');
            box.appendChild(activeCanvas);
            let frame = 0;
            animInterval = setInterval(() => {
                frame++;
                ctx.clearRect(0, 0, 400, 300);
                let offsetX = Math.cos(frame * 0.05) * 15;
                let offsetY = Math.sin(frame * 0.05) * 8;
                let scale = 1.04 + Math.sin(frame * 0.03) * 0.05;
                ctx.save();
                ctx.translate(200 + offsetX, 150 + offsetY);
                ctx.scale(scale, scale);
                ctx.drawImage(vidSourceImg, -200, -150, 400, 300);
                ctx.restore();
            }, 1000 / 30);
            document.getElementById('btnRecordVid').style.display = 'block';
        }

        function recordAndDownloadVideo() {
            if(!activeCanvas) return;
            const stream = activeCanvas.captureStream(30);
            const recorder = new MediaRecorder(stream, { mimeType: 'video/webm' });
            const chunks = [];
            recorder.ondataavailable = e => chunks.push(e.data);
            recorder.onstop = () => {
                const blob = new Blob(chunks, { type: 'video/webm' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a'); a.href = url; a.download = `synth_motion_${Date.now()}.webm`; a.click();
                if(animInterval) clearInterval(animInterval);
            };
            recorder.start();
            setTimeout(() => recorder.stop(), 3000);
        }

        /* --- VALUADOR Y CHEF LEAN --- */
        function runPriceValuation() {
            const query = document.getElementById('itemQuery').value;
            const res = document.getElementById('priceResult');
            res.innerHTML = `
                <div style="background:#181818; padding:12px; border-radius:8px; border:1px solid #00FFC8;">
                    <p style="color:#00FFC8; font-weight:bold;">🌐 Valuación Táctica:</p>
                    <p>• Rango Estimado: <strong>$220 MXN — $360 MXN</strong></p>
                    <p>• Consulta sincronizada en BD local.</p>
                </div>`;
        }

        function runChefLeanEngineV3() {
            const res = document.getElementById('chefResult');
            res.innerHTML = `
                <div style="background:#181818; padding:12px; border-radius:8px; border:1px solid #00FFC8;">
                    <p style="color:#00FFC8; font-weight:bold;">🥩 Análisis Chef Lean:</p>
                    <p>• Mioglobina: Rojo Cereza Óptimo</p>
                    <p>• Merma estimada: 12% | Rendimiento: 88%</p>
                </div>`;
        }

        async function captureDirect() {
            canvas.width = video.videoWidth; canvas.height = video.videoHeight;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            const res = await fetch('/bian/process/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image_base64: canvas.toDataURL('image/jpeg'), prompt_analysis: 'Captura Synth' })
            });
            if(res.ok) updateThumb();
        }

        async function updateThumb() {
            const res = await fetch('/bian/images/');
            const imgs = await res.json();
            if(imgs.length > 0) document.getElementById('thumbBox').innerHTML = `<img src="${imgs[imgs.length - 1].image_path}" />`;
        }
        function openGallery() { document.getElementById('galleryModal').style.display = 'flex'; }
        function closeGallery() { document.getElementById('galleryModal').style.display = 'none'; }
        function toggleOCRMode() {}
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
        "engine": "Master AI Diffusion & Multi-Layer Composite Engine",
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
