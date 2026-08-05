from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlmodel import Session, select
from core.database import get_session
from apps.bian.models import ProcessedImage, PrintServiceJob, PhotoStudioSession, CinemaProject
from pydantic import BaseModel
import os
import base64
from datetime import datetime

router = APIRouter(prefix="/bian", tags=["Bian AI Vision Pro"])

class ImageCaptureRequest(BaseModel):
    image_base64: str
    prompt_analysis: str = "Detección NPU Snapdragon"

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bian AI Vision Pro Suite</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: system-ui, sans-serif; }
        body { background: #000; color: #fff; height: 100vh; overflow: hidden; display: flex; flex-direction: column; }
        
        /* Top Navigation Tabs */
        .module-nav { display: flex; background: #0d0d0d; border-bottom: 1px solid #222; overflow-x: auto; white-space: nowrap; }
        .nav-tab { padding: 12px 16px; font-size: 11px; font-weight: 700; color: #888; border: none; background: none; cursor: pointer; text-transform: uppercase; letter-spacing: 0.5px; }
        .nav-tab.active { color: #00FFC8; border-bottom: 2px solid #00FFC8; background: rgba(0,255,200,0.05); }

        .header { padding: 10px 18px; background: rgba(0,0,0,0.85); display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #111; }
        .badge { color: #00FFC8; font-weight: bold; font-size: 10px; border: 1px solid #00FFC8; padding: 3px 6px; border-radius: 4px; }
        
        .main-container { flex: 1; position: relative; display: flex; overflow: hidden; }
        .module-view { display: none; width: 100%; height: 100%; flex-direction: column; position: relative; }
        .module-view.active { display: flex; }

        /* Camara View */
        video { width: 100%; height: 100%; object-fit: cover; }
        .hud-overlay { position: absolute; border: 2px solid #00FFC8; width: 65%; height: 45%; top: 25%; left: 17.5%; border-radius: 16px; box-shadow: 0 0 20px rgba(0,255,200,0.25); pointer-events: none; }
        .hud-info { position: absolute; bottom: 12px; left: 12px; font-size: 11px; color: #00FFC8; background: rgba(0,0,0,0.6); padding: 4px 8px; border-radius: 4px; }
        
        /* Controls Bar */
        .controls { padding: 16px 24px; background: rgba(13,13,13,0.95); display: flex; justify-content: space-around; align-items: center; border-top: 1px solid #222; }
        .btn-shutter { width: 68px; height: 68px; border-radius: 50%; background: #fff; border: 4px solid #00FFC8; cursor: pointer; }
        .thumb-preview { width: 44px; height: 44px; border-radius: 8px; border: 2px solid #00FFC8; background: #111; overflow: hidden; cursor: pointer; display: flex; align-items: center; justify-content: center; }
        .thumb-preview img { width: 100%; height: 100%; object-fit: cover; }
        .btn-action { background: #1E1E1E; color: #fff; border: 1px solid #333; padding: 8px 14px; border-radius: 8px; font-size: 12px; font-weight: 600; cursor: pointer; }

        /* Panels de Imprenta, Estudio y Cine */
        .panel-content { padding: 20px; overflow-y: auto; flex: 1; background: #0a0a0a; }
        .card { background: #121212; border: 1px solid #222; border-radius: 12px; padding: 16px; margin-bottom: 16px; }
        .card h3 { color: #00FFC8; font-size: 15px; margin-bottom: 8px; }
        .card p { color: #aaa; font-size: 12px; line-height: 1.4; }
        
        /* Modal Galería */
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.95); z-index: 100; flex-direction: column; padding: 20px; }
        .gallery-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; overflow-y: auto; flex: 1; }
        .gallery-item { background: #111; border: 1px solid #333; border-radius: 10px; padding: 8px; }
        .gallery-item img { width: 100%; height: 120px; object-fit: cover; border-radius: 6px; }
    </style>
</head>
<body>
    <!-- Top Module Nav -->
    <div class="module-nav">
        <button class="nav-tab active" onclick="switchModule('cameraTab', this)">📷 Cam Vision</button>
        <button class="nav-tab" onclick="switchModule('printTab', this)">🖨️ Imprenta / Copias</button>
        <button class="nav-tab" onclick="switchModule('studioTab', this)">📸 Estudio Foto</button>
        <button class="nav-tab" onclick="switchModule('cinemaTab', this)">🎬 Cine / Video</button>
    </div>

    <div class="header">
        <span style="font-weight: 700; font-size: 13px;" id="moduleTitle">BIAN VISION IA</span>
        <span class="badge" id="npuBadge">NPU: ONLINE</span>
    </div>

    <div class="main-container">
        <!-- Module 1: Camera -->
        <div id="cameraTab" class="module-view active">
            <video id="webcam" autoplay playsinline></video>
            <div class="hud-overlay">
                <div class="hud-info" id="hudInfo">LATENCY: 12ms | 1080p</div>
            </div>
            <canvas id="canvas" style="display:none;"></canvas>
        </div>

        <!-- Module 2: Imprenta y Servicios -->
        <div id="printTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>🖨️ Centro de Impresión & Copiado</h3>
                    <p>Gestión local de documentos, escaneo en alta definición y cola de impresión para servomotores/impresoras en red.</p>
                </div>
                <div class="card">
                    <h3>📄 Nuevo Trabajo de Copia</h3>
                    <p>Tamaño: Carta / Oficio | Modo: Color HD | Duplex: Activo</p>
                    <button class="btn-action" style="margin-top: 10px; color: #00FFC8;">Crear Orden de Impresión</button>
                </div>
            </div>
        </div>

        <!-- Module 3: Estudio Fotográfico -->
        <div id="studioTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>📸 Estudio Fotográfico Profesional</h3>
                    <p>Procesamiento RAW, presets de iluminación Rembrandt, corrección de color y remoción de fondos por IA local.</p>
                </div>
                <div class="card">
                    <h3>🎨 Presets de Luz NPU</h3>
                    <p>Filtro activo: Softbox Neón Pro | Relación: 4:3</p>
                    <button class="btn-action" style="margin-top: 10px; color: #00FFC8;">Aplicar Estudio AI</button>
                </div>
            </div>
        </div>

        <!-- Module 4: Cine y Video -->
        <div id="cinemaTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>🎬 Edición de Cine & Video Pro</h3>
                    <p>Renderizado offline, aplicación de LUTs cinematográficos (Teal & Orange), corte a 24 FPS y formato 21:9 CinemaScope.</p>
                </div>
                <div class="card">
                    <h3>🎥 Nuevo Proyecto de Cine</h3>
                    <p>Formato: 21:9 CinemaScope | Color Grading: Snapdragon LUT</p>
                    <button class="btn-action" style="margin-top: 10px; color: #00FFC8;">Iniciar Proyecto Cinema</button>
                </div>
            </div>
        </div>
    </div>

    <!-- Bottom Controls (Solo activos en Vista Cámara) -->
    <div class="controls" id="bottomControls">
        <div class="thumb-preview" id="thumbBox" onclick="openGallery()">
            <span style="font-size: 9px; color: #666;">GALERÍA</span>
        </div>
        <button class="btn-shutter" onclick="capture()"></button>
        <button class="btn-action" style="color: #00FFC8;" onclick="toggleMode()">IA Mode</button>
    </div>

    <!-- Modal Galería -->
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
        let currentMode = "ANALYSIS";

        navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })
            .then(stream => { video.srcObject = stream; updateThumb(); })
            .catch(err => console.error("Error cámara:", err));

        function switchModule(tabId, btn) {
            document.querySelectorAll('.module-view').forEach(m => m.classList.remove('active'));
            document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
            
            document.getElementById(tabId).classList.add('active');
            btn.classList.add('active');

            const controls = document.getElementById('bottomControls');
            if (tabId === 'cameraTab') {
                controls.style.display = 'flex';
                document.getElementById('moduleTitle').innerText = 'BIAN VISION IA';
            } else {
                controls.style.display = 'none';
                document.getElementById('moduleTitle').innerText = btn.innerText;
            }
        }

        async function capture() {
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            const imageBase64 = canvas.toDataURL('image/jpeg');

            const response = await fetch('/bian/process/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    image_base64: imageBase64,
                    prompt_analysis: `Modo: ${currentMode} | Snapdragon Engine`
                })
            });

            if(response.ok) {
                const saved = await response.json();
                updateThumb(saved.image_path);
            }
        }

        async function updateThumb(pathOverride) {
            const thumbBox = document.getElementById('thumbBox');
            if(pathOverride) {
                thumbBox.innerHTML = `<img src="${pathOverride}" />`;
                return;
            }
            const res = await fetch('/bian/images/');
            const images = await res.json();
            if(images.length > 0) {
                thumbBox.innerHTML = `<img src="${images[images.length - 1].image_path}" />`;
            }
        }

        async function openGallery() {
            document.getElementById('galleryModal').style.display = 'flex';
            const res = await fetch('/bian/images/');
            const images = await res.json();
            const grid = document.getElementById('galleryGrid');
            grid.innerHTML = images.map(img => `
                <div class="gallery-item">
                    <img src="${img.image_path}" />
                    <p style="font-size: 10px; color: #aaa; margin-top: 4px;">${img.prompt_analysis}</p>
                </div>
            `).join('');
        }

        function closeGallery() {
            document.getElementById('galleryModal').style.display = 'none';
        }

        function toggleMode() {
            currentMode = currentMode === "ANALYSIS" ? "ENHANCE" : "ANALYSIS";
            document.getElementById('hudInfo').innerText = `MODE: ${currentMode} | 1080p`;
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
        "engine": "Snapdragon Vision Neural Engine",
        "features": ["camera_ia", "print_services", "photo_studio", "cinema_editor"],
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

# --- Endpoints de Servicios ---

@router.post("/print/jobs/", response_model=PrintServiceJob)
def create_print_job(job: PrintServiceJob, session: Session = Depends(get_session)):
    session.add(job)
    session.commit()
    session.refresh(job)
    return job

@router.post("/studio/sessions/", response_model=PhotoStudioSession)
def create_studio_session(studio: PhotoStudioSession, session: Session = Depends(get_session)):
    session.add(studio)
    session.commit()
    session.refresh(studio)
    return studio

@router.post("/cinema/projects/", response_model=CinemaProject)
def create_cinema_project(project: CinemaProject, session: Session = Depends(get_session)):
    session.add(project)
    session.commit()
    session.refresh(project)
    return project
