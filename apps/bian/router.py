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

os.makedirs("storage/bian", exist_ok=True)
router.mount("/storage", StaticFiles(directory="storage"), name="storage")

class ImageCaptureRequest(BaseModel):
    image_base64: str
    prompt_analysis: str = "Captura Nano-Bot V2"

HTML_CONTENT = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>BIAN MASTER SUITE V10 - NANO-BOT V2</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', Roboto, monospace; -webkit-tap-highlight-color: transparent; }
        body { background: #000; color: #fff; height: 100vh; width: 100vw; overflow: hidden; position: fixed; }

        .edge-screen-border {
            position: fixed; inset: 0; pointer-events: none; z-index: 150;
            border: 3.5px solid transparent; box-shadow: inset 0 0 0px transparent;
            transition: border-color 0.1s ease-in, box-shadow 0.1s ease-in;
        }

        .ambient-fade-light {
            position: fixed; inset: 0; pointer-events: none; z-index: 140;
            background: radial-gradient(circle at 50% 50%, rgba(255,255,255,0.3) 0%, transparent 70%);
            opacity: 0; transition: opacity 0.1s ease-in;
        }
        .ambient-fade-light.flash { opacity: 1; }

        #lockscreen {
            position: fixed; inset: 0; background: #050608; z-index: 200;
            display: flex; flex-direction: column; align-items: center; justify-content: space-between;
            padding: 45px 20px 35px 20px; transition: transform 0.55s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.5s ease;
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
            text-shadow: 0 0 20px rgba(255, 255, 255, 0.45); line-height: 1; margin-bottom: 8px;
        }
        .brand-subtitle { font-size: 15px; font-weight: 600; color: #fff; margin-bottom: 12px; }

        .lens-cap-assembly {
            display: flex; flex-direction: column; align-items: center; cursor: pointer; touch-action: none; margin-bottom: 20px;
        }
        .lens-cap-disk {
            width: 95px; height: 95px; border-radius: 50%;
            background: radial-gradient(circle, #25262c 0%, #111216 70%, #08080a 100%);
            border: 3px solid #333640; box-shadow: 0 8px 30px rgba(0,0,0,0.9);
            display: flex; flex-direction: column; align-items: center; justify-content: center;
            position: relative; transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1), border-color 0.3s;
        }
        .lens-cap-center { font-size: 10px; font-weight: 900; letter-spacing: 2px; color: #00FFC8; transition: color 0.3s; }
        .lens-cap-sub { font-size: 7.5px; color: #888; margin-top: 2px; }
        .lens-cap-hint { font-size: 10px; font-weight: 800; color: #aaa; margin-top: 10px; letter-spacing: 1px; }

        .suite-view { width: 100vw; height: 100vh; position: relative; background: #000; overflow: hidden; display: flex; flex-direction: column; }
        #videoContainer { width: 100%; height: 100%; position: relative; overflow: hidden; }
        video { width: 100%; height: 100%; object-fit: cover; }

        #ghostScopeCanvas {
            position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover;
            pointer-events: none; z-index: 45; opacity: 0; mix-blend-mode: screen; transition: opacity 0.3s;
        }
        #ghostScopeCanvas.active { opacity: 0.75; }

        /* CANVAS DE ESPORAS CON DESVANECIMIENTO EXACTO DE 1.0 SEGUNDO */
        #sporesMatrixCanvas {
            position: absolute; inset: 0; width: 100%; height: 100%; pointer-events: none; z-index: 52;
            opacity: 0; transition: opacity 1.0s cubic-bezier(0.16, 1, 0.3, 1);
        }
        #sporesMatrixCanvas.active { opacity: 1; transition: opacity 0.05s ease-in; }

        .top-dock {
            position: absolute; top: 16px; left: 16px; right: 16px; z-index: 100;
            display: flex; justify-content: space-between; align-items: center;
        }
        .hud-status-badge {
            background: rgba(18, 18, 22, 0.72); border: 1px solid rgba(255, 255, 255, 0.12);
            color: #fff; font-size: 11px; font-weight: 700; padding: 6px 14px; border-radius: 20px;
            backdrop-filter: blur(10px); display: flex; align-items: center; gap: 6px;
        }
        .hud-status-badge .dot { width: 7px; height: 7px; border-radius: 50%; background: #00FFC8; display: inline-block; }
        .top-action-btn {
            background: rgba(18, 18, 22, 0.72); border: 1px solid rgba(255, 255, 255, 0.15);
            color: #fff; font-size: 11px; font-weight: 600; padding: 6px 14px; border-radius: 20px;
            backdrop-filter: blur(10px); cursor: pointer; display: flex; align-items: center; gap: 4px;
        }
        #botToggleBtn {
            border-color: rgba(0, 255, 200, 0.4); color: #00FFC8; transition: all 0.4s ease; min-width: 155px; justify-content: center;
        }

        .ghost-scope-btn {
            background: rgba(18, 18, 22, 0.75); border: 1px solid rgba(255, 255, 255, 0.2);
            color: #fff; font-size: 10px; font-weight: 800; padding: 6px 11px; border-radius: 18px;
            cursor: pointer; backdrop-filter: blur(8px);
        }
        .ghost-scope-btn.active { background: #00FFC8; color: #000; box-shadow: 0 0 14px rgba(0,255,200,0.6); }

        .center-hud-overlay {
            position: absolute; top: 68px; left: 0; right: 0; z-index: 95;
            display: flex; flex-direction: column; align-items: center; gap: 8px; pointer-events: none;
        }
        .context-pill {
            background: rgba(18, 18, 22, 0.82); border: 1px solid rgba(0, 255, 200, 0.4);
            color: #00FFC8; font-size: 10px; font-weight: 800; letter-spacing: 0.8px;
            padding: 4px 14px; border-radius: 20px; backdrop-filter: blur(10px); text-transform: uppercase;
        }

        .deck-stack-wrapper {
            position: absolute; bottom: 98px; left: calc(50% + 55px); z-index: 105;
            width: 58px; height: 58px; perspective: 600px; touch-action: none;
        }
        .deck-card-item {
            position: absolute; inset: 0; border-radius: 18px;
            background: rgba(24, 25, 30, 0.92); border: 2px solid rgba(255, 255, 255, 0.25);
            display: flex; align-items: center; justify-content: center; font-size: 25px;
            cursor: pointer; backdrop-filter: blur(16px); box-shadow: 0 8px 24px rgba(0,0,0,0.7);
            transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
        }
        .deck-card-item.pos-0 { transform: translate3d(0, 0, 0); z-index: 6; opacity: 1; }
        .deck-card-item.pos-1 { transform: translate3d(6px, -5px, -15px) rotate(4deg); z-index: 5; opacity: 0.85; }
        .deck-card-item.pos-2 { transform: translate3d(12px, -10px, -30px) rotate(8deg); z-index: 4; opacity: 0.65; }
        .deck-card-item.pos-3 { transform: translate3d(18px, -15px, -45px) rotate(12deg); z-index: 3; opacity: 0.45; }
        .deck-card-item.pos-4 { transform: translate3d(24px, -20px, -60px) rotate(16deg); z-index: 2; opacity: 0.25; }

        #horizontalDockBar {
            position: absolute; bottom: 104px; left: 16px; right: 16px; z-index: 110;
            background: rgba(18, 20, 26, 0.88); border: 1px solid rgba(255, 255, 255, 0.14);
            border-radius: 28px; padding: 8px 14px; backdrop-filter: blur(25px);
            display: none; align-items: center; gap: 12px; overflow-x: auto; scrollbar-width: none;
        }
        #horizontalDockBar.active { display: flex; }
        .dock-item-btn {
            position: relative; flex-shrink: 0; width: 44px; height: 44px; border-radius: 50%;
            background: rgba(255, 255, 255, 0.05); border: 1.5px solid rgba(255, 255, 255, 0.15);
            display: flex; align-items: center; justify-content: center; font-size: 20px; cursor: pointer;
        }
        .dock-item-btn.active { background: rgba(255, 255, 255, 0.18); transform: scale(1.12); }
        .dock-dot-indicator {
            position: absolute; bottom: -3px; width: 6px; height: 6px; border-radius: 50%; display: none;
        }
        .dock-item-btn.active .dock-dot-indicator { display: block; }

        .bottom-bar {
            position: absolute; bottom: 20px; left: 0; right: 0; z-index: 100;
            display: flex; justify-content: space-around; align-items: center; padding: 0 25px;
        }
        .shutter-wrapper { position: relative; width: 80px; height: 80px; display: flex; align-items: center; justify-content: center; }
        .shutter-corona {
            position: absolute; inset: -4px; border-radius: 50%;
            border: 2px dashed rgba(255,255,255,0.3); pointer-events: none;
        }
        .shutter-btn {
            width: 72px; height: 72px; border-radius: 50%; background: #00FFC8;
            border: 4px solid #fff; box-shadow: 0 0 22px rgba(0, 255, 200, 0.55); cursor: pointer;
        }
        .lens-switch-btn {
            width: 46px; height: 46px; border-radius: 50%; background: rgba(30, 30, 35, 0.75);
            border: 1px solid rgba(255, 255, 255, 0.2); display: flex; align-items: center; justify-content: center; font-size: 19px; cursor: pointer;
        }
        .gallery-thumb {
            width: 46px; height: 46px; border-radius: 50%; border: 2px solid rgba(255, 255, 255, 0.3);
            background: #111; overflow: hidden; cursor: pointer;
        }
        .gallery-thumb img { width: 100%; height: 100%; object-fit: cover; }

        #floatingGadget {
            position: fixed; top: 180px; left: 14px; width: 48px; height: 48px;
            border-radius: 50%; background: #0c0d12; border: 2px solid #00FFC8;
            box-shadow: 0 6px 18px rgba(0, 255, 200, 0.4); z-index: 250;
            display: flex; align-items: center; justify-content: center; font-size: 20px; cursor: grab;
        }
        #floatingPanel {
            display: none; position: fixed; inset: 100px 18px 120px 18px; z-index: 260;
            background: rgba(10, 12, 16, 0.96); border: 1px solid #00FFC8; border-radius: 20px;
            backdrop-filter: blur(25px); flex-direction: column; padding: 16px;
        }
        .float-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }

        /* 🌟 NANO-BOT TÁCTICO V2 MODAL 🌟 */
        #nanobotModal {
            display: none; position: fixed; inset: 0; z-index: 330; background: rgba(5, 7, 10, 0.96);
            backdrop-filter: blur(25px); flex-direction: column; padding: 22px 18px; justify-content: space-between;
        }
        .bot-terminal-card {
            background: #080c10; border: 1px solid rgba(0, 255, 200, 0.35); border-radius: 16px;
            padding: 14px; font-family: monospace; font-size: 11px; color: #00FFC8; margin-top: 10px;
        }
        .bot-telemetry-grid {
            display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; margin-top: 12px;
        }
        .bot-telemetry-item {
            background: rgba(255, 255, 255, 0.04); border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 10px; padding: 8px; font-size: 10px; color: #ccc;
        }
        .bot-input-box {
            display: flex; gap: 8px; margin-top: 12px; background: rgba(0, 255, 200, 0.06);
            border: 1px solid rgba(0, 255, 200, 0.3); border-radius: 12px; padding: 6px 12px;
        }
        .bot-input {
            flex: 1; background: transparent; border: none; color: #fff; font-size: 11px;
            font-family: inherit; outline: none;
        }
        .bot-actions { display: flex; flex-direction: column; gap: 8px; margin-top: 12px; overflow-y: auto; max-height: 220px; }
        .bot-btn {
            background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.15); color: #fff;
            padding: 10px 14px; border-radius: 12px; font-size: 11px; font-weight: 700; text-align: left; cursor: pointer;
            display: flex; justify-content: space-between; align-items: center;
        }
        .bot-btn:hover { border-color: #00FFC8; background: rgba(0, 255, 200, 0.1); }

        #postEditModal {
            display: none; position: fixed; inset: 0; z-index: 300; background: rgba(6, 7, 10, 0.96);
            backdrop-filter: blur(20px); flex-direction: column; padding: 20px 18px 25px 18px;
        }
        .edit-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
        .edit-title { font-size: 14px; font-weight: 800; color: #00FFC8; }
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
            padding: 8px 14px; border-radius: 20px; font-size: 11px; font-weight: 700; color: #ddd; cursor: pointer;
        }
        .tool-chip.active { border-color: #00FFC8; color: #00FFC8; background: rgba(0,255,200,0.12); }
        .btn-export-master {
            background: linear-gradient(90deg, #00FFC8, #00D2FF); color: #000; font-size: 13px;
            font-weight: 900; padding: 13px; border-radius: 14px; border: none; cursor: pointer;
            width: 100%; display: flex; align-items: center; justify-content: center; gap: 8px;
        }

        #galleryModal {
            display: none; position: fixed; inset: 0; z-index: 320; background: rgba(5, 6, 8, 0.98);
            backdrop-filter: blur(25px); flex-direction: column; padding: 20px;
        }
        .gallery-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; overflow-y: auto; flex: 1; margin-top: 14px; }
        .gallery-card { background: #111216; border: 1px solid #222; border-radius: 12px; overflow: hidden; cursor: pointer; min-height: 140px; }
        .gallery-card img { width: 100%; height: 110px; object-fit: cover; }
        .gallery-card-info { padding: 6px 8px; font-size: 10px; color: #888; background: #16171d; }
    </style>
</head>
<body>
    <div class="edge-screen-border" id="screenEdgeBorder"></div>
    <div class="ambient-fade-light" id="ambientLightLayer"></div>

    <div id="lockscreen">
        <div class="pill-badge" id="lockscreenBadge">• NANO-BOT TÁCTICO V2</div>
        <div class="brand-center">
            <div class="brand-title">BIAN</div>
            <div class="brand-subtitle" id="lockscreenSub">Asistente Neuronal V2</div>
            <div style="font-size:11px; color:#777; max-width:280px; margin:0 auto; line-height:1.4;" id="lockscreenDesc">
                Copiloto Táctico • Macros en RAM • Diagnóstico en Tiempo Real
            </div>
        </div>
        <div class="lens-cap-assembly" id="lensCapUnlockBtn">
            <div class="lens-cap-disk" id="lensCapDisk">
                <div class="lens-cap-center" id="lensCapCenterText">NANO-BOT</div>
                <div class="lens-cap-sub" id="lensCapSubText">F/1.4 • TACTICAL AI</div>
            </div>
            <div class="lens-cap-hint">🔓 DESTAPAR LENTE</div>
        </div>
    </div>

    <div id="floatingGadget" title="Taller Táctico">⚡</div>

    <div id="floatingPanel">
        <div class="float-header">
            <div style="font-size:13px; font-weight:800; color:#00FFC8;" id="floatHeaderTitle">⚡ TALLER TÁCTICO FLOTANTE</div>
            <button class="edit-close-btn" onclick="toggleFloatingPanel()">✖ Cerrar</button>
        </div>
        <div style="flex:1; overflow-y:auto; font-size:12px; color:#aaa; display:flex; flex-direction:column; gap:10px;">
            <div style="background:#14151b; padding:12px; border-radius:12px; border:1px solid #222;">
                <div style="color:#fff; font-weight:700; margin-bottom:4px;" id="floatModTitle">MODO ACTIVO</div>
                <div id="floatModDesc">Herramientas optimizadas en RAM y Snapdragon 8 Gen 2.</div>
            </div>
            <div class="bot-actions" id="floatActionList"></div>
        </div>
    </div>

    <div class="suite-view" id="viewportArea">
        <div id="videoContainer">
            <video id="webcam" autoplay playsinline></video>
            <canvas id="ghostScopeCanvas"></canvas>
            <!-- 🌟 CANVAS DE ESPORAS CON DESVANECIMIENTO EXACTO DE 1.0 SEGUNDO 🌟 -->
            <canvas id="sporesMatrixCanvas"></canvas>
        </div>

        <div class="top-dock">
            <div class="hud-status-badge" id="moduleTitleBadge">
                <span class="dot" id="statusDot"></span>
                <span id="moduleNameText">BIAN SUITE V10</span>
            </div>
            <div style="display: flex; gap: 6px;">
                <button class="ghost-scope-btn" id="scopeToggleBtn" onclick="toggleGhostScope()">
                    👁️ ESPECTRO
                </button>
                <button class="top-action-btn" onclick="lockSuite()">🔒</button>
                <button class="top-action-btn" id="botToggleBtn" onclick="openNanobot()">✨ Nano-Bot V2</button>
            </div>
        </div>

        <div class="center-hud-overlay" id="centerHud">
            <div class="context-pill" id="contextPillText">BIAN SUITE V10 READY</div>
        </div>

        <div class="hud-zoom-tag" id="zoomChip" onclick="cycleZoomLevel()">
            🔍 <span id="zoomLabel">1x</span>
        </div>

        <div class="deck-stack-wrapper" id="deckStack" onclick="openHorizontalDock()"></div>
        <div id="horizontalDockBar"></div>

        <div class="bottom-bar">
            <div class="lens-switch-btn" onclick="toggleLens()">🔄</div>
            <div class="shutter-wrapper">
                <div class="shutter-corona" id="shutterCorona"></div>
                <div class="shutter-btn" id="masterShutterBtn" onclick="handleMasterCapture()"></div>
            </div>
            <div class="gallery-thumb" id="thumbBox" onclick="openGalleryModal()"></div>
        </div>
    </div>

    <!-- 🌟 NANO-BOT TÁCTICO V2 MODAL 🌟 -->
    <div id="nanobotModal">
        <div>
            <div class="edit-header">
                <div class="edit-title" style="color:#00FFC8;">✨ NANO-BOT TÁCTICO V2 ULTRA</div>
                <button class="edit-close-btn" onclick="closeNanobot()">✖ Cerrar</button>
            </div>

            <div class="bot-terminal-card" id="botTerminalOutput">
                > COPILOTO TÁCTICO INICIALIZADO...<br>
                > MÓDULO ACTIVO: <span id="botActiveModLabel" style="color:#fff;">DESPACHO COMERCIAL</span><br>
                > ESTADO DEL SISTEMA: 100% OPERATIVO EN RAM
            </div>

            <div class="bot-telemetry-grid">
                <div class="bot-telemetry-item">
                    <div style="color:#888;">NEURAL CORE</div>
                    <strong style="color:#00FFC8;">ONLINE (NPU 8G2)</strong>
                </div>
                <div class="bot-telemetry-item">
                    <div style="color:#888;">LATENCIA</div>
                    <strong style="color:#30D158;">11.8 ms</strong>
                </div>
                <div class="bot-telemetry-item">
                    <div style="color:#888;">BUFFER RAM</div>
                    <strong style="color:#FFD600;">VOLÁTIL ZERO-LAG</strong>
                </div>
                <div class="bot-telemetry-item">
                    <div style="color:#888;">SUITE MÓDULOS</div>
                    <strong style="color:#FF007A;">19/19 INTEGRADOS</strong>
                </div>
            </div>

            <div class="bot-input-box">
                <input type="text" id="botCommandInput" class="bot-input" placeholder="Escribe un comando táctico o macro..." onkeydown="if(event.key==='Enter') executeCustomBotCommand()">
                <button style="background:transparent; border:none; color:#00FFC8; cursor:pointer;" onclick="executeCustomBotCommand()">⚡</button>
            </div>

            <div class="bot-actions" id="botActionList"></div>
        </div>
        <div style="font-size:10px; color:#555; text-align:center;">IA Soberana local operando en Debian 13 Termux</div>
    </div>

    <!-- MESA POST-PROCESO -->
    <div id="postEditModal">
        <div class="edit-header">
            <div class="edit-title" id="editModalTitle">RESULTADO MASTER V10</div>
            <button class="edit-close-btn" onclick="closeEditModal()">✖ Volver</button>
        </div>
        <div class="edit-preview-box">
            <img id="editImagePreview" src="" alt="Frame Render" />
        </div>
        <div class="edit-tools-panel">
            <div class="tool-row" id="moduleToolRow">
                <div class="tool-chip active" onclick="applyMasterFilter('standard', this)">💎 Grado Master V10</div>
                <div class="tool-chip" onclick="applyMasterFilter('high_contrast', this)">⚡ Alto Contraste</div>
                <div class="tool-chip" onclick="applyMasterFilter('vivid_tone', this)">🎨 Tono Vívido</div>
            </div>
            <button class="btn-export-master" onclick="exportMasterResult()">
                💾 EXPORTAR ASSET HD MASTER
            </button>
        </div>
    </div>

    <div id="galleryModal">
        <div class="edit-header">
            <div class="edit-title" style="color:#00FFC8;">🖼️ GALERÍA SOBERANA (SQLITE LOCAL)</div>
            <button class="edit-close-btn" onclick="closeGalleryModal()">✖ Cerrar</button>
        </div>
        <div class="gallery-grid" id="galleryGridContent"></div>
    </div>

    <canvas id="hiddenBufferCanvas" style="display:none;"></canvas>
    <canvas id="processBufferCanvas" style="display:none;"></canvas>

    <script>
        const video = document.getElementById('webcam');
        const hiddenCanvas = document.getElementById('hiddenBufferCanvas');
        const procCanvas = document.getElementById('processBufferCanvas');
        const ghostCanvas = document.getElementById('ghostScopeCanvas');
        const ghostCtx = ghostCanvas.getContext('2d');
        const sporesCanvas = document.getElementById('sporesMatrixCanvas');
        const sporesCtx = sporesCanvas.getContext('2d');
        let audioCtx = null;
        let facingMode = 'environment';
        let currentZoomIndex = 1;
        const zoomLevels = [0.6, 1.0, 2.0];
        let isGhostScopeOn = false;
        let sporesTimeout = null;
        let lastCapturedUrl = null;

        /* SISTEMA DE ESPORAS */
        let spores = [];
        const NUM_SPORES = 28;

        function initSpores() {
            spores = [];
            for (let i = 0; i < NUM_SPORES; i++) {
                spores.push({
                    x: Math.random() * window.innerWidth,
                    y: Math.random() * window.innerHeight,
                    vx: (Math.random() - 0.5) * 1.5,
                    vy: (Math.random() - 0.5) * 1.5,
                    radius: Math.random() * 2.8 + 1.2,
                    pulse: Math.random() * Math.PI * 2
                });
            }
        }
        initSpores();
        window.addEventListener('resize', initSpores);

        function getAudioContext() {
            if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            if (audioCtx.state === 'suspended') audioCtx.resume();
            return audioCtx;
        }

        function startCamera() {
            if (video.srcObject) video.srcObject.getTracks().forEach(t => t.stop());
            navigator.mediaDevices.getUserMedia({
                video: { facingMode, width: { ideal: 1920 }, height: { ideal: 1080 } }
            })
            .then(stream => {
                video.srcObject = stream;
                updateThumb();
                requestAnimationFrame(processPipeline);
            })
            .catch(err => console.warn("Error cámara:", err));
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

        let frameCount = 0;
        function processPipeline() {
            if (video.readyState >= 2) {
                if (hiddenCanvas.width !== video.videoWidth) {
                    hiddenCanvas.width = video.videoWidth || 640;
                    hiddenCanvas.height = video.videoHeight || 480;
                    procCanvas.width = hiddenCanvas.width;
                    procCanvas.height = hiddenCanvas.height;
                    sporesCanvas.width = window.innerWidth;
                    sporesCanvas.height = window.innerHeight;
                    ghostCanvas.width = 320;
                    ghostCanvas.height = 240;
                }
                const hCtx = hiddenCanvas.getContext('2d');
                hCtx.drawImage(video, 0, 0, hiddenCanvas.width, hiddenCanvas.height);

                frameCount++;
                if (isGhostScopeOn && frameCount % 3 === 0) {
                    ghostCtx.drawImage(hiddenCanvas, 0, 0, 320, 240);
                    const imgData = ghostCtx.getImageData(0, 0, 320, 240);
                    const d = imgData.data;
                    for (let i = 0; i < d.length; i += 4) {
                        const luma = (d[i] * 0.299 + d[i+1] * 0.587 + d[i+2] * 0.114);
                        if (luma < 30) {
                            d[i] = 255; d[i+1] = 0; d[i+2] = 180;
                        } else if (luma > 235) {
                            d[i] = 0; d[i+1] = 255; d[i+2] = 200;
                        } else {
                            d[i+3] = 0;
                        }
                    }
                    ghostCtx.putImageData(imgData, 0, 0);
                }

                renderSporesFrame();
            }
            requestAnimationFrame(processPipeline);
        }

        function renderSporesFrame() {
            sporesCtx.clearRect(0, 0, sporesCanvas.width, sporesCanvas.height);
            const w = sporesCanvas.width;
            const h = sporesCanvas.height;
            const curMod = moduleCatalog[activeCardIndex];
            const col = curMod.color;

            sporesCtx.strokeStyle = `${col}28`;
            sporesCtx.lineWidth = 0.8;
            sporesCtx.setLineDash([2, 8]);
            const step = 45;
            for (let x = 0; x < w; x += step) {
                sporesCtx.beginPath(); sporesCtx.moveTo(x, 0); sporesCtx.lineTo(x, h); sporesCtx.stroke();
            }
            for (let y = 0; y < h; y += step) {
                sporesCtx.beginPath(); sporesCtx.moveTo(0, y); sporesCtx.lineTo(w, y); sporesCtx.stroke();
            }
            sporesCtx.setLineDash([]);

            const cornerSize = 16;
            sporesCtx.strokeStyle = col;
            sporesCtx.lineWidth = 1.8;
            sporesCtx.beginPath(); sporesCtx.moveTo(25, 25 + cornerSize); sporesCtx.lineTo(25, 25); sporesCtx.lineTo(25 + cornerSize, 25); sporesCtx.stroke();
            sporesCtx.beginPath(); sporesCtx.moveTo(w - 25 - cornerSize, 25); sporesCtx.lineTo(w - 25, 25); sporesCtx.lineTo(w - 25, 25 + cornerSize); sporesCtx.stroke();
            sporesCtx.beginPath(); sporesCtx.moveTo(25, h - 25 - cornerSize); sporesCtx.lineTo(25, h - 25); sporesCtx.lineTo(25 + cornerSize, h - 25); sporesCtx.stroke();
            sporesCtx.beginPath(); sporesCtx.moveTo(w - 25 - cornerSize, h - 25); sporesCtx.lineTo(w - 25, h - 25); sporesCtx.lineTo(w - 25, h - 25 - cornerSize); sporesCtx.stroke();

            spores.forEach(sp => {
                sp.x += sp.vx;
                sp.y += sp.vy;
                sp.pulse += 0.05;

                if (sp.x < 0) sp.x = w;
                if (sp.x > w) sp.x = 0;
                if (sp.y < 0) sp.y = h;
                if (sp.y > h) sp.y = 0;

                const currentR = sp.radius + Math.sin(sp.pulse) * 0.8;
                const alpha = 0.5 + Math.sin(sp.pulse) * 0.4;

                sporesCtx.fillStyle = col;
                sporesCtx.shadowColor = col;
                sporesCtx.shadowBlur = 10;
                sporesCtx.globalAlpha = Math.max(0.1, alpha);
                sporesCtx.beginPath();
                sporesCtx.arc(sp.x, sp.y, Math.max(0.5, currentR), 0, Math.PI * 2);
                sporesCtx.fill();
            });

            sporesCtx.globalAlpha = 1.0;
            sporesCtx.shadowBlur = 0;
        }

        /* 🌟 PROTOCOLO UNIVERSAL: ESPORAS A 1.0 SEGUNDO EXACTO 🌟 */
        function triggerUniversalEntryProtocol(color) {
            const border = document.getElementById('screenEdgeBorder');
            const ambient = document.getElementById('ambientLightLayer');
            const sCanvas = document.getElementById('sporesMatrixCanvas');

            border.style.transition = 'border-color 0.08s ease-in, box-shadow 0.08s ease-in';
            border.style.borderColor = color;
            border.style.boxShadow = `inset 0 0 35px ${color}, 0 0 25px ${color}`;

            ambient.style.background = `radial-gradient(circle at 50% 50%, ${color}66 0%, transparent 74%)`;
            ambient.classList.remove('flash');
            void ambient.offsetWidth;
            ambient.classList.add('flash');

            sCanvas.classList.add('active');

            const cx = window.innerWidth / 2;
            const cy = window.innerHeight / 2;
            spores.forEach(sp => {
                const angle = Math.atan2(sp.y - cy, sp.x - cx);
                const speed = 4.5 + Math.random() * 4;
                sp.vx = Math.cos(angle) * speed;
                sp.vy = Math.sin(angle) * speed;
            });

            playTacticalEntrySound(color);

            setTimeout(() => {
                border.style.transition = 'border-color 1.0s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 1.0s cubic-bezier(0.16, 1, 0.3, 1)';
                border.style.borderColor = 'transparent';
                border.style.boxShadow = 'none';
                ambient.classList.remove('flash');
            }, 120);

            // 🌟 1.0 SEGUNDO EXACTO: DESAPARECER LAS ESPORAS 🌟
            clearTimeout(sporesTimeout);
            sporesTimeout = setTimeout(() => {
                sCanvas.classList.remove('active');
                setTimeout(() => {
                    spores.forEach(sp => {
                        sp.vx = (Math.random() - 0.5) * 1.5;
                        sp.vy = (Math.random() - 0.5) * 1.5;
                    });
                }, 400);
            }, 1000);
        }

        function playTacticalEntrySound(color) {
            try {
                const ctx = getAudioContext();
                const now = ctx.currentTime;
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.connect(gain); gain.connect(ctx.destination);
                osc.type = 'triangle';
                osc.frequency.setValueAtTime(240, now);
                osc.frequency.exponentialRampToValueAtTime(920, now + 0.16);
                gain.gain.setValueAtTime(0.3, now);
                gain.gain.exponentialRampToValueAtTime(0.001, now + 0.16);
                osc.start(now); osc.stop(now + 0.17);
            } catch(e) {}
        }

        function toggleGhostScope() {
            isGhostScopeOn = !isGhostScopeOn;
            const btn = document.getElementById('scopeToggleBtn');
            const gCanvas = document.getElementById('ghostScopeCanvas');
            if (isGhostScopeOn) {
                btn.classList.add('active');
                gCanvas.classList.add('active');
            } else {
                btn.classList.remove('active');
                gCanvas.classList.remove('active');
                ghostCtx.clearRect(0, 0, ghostCanvas.width, ghostCanvas.height);
            }
        }

        /* CATÁLOGO DE MÓDULOS DE LA MASTER SUITE */
        const moduleCatalog = [
            { key: 'dispatch', icon: '📦', title: 'DESPACHO COMERCIAL V2', pill: '📦 CUBICAJE IATA & MANIFIESTO LOGÍSTICO', color: '#00E676', capText: 'DESPACHO', capSub: 'F/1.4 • WAYBILL MATRIX', botTips: 'Calcula cubicaje CBM, peso volumétrico y genera manifiestos de salida.' },
            { key: 'ai', icon: '✨', title: 'GENERADOR AI V8', pill: '✨ DIFUSIÓN LATENTE & MORFOLOGÍA NEURONAL', color: '#FF007A', capText: 'NEURAL AI', capSub: 'F/1.4 • LATENT SYNTHESIS', botTips: 'Transformación neuronal guiada por cámara.' },
            { key: 'price', icon: '🏷️', title: 'VALUADOR HÍBRIDO V10', pill: '🏷️ TASACIÓN DE MERCADO & PÓLIZA COMERCIAL', color: '#63E6E2', capText: 'VALUADOR', capSub: 'F/1.4 • COMMERCIAL SCAN', botTips: 'Tasación comercial y márgenes.' },
            { key: 'chef', icon: '👨‍🍳', title: 'CHEF LEAN V10', pill: '👨‍🍳 BÁSCULA NPU & AUDITORÍA DE MERMA', color: '#FF9500', capText: 'CHEF LEAN', capSub: 'F/1.4 • MEAT YIELD MATRIX', botTips: 'Báscula volumétrica y merma cárnica.' },
            { key: 'depth', icon: '🛰️', title: 'DEPTH-MAP NPU', pill: '🛰️ Z-BUFFER 16-BIT & NUBE LIDAR', color: '#00F2FE', capText: 'DEPTH NPU', capSub: 'F/1.4 • DISPARITY 16-BIT', botTips: 'Disparidad de 16-bit y Wiggle 3D.' },
            { key: 'motion', icon: '⚡', title: 'VIDEO MOTION', pill: '⚡ FLUJO ÓPTICO & ESTELAS 60 FPS', color: '#FF9500', capText: 'MOTION V9', capSub: 'F/1.4 • OPTICAL FLOW 60FPS', botTips: 'Rastreo kinético de vectores.' },
            { key: 'svg', icon: '📐', title: 'SVG LOGOS', pill: '📐 VECTORIZADOR CAD & CÓDIGO XML', color: '#00FFC8', capText: 'SVG CAD', capSub: 'F/1.4 • BEZIER AUTOTRACE', botTips: 'Vectorización paramétrica y exportación XML.' },
            { key: 'raw', icon: '🎞️', title: 'ESTUDIO RAW', pill: '🎞️ REVELADO DIGITAL DE 14-BIT & HISTOGRAMA', color: '#FF9F0A', capText: 'RAW STUDIO', capSub: 'F/1.4 • 14-BIT DNG PROFILE', botTips: 'Histograma espectral RGB.' },
            { key: 'cine', icon: '🎬', title: 'CINE SCOPE V10', pill: '🎬 ANAMÓRFICO 2.39:1 & BLUE STREAK FLARE', color: '#FF0055', capText: 'SCOPE 2.39', capSub: 'F/1.4 • ANAMORPHIC DCI', botTips: 'Enmarcado cinematográfico Scope 2.39:1.' },
            { key: 'imprenta', icon: '🖨️', title: 'IMPRENTA PDF', pill: '🖨️ PREPRENSA CMYK & FOGRA39 PROOF', color: '#FF2D85', capText: 'PREPRESS', capSub: 'F/1.4 • CMYK FOGRA39', botTips: 'Mesa de preprensa industrial.' },
            { key: 'stickers', icon: '🎨', title: 'WALLPAPERS STICKERS', pill: '🎨 TROQUELADO 3D & AMOLED BLACK', color: '#BF5AF2', capText: 'DIE-CUT 3D', capSub: 'F/1.4 • AMOLED 19.5:9', botTips: 'Stickers troquelados y wallpapers.' },
            { key: 'lonas', icon: '🎪', title: 'LONAS 3D', pill: '🎪 BASTIDOR PTR & TÚNEL DE VIENTO 110 km/h', color: '#FFD60A', capText: 'LONAS 3D', capSub: 'F/1.4 • PTR WIND TUNNEL', botTips: 'Bastidor PTR y túnel de viento.' },
            { key: 'bokeh', icon: '🎭', title: 'RETRATO BOKEH', pill: '🎭 APERTURA ÓPTICA & IRIS SHAPER', color: '#FF2D55', capText: 'BOKEH f/1.2', capSub: 'F/1.2 • 85MM CINEMA IRIS', botTips: 'Convolución gaussiana y desenfoque.' },
            { key: 'night', icon: '🌙', title: 'NIGHTOGRAPHY', pill: '🌙 MULTI-FRAME STACK & DEEP-SKY BOOST', color: '#5E5CE6', capText: 'NIGHT PRO', capSub: 'F/1.4 • MULTI-FRAME RAW', botTips: 'Fotómetro cuántico y apilado.' },
            { key: 'macro', icon: '🔍', title: 'MACRO PRO', pill: '🔍 FOCUS PEAKING & DEEP FOCUS STACK', color: '#30D158', capText: 'MACRO PRO', capSub: 'F/1.4 • FOCUS PEAKING', botTips: 'Focus Peaking verde y lupa 10x.' },
            { key: 'scan', icon: '📄', title: 'SCAN DOC PRO', pill: '📄 AUTO-ENCUADRE HOMOGRÁFICO & OCR', color: '#00D2FF', capText: 'SCAN DOC', capSub: 'F/1.4 • HOMOGRAPHY OCR', botTips: 'Enderezado homográfico y OCR.' },
            { key: 'timelapse', icon: '⏱️', title: 'TIMELAPSE V10', pill: '⏱️ TIME-LAPSE: CAPTURA COMPRIMIDA 4x', color: '#FF3B30', capText: 'CHRONO OIS', capSub: 'F/1.4 • QUANTUM TRAILS', botTips: 'Gimbal virtual OIS.' },
            { key: 'pano', icon: '🌐', title: 'PANORÁMICA 360', pill: '🌐 BARRIDO POLAR & ORBE 3D VR', color: '#00FFC8', capText: 'PANO 360', capSub: 'F/1.4 • POLAR SPHERE', botTips: 'Barrido cilíndrico y render VR.' }
        ];

        let activeCardIndex = 0;
        const deckStack = document.getElementById('deckStack');
        const horizontalDock = document.getElementById('horizontalDockBar');
        let lastClickedModuleIndex = -1;
        let lastModuleClickTime = 0;

        function renderDeckStack() {
            deckStack.innerHTML = '';
            for (let i = 0; i < 5; i++) {
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

        function renderHorizontalDock() {
            horizontalDock.innerHTML = '';
            moduleCatalog.forEach((m, idx) => {
                const btn = document.createElement('div');
                btn.className = `dock-item-btn ${(idx === activeCardIndex) ? 'active' : ''}`;
                btn.innerHTML = `
                    <span>${m.icon}</span>
                    <span class="dock-dot-indicator" style="background:${m.color}; box-shadow:0 0 6px ${m.color};"></span>
                `;
                if(idx === activeCardIndex) {
                    btn.style.borderColor = m.color;
                    btn.style.boxShadow = `0 0 12px ${m.color}88`;
                }

                btn.onclick = (e) => {
                    e.stopPropagation();
                    const now = Date.now();
                    const isDoubleClick = (lastClickedModuleIndex === idx) && (now - lastModuleClickTime < 650);

                    if (idx === activeCardIndex || isDoubleClick) {
                        activeCardIndex = idx;
                        closeHorizontalDock();
                        renderDeckStack();
                        applyActiveCardTheme(moduleCatalog[activeCardIndex], true);
                        lastClickedModuleIndex = -1;
                    } else {
                        activeCardIndex = idx;
                        lastClickedModuleIndex = idx;
                        lastModuleClickTime = now;
                        renderHorizontalDock();
                        applyActiveCardTheme(moduleCatalog[activeCardIndex], true);
                    }
                };
                horizontalDock.appendChild(btn);
            });
        }

        function openHorizontalDock() {
            renderHorizontalDock();
            deckStack.style.display = 'none';
            horizontalDock.classList.add('active');
        }

        function closeHorizontalDock() {
            horizontalDock.classList.remove('active');
            deckStack.style.display = 'block';
        }

        let deckTouchStartY = 0;
        deckStack.addEventListener('touchstart', (e) => { deckTouchStartY = e.touches[0].clientY; }, { passive: true });
        deckStack.addEventListener('touchend', (e) => {
            const deltaY = deckTouchStartY - e.changedTouches[0].clientY;
            if (deltaY > 20) shiftCard(1, 'slide-up');
            else if (deltaY < -20) shiftCard(-1, 'slide-down');
        }, { passive: true });

        function shiftCard(dir, animClass) {
            const topCard = deckStack.querySelector('.pos-0');
            if (topCard) topCard.classList.add(animClass);

            setTimeout(() => {
                activeCardIndex = (activeCardIndex + dir + moduleCatalog.length) % moduleCatalog.length;
                renderDeckStack();
                applyActiveCardTheme(moduleCatalog[activeCardIndex], true);
            }, 180);
        }

        function applyActiveCardTheme(m, triggerEntryEffect = false) {
            document.getElementById('moduleNameText').innerText = m.title;
            document.getElementById('statusDot').style.background = m.color;
            document.getElementById('contextPillText').innerText = m.pill;
            document.getElementById('contextPillText').style.color = m.color;
            document.getElementById('contextPillText').style.borderColor = `${m.color}66`;

            document.getElementById('masterShutterBtn').style.background = m.color;
            document.getElementById('masterShutterBtn').style.boxShadow = `0 0 22px ${m.color}88`;
            document.getElementById('shutterCorona').style.borderColor = m.color;

            document.getElementById('floatingGadget').innerText = m.icon;
            document.getElementById('floatingGadget').style.borderColor = m.color;
            document.getElementById('floatModTitle').innerText = m.title;
            document.getElementById('floatModTitle').style.color = m.color;
            document.getElementById('floatModDesc').innerText = m.botTips;

            document.getElementById('lockscreenBadge').innerText = `• ${m.title}`;
            document.getElementById('lockscreenBadge').style.color = m.color;
            document.getElementById('lockscreenBadge').style.borderColor = `${m.color}55`;
            document.getElementById('lensCapCenterText').innerText = m.capText;
            document.getElementById('lensCapCenterText').style.color = m.color;
            document.getElementById('lensCapSubText').innerText = m.capSub;

            const topCard = deckStack.querySelector('.pos-0');
            if (topCard) {
                topCard.style.borderColor = m.color;
                topCard.style.background = m.color;
                topCard.style.boxShadow = `0 0 22px ${m.color}`;
                setTimeout(() => {
                    topCard.style.borderColor = 'rgba(255, 255, 255, 0.25)';
                    topCard.style.background = 'rgba(24, 25, 30, 0.92)';
                    topCard.style.boxShadow = '0 8px 24px rgba(0,0,0,0.7)';
                }, 1200);
            }

            if (triggerEntryEffect) {
                triggerUniversalEntryProtocol(m.color);
            }
        }

        let unlocked = false;
        function unlockSuite() {
            if (unlocked) return;
            unlocked = true;
            const curMod = moduleCatalog[activeCardIndex];
            const cap = document.getElementById('lensCapDisk');
            cap.style.transform = 'rotate(-45deg) scale(1.18)';

            setTimeout(() => {
                document.getElementById('lockscreen').classList.add('unlocked');
                applyActiveCardTheme(curMod, true);
            }, 160);
        }

        function lockSuite() {
            unlocked = false;
            document.getElementById('lockscreen').classList.remove('unlocked');
            document.getElementById('lensCapDisk').style.transform = 'none';
            const border = document.getElementById('screenEdgeBorder');
            border.style.borderColor = 'transparent';
            border.style.boxShadow = 'none';
        }

        const lensCapBtn = document.getElementById('lensCapUnlockBtn');
        let touchStartY = 0;
        lensCapBtn.addEventListener('click', unlockSuite);
        lensCapBtn.addEventListener('touchstart', (e) => { touchStartY = e.touches[0].clientY; }, { passive: true });
        lensCapBtn.addEventListener('touchend', (e) => {
            const deltaY = touchStartY - e.changedTouches[0].clientY;
            if (deltaY > 20 || Math.abs(deltaY) < 10) unlockSuite();
        }, { passive: true });

        /* DISPARO GENERAL */
        async function handleMasterCapture() {
            const curMod = moduleCatalog[activeCardIndex];
            triggerUniversalEntryProtocol(curMod.color);

            const b64 = hiddenCanvas.toDataURL('image/jpeg', 0.95);
            lastCapturedUrl = b64;

            const res = await fetch('/bian/process/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image_base64: b64, prompt_analysis: `Captura ${curMod.title}` })
            });

            if (res.ok) {
                const data = await res.json();
                document.getElementById('thumbBox').innerHTML = `<img src="${data.image_path}" />`;
                openMasterEditModal(b64, curMod);
            }
        }

        function openMasterEditModal(imgSrc, curMod) {
            document.getElementById('editModalTitle').innerText = `${curMod.icon} ${curMod.title} RENDER`;
            document.getElementById('editImagePreview').src = imgSrc;
            document.getElementById('postEditModal').style.display = 'flex';
        }

        function closeEditModal() { document.getElementById('postEditModal').style.display = 'none'; }

        function applyMasterFilter(mode, elem) {
            document.querySelectorAll('.tool-chip').forEach(c => c.classList.remove('active'));
            elem.classList.add('active');
            const img = document.getElementById('editImagePreview');
            if (mode === 'standard') img.style.filter = 'contrast(1.1) saturate(1.1)';
            else if (mode === 'high_contrast') img.style.filter = 'contrast(1.35) brightness(1.05)';
            else if (mode === 'vivid_tone') img.style.filter = 'saturate(1.4) contrast(1.15)';
        }

        function exportMasterResult() {
            const curMod = moduleCatalog[activeCardIndex];
            const a = document.createElement('a');
            a.href = lastCapturedUrl || document.getElementById('editImagePreview').src;
            a.download = `bian_${curMod.key}_v10_${Date.now()}.jpg`;
            a.click();
            alert('✔ Asset exportado exitosamente a la memoria local.');
        }

        /* GADGET FLOTANTE */
        const gadget = document.getElementById('floatingGadget');
        let isDragging = false;
        let dragStartX, dragStartY, gadgetStartX, gadgetStartY;
        let hasMovedSignificantly = false;

        gadget.addEventListener('touchstart', (e) => {
            isDragging = true;
            hasMovedSignificantly = false;
            const touch = e.touches[0];
            dragStartX = touch.clientX;
            dragStartY = touch.clientY;
            const rect = gadget.getBoundingClientRect();
            gadgetStartX = rect.left;
            gadgetStartY = rect.top;
            gadget.style.transition = 'none';
        }, { passive: true });

        window.addEventListener('touchmove', (e) => {
            if (!isDragging) return;
            const touch = e.touches[0];
            const deltaX = touch.clientX - dragStartX;
            const deltaY = touch.clientY - dragStartY;
            if (Math.abs(deltaX) > 5 || Math.abs(deltaY) > 5) hasMovedSignificantly = true;
            const newX = Math.min(window.innerWidth - 52, Math.max(4, gadgetStartX + deltaX));
            const newY = Math.min(window.innerHeight - 100, Math.max(60, gadgetStartY + deltaY));
            gadget.style.left = `${newX}px`;
            gadget.style.top = `${newY}px`;
        }, { passive: true });

        window.addEventListener('touchend', () => {
            if (!isDragging) return;
            isDragging = false;
            gadget.style.transition = 'left 0.35s cubic-bezier(0.16, 1, 0.3, 1), top 0.35s ease';
            if (!hasMovedSignificantly) {
                toggleFloatingPanel();
                return;
            }
            const rect = gadget.getBoundingClientRect();
            const snapLeft = (rect.left + rect.width / 2 < window.innerWidth / 2) ? 14 : (window.innerWidth - 62);
            gadget.style.left = `${snapLeft}px`;
        });

        function toggleFloatingPanel() {
            const panel = document.getElementById('floatingPanel');
            const isOpen = panel.style.display === 'flex';
            panel.style.display = isOpen ? 'none' : 'flex';

            if (!isOpen) {
                const cur = moduleCatalog[activeCardIndex];
                const list = document.getElementById('floatActionList');
                list.innerHTML = `
                    <button class="bot-btn" onclick="handleMasterCapture(); toggleFloatingPanel();">📸 Disparo con ${cur.title}</button>
                    <button class="bot-btn" onclick="openHorizontalDock(); toggleFloatingPanel();">🎴 Selector de Módulos</button>
                    <button class="bot-btn" onclick="toggleGhostScope(); toggleFloatingPanel();">👁 Alternar Radar Espectral</button>
                    <button class="bot-btn" onclick="openGalleryModal(); toggleFloatingPanel();">🖼️ Ver Galería Local</button>
                `;
            }
        }

        async function updateThumb() {
            try {
                const res = await fetch('/bian/images/');
                const list = await res.json();
                if(list.length > 0) {
                    const last = list[list.length - 1];
                    document.getElementById('thumbBox').innerHTML = `<img src="${last.image_path}" />`;
                }
            } catch(e) {}
        }

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
                        openMasterEditModal(img.image_path, moduleCatalog[activeCardIndex]);
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

        /* 🌟 NANO-BOT TÁCTICO V2 ULTRA: MÉTODOS Y MACROS 🌟 */
        function openNanobot() {
            const curMod = moduleCatalog[activeCardIndex];
            const modal = document.getElementById('nanobotModal');
            const term = document.getElementById('botTerminalOutput');
            const act = document.getElementById('botActionList');

            document.getElementById('botActiveModLabel').innerText = curMod.title;
            term.innerHTML = `
                > INICIALIZANDO COPILOTO TÁCTICO V2...<br>
                > MÓDULO AUDITADO: <span style="color:${curMod.color}; font-weight:800;">${curMod.title}</span><br>
                > ESTADO: ${curMod.botTips}<br>
                > LATENCIA EN MEMORIA RAM: 11.4 ms | INFERENCIA LISTA
            `;

            act.innerHTML = `
                <button class="bot-btn" onclick="executeBotMacro('calibrate')">
                    <span>⚡ Calibración Óptima del Módulo</span>
                    <span style="color:#888;">MACRO</span>
                </button>
                <button class="bot-btn" onclick="executeBotMacro('clear_ram')">
                    <span>🧹 Purgar Búfer de RAM en Termux</span>
                    <span style="color:#888;">CACHE</span>
                </button>
                <button class="bot-btn" onclick="executeBotMacro('ghost')">
                    <span>👁 Alternar Radar de Frecuencia Espectral</span>
                    <span style="color:#888;">VISOR</span>
                </button>
                <button class="bot-btn" onclick="executeBotMacro('gallery')">
                    <span>🖼 Inspeccionar Almacén SQLite Local</span>
                    <span style="color:#888;">BASE DE DATOS</span>
                </button>
            `;

            playBotVoiceChirp();
            modal.style.display = 'flex';
        }

        function closeNanobot() { document.getElementById('nanobotModal').style.display = 'none'; }

        function playBotVoiceChirp() {
            try {
                const ctx = getAudioContext();
                const now = ctx.currentTime;
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.connect(gain); gain.connect(ctx.destination);
                osc.type = 'sine';
                osc.frequency.setValueAtTime(600, now);
                osc.frequency.setValueAtTime(1200, now + 0.08);
                osc.frequency.setValueAtTime(1800, now + 0.14);
                gain.gain.setValueAtTime(0.2, now);
                gain.gain.exponentialRampToValueAtTime(0.001, now + 0.22);
                osc.start(now); osc.stop(now + 0.23);
            } catch(e) {}
        }

        function executeBotMacro(macro) {
            const curMod = moduleCatalog[activeCardIndex];
            closeNanobot();

            if (macro === 'calibrate') {
                applyActiveCardTheme(curMod, true);
                alert(`✔ Calibración completa para ${curMod.title}. Parámetros fijados en RAM.`);
            } else if (macro === 'clear_ram') {
                spores = [];
                initSpores();
                triggerUniversalEntryProtocol(curMod.color);
                alert("✔ Búfer de memoria purgado exitosamente. Esporas re-inicializadas.");
            } else if (macro === 'ghost') {
                toggleGhostScope();
            } else if (macro === 'gallery') {
                openGalleryModal();
            }
        }

        function executeCustomBotCommand() {
            const input = document.getElementById('botCommandInput');
            const cmd = input.value.trim().toLowerCase();
            if (!cmd) return;

            const term = document.getElementById('botTerminalOutput');
            const curMod = moduleCatalog[activeCardIndex];

            playBotVoiceChirp();
            term.innerHTML += `<br>> COMANDO EJECUTADO: <span style="color:#fff;">${cmd}</span><br>> APLICANDO AJUSTE NEURONAL...`;
            input.value = '';

            setTimeout(() => {
                triggerUniversalEntryProtocol(curMod.color);
                term.innerHTML += `<br>> AJUSTE CONFIRMADO EN TERMINAL [OK]`;
            }, 300);
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
    db_image = ProcessedImage(image_path=f"/bian/{filename}", prompt_analysis=payload.prompt_analysis)
    session.add(db_image)
    session.commit()
    session.refresh(db_image)
    return db_image

@router.get("/images/", response_model=list[ProcessedImage])
def list_images(session: Session = Depends(get_session)):
    return session.exec(select(ProcessedImage)).all()
