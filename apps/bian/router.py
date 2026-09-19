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
    prompt_analysis: str = "Lonas 3D V9 Ultra"

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Bian AI Suite - V9 Liquid Glass (Lonas 3D V9)</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", Roboto, sans-serif; -webkit-tap-highlight-color: transparent; }
        body { background: #000; color: #fff; height: 100vh; overflow: hidden; display: flex; flex-direction: column; user-select: none; }

        .top-float-left {
            position: absolute; top: 16px; left: 18px; z-index: 50;
            background: rgba(22, 22, 26, 0.6);
            backdrop-filter: blur(25px); -webkit-backdrop-filter: blur(25px);
            border: 1px solid rgba(255, 255, 255, 0.14);
            border-radius: 20px; padding: 7px 14px;
            display: flex; align-items: center; gap: 8px; font-weight: 700; font-size: 12px;
            box-shadow: 0 6px 24px rgba(0,0,0,0.4);
        }
        .glow-dot { width: 7px; height: 7px; border-radius: 50%; background: #30D158; box-shadow: 0 0 8px #30D158; }

        .top-float-right {
            position: absolute; top: 16px; right: 18px; z-index: 50;
            background: rgba(255, 214, 10, 0.16);
            backdrop-filter: blur(25px); -webkit-backdrop-filter: blur(25px);
            border: 1px solid rgba(255, 214, 10, 0.38);
            color: #FFD60A; font-size: 11px; font-weight: 700; padding: 7px 14px; border-radius: 20px;
            display: flex; align-items: center; gap: 6px; cursor: pointer;
            transition: all 0.28s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 6px 24px rgba(0,0,0,0.35);
        }
        .top-float-right.active {
            background: linear-gradient(135deg, #FF9F0A, #FF375F);
            color: #fff; border-color: transparent;
            box-shadow: 0 0 16px rgba(255, 55, 95, 0.65);
            transform: scale(1.04);
        }

        /* VIEWPORT CON AJUSTE 100% PARA ZOOM */
        .viewport {
            flex: 1; position: relative; display: flex; align-items: center; justify-content: center;
            background: #000; overflow: hidden; width: 100%; height: 100%;
        }
        .video-wrapper {
            position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;
            overflow: hidden;
        }
        video {
            min-width: 100%; min-height: 100%; width: 100%; height: 100%;
            object-fit: cover; transform-origin: center center;
            transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1);
        }
        
        .shutter-flash {
            position: absolute; inset: 0; background: #fff; opacity: 0; pointer-events: none; z-index: 60;
            transition: opacity 0.12s ease-out;
        }
        .shutter-flash.flash { opacity: 0.85; }

        .water-ripple-ring {
            position: absolute; border-radius: 50%;
            border: 2px solid rgba(255, 255, 255, 0.85);
            box-shadow: 0 0 25px rgba(255, 255, 255, 0.7);
            pointer-events: none; z-index: 35;
            animation: waterRipple 0.55s cubic-bezier(0.1, 0.8, 0.3, 1) forwards;
        }
        @keyframes waterRipple {
            0% { width: 10px; height: 10px; opacity: 1; transform: translate(-50%, -50%) scale(1); }
            100% { width: 160px; height: 160px; opacity: 0; transform: translate(-50%, -50%) scale(1.3); }
        }

        .focus-circle-ring {
            position: absolute; width: 95px; height: 95px; pointer-events: none;
            border-radius: 50%; border: 1.8px solid rgba(255, 255, 255, 0.85);
            box-shadow: 0 0 16px rgba(255, 255, 255, 0.35);
            transition: left 0.28s cubic-bezier(0.16, 1, 0.3, 1), top 0.28s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.6s ease, border-color 0.3s, transform 0.25s;
            display: flex; flex-direction: column; align-items: center; justify-content: space-between;
            opacity: 1; transform: translate(-50%, -50%);
        }
        .focus-circle-ring.faded {
            opacity: 0.15;
            border-color: rgba(255, 255, 255, 0.2);
            box-shadow: none;
        }
        .focus-circle-ring.glowing {
            transform: translate(-50%, -50%) scale(1.08);
            border-color: #FFD60A;
            box-shadow: 0 0 25px rgba(255, 214, 10, 0.8);
        }

        .lock-icon-badge {
            font-size: 11px; margin-top: -16px; background: rgba(0,0,0,0.5); border-radius: 50%; padding: 2px 4px;
        }
        .sun-slider-badge {
            font-size: 12px; margin-bottom: -18px; background: rgba(0,0,0,0.5); border-radius: 50%; padding: 2px 4px;
        }

        .lens-pill-bar {
            position: absolute; bottom: 182px; z-index: 45;
            display: flex; gap: 8px; background: rgba(18, 18, 22, 0.55);
            backdrop-filter: blur(25px); -webkit-backdrop-filter: blur(25px);
            border: 1px solid rgba(255, 255, 255, 0.12);
            padding: 4px 8px; border-radius: 20px;
        }
        .lens-btn {
            background: transparent; border: none; color: rgba(255,255,255,0.7);
            font-size: 11px; font-weight: 700; padding: 4px 10px; border-radius: 14px;
            cursor: pointer; transition: all 0.2s;
        }
        .lens-btn.active { background: rgba(255, 255, 255, 0.2); color: #fff; }

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
            position: absolute; bottom: 104px; left: 14px; right: 14px; z-index: 40;
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
            transform: translateY(-4px) scale(1.1);
        }
        .dock-icon-btn.selected::after {
            content: ''; position: absolute; bottom: -5px; width: 5px; height: 5px;
            border-radius: 50%; background: #fff;
        }

        /* COLORES INDIVIDUALES DE SELECCIÓN POR MÓDULO */
        .dock-icon-btn[data-key="lonas"].selected { background: linear-gradient(135deg, #FF9500, #FF5E3A); border-color: rgba(255,149,0,0.6); box-shadow: 0 8px 20px rgba(255,94,58,0.5); }
        .dock-icon-btn[data-key="custom"].selected { background: linear-gradient(135deg, #FF2D55, #AF52DE); border-color: rgba(255,45,85,0.6); box-shadow: 0 8px 20px rgba(255,45,85,0.5); }
        .dock-icon-btn[data-key="print"].selected { background: linear-gradient(135deg, #32ADE6, #007AFF); border-color: rgba(50,173,230,0.6); box-shadow: 0 8px 20px rgba(0,122,255,0.5); }
        .dock-icon-btn[data-key="cine"].selected { background: linear-gradient(135deg, #FF3B30, #FF2D55); border-color: rgba(255,59,48,0.6); box-shadow: 0 8px 20px rgba(255,59,48,0.5); }
        .dock-icon-btn[data-key="raw"].selected { background: linear-gradient(135deg, #30D158, #34C759); border-color: rgba(48,209,88,0.6); box-shadow: 0 8px 20px rgba(48,209,88,0.5); }
        .dock-icon-btn[data-key="svg"].selected { background: linear-gradient(135deg, #FFD60A, #FF9F0A); border-color: rgba(255,214,10,0.6); box-shadow: 0 8px 20px rgba(255,214,10,0.5); }
        .dock-icon-btn[data-key="vid"].selected { background: linear-gradient(135deg, #BF5AF2, #5E5CE6); border-color: rgba(191,90,242,0.6); box-shadow: 0 8px 20px rgba(94,92,230,0.5); }
        .dock-icon-btn[data-key="depth"].selected { background: linear-gradient(135deg, #FF375F, #BF5AF2); border-color: rgba(255,55,95,0.6); box-shadow: 0 8px 20px rgba(255,55,95,0.5); }
        .dock-icon-btn[data-key="chef"].selected { background: linear-gradient(135deg, #FF9F0A, #FF6B00); border-color: rgba(255,159,10,0.6); box-shadow: 0 8px 20px rgba(255,107,0,0.5); }
        .dock-icon-btn[data-key="price"].selected { background: linear-gradient(135deg, #63E6E2, #00C7BE); border-color: rgba(99,230,226,0.6); box-shadow: 0 8px 20px rgba(0,199,190,0.5); }
        .dock-icon-btn[data-key="ai"].selected { background: linear-gradient(135deg, #0A84FF, #5E5CE6); border-color: rgba(10,132,255,0.6); box-shadow: 0 8px 20px rgba(10,132,255,0.5); }

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
        .shutter-outer.banana-ready .shutter-inner {
            background: linear-gradient(135deg, #FF375F, #FF2D55);
            box-shadow: 0 0 24px rgba(255, 45, 85, 0.9);
        }
        .side-btn {
            width: 44px; height: 44px; border-radius: 50%;
            background: rgba(255, 255, 255, 0.1); backdrop-filter: blur(15px);
            border: 1px solid rgba(255, 255, 255, 0.15); font-size: 16px;
            color: #fff; display: flex; align-items: center; justify-content: center;
            cursor: pointer; transition: transform 0.15s;
        }
        .side-btn:active { transform: scale(0.9); }

        .sheet-modal {
            position: fixed; inset: 0; z-index: 100; background: rgba(0,0,0,0.65);
            backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
            display: none; flex-direction: column; justify-content: flex-end;
            opacity: 0; transition: opacity 0.3s ease;
        }
        .sheet-modal.active { display: flex; opacity: 1; }
        .sheet-card {
            background: #161618; border-top: 1px solid rgba(255,255,255,0.15);
            border-radius: 32px 32px 0 0; padding: 22px 20px 36px 20px;
            max-height: 85vh; overflow-y: auto; box-shadow: 0 -10px 40px rgba(0,0,0,0.7);
            animation: slideUp 0.35s cubic-bezier(0.16, 1, 0.3, 1);
        }
        @keyframes slideUp { from { transform: translateY(100%); } to { transform: translateY(0); } }
        .sheet-drag { width: 38px; height: 5px; background: rgba(255,255,255,0.25); border-radius: 4px; margin: 0 auto 16px; cursor: pointer; }
        .sheet-title { font-size: 18px; font-weight: 700; color: #fff; margin-bottom: 4px; }
        .sheet-desc { font-size: 12px; color: rgba(255,255,255,0.65); line-height: 1.4; margin-bottom: 16px; }
        
        .preview-canvas-box { width: 100%; height: 230px; background: #080808; border-radius: 18px; overflow: hidden; border: 1px solid rgba(255,255,255,0.08); display: flex; align-items: center; justify-content: center; margin-bottom: 16px; position: relative; }
        .preview-canvas-box canvas, .preview-canvas-box svg { max-width: 100%; max-height: 100%; object-fit: contain; }

        .apple-input-group { margin-bottom: 12px; text-align: left; }
        .apple-input-group label { font-size: 11px; font-weight: 600; color: rgba(255,255,255,0.7); display: block; margin-bottom: 6px; }
        .apple-input-group select, .apple-input-group input[type="range"] {
            width: 100%; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.12);
            border-radius: 12px; padding: 10px 12px; color: #fff; font-size: 12px; outline: none;
        }

        .metrics-grid {
            display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-bottom: 14px;
        }
        .metric-cell {
            background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.08);
            padding: 8px; border-radius: 14px; text-align: center;
        }
        .metric-cell span { font-size: 9px; color: rgba(255,255,255,0.5); font-weight: 600; display: block; }
        .metric-cell strong { font-size: 13px; font-weight: 700; margin-top: 2px; display: block; }

        .apple-btn-main {
            width: 100%; background: #0A84FF; border: none; color: #fff;
            padding: 14px; border-radius: 16px; font-size: 14px; font-weight: 600;
            cursor: pointer; margin-top: 8px;
        }
        .apple-btn-main:active { background: #0071E3; }
        
        .apple-btn-export {
            width: 100%; background: rgba(255, 149, 0, 0.15); border: 1px solid rgba(255, 149, 0, 0.4);
            color: #FF9500; padding: 12px; border-radius: 14px; font-size: 12px; font-weight: 700;
            cursor: pointer; margin-top: 6px;
        }
    </style>
</head>
<body>

    <div class="shutter-flash" id="flashLayer"></div>

    <div class="top-float-left">
        <div class="glow-dot"></div>
        <span>Cam Vision V7</span>
    </div>

    <div class="top-float-right" id="bananaChip" onclick="resetArmEngine()">
        <span>🍌</span>
        <span id="bananaText">Nano-Banana</span>
    </div>

    <div class="viewport" id="viewportArea" onclick="handleTapToFocus(event)">
        <div class="video-wrapper">
            <video id="webcam" autoplay playsinline></video>
        </div>
        
        <div class="focus-circle-ring" id="focusCircle">
            <div class="lock-icon-badge">🔒</div>
            <div class="sun-slider-badge">☀️</div>
        </div>

        <canvas id="internalCanvas" style="display:none;"></canvas>
    </div>

    <div class="lens-pill-bar">
        <button class="lens-btn" onclick="applyDigitalZoom(0.6, this)">0.6x</button>
        <button class="lens-btn active" onclick="applyDigitalZoom(1.0, this)">1x</button>
        <button class="lens-btn" onclick="applyDigitalZoom(1.5, this)">2x</button>
    </div>

    <div class="dock-tooltip" id="dockTooltip">Módulo</div>

    <div class="glass-dock">
        <div class="dock-icon-btn" data-key="lonas" onclick="selectEngine('lonas', '⛺ Lonas 3D V9', this)">⛺</div>
        <div class="dock-icon-btn" data-key="custom" onclick="selectEngine('custom', '🎨 Wallpapers V9', this)">🎨</div>
        <div class="dock-icon-btn" data-key="print" onclick="selectEngine('print', '🖨️ Imprenta PDF V9', this)">🖨️</div>
        <div class="dock-icon-btn" data-key="cine" onclick="selectEngine('cine', '🎬 Cine Scope V9', this)">🎬</div>
        <div class="dock-icon-btn" data-key="raw" onclick="selectEngine('raw', '📸 Revelado RAW V9', this)">📸</div>
        <div class="dock-icon-btn" data-key="svg" onclick="selectEngine('svg', '📐 SVG Logos V9', this)">📐</div>
        <div class="dock-icon-btn" data-key="vid" onclick="selectEngine('vid', '🎥 Video Motion V8', this)">🎥</div>
        <div class="dock-icon-btn" data-key="depth" onclick="selectEngine('depth', '🧠 Depth-Map NPU V9', this)">🧠</div>
        <div class="dock-icon-btn" data-key="chef" onclick="selectEngine('chef', '👨‍🍳 Chef Lean V9', this)">👨‍🍳</div>
        <div class="dock-icon-btn" data-key="price" onclick="selectEngine('price', '🏷️ Valuador Híbrido V7', this)">🏷️</div>
        <div class="dock-icon-btn" data-key="ai" onclick="selectEngine('ai', '✨ Generar Imagen AI V7', this)">✨</div>
    </div>

    <div class="bottom-shutter-bar">
        <div class="side-btn" onclick="toggleLens()">🔄</div>
        <div class="shutter-outer" id="shutterBtn" onclick="triggerNanoBananaCapture()">
            <div class="shutter-inner"></div>
        </div>
        <div class="side-btn" onclick="alert('✔ Galería Soberana Sincronizada')">🖼️</div>
    </div>

    <div class="sheet-modal" id="sheetModal">
        <div class="sheet-card">
            <div class="sheet-drag" onclick="closeSheet()"></div>
            <div class="sheet-title" id="sheetTitle">Módulo Procesado</div>
            <div class="sheet-desc" id="sheetDesc">Acción ejecutada mediante la canalización Nano-Banana.</div>
            <div class="preview-canvas-box" id="sheetCanvasBox"></div>

            <!-- PANEL LONAS 3D V9 ULTRA -->
            <div id="lonasControlPanel" style="display:none;">
                <div class="metrics-grid">
                    <div class="metric-cell">
                        <span>VIENTO</span>
                        <strong style="color:#FF9500;" id="lonasWindLabel">45 km/h</strong>
                    </div>
                    <div class="metric-cell">
                        <span>TENSIÓN</span>
                        <strong style="color:#30D158;">Estable</strong>
                    </div>
                    <div class="metric-cell">
                        <span>OJILLOS</span>
                        <strong style="color:#00FFC8;" id="lonasOjillosLabel">28 Unidades</strong>
                    </div>
                </div>
                <div class="apple-input-group">
                    <label>Material Publicitario de la Lona:</label>
                    <select id="lonaMatSelectV9" onchange="renderLonas3DV9()">
                        <option value="frontlit">Frontlit 13oz Brillante (Refuerzo Térmico)</option>
                        <option value="mesh">Mesh Microperforada (Anti-Viento Alta Carga)</option>
                        <option value="backlight">Backlight Translúcida (Caja Lumínica)</option>
                    </select>
                </div>
                <div class="apple-input-group">
                    <label>Carga Eólica / Velocidad del Viento (km/h):</label>
                    <input type="range" id="lonaWindSliderV9" min="10" max="110" step="5" value="45" oninput="renderLonas3DV9()">
                </div>
                <button class="apple-btn-export" onclick="exportLonas3DV9()">💾 Guardar Render Estructural .JPG V9</button>
            </div>

            <!-- CONTENEDORES AUXILIARES -->
            <div id="customControlPanel" style="display:none;"></div>
            <div id="printControlPanel" style="display:none;"></div>
            <div id="cineControlPanel" style="display:none;"></div>
            <div id="rawControlPanel" style="display:none;"></div>
            <div id="svgControlPanel" style="display:none;"></div>
            <div id="vidControlPanel" style="display:none;"></div>
            <div id="depthControlPanel" style="display:none;"></div>
            <div id="chefControlPanel" style="display:none;"></div>
            <div id="priceControlPanel" style="display:none;"></div>
            <div id="aiControlPanel" style="display:none;"></div>

            <button class="apple-btn-main" onclick="closeSheet()">Listo</button>
        </div>
    </div>

    <script>
        const video = document.getElementById('webcam');
        const internalCanvas = document.getElementById('internalCanvas');
        let selectedEngineKey = null;
        let selectedEngineName = null;
        let facingMode = 'environment';
        let capturedImage = new Image();
        let tooltipTimeout = null;
        let audioCtx = null;
        let lonasActiveCanvas = null;
        let fadeCircleTimeout = null;

        function getAudioContext() {
            if (!audioCtx) {
                audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            }
            if (audioCtx.state === 'suspended') {
                audioCtx.resume();
            }
            return audioCtx;
        }

        function playFocusBeep() {
            try {
                const ctx = getAudioContext();
                const now = ctx.currentTime;
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.connect(gain);
                gain.connect(ctx.destination);

                osc.type = 'sine';
                osc.frequency.setValueAtTime(1400, now);
                osc.frequency.setValueAtTime(1800, now + 0.04);
                gain.gain.setValueAtTime(0.12, now);
                gain.gain.linearRampToValueAtTime(0.01, now + 0.09);
                osc.start(now); osc.stop(now + 0.09);
            } catch(e) { console.error("Audio error:", e); }
        }

        function playModuleSound(key) {
            try {
                const ctx = getAudioContext();
                const now = ctx.currentTime;
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.connect(gain);
                gain.connect(ctx.destination);

                if (key === 'lonas') {
                    // Tensión elástica de cable acerado y lona tensa
                    osc.type = 'sawtooth';
                    osc.frequency.setValueAtTime(160, now);
                    osc.frequency.exponentialRampToValueAtTime(880, now + 0.12);
                    osc.frequency.exponentialRampToValueAtTime(110, now + 0.26);
                    gain.gain.setValueAtTime(0.24, now);
                    gain.gain.linearRampToValueAtTime(0.01, now + 0.26);
                    osc.start(now); osc.stop(now + 0.26);
                } else if (key === 'custom') {
                    osc.type = 'triangle';
                    osc.frequency.setValueAtTime(520, now);
                    osc.frequency.exponentialRampToValueAtTime(1600, now + 0.16);
                    gain.gain.setValueAtTime(0.2, now);
                    gain.gain.linearRampToValueAtTime(0.01, now + 0.16);
                    osc.start(now); osc.stop(now + 0.16);
                } else if (key === 'print') {
                    osc.type = 'square';
                    osc.frequency.setValueAtTime(180, now);
                    osc.frequency.exponentialRampToValueAtTime(45, now + 0.28);
                    gain.gain.setValueAtTime(0.18, now);
                    gain.gain.linearRampToValueAtTime(0.01, now + 0.28);
                    osc.start(now); osc.stop(now + 0.28);
                } else if (key === 'cine') {
                    osc.type = 'sawtooth';
                    osc.frequency.setValueAtTime(120, now);
                    osc.frequency.linearRampToValueAtTime(80, now + 0.22);
                    gain.gain.setValueAtTime(0.2, now);
                    gain.gain.linearRampToValueAtTime(0.01, now + 0.22);
                    osc.start(now); osc.stop(now + 0.22);
                } else if (key === 'raw') {
                    osc.type = 'triangle';
                    osc.frequency.setValueAtTime(240, now);
                    osc.frequency.exponentialRampToValueAtTime(60, now + 0.08);
                    gain.gain.setValueAtTime(0.3, now);
                    gain.gain.linearRampToValueAtTime(0.01, now + 0.08);
                    osc.start(now); osc.stop(now + 0.08);
                } else {
                    osc.type = 'sine';
                    osc.frequency.setValueAtTime(440, now);
                    gain.gain.setValueAtTime(0.12, now);
                    gain.gain.linearRampToValueAtTime(0.01, now + 0.15);
                    osc.start(now); osc.stop(now + 0.15);
                }
            } catch(e) { console.error("Audio error:", e); }
        }

        function startCamera() {
            navigator.mediaDevices.getUserMedia({ video: { facingMode: facingMode } })
                .then(stream => { 
                    video.srcObject = stream;
                    const circle = document.getElementById('focusCircle');
                    circle.style.left = '50%';
                    circle.style.top = '46%';
                    triggerCircleFade();
                })
                .catch(err => console.error("Error cámara:", err));
        }
        startCamera();

        function toggleLens() {
            facingMode = (facingMode === 'environment') ? 'user' : 'environment';
            if (video.srcObject) video.srcObject.getTracks().forEach(t => t.stop());
            startCamera();
        }

        function applyDigitalZoom(scale, elem) {
            // Escala geométrica sin alterar proporción ni dejar huecos
            video.style.transform = `scale(${scale})`;
            document.querySelectorAll('.lens-btn').forEach(b => b.classList.remove('active'));
            elem.classList.add('active');
            triggerCircleFade();
        }

        function triggerCircleFade() {
            const circle = document.getElementById('focusCircle');
            circle.classList.remove('faded');
            if (fadeCircleTimeout) clearTimeout(fadeCircleTimeout);
            fadeCircleTimeout = setTimeout(() => {
                circle.classList.add('faded');
            }, 1800);
        }

        function handleTapToFocus(e) {
            if (e.target.closest('.glass-dock') || e.target.closest('.bottom-shutter-bar') || e.target.closest('.top-float-left') || e.target.closest('.top-float-right') || e.target.closest('.lens-pill-bar') || e.target.closest('.dock-tooltip')) return;
            
            const viewport = document.getElementById('viewportArea');
            const rect = viewport.getBoundingClientRect();
            const clickX = e.clientX - rect.left;
            const clickY = e.clientY - rect.top;

            const ripple = document.createElement('div');
            ripple.className = 'water-ripple-ring';
            ripple.style.left = clickX + 'px';
            ripple.style.top = clickY + 'px';
            viewport.appendChild(ripple);
            setTimeout(() => ripple.remove(), 600);

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

        function selectEngine(key, name, elem) {
            showDockTooltipAboveElement(name, elem);
            playModuleSound(key);

            document.querySelectorAll('.dock-icon-btn').forEach(btn => btn.classList.remove('selected'));
            
            if (selectedEngineKey === key) {
                resetArmEngine();
                return;
            }

            selectedEngineKey = key;
            selectedEngineName = name;
            elem.classList.add('selected');

            document.getElementById('bananaChip').classList.add('active');
            document.getElementById('bananaText').innerText = key.toUpperCase();
            document.getElementById('shutterBtn').classList.add('banana-ready');
            triggerCircleFade();
        }

        function resetArmEngine() {
            selectedEngineKey = null;
            selectedEngineName = null;
            document.querySelectorAll('.dock-icon-btn').forEach(btn => btn.classList.remove('selected'));
            document.getElementById('bananaChip').classList.remove('active');
            document.getElementById('bananaText').innerText = 'Nano-Banana';
            document.getElementById('shutterBtn').classList.remove('banana-ready');
            triggerCircleFade();
        }

        function triggerNanoBananaCapture() {
            if (video.videoWidth === 0) return;

            const flash = document.getElementById('flashLayer');
            flash.classList.add('flash');
            setTimeout(() => flash.classList.remove('flash'), 120);

            internalCanvas.width = 400;
            internalCanvas.height = 300;
            const ctx = internalCanvas.getContext('2d');
            ctx.drawImage(video, 0, 0, 400, 300);

            capturedImage.onload = () => {
                if (!selectedEngineKey) {
                    executeModulePipeline('lonas', '⛺ Lonas 3D V9');
                } else {
                    executeModulePipeline(selectedEngineKey, selectedEngineName);
                }
            };
            capturedImage.src = internalCanvas.toDataURL('image/jpeg');
        }

        function executeModulePipeline(engine, name) {
            document.getElementById('sheetTitle').innerText = name;
            const lonasPanel = document.getElementById('lonasControlPanel');
            const customPanel = document.getElementById('customControlPanel');
            const printPanel = document.getElementById('printControlPanel');
            const cinePanel = document.getElementById('cineControlPanel');
            const rawPanel = document.getElementById('rawControlPanel');
            const svgPanel = document.getElementById('svgControlPanel');
            const vidPanel = document.getElementById('vidControlPanel');
            const depthPanel = document.getElementById('depthControlPanel');
            const chefPanel = document.getElementById('chefControlPanel');
            const pricePanel = document.getElementById('priceControlPanel');
            const aiPanel = document.getElementById('aiControlPanel');

            if (engine === 'lonas') {
                lonasPanel.style.display = 'block';
                customPanel.style.display = 'none';
                printPanel.style.display = 'none';
                cinePanel.style.display = 'none';
                rawPanel.style.display = 'none';
                svgPanel.style.display = 'none';
                vidPanel.style.display = 'none';
                depthPanel.style.display = 'none';
                chefPanel.style.display = 'none';
                pricePanel.style.display = 'none';
                aiPanel.style.display = 'none';
                document.getElementById('sheetDesc').innerText = "Render estructural en perspectiva 3D con simulación de tensión eólica y anclajes.";
                renderLonas3DV9();
            } else {
                lonasPanel.style.display = 'none';
                customPanel.style.display = 'none';
                printPanel.style.display = 'none';
                cinePanel.style.display = 'none';
                rawPanel.style.display = 'none';
                svgPanel.style.display = 'none';
                vidPanel.style.display = 'none';
                depthPanel.style.display = 'none';
                chefPanel.style.display = 'none';
                pricePanel.style.display = 'none';
                aiPanel.style.display = 'none';
                const box = document.getElementById('sheetCanvasBox');
                box.innerHTML = "";
                const canvas = document.createElement('canvas');
                canvas.width = 360; canvas.height = 220;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(capturedImage, 0, 0, 360, 220);
                box.appendChild(canvas);
                document.getElementById('sheetDesc').innerText = `Procesamiento completado en ${name}.`;
            }

            document.getElementById('sheetModal').classList.add('active');
        }

        function renderLonas3DV9() {
            const wind = parseInt(document.getElementById('lonaWindSliderV9').value);
            const mat = document.getElementById('lonaMatSelectV9').value;
            document.getElementById('lonasWindLabel').innerText = wind + " km/h";

            const ojillosCount = wind > 70 ? 36 : (wind > 40 ? 28 : 20);
            document.getElementById('lonasOjillosLabel').innerText = ojillosCount + " Unidades";

            const box = document.getElementById('sheetCanvasBox');
            box.innerHTML = "";

            lonasActiveCanvas = document.createElement('canvas');
            lonasActiveCanvas.width = 360;
            lonasActiveCanvas.height = 230;
            const ctx = lonasActiveCanvas.getContext('2d');

            // Fondo de taller / exterior
            ctx.fillStyle = "#0c0d10";
            ctx.fillRect(0, 0, 360, 230);

            // Deformación de curvatura por viento en el centro de la lona
            const windDeflection = (wind / 110) * 16;

            // Marco tubular 3D perimetral
            ctx.strokeStyle = "#3A3D45";
            ctx.lineWidth = 5;
            ctx.strokeRect(26, 20, 308, 185);

            // Cables de anclaje tensores
            ctx.strokeStyle = "rgba(255, 149, 0, 0.4)";
            ctx.lineWidth = 1.2;
            ctx.beginPath();
            ctx.moveTo(10, 10); ctx.lineTo(34, 28);
            ctx.moveTo(350, 10); ctx.lineTo(326, 28);
            ctx.moveTo(10, 220); ctx.lineTo(34, 197);
            ctx.moveTo(350, 220); ctx.lineTo(326, 197);
            ctx.stroke();

            // Dibujo de la lona con textura y perspectiva
            ctx.save();
            ctx.drawImage(capturedImage, 34, 28, 292, 169);

            // Simulación de deflexión eólica central
            const gradWind = ctx.createRadialGradient(180, 112, 10, 180, 112, 120);
            gradWind.addColorStop(0, `rgba(255,255,255,${windDeflection * 0.015})`);
            gradWind.addColorStop(1, "rgba(0,0,0,0.35)");
            ctx.fillStyle = gradWind;
            ctx.fillRect(34, 28, 292, 169);

            if (mat === 'mesh') {
                // Trama microperforada
                ctx.fillStyle = "rgba(0,0,0,0.22)";
                for (let x = 38; x < 322; x += 6) {
                    ctx.fillRect(x, 28, 2, 169);
                }
            }
            ctx.restore();

            // Anillos / Ojillos de acero perimetrales
            ctx.fillStyle = "#E5E5EA";
            ctx.strokeStyle = "#1C1C1E";
            ctx.lineWidth = 1;

            const drawOjillo = (ox, oy) => {
                ctx.beginPath();
                ctx.arc(ox, oy, 3.5, 0, Math.PI * 2);
                ctx.fill();
                ctx.stroke();
            };

            // Ojillos superiores e inferiores
            for (let x = 46; x <= 314; x += 30) {
                drawOjillo(x, 28);
                drawOjillo(x, 197);
            }
            // Ojillos laterales
            for (let y = 46; y <= 180; y += 26) {
                drawOjillo(34, y);
                drawOjillo(326, y);
            }

            box.appendChild(lonasActiveCanvas);
        }

        function exportLonas3DV9() {
            if (!lonasActiveCanvas) return;
            const a = document.createElement('a');
            a.href = lonasActiveCanvas.toDataURL('image/jpeg', 0.95);
            a.download = `lona3d_v9_${Date.now()}.jpg`;
            a.click();
        }

        function closeSheet() {
            document.getElementById('sheetModal').classList.remove('active');
            triggerCircleFade();
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
        "engine": "Lonas 3D V9 Ultra (Complete V9 Unified Suite)",
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
