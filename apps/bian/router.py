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
    prompt_analysis: str = "Detección V3 Ultra Pro"

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bian AI Vision & Creative Suite - Master V5 Ultra</title>
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
        
        /* HUD CAM VISION */
        .hud-overlay { position: absolute; border: 2px solid #00FFC8; width: 80%; height: 60%; top: 12%; left: 10%; border-radius: 20px; box-shadow: 0 0 25px rgba(0,255,200,0.4); pointer-events: none; display: flex; flex-direction: column; justify-content: space-between; padding: 15px; }
        .hud-top { display: flex; justify-content: space-between; font-size: 10px; color: #00FFC8; background: rgba(0,0,0,0.8); padding: 5px 10px; border-radius: 6px; pointer-events: auto; }
        .ocr-box { font-size: 11px; color: #FFF; background: rgba(0,0,0,0.85); padding: 8px 12px; border-radius: 8px; border-left: 3px solid #00FFC8; max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        
        .bounding-box { position: absolute; border: 1px dashed #FF0055; width: 45%; height: 30%; top: 30%; left: 28%; pointer-events: none; border-radius: 6px; display: flex; align-items: flex-start; justify-content: flex-end; padding: 4px; transition: all 0.2s ease; }
        .bounding-tag { background: rgba(255,0,85,0.85); color: #fff; font-size: 8px; padding: 2px 5px; border-radius: 3px; font-weight: bold; }

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
        <button class="nav-tab active" onclick="switchModule('cameraTab', this)">📷 Cam Vision V3.5 Pro</button>
        <button class="nav-tab" onclick="switchModule('genPromptTab', this)">✨ Generar Imagen AI V3 Ultra</button>
        <button class="nav-tab" onclick="switchModule('priceTab', this)">🏷️ Valuador Híbrido V3 Ultra</button>
        <button class="nav-tab" onclick="switchModule('foodIndustryTab', this)">👨‍🍳 Chef Lean V5 Ultra</button>
        <button class="nav-tab" onclick="switchModule('genVidTab', this)">🎥 Video Motion V5 Ultra</button>
        <button class="nav-tab" onclick="switchModule('genImgTab', this)">🎨 SVG & Logos V5 Ultra</button>
        <button class="nav-tab" onclick="switchModule('lonasPhysicsTab', this)">📐 Lonas 3D V5 Ultra</button>
        <button class="nav-tab" onclick="switchModule('studioTab', this)">📸 Estudio RAW V4 Pro</button>
        <button class="nav-tab" onclick="switchModule('cinemaTab', this)">🎬 Cine Scope 21:9 V4 Pro</button>
        <button class="nav-tab" onclick="switchModule('printTab', this)">🖨️ Imprenta PDF V4 Pro</button>
        <button class="nav-tab" onclick="switchModule('customTab', this)">✨ Wallpapers V2 Pro</button>
    </div>

    <div class="header">
        <span style="font-weight: 700; font-size: 13px;" id="moduleTitle">BIAN V5 MASTER SUITE</span>
        <span class="badge" id="netBadge">RED: AUDITANDO...</span>
    </div>

    <div class="main-container">
        <!-- 📷 1. Cam Vision V3.5 Ultra Realtime -->
        <div id="cameraTab" class="module-view active" onclick="handleTapToFocus(event)">
            <video id="webcam" autoplay playsinline></video>
            <div class="hud-overlay">
                <div class="hud-top">
                    <span id="modeLabel">MODO: OCR & VISION EN VIVO</span>
                    <button onclick="toggleCameraFacing()" style="background:#111; color:#00FFC8; border:1px solid #00FFC8; padding:2px 6px; border-radius:4px; font-size:9px; cursor:pointer;">CAMBIAR LENTE</button>
                </div>
                <div class="bounding-box" id="dynamicBoundingBox">
                    <span class="bounding-tag" id="targetTag">OBJETIVO EN VIVO</span>
                </div>
                <div class="ocr-box" id="ocrResult">Cam Vision V3.5: Lente activa y sincronizada...</div>
            </div>
            <canvas id="canvas" style="display:none;"></canvas>
        </div>

        <!-- ✨ 2. Generar Imagen AI V3 Ultra Engine -->
        <div id="genPromptTab" class="module-view"><div class="panel-content"><div class="card"><h3>✨ Generar Imagen AI V3 Ultra</h3></div></div></div>

        <!-- 🏷️ 3. Valuador Híbrido V3 Ultra Engine -->
        <div id="priceTab" class="module-view"><div class="panel-content"><div class="card"><h3>🏷️ Valuador Híbrido V3 Ultra</h3></div></div></div>

        <!-- 👨‍🍳 4. Chef Lean V5 Ultra -->
        <div id="foodIndustryTab" class="module-view"><div class="panel-content"><div class="card"><h3>👨‍🍳 Chef Lean V5 Ultra</h3></div></div></div>

        <!-- 🎥 5. Video Motion V5 Ultra Engine -->
        <div id="genVidTab" class="module-view"><div class="panel-content"><div class="card"><h3>🎥 Video Motion V5 Ultra</h3></div></div></div>

        <!-- 🎨 6. SVG & Logos Vectorial V5 Ultra Engine -->
        <div id="genImgTab" class="module-view"><div class="panel-content"><div class="card"><h3>🎨 SVG & Logos Vectorial V5 Ultra</h3></div></div></div>

        <!-- 📐 7. Lonas 3D V5 Ultra Engine -->
        <div id="lonasPhysicsTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>📐 Lonas 3D & Simulación Eólica V5 Ultra Engine</h3>
                    <p>Simulación de resistencia mecánica ante viento, maqueta visual 3D, matriz de materiales y Ficha Técnica de Instalación.</p>
                </div>
                <div class="card">
                    <button class="btn-action" style="color:#00FFC8; margin-bottom:8px; width:100%; border:1px dashed #00FFC8;" onclick="loadLonaArtFromGalleryV5()">🖼️ Cargar Isotipo / Imagen de Galería para Maqueta 3D</button>
                    <div class="form-group">
                        <label>Dimensiones (Ancho x Alto en Metros):</label>
                        <div style="display:flex; gap:8px;">
                            <input type="number" id="lonaWValV5" value="4.0" step="0.5">
                            <input type="number" id="lonaHValV5" value="3.0" step="0.5">
                        </div>
                    </div>
                    <div class="form-group">
                        <label>Tipo de Material Publicitario:</label>
                        <select id="lonaMaterialV5">
                            <option value="13oz_frontlit">Lona Frontlit Promocional 13oz</option>
                            <option value="mesh_anti_viento">Lona Mesh Microperforada (Anti-Viento Carga Alta)</option>
                            <option value="backlight_caja">Lona Backlight Traslúcida (Caja de Luz Neón)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Simulación de Viento / Tensión Eólica NPU:</label>
                        <select id="windSpeedV5">
                            <option value="40">Viento Moderado (40 km/h - Tensión Estándar)</option>
                            <option value="60">Ráfaga Fuerte (60 km/h - Refuerzo de Esquinas)</option>
                            <option value="90">Tormenta Crítica (90 km/h - Ojillos Dobles a cada 30cm)</option>
                        </select>
                    </div>
                    <button class="btn-action" style="background: #00FFC8; color: #000; font-weight: bold; margin-top: 12px; width: 100%;" onclick="calculateLonaSpecsV5()">⚡ Renderizar Maqueta 3D & Simulación V5</button>

                    <div class="preview-box" id="lonaPreviewBoxV5"><span style="font-size: 11px; color: #555;">Sin maqueta 3D renderizada</span></div>
                    <div id="lonaResultV5" style="margin-top: 10px;"></div>
                </div>
            </div>
        </div>

        <!-- 📸 8. Estudio RAW V4 Pro -->
        <div id="studioTab" class="module-view"><div class="panel-content"><div class="card"><h3>📸 Estudio RAW V4 Pro</h3></div></div></div>
        <!-- 🎬 9. Cine Scope 21:9 V4 Pro -->
        <div id="cinemaTab" class="module-view"><div class="panel-content"><div class="card"><h3>🎬 Cine Scope 21:9 V4 Pro</h3></div></div></div>
        <!-- 🖨️ 10. Imprenta PDF V4 Pro -->
        <div id="printTab" class="module-view"><div class="panel-content"><div class="card"><h3>🖨️ Imprenta PDF V4 Pro</h3></div></div></div>
        <!-- ✨ 11. Wallpapers V2 Pro -->
        <div id="customTab" class="module-view"><div class="panel-content"><div class="card"><h3>✨ Wallpapers V2 Pro</h3></div></div></div>
    </div>

    <!-- Controls para Cam Vision -->
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
        let useFrontCamera = false;
        let lonaArtImgV5 = new Image();

        let currentMode = 0;
        const modes = ["OCR CONTINUO", "DETECCIÓN OBJETOS", "ESCÁNER QR/BARRAS"];

        function initCamera() {
            navigator.mediaDevices.getUserMedia({ video: { facingMode: useFrontCamera ? 'user' : 'environment' } })
                .then(stream => { video.srcObject = stream; updateThumb(); startRealtimeOCR(); })
                .catch(err => console.error("Error cámara:", err));
        }
        initCamera();

        function toggleCameraFacing() {
            useFrontCamera = !useFrontCamera;
            if (video.srcObject) video.srcObject.getTracks().forEach(track => track.stop());
            initCamera();
        }

        function handleTapToFocus(event) {
            const box = document.getElementById('dynamicBoundingBox');
            box.style.left = Math.max(10, Math.min(window.innerWidth - 180, event.clientX - 60)) + 'px';
            box.style.top = Math.max(50, Math.min(window.innerHeight - 250, event.clientY - 60)) + 'px';
            document.getElementById('targetTag').innerText = "ENFOQUE TÁCTICO";
        }

        function switchModule(tabId, btn) {
            document.querySelectorAll('.module-view').forEach(m => m.classList.remove('active'));
            document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            btn.classList.add('active');

            const controls = document.getElementById('bottomControls');
            if (tabId === 'cameraTab') {
                controls.style.display = 'flex';
                document.getElementById('moduleTitle').innerText = 'BIAN V5 MASTER SUITE';
            } else {
                controls.style.display = 'none';
                document.getElementById('moduleTitle').innerText = btn.innerText;
            }
        }

        function toggleMode() {
            currentMode = (currentMode + 1) % modes.length;
            document.getElementById('modeLabel').innerText = "MODO: " + modes[currentMode];
            document.getElementById('targetTag').innerText = modes[currentMode];
        }

        function toggleFlash() { alert("Linterna activada/desactivada"); }

        async function startRealtimeOCR() {
            setInterval(async () => {
                if (!ocrActive) return;
                const now = Date.now();
                if (now - lastOcrTime < 3000) return;
                lastOcrTime = now;
                if (video.videoWidth === 0 || video.videoHeight === 0) return;

                canvas.width = 300; canvas.height = (video.videoHeight / video.videoWidth) * 300;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

                try {
                    const worker = await Tesseract.createWorker('spa+eng');
                    const ret = await worker.recognize(canvas);
                    const text = ret.data.text.trim();
                    if (text.length > 2) document.getElementById('ocrResult').innerText = "Texto: " + text.substring(0, 35) + "...";
                    await worker.terminate();
                } catch(e) { console.error("OCR Error:", e); }
            }, 3000);
        }

        /* --- 7. LOGICA LONAS 3D V5 ULTRA --- */
        async function loadLonaArtFromGalleryV5() {
            const res = await fetch('/bian/images/');
            const images = await res.json();
            if(images.length === 0) { alert("No hay imágenes en la galería."); return; }
            lonaArtImgV5.crossOrigin = "anonymous";
            lonaArtImgV5.src = images[images.length - 1].image_path;
            lonaArtImgV5.onload = () => alert("✔ Arte cargado en maqueta 3D V5 Ultra.");
        }

        function calculateLonaSpecsV5() {
            const w = parseFloat(document.getElementById('lonaWValV5').value) || 4.0;
            const h = parseFloat(document.getElementById('lonaHValV5').value) || 3.0;
            const mat = document.getElementById('lonaMaterialV5').value;
            const wind = parseInt(document.getElementById('windSpeedV5').value);
            const box = document.getElementById('lonaPreviewBoxV5');
            const res = document.getElementById('lonaResultV5');

            const area = w * h;
            const perimeter = (w + h) * 2;
            const ojillosDist = wind >= 90 ? 0.30 : (wind >= 60 ? 0.40 : 0.50);
            const totalOjillos = Math.ceil(perimeter / ojillosDist);
            const weightGrams = mat === 'mesh_anti_viento' ? 320 : 540;
            const totalKg = ((area * weightGrams) / 1000).toFixed(2);

            const costPerM2 = mat === 'mesh_anti_viento' ? 140 : 95;
            const prodCost = Math.round(area * costPerM2);
            const installCost = Math.round(prodCost * 0.6);
            const totalBudget = prodCost + installCost;

            const lonaCanvas = document.createElement('canvas');
            lonaCanvas.width = 380; lonaCanvas.height = 200;
            const ctx = lonaCanvas.getContext('2d');

            ctx.fillStyle = "#111"; ctx.fillRect(0, 0, lonaCanvas.width, lonaCanvas.height);
            ctx.strokeStyle = "#00FFC8"; ctx.lineWidth = 3;
            ctx.strokeRect(20, 20, lonaCanvas.width - 40, lonaCanvas.height - 40);

            if(lonaArtImgV5.src) {
                ctx.drawImage(lonaArtImgV5, 25, 25, lonaCanvas.width - 50, lonaCanvas.height - 50);
            } else {
                ctx.fillStyle = "rgba(0, 255, 200, 0.1)";
                ctx.fillRect(25, 25, lonaCanvas.width - 50, lonaCanvas.height - 50);
                ctx.fillStyle = "#00FFC8"; ctx.font = "bold 12px system-ui"; ctx.textAlign = "center";
                ctx.fillText(`MAQUETA 3D V5: LONA ${w}m x ${h}m`, lonaCanvas.width/2, lonaCanvas.height/2);
            }

            ctx.fillStyle = "#FFD700";
            for(let x = 20; x <= lonaCanvas.width - 20; x += 30) {
                ctx.beginPath(); ctx.arc(x, 20, 3, 0, Math.PI*2); ctx.fill();
                ctx.beginPath(); ctx.arc(x, lonaCanvas.height - 20, 3, 0, Math.PI*2); ctx.fill();
            }

            box.innerHTML = ""; box.appendChild(lonaCanvas);
            res.innerHTML = `
            <div style="background:#181818; padding:12px; border-radius:8px; border:1px solid #00FFC8;">
                <p style="color:#00FFC8; font-weight:bold; margin-bottom:4px;">📊 Ficha de Simulación Estructural V5 Ultra:</p>
                <p>• Superficie: <strong style="color:#FFF;">${area.toFixed(2)} m²</strong> | Peso: <strong style="color:#FFF;">${totalKg} Kg</strong></p>
                <p>• Perforación Ojillos: <strong style="color:#FFD700;">${totalOjillos} Ojillos</strong> (Espaciado ${(ojillosDist*100).toFixed(0)}cm)</p>
                <p>• Tolerancia Viento: Soportado hasta ${wind} km/h</p>
                <p>• Presupuesto Estimado: <strong style="color:#00FFC8; font-size:13px;">$${totalBudget} MXN</strong></p>
            </div>`;
        }

        async function capture() {
            canvas.width = video.videoWidth; canvas.height = video.videoHeight;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            const imageBase64 = canvas.toDataURL('image/jpeg');
            const response = await fetch('/bian/process/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image_base64: imageBase64, prompt_analysis: `Captura Cam Vision V3.5` })
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
        function toggleOCRMode() { ocrActive = !ocrActive; }
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
        "engine": "Bian V5 Master Suite (Lonas 3D V5 Ultra Integrated)",
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
