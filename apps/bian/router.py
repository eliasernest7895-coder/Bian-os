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
    prompt_analysis: str = "Wallpapers & Stickers V9 Ultra"

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Bian AI Suite - V9 Liquid Glass (Wallpapers & Stickers V9)</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", Roboto, sans-serif; -webkit-tap-highlight-color: transparent; }
        body { background: #000; color: #fff; height: 100vh; overflow: hidden; display: flex; flex-direction: column; user-select: none; }

        /* HEADER DESARTICULADO (SIN BLOQUE CONTENEDOR) */
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

        .viewport { flex: 1; position: relative; display: flex; align-items: center; justify-content: center; background: #000; overflow: hidden; }
        video { width: 100%; height: 100%; object-fit: cover; }
        
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
            background: linear-gradient(135deg, #0A84FF, #5E5CE6);
            border-color: rgba(255,255,255,0.4);
            transform: translateY(-4px) scale(1.1);
            box-shadow: 0 8px 20px rgba(94, 92, 230, 0.5);
        }
        .dock-icon-btn.selected::after {
            content: ''; position: absolute; bottom: -5px; width: 5px; height: 5px;
            border-radius: 50%; background: #fff;
        }

        /* BOTON DE CAPTURA ROJO CINE */
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
        
        .dual-export-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 6px; }
        .apple-btn-export-half {
            background: rgba(255, 255, 255, 0.08); border: 1px solid rgba(255, 255, 255, 0.2);
            color: #fff; padding: 12px; border-radius: 14px; font-size: 11px; font-weight: 700;
            cursor: pointer; text-align: center;
        }
        .apple-btn-export-half.highlight {
            background: rgba(255, 45, 85, 0.2); border-color: rgba(255, 45, 85, 0.45);
            color: #FF2D55;
        }
    </style>
</head>
<body>

    <div class="shutter-flash" id="flashLayer"></div>

    <!-- CHIPS FLOTANTES INDEPENDIENTES -->
    <div class="top-float-left">
        <div class="glow-dot"></div>
        <span>Cam Vision V7</span>
    </div>

    <div class="top-float-right" id="bananaChip" onclick="resetArmEngine()">
        <span>🍌</span>
        <span id="bananaText">Nano-Banana</span>
    </div>

    <div class="viewport" id="viewportArea" onclick="handleTapToFocus(event)">
        <video id="webcam" autoplay playsinline></video>
        
        <div class="focus-circle-ring" id="focusCircle">
            <div class="lock-icon-badge">🔒</div>
            <div class="sun-slider-badge">☀️</div>
        </div>

        <canvas id="internalCanvas" style="display:none;"></canvas>
    </div>

    <div class="lens-pill-bar">
        <button class="lens-btn" onclick="applyDigitalZoom(0.8, this)">0.6x</button>
        <button class="lens-btn active" onclick="applyDigitalZoom(1.0, this)">1x</button>
        <button class="lens-btn" onclick="applyDigitalZoom(1.5, this)">2x</button>
    </div>

    <div class="dock-tooltip" id="dockTooltip">Módulo</div>

    <div class="glass-dock">
        <div class="dock-icon-btn" onclick="selectEngine('custom', '🎨 Wallpapers & Stickers V9', this)">🎨</div>
        <div class="dock-icon-btn" onclick="selectEngine('print', '🖨️ Imprenta PDF V9', this)">🖨️</div>
        <div class="dock-icon-btn" onclick="selectEngine('cine', '🎬 Cine Scope V9', this)">🎬</div>
        <div class="dock-icon-btn" onclick="selectEngine('raw', '📸 Revelado RAW V9', this)">📸</div>
        <div class="dock-icon-btn" onclick="selectEngine('svg', '📐 SVG Logos V9', this)">📐</div>
        <div class="dock-icon-btn" onclick="selectEngine('vid', '🎥 Video Motion V8', this)">🎥</div>
        <div class="dock-icon-btn" onclick="selectEngine('depth', '🧠 Depth-Map NPU V9', this)">🧠</div>
        <div class="dock-icon-btn" onclick="selectEngine('chef', '👨‍🍳 Chef Lean V9', this)">👨‍🍳</div>
        <div class="dock-icon-btn" onclick="selectEngine('price', '🏷️ Valuador Híbrido V7', this)">🏷️</div>
        <div class="dock-icon-btn" onclick="selectEngine('ai', '✨ Generar Imagen AI V7', this)">✨</div>
        <div class="dock-icon-btn" onclick="selectEngine('lonas', '⛺ Lonas 3D Tensión', this)">⛺</div>
    </div>

    <!-- BARRA CON BOTÓN ROJO CINEMÁTICO -->
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

            <!-- PANEL WALLPAPERS & STICKERS V9 -->
            <div id="customControlPanel" style="display:none;">
                <div class="metrics-grid">
                    <div class="metric-cell">
                        <span>ESTILO</span>
                        <strong style="color:#FF2D55;" id="stickerStyleLabel">Die-Cut</strong>
                    </div>
                    <div class="metric-cell">
                        <span>FONDO</span>
                        <strong style="color:#00FFC8;">AMOLED Puro</strong>
                    </div>
                    <div class="metric-cell">
                        <span>BORDE</span>
                        <strong style="color:#FFD60A;" id="stickerBorderLabel">4.0 mm</strong>
                    </div>
                </div>
                <div class="apple-input-group">
                    <label>Modo de Procesamiento V9:</label>
                    <select id="stickerModeSelectV9" onchange="renderStickersV9()">
                        <option value="die_cut">Sticker Troquelado Die-Cut (Reborde Blanco)</option>
                        <option value="amoled_wp">Wallpaper AMOLED Deep Black (#000000 Puro)</option>
                        <option value="cyber_pop">Sticker Holográfico Neón Pop</option>
                    </select>
                </div>
                <div class="apple-input-group">
                    <label>Grosor del Borde Die-Cut:</label>
                    <input type="range" id="stickerBorderSliderV9" min="2" max="10" step="1" value="4" oninput="renderStickersV9()">
                </div>
                <div class="dual-export-grid">
                    <button class="apple-btn-export-half highlight" onclick="exportStickerPNGV9()">✂️ Sticker .PNG</button>
                    <button class="apple-btn-export-half" onclick="exportWallpaperJPGV9()">📱 Wallpaper .JPG</button>
                </div>
            </div>

            <!-- CONTENEDORES AUXILIARES -->
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
        let stickerActiveCanvas = null;
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

                if (key === 'custom') {
                    // Sonido texturizado de despegue vinil adhesivo (Sticker Peel)
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
                    executeModulePipeline('custom', '🎨 Wallpapers & Stickers V9');
                } else {
                    executeModulePipeline(selectedEngineKey, selectedEngineName);
                }
            };
            capturedImage.src = internalCanvas.toDataURL('image/jpeg');
        }

        function executeModulePipeline(engine, name) {
            document.getElementById('sheetTitle').innerText = name;
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

            if (engine === 'custom') {
                customPanel.style.display = 'block';
                printPanel.style.display = 'none';
                cinePanel.style.display = 'none';
                rawPanel.style.display = 'none';
                svgPanel.style.display = 'none';
                vidPanel.style.display = 'none';
                depthPanel.style.display = 'none';
                chefPanel.style.display = 'none';
                pricePanel.style.display = 'none';
                aiPanel.style.display = 'none';
                document.getElementById('sheetDesc').innerText = "Troquelado Die-Cut procedural con reborde de calcomanía y wallpapers AMOLED Deep Black.";
                renderStickersV9();
            } else {
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

        function renderStickersV9() {
            const mode = document.getElementById('stickerModeSelectV9').value;
            const borderW = parseInt(document.getElementById('stickerBorderSliderV9').value);
            document.getElementById('stickerBorderLabel').innerText = borderW + ".0 mm";
            document.getElementById('stickerStyleLabel').innerText = mode === 'die_cut' ? 'Die-Cut' : (mode === 'amoled_wp' ? 'AMOLED' : 'Holo Pop');

            const box = document.getElementById('sheetCanvasBox');
            box.innerHTML = "";

            stickerActiveCanvas = document.createElement('canvas');
            stickerActiveCanvas.width = 360;
            stickerActiveCanvas.height = 230;
            const ctx = stickerActiveCanvas.getContext('2d');

            if (mode === 'die_cut') {
                // Fondo cuadriculado transparente
                ctx.fillStyle = "#161618";
                ctx.fillRect(0, 0, 360, 230);

                // Sombra de despegue sticker
                ctx.save();
                ctx.shadowColor = "rgba(0,0,0,0.65)";
                ctx.shadowBlur = 18;
                ctx.shadowOffsetY = 6;

                // Borde blanco Die-Cut
                ctx.fillStyle = "#FFFFFF";
                ctx.beginPath();
                ctx.ellipse(180, 115, 128 + borderW * 2, 88 + borderW * 2, 0, 0, Math.PI * 2);
                ctx.fill();
                ctx.restore();

                // Recorte del contenido interno
                ctx.save();
                ctx.beginPath();
                ctx.ellipse(180, 115, 128, 88, 0, 0, Math.PI * 2);
                ctx.clip();
                ctx.drawImage(capturedImage, 50, 25, 260, 180);
                ctx.restore();

            } else if (mode === 'amoled_wp') {
                // Fondo Negro Absoluto AMOLED 0x000000
                ctx.fillStyle = "#000000";
                ctx.fillRect(0, 0, 360, 230);

                // Viñeta y objeto centrado
                ctx.save();
                ctx.drawImage(capturedImage, 60, 20, 240, 190);
                const radGrad = ctx.createRadialGradient(180, 115, 60, 180, 115, 130);
                radGrad.addColorStop(0, "rgba(0,0,0,0)");
                radGrad.addColorStop(1, "rgba(0,0,0,0.95)");
                ctx.fillStyle = radGrad;
                ctx.fillRect(0, 0, 360, 230);
                ctx.restore();

            } else {
                // Modo Neón Pop Holográfico
                ctx.fillStyle = "#050B14";
                ctx.fillRect(0, 0, 360, 230);

                // Resplandor neón
                ctx.save();
                ctx.shadowColor = "#FF2D55";
                ctx.shadowBlur = 24;
                ctx.strokeStyle = "#FF2D55";
                ctx.lineWidth = borderW;
                ctx.strokeRect(60, 25, 240, 180);
                ctx.drawImage(capturedImage, 60, 25, 240, 180);
                ctx.restore();
            }

            box.appendChild(stickerActiveCanvas);
        }

        function exportStickerPNGV9() {
            if (!stickerActiveCanvas) return;
            const a = document.createElement('a');
            a.href = stickerActiveCanvas.toDataURL('image/png');
            a.download = `sticker_diecut_v9_${Date.now()}.png`;
            a.click();
        }

        function exportWallpaperJPGV9() {
            if (!stickerActiveCanvas) return;
            const a = document.createElement('a');
            a.href = stickerActiveCanvas.toDataURL('image/jpeg', 0.98);
            a.download = `wallpaper_amoled_v9_${Date.now()}.jpg`;
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
        "engine": "Wallpapers & Stickers V9 Ultra (Red Cine Shutter & Dual Export)",
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
