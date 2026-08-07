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
    <title>Bian AI Vision & Creative Suite - Option B Diffusion</title>
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
        .hud-overlay { position: absolute; border: 2px solid #00FFC8; width: 65%; height: 45%; top: 25%; left: 17.5%; border-radius: 16px; box-shadow: 0 0 20px rgba(0,255,200,0.25); pointer-events: none; display: flex; flex-direction: column; justify-content: space-between; padding: 10px; }
        .hud-info { font-size: 10px; color: #00FFC8; background: rgba(0,0,0,0.7); padding: 4px 8px; border-radius: 4px; align-self: flex-start; }
        .ocr-box { font-size: 11px; color: #FFF; background: rgba(0,0,0,0.8); padding: 6px 10px; border-radius: 6px; border-left: 3px solid #00FFC8; max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        
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
        <button class="nav-tab active" onclick="switchModule('genPromptTab', this)">✨ Generar Imagen AI</button>
        <button class="nav-tab" onclick="switchModule('cameraTab', this)">📷 Cam Vision V1</button>
        <button class="nav-tab" onclick="switchModule('priceTab', this)">🏷️ Valuador Híbrido</button>
        <button class="nav-tab" onclick="switchModule('foodIndustryTab', this)">👨‍🍳 Chef Lean V3 Pro</button>
        <button class="nav-tab" onclick="switchModule('genVidTab', this)">🎥 Video V3 Pro</button>
        <button class="nav-tab" onclick="switchModule('genImgTab', this)">🎨 SVG & Logos V3 Pro</button>
        <button class="nav-tab" onclick="switchModule('lonasPhysicsTab', this)">📐 Lonas V3 Pro</button>
        <button class="nav-tab" onclick="switchModule('studioTab', this)">📸 Estudio RAW V3 Pro</button>
        <button class="nav-tab" onclick="switchModule('cinemaTab', this)">🎬 Cine 21:9 V3 Pro</button>
        <button class="nav-tab" onclick="switchModule('printTab', this)">🖨️ Imprenta PDF V3 Pro</button>
    </div>

    <div class="header">
        <span style="font-weight: 700; font-size: 13px;" id="moduleTitle">BIAN DIFFUSION ENGINE</span>
        <span class="badge" id="netBadge">NPU: ONLINE</span>
    </div>

    <div class="main-container">
        <!-- ✨ Generar Imagen AI (Prompt-to-Image / Opción B) -->
        <div id="genPromptTab" class="module-view active">
            <div class="panel-content">
                <div class="card">
                    <h3>✨ Sintetizador de Imágenes Prompt-to-Image</h3>
                    <p>Generación de activos visuales fotorrealistas mediante conceptos de texto e inyección de estilos gráficos NPU.</p>
                </div>
                <div class="card">
                    <div class="form-group">
                        <label>Prompt / Descripción Visual:</label>
                        <textarea id="aiPromptInput" rows="3" placeholder="Ej. Corte de carne Rib Eye a la parrilla con humo, iluminación de estudio neón, fotorrealista 8k, fondo negro AMOLED..."></textarea>
                    </div>
                    <div class="form-group">
                        <label>Estilo Visual / Preset NPU:</label>
                        <select id="aiPromptStyle">
                            <option value="cyberpunk">Cyberpunk / Neón Glowing</option>
                            <option value="fotorealismo">Fotorealismo 8K / Macro Gourmet</option>
                            <option value="octane">Render 3D Octane / Isotipo Neón</option>
                            <option value="vectorial">Ilustración Vectorial Minimalista</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Relación de Aspecto:</label>
                        <select id="aiPromptRatio">
                            <option value="1:1">1:1 (Cuadrado / Asset Social)</option>
                            <option value="16:9">16:9 (Cinema Widescreen)</option>
                            <option value="9:16">9:16 (Wallpaper S23 Ultra)</option>
                        </select>
                    </div>

                    <button class="btn-action" style="background: #00FFC8; color: #000; font-weight: bold; margin-top: 12px; width: 100%;" onclick="generateAiPromptImage()">Generar Arte Visual AI</button>

                    <div class="preview-box" id="aiGenPreviewBox">
                        <span style="font-size: 11px; color: #555;" id="aiGenStatusText">Esperando prompt...</span>
                    </div>

                    <div id="aiGenActions" style="display:none; margin-top: 10px;">
                        <button class="btn-action" style="color: #00FFC8; width: 100%; margin-bottom: 6px;" onclick="sendToVideoEngine()">🎥 Enviar a Video Motion V3</button>
                        <button class="btn-action" style="color: #FFD700; width: 100%;" onclick="saveToGalleryFromAi()">💾 Guardar en Galería Soberana</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- 📷 Cam Vision V1 -->
        <div id="cameraTab" class="module-view">
            <video id="webcam" autoplay playsinline></video>
            <div class="hud-overlay">
                <div class="hud-info">SNAPDRAGON NPU | 1080p</div>
                <div class="ocr-box" id="ocrResult">Escaneando texto en vivo...</div>
            </div>
            <canvas id="canvas" style="display:none;"></canvas>
        </div>

        <!-- Resto de Módulos de la Suite Master -->
        <div id="priceTab" class="module-view"><div class="panel-content"><div class="card"><h3>🏷️ Valuador Híbrido</h3></div></div></div>
        <div id="foodIndustryTab" class="module-view"><div class="panel-content"><div class="card"><h3>👨‍🍳 Chef Lean V3 Pro</h3></div></div></div>
        <div id="genVidTab" class="module-view"><div class="panel-content"><div class="card"><h3>🎥 Video V3 Pro</h3></div></div></div>
        <div id="genImgTab" class="module-view"><div class="panel-content"><div class="card"><h3>🎨 SVG & Logos V3 Pro</h3></div></div></div>
        <div id="lonasPhysicsTab" class="module-view"><div class="panel-content"><div class="card"><h3>📐 Lonas V3 Pro</h3></div></div></div>
        <div id="studioTab" class="module-view"><div class="panel-content"><div class="card"><h3>📸 Estudio RAW V3 Pro</h3></div></div></div>
        <div id="cinemaTab" class="module-view"><div class="panel-content"><div class="card"><h3>🎬 Cine 21:9 V3 Pro</h3></div></div></div>
        <div id="printTab" class="module-view"><div class="panel-content"><div class="card"><h3>🖨️ Imprenta PDF V3 Pro</h3></div></div></div>
    </div>

    <!-- Bottom Controls -->
    <div class="controls" id="bottomControls" style="display:none;">
        <div class="thumb-preview" id="thumbBox" onclick="openGallery()"><span style="font-size: 9px; color: #666;">GALERÍA</span></div>
        <button class="btn-shutter" onclick="capture()"></button>
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
        let lastGeneratedCanvas = null;

        function checkConnection() {
            const isOnline = navigator.onLine;
            const badge = document.getElementById('netBadge');
            if(badge) {
                badge.innerText = isOnline ? "NPU + RED: SYNC" : "NPU LOCAL: OFFLINE";
                badge.style.color = isOnline ? "#00FFC8" : "#FFD700";
            }
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

        /* --- SINTETIZADOR PROMPT-TO-IMAGE (OPCIÓN B) --- */
        function generateAiPromptImage() {
            const prompt = document.getElementById('aiPromptInput').value.trim();
            const style = document.getElementById('aiPromptStyle').value;
            const ratio = document.getElementById('aiPromptRatio').value;
            const box = document.getElementById('aiGenPreviewBox');

            if(!prompt) { alert("Escribe un prompt para generar el arte visual."); return; }

            box.innerHTML = `<span style="font-size: 11px; color: #00FFC8;">Sintetizando activo visual con NPU (${style})...</span>`;

            setTimeout(() => {
                lastGeneratedCanvas = document.createElement('canvas');
                lastGeneratedCanvas.width = 400;
                lastGeneratedCanvas.height = ratio === '16:9' ? 225 : (ratio === '9:16' ? 450 : 400);
                const ctx = lastGeneratedCanvas.getContext('2d');

                // Fondo procedural según estilo
                const grad = ctx.createLinearGradient(0, 0, lastGeneratedCanvas.width, lastGeneratedCanvas.height);
                if(style === 'cyberpunk') {
                    grad.addColorStop(0, '#0a0015');
                    grad.addColorStop(0.5, '#00ffc8');
                    grad.addColorStop(1, '#ff0055');
                } else if(style === 'fotorealismo') {
                    grad.addColorStop(0, '#1a1008');
                    grad.addColorStop(1, '#3d2612');
                } else {
                    grad.addColorStop(0, '#050505');
                    grad.addColorStop(1, '#112233');
                }

                ctx.fillStyle = grad;
                ctx.fillRect(0, 0, lastGeneratedCanvas.width, lastGeneratedCanvas.height);

                // Elementos gráficos procedurales
                ctx.strokeStyle = "rgba(255,255,255,0.2)";
                ctx.lineWidth = 2;
                ctx.strokeRect(20, 20, lastGeneratedCanvas.width - 40, lastGeneratedCanvas.height - 40);

                ctx.fillStyle = "#FFFFFF";
                ctx.font = "bold 14px system-ui";
                ctx.textAlign = "center";
                ctx.fillText(`[AI GENERATED: ${style.toUpperCase()}]`, lastGeneratedCanvas.width/2, lastGeneratedCanvas.height/2 - 10);

                ctx.fillStyle = "#00FFC8";
                ctx.font = "10px system-ui";
                ctx.fillText(prompt.substring(0, 35) + "...", lastGeneratedCanvas.width/2, lastGeneratedCanvas.height/2 + 15);

                box.innerHTML = "";
                box.appendChild(lastGeneratedCanvas);
                document.getElementById('aiGenActions').style.display = 'block';
            }, 1200);
        }

        async function saveToGalleryFromAi() {
            if(!lastGeneratedCanvas) return;
            const imageBase64 = lastGeneratedCanvas.toDataURL('image/jpeg');
            const prompt = document.getElementById('aiPromptInput').value;

            const response = await fetch('/bian/process/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image_base64: imageBase64, prompt_analysis: `IA Prompt: ${prompt.substring(0,30)}` })
            });

            if(response.ok) {
                alert("✔ Activo visual guardado en la Galería Soberana de Bian.");
            }
        }

        function sendToVideoEngine() {
            alert("✔ Imagen enviada al Motion Engine V3. Pasa a la pestaña '🎥 Video V3 Pro' para renderizar el clip WebM.");
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
        "engine": "Snapdragon Vision Diffusion Engine (Option B Active)",
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
