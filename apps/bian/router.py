from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, select
from core.database import get_session
from apps.bian.models import ProcessedImage
from pydantic import BaseModel
import os
import base64
from datetime import datetime

router = APIRouter(prefix="/bian", tags=["Bian Master Suite V10"])

STORAGE_DIR = os.path.abspath("storage/bian")
os.makedirs(STORAGE_DIR, exist_ok=True)

class ImageCaptureRequest(BaseModel):
    image_base64: str
    prompt_analysis: str = "Captura Master Suite V10"

@router.get("/asset/{filename}")
async def get_asset(filename: str):
    file_path = os.path.join(STORAGE_DIR, filename)
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    return FileResponse(file_path)

HTML_CONTENT = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>BIAN MASTER SUITE V10 PRO - 21 MÓDULOS</title>
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

        /* LOCKSCREEN CON GESTO DE DESLIZAMIENTO DEL DEDO */
        #lockscreen {
            position: fixed; inset: 0; background: #050608; z-index: 200;
            display: flex; flex-direction: column; align-items: center; justify-content: space-between;
            padding: 45px 20px 35px 20px; transition: transform 0.5s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.45s ease;
            touch-action: none;
        }
        #lockscreen.unlocked { transform: translateY(-100%); opacity: 0; pointer-events: none; }

        .pill-badge {
            background: rgba(0, 229, 255, 0.08); border: 1px solid rgba(0, 229, 255, 0.3);
            color: #00E5FF; font-size: 10px; font-weight: 700; letter-spacing: 1.5px;
            padding: 6px 14px; border-radius: 20px; text-transform: uppercase;
        }
        .brand-center { text-align: center; margin-top: auto; margin-bottom: auto; }
        .brand-title {
            font-size: 64px; font-weight: 900; letter-spacing: 8px; color: #FFFFFF;
            text-shadow: 0 0 20px rgba(255, 255, 255, 0.45); line-height: 1; margin-bottom: 8px;
        }
        .brand-subtitle { font-size: 14px; font-weight: 600; color: #aaa; margin-bottom: 12px; }

        /* PERILLA CON MOVIMIENTO DEL DEDO */
        .camera-dial-assembly {
            display: flex; flex-direction: column; align-items: center; cursor: pointer; touch-action: none; margin-bottom: 20px;
        }
        .camera-knurled-dial {
            width: 105px; height: 105px; border-radius: 50%;
            background: radial-gradient(circle, #2a2d36 0%, #15171d 60%, #0a0b0e 100%);
            border: 4px solid #3d4352; box-shadow: 0 10px 35px rgba(0,0,0,0.95), inset 0 0 12px rgba(255,255,255,0.08);
            display: flex; flex-direction: column; align-items: center; justify-content: center;
            position: relative; transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1), border-color 0.3s;
        }
        .knurled-ring {
            position: absolute; inset: -2px; border-radius: 50%;
            border: 2px dashed rgba(255, 255, 255, 0.15); pointer-events: none;
        }
        .dial-red-dot {
            width: 7px; height: 7px; border-radius: 50%; background: #FF3B30; margin-bottom: 4px;
            box-shadow: 0 0 8px #FF3B30;
        }
        .dial-center-title { font-size: 11px; font-weight: 900; letter-spacing: 2px; color: #00E5FF; text-align: center; }
        .dial-sub-spec { font-size: 7px; color: #777; margin-top: 2px; font-weight: 700; letter-spacing: 0.5px; }
        .dial-hint-text { font-size: 9.5px; font-weight: 800; color: #888; margin-top: 10px; letter-spacing: 1.5px; }

        /* VIEWPORT Y VISOR */
        .suite-view { width: 100vw; height: 100vh; position: relative; background: #000; overflow: hidden; display: flex; flex-direction: column; }
        #videoContainer { width: 100%; height: 100%; position: relative; overflow: hidden; }
        video { width: 100%; height: 100%; object-fit: cover; }

        #ghostScopeCanvas {
            position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover;
            pointer-events: none; z-index: 45; opacity: 0; mix-blend-mode: screen; transition: opacity 0.3s;
        }
        #ghostScopeCanvas.active { opacity: 0.75; }

        /* ESPORAS DE LUZ (SOLO EN EL DESBLOQUEO, 0.8s) */
        #sporesMatrixCanvas {
            position: absolute; inset: 0; width: 100%; height: 100%; pointer-events: none; z-index: 52;
            opacity: 0; transition: opacity 0.8s cubic-bezier(0.16, 1, 0.3, 1);
        }
        #sporesMatrixCanvas.active { opacity: 1; transition: opacity 0.05s ease-in; }

        /* TOP DOCK LIMPIO */
        .top-dock {
            position: absolute; top: 16px; left: 16px; right: 16px; z-index: 100;
            display: flex; justify-content: space-between; align-items: center;
        }
        .hud-status-badge {
            background: rgba(18, 18, 22, 0.75); border: 1px solid rgba(255, 255, 255, 0.12);
            color: #fff; font-size: 11px; font-weight: 700; padding: 6px 14px; border-radius: 20px;
            backdrop-filter: blur(10px); display: flex; align-items: center; gap: 6px;
        }
        .hud-status-badge .dot { width: 7px; height: 7px; border-radius: 50%; background: #00E5FF; display: inline-block; }
        .top-action-btn {
            background: rgba(18, 18, 22, 0.75); border: 1px solid rgba(255, 255, 255, 0.15);
            color: #fff; font-size: 11px; font-weight: 600; padding: 6px 14px; border-radius: 20px;
            backdrop-filter: blur(10px); cursor: pointer; display: flex; align-items: center; gap: 4px;
        }

        /* 🌟 GADGETS REUBICADOS ABAJO (ENCIMA DE LA BARRA DE DISPARO) 🌟 */
        .bottom-hud-control-stack {
            position: absolute; bottom: 165px; left: 0; right: 0; z-index: 95;
            display: flex; flex-direction: column; align-items: center; gap: 8px; pointer-events: auto;
        }

        .telemetry-dial-pill {
            background: rgba(16, 20, 26, 0.9); border: 1px solid rgba(255, 255, 255, 0.2);
            color: #00E5FF; font-size: 10px; font-weight: 800; letter-spacing: 1px;
            padding: 5px 14px; border-radius: 20px; cursor: pointer; backdrop-filter: blur(14px);
            display: flex; align-items: center; gap: 6px; box-shadow: 0 4px 16px rgba(0,0,0,0.7);
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
        }
        .telemetry-dial-pill:hover { border-color: #00E5FF; box-shadow: 0 0 12px rgba(0, 229, 255, 0.4); }
        .telemetry-dial-pill .knurl-dot { width: 5px; height: 5px; border-radius: 50%; background: #00E5FF; }

        .context-pill {
            background: rgba(14, 16, 22, 0.85); border: 1px solid rgba(0, 229, 255, 0.4);
            color: #00E5FF; font-size: 10px; font-weight: 800; letter-spacing: 0.8px;
            padding: 4px 14px; border-radius: 20px; backdrop-filter: blur(10px); text-transform: uppercase;
        }

        /* BANDEJA DESPLEGABLE DE TELEMETRÍA (SE ABRE HACIA ARRIBA DESDE ABAJO) */
        #telemetryDrawer {
            display: none; position: absolute; bottom: 230px; left: 16px; right: 16px; z-index: 97;
            background: rgba(8, 12, 16, 0.95); border: 1px solid rgba(0, 229, 255, 0.4);
            border-radius: 16px; padding: 12px 14px; backdrop-filter: blur(25px);
            flex-direction: column; gap: 6px; font-family: monospace; font-size: 10px;
            box-shadow: 0 -8px 25px rgba(0,0,0,0.85); animation: drawerRise 0.22s cubic-bezier(0.16, 1, 0.3, 1);
        }
        @keyframes drawerRise {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .drawer-row { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.06); padding: 4px 0; }

        /* DOCKS Y OBTURADOR */
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
        .dock-dot-indicator { position: absolute; bottom: -3px; width: 6px; height: 6px; border-radius: 50%; display: none; }
        .dock-item-btn.active .dock-dot-indicator { display: block; }

        .bottom-bar {
            position: absolute; bottom: 20px; left: 0; right: 0; z-index: 100;
            display: flex; justify-content: space-around; align-items: center; padding: 0 25px;
        }
        .shutter-wrapper { position: relative; width: 80px; height: 80px; display: flex; align-items: center; justify-content: center; }
        .shutter-corona { position: absolute; inset: -4px; border-radius: 50%; border: 2px dashed rgba(255,255,255,0.3); pointer-events: none; }
        .shutter-btn {
            width: 72px; height: 72px; border-radius: 50%; background: #00E5FF;
            border: 4px solid #fff; box-shadow: 0 0 22px rgba(0, 229, 255, 0.55); cursor: pointer;
        }
        .lens-switch-btn {
            width: 46px; height: 46px; border-radius: 50%; background: rgba(30, 30, 35, 0.75);
            border: 1px solid rgba(255, 255, 255, 0.2); display: flex; align-items: center; justify-content: center; font-size: 19px; cursor: pointer;
        }
        .gallery-thumb {
            width: 46px; height: 46px; border-radius: 50%; border: 2px solid rgba(0, 229, 255, 0.6);
            background: #111; overflow: hidden; cursor: pointer; box-shadow: 0 0 10px rgba(0, 229, 255, 0.4);
        }
        .gallery-thumb img { width: 100%; height: 100%; object-fit: cover; }

        /* MODALES */
        #galleryModal {
            display: none; position: fixed; inset: 0; z-index: 320; background: rgba(5, 7, 10, 0.98);
            backdrop-filter: blur(25px); flex-direction: column; padding: 18px;
        }
        .vault-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
        .vault-filter-bar { display: flex; gap: 6px; overflow-x: auto; scrollbar-width: none; margin-bottom: 12px; }
        .vault-chip {
            padding: 5px 12px; font-size: 10px; font-weight: 800; border-radius: 14px;
            background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.15);
            color: #ccc; cursor: pointer; white-space: nowrap;
        }
        .vault-chip.active { background: #00E5FF; color: #000; border-color: #00E5FF; }
        .gallery-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; overflow-y: auto; flex: 1; }
        .gallery-card {
            background: #0d1117; border: 1px solid #1f2838; border-radius: 14px; overflow: hidden;
            cursor: pointer; position: relative; display: flex; flex-direction: column; min-height: 145px;
        }
        .gallery-card-img-wrapper {
            width: 100%; height: 115px; background: #05070a; overflow: hidden; display: flex; align-items: center; justify-content: center;
        }
        .gallery-card img { width: 100%; height: 100%; object-fit: cover; display: block; }
        .gallery-card-info {
            padding: 7px 9px; font-size: 9.5px; color: #888; background: #090c12;
            display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #161e2a;
        }

        #assetDetailModal {
            display: none; position: fixed; inset: 0; z-index: 340; background: rgba(3, 5, 8, 0.98);
            backdrop-filter: blur(25px); flex-direction: column; padding: 18px;
        }
        .asset-preview-box {
            flex: 1; border-radius: 14px; overflow: hidden; background: #000; border: 1px solid #1a2230;
            display: flex; align-items: center; justify-content: center; position: relative; margin: 10px 0;
        }
        .asset-preview-box img { max-width: 100%; max-height: 100%; object-fit: contain; }
        .asset-metadata-card {
            background: #0c1017; border: 1px solid #1f2a38; border-radius: 12px; padding: 12px;
            font-family: monospace; font-size: 11px; color: #00E5FF; display: flex; flex-direction: column; gap: 4px;
        }
        .asset-action-row { display: flex; gap: 8px; margin-top: 10px; }
        .btn-asset-action { flex: 1; padding: 11px; border-radius: 12px; font-size: 11px; font-weight: 800; border: none; cursor: pointer; }

        #nanobotModal {
            display: none; position: fixed; inset: 0; z-index: 330; background: rgba(5, 7, 10, 0.96);
            backdrop-filter: blur(25px); flex-direction: column; padding: 22px 18px; justify-content: space-between;
        }
        .bot-terminal-card {
            background: #080c10; border: 1px solid rgba(0, 255, 200, 0.35); border-radius: 16px;
            padding: 14px; font-family: monospace; font-size: 11px; color: #00FFC8; margin-top: 10px;
        }
        .bot-actions { display: flex; flex-direction: column; gap: 8px; margin-top: 12px; }
        .bot-btn {
            background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.15); color: #fff;
            padding: 10px 14px; border-radius: 12px; font-size: 11px; font-weight: 700; text-align: left; cursor: pointer;
        }
    </style>
