from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
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
    prompt_analysis: str = "Escaneo Documental Bian V9"

class NanoBotQuery(BaseModel):
    message: str
    current_module: str = "general"

@router.get("/storage/bian/{filename}")
async def serve_bian_image(filename: str):
    file_path = os.path.join("storage", "bian", filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="Imagen no encontrada")

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Bian AI Suite - Scanner & Cámara Pro V9</title>
    <script src="https://unpkg.com/tesseract.js@v4.0.2/dist/tesseract.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", Roboto, sans-serif; -webkit-tap-highlight-color: transparent; }
        body { background: #000; color: #fff; height: 100vh; overflow: hidden; display: flex; flex-direction: column; user-select: none; }

        .top-float-left {
            position: absolute; top: 16px; left: 18px; z-index: 50;
            background: rgba(22, 22, 26, 0.65);
            backdrop-filter: blur(25px); -webkit-backdrop-filter: blur(25px);
            border: 1px solid rgba(255, 255, 255, 0.16);
            border-radius: 20px; padding: 7px 14px;
            display: flex; align-items: center; gap: 8px; font-weight: 700; font-size: 12px;
            box-shadow: 0 6px 24px rgba(0,0,0,0.4);
            transition: all 0.25s ease;
        }
        .glow-dot { width: 7px; height: 7px; border-radius: 50%; background: #30D158; box-shadow: 0 0 8px #30D158; }

        .top-float-right {
            position: absolute; top: 16px; right: 18px; z-index: 50;
            background: rgba(255, 255, 255, 0.12);
            backdrop-filter: blur(25px); -webkit-backdrop-filter: blur(25px);
            border: 1px solid rgba(255, 255, 255, 0.28);
            color: #FFFFFF; font-size: 12px; font-weight: 700; padding: 8px 16px; border-radius: 22px;
            display: flex; align-items: center; gap: 6px; cursor: pointer;
            box-shadow: 0 6px 24px rgba(0,0,0,0.5), 0 0 14px rgba(255, 255, 255, 0.18);
            transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
        }
        .top-float-right:active { transform: scale(0.95); background: rgba(255,255,255,0.22); }

        .viewport {
            position: absolute; inset: 0; width: 100%; height: 100%;
            background: #000; overflow: hidden; display: flex; align-items: center; justify-content: center;
        }
        video {
            width: 100%; height: 100%; object-fit: cover;
            transform-origin: center center;
            transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1), filter 0.3s ease;
        }
        
        /* FILTROS POR MODO */
        video.portrait-bokeh { filter: drop-shadow(0 0 16px rgba(0,255,200,0.3)); }
        video.night-mode { filter: brightness(1.35) contrast(1.1) saturate(1.2); }
        video.macro-mode { filter: contrast(1.25) saturate(1.15); }
        video.scan-mode { filter: grayscale(1) contrast(1.4) brightness(1.1); }

        /* GUIA DE ESCANEO DE DOCUMENTOS */
        .doc-scanner-frame {
            position: absolute; width: 78%; height: 68%;
            border: 2px dashed #00FFC8; border-radius: 12px;
            box-shadow: 0 0 0 2000px rgba(0, 0, 0, 0.45);
            pointer-events: none; z-index: 35; display: none;
            justify-content: space-between; flex-direction: column; padding: 10px;
        }
        .doc-scanner-frame.active { display: flex; }
        .doc-corner { width: 18px; height: 18px; border-color: #00FFC8; border-style: solid; }
        .doc-corner.tl { border-width: 3px 0 0 3px; align-self: flex-start; }
        .doc-corner.tr { border-width: 3px 3px 0 0; align-self: flex-end; }
        .doc-corner.bl { border-width: 0 0 3px 3px; align-self: flex-start; }
        .doc-corner.br { border-width: 0 3px 3px 0; align-self: flex-end; }
        .doc-row { display: flex; justify-content: space-between; width: 100%; }

        .mode-status-chip {
            position: absolute; top: 68px; left: 50%; transform: translateX(-50%); z-index: 45;
            background: rgba(0, 0, 0, 0.65); backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 214, 10, 0.5); color: #FFD60A;
            padding: 5px 14px; border-radius: 16px; font-size: 11px; font-weight: 700;
            display: none; align-items: center; gap: 6px;
        }
        .mode-status-chip.active { display: flex; }
        
        .shutter-flash {
            position: absolute; inset: 0; background: #fff; opacity: 0; pointer-events: none; z-index: 60;
            transition: opacity 0.12s ease-out;
        }
        .shutter-flash.flash { opacity: 0.85; }

        .focus-circle-ring {
            position: absolute; width: 95px; height: 95px; pointer-events: none;
            border-radius: 50%; border: 1.8px solid rgba(255, 255, 255, 0.85);
            box-shadow: 0 0 16px rgba(255, 255, 255, 0.35);
            transition: left 0.28s cubic-bezier(0.16, 1, 0.3, 1), top 0.28s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.6s ease, border-color 0.3s, transform 0.25s;
            display: flex; flex-direction: column; align-items: center; justify-content: space-between;
            opacity: 1; transform: translate(-50%, -50%); z-index: 30;
        }
        .focus-circle-ring.faded { opacity: 0.15; border-color: rgba(255, 255, 255, 0.2); box-shadow: none; }
        .focus-circle-ring.glowing { transform: translate(-50%, -50%) scale(1.08); border-color: #FFD60A; box-shadow: 0 0 25px rgba(255, 214, 10, 0.8); }

        .lock-icon-badge { font-size: 11px; margin-top: -16px; background: rgba(0,0,0,0.5); border-radius: 50%; padding: 2px 4px; }
        .sun-slider-badge { font-size: 12px; margin-bottom: -18px; background: rgba(0,0,0,0.5); border-radius: 50%; padding: 2px 4px; }

        .lens-pill-bar {
            position: absolute; bottom: 175px; z-index: 45;
            display: flex; gap: 4px; background: rgba(0, 0, 0, 0.55);
            backdrop-filter: blur(25px); -webkit-backdrop-filter: blur(25px);
            border: 1px solid rgba(255, 255, 255, 0.12);
            padding: 4px 6px; border-radius: 24px;
            transition: all 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
        }
        .lens-btn {
            background: transparent; border: none; color: rgba(255,255,255,0.7);
            font-size: 10px; font-weight: 700; padding: 5px 9px; border-radius: 14px;
            cursor: pointer; transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
        }
        .lens-btn.active { background: rgba(255, 255, 255, 0.25); color: #fff; transform: scale(1.05); }

        .lens-pill-bar.collapsed { padding: 3px 5px; }
        .lens-pill-bar.collapsed .lens-btn:not(.active) {
            opacity: 0; width: 0; padding: 0; margin: 0; pointer-events: none; overflow: hidden; transform: scale(0.4);
        }

        .dock-tooltip {
            position: absolute; z-index: 46;
            background: rgba(28, 28, 35, 0.92); backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.22);
            color: #fff; font-size: 10px; font-weight: 600; padding: 4px 12px;
            border-radius: 14px; pointer-events: none; opacity: 0; transform: translate(-50%, 6px);
            transition: opacity 0.2s cubic-bezier(0.16, 1, 0.3, 1), transform 0.2s cubic-bezier(0.16, 1, 0.3, 1);
            box-shadow: 0 4px 16px rgba(0,0,0,0.6); white-space: nowrap;
        }
        .dock-tooltip.visible { opacity: 1; transform: translate(-50%, 0); }

        .glass-dock {
            position: absolute; bottom: 104px; left: 50%; transform: translateX(-50%); z-index: 40;
            width: calc(100% - 32px); max-width: 500px;
            background: rgba(18, 18, 22, 0.55);
            backdrop-filter: blur(30px); -webkit-backdrop-filter: blur(30px);
            border: 1px solid rgba(255, 255, 255, 0.14);
            border-radius: 30px; padding: 10px 14px;
            display: flex; align-items: center; justify-content: flex-start;
            gap: 10px; overflow-x: auto; scrollbar-width: none;
            box-shadow: 0 10px 40px rgba(0,0,0,0.5);
            transition: all 0.45s cubic-bezier(0.16, 1, 0.3, 1), background 1.8s ease, border-color 1.8s ease, box-shadow 1.8s ease;
        }
        .glass-dock::-webkit-scrollbar { display: none; }

        .glass-dock.stacked-mode {
            left: 76%; transform: translateX(-50%); width: 125px;
            overflow: visible; justify-content: flex-start; padding: 6px;
        }
        .glass-dock.stacked-mode.evaporated-dock {
            background: transparent !important; border-color: transparent !important; box-shadow: none !important;
        }

        .dock-icon-btn {
            flex: 0 0 44px; height: 44px; border-radius: 18px; border: 1px solid rgba(255,255,255,0.1);
            background: rgba(255, 255, 255, 0.06); font-size: 19px;
            display: flex; align-items: center; justify-content: center;
            cursor: pointer; position: relative;
            transition: transform 0.35s cubic-bezier(0.34, 1.56, 0.64, 1), opacity 0.35s ease, background 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
        }
        .dock-icon-btn:active { transform: scale(0.92); }

        .dock-icon-btn.selected {
            transform: translateY(-8px) scale(1.18) !important;
            border-color: rgba(255, 255, 255, 0.45) !important;
            z-index: 25 !important; opacity: 1 !important;
        }
        .dock-icon-btn.selected::after {
            content: ''; position: absolute; bottom: -6px; width: 5px; height: 5px;
            border-radius: 50%; background: #fff; box-shadow: 0 0 6px #fff;
        }

        .glass-dock.stacked-mode .dock-icon-btn.stack-layer { position: absolute; pointer-events: auto; opacity: 0.85; transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1); }
        .glass-dock.stacked-mode .dock-icon-btn.stack-1 { transform: translateX(18px) translateY(-5px) scale(0.94); z-index: 20; }
        .glass-dock.stacked-mode .dock-icon-btn.stack-2 { transform: translateX(34px) translateY(-2px) scale(0.88); z-index: 15; opacity: 0.6; }
        .glass-dock.stacked-mode .dock-icon-btn.stack-3 { transform: translateX(48px) translateY(1px) scale(0.82); z-index: 10; opacity: 0.35; }
        .glass-dock.stacked-mode .dock-icon-btn.stack-deep { position: absolute; transform: translateX(54px) scale(0.7); opacity: 0; pointer-events: none; z-index: 5; }

        .dock-icon-btn[data-key="scan"].active-glow { background: linear-gradient(135deg, rgba(0,255,200,0.7), rgba(10,132,255,0.5)); border-color: #00FFC8; box-shadow: 0 8px 20px rgba(0,255,200,0.6); }
        .dock-icon-btn[data-key="night"].active-glow { background: linear-gradient(135deg, rgba(94,92,230,0.7), rgba(48,209,88,0.5)); border-color: #5E5CE6; box-shadow: 0 8px 20px rgba(94,92,230,0.6); }
        .dock-icon-btn[data-key="macro"].active-glow { background: linear-gradient(135deg, rgba(48,209,88,0.7), rgba(0,255,200,0.5)); border-color: #30D158; box-shadow: 0 8px 20px rgba(48,209,88,0.6); }
        .dock-icon-btn[data-key="portrait"].active-glow { background: linear-gradient(135deg, rgba(255,214,10,0.7), rgba(255,107,0,0.5)); border-color: #FFD60A; box-shadow: 0 8px 20px rgba(255,214,10,0.6); }
        .dock-icon-btn[data-key="lonas"].active-glow { background: linear-gradient(135deg, rgba(255,149,0,0.7), rgba(255,94,58,0.5)); border-color: #FF9500; box-shadow: 0 8px 20px rgba(255,149,0,0.6); }
        .dock-icon-btn[data-key="custom"].active-glow { background: linear-gradient(135deg, rgba(255,45,85,0.7), rgba(175,82,222,0.5)); border-color: #FF2D55; box-shadow: 0 8px 20px rgba(255,45,85,0.6); }
        .dock-icon-btn[data-key="print"].active-glow { background: linear-gradient(135deg, rgba(50,173,230,0.7), rgba(0,122,255,0.5)); border-color: #32ADE6; box-shadow: 0 8px 20px rgba(0,122,255,0.6); }
        .dock-icon-btn[data-key="cine"].active-glow { background: linear-gradient(135deg, rgba(255,59,48,0.7), rgba(255,45,85,0.5)); border-color: #FF3B30; box-shadow: 0 8px 20px rgba(255,59,48,0.6); }
        .dock-icon-btn[data-key="raw"].active-glow { background: linear-gradient(135deg, rgba(48,209,88,0.7), rgba(52,199,89,0.5)); border-color: #30D158; box-shadow: 0 8px 20px rgba(48,209,88,0.6); }
        .dock-icon-btn[data-key="svg"].active-glow { background: linear-gradient(135deg, rgba(255,214,10,0.7), rgba(255,159,10,0.5)); border-color: #FFD60A; box-shadow: 0 8px 20px rgba(255,214,10,0.6); }
        .dock-icon-btn[data-key="vid"].active-glow { background: linear-gradient(135deg, rgba(191,90,242,0.7), rgba(94,92,230,0.5)); border-color: #BF5AF2; box-shadow: 0 8px 20px rgba(94,92,230,0.6); }
        .dock-icon-btn[data-key="depth"].active-glow { background: linear-gradient(135deg, rgba(255,55,95,0.7), rgba(191,90,242,0.5)); border-color: #FF375F; box-shadow: 0 8px 20px rgba(255,55,95,0.6); }
        .dock-icon-btn[data-key="chef"].active-glow { background: linear-gradient(135deg, rgba(255,159,10,0.7), rgba(255,107,0,0.5)); border-color: #FF9F0A; box-shadow: 0 8px 20px rgba(255,159,10,0.6); }
        .dock-icon-btn[data-key="price"].active-glow { background: linear-gradient(135deg, rgba(99,230,226,0.7), rgba(0,199,190,0.5)); border-color: #63E6E2; box-shadow: 0 8px 20px rgba(0,199,190,0.6); }
        .dock-icon-btn[data-key="ai"].active-glow { background: linear-gradient(135deg, rgba(10,132,255,0.7), rgba(94,92,230,0.5)); border-color: #0A84FF; box-shadow: 0 8px 20px rgba(10,132,255,0.6); }

        .dock-icon-btn.evaporated {
            background: rgba(255, 255, 255, 0.08) !important;
            border-color: rgba(255, 255, 255, 0.22) !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;
            transition: background 2.5s cubic-bezier(0.25, 1, 0.5, 1), border-color 2.5s cubic-bezier(0.25, 1, 0.5, 1), box-shadow 2.5s cubic-bezier(0.25, 1, 0.5, 1) !important;
        }

        .bottom-shutter-bar {
            position: absolute; bottom: 18px; left: 0; right: 0;
            display: flex; justify-content: space-around; align-items: center; z-index: 50;
            padding: 0 30px;
        }
        .shutter-outer {
            width: 76px; height: 76px; border-radius: 50%;
            background: rgba(255, 59, 48, 0.15); backdrop-filter: blur(10px);
            border: 2px solid rgba(255, 59, 48, 0.65);
            display: flex; align-items: center; justify-content: center; cursor: pointer;
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
        }
        .shutter-outer:active { transform: scale(0.9); }
        .shutter-inner {
            width: 62px; height: 62px; border-radius: 50%;
            background: linear-gradient(135deg, #FF453A, #FF3B30);
            box-shadow: 0 0 16px rgba(255, 59, 48, 0.65);
            transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
        }
        
        .side-btn {
            width: 44px; height: 44px; border-radius: 50%;
            background: rgba(255, 255, 255, 0.1); backdrop-filter: blur(15px);
            border: 1px solid rgba(255, 255, 255, 0.15); font-size: 16px;
            color: #fff; display: flex; align-items: center; justify-content: center;
            cursor: pointer; transition: transform 0.15s; overflow: hidden;
        }
        .side-btn:active { transform: scale(0.9); }
        .side-btn img { width: 100%; height: 100%; object-fit: cover; }

        /* MODAL NANO-BOT */
        .bot-modal {
            position: fixed; inset: 0; z-index: 100; background: rgba(0,0,0,0.7);
            backdrop-filter: blur(25px); -webkit-backdrop-filter: blur(25px);
            display: none; flex-direction: column; justify-content: flex-end;
            opacity: 0; transition: opacity 0.3s ease;
        }
        .bot-modal.active { display: flex; opacity: 1; }
        .bot-card {
            background: #141418; border-top: 1px solid rgba(255,255,255,0.16);
            border-radius: 32px 32px 0 0; padding: 20px;
            max-height: 82vh; display: flex; flex-direction: column;
            box-shadow: 0 -10px 40px rgba(0,0,0,0.8);
            animation: slideUp 0.32s cubic-bezier(0.16, 1, 0.3, 1);
        }
        @keyframes slideUp { from { transform: translateY(100%); } to { transform: translateY(0); } }
        
        .bot-drag { width: 40px; height: 5px; background: rgba(255,255,255,0.3); border-radius: 4px; margin: 0 auto 12px; cursor: pointer; }
        .bot-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
        .bot-title { font-size: 16px; font-weight: 700; color: #fff; display: flex; align-items: center; gap: 6px; }
        .bot-badge { font-size: 9px; padding: 2px 7px; border-radius: 10px; background: rgba(0,255,200,0.15); color: #00FFC8; border: 1px solid #00FFC8; }

        .bot-chat-stream { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; margin-bottom: 12px; padding-right: 4px; max-height: 280px; }
        .bot-msg { max-width: 85%; padding: 10px 14px; border-radius: 16px; font-size: 12px; line-height: 1.45; }
        .bot-msg.ia { background: rgba(255,255,255,0.08); color: #E5E5EA; align-self: flex-start; border-bottom-left-radius: 4px; border: 1px solid rgba(255,255,255,0.08); }
        .bot-msg.user { background: #0A84FF; color: #fff; align-self: flex-end; border-bottom-right-radius: 4px; }

        .bot-quick-chips { display: flex; gap: 6px; overflow-x: auto; padding-bottom: 8px; margin-bottom: 10px; scrollbar-width: none; }
        .bot-quick-chips::-webkit-scrollbar { display: none; }
        .bot-chip {
            white-space: nowrap; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.15);
            color: #ccc; font-size: 10px; padding: 6px 12px; border-radius: 16px; cursor: pointer;
        }
        .bot-chip:active { background: rgba(0,255,200,0.2); border-color: #00FFC8; color: #fff; }

        .bot-input-box { display: flex; gap: 8px; align-items: center; }
        .bot-input {
            flex: 1; background: #1C1C22; border: 1px solid rgba(255,255,255,0.14);
            border-radius: 18px; padding: 11px 16px; color: #fff; font-size: 13px; outline: none;
        }
        .bot-btn-send {
            background: #00FFC8; border: none; color: #000; font-weight: 700;
            border-radius: 50%; width: 42px; height: 42px; display: flex; align-items: center; justify-content: center; cursor: pointer;
        }

        .gallery-modal {
            position: fixed; inset: 0; z-index: 105; background: #000;
            display: none; flex-direction: column; padding: 18px 14px;
        }
        .gallery-modal.active { display: flex; }
        .gallery-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
        .gallery-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; overflow-y: auto; flex: 1; }
        .gallery-item { aspect-ratio: 1; background: #111; border-radius: 8px; overflow: hidden; position: relative; border: 1px solid #222; }
        .gallery-item img { width: 100%; height: 100%; object-fit: cover; }
    </style>
</head>
<body>

    <div class="shutter-flash" id="flashLayer"></div>

    <div class="top-float-left" id="activeModulePill">
        <div class="glow-dot"></div>
        <span id="activeModuleName">Cam Vision V9</span>
    </div>

    <div class="top-float-right" id="actionPromptPill" onclick="openNanoBotModal()">
        <span>✨ ¿Qué quieres hacer?</span>
    </div>

    <!-- GUÍA TÁCTICA PARA DOCUMENTOS -->
    <div class="doc-scanner-frame" id="docScannerFrame">
        <div class="doc-row">
            <div class="doc-corner tl"></div>
            <div class="doc-corner tr"></div>
        </div>
        <div style="text-align: center; color: #00FFC8; font-size: 11px; font-weight: 700; letter-spacing: 0.5px;">ALINEA EL DOCUMENTO O TICKET AQUÍ</div>
        <div class="doc-row">
            <div class="doc-corner bl"></div>
            <div class="doc-corner br"></div>
        </div>
    </div>

    <div class="mode-status-chip" id="modeStatusChip">
        <span id="modeStatusText">📸 MODO ACTIVO</span>
    </div>

    <div class="viewport" id="viewportArea" onclick="handleTapToFocus(event)">
        <video id="webcam" autoplay playsinline></video>
        
        <div class="focus-circle-ring" id="focusCircle">
            <div class="lock-icon-badge">🔒</div>
            <div class="sun-slider-badge">☀️</div>
        </div>

        <canvas id="internalCanvas" style="display:none;"></canvas>
    </div>

    <div class="lens-pill-bar collapsed" id="lensPillBar">
        <button class="lens-btn" onclick="handleLensClick(0.6, this, event)">0.6x</button>
        <button class="lens-btn active" onclick="handleLensClick(1.0, this, event)">1x</button>
        <button class="lens-btn" onclick="handleLensClick(2.0, this, event)">2x</button>
        <button class="lens-btn" onclick="handleLensClick(3.0, this, event)">3x</button>
        <button class="lens-btn" onclick="handleLensClick(10.0, this, event)">10x</button>
    </div>

    <div class="dock-tooltip" id="dockTooltip">Módulo</div>

    <div class="glass-dock" id="glassDockBar">
        <!-- ESCÁNER DE DOCUMENTOS PRO EN EL DOCK -->
        <div class="dock-icon-btn" data-key="scan" onclick="handleIconClick('scan', '📄 Scan Doc Pro V9', this, event)">📄</div>
        <div class="dock-icon-btn" data-key="night" onclick="handleIconClick('night', '🌙 Nightography V9', this, event)">🌙</div>
        <div class="dock-icon-btn" data-key="macro" onclick="handleIconClick('macro', '🔍 Macro Pro V9', this, event)">🔍</div>
        <div class="dock-icon-btn" data-key="portrait" onclick="handleIconClick('portrait', '👤 Modo Retrato Bokeh V9', this, event)">👤</div>
        <div class="dock-icon-btn" data-key="lonas" onclick="handleIconClick('lonas', '⛺ Lonas 3D V9', this, event)">⛺</div>
        <div class="dock-icon-btn" data-key="custom" onclick="handleIconClick('custom', '🎨 Wallpapers V9', this, event)">🎨</div>
        <div class="dock-icon-btn" data-key="print" onclick="handleIconClick('print', '🖨️ Imprenta PDF V9', this, event)">🖨️</div>
        <div class="dock-icon-btn" data-key="cine" onclick="handleIconClick('cine', '🎬 Cine Scope V9', this, event)">🎬</div>
        <div class="dock-icon-btn" data-key="raw" onclick="handleIconClick('raw', '📸 Revelado RAW V9', this, event)">📸</div>
        <div class="dock-icon-btn" data-key="svg" onclick="handleIconClick('svg', '📐 SVG Logos V9', this, event)">📐</div>
        <div class="dock-icon-btn" data-key="vid" onclick="handleIconClick('vid', '🎥 Video Motion V8', this, event)">🎥</div>
        <div class="dock-icon-btn" data-key="depth" onclick="handleIconClick('depth', '🧠 Depth-Map NPU V9', this, event)">🧠</div>
        <div class="dock-icon-btn" data-key="chef" onclick="handleIconClick('chef', '👨‍🍳 Chef Lean V9', this, event)">👨‍🍳</div>
        <div class="dock-icon-btn" data-key="price" onclick="handleIconClick('price', '🏷️ Valuador Híbrido V7', this, event)">🏷️</div>
        <div class="dock-icon-btn" data-key="ai" onclick="handleIconClick('ai', '✨ Generar Imagen AI V7', this, event)">✨</div>
    </div>

    <div class="bottom-shutter-bar">
        <div class="side-btn" onclick="toggleLens()">🔄</div>
        <div class="shutter-outer" id="shutterBtn" onclick="triggerNativeCaptureAndSave()">
            <div class="shutter-inner"></div>
        </div>
        <div class="side-btn" id="galleryThumbBtn" onclick="openGalleryModal()">
            <span id="galleryIconPlaceholder">🖼️</span>
        </div>
    </div>

    <!-- MODAL NANO-BOT -->
    <div class="bot-modal" id="botModal">
        <div class="bot-card">
            <div class="bot-drag" onclick="closeNanoBotModal()"></div>
            <div class="bot-header">
                <div class="bot-title">
                    <span>⚡ Nano-Bot Táctico</span>
                    <span class="bot-badge" id="botModuleBadge">GENERAL</span>
                </div>
                <button onclick="closeNanoBotModal()" style="background:none; border:none; color:#888; font-size:16px; cursor:pointer;">✕</button>
            </div>
            
            <div class="bot-quick-chips">
                <button class="bot-chip" onclick="askNanoQuick('¿Cómo uso el Escáner de Documentos?')">📄 Escanear Documento</button>
                <button class="bot-chip" onclick="askNanoQuick('¿Qué hace Nightography?')">🌙 Modo Noche</button>
                <button class="bot-chip" onclick="askNanoQuick('¿Para qué sirve el Macro Pro?')">🔍 Macro Pro</button>
                <button class="bot-chip" onclick="askNanoQuick('¿Cómo saco el costo y merma con Chef Lean?')">🥩 Costear Carne</button>
            </div>

            <div class="bot-chat-stream" id="botChatStream">
                <div class="bot-msg ia">
                    ¡Qué onda! Soy tu <strong>Nano-Bot Táctico</strong>. Tienes activos todos los modos modernos: Escáner Documental con OCR, Nightography, Macro Pro, Retrato y las herramientas industriales.
                </div>
            </div>

            <div class="bot-input-box">
                <input type="text" class="bot-input" id="botUserInput" placeholder="Pregúntale al Nano-Bot..." onkeydown="if(event.key==='Enter') sendNanoBotMessage()">
                <button class="bot-btn-send" onclick="sendNanoBotMessage()">➤</button>
            </div>
        </div>
    </div>

    <div class="gallery-modal" id="galleryModal">
        <div class="gallery-top">
            <h3 style="font-size:16px; font-weight:700;">Galería Soberana S23 Ultra</h3>
            <button onclick="closeGalleryModal()" style="background:#1c1c22; border:1px solid #333; color:#fff; padding:6px 14px; border-radius:14px; font-size:12px;">Cerrar</button>
        </div>
        <div class="gallery-grid" id="galleryGrid"></div>
    </div>

    <script>
        const video = document.getElementById('webcam');
        const internalCanvas = document.getElementById('internalCanvas');
        let selectedEngineKey = null;
        let selectedEngineName = null;
        let facingMode = 'environment';
        let tooltipTimeout = null;
        let audioCtx = null;
        let fadeCircleTimeout = null;
        let currentStreamTrack = null;
        let evaporateTimeout = null;

        const enginesList = [
            { key: 'scan', name: '📄 Scan Doc Pro V9' },
            { key: 'night', name: '🌙 Nightography V9' },
            { key: 'macro', name: '🔍 Macro Pro V9' },
            { key: 'portrait', name: '👤 Modo Retrato Bokeh V9' },
            { key: 'lonas', name: '⛺ Lonas 3D V9' },
            { key: 'custom', name: '🎨 Wallpapers V9' },
            { key: 'print', name: '🖨️ Imprenta PDF V9' },
            { key: 'cine', name: '🎬 Cine Scope V9' },
            { key: 'raw', name: '📸 Revelado RAW V9' },
            { key: 'svg', name: '📐 SVG Logos V9' },
            { key: 'vid', name: '🎥 Video Motion V8' },
            { key: 'depth', name: '🧠 Depth-Map NPU V9' },
            { key: 'chef', name: '👨‍🍳 Chef Lean V9' },
            { key: 'price', name: '🏷️ Valuador Híbrido V7' },
            { key: 'ai', name: '✨ Generar Imagen AI V7' }
        ];

        function getAudioContext() {
            if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            if (audioCtx.state === 'suspended') audioCtx.resume();
            return audioCtx;
        }

        function playWhatsAppSwooshSound() {
            try {
                const ctx = getAudioContext();
                const now = ctx.currentTime;
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.connect(gain); gain.connect(ctx.destination);
                osc.type = 'sine';
                osc.frequency.setValueAtTime(440, now);
                osc.frequency.exponentialRampToValueAtTime(840, now + 0.12);
                gain.gain.setValueAtTime(0.001, now);
                gain.gain.linearRampToValueAtTime(0.18, now + 0.03);
                gain.gain.exponentialRampToValueAtTime(0.001, now + 0.14);
                osc.start(now); osc.stop(now + 0.14);
            } catch(e) {}
        }

        function playSignatureProSound(key) {
            try {
                const ctx = getAudioContext();
                const now = ctx.currentTime;
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.connect(gain); gain.connect(ctx.destination);
                osc.type = 'sine';
                osc.frequency.setValueAtTime(140, now);
                osc.frequency.exponentialRampToValueAtTime(60, now + 0.15);
                gain.gain.setValueAtTime(0.28, now);
                gain.gain.linearRampToValueAtTime(0.001, now + 0.15);
                osc.start(now); osc.stop(now + 0.15);
            } catch(e) {}
        }

        function playFocusBeep() {
            try {
                const ctx = getAudioContext();
                const now = ctx.currentTime;
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.connect(gain); gain.connect(ctx.destination);
                osc.type = 'sine';
                osc.frequency.setValueAtTime(1200, now);
                osc.frequency.setValueAtTime(1600, now + 0.03);
                gain.gain.setValueAtTime(0.08, now);
                gain.gain.linearRampToValueAtTime(0.001, now + 0.08);
                osc.start(now); osc.stop(now + 0.08);
            } catch(e) {}
        }

        function startCamera() {
            const constraints = {
                video: {
                    facingMode: { ideal: facingMode },
                    width: { ideal: 3840 },
                    height: { ideal: 2160 }
                }
            };

            navigator.mediaDevices.getUserMedia(constraints)
                .then(stream => { 
                    video.srcObject = stream;
                    currentStreamTrack = stream.getVideoTracks()[0];
                    const circle = document.getElementById('focusCircle');
                    circle.style.left = '50%';
                    circle.style.top = '46%';
                    triggerCircleFade();
                    refreshThumb();
                })
                .catch(err => console.error("Error cámara:", err));
        }
        startCamera();

        function toggleLens() {
            facingMode = (facingMode === 'environment') ? 'user' : 'environment';
            if (video.srcObject) video.srcObject.getTracks().forEach(t => t.stop());
            startCamera();
        }

        function handleLensClick(zoomLevel, elem, event) {
            const bar = document.getElementById('lensPillBar');
            if (bar.classList.contains('collapsed')) {
                bar.classList.remove('collapsed');
                return;
            }
            document.querySelectorAll('.lens-btn').forEach(b => b.classList.remove('active'));
            elem.classList.add('active');
            bar.classList.add('collapsed');

            if (currentStreamTrack && typeof currentStreamTrack.getCapabilities === 'function') {
                const caps = currentStreamTrack.getCapabilities();
                if (caps.zoom) {
                    const min = caps.zoom.min || 1;
                    const max = caps.zoom.max || 10;
                    const targetZoom = Math.min(Math.max(zoomLevel, min), max);
                    currentStreamTrack.applyConstraints({ advanced: [{ zoom: targetZoom }] })
                        .catch(() => video.style.transform = `scale(${Math.max(1.0, zoomLevel)})`);
                    return;
                }
            }
            video.style.transform = `scale(${Math.max(1.0, zoomLevel)})`;
        }

        function triggerCircleFade() {
            const circle = document.getElementById('focusCircle');
            circle.classList.remove('faded');
            if (fadeCircleTimeout) clearTimeout(fadeCircleTimeout);
            fadeCircleTimeout = setTimeout(() => { circle.classList.add('faded'); }, 1800);
        }

        function handleTapToFocus(e) {
            if (e.target.closest('.glass-dock') || e.target.closest('.bottom-shutter-bar') || e.target.closest('.top-float-left') || e.target.closest('.top-float-right') || e.target.closest('.lens-pill-bar') || e.target.closest('.dock-tooltip')) return;
            
            document.getElementById('lensPillBar').classList.add('collapsed');

            const viewport = document.getElementById('viewportArea');
            const rect = viewport.getBoundingClientRect();
            const clickX = e.clientX - rect.left;
            const clickY = e.clientY - rect.top;

            const circle = document.getElementById('focusCircle');
            circle.style.left = clickX + 'px';
            circle.style.top = clickY + 'px';
            circle.classList.add('glowing');
            setTimeout(() => circle.classList.remove('glowing'), 300);

            playFocusBeep();
            triggerCircleFade();
        }

        function showDockTooltipAboveElement(name, elem) {
            const tooltip = document.getElementById('dockTooltip');
            const btnRect = elem.getBoundingClientRect();
            tooltip.innerText = name;
            tooltip.style.left = (btnRect.left + (btnRect.width / 2)) + 'px';
            tooltip.style.bottom = (window.innerHeight - btnRect.top + 8) + 'px';
            tooltip.classList.add('visible');

            if (tooltipTimeout) clearTimeout(tooltipTimeout);
            tooltipTimeout = setTimeout(() => { tooltip.classList.remove('visible'); }, 1800);
        }

        function arrangeAlbumStack(activeKey) {
            const dock = document.getElementById('glassDockBar');
            dock.classList.add('stacked-mode');

            const allBtns = Array.from(document.querySelectorAll('.dock-icon-btn'));
            const activeIndex = enginesList.findIndex(e => e.key === activeKey);

            allBtns.forEach(btn => {
                btn.className = 'dock-icon-btn';
                const key = btn.getAttribute('data-key');
                const idx = enginesList.findIndex(e => e.key === key);
                let offset = (idx - activeIndex + enginesList.length) % enginesList.length;

                if (offset === 0) {
                    btn.classList.add('selected', 'active-glow');
                } else {
                    btn.classList.add('stack-layer');
                    if (offset === 1) btn.classList.add('stack-1');
                    else if (offset === 2) btn.classList.add('stack-2');
                    else if (offset === 3) btn.classList.add('stack-3');
                    else btn.classList.add('stack-deep');
                }
            });
        }

        function handleIconClick(key, name, elem, evt) {
            if (selectedEngineKey === key) {
                resetArmEngine();
                return;
            }
            selectEngine(key, name, elem);
        }

        function selectEngine(key, name, elem) {
            showDockTooltipAboveElement(name, elem);
            playSignatureProSound(key);

            if (evaporateTimeout) clearTimeout(evaporateTimeout);

            selectedEngineKey = key;
            selectedEngineName = name;

            const dock = document.getElementById('glassDockBar');
            dock.classList.remove('evaporated-dock');

            arrangeAlbumStack(key);

            document.getElementById('activeModuleName').innerText = key.toUpperCase();
            document.getElementById('botModuleBadge').innerText = key.toUpperCase();

            // CONTROL DE MODOS
            const statusChip = document.getElementById('modeStatusChip');
            const statusText = document.getElementById('modeStatusText');
            const scanFrame = document.getElementById('docScannerFrame');
            video.className = "";
            scanFrame.classList.remove('active');

            if (key === 'scan') {
                video.classList.add('scan-mode');
                scanFrame.classList.add('active');
                statusText.innerText = "📄 ESCÁNER DOCUMENTAL: ALTO CONTRASTE + OCR";
                statusChip.classList.add('active');
            } else if (key === 'portrait') {
                video.classList.add('portrait-bokeh');
                statusText.innerText = "📸 MODO RETRATO: f/1.4 BOKEH NPU";
                statusChip.classList.add('active');
            } else if (key === 'night') {
                video.classList.add('night-mode');
                statusText.innerText = "🌙 NIGHTOGRAPHY: ISO BOOST + RAW DENOISE";
                statusChip.classList.add('active');
            } else if (key === 'macro') {
                video.classList.add('macro-mode');
                statusText.innerText = "🔍 MACRO PRO: REALCE TEXTURAL 8K";
                statusChip.classList.add('active');
            } else {
                statusChip.classList.remove('active');
            }

            evaporateTimeout = setTimeout(() => {
                const activeBtn = document.querySelector(`.dock-icon-btn[data-key="${key}"]`);
                if (activeBtn) {
                    activeBtn.classList.remove('active-glow');
                    activeBtn.classList.add('evaporated');
                }
                dock.classList.add('evaporated-dock');
            }, 1000);

            triggerCircleFade();
        }

        /* GESTO TÁCTIL BIDIRECCIONAL */
        let touchStartY = 0;
        let touchStartX = 0;
        const dockEl = document.getElementById('glassDockBar');

        dockEl.addEventListener('touchstart', (e) => {
            touchStartY = e.touches[0].clientY;
            touchStartX = e.touches[0].clientX;
        }, { passive: true });

        dockEl.addEventListener('touchend', (e) => {
            const touchEndY = e.changedTouches[0].clientY;
            const touchEndX = e.changedTouches[0].clientX;
            const deltaY = touchEndY - touchStartY;
            const deltaX = touchEndX - touchStartX;

            if (Math.abs(deltaY) > 28 && Math.abs(deltaY) > Math.abs(deltaX) && selectedEngineKey) {
                if (deltaY > 0) cycleEngine(1);
                else cycleEngine(-1);
            }
        }, { passive: true });

        function cycleEngine(direction) {
            const currentIdx = enginesList.findIndex(e => e.key === selectedEngineKey);
            const nextIdx = (currentIdx + direction + enginesList.length) % enginesList.length;
            const nextEngine = enginesList[nextIdx];
            const nextBtn = document.querySelector(`.dock-icon-btn[data-key="${nextEngine.key}"]`);
            selectEngine(nextEngine.key, nextEngine.name, nextBtn);
        }

        function resetArmEngine() {
            selectedEngineKey = null;
            selectedEngineName = null;
            if (evaporateTimeout) clearTimeout(evaporateTimeout);

            const dock = document.getElementById('glassDockBar');
            dock.classList.remove('stacked-mode', 'evaporated-dock');

            document.querySelectorAll('.dock-icon-btn').forEach(btn => {
                btn.className = 'dock-icon-btn';
            });

            video.className = "";
            document.getElementById('docScannerFrame').classList.remove('active');
            document.getElementById('modeStatusChip').classList.remove('active');

            document.getElementById('activeModuleName').innerText = 'Cam Vision V9';
            document.getElementById('botModuleBadge').innerText = 'GENERAL';
            triggerCircleFade();
        }

        /* CAPTURA Y GUARDADO */
        async function triggerNativeCaptureAndSave() {
            if (video.videoWidth === 0) return;

            playWhatsAppSwooshSound();

            const flash = document.getElementById('flashLayer');
            flash.classList.add('flash');
            setTimeout(() => flash.classList.remove('flash'), 120);

            internalCanvas.width = video.videoWidth;
            internalCanvas.height = video.videoHeight;
            const ctx = internalCanvas.getContext('2d');

            // Si está en modo Scan Doc Pro, aplicar procesado de documento de alto contraste
            if (selectedEngineKey === 'scan') {
                ctx.filter = 'grayscale(100%) contrast(160%) brightness(110%)';
            } else {
                ctx.filter = 'none';
            }
            ctx.drawImage(video, 0, 0, internalCanvas.width, internalCanvas.height);

            const base64Data = internalCanvas.toDataURL('image/jpeg', 0.92);
            const tag = selectedEngineName ? `Módulo ${selectedEngineName}` : "Captura Directa Cam Vision";

            try {
                const res = await fetch('/bian/process/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ image_base64: base64Data, prompt_analysis: tag })
                });
                if (res.ok) {
                    const saved = await res.json();
                    updateThumbUI(saved.image_path);
                }
            } catch (err) {
                console.error("Error guardando foto:", err);
            }
        }

        async function refreshThumb() {
            try {
                const res = await fetch('/bian/images/');
                const list = await res.json();
                if (list.length > 0) {
                    updateThumbUI(list[list.length - 1].image_path);
                }
            } catch(e) {}
        }

        function updateThumbUI(imgPath) {
            const btn = document.getElementById('galleryThumbBtn');
            const fixedPath = imgPath.startsWith('/bian') ? imgPath : `/bian${imgPath}`;
            btn.innerHTML = `<img src="${fixedPath}" />`;
        }

        async function openGalleryModal() {
            const modal = document.getElementById('galleryModal');
            const grid = document.getElementById('galleryGrid');
            modal.classList.add('active');
            grid.innerHTML = "<p style='color:#777; font-size:12px; grid-column:span 3;'>Cargando fotos reales...</p>";

            try {
                const res = await fetch('/bian/images/');
                const list = await res.json();
                if (list.length === 0) {
                    grid.innerHTML = "<p style='color:#888; font-size:12px; grid-column:span 3;'>No hay fotos capturadas aún.</p>";
                    return;
                }
                grid.innerHTML = list.reverse().map(img => {
                    const fullUrl = img.image_path.startsWith('/bian') ? img.image_path : `/bian${img.image_path}`;
                    return `
                        <div class="gallery-item">
                            <img src="${fullUrl}" />
                        </div>
                    `;
                }).join('');
            } catch(e) {
                grid.innerHTML = "<p style='color:#f55; font-size:12px;'>Error cargando galería.</p>";
            }
        }

        function closeGalleryModal() {
            document.getElementById('galleryModal').classList.remove('active');
        }

        function openNanoBotModal() {
            document.getElementById('botModal').classList.add('active');
            document.getElementById('botUserInput').focus();
        }

        function closeNanoBotModal() {
            document.getElementById('botModal').classList.remove('active');
        }

        function askNanoQuick(text) {
            document.getElementById('botUserInput').value = text;
            sendNanoBotMessage();
        }

        async function sendNanoBotMessage() {
            const input = document.getElementById('botUserInput');
            const q = input.value.trim();
            if (!q) return;

            const chat = document.getElementById('botChatStream');
            chat.innerHTML += `<div class="bot-msg user">${q}</div>`;
            input.value = "";
            chat.scrollTop = chat.scrollHeight;

            try {
                const res = await fetch('/bian/nanobot/query', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: q, current_module: selectedEngineKey || "general" })
                });
                const data = await res.json();
                chat.innerHTML += `<div class="bot-msg ia">${data.reply}</div>`;
            } catch(e) {
                chat.innerHTML += `<div class="bot-msg ia">Nano-Bot activo localmente.</div>`;
            }
            chat.scrollTop = chat.scrollHeight;
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
        "engine": "Samsung Native Camera Core V9 (CamScanner Pro & OCR Integration)",
        "status": "online"
    }

@router.post("/process/", response_model=ProcessedImage)
def process_image(payload: ImageCaptureRequest, session: Session = Depends(get_session)):
    os.makedirs("storage/bian", exist_ok=True)
    filename = f"storage/bian/photo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    
    header, encoded = payload.image_base64.split(",", 1) if "," in payload.image_base64 else ("", payload.image_base64)
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

@router.post("/nanobot/query")
def nanobot_query(payload: NanoBotQuery):
    msg = payload.message.lower()
    mod = payload.current_module

    if "scan" in msg or "doc" in msg or "escan" in msg or "ticket" in msg or "factura" in msg:
        return {
            "reply": "📄 <strong>Scan Doc Pro:</strong> Alinea el documento o ticket dentro del marco verde. Al disparar, el sistema elimina las sombras, aclara el fondo blanco a nivel de imprenta y prepara el texto para OCR instantáneo."
        }
    elif "noche" in msg or "night" in msg:
        return {
            "reply": "🌙 <strong>Nightography:</strong> Activa el sensor para condiciones de baja luz, simulando mayor tiempo de exposición y reducción de ruido en sombras profundas."
        }
    elif "macro" in msg:
        return {
            "reply": "🔍 <strong>Macro Pro:</strong> Optimizado para capturar detalles a milímetros de distancia con realce de texturas finas (carnes, papel, telas o componentes)."
        }
    elif "retrato" in msg or "portrait" in msg or "bokeh" in msg:
        return {
            "reply": "👤 <strong>Modo Retrato Bokeh:</strong> Aisla el sujeto en primer plano y desenfoca suavemente el fondo con apertura f/1.4."
        }
    elif "carne" in msg or "chef" in msg or "merma" in msg or "porci" in msg:
        return {
            "reply": "🥩 <strong>Chef Lean:</strong> Toma la foto del corte. Descuenta mermas (13-14%) y entrega el porcionado exacto y costeo directo."
        }
    elif "lona" in msg or "viento" in msg:
        return {
            "reply": "⛺ <strong>Lonas 3D:</strong> Captura la estructura para calcular resistencia eólica (40 a 90 km/h) y distribución perimetral de ojillos."
        }
    else:
        return {
            "reply": f"🎯 Tienes a la mano <strong>📄 Scan Doc</strong>, <strong>🌙 Noche</strong>, <strong>🔍 Macro</strong>, <strong>👤 Retrato</strong> y las herramientas de taller y negocio. Dispara y se guarda en tu galería."
        }
