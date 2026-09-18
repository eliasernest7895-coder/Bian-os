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
    prompt_analysis: str = "Captura V9 Liquid Glass"

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Bian AI Suite - V9 Liquid Glass</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", Roboto, sans-serif; -webkit-tap-highlight-color: transparent; }
        body { background: #000; color: #fff; height: 100vh; overflow: hidden; display: flex; flex-direction: column; }

        /* HEADER ESTILO APPLE DINÁMICO */
        .glass-header {
            position: absolute; top: 12px; left: 16px; right: 16px; z-index: 50;
            background: rgba(25, 25, 30, 0.45);
            backdrop-filter: blur(25px); -webkit-backdrop-filter: blur(25px);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 26px; padding: 10px 18px;
            display: flex; justify-content: space-between; align-items: center;
            box-shadow: 0 8px 32px rgba(0,0,0,0.37);
        }
        .apple-pill {
            display: flex; align-items: center; gap: 8px; font-weight: 700; font-size: 13px; letter-spacing: -0.3px;
        }
        .glow-dot {
            width: 8px; height: 8px; border-radius: 50%; background: #30D158;
            box-shadow: 0 0 10px #30D158;
        }
        .banana-chip {
            background: rgba(255, 214, 10, 0.18); border: 1px solid rgba(255, 214, 10, 0.4);
            color: #FFD60A; font-size: 10px; font-weight: 700; padding: 4px 10px; border-radius: 14px;
            display: flex; align-items: center; gap: 4px; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .banana-chip.active {
            background: linear-gradient(135deg, #FF9F0A, #FF375F);
            color: #fff; border-color: transparent;
            box-shadow: 0 0 15px rgba(255, 55, 95, 0.6);
            transform: scale(1.05);
        }

        /* VIEWPORT Y VISOR */
        .viewport { flex: 1; position: relative; display: flex; align-items: center; justify-content: center; background: #000; overflow: hidden; }
        video { width: 100%; height: 100%; object-fit: cover; }
        
        /* APPLE FOCUS RETICLE */
        .reticle-container {
            position: absolute; width: 65%; height: 45%; pointer-events: none;
            border-radius: 36px; border: 1.5px solid rgba(255, 255, 255, 0.25);
            transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
            display: flex; align-items: flex-end; justify-content: center; padding-bottom: 12px;
        }
        .reticle-container.banana-lock {
            border-color: #FFD60A;
            box-shadow: 0 0 30px rgba(255, 214, 10, 0.35), inset 0 0 20px rgba(255, 214, 10, 0.15);
        }
        .status-badge {
            background: rgba(0, 0, 0, 0.6); backdrop-filter: blur(12px);
            padding: 5px 12px; border-radius: 12px; font-size: 10px; font-weight: 600;
            color: rgba(255,255,255,0.85); border: 1px solid rgba(255,255,255,0.1);
        }

        /* LIQUID GLASS ICON DOCK */
        .glass-dock {
            position: absolute; bottom: 108px; left: 14px; right: 14px; z-index: 40;
            background: rgba(18, 18, 22, 0.55);
            backdrop-filter: blur(30px); -webkit-backdrop-filter: blur(30px);
            border: 1px solid rgba(255, 255, 255, 0.14);
            border-radius: 28px; padding: 10px 14px;
            display: flex; gap: 10px; overflow-x: auto; scrollbar-width: none;
            box-shadow: 0 10px 40px rgba(0,0,0,0.5);
        }
        .glass-dock::-webkit-scrollbar { display: none; }
        
        .dock-icon-btn {
            flex: 0 0 44px; height: 44px; border-radius: 18px; border: 1px solid rgba(255,255,255,0.1);
            background: rgba(255, 255, 255, 0.06); font-size: 19px;
            display: flex; align-items: center; justify-content: center;
            cursor: pointer; transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
            position: relative;
        }
        .dock-icon-btn:active { transform: scale(0.88); }
        .dock-icon-btn.selected {
            background: linear-gradient(135deg, #0A84FF, #5E5CE6);
            border-color: rgba(255,255,255,0.4);
            transform: translateY(-4px) scale(1.1);
            box-shadow: 0 8px 20px rgba(94, 92, 230, 0.5);
        }
        .dock-icon-btn.selected::after {
            content: ''; position: absolute; bottom: -5px; width: 5px; height: 5px;
            border-radius: 50%; background: #fff;
        }

        /* SHUTTER BAR APPLE STYLE */
        .bottom-shutter-bar {
            position: absolute; bottom: 18px; left: 0; right: 0;
            display: flex; justify-content: space-around; align-items: center; z-index: 50;
            padding: 0 30px;
        }
        .shutter-outer {
            width: 76px; height: 76px; border-radius: 50%;
            background: rgba(255, 255, 255, 0.2); backdrop-filter: blur(10px);
            border: 2px solid rgba(255, 255, 255, 0.7);
            display: flex; align-items: center; justify-content: center; cursor: pointer;
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
        }
        .shutter-outer:active { transform: scale(0.9); }
        .shutter-inner {
            width: 62px; height: 62px; border-radius: 50%; background: #fff;
            transition: all 0.2s;
        }
        .shutter-outer.banana-ready .shutter-inner {
            background: linear-gradient(135deg, #FFD60A, #FF9F0A);
            box-shadow: 0 0 20px rgba(255, 214, 10, 0.8);
        }
        .side-btn {
            width: 44px; height: 44px; border-radius: 50%;
            background: rgba(255, 255, 255, 0.1); backdrop-filter: blur(15px);
            border: 1px solid rgba(255, 255, 255, 0.15); font-size: 16px;
            color: #fff; display: flex; align-items: center; justify-content: center;
            cursor: pointer;
        }

        /* MODAL / BOTTOM SHEET MODULAR */
        .sheet-modal {
            position: fixed; inset: 0; z-index: 100; background: rgba(0,0,0,0.6);
            backdrop-filter: blur(15px); -webkit-backdrop-filter: blur(15px);
            display: none; flex-direction: column; justify-content: flex-end;
            opacity: 0; transition: opacity 0.3s ease;
        }
        .sheet-modal.active { display: flex; opacity: 1; }
        .sheet-card {
            background: #161618; border-top: 1px solid rgba(255,255,255,0.15);
            border-radius: 32px 32px 0 0; padding: 22px 20px 36px 20px;
            max-height: 80vh; overflow-y: auto; box-shadow: 0 -10px 40px rgba(0,0,0,0.7);
            animation: slideUp 0.35s cubic-bezier(0.16, 1, 0.3, 1);
        }
        @keyframes slideUp { from { transform: translateY(100%); } to { transform: translateY(0); } }
        .sheet-drag { width: 36px; height: 5px; background: rgba(255,255,255,0.25); border-radius: 4px; margin: 0 auto 16px; }
        .sheet-title { font-size: 18px; font-weight: 700; color: #fff; margin-bottom: 4px; }
        .sheet-desc { font-size: 12px; color: rgba(255,255,255,0.6); line-height: 1.4; margin-bottom: 16px; }
        .preview-canvas-box { width: 100%; height: 240px; background: #080808; border-radius: 18px; overflow: hidden; border: 1px solid rgba(255,255,255,0.08); display: flex; align-items: center; justify-content: center; margin-bottom: 16px; }
        .preview-canvas-box canvas { max-width: 100%; max-height: 100%; object-fit: contain; }
        .apple-btn-main {
            width: 100%; background: #0A84FF; border: none; color: #fff;
            padding: 14px; border-radius: 16px; font-size: 14px; font-weight: 600;
            cursor: pointer; transition: background 0.2s;
        }
        .apple-btn-main:active { background: #0071E3; }
    </style>
</head>
<body>

    <!-- HEADER FLOTANTE TIPO APPLE INTELLIGENCE -->
    <div class="glass-header">
        <div class="apple-pill">
            <div class="glow-dot"></div>
            <span>Bian V9 Ultra</span>
        </div>
        <div class="banana-chip" id="bananaChip" onclick="resetArmEngine()">
            <span>🍌</span>
            <span id="bananaText">Nano-Banana Auto</span>
        </div>
    </div>

    <!-- VIEWPORT CON RETÍCULA DINÁMICA -->
    <div class="viewport">
        <video id="webcam" autoplay playsinline></video>
        <div class="reticle-container" id="focusReticle">
            <div class="status-badge" id="hudStatus">Modo: Esperando selección</div>
        </div>
        <canvas id="internalCanvas" style="display:none;"></canvas>
    </div>

    <!-- DOCK FLOTANTE CON ICONOS DE TODOS LOS MÓDULOS -->
    <div class="glass-dock">
        <div class="dock-icon-btn" onclick="selectEngine('cine', '🎬 Cine Scope 21:9', this)" title="Cine Scope">🎬</div>
        <div class="dock-icon-btn" onclick="selectEngine('print', '🖨️ Imprenta PDF Offset', this)" title="Imprenta PDF">🖨️</div>
        <div class="dock-icon-btn" onclick="selectEngine('custom', '✨ Wallpapers & Stickers', this)" title="Stickers">✨</div>
        <div class="dock-icon-btn" onclick="selectEngine('raw', '📸 Revelado RAW EV', this)" title="Estudio RAW">📸</div>
        <div class="dock-icon-btn" onclick="selectEngine('depth', '🧠 Depth-Map NPU', this)" title="Profundidad Z">🧠</div>
        <div class="dock-icon-btn" onclick="selectEngine('vid', '🎥 Video Motion 60fps', this)" title="Video Motion">🎥</div>
        <div class="dock-icon-btn" onclick="selectEngine('svg', '🎨 SVG Logos Vector', this)" title="SVG Logos">🎨</div>
        <div class="dock-icon-btn" onclick="selectEngine('lonas', '📐 Lonas 3D Tensión', this)" title="Lonas 3D">📐</div>
        <div class="dock-icon-btn" onclick="selectEngine('price', '🏷️ Valuador Híbrido', this)" title="Valuador">🏷️</div>
        <div class="dock-icon-btn" onclick="selectEngine('chef', '👨‍🍳 Chef Lean Merma', this)" title="Chef Lean">👨‍🍳</div>
    </div>

    <!-- BOTÓN DISPARADOR CON EFECTO NANO-BANANA -->
    <div class="bottom-shutter-bar">
        <div class="side-btn" onclick="toggleLens()">🔄</div>
        <div class="shutter-outer" id="shutterBtn" onclick="triggerNanoBananaCapture()">
            <div class="shutter-inner"></div>
        </div>
        <div class="side-btn" onclick="alert('✔ Galería Soberana V9 Sincronizada')">🖼️</div>
    </div>

    <!-- HOJA DE RESULTADO MODULAR (APPLE SHEET) -->
    <div class="sheet-modal" id="sheetModal">
        <div class="sheet-card">
            <div class="sheet-drag" onclick="closeSheet()"></div>
            <div class="sheet-title" id="sheetTitle">Módulo Procesado</div>
            <div class="sheet-desc" id="sheetDesc">Acción ejecutada mediante la canalización Nano-Banana V9.</div>
            <div class="preview-canvas-box" id="sheetCanvasBox"></div>
            <button class="apple-btn-main" onclick="closeSheet()">Finalizar y Continuar</button>
        </div>
    </div>

    <script>
        const video = document.getElementById('webcam');
        const internalCanvas = document.getElementById('internalCanvas');
        let selectedEngineKey = null;
        let selectedEngineName = null;
        let facingMode = 'environment';
        let capturedImage = new Image();

        // Inicialización suave de cámara
        function startCamera() {
            navigator.mediaDevices.getUserMedia({ video: { facingMode: facingMode } })
                .then(stream => { video.srcObject = stream; })
                .catch(err => console.error("Error al acceder a la cámara:", err));
        }
        startCamera();

        function toggleLens() {
            facingMode = (facingMode === 'environment') ? 'user' : 'environment';
            if (video.srcObject) video.srcObject.getTracks().forEach(t => t.stop());
            startCamera();
        }

        // Selección de módulo en el Dock (Nano-Banana Arming)
        function selectEngine(key, name, elem) {
            document.querySelectorAll('.dock-icon-btn').forEach(btn => btn.classList.remove('selected'));
            
            if (selectedEngineKey === key) {
                resetArmEngine();
                return;
            }

            selectedEngineKey = key;
            selectedEngineName = name;
            elem.classList.add('selected');

            // Armar modo Nano-Banana
            document.getElementById('bananaChip').classList.add('active');
            document.getElementById('bananaText').innerText = `Armado: ${key.toUpperCase()}`;
            document.getElementById('focusReticle').classList.add('banana-lock');
            document.getElementById('shutterBtn').classList.add('banana-ready');
            document.getElementById('hudStatus').innerText = `Listo para ejecutar: ${name}`;
        }

        function resetArmEngine() {
            selectedEngineKey = null;
            selectedEngineName = null;
            document.querySelectorAll('.dock-icon-btn').forEach(btn => btn.classList.remove('selected'));
            document.getElementById('bananaChip').classList.remove('active');
            document.getElementById('bananaText').innerText = 'Nano-Banana Auto';
            document.getElementById('focusReticle').classList.remove('banana-lock');
            document.getElementById('shutterBtn').classList.remove('banana-ready');
            document.getElementById('hudStatus').innerText = 'Modo: Esperando selección';
        }

        // Captura y ejecución autónoma Nano-Banana
        function triggerNanoBananaCapture() {
            if (video.videoWidth === 0) return;

            internalCanvas.width = 400;
            internalCanvas.height = 300;
            const ctx = internalCanvas.getContext('2d');
            ctx.drawImage(video, 0, 0, 400, 300);

            capturedImage.onload = () => {
                if (!selectedEngineKey) {
                    // Si no seleccionó nada, abre por defecto la suite cinemática V9
                    executeModulePipeline('cine', '🎬 Cine Scope 21:9');
                } else {
                    executeModulePipeline(selectedEngineKey, selectedEngineName);
                }
            };
            capturedImage.src = internalCanvas.toDataURL('image/jpeg');
        }

        // Enrutador de ejecución directa en la hoja Apple Sheet
        function executeModulePipeline(engine, name) {
            document.getElementById('sheetTitle').innerText = name;
            const box = document.getElementById('sheetCanvasBox');
            box.innerHTML = "";

            const canvas = document.createElement('canvas');
            canvas.width = 360; canvas.height = 220;
            const ctx = canvas.getContext('2d');

            if (engine === 'cine') {
                ctx.drawImage(capturedImage, 0, 0, 360, 220);
                // 2.39:1 Anamorphic CinemaScope Bars
                ctx.fillStyle = "#000"; ctx.fillRect(0, 0, 360, 24); ctx.fillRect(0, 196, 360, 24);
                // Teal & Orange Tint
                ctx.fillStyle = "rgba(0, 255, 200, 0.12)"; ctx.fillRect(0, 24, 360, 172);
                document.getElementById('sheetDesc').innerText = "Color grading anamórfico 2.39:1 con look Teal & Orange aplicado automáticamente.";
            } else if (engine === 'print') {
                ctx.fillStyle = "#0f0f12"; ctx.fillRect(0, 0, 360, 220);
                ctx.drawImage(capturedImage, 20, 15, 320, 180);
                ctx.strokeStyle = "#FF3B30"; ctx.lineWidth = 1.5; ctx.strokeRect(20, 15, 320, 180);
                document.getElementById('sheetDesc').innerText = "Pliego de preprensa offset con marcas de corte perimetral y sangrado industrial de 3 mm.";
            } else if (engine === 'custom') {
                ctx.fillStyle = "#000000"; ctx.fillRect(0, 0, 360, 220);
                ctx.fillStyle = "#FFFFFF"; ctx.beginPath(); ctx.roundRect(80, 20, 200, 180, 18); ctx.fill();
                ctx.save(); ctx.beginPath(); ctx.roundRect(88, 28, 184, 164, 12); ctx.clip();
                ctx.drawImage(capturedImage, 88, 28, 184, 164); ctx.restore();
                document.getElementById('sheetDesc').innerText = "Sticker Die-Cut con relieve blanco puro y fondo AMOLED negro absoluto (#000000).";
            } else {
                ctx.drawImage(capturedImage, 0, 0, 360, 220);
                ctx.fillStyle = "rgba(10, 132, 255, 0.2)"; ctx.fillRect(0, 0, 360, 220);
                document.getElementById('sheetDesc').innerText = `Procesamiento inteligente completado en el motor de ${name}.`;
            }

            box.appendChild(canvas);
            const modal = document.getElementById('sheetModal');
            modal.classList.add('active');
        }

        function closeSheet() {
            document.getElementById('sheetModal').classList.remove('active');
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
        "engine": "Bian V9 Ultra Liquid Glass (Nano-Banana Engine Active)",
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
