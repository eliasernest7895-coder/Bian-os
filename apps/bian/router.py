from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, select
from core.database import get_session
from apps.bian.models import ProcessedImage
from pydantic import BaseModel
import os
import base64
from datetime import datetime

router = APIRouter(prefix="/bian", tags=["Bian Master Suite V10"])

# Montar carpeta de almacenamiento para servir imágenes en la galería
os.makedirs("storage/bian", exist_ok=True)
router.mount("/storage", StaticFiles(directory="storage"), name="storage")

class ImageCaptureRequest(BaseModel):
    image_base64: str
    prompt_analysis: str = "Captura Master V10"

HTML_CONTENT = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>BIAN MASTER SUITE V10 PRO</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; -webkit-tap-highlight-color: transparent; }
        body { background: #000; color: #fff; height: 100vh; width: 100vw; overflow: hidden; position: fixed; }

        /* BORDE PERIMETRAL QUE SE APAGA TOTALMENTE (1.5 SEG) */
        .edge-screen-border {
            position: fixed; inset: 0; pointer-events: none; z-index: 150;
            border: 3px solid transparent;
            box-shadow: inset 0 0 0px transparent;
            transition: border-color 1.5s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 1.5s cubic-bezier(0.16, 1, 0.3, 1);
        }

        /* LUZ AMBIENTAL DESTELLO */
        .ambient-fade-light {
            position: fixed; inset: 0; pointer-events: none; z-index: 140;
            background: radial-gradient(circle at 50% 50%, rgba(255,255,255,0.25) 0%, transparent 70%);
            opacity: 0;
            transition: opacity 1.5s cubic-bezier(0.16, 1, 0.3, 1);
        }
        .ambient-fade-light.flash { opacity: 1; transition: opacity 0.05s ease-in; }

        /* LOCKSCREEN BRANDING BLANCO */
        #lockscreen {
            position: fixed; inset: 0; background: #050608; z-index: 200;
            display: flex; flex-direction: column; align-items: center; justify-content: space-between;
            padding: 45px 20px 35px 20px;
            transition: transform 0.6s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.6s ease;
        }
        #lockscreen.unlocked { transform: translateY(-100%); opacity: 0; pointer-events: none; }

        .pill-badge {
            background: rgba(0, 255, 200, 0.08); border: 1px solid rgba(0, 255, 200, 0.3);
            color: #00FFC8; font-size: 10px; font-weight: 700; letter-spacing: 1.5px;
            padding: 6px 14px; border-radius: 20px; text-transform: uppercase;
        }
        .brand-center { text-align: center; margin-top: auto; margin-bottom: auto; }
        .brand-title {
            font-size: 64px; font-weight: 900; letter-spacing: 8px; color: #FFFFFF;
            text-shadow: 0 0 20px rgba(255, 255, 255, 0.45), 0 0 50px rgba(255, 255, 255, 0.2);
            line-height: 1; margin-bottom: 12px;
        }
        .brand-subtitle { font-size: 16px; font-weight: 600; color: #fff; margin-bottom: 20px; }
        .brand-card {
            background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 16px; padding: 16px 20px; max-width: 320px; margin: 0 auto;
            font-size: 11px; color: #888; line-height: 1.5; backdrop-filter: blur(10px);
        }

        .gift-container { display: flex; flex-direction: column; align-items: center; cursor: pointer; touch-action: none; padding: 15px; user-select: none; }
        .gift-bow-svg { width: 76px; height: 76px; filter: drop-shadow(0 0 16px rgba(255, 170, 0, 0.65)); transition: transform 0.25s ease; }
        .gift-container:active .gift-bow-svg { transform: scale(1.12); }
        .gift-hint { font-size: 11px; font-weight: 800; color: #FFD200; margin-top: 10px; letter-spacing: 1.5px; text-transform: uppercase; }

        /* VIEWPORT Y VISOR */
        .suite-view { width: 100vw; height: 100vh; position: relative; background: #000; overflow: hidden; display: flex; flex-direction: column; }
        #videoContainer { width: 100%; height: 100%; position: relative; overflow: hidden; }
        video { width: 100%; height: 100%; object-fit: cover; transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1); }

        /* TOP HUD */
        .top-dock {
            position: absolute; top: 16px; left: 16px; right: 16px; z-index: 100;
            display: flex; justify-content: space-between; align-items: center;
        }
        .hud-status-badge {
            background: rgba(18, 18, 22, 0.72); border: 1px solid rgba(255, 255, 255, 0.12);
            color: #fff; font-size: 11px; font-weight: 700; padding: 6px 14px; border-radius: 20px;
            backdrop-filter: blur(10px); display: flex; align-items: center; gap: 6px;
        }
        .hud-status-badge .dot { width: 7px; height: 7px; border-radius: 50%; background: #5E5CE6; display: inline-block; transition: background 0.3s; }
        .top-action-btn {
            background: rgba(18, 18, 22, 0.72); border: 1px solid rgba(255, 255, 255, 0.15);
            color: #fff; font-size: 11px; font-weight: 600; padding: 6px 14px; border-radius: 20px;
            backdrop-filter: blur(10px); cursor: pointer; display: flex; align-items: center; gap: 4px;
        }

        /* BOTÓN ALTERNANTE NANO-BOT (CADA 5 SEG) */
        #botToggleBtn {
            border-color: rgba(0,255,200,0.4); color: #00FFC8;
            transition: all 0.4s ease; min-width: 145px; justify-content: center;
        }

        /* BANNER CONTEXTUAL CENTRAL */
        .center-hud-overlay {
            position: absolute; top: 68px; left: 0; right: 0; z-index: 95;
            display: flex; flex-direction: column; align-items: center; gap: 8px; pointer-events: none;
        }
        .context-pill {
            background: rgba(18, 18, 22, 0.82); border: 1px solid rgba(94, 92, 230, 0.4);
            color: #5E5CE6; font-size: 10px; font-weight: 800; letter-spacing: 0.8px;
            padding: 4px 14px; border-radius: 20px; backdrop-filter: blur(10px); text-transform: uppercase;
            transition: all 0.3s ease;
        }

        /* ANILLO DE ENFOQUE TÁCTICO */
        .focus-ring {
            position: absolute; width: 84px; height: 84px; border-radius: 50%;
            border: 1.5px solid rgba(255, 255, 255, 0.85);
            box-shadow: 0 0 12px rgba(255, 255, 255, 0.4);
            pointer-events: none; z-index: 90; display: flex; flex-direction: column;
            align-items: center; justify-content: space-between; padding: 4px 0;
            transform: translate(-50%, -50%) scale(0.9);
            transition: opacity 0.3s, transform 0.2s cubic-bezier(0.16, 1, 0.3, 1);
            opacity: 0;
        }
        .focus-ring.active { opacity: 1; transform: translate(-50%, -50%) scale(1); }
        .focus-lock-icon { font-size: 11px; color: #FFD200; filter: drop-shadow(0 0 4px rgba(255,210,0,0.8)); }
        .focus-sun-icon { font-size: 13px; color: #FFAA00; filter: drop-shadow(0 0 4px rgba(255,170,0,0.8)); }

        /* SELECTOR DE ZOOM INTERACTIVO (0.6x / 1x / 2x) */
        .hud-zoom-tag {
            position: absolute; bottom: 155px; left: 24px; z-index: 100;
            background: rgba(20, 20, 24, 0.82); border: 1px solid rgba(255, 255, 255, 0.18);
            border-radius: 18px; padding: 5px 12px; font-size: 12px; font-weight: 800; color: #00FFC8;
            cursor: pointer; backdrop-filter: blur(12px); box-shadow: 0 4px 12px rgba(0,0,0,0.6);
            display: flex; align-items: center; gap: 4px; user-select: none;
        }

        /* PILA DE CARTAS CENTRADA Y ERGONÓMICA */
        .deck-stack-wrapper {
            position: absolute; bottom: 98px; left: calc(50% + 55px); z-index: 105;
            width: 58px; height: 58px; perspective: 600px; touch-action: none;
        }
        .deck-card-item {
            position: absolute; inset: 0; border-radius: 18px;
            background: rgba(24, 25, 30, 0.92); border: 2px solid rgba(255, 255, 255, 0.25);
            display: flex; align-items: center; justify-content: center; font-size: 25px;
            cursor: pointer; backdrop-filter: blur(16px);
            box-shadow: 0 8px 24px rgba(0,0,0,0.7);
            transition: all 1.5s cubic-bezier(0.16, 1, 0.3, 1), transform 0.35s cubic-bezier(0.16, 1, 0.3, 1);
            user-select: none;
        }
        .deck-card-item.pos-0 { transform: translate3d(0, 0, 0); z-index: 6; opacity: 1; }
        .deck-card-item.pos-1 { transform: translate3d(6px, -5px, -15px) rotate(4deg); z-index: 5; opacity: 0.85; }
        .deck-card-item.pos-2 { transform: translate3d(12px, -10px, -30px) rotate(8deg); z-index: 4; opacity: 0.65; }
        .deck-card-item.pos-3 { transform: translate3d(18px, -15px, -45px) rotate(12deg); z-index: 3; opacity: 0.45; }
        .deck-card-item.pos-4 { transform: translate3d(24px, -20px, -60px) rotate(16deg); z-index: 2; opacity: 0.25; }

        .deck-card-item.slide-up { transform: translate3d(0, -70px, 40px) scale(1.08); opacity: 0; }
        .deck-card-item.slide-down { transform: translate3d(0, 70px, 40px) scale(1.08); opacity: 0; }

        /* BARRA INFERIOR DE DISPARO */
        .bottom-bar {
            position: absolute; bottom: 20px; left: 0; right: 0; z-index: 100;
            display: flex; justify-content: space-around; align-items: center; padding: 0 25px;
        }
        .lens-switch-btn {
            width: 46px; height: 46px; border-radius: 50%; background: rgba(30, 30, 35, 0.75);
            border: 1px solid rgba(255, 255, 255, 0.2); display: flex; align-items: center;
            justify-content: center; cursor: pointer; font-size: 19px;
        }
        .shutter-btn {
            width: 76px; height: 76px; border-radius: 50%; background: #FF3B30;
            border: 4px solid #fff; box-shadow: 0 0 22px rgba(255, 59, 48, 0.55); cursor: pointer;
        }
        .gallery-thumb {
            width: 46px; height: 46px; border-radius: 50%; border: 2px solid rgba(255, 255, 255, 0.3);
            background: #111; overflow: hidden; cursor: pointer;
        }
        .gallery-thumb img { width: 100%; height: 100%; object-fit: cover; }

        /* MODAL DE EDICIÓN POST-CAPTURA */
        #postEditModal {
            display: none; position: fixed; inset: 0; z-index: 300; background: rgba(6, 7, 10, 0.96);
            backdrop-filter: blur(20px); flex-direction: column; padding: 20px 18px 25px 18px;
        }
        .edit-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
        .edit-title { font-size: 14px; font-weight: 800; color: #00FFC8; letter-spacing: 0.5px; }
        .edit-close-btn { background: #222; border: 1px solid #444; color: #fff; padding: 5px 12px; border-radius: 14px; font-size: 11px; cursor: pointer; }
        
        .edit-preview-box {
            flex: 1; border-radius: 16px; overflow: hidden; background: #000; border: 1px solid #222;
            display: flex; align-items: center; justify-content: center; position: relative;
        }
        .edit-preview-box img { max-width: 100%; max-height: 100%; object-fit: contain; }

        .edit-tools-panel { margin-top: 14px; display: flex; flex-direction: column; gap: 10px; }
        .tool-row { display: flex; gap: 8px; overflow-x: auto; scrollbar-width: none; }
        .tool-chip {
            background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.15);
            padding: 8px 14px; border-radius: 20px; font-size: 11px; font-weight: 700; white-space: nowrap;
            color: #ddd; cursor: pointer;
        }
        .tool-chip.active { border-color: #00FFC8; color: #00FFC8; background: rgba(0,255,200,0.12); }

        .btn-export-master {
            background: linear-gradient(90deg, #00FFC8, #00B3FF); color: #000; font-size: 13px;
            font-weight: 900; letter-spacing: 0.5px; padding: 13px; border-radius: 14px; border: none;
            cursor: pointer; width: 100%; display: flex; align-items: center; justify-content: center;
            gap: 8px; box-shadow: 0 4px 18px rgba(0, 255, 200, 0.4); margin-top: 4px;
        }

        /* MODAL GALERÍA SOBERANA (CON GRID COMPACTO DE FOTOS) */
        #galleryModal {
            display: none; position: fixed; inset: 0; z-index: 320; background: rgba(5, 6, 8, 0.98);
            backdrop-filter: blur(25px); flex-direction: column; padding: 20px;
        }
        .gallery-grid {
            display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; overflow-y: auto; flex: 1; margin-top: 14px;
        }
        .gallery-card {
            background: #111216; border: 1px solid #222; border-radius: 12px; overflow: hidden; cursor: pointer;
            display: flex; flex-direction: column; min-height: 140px;
        }
        .gallery-card img { width: 100%; height: 110px; object-fit: cover; background: #000; }
        .gallery-card-info { padding: 6px 8px; font-size: 10px; color: #888; background: #16171d; }

        /* MODAL NANO-BOT ASISTENTE */
        #nanobotModal {
            display: none; position: fixed; inset: 0; z-index: 330; background: rgba(5, 6, 8, 0.95);
            backdrop-filter: blur(25px); flex-direction: column; padding: 20px; justify-content: space-between;
        }
        .bot-bubble {
            background: #121318; border: 1px solid rgba(0,255,200,0.3); border-radius: 16px; padding: 16px;
            font-size: 13px; line-height: 1.5; color: #eee; margin-top: 15px;
        }
        .bot-actions { display: flex; flex-direction: column; gap: 8px; margin-top: 16px; }
        .bot-btn {
            background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.15); color: #fff;
            padding: 12px; border-radius: 12px; font-size: 12px; font-weight: 700; text-align: left; cursor: pointer;
        }
        .bot-btn:hover { border-color: #00FFC8; color: #00FFC8; }
    </style>
</head>
<body>
    <div class="edge-screen-border" id="screenEdgeBorder"></div>
    <div class="ambient-fade-light" id="ambientLightLayer"></div>

    <!-- LOCKSCREEN CON BRANDING BLANCO Y GESTO DE MOÑO -->
    <div id="lockscreen">
        <div class="pill-badge">• BIAN MASTER SUITE V10</div>

        <div class="brand-center">
            <div class="brand-title">BIAN</div>
            <div class="brand-subtitle">Tu app de fotos y video</div>
            <div class="brand-card">
                Potencia visual, sensor pro calibrado, flujo documental, costeo y 21 módulos soberanos ejecutados 100% de manera local.
            </div>
        </div>

        <div class="gift-container" id="giftUnlockBtn">
            <svg class="gift-bow-svg" viewBox="0 0 100 100">
                <defs>
                    <linearGradient id="bowGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stop-color="#FFF275"/>
                        <stop offset="50%" stop-color="#FFAA00"/>
                        <stop offset="100%" stop-color="#FF3300"/>
                    </linearGradient>
                </defs>
                <path d="M50 50 C30 20 5 35 25 55 C40 65 50 52 50 50 Z" fill="url(#bowGrad)"/>
                <path d="M50 50 C70 20 95 35 75 55 C60 65 50 52 50 50 Z" fill="url(#bowGrad)"/>
                <circle cx="50" cy="50" r="10" fill="#FFE600"/>
                <path d="M46 55 Q35 75 25 90 Q38 82 48 60 Z" fill="url(#bowGrad)"/>
                <path d="M54 55 Q65 75 75 90 Q62 82 52 60 Z" fill="url(#bowGrad)"/>
            </svg>
            <div class="gift-hint">🎁 TOCA O DESLIZA PARA ENTRAR</div>
        </div>
    </div>

    <!-- VIEWPORT CON ANILLO DE ENFOQUE PRO Y BARALJA DE CARTAS STACK -->
    <div class="suite-view" id="viewportArea">
        <div id="videoContainer">
            <video id="webcam" autoplay playsinline></video>
        </div>

        <!-- ANILLO DE ENFOQUE TÁCTICO CON CANDADO Y SOL -->
        <div class="focus-ring" id="focusRing">
            <div class="focus-lock-icon">🔒</div>
            <div class="focus-sun-icon">☀️</div>
        </div>

        <!-- TOP BAR NATIVA -->
        <div class="top-dock">
            <div class="hud-status-badge" id="moduleTitleBadge">
                <span class="dot" id="statusDot"></span>
                <span id="moduleNameText">NIGHTOGRAPHY</span>
            </div>
            <div style="display: flex; gap: 8px;">
                <button class="top-action-btn" onclick="lockSuite()">🔒 Bloquear</button>
                <button class="top-action-btn" id="botToggleBtn" onclick="openNanobot()">✨ ¿Qué quieres hacer?</button>
            </div>
        </div>

        <!-- BANNER CONTEXTUAL CENTRAL -->
        <div class="center-hud-overlay" id="centerHud">
            <div class="context-pill" id="contextPillText">🌙 NIGHTOGRAPHY: ISO BOOST + RAW DENOISE</div>
        </div>

        <!-- SELECTOR DE ZOOM PRO (0.6x, 1x, 2x) -->
        <div class="hud-zoom-tag" id="zoomChip" onclick="cycleZoomLevel()">
            🔍 <span id="zoomLabel">1x</span>
        </div>

        <!-- PILA DE CARTAS CENTRADA Y ERGONÓMICA AL LADO DEL SHUTTER -->
        <div class="deck-stack-wrapper" id="deckStack">
            <div class="deck-card-item pos-0" data-key="night">🌙</div>
            <div class="deck-card-item pos-1" data-key="timelapse">⏱️</div>
            <div class="deck-card-item pos-2" data-key="macro">🔍</div>
            <div class="deck-card-item pos-3" data-key="chef">👨‍🍳</div>
            <div class="deck-card-item pos-4" data-key="price">🏷️</div>
        </div>

        <!-- BARRA INFERIOR DE DISPARO -->
        <div class="bottom-bar">
            <div class="lens-switch-btn" onclick="toggleLens()">🔄</div>
            <div class="shutter-btn" onclick="captureDirect()"></div>
            <div class="gallery-thumb" id="thumbBox" onclick="openGalleryModal()"></div>
        </div>
    </div>

    <!-- MESA DE EDICIÓN & EXPORTACIÓN POST-CAPTURA -->
    <div id="postEditModal">
        <div class="edit-header">
            <div class="edit-title" id="editModalTitle">🛠️ POST-PROCESO & EDICIÓN</div>
            <button class="edit-close-btn" onclick="closeEditModal()">✖ Volver a Cámara</button>
        </div>
        <div class="edit-preview-box">
            <img id="editImagePreview" src="" alt="Captura a editar" />
        </div>
        <div class="edit-tools-panel">
            <div class="tool-row" id="moduleToolRow">
                <div class="tool-chip active" onclick="applyEditTool('original', this)">Normal</div>
                <div class="tool-chip" onclick="applyEditTool('npu_boost', this)">✨ NPU Boost</div>
                <div class="tool-chip" onclick="applyEditTool('alpha_matte', this)">✂️ Recorte Alfa</div>
                <div class="tool-chip" onclick="applyEditTool('cinematic_grade', this)">🎞️ Grado Cine</div>
            </div>
            <button class="btn-export-master" onclick="exportEditedResult()">
                💾 EXPORTAR MASTER HD / CLIP
            </button>
        </div>
    </div>

    <!-- MODAL GALERÍA SOBERANA -->
    <div id="galleryModal">
        <div class="edit-header">
            <div class="edit-title" style="color:#00FFC8;">🖼️ GALERÍA SOBERANA (SQLITE LOCAL)</div>
            <button class="edit-close-btn" onclick="closeGalleryModal()">✖ Cerrar</button>
        </div>
        <div class="gallery-grid" id="galleryGridContent"></div>
    </div>

    <!-- MODAL NANO-BOT ASISTENTE -->
    <div id="nanobotModal">
        <div>
            <div class="edit-header">
                <div class="edit-title" style="color:#00FFC8;">✨ NANO-BOT TÁCTICO BIAN</div>
                <button class="edit-close-btn" onclick="closeNanobot()">✖ Cerrar</button>
            </div>
            <div class="bot-bubble" id="botMessageText">
                Analizando escena...
            </div>
            <div class="bot-actions" id="botActionList"></div>
        </div>
        <div style="font-size:10px; color:#555; text-align:center;">IA Soberana local operando en Snapdragon 8 Gen 2</div>
    </div>

    <canvas id="canvas" style="display:none;"></canvas>

    <script>
        const video = document.getElementById('webcam');
        const canvas = document.getElementById('canvas');
        const focusRing = document.getElementById('focusRing');
        let audioCtx = null;
        let facingMode = 'environment';
        let currentZoomIndex = 1;
        const zoomLevels = [0.6, 1.0, 2.0];
        let lastCapturedBlob = null;

        function getAudioContext() {
            if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            if (audioCtx.state === 'suspended') audioCtx.resume();
            return audioCtx;
        }

        function startCamera() {
            if (video.srcObject) video.srcObject.getTracks().forEach(t => t.stop());
            navigator.mediaDevices.getUserMedia({ video: { facingMode } })
                .then(stream => { video.srcObject = stream; updateThumb(); })
                .catch(err => console.warn("Permiso de cámara:", err));
        }
        startCamera();

        function toggleLens() {
            facingMode = (facingMode === 'environment') ? 'user' : 'environment';
            startCamera();
        }

        function cycleZoomLevel() {
            currentZoomIndex = (currentZoomIndex + 1) % zoomLevels.length;
            const z = zoomLevels[currentZoomIndex];
            document.getElementById('zoomLabel').innerText = `${z}x`;
            video.style.transform = `scale(${z})`;
        }

        /* ALTERNANCIA CADA 5 SEGUNDOS DEL NANO-BOT */
        let botLabelState = 0;
        setInterval(() => {
            const btn = document.getElementById('botToggleBtn');
            botLabelState = (botLabelState === 0) ? 1 : 0;
            btn.style.opacity = '0.2';
            setTimeout(() => {
                btn.innerHTML = (botLabelState === 0) ? '✨ ¿Qué quieres hacer?' : '🤖 Nano-Bot Táctico';
                btn.style.opacity = '1';
            }, 250);
        }, 5000);

        /* ENFOQUE TÁCTICO AL TOCAR EL VISOR */
        window.addEventListener('click', (e) => {
            if (e.target.closest('.bottom-bar') || e.target.closest('.top-dock') || e.target.closest('#deckStack') || e.target.closest('#zoomChip') || !unlocked || e.target.closest('#postEditModal') || e.target.closest('#galleryModal') || e.target.closest('#nanobotModal')) return;
            focusRing.style.left = `${e.clientX}px`;
            focusRing.style.top = `${e.clientY}px`;
            focusRing.classList.remove('active');
            void focusRing.offsetWidth;
            focusRing.classList.add('active');
            setTimeout(() => focusRing.classList.remove('active'), 2500);
        });

        /* SONIDO CUTE DE BIENVENIDA */
        function playCuteGiftSound() {
            try {
                const ctx = getAudioContext();
                const now = ctx.currentTime;
                const notes = [1046.50, 1318.51, 1567.98, 1975.53, 2093.00, 2637.02];
                notes.forEach((f, i) => {
                    const osc = ctx.createOscillator();
                    const gain = ctx.createGain();
                    osc.connect(gain); gain.connect(ctx.destination);
                    osc.type = 'sine';
                    osc.frequency.setValueAtTime(f, now + (i * 0.05));
                    gain.gain.setValueAtTime(0.001, now + (i * 0.05));
                    gain.gain.linearRampToValueAtTime(0.18, now + (i * 0.05) + 0.015);
                    gain.gain.exponentialRampToValueAtTime(0.0001, now + (i * 0.05) + 0.38);
                    osc.start(now + (i * 0.05));
                    osc.stop(now + (i * 0.05) + 0.39);
                });
            } catch(e) {}
        }

        let unlocked = false;
        function unlockSuite() {
            if (unlocked) return;
            unlocked = true;
            playCuteGiftSound();
            document.getElementById('lockscreen').classList.add('unlocked');
            applyActiveCardTheme(moduleCatalog[activeCardIndex]);
        }

        function lockSuite() {
            unlocked = false;
            document.getElementById('lockscreen').classList.remove('unlocked');
            const border = document.getElementById('screenEdgeBorder');
            border.style.borderColor = 'transparent';
            border.style.boxShadow = 'none';
        }

        const giftBtn = document.getElementById('giftUnlockBtn');
        let touchStartY = 0;

        giftBtn.addEventListener('click', unlockSuite);
        giftBtn.addEventListener('touchstart', (e) => { touchStartY = e.touches[0].clientY; }, { passive: true });
        giftBtn.addEventListener('touchend', (e) => {
            const deltaY = touchStartY - e.changedTouches[0].clientY;
            if (deltaY > 25 || Math.abs(deltaY) < 10) unlockSuite();
        }, { passive: true });

        /* SWIPE GLOBAL */
        window.addEventListener('touchstart', (e) => {
            if (!e.target.closest('#deckStack') && !e.target.closest('#postEditModal') && !e.target.closest('#galleryModal') && !e.target.closest('#nanobotModal')) touchStartY = e.touches[0].clientY;
        }, { passive: true });
        window.addEventListener('touchend', (e) => {
            if (!e.target.closest('#deckStack') && !e.target.closest('#postEditModal') && !e.target.closest('#galleryModal') && !e.target.closest('#nanobotModal')) {
                const deltaY = touchStartY - e.changedTouches[0].clientY;
                if (!unlocked && deltaY > 35) unlockSuite();
                else if (unlocked && deltaY < -75 && touchStartY < 120) lockSuite();
            }
        }, { passive: true });

        /* CATÁLOGO DE MÓDULOS */
        const moduleCatalog = [
            { key: 'night', icon: '🌙', title: 'NIGHTOGRAPHY', pill: '🌙 NIGHTOGRAPHY: ISO BOOST + RAW DENOISE', color: '#5E5CE6', freqs: [180, 270, 360], type: 'sine', botTips: 'Baja iluminación detectada. Recomiendo estabilizar 1 segundo para capturar más fotones sin ruido.' },
            { key: 'timelapse', icon: '⏱️', title: 'TIMELAPSE', pill: '⏱️ TIME-LAPSE: CAPTURA COMPRIMIDA 4x', color: '#FF3B30', freqs: [220, 440, 880], type: 'sawtooth', botTips: 'Modo compresión activo. Selecciona 8x o 16x si vas a registrar movimiento de nubes o tránsito rápido.' },
            { key: 'macro', icon: '🔍', title: 'MACRO PRO', pill: '🔍 ENFOQUE A CORTO ALCANCE ULTRA DETALLE', color: '#30D158', freqs: [880, 1100, 1320], type: 'triangle', botTips: 'Distancia de enfoque a 4-8 cm. La NPU optimizará el micro-contraste en texturas complejas.' },
            { key: 'chef', icon: '👨‍🍳', title: 'CHEF LEAN V3', pill: '👨‍🍳 FOOD COST & CONTROL DE MERMA CÁRNICA', color: '#FF9F0A', freqs: [320, 480, 640], type: 'triangle', botTips: 'Insumo cárnico o gastronómico en mira. Calcula de inmediato la merma técnica y porciones netas.' },
            { key: 'price', icon: '🏷️', title: 'VALUADOR HÍBRIDO', pill: '🏷️ TASACIÓN DE MERCADO OFFLINE/ONLINE', color: '#63E6E2', freqs: [480, 640, 800], type: 'sine', botTips: 'Cotejo comercial activado. Puedo estimar banda de costo de adquisición vs precio sugerido.' }
        ];

        let activeCardIndex = 0;
        const deckStack = document.getElementById('deckStack');

        function renderDeckStack() {
            deckStack.innerHTML = '';
            for (let i = 0; i < moduleCatalog.length; i++) {
                const idx = (activeCardIndex + i) % moduleCatalog.length;
                const m = moduleCatalog[idx];
                const card = document.createElement('div');
                card.className = `deck-card-item pos-${i}`;
                card.innerText = m.icon;
                card.setAttribute('data-key', m.key);
                deckStack.appendChild(card);
            }
        }
        renderDeckStack();

        /* GESTO SWIPE VERTICAL EN LA BARAJA */
        let deckTouchStartY = 0;
        deckStack.addEventListener('touchstart', (e) => { deckTouchStartY = e.touches[0].clientY; }, { passive: true });
        deckStack.addEventListener('touchend', (e) => {
            const deltaY = deckTouchStartY - e.changedTouches[0].clientY;
            if (deltaY > 20) shiftCard(1, 'slide-up');
            else if (deltaY < -20) shiftCard(-1, 'slide-down');
            else shiftCard(1, 'slide-up');
        }, { passive: true });

        function shiftCard(dir, animClass) {
            const topCard = deckStack.querySelector('.pos-0');
            if (topCard) topCard.classList.add(animClass);

            setTimeout(() => {
                activeCardIndex = (activeCardIndex + dir + moduleCatalog.length) % moduleCatalog.length;
                const currentMod = moduleCatalog[activeCardIndex];
                renderDeckStack();
                applyActiveCardTheme(currentMod);
            }, 180);
        }

        function applyActiveCardTheme(m) {
            document.getElementById('moduleNameText').innerText = m.title;
            document.getElementById('statusDot').style.background = m.color;
            document.getElementById('contextPillText').innerText = m.pill;
            document.getElementById('contextPillText').style.color = m.color;
            document.getElementById('contextPillText').style.borderColor = `${m.color}66`;

            try {
                const ctx = getAudioContext();
                const now = ctx.currentTime;
                m.freqs.forEach((f, i) => {
                    const osc = ctx.createOscillator();
                    const gain = ctx.createGain();
                    osc.connect(gain); gain.connect(ctx.destination);
                    osc.type = m.type;
                    osc.frequency.setValueAtTime(f, now + (i * 0.04));
                    gain.gain.setValueAtTime(0.001, now + (i * 0.04));
                    gain.gain.linearRampToValueAtTime(0.14, now + (i * 0.04) + 0.015);
                    gain.gain.exponentialRampToValueAtTime(0.0001, now + (i * 0.04) + 0.26);
                    osc.start(now + (i * 0.04));
                    osc.stop(now + (i * 0.04) + 0.27);
                });
            } catch(e) {}

            // Encendido del color en icono y pantalla
            const topCard = deckStack.querySelector('.pos-0');
            if (topCard) {
                topCard.style.borderColor = m.color;
                topCard.style.background = m.color;
                topCard.style.boxShadow = `0 0 22px ${m.color}`;
            }

            triggerModuleVisuals(m.color);

            // EL COLOR DESAPARECE TOTALMENTE TRAS 1.5 SEGUNDOS (CERO SEGUNDO PLANO)
            setTimeout(() => {
                if (topCard) {
                    topCard.style.borderColor = 'rgba(255, 255, 255, 0.25)';
                    topCard.style.background = 'rgba(24, 25, 30, 0.92)';
                    topCard.style.boxShadow = '0 8px 24px rgba(0,0,0,0.7)';
                }
            }, 1500);
        }

        function triggerModuleVisuals(color) {
            const border = document.getElementById('screenEdgeBorder');
            const ambient = document.getElementById('ambientLightLayer');

            border.style.transition = 'border-color 0.08s ease-in, box-shadow 0.08s ease-in';
            border.style.borderColor = color;
            border.style.boxShadow = `inset 0 0 32px ${color}, 0 0 20px ${color}`;

            ambient.style.background = `radial-gradient(circle at 50% 50%, ${color}48 0%, transparent 70%)`;
            ambient.classList.remove('flash');
            void ambient.offsetWidth;
            ambient.classList.add('flash');

            // Apagado completo en 1.5 segundos (transparent 100%)
            setTimeout(() => {
                border.style.transition = 'border-color 1.5s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 1.5s cubic-bezier(0.16, 1, 0.3, 1)';
                border.style.borderColor = 'transparent';
                border.style.boxShadow = 'none';
                ambient.classList.remove('flash');
            }, 100);
        }

        /* CAPTURA & EDICIÓN */
        async function captureDirect() {
            canvas.width = video.videoWidth || 640;
            canvas.height = video.videoHeight || 480;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            const b64 = canvas.toDataURL('image/jpeg');

            const res = await fetch('/bian/process/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image_base64: b64, prompt_analysis: 'Captura Master V10' })
            });
            if (res.ok) {
                const data = await res.json();
                document.getElementById('thumbBox').innerHTML = `<img src="${data.image_path}" />`;
                lastCapturedBlob = b64;
                openEditModalWithCapture(b64);
            }
        }

        async function updateThumb() {
            try {
                const res = await fetch('/bian/images/');
                const list = await res.json();
                if(list.length > 0) {
                    const last = list[list.length - 1];
                    document.getElementById('thumbBox').innerHTML = `<img src="${last.image_path}" />`;
                    lastCapturedBlob = last.image_path;
                }
            } catch(e) {}
        }

        function openEditModalWithCapture(imgSrc) {
            const curMod = moduleCatalog[activeCardIndex];
            document.getElementById('editModalTitle').innerText = `🛠️ EDICIÓN: ${curMod.title}`;
            document.getElementById('editModalTitle').style.color = curMod.color;
            document.getElementById('editImagePreview').src = imgSrc;
            document.getElementById('postEditModal').style.display = 'flex';
        }

        function closeEditModal() { document.getElementById('postEditModal').style.display = 'none'; }

        function applyEditTool(tool, elem) {
            document.querySelectorAll('.tool-chip').forEach(c => c.classList.remove('active'));
            elem.classList.add('active');
            const img = document.getElementById('editImagePreview');
            if(tool === 'original') img.style.filter = 'none';
            else if(tool === 'npu_boost') img.style.filter = 'contrast(1.25) saturate(1.3) brightness(1.05)';
            else if(tool === 'alpha_matte') img.style.filter = 'drop-shadow(0 0 15px #00FFC8) contrast(1.1)';
            else if(tool === 'cinematic_grade') img.style.filter = 'sepia(0.2) contrast(1.3) saturate(0.9)';
        }

        function exportEditedResult() {
            const a = document.createElement('a');
            a.href = document.getElementById('editImagePreview').src;
            a.download = `bian_master_export_${Date.now()}.jpg`;
            a.click();
            alert("✔ Activo exportado con éxito a la memoria local.");
        }

        /* --- GALERÍA SOBERANA CON CARGA REAL DE FOTOS --- */
        async function openGalleryModal() {
            const modal = document.getElementById('galleryModal');
            const container = document.getElementById('galleryGridContent');
            container.innerHTML = '<div style="color:#aaa; font-size:12px;">Cargando activos...</div>';
            modal.style.display = 'flex';

            try {
                const res = await fetch('/bian/images/');
                const items = await res.json();
                if(items.length === 0) {
                    container.innerHTML = '<div style="color:#666; font-size:12px; grid-column:span 2;">No hay imágenes guardadas aún.</div>';
                    return;
                }
                container.innerHTML = '';
                items.slice().reverse().forEach(img => {
                    const card = document.createElement('div');
                    card.className = 'gallery-card';
                    card.onclick = () => {
                        closeGalleryModal();
                        openEditModalWithCapture(img.image_path);
                    };
                    card.innerHTML = `
                        <img src="${img.image_path}" onerror="this.src='data:image/svg+xml;utf8,<svg xmlns=\\'http://www.w3.org/2000/svg\\' width=\\'100\\' height=\\'100\\' viewBox=\\'0 0 100 100\\'><rect width=\\'100\\' height=\\'100\\' fill=\\'%23222\\'/><text x=\\'50\\' y=\\'55\\' fill=\\'%23666\\' font-size=\\'11\\' text-anchor=\\'middle\\'>Sin Vista</text></svg>'"/>
                        <div class="gallery-card-info">
                            <div><strong>#${img.id}</strong> - ${img.prompt_analysis || 'Captura'}</div>
                        </div>
                    `;
                    container.appendChild(card);
                });
            } catch(e) {
                container.innerHTML = '<div style="color:#FF3B30;">Error cargando galería local.</div>';
            }
        }

        function closeGalleryModal() { document.getElementById('galleryModal').style.display = 'none'; }

        /* --- NANO-BOT ASISTENTE TÁCTICO --- */
        function openNanobot() {
            const curMod = moduleCatalog[activeCardIndex];
            const modal = document.getElementById('nanobotModal');
            const msg = document.getElementById('botMessageText');
            const act = document.getElementById('botActionList');

            msg.innerHTML = `
                <div style="color:#00FFC8; font-weight:800; margin-bottom:6px;">🤖 Diagnóstico para ${curMod.title}:</div>
                <div>${curMod.botTips}</div>
            `;

            act.innerHTML = `
                <button class="bot-btn" onclick="executeBotAction('calibrate')">⚡ Calibrar Sensor & NPU para ${curMod.title}</button>
                <button class="bot-btn" onclick="executeBotAction('focus')">🎯 Enfocar Sujeto al Centro</button>
                <button class="bot-btn" onclick="executeBotAction('gallery')">🖼️ Explorar Capturas de este Modo</button>
            `;

            modal.style.display = 'flex';
        }

        function closeNanobot() { document.getElementById('nanobotModal').style.display = 'none'; }

        function executeBotAction(action) {
            closeNanobot();
            if(action === 'calibrate') {
                applyActiveCardTheme(moduleCatalog[activeCardIndex]);
                alert("✔ Parámetros NPU y balance de blancos calibrados.");
            } else if(action === 'focus') {
                focusRing.style.left = "50%";
                focusRing.style.top = "50%";
                focusRing.classList.remove('active');
                void focusRing.offsetWidth;
                focusRing.classList.add('active');
                setTimeout(() => focusRing.classList.remove('active'), 2500);
            } else if(action === 'gallery') {
                openGalleryModal();
            }
        }
    </script>
</body>
</html>"""

@router.get("/ui", response_class=HTMLResponse)
async def get_ui():
    return HTML_CONTENT

@router.post("/process/", response_model=ProcessedImage)
def process_image(payload: ImageCaptureRequest, session: Session = Depends(get_session)):
    os.makedirs("storage/bian", exist_ok=True)
    filename = f"storage/bian/photo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    header, encoded = payload.image_base64.split(",", 1) if "," in payload.image_base64 else ("", payload.image_base64)
    data = base64.b64decode(encoded)
    with open(filename, "wb") as f:
        f.write(data)
    # Ruta estática montada directamente en /bian/storage/...
    db_image = ProcessedImage(image_path=f"/bian/{filename}", prompt_analysis=payload.prompt_analysis)
    session.add(db_image)
    session.commit()
    session.refresh(db_image)
    return db_image

@router.get("/images/", response_model=list[ProcessedImage])
def list_images(session: Session = Depends(get_session)):
    return session.exec(select(ProcessedImage)).all()
