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

# Directorio físico asegurado
STORAGE_DIR = os.path.abspath("storage/bian")
os.makedirs(STORAGE_DIR, exist_ok=True)

class ImageCaptureRequest(BaseModel):
    image_base64: str
    prompt_analysis: str = "Captura Master Suite V10"

# Endpoint directo y seguro para servir imágenes sin fallos de montaje
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
    <title>BIAN MASTER SUITE V10 - ALMACÉN V3</title>
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
            background: rgba(0, 229, 255, 0.08); border: 1px solid rgba(0, 229, 255, 0.3);
            color: #00E5FF; font-size: 10px; font-weight: 700; letter-spacing: 1.5px;
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
        .lens-cap-center { font-size: 10px; font-weight: 900; letter-spacing: 2px; color: #00E5FF; }
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

        #sporesMatrixCanvas {
            position: absolute; inset: 0; width: 100%; height: 100%; pointer-events: none; z-index: 52;
            opacity: 0; transition: opacity 0.8s cubic-bezier(0.16, 1, 0.3, 1);
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
        .hud-status-badge .dot { width: 7px; height: 7px; border-radius: 50%; background: #00E5FF; display: inline-block; }
        .top-action-btn {
            background: rgba(18, 18, 22, 0.72); border: 1px solid rgba(255, 255, 255, 0.15);
            color: #fff; font-size: 11px; font-weight: 600; padding: 6px 14px; border-radius: 20px;
            backdrop-filter: blur(10px); cursor: pointer; display: flex; align-items: center; gap: 4px;
        }

        .center-hud-overlay {
            position: absolute; top: 68px; left: 0; right: 0; z-index: 95;
            display: flex; flex-direction: column; align-items: center; gap: 8px; pointer-events: none;
        }
        .context-pill {
            background: rgba(18, 18, 22, 0.82); border: 1px solid rgba(0, 229, 255, 0.4);
            color: #00E5FF; font-size: 10px; font-weight: 800; letter-spacing: 0.8px;
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

        /* MODAL BÓVEDA & GALERÍA V3 */
        #galleryModal {
            display: none; position: fixed; inset: 0; z-index: 320; background: rgba(5, 7, 10, 0.98);
            backdrop-filter: blur(25px); flex-direction: column; padding: 18px;
        }
        .vault-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
        .vault-telemetry {
            display: flex; gap: 8px; font-family: monospace; font-size: 10px; color: #888;
            background: #090c10; padding: 6px 12px; border-radius: 12px; border: 1px solid #1c2430; margin-bottom: 12px;
        }
        .vault-filter-bar { display: flex; gap: 6px; overflow-x: auto; scrollbar-width: none; margin-bottom: 12px; }
        .vault-chip {
            padding: 5px 12px; font-size: 10px; font-weight: 800; border-radius: 14px;
            background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.15);
            color: #ccc; cursor: pointer; white-space: nowrap;
        }
        .vault-chip.active { background: #00E5FF; color: #000; border-color: #00E5FF; box-shadow: 0 0 8px rgba(0,229,255,0.5); }
        .gallery-grid {
            display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; overflow-y: auto; flex: 1; padding-bottom: 10px;
        }
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

        /* MODAL FORENSE DETALLADO */
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
    </style>
</head>
<body>
    <div class="edge-screen-border" id="screenEdgeBorder"></div>
    <div class="ambient-fade-light" id="ambientLightLayer"></div>

    <div id="lockscreen">
        <div class="pill-badge">• ALMACÉN & GALERÍA V3</div>
        <div class="brand-center">
            <div class="brand-title">BIAN</div>
            <div class="brand-subtitle">Vault Storage V3 Ultra</div>
        </div>
        <div class="lens-cap-assembly" id="lensCapUnlockBtn">
            <div class="lens-cap-disk" id="lensCapDisk">
                <div class="lens-cap-center">ALMACÉN</div>
                <div class="lens-cap-sub">F/1.4 • VAULT STORAGE</div>
            </div>
            <div class="lens-cap-hint">🔓 DESTAPAR LENTE</div>
        </div>
    </div>

    <div class="suite-view">
        <div id="videoContainer">
            <video id="webcam" autoplay playsinline></video>
            <canvas id="ghostScopeCanvas"></canvas>
            <canvas id="sporesMatrixCanvas"></canvas>
        </div>

        <div class="top-dock">
            <div class="hud-status-badge">
                <span class="dot"></span>
                <span id="moduleNameText">ALMACÉN & GALERÍA V3</span>
            </div>
            <div style="display: flex; gap: 6px;">
                <button class="top-action-btn" onclick="lockSuite()">🔒</button>
                <button class="top-action-btn" onclick="openGalleryModal()">🖼️ Almacén</button>
            </div>
        </div>

        <div class="center-hud-overlay">
            <div class="context-pill" id="contextPillText">BÓVEDA DE ACTIVOS V3 READY</div>
        </div>

        <div class="deck-stack-wrapper" id="deckStack" onclick="openHorizontalDock()"></div>
        <div id="horizontalDockBar"></div>

        <div class="bottom-bar">
            <div class="lens-switch-btn" onclick="toggleLens()">🔄</div>
            <div class="shutter-wrapper">
                <div class="shutter-corona"></div>
                <div class="shutter-btn" id="masterShutterBtn" onclick="handleMasterCapture()"></div>
            </div>
            <div class="gallery-thumb" id="thumbBox" onclick="openGalleryModal()"></div>
        </div>
    </div>

    <!-- MODAL BÓVEDA & GALERÍA V3 -->
    <div id="galleryModal">
        <div class="vault-header">
            <div style="font-size:14px; font-weight:900; color:#00E5FF;">🏛️ BÓVEDA & ALMACÉN SOBERANO V3</div>
            <button class="top-action-btn" onclick="closeGalleryModal()">✖ Cerrar</button>
        </div>
        <div class="vault-telemetry">
            <div>ASSETS: <strong id="vaultCountLabel" style="color:#fff;">0</strong></div>
            <div>|</div>
            <div>STATUS: <strong style="color:#30D158;">SQLITE ONLINE</strong></div>
        </div>
        <div class="vault-filter-bar">
            <button class="vault-chip active" onclick="filterGallery('todos', this)">Todos los Activos</button>
            <button class="vault-chip" onclick="filterGallery('despacho', this)">Despacho</button>
            <button class="vault-chip" onclick="filterGallery('chef', this)">Chef Lean</button>
            <button class="vault-chip" onclick="filterGallery('valuador', this)">Valuador</button>
        </div>
        <div class="gallery-grid" id="galleryGridContent"></div>
    </div>

    <!-- MODAL INSPECCIÓN FORENSE -->
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
            <button class="btn-asset-action" style="background:#FF3B30; color:#fff;" onclick="deleteActiveAsset()">🗑️ Eliminar Registro</button>
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
            const col = "#00E5FF";

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

        let unlocked = false;
        function unlockSuite() {
            if (unlocked) return;
            unlocked = true;
            document.getElementById('lockscreen').classList.add('unlocked');
            triggerUniversalEntryProtocol('#00E5FF');
        }

        function lockSuite() {
            unlocked = false;
            document.getElementById('lockscreen').classList.remove('unlocked');
        }
        document.getElementById('lensCapUnlockBtn').addEventListener('click', unlockSuite);

        // Extractor unificado del nombre de archivo físico
        function getSafeAssetUrl(rawPath) {
            if (!rawPath) return '';
            const filename = rawPath.split('/').pop();
            return `/bian/asset/${filename}`;
        }

        async function handleMasterCapture() {
            triggerUniversalEntryProtocol('#00E5FF');
            const b64 = hiddenCanvas.toDataURL('image/jpeg', 0.95);

            const res = await fetch('/bian/process/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image_base64: b64, prompt_analysis: 'Captura Almacén V3' })
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
                document.getElementById('vaultCountLabel').innerText = allGalleryItems.length;
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

    # Guardar ruta relativa estandarizada
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
