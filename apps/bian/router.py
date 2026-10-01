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
    prompt_analysis: str = "Captura Valuador Hibrido V10"

HTML_CONTENT = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>BIAN MASTER SUITE V10 PRO - VALUADOR HÍBRIDO</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', Roboto, monospace; -webkit-tap-highlight-color: transparent; }
        body { background: #000; color: #fff; height: 100vh; width: 100vw; overflow: hidden; position: fixed; }

        .edge-screen-border {
            position: fixed; inset: 0; pointer-events: none; z-index: 150;
            border: 3px solid transparent; box-shadow: inset 0 0 0px transparent;
            transition: border-color 1.5s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 1.5s cubic-bezier(0.16, 1, 0.3, 1);
        }

        .ambient-fade-light {
            position: fixed; inset: 0; pointer-events: none; z-index: 140;
            background: radial-gradient(circle at 50% 50%, rgba(255,255,255,0.25) 0%, transparent 70%);
            opacity: 0; transition: opacity 1.5s cubic-bezier(0.16, 1, 0.3, 1);
        }
        .ambient-fade-light.flash { opacity: 1; transition: opacity 0.05s ease-in; }

        /* LOCKSCREEN TAPA 35MM */
        #lockscreen {
            position: fixed; inset: 0; background: #050608; z-index: 200;
            display: flex; flex-direction: column; align-items: center; justify-content: space-between;
            padding: 45px 20px 35px 20px; transition: transform 0.6s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.6s ease;
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
        .brand-subtitle { font-size: 15px; font-weight: 600; color: #fff; margin-bottom: 15px; }

        .lens-cap-assembly {
            display: flex; flex-direction: column; align-items: center; cursor: pointer; touch-action: none; margin-bottom: 20px;
        }
        .lens-cap-disk {
            width: 90px; height: 90px; border-radius: 50%;
            background: radial-gradient(circle, #25262c 0%, #111216 70%, #08080a 100%);
            border: 3px solid #333640; box-shadow: 0 8px 30px rgba(0,0,0,0.9);
            display: flex; flex-direction: column; align-items: center; justify-content: center;
            position: relative; transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);
        }
        .lens-cap-center { font-size: 10px; font-weight: 900; letter-spacing: 2px; color: #63E6E2; }
        .lens-cap-sub { font-size: 7px; color: #777; margin-top: 2px; }
        .lens-cap-hint { font-size: 10px; font-weight: 800; color: #aaa; margin-top: 10px; letter-spacing: 1px; }

        /* VIEWPORT Y VISOR */
        .suite-view { width: 100vw; height: 100vh; position: relative; background: #000; overflow: hidden; display: flex; flex-direction: column; }
        #videoContainer { width: 100%; height: 100%; position: relative; overflow: hidden; }
        video { width: 100%; height: 100%; object-fit: cover; }

        #ghostScopeCanvas {
            position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover;
            pointer-events: none; z-index: 45; opacity: 0; mix-blend-mode: screen; transition: opacity 0.3s;
        }
        #ghostScopeCanvas.active { opacity: 0.75; }

        /* 1. RETÍCULA DE ESCANEO DE ACTIVOS */
        #valuationReticleCanvas {
            position: absolute; inset: 0; width: 100%; height: 100%; pointer-events: none; z-index: 52;
        }

        /* 1. HUD VALUADOR HÍBRIDO V10 */
        .val-hud-container {
            display: none; position: absolute; top: 120px; left: 16px; right: 16px;
            z-index: 60; flex-direction: column; align-items: center; gap: 8px; pointer-events: auto;
        }
        .val-status-pill {
            display: flex; gap: 10px; align-items: center; background: rgba(8, 24, 26, 0.88);
            border: 1px solid rgba(99, 230, 226, 0.45); border-radius: 20px; padding: 5px 14px;
            backdrop-filter: blur(14px); font-size: 11px; font-weight: 800; color: #63E6E2;
        }
        .val-category-selector {
            display: flex; gap: 6px; background: rgba(6, 18, 20, 0.8);
            border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 20px; padding: 4px 8px;
            backdrop-filter: blur(12px);
        }
        .val-chip-btn {
            padding: 3px 9px; font-size: 10px; font-weight: 800; border-radius: 12px;
            color: #888; background: transparent; border: none; cursor: pointer; transition: all 0.2s;
        }
        .val-chip-btn.active { background: #63E6E2; color: #000; box-shadow: 0 0 8px rgba(99,230,226,0.6); }

        .aero-hud-overlay {
            position: absolute; inset: 0; pointer-events: none; z-index: 50;
            display: flex; flex-direction: column; justify-content: space-between; padding: 75px 18px 185px 18px;
        }
        .horizon-line {
            position: absolute; top: 50%; left: 25%; width: 50%; height: 1px;
            background: linear-gradient(90deg, transparent, rgba(99, 230, 226, 0.6), transparent);
        }
        .hud-telemetry-corner {
            display: flex; justify-content: space-between; font-family: monospace;
            font-size: 10px; font-weight: 800; color: rgba(255, 255, 255, 0.7);
        }
        .telemetry-tag {
            background: rgba(14, 16, 20, 0.65); padding: 3px 8px; border-radius: 6px;
            border: 1px solid rgba(255, 255, 255, 0.1); backdrop-filter: blur(8px);
        }

        /* TOP DOCK */
        .top-dock {
            position: absolute; top: 16px; left: 16px; right: 16px; z-index: 100;
            display: flex; justify-content: space-between; align-items: center;
        }
        .hud-status-badge {
            background: rgba(18, 18, 22, 0.72); border: 1px solid rgba(255, 255, 255, 0.12);
            color: #fff; font-size: 11px; font-weight: 700; padding: 6px 14px; border-radius: 20px;
            backdrop-filter: blur(10px); display: flex; align-items: center; gap: 6px;
        }
        .hud-status-badge .dot { width: 7px; height: 7px; border-radius: 50%; background: #63E6E2; display: inline-block; }
        .top-action-btn {
            background: rgba(18, 18, 22, 0.72); border: 1px solid rgba(255, 255, 255, 0.15);
            color: #fff; font-size: 11px; font-weight: 600; padding: 6px 14px; border-radius: 20px;
            backdrop-filter: blur(10px); cursor: pointer; display: flex; align-items: center; gap: 4px;
        }
        #botToggleBtn {
            border-color: rgba(99,230,226,0.4); color: #63E6E2; transition: all 0.4s ease; min-width: 155px; justify-content: center;
        }

        .ghost-scope-btn {
            background: rgba(18, 18, 22, 0.75); border: 1px solid rgba(99, 230, 226, 0.35);
            color: #63E6E2; font-size: 10px; font-weight: 800; padding: 6px 11px; border-radius: 18px;
            cursor: pointer; backdrop-filter: blur(8px);
        }
        .ghost-scope-btn.active { background: #63E6E2; color: #000; box-shadow: 0 0 14px rgba(99,230,226,0.6); }

        .center-hud-overlay {
            position: absolute; top: 68px; left: 0; right: 0; z-index: 95;
            display: flex; flex-direction: column; align-items: center; gap: 8px; pointer-events: none;
        }
        .context-pill {
            background: rgba(18, 18, 22, 0.82); border: 1px solid rgba(99, 230, 226, 0.4);
            color: #63E6E2; font-size: 10px; font-weight: 800; letter-spacing: 0.8px;
            padding: 4px 14px; border-radius: 20px; backdrop-filter: blur(10px); text-transform: uppercase;
        }

        .focus-ring {
            position: absolute; width: 84px; height: 84px; border-radius: 50%;
            border: 1.5px solid rgba(255, 255, 255, 0.85); box-shadow: 0 0 12px rgba(255, 255, 255, 0.4);
            pointer-events: none; z-index: 90; display: flex; flex-direction: column;
            align-items: center; justify-content: space-between; padding: 4px 0;
            transform: translate(-50%, -50%) scale(0.9); opacity: 0; transition: opacity 0.3s, transform 0.2s;
        }
        .focus-ring.active { opacity: 1; transform: translate(-50%, -50%) scale(1); }

        .hud-zoom-tag {
            position: absolute; bottom: 155px; left: 24px; z-index: 100;
            background: rgba(20, 20, 24, 0.82); border: 1px solid rgba(255, 255, 255, 0.18);
            border-radius: 18px; padding: 5px 12px; font-size: 12px; font-weight: 800; color: #63E6E2;
            cursor: pointer; backdrop-filter: blur(12px);
        }

        /* MODO CARTAS */
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

        /* DOCK HORIZONTAL */
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

        /* OBTURADOR VALUADOR */
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
            width: 72px; height: 72px; border-radius: 50%; background: #63E6E2;
            border: 4px solid #fff; box-shadow: 0 0 22px rgba(99, 230, 226, 0.55); cursor: pointer;
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

        /* GADGET Y PANELES */
        #floatingGadget {
            position: fixed; top: 180px; left: 14px; width: 48px; height: 48px;
            border-radius: 50%; background: #0c0d12; border: 2px solid #63E6E2;
            box-shadow: 0 6px 18px rgba(99, 230, 226, 0.4); z-index: 250;
            display: flex; align-items: center; justify-content: center; font-size: 20px; cursor: grab;
        }
        #floatingPanel {
            display: none; position: fixed; inset: 100px 18px 120px 18px; z-index: 260;
            background: rgba(10, 12, 16, 0.96); border: 1px solid #63E6E2; border-radius: 20px;
            backdrop-filter: blur(25px); flex-direction: column; padding: 16px;
        }
        .float-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }

        /* MESA DE EDICIÓN POST-VALUACIÓN & CERTIFICADO COMERCIAL */
        #postEditModal {
            display: none; position: fixed; inset: 0; z-index: 300; background: rgba(6, 7, 10, 0.96);
            backdrop-filter: blur(20px); flex-direction: column; padding: 20px 18px 25px 18px;
        }
        .edit-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
        .edit-title { font-size: 14px; font-weight: 800; color: #63E6E2; }
        .edit-close-btn { background: #222; border: 1px solid #444; color: #fff; padding: 5px 12px; border-radius: 14px; font-size: 11px; cursor: pointer; }
        
        .edit-preview-box {
            flex: 1; border-radius: 16px; overflow: hidden; background: #000; border: 1px solid #222;
            display: flex; align-items: center; justify-content: center; position: relative;
        }
        .edit-preview-box img { max-width: 100%; max-height: 100%; object-fit: contain; }

        /* 3. INNOVACIÓN: PÓLIZA-CERTIFICADO COMERCIAL EN VIVO */
        #valCertificateBox {
            display: none; position: absolute; inset: 12px; background: rgba(8, 14, 18, 0.95);
            border: 1px solid #63E6E2; border-radius: 12px; padding: 16px; font-family: monospace;
            font-size: 11px; color: #eee; flex-direction: column; justify-content: space-between; z-index: 310;
        }
        .cert-row { display: flex; justify-content: space-between; border-bottom: 1px solid #1a2830; padding: 6px 0; }
        .cert-total { font-size: 13px; font-weight: 900; color: #63E6E2; }

        .edit-tools-panel { margin-top: 14px; display: flex; flex-direction: column; gap: 10px; }
        .tool-row { display: flex; gap: 8px; overflow-x: auto; scrollbar-width: none; }
        .tool-chip {
            background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.15);
            padding: 8px 14px; border-radius: 20px; font-size: 11px; font-weight: 700; color: #ddd; cursor: pointer;
        }
        .tool-chip.active { border-color: #63E6E2; color: #63E6E2; background: rgba(99,230,226,0.12); }
        .btn-export-master {
            background: linear-gradient(90deg, #63E6E2, #00D2FF); color: #000; font-size: 13px;
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

        #nanobotModal {
            display: none; position: fixed; inset: 0; z-index: 330; background: rgba(5, 6, 8, 0.95);
            backdrop-filter: blur(25px); flex-direction: column; padding: 20px; justify-content: space-between;
        }
        .bot-bubble { background: #121318; border: 1px solid rgba(99,230,226,0.3); border-radius: 16px; padding: 16px; font-size: 13px; line-height: 1.5; color: #eee; margin-top: 15px; }
        .bot-actions { display: flex; flex-direction: column; gap: 8px; margin-top: 16px; }
        .bot-btn {
            background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.15); color: #fff;
            padding: 12px; border-radius: 12px; font-size: 12px; font-weight: 700; text-align: left; cursor: pointer;
        }
    </style>
</head>
<body>
    <div class="edge-screen-border" id="screenEdgeBorder"></div>
    <div class="ambient-fade-light" id="ambientLightLayer"></div>

    <!-- LOCKSCREEN CON TAPA 35MM -->
    <div id="lockscreen">
        <div class="pill-badge">• BIAN MASTER SUITE V10</div>
        <div class="brand-center">
            <div class="brand-title">BIAN</div>
            <div class="brand-subtitle">Valuador Híbrido V10 Ultra</div>
            <div style="font-size:11px; color:#777; max-width:280px; margin:0 auto; line-height:1.4;">
                Tasación Comercial • Bandas de Margen Bruto • Póliza Oficial
            </div>
        </div>
        <div class="lens-cap-assembly" id="lensCapUnlockBtn">
            <div class="lens-cap-disk" id="lensCapDisk">
                <div class="lens-cap-center">VALUADOR</div>
                <div class="lens-cap-sub">F/1.4 • 35MM ASSET APPRAISAL</div>
            </div>
            <div class="lens-cap-hint">🔓 DESTAPAR LENTE</div>
        </div>
    </div>

    <!-- GADGET FLOTANTE -->
    <div id="floatingGadget" title="Arrastra o toca para abrir taller">⚡</div>

    <!-- PANEL FLOTANTE -->
    <div id="floatingPanel">
        <div class="float-header">
            <div style="font-size:13px; font-weight:800; color:#63E6E2;">⚡ TALLER TÁCTICO FLOTANTE</div>
            <button class="edit-close-btn" onclick="toggleFloatingPanel()">✖ Cerrar</button>
        </div>
        <div style="flex:1; overflow-y:auto; font-size:12px; color:#aaa; display:flex; flex-direction:column; gap:10px;">
            <div style="background:#14151b; padding:12px; border-radius:12px; border:1px solid #222;">
                <div style="color:#fff; font-weight:700; margin-bottom:4px;" id="floatModTitle">MODO ACTIVO</div>
                <div id="floatModDesc">Motor de cotización multimodal y análisis de margen comercial listos.</div>
            </div>
            <div class="bot-actions" id="floatActionList"></div>
        </div>
    </div>

    <!-- VIEWPORT CON RETÍCULA DE VALUACIÓN DE ACTIVOS -->
    <div class="suite-view" id="viewportArea">
        <div id="videoContainer">
            <video id="webcam" autoplay playsinline></video>
            <canvas id="ghostScopeCanvas"></canvas>
            <!-- 1. RETÍCULA DE ESCANEO DE ACTIVOS -->
            <canvas id="valuationReticleCanvas"></canvas>
        </div>

        <!-- 1. HUD VALUADOR HÍBRIDO V10 -->
        <div class="val-hud-container" id="valHud">
            <div class="val-status-pill">
                <span id="valMarketLabel">🏷️ MERCADO: $1,450 MXN</span>
                <span style="color:#888;">|</span>
                <span id="valLiquidityLabel">LIQUIDEZ: 85%</span>
                <span style="color:#888;">|</span>
                <span style="color:#30D158;">MARGEN: 42%</span>
            </div>
            <div class="val-category-selector">
                <button class="val-chip-btn active" onclick="setAssetCategory('tech_device', 1450, 0.45, this)">Electrónica / Gadgets</button>
                <button class="val-chip-btn" onclick="setAssetCategory('industrial_tool', 2200, 0.38, this)">Herramienta / PTR</button>
                <button class="val-chip-btn" onclick="setAssetCategory('apparel_merch', 650, 0.55, this)">Textil / Merch</button>
            </div>
        </div>

        <!-- HUD AEROESPACIAL -->
        <div class="aero-hud-overlay">
            <div class="hud-telemetry-corner">
                <div class="telemetry-tag" id="telCondition">ESTADO: GRADO A (9.5/10)</div>
                <div class="telemetry-tag" id="telDeprec">DEPRECIACIÓN: -8% AÑO</div>
                <div class="telemetry-tag" id="telISO">ISO: 100 BASE</div>
                <div class="telemetry-tag" id="telShutter">SS: 1/500s</div>
            </div>

            <div class="horizon-line" id="horizonGyro"></div>

            <div class="hud-telemetry-corner" style="justify-content: flex-end; gap: 8px;">
                <div class="telemetry-tag" style="color:#63E6E2;" id="telValStatus">APPRAISAL: READY</div>
                <div class="telemetry-tag">SNAPDRAGON 8G2 NPU</div>
            </div>
        </div>

        <div class="focus-ring" id="focusRing">
            <div class="focus-lock-icon">🔒</div>
            <div class="focus-sun-icon">☀️</div>
        </div>

        <div class="top-dock">
            <div class="hud-status-badge" id="moduleTitleBadge">
                <span class="dot" id="statusDot"></span>
                <span id="moduleNameText">VALUADOR HÍBRIDO V10</span>
            </div>
            <div style="display: flex; gap: 6px;">
                <button class="ghost-scope-btn" id="scopeToggleBtn" onclick="toggleGhostScope()">
                    👁️ ESPECTRO
                </button>
                <button class="top-action-btn" onclick="lockSuite()">🔒</button>
                <button class="top-action-btn" id="botToggleBtn" onclick="openNanobot()">✨ Nano-Bot</button>
            </div>
        </div>

        <div class="center-hud-overlay" id="centerHud">
            <div class="context-pill" id="contextPillText">🏷️ VALUADOR HÍBRIDO: TASACIÓN COMERCIAL MULTIMODAL</div>
        </div>

        <div class="hud-zoom-tag" id="zoomChip" onclick="cycleZoomLevel()">
            🔍 <span id="zoomLabel">1x</span>
        </div>

        <!-- BARAJA DE CARTAS -->
        <div class="deck-stack-wrapper" id="deckStack" onclick="openHorizontalDock()"></div>

        <!-- DOCK HORIZONTAL FLOTANTE -->
        <div id="horizontalDockBar"></div>

        <!-- OBTURADOR VALUADOR -->
        <div class="bottom-bar">
            <div class="lens-switch-btn" onclick="toggleLens()">🔄</div>
            <div class="shutter-wrapper">
                <div class="shutter-corona" id="shutterCorona"></div>
                <div class="shutter-btn" id="valShutterBtn" onclick="handleValuationCaptureTrigger()"></div>
            </div>
            <div class="gallery-thumb" id="thumbBox" onclick="openGalleryModal()"></div>
        </div>
    </div>

    <!-- MESA DE EDICIÓN POST-VALUACIÓN -->
    <div id="postEditModal">
        <div class="edit-header">
            <div class="edit-title" id="editModalTitle">🏷️ VALUACIÓN COMERCIAL V10</div>
            <button class="edit-close-btn" onclick="closeEditModal()">✖ Volver</button>
        </div>
        <div class="edit-preview-box">
            <img id="editImagePreview" src="" alt="Valuation Frame" />
            <!-- 3. INNOVACIÓN: PÓLIZA-CERTIFICADO DE TASACIÓN -->
            <div id="valCertificateBox">
                <div style="text-align:center; font-weight:900; color:#63E6E2; font-size:12px; margin-bottom:8px;">
                    === CERTIFICADO DE TASACIÓN COMERCIAL BIAN ===
                </div>
                <div class="cert-row"><span>ACTIVO IDENTIFICADO:</span><strong id="certCategoryName">Electrónica / Gadgets</strong></div>
                <div class="cert-row"><span>ESTADO FÍSICO / COSMÉTICO:</span><strong id="certConditionGrade">Grado A (9.5/10)</strong></div>
                <div class="cert-row"><span>PRECIO COMPRA REMATE (OPORTUNIDAD):</span><strong id="certBuyPrice">$797.50 MXN</strong></div>
                <div class="cert-row"><span>VALOR PROMEDIO MERCADO:</span><strong id="certMarketPrice">$1,450.00 MXN</strong></div>
                <div class="cert-row"><span>PRECIO VENTA SUGERIDO EN MOSTRADOR:</span><strong id="certSellPrice">$1,380.00 MXN</strong></div>
                <div class="cert-row cert-total"><span>MARGEN BRUTO ESTIMADO:</span><strong id="certMarginPercent">42.2% ($582.50 MXN)</strong></div>
                <div style="font-size:9px; color:#777; text-align:center; margin-top:8px;">Trazabilidad algorítmica SQLite Local • Valuación Soberana</div>
            </div>
        </div>
        <div class="edit-tools-panel">
            <div class="tool-row" id="moduleToolRow">
                <div class="tool-chip active" onclick="switchValView('preview', this)">📷 Activo Evaluado</div>
                <div class="tool-chip" onclick="switchValView('certificate', this)">📜 Póliza de Tasación</div>
                <div class="tool-chip" onclick="applyValFilter('highlight_asset', this)">⚡ Realce de Sellos/Detalles</div>
                <div class="tool-chip" onclick="applyValFilter('commercial_clean', this)">🏪 Modo Catálogo Limpio</div>
            </div>
            <button class="btn-export-master" onclick="exportEditedResult()">
                💾 EXPORTAR CERTIFICADO COMERCIAL HD
            </button>
        </div>
    </div>

    <!-- GALERÍA SOBERANA -->
    <div id="galleryModal">
        <div class="edit-header">
            <div class="edit-title" style="color:#00FFC8;">🖼️ GALERÍA SOBERANA (SQLITE LOCAL)</div>
            <button class="edit-close-btn" onclick="closeGalleryModal()">✖ Cerrar</button>
        </div>
        <div class="gallery-grid" id="galleryGridContent"></div>
    </div>

    <!-- NANO-BOT ASISTENTE -->
    <div id="nanobotModal">
        <div>
            <div class="edit-header">
                <div class="edit-title" style="color:#00FFC8;">✨ NANO-BOT TÁCTICO V10</div>
                <button class="edit-close-btn" onclick="closeNanobot()">✖ Cerrar</button>
            </div>
            <div class="bot-bubble" id="botMessageText">Analizando activo comercial y dispersión de precios...</div>
            <div class="bot-actions" id="botActionList"></div>
        </div>
        <div style="font-size:10px; color:#555; text-align:center;">IA Soberana local operando en Snapdragon 8 Gen 2</div>
    </div>

    <canvas id="hiddenBufferCanvas" style="display:none;"></canvas>
    <!-- CANVAS DE COMPOSICIÓN COMERCIAL -->
    <canvas id="valuationRenderCanvas" style="display:none;"></canvas>

    <script>
        const video = document.getElementById('webcam');
        const hiddenCanvas = document.getElementById('hiddenBufferCanvas');
        const ghostCanvas = document.getElementById('ghostScopeCanvas');
        const ghostCtx = ghostCanvas.getContext('2d');
        const reticleCanvas = document.getElementById('valuationReticleCanvas');
        const reticleCtx = reticleCanvas.getContext('2d');
        const valCanvas = document.getElementById('valuationRenderCanvas');
        const valCtx = valCanvas.getContext('2d');
        const focusRing = document.getElementById('focusRing');
        let audioCtx = null;
        let facingMode = 'environment';
        let currentZoomIndex = 1;
        const zoomLevels = [0.6, 1.0, 2.0];
        let isGhostScopeOn = false;

        /* ESTADO VALUADOR HÍBRIDO V10 */
        let currentCategoryName = "Electrónica / Gadgets";
        let baseMarketPrice = 1450;
        let targetMargin = 0.45;
        let processedValDataUrl = null;

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
                requestAnimationFrame(processVideoPipeline);
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

        /* HORIZONTE ARTIFICIAL */
        window.addEventListener('deviceorientation', (e) => {
            if (e.gamma !== null) {
                const angle = Math.max(-30, Math.min(30, e.gamma));
                document.getElementById('horizonGyro').style.transform = `rotate(${angle}deg)`;
            }
        });

        /* 1. PIPELINE DE RETÍCULA DE ESCANEO DE ACTIVOS EN TIEMPO REAL */
        let frameCount = 0;
        function processVideoPipeline() {
            if (video.readyState >= 2) {
                if (hiddenCanvas.width !== video.videoWidth) {
                    hiddenCanvas.width = video.videoWidth || 640;
                    hiddenCanvas.height = video.videoHeight || 480;
                    valCanvas.width = hiddenCanvas.width;
                    valCanvas.height = hiddenCanvas.height;
                    reticleCanvas.width = window.innerWidth;
                    reticleCanvas.height = window.innerHeight;
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

                // Renderizar retícula de valuador si está activo
                const curMod = moduleCatalog[activeCardIndex];
                if (curMod.key === 'price') {
                    renderValuationScannerGrid();
                } else {
                    reticleCtx.clearRect(0, 0, reticleCanvas.width, reticleCanvas.height);
                }
            }
            requestAnimationFrame(processVideoPipeline);
        }

        function renderValuationScannerGrid() {
            reticleCtx.clearRect(0, 0, reticleCanvas.width, reticleCanvas.height);
            const w = reticleCanvas.width;
            const h = reticleCanvas.height;

            const boxW = w * 0.68;
            const boxH = h * 0.36;
            const bx = (w - boxW) / 2;
            const by = (h - boxH) / 2;

            // Marco de escaneo de producto en turquesa financiero
            reticleCtx.strokeStyle = "#63E6E2";
            reticleCtx.lineWidth = 1.5;
            reticleCtx.strokeRect(bx, by, boxW, boxH);

            // Esquinas tipo colimador láser
            const len = 20;
            reticleCtx.strokeStyle = "#00D2FF";
            reticleCtx.lineWidth = 3.5;
            // TL
            reticleCtx.beginPath(); reticleCtx.moveTo(bx, by + len); reticleCtx.lineTo(bx, by); reticleCtx.lineTo(bx + len, by); reticleCtx.stroke();
            // TR
            reticleCtx.beginPath(); reticleCtx.moveTo(bx + boxW - len, by); reticleCtx.lineTo(bx + boxW, by); reticleCtx.lineTo(bx + boxW, by + len); reticleCtx.stroke();
            // BL
            reticleCtx.beginPath(); reticleCtx.moveTo(bx, by + boxH - len); scaleCtx = reticleCtx; reticleCtx.lineTo(bx, by + boxH); reticleCtx.lineTo(bx + len, by + boxH); reticleCtx.stroke();
            // BR
            reticleCtx.beginPath(); reticleCtx.moveTo(bx + boxW - len, by + boxH); reticleCtx.lineTo(bx + boxW, by + boxH); reticleCtx.lineTo(bx + boxW, by + boxH - len); reticleCtx.stroke();

            // Línea de escaneo láser animada vertical
            const scanY = by + (Math.sin(Date.now() * 0.003) * 0.5 + 0.5) * boxH;
            reticleCtx.strokeStyle = "rgba(99, 230, 226, 0.7)";
            reticleCtx.lineWidth = 2;
            reticleCtx.beginPath();
            reticleCtx.moveTo(bx + 4, scanY);
            reticleCtx.lineTo(bx + boxW - 4, scanY);
            reticleCtx.stroke();

            // Etiqueta de tasación
            reticleCtx.fillStyle = "#63E6E2";
            reticleCtx.font = "bold 10px monospace";
            reticleCtx.fillText("ESCANEO DE VALORACIÓN ACTIVO", bx + 6, by - 8);
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

        /* 2. TRABAJO PESADO: TASACIÓN COMERCIAL Y CÁLCULO DE MARGEN */
        function setAssetCategory(key, marketPrice, margin, elem) {
            baseMarketPrice = marketPrice;
            targetMargin = margin;
            currentCategoryName = elem.innerText;
            document.querySelectorAll('.val-chip-btn').forEach(b => b.classList.remove('active'));
            elem.classList.add('active');

            document.getElementById('valMarketLabel').innerText = `🏷️ MERCADO: $${marketPrice} MXN`;
            document.getElementById('valLiquidityLabel').innerText = `LIQUIDEZ: ${(80 + Math.random() * 10).toFixed(0)}%`;
        }

        async function handleValuationCaptureTrigger() {
            const curMod = moduleCatalog[activeCardIndex];
            if (curMod.key === 'price') {
                executeValuationCapture();
            } else {
                captureStandardZSL();
            }
        }

        async function executeValuationCapture() {
            const flash = document.getElementById('ambientLightLayer');
            flash.classList.add('flash');
            setTimeout(() => flash.classList.remove('flash'), 60);
            playCashChirpSound();

            document.getElementById('telValStatus').innerText = 'APPRAISAL: COMPUTING';

            // Lienzo con el activo evaluado
            valCtx.drawImage(hiddenCanvas, 0, 0);

            // Cálculos comerciales paramétricos
            const buyOpportunityPrice = Math.round(baseMarketPrice * (1 - targetMargin));
            const suggestedSellPrice = Math.round(baseMarketPrice * 0.95);
            const grossProfit = suggestedSellPrice - buyOpportunityPrice;
            const grossMarginPercent = ((grossProfit / suggestedSellPrice) * 100).toFixed(1);

            // Actualizar datos de la póliza
            document.getElementById('certCategoryName').innerText = currentCategoryName;
            document.getElementById('certConditionGrade').innerText = "Grado A (9.5/10)";
            document.getElementById('certBuyPrice').innerText = `$${buyOpportunityPrice}.00 MXN`;
            document.getElementById('certMarketPrice').innerText = `$${baseMarketPrice}.00 MXN`;
            document.getElementById('certSellPrice').innerText = `$${suggestedSellPrice}.00 MXN`;
            document.getElementById('certMarginPercent').innerText = `${grossMarginPercent}% ($${grossProfit}.00 MXN)`;

            // Cintillo grabado sobre la foto
            valCtx.fillStyle = "rgba(6, 14, 18, 0.78)";
            valCtx.fillRect(10, valCanvas.height - 45, valCanvas.width - 20, 35);
            valCtx.fillStyle = "#63E6E2";
            valCtx.font = "bold 13px monospace";
            valCtx.fillText(`VALUACIÓN BIAN • ${currentCategoryName} • COMPRA: $${buyOpportunityPrice} • VENTA: $${suggestedSellPrice} • MG: ${grossMarginPercent}%`, 20, valCanvas.height - 22);

            processedValDataUrl = valCanvas.toDataURL('image/jpeg', 0.95);

            const res = await fetch('/bian/process/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image_base64: processedValDataUrl, prompt_analysis: `Valuador Híbrido ${currentCategoryName} $${baseMarketPrice} V10` })
            });

            if (res.ok) {
                const data = await res.json();
                document.getElementById('thumbBox').innerHTML = `<img src="${data.image_path}" />`;
                openValEditModal(processedValDataUrl);
                document.getElementById('telValStatus').innerText = 'APPRAISAL: READY';
            }
        }

        function playCashChirpSound() {
            try {
                const ctx = getAudioContext();
                const now = ctx.currentTime;
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.connect(gain); gain.connect(ctx.destination);
                osc.type = 'sine';
                osc.frequency.setValueAtTime(520, now);
                osc.frequency.setValueAtTime(1040, now + 0.1);
                gain.gain.setValueAtTime(0.28, now);
                gain.gain.exponentialRampToValueAtTime(0.001, now + 0.2);
                osc.start(now); osc.stop(now + 0.21);
            } catch(e) {}
        }

        /* 3. INNOVACIÓN: MESA DE POST-EDICIÓN & PÓLIZA DE TASACIÓN */
        function openValEditModal(imgSrc) {
            document.getElementById('editModalTitle').innerText = '🏷️ VALUACIÓN COMERCIAL V10';
            document.getElementById('editImagePreview').src = imgSrc;
            document.getElementById('editImagePreview').style.display = 'block';
            document.getElementById('valCertificateBox').style.display = 'none';
            document.getElementById('postEditModal').style.display = 'flex';
        }

        function closeEditModal() { document.getElementById('postEditModal').style.display = 'none'; }

        function switchValView(view, elem) {
            document.querySelectorAll('.tool-chip').forEach(c => c.classList.remove('active'));
            elem.classList.add('active');

            const previewImg = document.getElementById('editImagePreview');
            const cert = document.getElementById('valCertificateBox');

            if (view === 'preview') {
                previewImg.style.display = 'block';
                cert.style.display = 'none';
            } else if (view === 'certificate') {
                previewImg.style.display = 'none';
                cert.style.display = 'flex';
            }
        }

        function applyValFilter(mode, elem) {
            document.querySelectorAll('.tool-chip').forEach(c => c.classList.remove('active'));
            elem.classList.add('active');
            const img = document.getElementById('editImagePreview');

            if (mode === 'highlight_asset') {
                img.style.filter = 'contrast(1.3) saturate(1.25) brightness(1.05)';
            } else if (mode === 'commercial_clean') {
                img.style.filter = 'contrast(1.15) brightness(1.1) drop-shadow(0 0 10px rgba(99,230,226,0.5))';
            }
        }

        function exportEditedResult() {
            const a = document.createElement('a');
            a.href = processedValDataUrl || document.getElementById('editImagePreview').src;
            a.download = `bian_valuacion_${currentCategoryName.toLowerCase().replace(/[^a-z0-9]/g, '_')}_v10_${Date.now()}.jpg`;
            a.click();
            alert('✔ Certificado de valuación comercial HD exportado con éxito.');
        }

        /* DISPARO ESTÁNDAR ZSL */
        async function captureStandardZSL() {
            const flash = document.getElementById('ambientLightLayer');
            flash.classList.add('flash');
            setTimeout(() => flash.classList.remove('flash'), 60);
            playLensCapShutterSound();

            const b64 = hiddenCanvas.toDataURL('image/jpeg', 0.95);
            const res = await fetch('/bian/process/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image_base64: b64, prompt_analysis: 'Captura V10' })
            });
            if (res.ok) {
                const data = await res.json();
                document.getElementById('thumbBox').innerHTML = `<img src="${data.image_path}" />`;
                openValEditModal(b64);
            }
        }

        function playLensCapShutterSound() {
            try {
                const ctx = getAudioContext();
                const now = ctx.currentTime;
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.connect(gain); gain.connect(ctx.destination);
                osc.type = 'triangle';
                osc.frequency.setValueAtTime(160, now);
                osc.frequency.exponentialRampToValueAtTime(35, now + 0.11);
                gain.gain.setValueAtTime(0.28, now);
                gain.gain.exponentialRampToValueAtTime(0.001, now + 0.11);
                osc.start(now); osc.stop(now + 0.12);
            } catch(e) {}
        }

        let unlocked = false;
        function unlockSuite() {
            if (unlocked) return;
            unlocked = true;
            playLensCapShutterSound();
            const cap = document.getElementById('lensCapDisk');
            cap.style.transform = 'rotate(-45deg) scale(1.18)';
            setTimeout(() => {
                document.getElementById('lockscreen').classList.add('unlocked');
                applyActiveCardTheme(moduleCatalog[activeCardIndex]);
            }, 180);
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

        /* SWIPE GLOBAL */
        window.addEventListener('touchstart', (e) => {
            if (!e.target.closest('#deckStack') && !e.target.closest('#horizontalDockBar') && !e.target.closest('#postEditModal') && !e.target.closest('#galleryModal') && !e.target.closest('#nanobotModal') && !e.target.closest('#floatingGadget') && !e.target.closest('#floatingPanel')) touchStartY = e.touches[0].clientY;
        }, { passive: true });
        window.addEventListener('touchend', (e) => {
            if (!e.target.closest('#deckStack') && !e.target.closest('#horizontalDockBar') && !e.target.closest('#postEditModal') && !e.target.closest('#galleryModal') && !e.target.closest('#nanobotModal') && !e.target.closest('#floatingGadget') && !e.target.closest('#floatingPanel')) {
                const deltaY = touchStartY - e.changedTouches[0].clientY;
                if (!unlocked && deltaY > 35) unlockSuite();
                else if (unlocked && deltaY < -75 && touchStartY < 120) lockSuite();
            }
        }, { passive: true });

        /* CATÁLOGO COMPLETO DE LOS 16 MÓDULOS DE LA MASTER SUITE V10 */
        const moduleCatalog = [
            { key: 'price', icon: '🏷️', title: 'VALUADOR HÍBRIDO V10', pill: '🏷️ TASACIÓN DE MERCADO & PÓLIZA COMERCIAL', color: '#63E6E2', botTips: 'Encuadra el activo comercial para estimar precio de compra de remate, precio de venta y margen bruto.' },
            { key: 'chef', icon: '👨‍🍳', title: 'CHEF LEAN V10', pill: '👨‍🍳 BÁSCULA NPU & AUDITORÍA DE MERMA', color: '#FF9500', botTips: 'Báscula volumétrica y control de merma cárnica.' },
            { key: 'depth', icon: '🛰️', title: 'DEPTH-MAP NPU', pill: '🛰️ Z-BUFFER 16-BIT & NUBE LIDAR', color: '#00F2FE', botTips: 'Sensor de disparidad y Wiggle 3D.' },
            { key: 'motion', icon: '⚡', title: 'VIDEO MOTION', pill: '⚡ FLUJO ÓPTICO & ESTELAS 60 FPS', color: '#FF9500', botTips: 'Rastreo kinético de vectores.' },
            { key: 'svg', icon: '📐', title: 'SVG LOGOS', pill: '📐 VECTORIZADOR CAD & CÓDIGO XML', color: '#00FFC8', botTips: 'Vectorizador Autotrace y exportador XML.' },
            { key: 'raw', icon: '🎞️', title: 'ESTUDIO RAW', pill: '🎞️ REVELADO DIGITAL DE 14-BIT & HISTOGRAMA', color: '#FF9F0A', botTips: 'Histograma espectral RGB.' },
            { key: 'cine', icon: '🎬', title: 'CINE SCOPE V10', pill: '🎬 ANAMÓRFICO 2.39:1 & BLUE STREAK FLARE', color: '#FF0055', botTips: 'Enmarcado cinematográfico DCI 2.39:1.' },
            { key: 'imprenta', icon: '🖨️', title: 'IMPRENTA PDF', pill: '🖨️ PREPRENSA CMYK & FOGRA39 PROOF', color: '#FF2D85', botTips: 'Mesa de preprensa industrial.' },
            { key: 'stickers', icon: '🎨', title: 'WALLPAPERS STICKERS', pill: '🎨 TROQUELADO 3D & AMOLED BLACK', color: '#BF5AF2', botTips: 'Stickers die-cut y fondos AMOLED.' },
            { key: 'lonas', icon: '🎪', title: 'LONAS 3D', pill: '🎪 BASTIDOR PTR & TÚNEL DE VIENTO 110 km/h', color: '#FFD60A', botTips: 'Bastidor de PTR y túnel de viento.' },
            { key: 'bokeh', icon: '🎭', title: 'RETRATO BOKEH', pill: '🎭 APERTURA ÓPTICA & IRIS SHAPER', color: '#FF2D55', botTips: 'Desenfoque f/1.2 y convolución gaussiana.' },
            { key: 'night', icon: '🌙', title: 'NIGHTOGRAPHY', pill: '🌙 MULTI-FRAME STACK & DEEP-SKY BOOST', color: '#5E5CE6', botTips: 'Baja iluminación y apilado en RAM.' },
            { key: 'macro', icon: '🔍', title: 'MACRO PRO', pill: '🔍 FOCUS PEAKING & DEEP FOCUS STACK', color: '#30D158', botTips: 'Focus Peaking verde y lupa 10x.' },
            { key: 'scan', icon: '📄', title: 'SCAN DOC PRO', pill: '📄 AUTO-ENCUADRE HOMOGRÁFICO & OCR', color: '#00D2FF', botTips: 'Alinea el documento dentro del cuadrilátero.' },
            { key: 'timelapse', icon: '⏱️', title: 'TIMELAPSE V10', pill: '⏱️ TIME-LAPSE: CAPTURA COMPRIMIDA 4x', color: '#FF3B30', botTips: 'Gimbal Virtual OIS activo.' },
            { key: 'pano', icon: '🌐', title: 'PANORÁMICA 360', pill: '🌐 BARRIDO POLAR & ORBE 3D VR', color: '#00FFC8', botTips: 'Gira el teléfono de izquierda a derecha.' }
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
                        applyActiveCardTheme(moduleCatalog[activeCardIndex]);
                        lastClickedModuleIndex = -1;
                    } else {
                        activeCardIndex = idx;
                        lastClickedModuleIndex = idx;
                        lastModuleClickTime = now;
                        renderHorizontalDock();
                        applyActiveCardTheme(moduleCatalog[activeCardIndex]);
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
                applyActiveCardTheme(moduleCatalog[activeCardIndex]);
            }, 180);
        }

        function applyActiveCardTheme(m) {
            document.getElementById('moduleNameText').innerText = m.title;
            document.getElementById('statusDot').style.background = m.color;
            document.getElementById('contextPillText').innerText = m.pill;
            document.getElementById('contextPillText').style.color = m.color;
            document.getElementById('contextPillText').style.borderColor = `${m.color}66`;

            document.getElementById('floatingGadget').innerText = m.icon;
            document.getElementById('floatingGadget').style.borderColor = m.color;
            document.getElementById('floatModTitle').innerText = m.title;
            document.getElementById('floatModTitle').style.color = m.color;
            document.getElementById('floatModDesc').innerText = m.botTips;
            document.getElementById('shutterCorona').style.borderColor = m.color;

            // Mostrar u ocultar controles del Valuador
            if (m.key === 'price') {
                document.getElementById('valHud').style.display = 'flex';
            } else {
                document.getElementById('valHud').style.display = 'none';
            }

            const topCard = deckStack.querySelector('.pos-0');
            if (topCard) {
                topCard.style.borderColor = m.color;
                topCard.style.background = m.color;
                topCard.style.boxShadow = `0 0 22px ${m.color}`;
            }

            triggerModuleVisuals(m.color);

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

            setTimeout(() => {
                border.style.transition = 'border-color 1.5s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 1.5s cubic-bezier(0.16, 1, 0.3, 1)';
                border.style.borderColor = 'transparent';
                border.style.boxShadow = 'none';
                ambient.classList.remove('flash');
            }, 100);
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
                    <button class="bot-btn" onclick="handleValuationCaptureTrigger(); toggleFloatingPanel();">📸 Disparo de Tasación con ${cur.title}</button>
                    <button class="bot-btn" onclick="openHorizontalDock(); toggleFloatingPanel();">🎴 Selector de Módulos</button>
                    <button class="bot-btn" onclick="toggleGhostScope(); toggleFloatingPanel();">👁️ Alternar Radar Espectral</button>
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
                        openValEditModal(img.image_path);
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

        function openNanobot() {
            const curMod = moduleCatalog[activeCardIndex];
            const modal = document.getElementById('nanobotModal');
            const msg = document.getElementById('botMessageText');
            const act = document.getElementById('botActionList');

            msg.innerHTML = `
                <div style="color:#63E6E2; font-weight:800; margin-bottom:6px;">🤖 Diagnóstico V10 para ${curMod.title}:</div>
                <div>${curMod.botTips}</div>
            `;

            act.innerHTML = `
                <button class="bot-btn" onclick="executeBotAction('calibrate')">⚡ Calibrar Sensor de Tasación & Bandas de Margen</button>
                <button class="bot-btn" onclick="executeBotAction('ghost')">👁️ Activar Radar Espectral</button>
                <button class="bot-btn" onclick="executeBotAction('gallery')">🖼️ Ver Valuaciones Guardadas</button>
            `;

            modal.style.display = 'flex';
        }

        function closeNanobot() { document.getElementById('nanobotModal').style.display = 'none'; }

        function executeBotAction(action) {
            closeNanobot();
            if(action === 'calibrate') {
                applyActiveCardTheme(moduleCatalog[activeCardIndex]);
                alert("✔ Algoritmo de tasación comercial y colimador calibrados.");
            } else if(action === 'ghost') {
                toggleGhostScope();
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
    db_image = ProcessedImage(image_path=f"/bian/{filename}", prompt_analysis=payload.prompt_analysis)
    session.add(db_image)
    session.commit()
    session.refresh(db_image)
    return db_image

@router.get("/images/", response_model=list[ProcessedImage])
def list_images(session: Session = Depends(get_session)):
    return session.exec(select(ProcessedImage)).all()
