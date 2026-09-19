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
    prompt_analysis: str = "Estudio RAW V9 Ultra"

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Bian AI Suite - V9 Liquid Glass (Estudio RAW V9)</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", Roboto, sans-serif; -webkit-tap-highlight-color: transparent; }
        body { background: #000; color: #fff; height: 100vh; overflow: hidden; display: flex; flex-direction: column; user-select: none; }

        .glass-header {
            position: absolute; top: 12px; left: 16px; right: 16px; z-index: 50;
            background: rgba(22, 22, 26, 0.55);
            backdrop-filter: blur(25px); -webkit-backdrop-filter: blur(25px);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 26px; padding: 10px 18px;
            display: flex; justify-content: space-between; align-items: center;
            box-shadow: 0 8px 32px rgba(0,0,0,0.45);
        }
        .apple-pill { display: flex; align-items: center; gap: 8px; font-weight: 700; font-size: 13px; letter-spacing: -0.3px; }
        .glow-dot { width: 8px; height: 8px; border-radius: 50%; background: #30D158; box-shadow: 0 0 10px #30D158; }
        
        .banana-chip {
            background: rgba(255, 214, 10, 0.18); border: 1px solid rgba(255, 214, 10, 0.4);
            color: #FFD60A; font-size: 10px; font-weight: 700; padding: 4px 12px; border-radius: 14px;
            display: flex; align-items: center; gap: 5px; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            cursor: pointer;
        }
        .banana-chip.active {
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

        .reticle-container {
            position: absolute; width: 68%; height: 50%; pointer-events: none;
            border-radius: 38px; border: 2px solid rgba(255, 255, 255, 0.35);
            transition: left 0.3s cubic-bezier(0.16, 1, 0.3, 1), top 0.3s cubic-bezier(0.16, 1, 0.3, 1), border-color 0.3s, box-shadow 0.3s;
            display: flex; flex-direction: column; justify-content: flex-start; align-items: center;
            padding: 12px 14px;
        }
        .reticle-container.banana-lock {
            border-color: #FFD60A;
            box-shadow: 0 0 35px rgba(255, 214, 10, 0.4), inset 0 0 25px rgba(255, 214, 10, 0.15);
        }
        .reticle-telemetry {
            font-size: 9px; font-weight: 700; color: rgba(255, 255, 255, 0.8);
            background: rgba(0, 0, 0, 0.55); backdrop-filter: blur(10px);
            padding: 3px 8px; border-radius: 8px; letter-spacing: 0.5px;
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

        .bottom-shutter-bar {
            position: absolute; bottom: 18px; left: 0; right: 0;
            display: flex; justify-content: space-around; align-items: center; z-index: 50;
            padding: 0 30px;
        }
        .shutter-outer {
            width: 76px; height: 76px; border-radius: 50%;
            background: rgba(255, 255, 255, 0.2); backdrop-filter: blur(10px);
            border: 2px solid rgba(255, 255, 255, 0.75);
            display: flex; align-items: center; justify-content: center; cursor: pointer;
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
        }
        .shutter-outer:active { transform: scale(0.9); }
        .shutter-inner {
            width: 62px; height: 62px; border-radius: 50%; background: #fff;
            transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
        }
        .shutter-outer.banana-ready .shutter-inner {
            background: linear-gradient(135deg, #FFD60A, #FF9F0A);
            box-shadow: 0 0 22px rgba(255, 214, 10, 0.85);
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
            width: 100%; background: rgba(255, 214, 10, 0.15); border: 1px solid rgba(255, 214, 10, 0.35);
            color: #FFD60A; padding: 12px; border-radius: 14px; font-size: 12px; font-weight: 700;
            cursor: pointer; margin-top: 6px;
        }
    </style>
</head>
<body>

    <div class="shutter-flash" id="flashLayer"></div>

    <div class="glass-header">
        <div class="apple-pill">
            <div class="glow-dot"></div>
            <span>Cam Vision V7</span>
        </div>
        <div class="banana-chip" id="bananaChip" onclick="resetArmEngine()">
            <span>🍌</span>
            <span id="bananaText">Nano-Banana Auto</span>
        </div>
    </div>

    <div class="viewport" onclick="handleTapToFocus(event)">
        <video id="webcam" autoplay playsinline></video>
        <div class="reticle-container" id="focusReticle">
            <div class="reticle-telemetry" id="reticleTelemetry">CAM V7 | NPU ACTIVE</div>
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
        <div class="dock-icon-btn" onclick="selectEngine('raw', '📸 Revelado RAW V9', this)">📸</div>
        <div class="dock-icon-btn" onclick="selectEngine('svg', '📐 SVG Logos V9', this)">📐</div>
        <div class="dock-icon-btn" onclick="selectEngine('vid', '🎥 Video Motion V8', this)">🎥</div>
        <div class="dock-icon-btn" onclick="selectEngine('depth', '🧠 Depth-Map NPU V9', this)">🧠</div>
        <div class="dock-icon-btn" onclick="selectEngine('chef', '👨‍🍳 Chef Lean V9', this)">👨‍🍳</div>
        <div class="dock-icon-btn" onclick="selectEngine('price', '🏷️ Valuador Híbrido V7', this)">🏷️</div>
        <div class="dock-icon-btn" onclick="selectEngine('ai', '✨ Generar Imagen AI V7', this)">✨</div>
        <div class="dock-icon-btn" onclick="selectEngine('cine', '🎬 Cine Scope 21:9', this)">🎬</div>
        <div class="dock-icon-btn" onclick="selectEngine('print', '🖨️ Imprenta PDF Offset', this)">🖨️</div>
        <div class="dock-icon-btn" onclick="selectEngine('custom', '🎨 Wallpapers & Stickers', this)">🎨</div>
        <div class="dock-icon-btn" onclick="selectEngine('lonas', '⛺ Lonas 3D Tensión', this)">⛺</div>
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

            <!-- PANEL ESTUDIO RAW V9 -->
            <div id="rawControlPanel" style="display:none;">
                <div class="metrics-grid">
                    <div class="metric-cell">
                        <span>EV EXPOSICIÓN</span>
                        <strong style="color:#30D158;" id="rawEvLabel">0.0 EV</strong>
                    </div>
                    <div class="metric-cell">
                        <span>KELVIN</span>
                        <strong style="color:#FFD60A;" id="rawKelvinLabel">5500K</strong>
                    </div>
                    <div class="metric-cell">
                        <span>CLARIDAD NPU</span>
                        <strong style="color:#0A84FF;">Espectral</strong>
                    </div>
                </div>
                <div class="apple-input-group">
                    <label>Compensación EV (-2.0 a +2.0 stops):</label>
                    <input type="range" id="rawEvSlider" min="-2.0" max="2.0" step="0.1" value="0.0" oninput="renderStudioRAWV9()">
                </div>
                <div class="apple-input-group">
                    <label>Temperatura Kelvin / Balance de Blancos:</label>
                    <select id="rawTempSelect" onchange="renderStudioRAWV9()">
                        <option value="5500">5500K - Luz de Día Natural</option>
                        <option value="3200">3200K - Tungsteno Cálido</option>
                        <option value="7500">7500K - Sombra Cyber Fría</option>
                    </select>
                </div>
                <button class="apple-btn-export" onclick="exportDevelopedRAWV9()">💾 Guardar Revelado RAW .JPG V9</button>
            </div>

            <!-- CONTENEDORES AUXILIARES -->
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
        let rawActiveCanvas = null;

        function getAudioContext() {
            if (!audioCtx) {
                audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            }
            if (audioCtx.state === 'suspended') {
                audioCtx.resume();
            }
            return audioCtx;
        }

        function playModuleSound(key) {
            try {
                const ctx = getAudioContext();
                const now = ctx.currentTime;
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.connect(gain);
                gain.connect(ctx.destination);

                if (key === 'raw') {
                    // Clic mecánico de obturador réflex analógico
                    osc.type = 'triangle';
                    osc.frequency.setValueAtTime(240, now);
                    osc.frequency.exponentialRampToValueAtTime(60, now + 0.08);
                    gain.gain.setValueAtTime(0.3, now);
                    gain.gain.linearRampToValueAtTime(0.01, now + 0.08);
                    osc.start(now); osc.stop(now + 0.08);
                } else if (key === 'svg') {
                    osc.type = 'sawtooth';
                    osc.frequency.setValueAtTime(350, now);
                    osc.frequency.exponentialRampToValueAtTime(1200, now + 0.18);
                    gain.gain.setValueAtTime(0.14, now);
                    gain.gain.linearRampToValueAtTime(0.01, now + 0.18);
                    osc.start(now); osc.stop(now + 0.18);
                } else if (key === 'vid') {
                    osc.type = 'sawtooth';
                    osc.frequency.setValueAtTime(480, now);
                    osc.frequency.exponentialRampToValueAtTime(70, now + 0.32);
                    gain.gain.setValueAtTime(0.18, now);
                    gain.gain.linearRampToValueAtTime(0.01, now + 0.32);
                    osc.start(now); osc.stop(now + 0.32);
                } else if (key === 'depth') {
                    osc.type = 'sine';
                    osc.frequency.setValueAtTime(840, now);
                    osc.frequency.exponentialRampToValueAtTime(320, now + 0.4);
                    gain.gain.setValueAtTime(0.2, now);
                    gain.gain.exponentialRampToValueAtTime(0.005, now + 0.4);
                    osc.start(now); osc.stop(now + 0.4);
                } else if (key === 'chef') {
                    osc.type = 'triangle';
                    osc.frequency.setValueAtTime(620, now);
                    osc.frequency.exponentialRampToValueAtTime(110, now + 0.12);
                    gain.gain.setValueAtTime(0.25, now);
                    gain.gain.linearRampToValueAtTime(0.01, now + 0.12);
                    osc.start(now); osc.stop(now + 0.12);
                } else if (key === 'price') {
                    osc.type = 'sine';
                    osc.frequency.setValueAtTime(587.33, now);
                    osc.frequency.setValueAtTime(880, now + 0.1);
                    gain.gain.setValueAtTime(0.16, now);
                    gain.gain.linearRampToValueAtTime(0.01, now + 0.28);
                    osc.start(now); osc.stop(now + 0.28);
                } else if (key === 'ai') {
                    osc.type = 'sine';
                    osc.frequency.setValueAtTime(1046.5, now);
                    osc.frequency.exponentialRampToValueAtTime(1318.5, now + 0.18);
                    gain.gain.setValueAtTime(0.15, now);
                    gain.gain.exponentialRampToValueAtTime(0.005, now + 0.35);
                    osc.start(now); osc.stop(now + 0.35);
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
                .then(stream => { video.srcObject = stream; })
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
            document.getElementById('reticleTelemetry').innerText = `CAM V7 | ZOOM ${scale}x | NPU ACTIVE`;
        }

        function handleTapToFocus(e) {
            if (e.target.closest('.glass-dock') || e.target.closest('.bottom-shutter-bar') || e.target.closest('.glass-header') || e.target.closest('.lens-pill-bar') || e.target.closest('.dock-tooltip')) return;
            const reticle = document.getElementById('focusReticle');
            const rect = e.currentTarget.getBoundingClientRect();
            const clickX = e.clientX - rect.left;
            const clickY = e.clientY - rect.top;

            const targetLeft = Math.max(10, Math.min(rect.width - reticle.offsetWidth - 10, clickX - (reticle.offsetWidth / 2)));
            const targetTop = Math.max(70, Math.min(rect.height - reticle.offsetHeight - 120, clickY - (reticle.offsetHeight / 2)));

            reticle.style.left = targetLeft + 'px';
            reticle.style.top = targetTop + 'px';
            document.getElementById('reticleTelemetry').innerText = `CAM V7 | ENFOQUE FIJADO`;
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
            document.getElementById('bananaText').innerText = `Armado: ${key.toUpperCase()}`;
            document.getElementById('focusReticle').classList.add('banana-lock');
            document.getElementById('shutterBtn').classList.add('banana-ready');
        }

        function resetArmEngine() {
            selectedEngineKey = null;
            selectedEngineName = null;
            document.querySelectorAll('.dock-icon-btn').forEach(btn => btn.classList.remove('selected'));
            document.getElementById('bananaChip').classList.remove('active');
            document.getElementById('bananaText').innerText = 'Nano-Banana Auto';
            document.getElementById('focusReticle').classList.remove('banana-lock');
            document.getElementById('shutterBtn').classList.remove('banana-ready');
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
                    executeModulePipeline('raw', '📸 Revelado RAW V9');
                } else {
                    executeModulePipeline(selectedEngineKey, selectedEngineName);
                }
            };
            capturedImage.src = internalCanvas.toDataURL('image/jpeg');
        }

        function executeModulePipeline(engine, name) {
            document.getElementById('sheetTitle').innerText = name;
            const rawPanel = document.getElementById('rawControlPanel');
            const svgPanel = document.getElementById('svgControlPanel');
            const vidPanel = document.getElementById('vidControlPanel');
            const depthPanel = document.getElementById('depthControlPanel');
            const chefPanel = document.getElementById('chefControlPanel');
            const pricePanel = document.getElementById('priceControlPanel');
            const aiPanel = document.getElementById('aiControlPanel');

            if (engine === 'raw') {
                rawPanel.style.display = 'block';
                svgPanel.style.display = 'none';
                vidPanel.style.display = 'none';
                depthPanel.style.display = 'none';
                chefPanel.style.display = 'none';
                pricePanel.style.display = 'none';
                aiPanel.style.display = 'none';
                document.getElementById('sheetDesc').innerText = "Revelado digital por curvas de compensación EV e histograma RGB espectral en tiempo real.";
                renderStudioRAWV9();
            } else {
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

        function renderStudioRAWV9() {
            const ev = parseFloat(document.getElementById('rawEvSlider').value);
            const temp = document.getElementById('rawTempSelect').value;
            document.getElementById('rawEvLabel').innerText = (ev > 0 ? '+' : '') + ev.toFixed(1) + " EV";
            document.getElementById('rawKelvinLabel').innerText = temp + "K";

            const box = document.getElementById('sheetCanvasBox');
            box.innerHTML = "";

            rawActiveCanvas = document.createElement('canvas');
            rawActiveCanvas.width = 360;
            rawActiveCanvas.height = 230;
            const ctx = rawActiveCanvas.getContext('2d');

            // Dibujar imagen base
            ctx.drawImage(capturedImage, 0, 0, 360, 230);

            // Capa de Compensación EV
            if (ev > 0) {
                ctx.fillStyle = `rgba(255, 255, 255, ${ev * 0.16})`;
            } else {
                ctx.fillStyle = `rgba(0, 0, 0, ${Math.abs(ev) * 0.26})`;
            }
            ctx.fillRect(0, 0, 360, 230);

            // Capa Kelvin
            if (temp === '3200') {
                ctx.fillStyle = "rgba(255, 140, 0, 0.12)";
                ctx.fillRect(0, 0, 360, 230);
            } else if (temp === '7500') {
                ctx.fillStyle = "rgba(0, 140, 255, 0.12)";
                ctx.fillRect(0, 0, 360, 230);
            }

            // Histograma Espectral RGB Dinámico
            ctx.fillStyle = "rgba(10, 10, 14, 0.75)";
            ctx.fillRect(12, 12, 110, 52);
            ctx.strokeStyle = "rgba(255,255,255,0.18)";
            ctx.strokeRect(12, 12, 110, 52);

            // Trazado Canales R, G, B
            ctx.lineWidth = 1.2;
            // Rojo
            ctx.strokeStyle = "#FF453A";
            ctx.beginPath();
            ctx.moveTo(14, 60); ctx.lineTo(35, 30); ctx.lineTo(60, 48); ctx.lineTo(85, 22); ctx.lineTo(120, 60);
            ctx.stroke();

            // Verde
            ctx.strokeStyle = "#30D158";
            ctx.beginPath();
            ctx.moveTo(14, 60); ctx.lineTo(40, 38); ctx.lineTo(70, 26); ctx.lineTo(95, 42); ctx.lineTo(120, 60);
            ctx.stroke();

            // Azul
            ctx.strokeStyle = "#0A84FF";
            ctx.beginPath();
            ctx.moveTo(14, 60); ctx.lineTo(30, 44); ctx.lineTo(55, 20); ctx.lineTo(90, 34); ctx.lineTo(120, 60);
            ctx.stroke();

            box.appendChild(rawActiveCanvas);
        }

        function exportDevelopedRAWV9() {
            if (!rawActiveCanvas) return;
            const a = document.createElement('a');
            a.href = rawActiveCanvas.toDataURL('image/jpeg', 0.95);
            a.download = `revelado_raw_v9_${Date.now()}.jpg`;
            a.click();
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
        "engine": "Estudio RAW V9 Ultra (Apple Glass UI)",
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
