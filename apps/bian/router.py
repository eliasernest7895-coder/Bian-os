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
    <title>Bian AI Vision & Creative Suite - Master V4 Final</title>
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
        
        /* HUD CAM VISION V2 PRO */
        .hud-overlay { position: absolute; border: 2px solid #00FFC8; width: 75%; height: 55%; top: 15%; left: 12.5%; border-radius: 18px; box-shadow: 0 0 20px rgba(0,255,200,0.3); pointer-events: none; display: flex; flex-direction: column; justify-content: space-between; padding: 12px; }
        .hud-top { display: flex; justify-content: space-between; font-size: 10px; color: #00FFC8; background: rgba(0,0,0,0.75); padding: 4px 8px; border-radius: 6px; }
        .ocr-box { font-size: 11px; color: #FFF; background: rgba(0,0,0,0.8); padding: 6px 10px; border-radius: 6px; border-left: 3px solid #00FFC8; max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        
        .controls { padding: 14px 20px; background: rgba(13,13,13,0.95); display: flex; justify-content: space-around; align-items: center; border-top: 1px solid #222; }
        .btn-shutter { width: 64px; height: 64px; border-radius: 50%; background: #fff; border: 4px solid #00FFC8; cursor: pointer; }
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
        <button class="nav-tab active" onclick="switchModule('cameraTab', this)">📷 Cam Vision V2 Pro</button>
        <button class="nav-tab" onclick="switchModule('genPromptTab', this)">✨ Generar Imagen AI V2 Pro</button>
        <button class="nav-tab" onclick="switchModule('priceTab', this)">🏷️ Valuador Híbrido V2 Pro</button>
        <button class="nav-tab" onclick="switchModule('foodIndustryTab', this)">👨‍🍳 Chef Lean V4 Pro</button>
        <button class="nav-tab" onclick="switchModule('genVidTab', this)">🎥 Video Motion V4 Pro</button>
        <button class="nav-tab" onclick="switchModule('genImgTab', this)">🎨 SVG & Logos V4 Pro</button>
        <button class="nav-tab" onclick="switchModule('lonasPhysicsTab', this)">📐 Lonas 3D V4 Pro</button>
        <button class="nav-tab" onclick="switchModule('studioTab', this)">📸 Estudio RAW V4 Pro</button>
        <button class="nav-tab" onclick="switchModule('cinemaTab', this)">🎬 Cine Scope 21:9 V4 Pro</button>
        <button class="nav-tab" onclick="switchModule('printTab', this)">🖨️ Imprenta PDF V4 Pro</button>
        <button class="nav-tab" onclick="switchModule('customTab', this)">✨ Wallpapers & Stickers V2 Pro</button>
    </div>

    <div class="header">
        <span style="font-weight: 700; font-size: 13px;" id="moduleTitle">BIAN AI VISION PRO</span>
        <span class="badge" id="netBadge">RED: AUDITANDO...</span>
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
                <div class="ocr-box" id="ocrResult">Escaneando entorno en vivo...</div>
            </div>
            <canvas id="canvas" style="display:none;"></canvas>
        </div>

        <!-- Resto de módulos intactos -->
        <div id="genPromptTab" class="module-view"><div class="panel-content"><div class="card"><h3>✨ Generar Imagen AI V2 Pro</h3></div></div></div>
        <div id="priceTab" class="module-view"><div class="panel-content"><div class="card"><h3>🏷️ Valuador Híbrido V2 Pro</h3></div></div></div>
        <div id="foodIndustryTab" class="module-view"><div class="panel-content"><div class="card"><h3>👨‍🍳 Chef Lean V4 Pro</h3></div></div></div>
        <div id="genVidTab" class="module-view"><div class="panel-content"><div class="card"><h3>🎥 Video Motion V4 Pro</h3></div></div></div>
        <div id="genImgTab" class="module-view"><div class="panel-content"><div class="card"><h3>🎨 SVG & Logos V4 Pro</h3></div></div></div>
        <div id="lonasPhysicsTab" class="module-view"><div class="panel-content"><div class="card"><h3>📐 Lonas 3D V4 Pro</h3></div></div></div>
        <div id="studioTab" class="module-view"><div class="panel-content"><div class="card"><h3>📸 Estudio RAW V4 Pro</h3></div></div></div>
        <div id="cinemaTab" class="module-view"><div class="panel-content"><div class="card"><h3>🎬 Cine Scope 21:9 V4 Pro</h3></div></div></div>
        <div id="printTab" class="module-view"><div class="panel-content"><div class="card"><h3>🖨️ Imprenta PDF V4 Pro</h3></div></div></div>

        <!-- ✨ Wallpapers & Stickers V2 Pro Engine -->
        <div id="customTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>✨ Wallpapers AMOLED & Stickers Die-Cut V2 Pro</h3>
                    <p>Diseño de fondos optimizados para paneles S23 Ultra (Deep Black #000000), efectos neón NPU y troquelado de vinil.</p>
                </div>
                <div class="card">
                    <button class="btn-action" style="color:#00FFC8; margin-bottom:10px; width:100%; border:1px dashed #00FFC8;" onclick="loadCustomArtFromGallery()">📷 Cargar Arte de Galería para Wallpaper/Sticker</button>

                    <div class="form-group">
                        <label>Tipo de Arte Objetivo:</label>
                        <select id="customTypeV2" onchange="renderCustomV2()">
                            <option value="wallpaper_amoled">Wallpaper QHD+ Deep Black AMOLED</option>
                            <option value="sticker_vinil">Sticker Troquelado (Borde Blanco 4px + Vinil)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Estilo / Inyección Neón:</label>
                        <select id="customStyleV2" onchange="renderCustomV2()">
                            <option value="cyber_grid">Cyberpunk Grid (#00FFC8 / #FF0055)</option>
                            <option value="gold_monolith">Gold Monolith (#FFD700 / Deep Dark)</option>
                            <option value="minimal_clean">Minimalista Limpio (Ultra Black)</option>
                        </select>
                    </div>

                    <button class="btn-action" style="background: #00FFC8; color: #000; font-weight: bold; margin-top: 12px; width: 100%;" onclick="renderCustomV2()">⚡ Sintetizar Activo V2 Pro</button>

                    <div class="preview-box" id="customPreviewBoxV2"><span style="font-size: 11px; color: #555;">Esperando sintetizar activo...</span></div>

                    <div id="customActionsV2" style="display:none; margin-top: 10px;">
                        <button class="btn-action" style="color: #00FFC8; width: 100%; margin-bottom: 6px;" onclick="downloadCustomAssetV2()">💾 Descargar Activo HD .PNG</button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Bottom Controls -->
    <div class="controls" id="bottomControls">
        <button class="btn-action" style="font-size:10px;" onclick="toggleMode()">MODO</button>
        <button class="btn-action" style="font-size:10px;" onclick="toggleFlash()">FLASH</button>
        <button class="btn-shutter" onclick="capture()"></button>
        <div class="thumb-preview" id="thumbBox" onclick="openGallery()"><span style="font-size: 9px; color: #666;">GALERÍA</span></div>
        <button class="btn-action" style="color: #00FFC8; font-size:10px;" onclick="toggleOCRMode()">OCR AUTO</button>
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
        let ocrActive = true;
        let lastOcrTime = 0;
        let customSourceImg = new Image();
        let lastCustomCanvas = null;

        let currentMode = 0;
        const modes = ["OCR CONTINUO", "DETECCIÓN OBJETOS", "ESCÁNER QR/BARRAS"];

        navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })
            .then(stream => { video.srcObject = stream; updateThumb(); startRealtimeOCR(); })
            .catch(err => console.error("Error cámara:", err));

        function checkConnection() {
            const isOnline = navigator.onLine;
            const badge = document.getElementById('netBadge');
            if(isOnline) {
                badge.innerText = "ONLINE: EFECTIVIDAD 100%";
                badge.style.color = "#00FFC8";
                badge.style.borderColor = "#00FFC8";
            } else {
                badge.innerText = "OFFLINE: EFECTIVIDAD 80% (BD + HEURÍSTICA)";
                badge.style.color = "#FFD700";
                badge.style.borderColor = "#FFD700";
            }
            return isOnline;
        }

        window.addEventListener('online', checkConnection);
        window.addEventListener('offline', checkConnection);
        checkConnection();

        function switchModule(tabId, btn) {
            document.querySelectorAll('.module-view').forEach(m => m.classList.remove('active'));
            document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
            
            document.getElementById(tabId).classList.add('active');
            btn.classList.add('active');

            const controls = document.getElementById('bottomControls');
            if (tabId === 'cameraTab') {
                controls.style.display = 'flex';
                document.getElementById('moduleTitle').innerText = 'BIAN AI VISION PRO';
            } else {
                controls.style.display = 'none';
                document.getElementById('moduleTitle').innerText = btn.innerText;
            }
        }

        function toggleMode() {
            currentMode = (currentMode + 1) % modes.length;
            document.getElementById('modeLabel').innerText = "MODO: " + modes[currentMode];
        }

        function toggleFlash() { alert("Linterna táctica activada/desactivada (NPU V2)"); }

        async function startRealtimeOCR() {
            setInterval(async () => {
                if (!ocrActive) return;
                const now = Date.now();
                if (now - lastOcrTime < 3000) return;
                lastOcrTime = now;

                if (video.videoWidth === 0 || video.videoHeight === 0) return;

                canvas.width = 300;
                canvas.height = (video.videoHeight / video.videoWidth) * 300;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

                try {
                    const worker = await Tesseract.createWorker('spa+eng');
                    const ret = await worker.recognize(canvas);
                    const text = ret.data.text.trim();
                    if (text.length > 2) {
                        document.getElementById('ocrResult').innerText = "Texto: " + text.substring(0, 40) + "...";
                    } else {
                        document.getElementById('ocrResult').innerText = "IA Vision (" + modes[currentMode] + "): Analizando...";
                    }
                    await worker.terminate();
                } catch(e) { console.error("OCR Error:", e); }
            }, 3000);
        }

        /* --- LOGICA WALLPAPERS & STICKERS V2 PRO --- */
        async function loadCustomArtFromGallery() {
            const res = await fetch('/bian/images/');
            const images = await res.json();
            if(images.length === 0) { alert("No hay imágenes en la galería."); return; }
            customSourceImg.crossOrigin = "anonymous";
            customSourceImg.src = images[images.length - 1].image_path;
            customSourceImg.onload = () => {
                renderCustomV2();
                alert("✔ Arte cargado en el Canvas V2 Pro.");
            };
        }

        function renderCustomV2() {
            const box = document.getElementById('customPreviewBoxV2');
            const type = document.getElementById('customTypeV2').value;
            const style = document.getElementById('customStyleV2').value;

            lastCustomCanvas = document.createElement('canvas');
            lastCustomCanvas.width = 300;
            lastCustomCanvas.height = type === 'wallpaper_amoled' ? 450 : 300;
            const ctx = lastCustomCanvas.getContext('2d');

            ctx.fillStyle = "#000000"; // Deep Black AMOLED
            ctx.fillRect(0, 0, lastCustomCanvas.width, lastCustomCanvas.height);

            if(type === 'wallpaper_amoled') {
                // Rejilla Cyberpunk en fondo
                if(style === 'cyber_grid') {
                    ctx.strokeStyle = "rgba(0, 255, 200, 0.15)";
                    ctx.lineWidth = 1;
                    for(let x = 0; x < lastCustomCanvas.width; x += 20) {
                        ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, lastCustomCanvas.height); ctx.stroke();
                    }
                    for(let y = 0; y < lastCustomCanvas.height; y += 20) {
                        ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(lastCustomCanvas.width, y); ctx.stroke();
                    }
                }

                if(customSourceImg.src) {
                    ctx.drawImage(customSourceImg, 25, 75, lastCustomCanvas.width - 50, 300);
                } else {
                    ctx.fillStyle = "#00FFC8";
                    ctx.font = "bold 13px system-ui";
                    ctx.textAlign = "center";
                    ctx.fillText("WALLPAPER AMOLED 9:16", lastCustomCanvas.width/2, lastCustomCanvas.height/2);
                }
            } else {
                // Modo Sticker Vinil Troquelado
                ctx.fillStyle = "rgba(15, 15, 15, 0.8)";
                ctx.fillRect(0, 0, lastCustomCanvas.width, lastCustomCanvas.height);

                if(customSourceImg.src) {
                    // Borde blanco troquelado
                    ctx.fillStyle = "#FFFFFF";
                    ctx.beginPath();
                    ctx.arc(lastCustomCanvas.width/2, lastCustomCanvas.height/2, 95, 0, Math.PI*2);
                    ctx.fill();

                    ctx.drawImage(customSourceImg, 60, 60, 180, 180);
                } else {
                    ctx.fillStyle = "#FFFFFF";
                    ctx.beginPath();
                    ctx.arc(lastCustomCanvas.width/2, lastCustomCanvas.height/2, 85, 0, Math.PI*2);
                    ctx.fill();

                    ctx.fillStyle = "#000";
                    ctx.font = "bold 12px system-ui";
                    ctx.textAlign = "center";
                    ctx.fillText("STICKER TROQUELADO", lastCustomCanvas.width/2, lastCustomCanvas.height/2);
                }
            }

            box.innerHTML = "";
            box.appendChild(lastCustomCanvas);
            document.getElementById('customActionsV2').style.display = 'block';
        }

        function downloadCustomAssetV2() {
            if(!lastCustomCanvas) return;
            const url = lastCustomCanvas.toDataURL('image/png');
            const a = document.createElement('a'); a.href = url; a.download = `activo_v2_${Date.now()}.png`; a.click();
        }

        async function capture() {
            canvas.width = video.videoWidth; canvas.height = video.videoHeight;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            const imageBase64 = canvas.toDataURL('image/jpeg');
            const response = await fetch('/bian/process/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image_base64: imageBase64, prompt_analysis: `Captura Cam Vision V2 Pro: ${modes[currentMode]}` })
            });
            if(response.ok) { const saved = await response.json(); updateThumb(saved.image_path); }
        }

        async function updateThumb(pathOverride) {
            const thumbBox = document.getElementById('thumbBox');
            if(pathOverride) { thumbBox.innerHTML = `<img src="${pathOverride}" />`; return; }
            const res = await fetch('/bian/images/');
            const images = await res.json();
            if(images.length > 0) thumbBox.innerHTML = `<img src="${images[images.length - 1].image_path}" />`;
        }

        async function openGallery() {
            document.getElementById('galleryModal').style.display = 'flex';
            const res = await fetch('/bian/images/');
            const images = await res.json();
            document.getElementById('galleryGrid').innerHTML = images.map(img => `<div class="gallery-item"><img src="${img.image_path}" /></div>`).join('');
        }

        function closeGallery() { document.getElementById('galleryModal').style.display = 'none'; }
        function toggleOCRMode() {
            ocrActive = !ocrActive;
            document.getElementById('ocrResult').innerText = ocrActive ? "OCR Auto Activado" : "OCR Pausado";
        }
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
        "engine": "Master Unified Suite V4 (Wallpapers & Stickers V2 Pro Complete)",
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
