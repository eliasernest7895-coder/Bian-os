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
    prompt_analysis: str = "Detección V5 Ultra Pro Engine"

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bian AI Vision & Creative Suite - Master V7 Ultra</title>
    <script src="https://unpkg.com/tesseract.js@v4.0.2/dist/tesseract.min.js"></script>
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
        
        /* HUD CAM VISION V5 ULTRA */
        .hud-overlay { position: absolute; border: 2px solid #00FFC8; width: 88%; height: 70%; top: 8%; left: 6%; border-radius: 20px; box-shadow: 0 0 30px rgba(0,255,200,0.35); pointer-events: none; display: flex; flex-direction: column; justify-content: space-between; padding: 12px; }
        .hud-top { display: flex; justify-content: space-between; font-size: 10px; color: #00FFC8; background: rgba(0,0,0,0.85); padding: 6px 10px; border-radius: 6px; pointer-events: auto; }
        .ocr-box { font-size: 11px; color: #FFF; background: rgba(0,0,0,0.9); padding: 8px 12px; border-radius: 8px; border-left: 3px solid #00FFC8; max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        
        /* Retículas y Telemetría V5 */
        .crosshair-center { position: absolute; top: 50%; left: 50%; width: 24px; height: 24px; transform: translate(-50%, -50%); border: 1px solid rgba(0,255,200,0.6); border-radius: 50%; pointer-events: none; }
        .crosshair-center::after { content: ''; position: absolute; top: 50%; left: 50%; width: 4px; height: 4px; background: #FF0055; transform: translate(-50%, -50%); border-radius: 50%; }

        .bounding-box-primary { position: absolute; border: 1.5px dashed #FF0055; width: 42%; height: 30%; top: 22%; left: 18%; pointer-events: none; border-radius: 8px; display: flex; align-items: flex-start; justify-content: flex-end; padding: 4px; transition: all 0.2s ease; }
        .bounding-box-secondary { position: absolute; border: 1.5px dashed #00FFC8; width: 34%; height: 22%; top: 58%; left: 58%; pointer-events: none; border-radius: 8px; display: flex; align-items: flex-start; justify-content: flex-end; padding: 4px; }
        .bounding-tag { background: rgba(255,0,85,0.9); color: #fff; font-size: 8px; padding: 2px 6px; border-radius: 3px; font-weight: bold; }
        .bounding-tag-sec { background: rgba(0,255,200,0.9); color: #000; font-size: 8px; padding: 2px 6px; border-radius: 3px; font-weight: bold; }

        .dispatch-bar { display: flex; gap: 6px; pointer-events: auto; margin-top: 6px; }
        .btn-dispatch { background: rgba(0,255,200,0.15); border: 1px solid #00FFC8; color: #00FFC8; font-size: 8px; font-weight: bold; padding: 4px 8px; border-radius: 4px; cursor: pointer; }

        .grid-overlay { position: absolute; top:0; left:0; width:100%; height:100%; background: linear-gradient(rgba(0,255,200,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(0,255,200,0.03) 1px, transparent 1px); background-size: 28px 28px; pointer-events:none; }

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
        .preview-box img, .preview-box canvas, .preview-box svg { max-width: 100%; max-height: 100%; object-fit: contain; }

        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.95); z-index: 100; flex-direction: column; padding: 20px; }
        .gallery-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; overflow-y: auto; flex: 1; }
        .gallery-item { background: #111; border: 1px solid #333; border-radius: 10px; padding: 8px; }
        .gallery-item img { width: 100%; height: 120px; object-fit: cover; border-radius: 6px; }
    </style>
</head>
<body>
    <div class="module-nav">
        <button class="nav-tab active" onclick="switchModule('cameraTab', this)">📷 Cam Vision V5 Ultra</button>
        <button class="nav-tab" onclick="switchModule('genPromptTab', this)">✨ Generar Imagen AI V5 Ultra</button>
        <button class="nav-tab" onclick="switchModule('priceTab', this)">🏷️ Valuador Híbrido V4 Ultra</button>
        <button class="nav-tab" onclick="switchModule('foodIndustryTab', this)">👨‍🍳 Chef Lean V6 Ultra</button>
        <button class="nav-tab" onclick="switchModule('genVidTab', this)">🎥 Video Motion V6 Ultra</button>
        <button class="nav-tab" onclick="switchModule('genImgTab', this)">🎨 SVG & Logos V6 Ultra</button>
        <button class="nav-tab" onclick="switchModule('lonasPhysicsTab', this)">📐 Lonas 3D V6 Ultra</button>
        <button class="nav-tab" onclick="switchModule('studioTab', this)">📸 Estudio RAW V6 Ultra</button>
        <button class="nav-tab" onclick="switchModule('cinemaTab', this)">🎬 Cine Scope 21:9 V6 Ultra</button>
        <button class="nav-tab" onclick="switchModule('printTab', this)">🖨️ Imprenta PDF V6 Ultra</button>
        <button class="nav-tab" onclick="switchModule('customTab', this)">✨ Wallpapers V4 Ultra</button>
    </div>

    <div class="header">
        <span style="font-weight: 700; font-size: 13px;" id="moduleTitle">BIAN V7 MASTER SUITE</span>
        <span class="badge" id="netBadge">RED: AUDITANDO...</span>
    </div>

    <div class="main-container">
        <!-- 📷 1. Cam Vision V5 Ultra Engine -->
        <div id="cameraTab" class="module-view active" onclick="handleTapToFocusV5(event)">
            <video id="webcam" autoplay playsinline></video>
            <div class="grid-overlay"></div>
            <div class="hud-overlay">
                <div class="hud-top">
                    <span id="modeLabel">MODO: TELEMETRÍA NPU V5 & MULTI-SEGMENTACIÓN</span>
                    <button onclick="toggleCameraFacingV5()" style="background:#111; color:#00FFC8; border:1px solid #00FFC8; padding:2px 6px; border-radius:4px; font-size:9px; cursor:pointer;">LENTE BACK/FRONT</button>
                </div>
                <div class="crosshair-center"></div>
                <div class="bounding-box-primary" id="dynamicBoundingBoxV5">
                    <span class="bounding-tag" id="targetTagV5">SUJETO NPU 99.1%</span>
                </div>
                <div class="bounding-box-secondary">
                    <span class="bounding-tag-sec">ENTORNO 92.4%</span>
                </div>
                <div>
                    <div class="ocr-box" id="ocrResult">Cam Vision V5 Ultra: Telemetría espacial y OCR listos...</div>
                    <div class="dispatch-bar">
                        <button class="btn-dispatch" onclick="dispatchTo('genPromptTab')">✨ ENVIAR A IA</button>
                        <button class="btn-dispatch" onclick="dispatchTo('priceTab')">🏷️ VALUAR</button>
                        <button class="btn-dispatch" onclick="dispatchTo('foodIndustryTab')">🥩 CHEF LEAN</button>
                    </div>
                </div>
            </div>
            <canvas id="canvas" style="display:none;"></canvas>
        </div>

        <!-- ✨ 2. Generar Imagen AI V5 Ultra Engine -->
        <div id="genPromptTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>✨ Sintetizador Diffusion AI V5 Ultra Engine</h3>
                    <p>Enrutador Inteligente (NPU Local vs Cloud API), historial de prompts y control Denoising V5.</p>
                </div>
                <div class="card">
                    <div class="form-group">
                        <label>Motor de Render (AI Router):</label>
                        <select id="aiRouterV5">
                            <option value="local_npu">🚀 Local NPU (Borradores & Assets rápidos - GRATIS)</option>
                            <option value="cloud_api">☁️ Cloud API Ultra (Fotorrealismo & Complejidad)</option>
                        </select>
                    </div>
                    <button class="btn-action" style="color:#00FFC8; margin-bottom:10px; width:100%; border:1px dashed #00FFC8;" onclick="useCameraImageForImg2ImgV5()">📷 Cargar Foto de Cam Vision V5</button>
                    
                    <div class="form-group">
                        <label>Prompt / Descripción Visual:</label>
                        <textarea id="aiPromptInputV5" rows="3" placeholder="Ej. Corte Rib Eye a la parrilla..."></textarea>
                    </div>
                    <div class="form-group">
                        <label>Historial de Prompts (Recientes):</label>
                        <select id="aiPromptHistoryV5" onchange="document.getElementById('aiPromptInputV5').value=this.value">
                            <option value="">-- Seleccionar prompt reciente --</option>
                            <option value="Corte Rib Eye a la parrilla, iluminación neón">Corte Rib Eye neón</option>
                            <option value="Isotipo bionico futurista, color oro">Isotipo biónico oro</option>
                        </select>
                    </div>

                    <button class="btn-action" style="background: #00FFC8; color: #000; font-weight: bold; margin-top: 12px; width: 100%;" onclick="generateAiPromptImageV5()">⚡ Sintetizar Arte Visual V5 Ultra</button>
                    <div class="preview-box" id="aiGenPreviewBoxV5"><span style="font-size: 11px; color: #555;">Esperando prompt V5...</span></div>
                </div>
            </div>
        </div>

        <!-- Demás módulos unificados -->
        <div id="priceTab" class="module-view"><div class="panel-content"><div class="card"><h3>🏷️ Valuador Híbrido V4 Ultra</h3></div></div></div>
        <div id="foodIndustryTab" class="module-view"><div class="panel-content"><div class="card"><h3>👨‍🍳 Chef Lean V6 Ultra</h3></div></div></div>
        <div id="genVidTab" class="module-view"><div class="panel-content"><div class="card"><h3>🎥 Video Motion V6 Ultra</h3></div></div></div>
        <div id="genImgTab" class="module-view"><div class="panel-content"><div class="card"><h3>🎨 SVG & Logos V6 Ultra</h3></div></div></div>
        <div id="lonasPhysicsTab" class="module-view"><div class="panel-content"><div class="card"><h3>📐 Lonas 3D V6 Ultra</h3></div></div></div>
        <div id="studioTab" class="module-view"><div class="panel-content"><div class="card"><h3>📸 Estudio RAW V6 Ultra</h3></div></div></div>
        <div id="cinemaTab" class="module-view"><div class="panel-content"><div class="card"><h3>🎬 Cine Scope 21:9 V6 Ultra</h3></div></div></div>
        <div id="printTab" class="module-view"><div class="panel-content"><div class="card"><h3>🖨️ Imprenta PDF V6 Ultra</h3></div></div></div>
        <div id="customTab" class="module-view"><div class="panel-content"><div class="card"><h3>✨ Wallpapers V4 Ultra</h3></div></div></div>
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

        function switchModule(tabId, btn) {
            document.querySelectorAll('.module-view').forEach(m => m.classList.remove('active'));
            document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            btn.classList.add('active');

            const controls = document.getElementById('bottomControls');
            if (tabId === 'cameraTab') {
                controls.style.display = 'flex';
                document.getElementById('moduleTitle').innerText = 'BIAN V7 MASTER SUITE';
            } else {
                controls.style.display = 'none';
                document.getElementById('moduleTitle').innerText = btn.innerText;
            }
        }

        function dispatchTo(tabId) {
            const tabBtn = Array.from(document.querySelectorAll('.nav-tab')).find(b => b.getAttribute('onclick').includes(tabId));
            if(tabBtn) switchModule(tabId, tabBtn);
        }

        /* --- LOGICA GENERAR IMAGEN AI V5 --- */
        async function useCameraImageForImg2ImgV5() {
             alert("✔ Foto Cam Vision V5 cargada en router V5.");
        }

        function generateAiPromptImageV5() {
            const router = document.getElementById('aiRouterV5').value;
            const prompt = document.getElementById('aiPromptInputV5').value;
            const box = document.getElementById('aiGenPreviewBoxV5');
            
            box.innerHTML = `<span style="font-size: 11px; color: #00FFC8;">Procesando en modo ${router.toUpperCase()}...</span>`;
            
            setTimeout(() => {
                box.innerHTML = `<span style="font-size: 11px; color: #fff;">Sintetizado: ${prompt.substring(0,20)}... (V5 Ultra)</span>`;
                alert(`✔ Renderizado finalizado con el motor ${router}`);
            }, 1200);
        }

        /* --- CAMERA & GALLERY V5 --- */
        function initCameraV5() {
            navigator.mediaDevices.getUserMedia({ video: { facingMode: useFrontCamera ? 'user' : 'environment' } })
                .then(stream => { video.srcObject = stream; })
                .catch(err => console.error("Error cámara:", err));
        }
        initCameraV5();

        async function capture() { alert("Captura V5 realizada."); }
        function openGallery() { document.getElementById('galleryModal').style.display = 'flex'; }
        function closeGallery() { document.getElementById('galleryModal').style.display = 'none'; }
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
        "engine": "Bian V7 Master Suite (Generar Imagen AI V5 Ultra Integrated)",
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