</head>
<body>
    <div class="edge-screen-border" id="screenEdgeBorder"></div>
    <div class="ambient-fade-light" id="ambientLightLayer"></div>

    <!-- LOCKSCREEN CON DESLIZAMIENTO DEL DEDO Y PERILLA -->
    <div id="lockscreen">
        <div class="pill-badge">• BIAN MASTER SUITE V10</div>
        <div class="brand-center">
            <div class="brand-title">BIAN</div>
            <div class="brand-subtitle" id="lockscreenSub">21 Módulos Ultra Integrados</div>
        </div>
        <div class="camera-dial-assembly" id="cameraDialUnlockBtn">
            <div class="camera-knurled-dial" id="knurledDialDisk">
                <div class="knurled-ring"></div>
                <div class="dial-red-dot"></div>
                <div class="dial-center-title" id="dialCenterTitle">BIAN 35MM</div>
                <div class="dial-sub-spec" id="dialSubSpec">F/1.4 • NATIVE ENGINE</div>
            </div>
            <div class="dial-hint-text">🔓 DESLIZA O GIRA PARA ABRIR</div>
        </div>
    </div>

    <div class="suite-view">
        <div id="videoContainer">
            <video id="webcam" autoplay playsinline></video>
            <canvas id="ghostScopeCanvas"></canvas>
            <canvas id="sporesMatrixCanvas"></canvas>
        </div>

        <!-- TOP DOCK LIMPIO -->
        <div class="top-dock">
            <div class="hud-status-badge">
                <span class="dot" id="statusDot"></span>
                <span id="moduleNameText">CAM VISION V10</span>
            </div>
            <div style="display: flex; gap: 6px;">
                <button class="top-action-btn" onclick="lockSuite()">🔒</button>
                <button class="top-action-btn" onclick="openGalleryModal()">🖼️ Almacén</button>
                <button class="top-action-btn" onclick="openNanobot()">✨ Nano-Bot</button>
            </div>
        </div>

        <!-- 🌟 BANDEJA DESPLEGABLE DE TELEMETRÍA (ABRE DE ABAJO HACIA ARRIBA) 🌟 -->
        <div id="telemetryDrawer">
            <div class="drawer-row">
                <span style="color:#888;">DENSIDAD / PERFIL:</span>
                <strong style="color:#00E5FF;" id="drawerDensity">DENSITY: AERO OPTIC</strong>
            </div>
            <div class="drawer-row">
                <span style="color:#888;">ESTADO NPU:</span>
                <strong style="color:#30D158;" id="drawerNpu">SNAPDRAGON 8G2 NPU</strong>
            </div>
            <div class="drawer-row">
                <span style="color:#888;">VELOCIDAD DE OBTURACIÓN:</span>
                <strong style="color:#FFD600;" id="drawerSS">SS: 1/500s</strong>
            </div>
            <div class="drawer-row">
                <span style="color:#888;">SENSIBILIDAD BASE:</span>
                <strong style="color:#fff;">ISO: 100 BASE</strong>
            </div>
        </div>

        <!-- 🌟 GADGETS COLOCADOS ABAJO, LIMPIANDO EL VISOR SUPERIOR 🌟 -->
        <div class="bottom-hud-control-stack">
            <div class="telemetry-dial-pill" onclick="toggleTelemetryDrawer()">
                <span class="knurl-dot"></span>
                <span id="moreInfoText">📊 MÁS INFO</span>
                <span style="font-size:8px;">▲</span>
            </div>
            <div class="context-pill" id="contextPillText">ENCUADRE TÁCTICO LISTO</div>
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

    <!-- MODAL DE BÓVEDA -->
    <div id="galleryModal">
        <div class="vault-header">
            <div style="font-size:14px; font-weight:900; color:#00E5FF;">🏛️ BÓVEDA & ALMACÉN SOBERANO V3</div>
            <button class="top-action-btn" onclick="closeGalleryModal()">✖ Cerrar</button>
        </div>
        <div class="vault-filter-bar">
            <button class="vault-chip active" onclick="filterGallery('todos', this)">Todos</button>
            <button class="vault-chip" onclick="filterGallery('despacho', this)">Despacho</button>
            <button class="vault-chip" onclick="filterGallery('chef', this)">Chef Lean</button>
            <button class="vault-chip" onclick="filterGallery('valuador', this)">Valuador</button>
            <button class="vault-chip" onclick="filterGallery('ai', this)">Generador AI</button>
        </div>
        <div class="gallery-grid" id="galleryGridContent"></div>
    </div>

    <!-- MODAL DE INSPECCIÓN -->
    <div id="assetDetailModal">
        <div class="vault-header">
            <div style="font-size:13px; font-weight:800; color:#00E5FF;" id="assetDetailTitle">INSPECCIÓN FORENSE</div>
            <button class="top-action-btn" onclick="closeAssetDetail()">✖ Volver</button>
        </div>
        <div class="asset-preview-box">
            <img id="assetDetailImg" src="" alt="Asset Detail" />
        </div>
        <div class="asset-metadata-card" id="assetDetailMeta"></div>
        <div class="asset-action-row">
            <button class="btn-asset-action" style="background:#00E5FF; color:#000;" onclick="downloadActiveAsset()">📥 Exportar HD</button>
            <button class="btn-asset-action" style="background:#FF3B30; color:#fff;" onclick="deleteActiveAsset()">🗑️ Eliminar</button>
        </div>
    </div>

    <!-- MODAL DE NANO-BOT -->
    <div id="nanobotModal">
        <div>
            <div class="vault-header">
                <div style="color:#00FFC8; font-size:13px; font-weight:800;">✨ NANO-BOT TÁCTICO V2</div>
                <button class="top-action-btn" onclick="closeNanobot()">✖ Cerrar</button>
            </div>
            <div class="bot-terminal-card" id="botTerminalOutput">
                > NANO-BOT TÁCTICO V2 ONLINE...<br>
                > MONITOREANDO LOS 21 MÓDULOS DE LA SUITE
            </div>
            <div class="bot-actions">
                <button class="bot-btn" onclick="closeNanobot(); openGalleryModal();">🏛️ Abrir Bóveda de Activos V3</button>
                <button class="bot-btn" onclick="clearRamMacro()">🧹 Purgar Búfer de RAM en Termux</button>
            </div>
        </div>
    </div>

    <canvas id="hiddenBufferCanvas" style="display:none;"></canvas>

    <script>
        const video = document.getElementById('webcam');
        const hiddenCanvas = document.getElementById('hiddenBufferCanvas');
        const sporesCanvas = document.getElementById('sporesMatrixCanvas');
        const sporesCtx = sporesCanvas.getContext('2d');
        let audioCtx = null;
        let facingMode = 'environment';
        let sporesTimeout = null;
        let allGalleryItems = [];
        let activeAssetItem = null;
        let isDrawerOpen = false;

        /* SISTEMA DE ESPORAS */
        let spores = [];
        const NUM_SPORES = 26;

        function initSpores() {
            spores = [];
            for (let i = 0; i < NUM_SPORES; i++) {
                spores.push({
                    x: Math.random() * window.innerWidth,
                    y: Math.random() * window.innerHeight,
                    vx: (Math.random() - 0.5) * 1.6,
                    vy: (Math.random() - 0.5) * 1.6,
                    radius: Math.random() * 2.8 + 1.2,
                    pulse: Math.random() * Math.PI * 2
                });
            }
        }
        initSpores();

        function getAudioContext() {
            if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            if (audioCtx.state === 'suspended') audioCtx.resume();
            return audioCtx;
        }

        function startCamera() {
            if (video.srcObject) video.srcObject.getTracks().forEach(t => t.stop());
            navigator.mediaDevices.getUserMedia({ video: { facingMode, width: { ideal: 1920 }, height: { ideal: 1080 } } })
            .then(stream => {
                video.srcObject = stream;
                updateThumb();
                requestAnimationFrame(processPipeline);
            }).catch(err => console.warn(err));
        }
        startCamera();

        function toggleLens() {
            facingMode = (facingMode === 'environment') ? 'user' : 'environment';
            startCamera();
        }

        function processPipeline() {
            if (video.readyState >= 2) {
                if (hiddenCanvas.width !== video.videoWidth) {
                    hiddenCanvas.width = video.videoWidth || 640;
                    hiddenCanvas.height = video.videoHeight || 480;
                    sporesCanvas.width = window.innerWidth;
                    sporesCanvas.height = window.innerHeight;
                }
                const hCtx = hiddenCanvas.getContext('2d');
                hCtx.drawImage(video, 0, 0, hiddenCanvas.width, hiddenCanvas.height);
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
            for (let x = 0; x < w; x += 45) {
                sporesCtx.beginPath(); sporesCtx.moveTo(x, 0); sporesCtx.lineTo(x, h); sporesCtx.stroke();
            }
            for (let y = 0; y < h; y += 45) {
                sporesCtx.beginPath(); sporesCtx.moveTo(0, y); sporesCtx.lineTo(w, y); sporesCtx.stroke();
            }
            sporesCtx.setLineDash([]);

            spores.forEach(sp => {
                sp.x += sp.vx; sp.y += sp.vy; sp.pulse += 0.05;
                if (sp.x < 0) sp.x = w; if (sp.x > w) sp.x = 0;
                if (sp.y < 0) sp.y = h; if (sp.y > h) sp.y = 0;
                const currentR = sp.radius + Math.sin(sp.pulse) * 0.8;
                sporesCtx.fillStyle = col;
                sporesCtx.shadowColor = col;
                sporesCtx.shadowBlur = 8;
                sporesCtx.beginPath();
                sporesCtx.arc(sp.x, sp.y, Math.max(0.5, currentR), 0, Math.PI * 2);
                sporesCtx.fill();
            });
            sporesCtx.shadowBlur = 0;
        }

        /* 🌟 1. EFECTO DE DESBLOQUEO (ESPORAS ACTIVAS SÓLO AQUÍ, 0.8s) 🌟 */
        function triggerUnlockProtocol(color) {
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

            // Esporas sólo en desbloqueo
            sCanvas.classList.add('active');

            setTimeout(() => {
                border.style.transition = 'border-color 0.8s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.8s cubic-bezier(0.16, 1, 0.3, 1)';
                border.style.borderColor = 'transparent';
                border.style.boxShadow = 'none';
                ambient.classList.remove('flash');
            }, 120);

            clearTimeout(sporesTimeout);
            sporesTimeout = setTimeout(() => {
                sCanvas.classList.remove('active');
            }, 800);
        }

        /* 🌟 2. CAMBIO DE MÓDULO (COLOR DE BORDES Y SONIDO PROPIO SIN ESPORAS) 🌟 */
        function triggerModuleSwitchProtocol(color, key) {
            const border = document.getElementById('screenEdgeBorder');
            const ambient = document.getElementById('ambientLightLayer');

            border.style.transition = 'border-color 0.08s ease-in, box-shadow 0.08s ease-in';
            border.style.borderColor = color;
            border.style.boxShadow = `inset 0 0 35px ${color}, 0 0 25px ${color}`;

            ambient.style.background = `radial-gradient(circle at 50% 50%, ${color}45 0%, transparent 70%)`;
            ambient.classList.remove('flash');
            void ambient.offsetWidth;
            ambient.classList.add('flash');

            playUniqueModuleSound(key);

            setTimeout(() => {
                border.style.transition = 'border-color 0.7s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.7s cubic-bezier(0.16, 1, 0.3, 1)';
                border.style.borderColor = 'transparent';
                border.style.boxShadow = 'none';
                ambient.classList.remove('flash');
            }, 100);
        }

        /* 🌟 3. FIRMA ACÚSTICA DEDICADA PARA CADA UNO DE LOS 21 MÓDULOS 🌟 */
        function playUniqueModuleSound(key) {
            try {
                const ctx = getAudioContext();
                const now = ctx.currentTime;
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.connect(gain); gain.connect(ctx.destination);

                // Configuración espectral individual por módulo
                const soundMap = {
                    'cam':       { type: 'triangle', fStart: 260, fEnd: 520, dur: 0.12 },
                    'pano':      { type: 'sine',     fStart: 180, fEnd: 880, dur: 0.18 },
                    'timelapse': { type: 'square',   fStart: 300, fEnd: 150, dur: 0.10 },
                    'scan':      { type: 'sawtooth', fStart: 880, fEnd: 1760, dur: 0.14 },
                    'night':     { type: 'sine',     fStart: 120, fEnd: 240, dur: 0.22 },
                    'macro':     { type: 'sine',     fStart: 1200, fEnd: 2400, dur: 0.15 },
                    'bokeh':     { type: 'triangle', fStart: 340, fEnd: 180, dur: 0.16 },
                    'lonas':     { type: 'sawtooth', fStart: 180, fEnd: 360, dur: 0.15 },
                    'stickers':  { type: 'sine',     fStart: 600, fEnd: 1200, dur: 0.11 },
                    'imprenta':  { type: 'square',   fStart: 440, fEnd: 220, dur: 0.14 },
                    'cine':      { type: 'triangle', fStart: 110, fEnd: 75,  dur: 0.25 },
                    'raw':       { type: 'sine',     fStart: 440, fEnd: 880, dur: 0.13 },
                    'svg':       { type: 'triangle', fStart: 700, fEnd: 1400, dur: 0.12 },
                    'motion':    { type: 'sawtooth', fStart: 150, fEnd: 650, dur: 0.17 },
                    'depth':     { type: 'sine',     fStart: 950, fEnd: 1900, dur: 0.16 },
                    'chef':      { type: 'triangle', fStart: 380, fEnd: 760, dur: 0.15 },
                    'price':     { type: 'sine',     fStart: 540, fEnd: 1080, dur: 0.14 },
                    'ai':        { type: 'sawtooth', fStart: 250, fEnd: 1500, dur: 0.20 },
                    'dispatch':  { type: 'square',   fStart: 750, fEnd: 1500, dur: 0.12 },
                    'nanobot':   { type: 'sine',     fStart: 1200, fEnd: 600, dur: 0.16 },
                    'vault':     { type: 'triangle', fStart: 200, fEnd: 400, dur: 0.15 }
                };

                const s = soundMap[key] || { type: 'sine', fStart: 440, fEnd: 880, dur: 0.14 };
                osc.type = s.type;
                osc.frequency.setValueAtTime(s.fStart, now);
                osc.frequency.exponentialRampToValueAtTime(s.fEnd, now + s.dur);
                gain.gain.setValueAtTime(0.28, now);
                gain.gain.exponentialRampToValueAtTime(0.001, now + s.dur);
                osc.start(now); osc.stop(now + s.dur + 0.01);
            } catch(e) {}
        }

        /* 🌟 GESTIÓN DE LA PERILLA "MÁS INFO" ABAJO 🌟 */
        function toggleTelemetryDrawer() {
            isDrawerOpen = !isDrawerOpen;
            const drawer = document.getElementById('telemetryDrawer');
            drawer.style.display = isDrawerOpen ? 'flex' : 'none';
            document.getElementById('moreInfoText').innerText = isDrawerOpen ? '▼ OCULTAR' : '📊 MÁS INFO';
        }

        /* 🌟 4. DESBLOQUEO POR GESTO DEL DEDO (TOUCH SWIPE) 🌟 */
        let unlocked = false;
        let touchStartY = 0;

        function unlockSuite() {
            if (unlocked) return;
            unlocked = true;
            const curMod = moduleCatalog[activeCardIndex];
            const dial = document.getElementById('knurledDialDisk');
            dial.style.transform = 'rotate(-60deg) scale(1.15)';

            setTimeout(() => {
                document.getElementById('lockscreen').classList.add('unlocked');
                applyActiveCardTheme(curMod, false);
                triggerUnlockProtocol(curMod.color); // Esporas solo aquí
                playUniqueModuleSound(curMod.key);
            }, 160);
        }

        function lockSuite() {
            unlocked = false;
            document.getElementById('lockscreen').classList.remove('unlocked');
            document.getElementById('knurledDialDisk').style.transform = 'none';
        }

        const lockElem = document.getElementById('lockscreen');
        lockElem.addEventListener('touchstart', (e) => {
            touchStartY = e.touches[0].clientY;
        }, { passive: true });

        lockElem.addEventListener('touchend', (e) => {
            const deltaY = touchStartY - e.changedTouches[0].clientY;
            // Desbloqueo por deslizamiento hacia arriba o toque del dial
            if (deltaY > 25 || Math.abs(deltaY) < 10) {
                unlockSuite();
            }
        }, { passive: true });

        function getSafeAssetUrl(rawPath) {
            if (!rawPath) return '';
            const filename = rawPath.split('/').pop();
            return `/bian/asset/${filename}`;
        }

        /* CATÁLOGO DE LOS 21 MÓDULOS DE BIAN V10 */
        const moduleCatalog = [
            { key: 'cam', icon: '📷', title: 'CAM VISION V10', pill: '📷 TITANIUM AERO & ZERO-SHUTTER-LAG', color: '#00E5FF', capText: 'CAM VISION', capSub: 'F/1.4 • AERO HUD', ss: '1/500s', density: 'AERO OPTIC' },
            { key: 'pano', icon: '🌐', title: 'PANORÁMICA 360', pill: '🌐 BARRIDO POLAR & ORBE 3D VR', color: '#00FFC8', capText: 'PANO 360', capSub: 'F/1.4 • POLAR SPHERE', ss: '1/250s', density: 'VR STITCH' },
            { key: 'timelapse', icon: '⏱️', title: 'TIMELAPSE V10', pill: '⏱️️ TIME-LAPSE: CAPTURA COMPRIMIDA 4x', color: '#FF3B30', capText: 'CHRONO OIS', capSub: 'F/1.4 • QUANTUM TRAILS', ss: '1/30s', density: 'OIS VIRTUAL' },
            { key: 'scan', icon: '📄', title: 'SCAN DOC PRO', pill: '📄 AUTO-ENCUADRE HOMOGRÁFICO & OCR', color: '#00D2FF', capText: 'SCAN DOC', capSub: 'F/1.4 • HOMOGRAPHY OCR', ss: '1/500s', density: 'OCR MATRIX' },
            { key: 'night', icon: '🌙', title: 'NIGHTOGRAPHY', pill: '🌙 MULTI-FRAME STACK & DEEP-SKY BOOST', color: '#5E5CE6', capText: 'NIGHT PRO', capSub: 'F/1.4 • MULTI-FRAME RAW', ss: '1/4s', density: 'DEEP-SKY' },
            { key: 'macro', icon: '🔍', title: 'MACRO PRO', pill: '🔍 FOCUS PEAKING & DEEP FOCUS STACK', color: '#30D158', capText: 'MACRO PRO', capSub: 'F/1.4 • FOCUS PEAKING', ss: '1/1000s', density: '10x LUPA' },
            { key: 'bokeh', icon: '🎭', title: 'RETRATO BOKEH', pill: '🎭 APERTURA ÓPTICA & IRIS SHAPER', color: '#FF2D55', capText: 'BOKEH f/1.2', capSub: 'F/1.2 • 85MM CINEMA IRIS', ss: '1/500s', density: 'IRIS SHAPER' },
            { key: 'lonas', icon: '🎪', title: 'LONAS 3D', pill: '🎪 BASTIDOR PTR & TÚNEL DE VIENTO 110 km/h', color: '#FFD60A', capText: 'LONAS 3D', capSub: 'F/1.4 • PTR WIND TUNNEL', ss: '1/500s', density: 'PTR 110km/h' },
            { key: 'stickers', icon: '🎨', title: 'WALLPAPERS STICKERS', pill: '🎨 TROQUELADO 3D & AMOLED BLACK', color: '#BF5AF2', capText: 'DIE-CUT 3D', capSub: 'F/1.4 • AMOLED 19.5:9', ss: '1/500s', density: 'AMOLED BLK' },
            { key: 'imprenta', icon: '🖨️', title: 'IMPRENTA PDF', pill: '🖨️ PREPRENSA CMYK & FOGRA39 PROOF', color: '#FF2D85', capText: 'PREPRESS', capSub: 'F/1.4 • CMYK FOGRA39', ss: '1/500s', density: 'FOGRA39' },
            { key: 'cine', icon: '🎬', title: 'CINE SCOPE V10', pill: '🎬 ANAMÓRFICO 2.39:1 & BLUE STREAK FLARE', color: '#FF0055', capText: 'SCOPE 2.39', capSub: 'F/1.4 • ANAMORPHIC DCI', ss: '1/48s', density: 'DCI 2.39:1' },
            { key: 'raw', icon: '🎞️', title: 'ESTUDIO RAW', pill: '🎞️ REVELADO DIGITAL DE 14-BIT & HISTOGRAMA', color: '#FF9F0A', capText: 'RAW STUDIO', capSub: 'F/1.4 • 14-BIT DNG PROFILE', ss: '1/250s', density: '14-BIT DNG' },
            { key: 'svg', icon: '📐', title: 'SVG LOGOS', pill: '📐 VECTORIZADOR CAD & CÓDIGO XML', color: '#00FFC8', capText: 'SVG CAD', capSub: 'F/1.4 • BEZIER AUTOTRACE', ss: '1/500s', density: 'XML BEZIER' },
            { key: 'motion', icon: '⚡', title: 'VIDEO MOTION', pill: '⚡ FLUJO ÓPTICO & ESTELAS 60 FPS', color: '#FF9500', capText: 'MOTION V9', capSub: 'F/1.4 • OPTICAL FLOW 60FPS', ss: '1/120s', density: '60 FPS FLOW' },
            { key: 'depth', icon: '🛰️', title: 'DEPTH-MAP NPU', pill: '🛰️ Z-BUFFER 16-BIT & NUBE LIDAR', color: '#00F2FE', capText: 'DEPTH NPU', capSub: 'F/1.4 • DISPARITY 16-BIT', ss: '1/500s', density: 'Z-BUFFER' },
            { key: 'chef', icon: '👨‍🍳', title: 'CHEF LEAN V10', pill: '👨‍🍳 BÁSCULA NPU & AUDITORÍA DE MERMA', color: '#FF9500', capText: 'CHEF LEAN', capSub: 'F/1.4 • MEAT YIELD MATRIX', ss: '1/500s', density: '1.05 g/cm³' },
            { key: 'price', icon: '🏷️', title: 'VALUADOR HÍBRIDO V10', pill: '🏷️ TASACIÓN DE MERCADO & PÓLIZA COMERCIAL', color: '#63E6E2', capText: 'VALUADOR', capSub: 'F/1.4 • COMMERCIAL SCAN', ss: '1/500s', density: 'TASACIÓN' },
            { key: 'ai', icon: '✨', title: 'GENERADOR AI V8', pill: '✨ DIFUSIÓN LATENTE & MORFOLOGÍA NEURONAL', color: '#FF007A', capText: 'NEURAL AI', capSub: 'F/1.4 • LATENT SYNTHESIS', ss: '1/500s', density: 'TENSOR NPU' },
            { key: 'dispatch', icon: '📦', title: 'DESPACHO COMERCIAL V2', pill: '📦 CUBICAJE IATA & MANIFIESTO LOGÍSTICO', color: '#00E676', capText: 'DESPACHO', capSub: 'F/1.4 • WAYBILL MATRIX', ss: '1/500s', density: 'IATA CBM' },
            { key: 'nanobot', icon: '🤖', title: 'NANO-BOT TÁCTICO V2', pill: '🤖 COPILOTO NEURONAL & MACROS EN RAM', color: '#00FFC8', capText: 'NANO-BOT', capSub: 'F/1.4 • TACTICAL COPILOT', ss: '1/1000s', density: 'LATENCY 11ms' },
            { key: 'vault', icon: '🏛️', title: 'ALMACÉN & GALERÍA V3', pill: '🏛️️ BÓVEDA SQLITE LOCAL & METADATOS FORENSES', color: '#00E5FF', capText: 'ALMACÉN', capSub: 'F/1.4 • VAULT STORAGE V3', ss: '1/500s', density: 'SQLITE LOCAL' }
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

        function applyActiveCardTheme(m, triggerModuleSwitch = false) {
            document.getElementById('moduleNameText').innerText = m.title;
            document.getElementById('statusDot').style.background = m.color;
            document.getElementById('contextPillText').innerText = m.pill;
            document.getElementById('contextPillText').style.color = m.color;
            document.getElementById('contextPillText').style.borderColor = `${m.color}66`;

            document.getElementById('masterShutterBtn').style.background = m.color;
            document.getElementById('masterShutterBtn').style.boxShadow = `0 0 22px ${m.color}88`;
            document.getElementById('shutterCorona').style.borderColor = m.color;

            document.getElementById('drawerDensity').innerText = `DENSITY: ${m.density}`;
            document.getElementById('drawerSS').innerText = `SS: ${m.ss}`;

            document.getElementById('dialCenterTitle').innerText = m.capText;
            document.getElementById('dialCenterTitle').style.color = m.color;
            document.getElementById('dialSubSpec').innerText = m.capSub;

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

            // Al cambiar de módulo: borde y sonido propio, SIN esporas
            if (triggerModuleSwitch) {
                triggerModuleSwitchProtocol(m.color, m.key);
            }
        }

        async function handleMasterCapture() {
            const curMod = moduleCatalog[activeCardIndex];
            triggerModuleSwitchProtocol(curMod.color, curMod.key);

            const b64 = hiddenCanvas.toDataURL('image/jpeg', 0.95);

            const res = await fetch('/bian/process/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image_base64: b64, prompt_analysis: `Captura ${curMod.title}` })
            });

            if (res.ok) {
                const data = await res.json();
                document.getElementById('thumbBox').innerHTML = `<img src="${getSafeAssetUrl(data.image_path)}" />`;
                openAssetDetail(data);
            }
        }

        async function updateThumb() {
            try {
                const res = await fetch('/bian/images/');
                const list = await res.json();
                if (list.length > 0) {
                    const last = list[list.length - 1];
                    document.getElementById('thumbBox').innerHTML = `<img src="${getSafeAssetUrl(last.image_path)}" />`;
                }
            } catch(e) {}
        }

        async function openGalleryModal() {
            document.getElementById('galleryModal').style.display = 'flex';
            await loadVaultAssets();
        }

        function closeGalleryModal() { document.getElementById('galleryModal').style.display = 'none'; }

        async function loadVaultAssets() {
            const container = document.getElementById('galleryGridContent');
            container.innerHTML = '<div style="color:#aaa; font-size:11px; padding:20px 0; text-align:center; grid-column:span 2;">Conectando a la bóveda...</div>';

            try {
                const res = await fetch('/bian/images/');
                allGalleryItems = await res.json();
                renderGalleryList(allGalleryItems);
            } catch(e) {
                container.innerHTML = '<div style="color:#FF3B30; padding:20px 0; text-align:center; grid-column:span 2;">Error en base de datos.</div>';
            }
        }

        function renderGalleryList(items) {
            const container = document.getElementById('galleryGridContent');
            container.innerHTML = '';
            if (items.length === 0) {
                container.innerHTML = '<div style="color:#666; font-size:11px; grid-column:span 2; text-align:center; padding:30px 0;">No hay activos registrados.</div>';
                return;
            }

            items.slice().reverse().forEach(img => {
                const card = document.createElement('div');
                card.className = 'gallery-card';
                card.onclick = () => openAssetDetail(img);
                const assetUrl = getSafeAssetUrl(img.image_path);

                card.innerHTML = `
                    <div class="gallery-card-img-wrapper">
                        <img src="${assetUrl}" loading="lazy" />
                    </div>
                    <div class="gallery-card-info">
                        <strong style="color:#00E5FF;">#${img.id}</strong>
                        <span>${(img.prompt_analysis || 'Asset').slice(0, 16)}</span>
                    </div>
                `;
                container.appendChild(card);
            });
        }

        function filterGallery(category, elem) {
            document.querySelectorAll('.vault-chip').forEach(c => c.classList.remove('active'));
            elem.classList.add('active');

            if (category === 'todos') {
                renderGalleryList(allGalleryItems);
            } else {
                const filtered = allGalleryItems.filter(item => 
                    (item.prompt_analysis || '').toLowerCase().includes(category.toLowerCase())
                );
                renderGalleryList(filtered);
            }
        }

        function openAssetDetail(item) {
            activeAssetItem = item;
            const assetUrl = getSafeAssetUrl(item.image_path);

            document.getElementById('assetDetailTitle').innerText = `INSPECCIÓN FORENSE #${item.id}`;
            document.getElementById('assetDetailImg').src = assetUrl;
            document.getElementById('assetDetailMeta').innerHTML = `
                <div>ID EN REGISTRO: #${item.id}</div>
                <div>ANÁLISIS: ${item.prompt_analysis || 'Captura'}</div>
                <div>ARCHIVO FÍSICO: ${item.image_path.split('/').pop()}</div>
                <div>ESTADO: ALMACENAMIENTO VERIFICADO (TERMUX)</div>
            `;
            document.getElementById('assetDetailModal').style.display = 'flex';
        }

        function closeAssetDetail() { document.getElementById('assetDetailModal').style.display = 'none'; }

        function downloadActiveAsset() {
            if (!activeAssetItem) return;
            const a = document.createElement('a');
            a.href = getSafeAssetUrl(activeAssetItem.image_path);
            a.download = `bian_asset_${activeAssetItem.id}.jpg`;
            a.click();
        }

        async function deleteActiveAsset() {
            if (!activeAssetItem) return;
            if (!confirm(`¿Eliminar permanentemente el Asset #${activeAssetItem.id}?`)) return;

            try {
                const res = await fetch(`/bian/images/${activeAssetItem.id}`, { method: 'DELETE' });
                if (res.ok) {
                    closeAssetDetail();
                    await loadVaultAssets();
                    updateThumb();
                } else {
                    alert('Error al intentar eliminar el activo.');
                }
            } catch(e) {
                alert('Fallo de conexión.');
            }
        }

        function openNanobot() { document.getElementById('nanobotModal').style.display = 'flex'; }
        function closeNanobot() { document.getElementById('nanobotModal').style.display = 'none'; }
        function clearRamMacro() {
            closeNanobot();
            spores = [];
            initSpores();
            triggerUnlockProtocol('#00E5FF');
            alert("✔ Búfer purgado. RAM optimizada.");
        }
    </script>
</body>
</html>"""

@router.get("/ui", response_class=HTMLResponse)
async def get_ui():
    return HTML_CONTENT

@router.post("/process/", response_model=ProcessedImage)
def process_image(payload: ImageCaptureRequest, session: Session = Depends(get_session)):
    filename = f"photo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    full_path = os.path.join(STORAGE_DIR, filename)

    header, encoded = payload.image_base64.split(",", 1) if "," in payload.image_base64 else ("", payload.image_base64)
    data = base64.b64decode(encoded)
    with open(full_path, "wb") as f:
        f.write(data)

    db_image = ProcessedImage(image_path=f"storage/bian/{filename}", prompt_analysis=payload.prompt_analysis)
    session.add(db_image)
    session.commit()
    session.refresh(db_image)
    return db_image

@router.get("/images/", response_model=list[ProcessedImage])
def list_images(session: Session = Depends(get_session)):
    return session.exec(select(ProcessedImage)).all()

@router.delete("/images/{image_id}")
def delete_image(image_id: int, session: Session = Depends(get_session)):
    db_image = session.get(ProcessedImage, image_id)
    if not db_image:
        raise HTTPException(status_code=404, detail="Imagen no encontrada")

    filename = os.path.basename(db_image.image_path)
    file_path = os.path.join(STORAGE_DIR, filename)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception:
            pass

    session.delete(db_image)
    session.commit()
    return {"status": "success", "deleted_id": image_id}
