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
    prompt_analysis: str = "Samsung Camera Core V9"

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Bian AI Suite - Samsung Native Camera Core V9</title>
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

        /* CAPSULA DERECHA CON TEXTO RESALTADO */
        .top-float-right {
            position: absolute; top: 16px; right: 18px; z-index: 50;
            background: rgba(255, 255, 255, 0.12);
            backdrop-filter: blur(25px); -webkit-backdrop-filter: blur(25px);
            border: 1px solid rgba(255, 255, 255, 0.28);
            color: #FFFFFF; font-size: 12px; font-weight: 700; padding: 8px 16px; border-radius: 22px;
            display: flex; align-items: center; gap: 6px; cursor: pointer;
            letter-spacing: 0.2px;
            box-shadow: 0 6px 24px rgba(0,0,0,0.5), 0 0 14px rgba(255, 255, 255, 0.18);
            transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
        }
        .top-float-right.active {
            background: linear-gradient(135deg, #FF9F0A, #FF375F);
            color: #fff; border-color: transparent;
            box-shadow: 0 0 20px rgba(255, 55, 95, 0.7);
            transform: scale(1.05);
        }

        .viewport {
            position: absolute; inset: 0; width: 100%; height: 100%;
            background: #000; overflow: hidden; display: flex; align-items: center; justify-content: center;
        }
        video {
            width: 100%; height: 100%; object-fit: cover;
            transform-origin: center center;
            transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1);
        }
        
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
        }
        .lens-btn {
            background: transparent; border: none; color: rgba(255,255,255,0.7);
            font-size: 10px; font-weight: 700; padding: 5px 9px; border-radius: 14px;
            cursor: pointer; transition: all 0.2s;
        }
        .lens-btn.active { background: rgba(255, 255, 255, 0.25); color: #fff; transform: scale(1.05); }

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
            position: absolute; bottom: 98px; left: 14px; right: 14px; z-index: 40;
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
            cursor: pointer;
            transition: transform 0.25s cubic-bezier(0.34, 1.56, 0.64, 1), background 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease;
            position: relative;
        }
        .dock-icon-btn:active { transform: scale(0.92); }

        .dock-icon-btn.selected {
            transform: translateY(-8px) scale(1.15);
            border-color: rgba(255, 255, 255, 0.4);
            z-index: 10;
        }
        .dock-icon-btn.selected::after {
            content: ''; position: absolute; bottom: -5px; width: 5px; height: 5px;
            border-radius: 50%; background: #fff;
            box-shadow: 0 0 6px #fff;
        }

        .dock-icon-btn[data-key="lonas"].active-glow { background: linear-gradient(135deg, rgba(255,149,0,0.65), rgba(255,94,58,0.45)); border-color: #FF9500; box-shadow: 0 8px 20px rgba(255,149,0,0.6); }
        .dock-icon-btn[data-key="custom"].active-glow { background: linear-gradient(135deg, rgba(255,45,85,0.65), rgba(175,82,222,0.45)); border-color: #FF2D55; box-shadow: 0 8px 20px rgba(255,45,85,0.6); }
        .dock-icon-btn[data-key="print"].active-glow { background: linear-gradient(135deg, rgba(50,173,230,0.65), rgba(0,122,255,0.45)); border-color: #32ADE6; box-shadow: 0 8px 20px rgba(0,122,255,0.6); }
        .dock-icon-btn[data-key="cine"].active-glow { background: linear-gradient(135deg, rgba(255,59,48,0.65), rgba(255,45,85,0.45)); border-color: #FF3B30; box-shadow: 0 8px 20px rgba(255,59,48,0.6); }
        .dock-icon-btn[data-key="raw"].active-glow { background: linear-gradient(135deg, rgba(48,209,88,0.65), rgba(52,199,89,0.45)); border-color: #30D158; box-shadow: 0 8px 20px rgba(48,209,88,0.6); }
        .dock-icon-btn[data-key="svg"].active-glow { background: linear-gradient(135deg, rgba(255,214,10,0.65), rgba(255,159,10,0.45)); border-color: #FFD60A; box-shadow: 0 8px 20px rgba(255,214,10,0.6); }
        .dock-icon-btn[data-key="vid"].active-glow { background: linear-gradient(135deg, rgba(191,90,242,0.65), rgba(94,92,230,0.45)); border-color: #BF5AF2; box-shadow: 0 8px 20px rgba(94,92,230,0.6); }
        .dock-icon-btn[data-key="depth"].active-glow { background: linear-gradient(135deg, rgba(255,55,95,0.65), rgba(191,90,242,0.45)); border-color: #FF375F; box-shadow: 0 8px 20px rgba(255,55,95,0.6); }
        .dock-icon-btn[data-key="chef"].active-glow { background: linear-gradient(135deg, rgba(255,159,10,0.65), rgba(255,107,0,0.45)); border-color: #FF9F0A; box-shadow: 0 8px 20px rgba(255,159,10,0.6); }
        .dock-icon-btn[data-key="price"].active-glow { background: linear-gradient(135deg, rgba(99,230,226,0.65), rgba(0,199,190,0.45)); border-color: #63E6E2; box-shadow: 0 8px 20px rgba(0,199,190,0.6); }
        .dock-icon-btn[data-key="ai"].active-glow { background: linear-gradient(135deg, rgba(10,132,255,0.65), rgba(94,92,230,0.45)); border-color: #0A84FF; box-shadow: 0 8px 20px rgba(10,132,255,0.6); }

        /* EVAPORACION PROGRESIVA Y SEDOSA TRAS 1 SEGUNDO */
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
        .preview-canvas-box canvas { max-width: 100%; max-height: 100%; object-fit: contain; }

        .apple-btn-main {
            width: 100%; background: #0A84FF; border: none; color: #fff;
            padding: 14px; border-radius: 16px; font-size: 14px; font-weight: 600;
            cursor: pointer; margin-top: 8px;
        }
    </style>
</head>
<body>

    <div class="shutter-flash" id="flashLayer"></div>

    <div class="top-float-left">
        <div class="glow-dot"></div>
        <span>Cam Vision V9</span>
    </div>

    <!-- TEXTO RESALTADO "¿QUÉ QUIERES HACER?" EN LUGAR DE NANO -->
    <div class="top-float-right" id="bananaChip" onclick="resetArmEngine()">
        <span id="bananaText">✨ ¿Qué quieres hacer?</span>
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
        <button class="lens-btn" onclick="setSamsungZoom(0.6, this)">0.6x</button>
        <button class="lens-btn active" onclick="setSamsungZoom(1.0, this)">1x</button>
        <button class="lens-btn" onclick="setSamsungZoom(2.0, this)">2x</button>
        <button class="lens-btn" onclick="setSamsungZoom(3.0, this)">3x</button>
        <button class="lens-btn" onclick="setSamsungZoom(10.0, this)">10x</button>
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
        let fadeCircleTimeout = null;
        let currentStreamTrack = null;
        let evaporateTimeout = null;

        function getAudioContext() {
            if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            if (audioCtx.state === 'suspended') audioCtx.resume();
            return audioCtx;
        }

        function playSignatureProSound(key) {
            try {
                const ctx = getAudioContext();
                const now = ctx.currentTime;
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.connect(gain);
                gain.connect(ctx.destination);

                if (key === 'lonas') {
                    osc.type = 'sine';
                    osc.frequency.setValueAtTime(110, now);
                    osc.frequency.exponentialRampToValueAtTime(45, now + 0.16);
                    gain.gain.setValueAtTime(0.35, now);
                    gain.gain.linearRampToValueAtTime(0.001, now + 0.16);
                    osc.start(now); osc.stop(now + 0.16);
                } else if (key === 'custom') {
                    osc.type = 'sine';
                    osc.frequency.setValueAtTime(260, now);
                    osc.frequency.exponentialRampToValueAtTime(90, now + 0.12);
                    gain.gain.setValueAtTime(0.25, now);
                    gain.gain.linearRampToValueAtTime(0.001, now + 0.12);
                    osc.start(now); osc.stop(now + 0.12);
                } else if (key === 'print') {
                    osc.type = 'triangle';
                    osc.frequency.setValueAtTime(140, now);
                    osc.frequency.exponentialRampToValueAtTime(35, now + 0.14);
                    gain.gain.setValueAtTime(0.28, now);
                    gain.gain.linearRampToValueAtTime(0.001, now + 0.14);
                    osc.start(now); osc.stop(now + 0.14);
                } else if (key === 'cine') {
                    osc.type = 'sine';
                    osc.frequency.setValueAtTime(95, now);
                    osc.frequency.linearRampToValueAtTime(50, now + 0.22);
                    gain.gain.setValueAtTime(0.32, now);
                    gain.gain.linearRampToValueAtTime(0.001, now + 0.22);
                    osc.start(now); osc.stop(now + 0.22);
                } else if (key === 'raw') {
                    osc.type = 'triangle';
                    osc.frequency.setValueAtTime(180, now);
                    osc.frequency.exponentialRampToValueAtTime(65, now + 0.08);
                    gain.gain.setValueAtTime(0.3, now);
                    gain.gain.linearRampToValueAtTime(0.001, now + 0.08);
                    osc.start(now); osc.stop(now + 0.08);
                } else if (key === 'svg') {
                    osc.type = 'sine';
                    osc.frequency.setValueAtTime(380, now);
                    osc.frequency.exponentialRampToValueAtTime(190, now + 0.18);
                    gain.gain.setValueAtTime(0.2, now);
                    gain.gain.linearRampToValueAtTime(0.001, now + 0.18);
                    osc.start(now); osc.stop(now + 0.18);
                } else if (key === 'vid') {
                    osc.type = 'sine';
                    osc.frequency.setValueAtTime(80, now);
                    osc.frequency.linearRampToValueAtTime(130, now + 0.1);
                    osc.frequency.exponentialRampToValueAtTime(40, now + 0.24);
                    gain.gain.setValueAtTime(0.28, now);
                    gain.gain.linearRampToValueAtTime(0.001, now + 0.24);
                    osc.start(now); osc.stop(now + 0.24);
                } else if (key === 'depth') {
                    osc.type = 'triangle';
                    osc.frequency.setValueAtTime(160, now);
                    osc.frequency.setValueAtTime(80, now + 0.06);
                    gain.gain.setValueAtTime(0.22, now);
                    gain.gain.linearRampToValueAtTime(0.001, now + 0.18);
                    osc.start(now); osc.stop(now + 0.18);
                } else if (key === 'chef') {
                    osc.type = 'sine';
                    osc.frequency.setValueAtTime(210, now);
                    osc.frequency.exponentialRampToValueAtTime(75, now + 0.09);
                    gain.gain.setValueAtTime(0.26, now);
                    gain.gain.linearRampToValueAtTime(0.001, now + 0.09);
                    osc.start(now); osc.stop(now + 0.09);
                } else if (key === 'price') {
                    osc.type = 'sine';
                    osc.frequency.setValueAtTime(220, now);
                    osc.frequency.setValueAtTime(330, now + 0.05);
                    gain.gain.setValueAtTime(0.18, now);
                    gain.gain.linearRampToValueAtTime(0.001, now + 0.14);
                    osc.start(now); osc.stop(now + 0.14);
                } else {
                    osc.type = 'sine';
                    osc.frequency.setValueAtTime(180, now);
                    osc.frequency.linearRampToValueAtTime(240, now + 0.15);
                    gain.gain.setValueAtTime(0.2, now);
                    gain.gain.linearRampToValueAtTime(0.001, now + 0.2);
                    osc.start(now); osc.stop(now + 0.2);
                }
            } catch(e) {}
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
                })
                .catch(err => console.error("Error cámara:", err));
        }
        startCamera();

        function toggleLens() {
            facingMode = (facingMode === 'environment') ? 'user' : 'environment';
            if (video.srcObject) video.srcObject.getTracks().forEach(t => t.stop());
            startCamera();
        }

        function setSamsungZoom(zoomLevel, elem) {
            document.querySelectorAll('.lens-btn').forEach(b => b.classList.remove('active'));
            elem.classList.add('active');

            if (currentStreamTrack && typeof currentStreamTrack.getCapabilities === 'function') {
                const caps = currentStreamTrack.getCapabilities();
                if (caps.zoom) {
                    const min = caps.zoom.min || 1;
                    const max = caps.zoom.max || 10;
                    const targetZoom = Math.min(Math.max(zoomLevel, min), max);
                    currentStreamTrack.applyConstraints({ advanced: [{ zoom: targetZoom }] })
                        .catch(() => fallbackCSSZoom(zoomLevel));
                    return;
                }
            }
            fallbackCSSZoom(zoomLevel);
        }

        function fallbackCSSZoom(zoomLevel) {
            const scale = Math.max(1.0, zoomLevel);
            video.style.transform = `scale(${scale})`;
            triggerCircleFade();
        }

        function triggerCircleFade() {
            const circle = document.getElementById('focusCircle');
            circle.classList.remove('faded');
            if (fadeCircleTimeout) clearTimeout(fadeCircleTimeout);
            fadeCircleTimeout = setTimeout(() => { circle.classList.add('faded'); }, 1800);
        }

        function handleTapToFocus(e) {
            if (e.target.closest('.glass-dock') || e.target.closest('.bottom-shutter-bar') || e.target.closest('.top-float-left') || e.target.closest('.top-float-right') || e.target.closest('.lens-pill-bar') || e.target.closest('.dock-tooltip')) return;
            
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

        function selectEngine(key, name, elem) {
            showDockTooltipAboveElement(name, elem);
            playSignatureProSound(key);

            document.querySelectorAll('.dock-icon-btn').forEach(btn => {
                btn.classList.remove('selected', 'active-glow', 'evaporated');
            });
            if (evaporateTimeout) clearTimeout(evaporateTimeout);
            
            if (selectedEngineKey === key) {
                resetArmEngine();
                return;
            }

            selectedEngineKey = key;
            selectedEngineName = name;

            elem.classList.add('selected');
            elem.classList.add('active-glow');

            // EXACTO 1.0 SEGUNDO PARA EMPEZAR LA DISIPACION SUAVE
            evaporateTimeout = setTimeout(() => {
                elem.classList.remove('active-glow');
                elem.classList.add('evaporated');
            }, 1000);

            document.getElementById('bananaChip').classList.add('active');
            document.getElementById('bananaText').innerText = key.toUpperCase();
            triggerCircleFade();
        }

        function resetArmEngine() {
            selectedEngineKey = null;
            selectedEngineName = null;
            document.querySelectorAll('.dock-icon-btn').forEach(btn => {
                btn.classList.remove('selected', 'active-glow', 'evaporated');
            });
            if (evaporateTimeout) clearTimeout(evaporateTimeout);
            document.getElementById('bananaChip').classList.remove('active');
            document.getElementById('bananaText').innerText = '✨ ¿Qué quieres hacer?';
            triggerCircleFade();
        }

        function triggerNanoBananaCapture() {
            if (video.videoWidth === 0) return;

            const flash = document.getElementById('flashLayer');
            flash.classList.add('flash');
            setTimeout(() => flash.classList.remove('flash'), 120);

            internalCanvas.width = video.videoWidth;
            internalCanvas.height = video.videoHeight;
            const ctx = internalCanvas.getContext('2d');
            ctx.drawImage(video, 0, 0, internalCanvas.width, internalCanvas.height);

            capturedImage.onload = () => {
                const box = document.getElementById('sheetCanvasBox');
                box.innerHTML = "";
                const canvas = document.createElement('canvas');
                canvas.width = 360; canvas.height = 240;
                const cctx = canvas.getContext('2d');
                cctx.drawImage(capturedImage, 0, 0, 360, 240);
                box.appendChild(canvas);

                document.getElementById('sheetTitle').innerText = selectedEngineName || "Captura Nativa S23 Ultra";
                document.getElementById('sheetDesc').innerText = "Fotograma capturado con cobertura de sensor nativo en proporción 3:4.";
                document.getElementById('sheetModal').classList.add('active');
            };
            capturedImage.src = internalCanvas.toDataURL('image/jpeg', 0.95);
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
        "engine": "Samsung Native Camera Core V9 (1.0s Fade & Action Prompt)",
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
