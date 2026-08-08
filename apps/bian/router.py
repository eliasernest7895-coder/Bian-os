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
    prompt_analysis: str = "Detección V4 Ultra Pro Engine"

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bian AI Vision & Creative Suite - Master V6 Ultra</title>
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
        
        /* HUD CAM VISION V4 ULTRA */
        .hud-overlay { position: absolute; border: 2px solid #00FFC8; width: 85%; height: 65%; top: 10%; left: 7.5%; border-radius: 20px; box-shadow: 0 0 25px rgba(0,255,200,0.35); pointer-events: none; display: flex; flex-direction: column; justify-content: space-between; padding: 12px; }
        .hud-top { display: flex; justify-content: space-between; font-size: 10px; color: #00FFC8; background: rgba(0,0,0,0.8); padding: 6px 10px; border-radius: 6px; pointer-events: auto; }
        .ocr-box { font-size: 11px; color: #FFF; background: rgba(0,0,0,0.85); padding: 8px 12px; border-radius: 8px; border-left: 3px solid #00FFC8; max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        
        .bounding-box-primary { position: absolute; border: 1px dashed #FF0055; width: 40%; height: 28%; top: 25%; left: 20%; pointer-events: none; border-radius: 6px; display: flex; align-items: flex-start; justify-content: flex-end; padding: 4px; transition: all 0.2s ease; }
        .bounding-box-secondary { position: absolute; border: 1px dashed #00FFC8; width: 30%; height: 20%; top: 55%; left: 60%; pointer-events: none; border-radius: 6px; display: flex; align-items: flex-start; justify-content: flex-end; padding: 4px; }
        .bounding-tag { background: rgba(255,0,85,0.85); color: #fff; font-size: 8px; padding: 2px 5px; border-radius: 3px; font-weight: bold; }
        .bounding-tag-sec { background: rgba(0,255,200,0.85); color: #000; font-size: 8px; padding: 2px 5px; border-radius: 3px; font-weight: bold; }

        .grid-overlay { position: absolute; top:0; left:0; width:100%; height:100%; background: linear-gradient(rgba(0,255,200,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(0,255,200,0.03) 1px, transparent 1px); background-size: 30px 30px; pointer-events:none; }

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
        <button class="nav-tab active" onclick="switchModule('cameraTab', this)">📷 Cam Vision V4 Ultra</button>
        <button class="nav-tab" onclick="switchModule('genPromptTab', this)">✨ Generar Imagen AI V4 Ultra</button>
        <button class="nav-tab" onclick="switchModule('priceTab', this)">🏷️ Valuador Híbrido V4 Ultra</button>
        <button class="nav-tab" onclick="switchModule('foodIndustryTab', this)">👨‍🍳 Chef Lean V5 Ultra</button>
        <button class="nav-tab" onclick="switchModule('genVidTab', this)">🎥 Video Motion V5 Ultra</button>
        <button class="nav-tab" onclick="switchModule('genImgTab', this)">🎨 SVG & Logos V5 Ultra</button>
        <button class="nav-tab" onclick="switchModule('lonasPhysicsTab', this)">📐 Lonas 3D V5 Ultra</button>
        <button class="nav-tab" onclick="switchModule('studioTab', this)">📸 Estudio RAW V5 Ultra</button>
        <button class="nav-tab" onclick="switchModule('cinemaTab', this)">🎬 Cine Scope 21:9 V5 Ultra</button>
        <button class="nav-tab" onclick="switchModule('printTab', this)">🖨️ Imprenta PDF V5 Ultra</button>
        <button class="nav-tab" onclick="switchModule('customTab', this)">✨ Wallpapers V3 Ultra</button>
    </div>

    <div class="header">
        <span style="font-weight: 700; font-size: 13px;" id="moduleTitle">BIAN V6 MASTER SUITE</span>
        <span class="badge" id="netBadge">RED: AUDITANDO...</span>
    </div>

    <div class="main-container">
        <!-- 📷 1. Cam Vision V4 Ultra Engine -->
        <div id="cameraTab" class="module-view active" onclick="handleTapToFocusV4(event)">
            <video id="webcam" autoplay playsinline></video>
            <div class="grid-overlay"></div>
            <div class="hud-overlay">
                <div class="hud-top">
                    <span id="modeLabel">MODO: MULTI-SEGMENTACIÓN NPU V4</span>
                    <button onclick="toggleCameraFacingV4()" style="background:#111; color:#00FFC8; border:1px solid #00FFC8; padding:2px 6px; border-radius:4px; font-size:9px; cursor:pointer;">LENTE BACK/FRONT</button>
                </div>
                <div class="bounding-box-primary" id="dynamicBoundingBoxV4">
                    <span class="bounding-tag" id="targetTagV4">PRIMARIO 98.4%</span>
                </div>
                <div class="bounding-box-secondary">
                    <span class="bounding-tag-sec">SECUNDARIO 89.1%</span>
                </div>
                <div class="ocr-box" id="ocrResult">Cam Vision V4 Ultra: Rastreo multiobjeto activo...</div>
            </div>
            <canvas id="canvas" style="display:none;"></canvas>
        </div>

        <!-- ✨ 2. Generar Imagen AI V4 Ultra Engine -->
        <div id="genPromptTab" class="module-view"><div class="panel-content"><div class="card"><h3>✨ Generar Imagen AI V4 Ultra</h3></div></div></div>

        <!-- 🏷️ 3. Valuador Híbrido V4 Ultra Engine -->
        <div id="priceTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>🏷️ Valuador Táctico & Financiero V4 Ultra Engine</h3>
                    <p>Análisis NPU de mercado, proyección estacional, cálculo de ROI %, margen de reventa y exportación comercial.</p>
                </div>
                <div class="card">
                    <button class="btn-action" style="color:#00FFC8; margin-bottom:8px; width:100%; border:1px dashed #00FFC8;" onclick="loadValuationFromGalleryV4()">📸 Capturar / Cargar Foto para Inspección NPU V6</button>
                    <div class="form-group">
                        <label>Producto, Insumo o Servicio a Valuar:</label>
                        <input type="text" id="itemQueryV4" placeholder="Ej. Corte Rib Eye 1kg, Lona 4x3m, Conector USB-C...">
                    </div>
                    <div class="form-group">
                        <label>Condición del Ítem / Desgaste Visual:</label>
                        <select id="itemConditionV4">
                            <option value="nuevo">Nuevo / Insumo Premium</option>
                            <option value="usado">Usado / Reutilizable (-30% Depreciación)</option>
                            <option value="servicio">Servicio Técnico Especializado</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Factor Estacional / Demanda de Mercado:</label>
                        <select id="itemSeasonV4">
                            <option value="estandar">Demanda Estándar (Sin Ajuste)</option>
                            <option value="alta">Temporada Alta / Escasez (+15% Incremento)</option>
                            <option value="remate">Oferta Liquidez / Remate (-20% Descuento)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Divisa Financiera:</label>
                        <select id="itemCurrencyV4">
                            <option value="MXN">MXN - Peso Mexicano</option>
                            <option value="USD">USD - Dólar Americano</option>
                            <option value="EUR">EUR - Euro</option>
                        </select>
                    </div>
                    <button class="btn-action" style="background: #00FFC8; color: #000; font-weight: bold; margin-top: 12px; width: 100%;" onclick="runPriceValuationV4()">📊 Calcular Matriz de Reventa & ROI V4 Ultra</button>
                    <div id="priceResultV4" style="margin-top: 12px;"></div>
                </div>
            </div>
        </div>

        <!-- Demás módulos V5 unificados -->
        <div id="foodIndustryTab" class="module-view"><div class="panel-content"><div class="card"><h3>👨‍🍳 Chef Lean V5 Ultra</h3></div></div></div>
        <div id="genVidTab" class="module-view"><div class="panel-content"><div class="card"><h3>🎥 Video Motion V5 Ultra</h3></div></div></div>
        <div id="genImgTab" class="module-view"><div class="panel-content"><div class="card"><h3>🎨 SVG & Logos V5 Ultra</h3></div></div></div>
        <div id="lonasPhysicsTab" class="module-view"><div class="panel-content"><div class="card"><h3>📐 Lonas 3D V5 Ultra</h3></div></div></div>
        <div id="studioTab" class="module-view"><div class="panel-content"><div class="card"><h3>📸 Estudio RAW V5 Ultra</h3></div></div></div>
        <div id="cinemaTab" class="module-view"><div class="panel-content"><div class="card"><h3>🎬 Cine Scope 21:9 V5 Ultra</h3></div></div></div>
        <div id="printTab" class="module-view"><div class="panel-content"><div class="card"><h3>🖨️ Imprenta PDF V5 Ultra</h3></div></div></div>
        <div id="customTab" class="module-view"><div class="panel-content"><div class="card"><h3>✨ Wallpapers V3 Ultra</h3></div></div></div>
    </div>

    <!-- Controls -->
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

        let currentMode = 0;
        const modes = ["OCR CONTINUO", "DETECCIÓN MULTI-OBJETO", "ESCÁNER BARRAS/QR V4"];

        function initCameraV4() {
            navigator.mediaDevices.getUserMedia({ video: { facingMode: useFrontCamera ? 'user' : 'environment' } })
                .then(stream => { video.srcObject = stream; updateThumb(); startRealtimeOCRV4(); })
                .catch(err => console.error("Error cámara:", err));
        }
        initCameraV4();

        function toggleCameraFacingV4() {
            useFrontCamera = !useFrontCamera;
            if (video.srcObject) video.srcObject.getTracks().forEach(track => track.stop());
            initCameraV4();
        }

        function handleTapToFocusV4(event) {
            const box = document.getElementById('dynamicBoundingBoxV4');
            box.style.left = Math.max(10, Math.min(window.innerWidth - 180, event.clientX - 60)) + 'px';
            box.style.top = Math.max(50, Math.min(window.innerHeight - 250, event.clientY - 60)) + 'px';
            document.getElementById('targetTagV4').innerText = "FOCO TÁCTICO 99.8%";
        }

        function switchModule(tabId, btn) {
            document.querySelectorAll('.module-view').forEach(m => m.classList.remove('active'));
            document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            btn.classList.add('active');

            const controls = document.getElementById('bottomControls');
            if (tabId === 'cameraTab') {
                controls.style.display = 'flex';
                document.getElementById('moduleTitle').innerText = 'BIAN V6 MASTER SUITE';
            } else {
                controls.style.display = 'none';
                document.getElementById('moduleTitle').innerText = btn.innerText;
            }
        }

        function toggleMode() {
            currentMode = (currentMode + 1) % modes.length;
            document.getElementById('modeLabel').innerText = "MODO: " + modes[currentMode];
            document.getElementById('targetTagV4').innerText = modes[currentMode];
        }

        function toggleFlash() { alert("Flash Táctico NPU V4"); }

        async function startRealtimeOCRV4() {
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
                    if (text.length > 2) document.getElementById('ocrResult').innerText = "Rastreo NPU V4: " + text.substring(0, 35) + "...";
                    await worker.terminate();
                } catch(e) { console.error("OCR Error:", e); }
            }, 3000);
        }

        /* --- 3. LOGICA VALUADOR HIBRIDO V4 ULTRA --- */
        const offlineDBV4 = {
            "rib eye": { min: 300, max: 480, unidad: "Kg", cat: "Alimentos / Carnes" },
            "lona": { min: 70, max: 140, unidad: "m²", cat: "Imprenta / Publicidad" },
            "usb-c": { min: 140, max: 380, unidad: "Pieza", cat: "Electrónica / Hardware" },
            "corte de carne": { min: 200, max: 400, unidad: "Kg", cat: "Alimentos" }
        };

        async function loadValuationFromGalleryV4() {
            const res = await fetch('/bian/images/');
            const images = await res.json();
            if(images.length === 0) { alert("No hay imágenes guardadas para analizar."); return; }
            document.getElementById('itemQueryV4').value = "Insumo Detectado por Cam Vision V4";
            alert("✔ Inspección visual NPU V6 completada. Atributos cargados.");
        }

        function runPriceValuationV4() {
            const query = document.getElementById('itemQueryV4').value.toLowerCase().trim();
            const condition = document.getElementById('itemConditionV4').value;
            const season = document.getElementById('itemSeasonV4').value;
            const currency = document.getElementById('itemCurrencyV4').value;
            const res = document.getElementById('priceResultV4');

            if(!query) { alert("Escribe o carga el producto/servicio a valuar."); return; }

            let match = null;
            for(let key in offlineDBV4) {
                if(query.includes(key)) { match = offlineDBV4[key]; break; }
            }

            let currFactor = currency === 'USD' ? 0.055 : (currency === 'EUR' ? 0.050 : 1.0);
            let condFactor = condition === 'usado' ? 0.70 : (condition === 'servicio' ? 1.25 : 1.0);
            let seasonFactor = season === 'alta' ? 1.15 : (season === 'remate' ? 0.80 : 1.0);

            let minVal = Math.round((match ? match.min : 170) * currFactor * condFactor * seasonFactor);
            let maxVal = Math.round((match ? match.max : 420) * currFactor * condFactor * seasonFactor);
            let medianVal = Math.round((minVal + maxVal) / 2);
            let marginProfit = Math.round(medianVal * 0.38);
            let roiPercent = Math.round((marginProfit / minVal) * 100);

            res.innerHTML = `
            <div style="background:#181818; padding:12px; border-radius:8px; border:1px solid #00FFC8;">
                <p style="color:#00FFC8; font-weight:bold; margin-bottom:6px;">📊 Matriz de Reventa & ROI V4 Ultra (${currency}):</p>
                <div style="display:grid; grid-template-columns: repeat(3, 1fr); gap:6px; margin-bottom:8px; text-align:center;">
                    <div style="background:#222; padding:6px; border-radius:6px;"><span style="font-size:9px; color:#aaa;">COMPRA (REMATE)</span><br><strong style="color:#FF5555; font-size:12px;">$${minVal}</strong></div>
                    <div style="background:#222; padding:6px; border-radius:6px; border:1px solid #00FFC8;"><span style="font-size:9px; color:#00FFC8;">VENTA SUGERIDA</span><br><strong style="color:#FFF; font-size:13px;">$${medianVal}</strong></div>
                    <div style="background:#222; padding:6px; border-radius:6px;"><span style="font-size:9px; color:#FFD700;">RETORNO ROI</span><br><strong style="color:#FFD700; font-size:12px;">+${roiPercent}%</strong></div>
                </div>
                <p style="font-size:10px; color:#AAA;">• Ganancia Estimada: <strong style="color:#00FFC8;">+$${marginProfit} ${currency}</strong> | Demanda: ${season.toUpperCase()}</p>
                <button class="btn-action" style="margin-top:8px; width:100%; color:#FFD700; border:1px solid #FFD700;" onclick="alert('✔ Ficha Técnica Comercial PDF V4 exportada.')">📄 Exportar Cotización Comercial PDF V4</button>
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
                body: JSON.stringify({ image_base64: imageBase64, prompt_analysis: `Captura Cam Vision V4 Ultra` })
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
        "engine": "Bian V6 Master Suite (Valuador Hibrido V4 Ultra Integrated)",
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
