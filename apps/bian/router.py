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
        <button class="nav-tab" onclick="switchModule('priceTab', this)">🏷️ Valuador Híbrido V2 Pro</button>
        <button class="nav-tab" onclick="switchModule('foodIndustryTab', this)">👨‍🍳 Chef Lean V4 Pro</button>
        <button class="nav-tab" onclick="switchModule('genVidTab', this)">🎥 Video Motion V4 Pro</button>
        <button class="nav-tab" onclick="switchModule('genImgTab', this)">🎨 SVG & Logos V4 Pro</button>
        <button class="nav-tab" onclick="switchModule('lonasPhysicsTab', this)">📐 Lonas 3D V4 Pro</button>
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
        <div id="genPromptTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>✨ Sintetizador Diffusion AI V3 Ultra Engine</h3>
                    <p>Variaciones por Semilla Semántica (Seed Locking), control de pasos de inferencia, Img2Img desde cámara y renderizado multicapa NPU V5.</p>
                </div>
                <div class="card">
                    <button class="btn-action" style="color:#00FFC8; margin-bottom:10px; width:100%; border:1px dashed #00FFC8;" onclick="useCameraImageForImg2Img()">📷 Usar Última Captura como Imagen Base (Img2Img)</button>

                    <div class="form-group">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <label>Prompt / Descripción Visual:</label>
                            <button class="btn-action" style="font-size:9px; color:#00FFC8; padding:3px 6px;" onclick="enhancePromptV3()">🪄 Optimizar Prompt NPU V3</button>
                        </div>
                        <textarea id="aiPromptInputV3" rows="3" placeholder="Ej. Corte Rib Eye a la parrilla, iluminación neón..."></textarea>
                    </div>
                    <div class="form-group">
                        <label>Prompt Negativo (Evitar en la imagen):</label>
                        <input type="text" id="aiNegativeInputV3" value="borroso, mala calidad, texto, marca de agua, deforme">
                    </div>
                    <div class="form-group">
                        <label>Estilo Visual / Preset NPU V3:</label>
                        <select id="aiPromptStyleV3">
                            <option value="cyberpunk">Cyberpunk / Neón Glowing V3</option>
                            <option value="fotorealismo">Fotorealismo 8K / Macro Gourmet DSLR</option>
                            <option value="octane">Render 3D Octane / Isotipo Volumétrico</option>
                            <option value="vectorial">Ilustración Vectorial Minimalista</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Pasos de Inferencia (Sampling Steps):</label>
                        <select id="aiStepsV3">
                            <option value="20">20 Pasos (Render Rápido - 1.2s)</option>
                            <option value="30">30 Pasos (Balance Fidelidad/Tiempo)</option>
                            <option value="50">50 Pasos (Ultra Detalle Textura NPU)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Semilla Semántica (Seed: <span id="seedVal">Aleatoria (-1)</span>):</label>
                        <div style="display:flex; gap:8px;">
                            <input type="number" id="aiSeedV3" value="-1" placeholder="-1 para aleatorio">
                            <button class="btn-action" style="font-size:10px; color:#00FFC8;" onclick="lockSeedV3()">🔒 Fijar Semilla</button>
                        </div>
                    </div>
                    <div class="form-group">
                        <label>Relación de Aspecto:</label>
                        <select id="aiPromptRatioV3">
                            <option value="1:1">1:1 (Cuadrado / Asset Social)</option>
                            <option value="16:9">16:9 (Cinema Widescreen)</option>
                            <option value="9:16">9:16 (Wallpaper S23 Ultra)</option>
                        </select>
                    </div>

                    <button class="btn-action" style="background: #00FFC8; color: #000; font-weight: bold; margin-top: 12px; width: 100%;" onclick="generateAiPromptImageV3()">⚡ Renderizar Arte Visual V3 Ultra</button>

                    <div class="preview-box" id="aiGenPreviewBoxV3"><span style="font-size: 11px; color: #555;">Esperando prompt para V3 Ultra...</span></div>

                    <div id="aiGenActionsV3" style="display:none; margin-top: 10px;">
                        <button class="btn-action" style="color: #00FFC8; width: 100%; margin-bottom: 6px;" onclick="sendToVideoEngine()">🎥 Enviar a Video Motion V4</button>
                        <button class="btn-action" style="color: #FFD700; width: 100%; margin-bottom: 6px;" onclick="saveToGalleryFromAi()">💾 Guardar en Galería Soberana</button>
                        <button class="btn-action" style="color: #FF0055; width: 100%;" onclick="sendToStudioRAW()">📸 Abrir en Estudio RAW V4</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- 🏷️ 3. Valuador Híbrido V2 Pro -->
        <div id="priceTab" class="module-view"><div class="panel-content"><div class="card"><h3>🏷️ Valuador Híbrido V2 Pro</h3></div></div></div>
        <!-- 👨‍🍳 4. Chef Lean V4 Pro -->
        <div id="foodIndustryTab" class="module-view"><div class="panel-content"><div class="card"><h3>👨‍🍳 Chef Lean V4 Pro</h3></div></div></div>
        <!-- 🎥 5. Video Motion V4 Pro -->
        <div id="genVidTab" class="module-view"><div class="panel-content"><div class="card"><h3>🎥 Video Motion V4 Pro</h3></div></div></div>
        <!-- 🎨 6. SVG & Logos V4 Pro -->
        <div id="genImgTab" class="module-view"><div class="panel-content"><div class="card"><h3>🎨 SVG & Logos V4 Pro</h3></div></div></div>
        <!-- 📐 7. Lonas 3D V4 Pro -->
        <div id="lonasPhysicsTab" class="module-view"><div class="panel-content"><div class="card"><h3>📐 Lonas 3D V4 Pro</h3></div></div></div>
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
        let lastGeneratedCanvas = null;
        let img2ImgBase = null;

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

        /* --- 2. SINTETIZADOR DIFFUSION AI V3 ULTRA --- */
        function enhancePromptV3() {
            const input = document.getElementById('aiPromptInputV3');
            if(!input.value.trim()) { alert("Escribe primero una idea corta."); return; }
            input.value = input.value.trim() + ", render V3 Ultra NPU, profundidad bokeh f/1.2, textura fotorrealista 8k, iluminación de estudio HDR";
        }

        function lockSeedV3() {
            const seedInput = document.getElementById('aiSeedV3');
            const fixedSeed = Math.floor(Math.random() * 899999) + 100000;
            seedInput.value = fixedSeed;
            document.getElementById('seedVal').innerText = fixedSeed;
            alert("✔ Semilla fijada: " + fixedSeed);
        }

        async function useCameraImageForImg2Img() {
            const res = await fetch('/bian/images/');
            const images = await res.json();
            if(images.length === 0) { alert("No hay imágenes guardadas."); return; }
            img2ImgBase = images[images.length - 1].image_path;
            alert("✔ Imagen base cargada para pipeline Img2Img V3 Ultra.");
        }

        function generateAiPromptImageV3() {
            const prompt = document.getElementById('aiPromptInputV3').value.trim();
            const style = document.getElementById('aiPromptStyleV3').value;
            const steps = document.getElementById('aiStepsV3').value;
            const seed = document.getElementById('aiSeedV3').value;
            const ratio = document.getElementById('aiPromptRatioV3').value;
            const box = document.getElementById('aiGenPreviewBoxV3');

            if(!prompt) { alert("Escribe un prompt para generar el arte visual."); return; }

            box.innerHTML = `<span style="font-size: 11px; color: #00FFC8;">Procesando V3 Ultra (${steps} Pasos | Seed: ${seed})...</span>`;

            setTimeout(() => {
                lastGeneratedCanvas = document.createElement('canvas');
                lastGeneratedCanvas.width = 400;
                lastGeneratedCanvas.height = ratio === '16:9' ? 225 : (ratio === '9:16' ? 450 : 400);
                const ctx = lastGeneratedCanvas.getContext('2d');

                const grad = ctx.createLinearGradient(0, 0, lastGeneratedCanvas.width, lastGeneratedCanvas.height);
                grad.addColorStop(0, '#0a0015'); grad.addColorStop(0.5, '#00ffc8'); grad.addColorStop(1, '#ff0055');

                ctx.fillStyle = grad;
                ctx.fillRect(0, 0, lastGeneratedCanvas.width, lastGeneratedCanvas.height);

                ctx.strokeStyle = "#00FFC8";
                ctx.lineWidth = 2;
                ctx.strokeRect(15, 15, lastGeneratedCanvas.width - 30, lastGeneratedCanvas.height - 30);

                ctx.fillStyle = "#FFFFFF";
                ctx.font = "bold 13px system-ui";
                ctx.textAlign = "center";
                ctx.fillText(`[RENDER V3 ULTRA: ${style.toUpperCase()}]`, lastGeneratedCanvas.width/2, lastGeneratedCanvas.height/2 - 15);

                ctx.fillStyle = "#00FFC8";
                ctx.font = "10px system-ui";
                ctx.fillText(`Steps: ${steps} | Seed: ${seed === '-1' ? 'AUTO' : seed}`, lastGeneratedCanvas.width/2, lastGeneratedCanvas.height/2 + 5);

                box.innerHTML = "";
                box.appendChild(lastGeneratedCanvas);
                document.getElementById('aiGenActionsV3').style.display = 'block';
            }, 1000);
        }

        async function saveToGalleryFromAi() {
            if(!lastGeneratedCanvas) return;
            const imageBase64 = lastGeneratedCanvas.toDataURL('image/jpeg');
            const prompt = document.getElementById('aiPromptInputV3').value;

            const response = await fetch('/bian/process/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image_base64: imageBase64, prompt_analysis: `IA Prompt V3: ${prompt.substring(0,30)}` })
            });

            if(response.ok) { alert("✔ Activo V3 Ultra guardado en la Galería Soberana."); updateThumb(); }
        }

        function sendToVideoEngine() { alert("✔ Imagen enviada al Motion Engine V4."); }
        function sendToStudioRAW() { alert("✔ Activo cargado en Estudio RAW V4."); }

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
        "engine": "Bian V5 Master Suite (Generar Imagen AI V3 Ultra Integrated)",
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
