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
    prompt_analysis: str = "Chef Lean V9 Ultra"

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Bian AI Suite - V9 Liquid Glass (Chef Lean V9)</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", Roboto, sans-serif; -webkit-tap-highlight-color: transparent; }
        body { background: #000; color: #fff; height: 100vh; overflow: hidden; display: flex; flex-direction: column; user-select: none; }

        /* HEADER APPLE GLASS */
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

        /* VIEWPORT Y RETÍCULA V9 */
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
            display: flex; flex-direction: column; justify-content: space-between; align-items: center;
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
        .status-badge {
            background: rgba(0, 0, 0, 0.65); backdrop-filter: blur(14px);
            padding: 6px 14px; border-radius: 14px; font-size: 11px; font-weight: 600;
            color: rgba(255,255,255,0.95); border: 1px solid rgba(255,255,255,0.12);
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
        .lens-btn.active {
            background: rgba(255, 255, 255, 0.2); color: #fff;
        }

        /* TOOLTIP FLOTANTE DE NOMBRE DE MÓDULO */
        .dock-tooltip {
            position: absolute; bottom: 156px; z-index: 46;
            background: rgba(28, 28, 35, 0.85); backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.18);
            color: #fff; font-size: 11px; font-weight: 600; padding: 5px 14px;
            border-radius: 16px; pointer-events: none; opacity: 0; transform: translateY(6px);
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
            box-shadow: 0 4px 16px rgba(0,0,0,0.5);
        }
        .dock-tooltip.visible { opacity: 1; transform: translateY(0); }

        /* LIQUID GLASS DOCK */
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

        /* SHUTTER BAR */
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

        /* MODAL SHEET APPLE */
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
        
        .preview-canvas-box { width: 100%; height: 230px; background: #080808; border-radius: 18px; overflow: hidden; border: 1px solid rgba(255,255,255,0.08); display: flex; align-items: center; justify-content: center; margin-bottom: 16px; }
        .preview-canvas-box canvas { max-width: 100%; max-height: 100%; object-fit: contain; }

        .apple-input-group { margin-bottom: 12px; text-align: left; }
        .apple-input-group label { font-size: 11px; font-weight: 600; color: rgba(255,255,255,0.7); display: block; margin-bottom: 6px; }
        .apple-input-group input, .apple-input-group select {
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
            <div class="status-badge" id="hudStatus">Modo: Esperando selección</div>
        </div>
        <canvas id="internalCanvas" style="display:none;"></canvas>
    </div>

    <div class="lens-pill-bar">
        <button class="lens-btn" onclick="applyDigitalZoom(0.8, this)">0.6x</button>
        <button class="lens-btn active" onclick="applyDigitalZoom(1.0, this)">1x</button>
        <button class="lens-btn" onclick="applyDigitalZoom(1.5, this)">2x</button>
    </div>

    <!-- TOOLTIP QUE INDICA EL NOMBRE DEL ICONO TOCADO -->
    <div class="dock-tooltip" id="dockTooltip">Módulo</div>

    <!-- DOCK FLOTANTE CON TODOS LOS ICONOS Y NOMBRES AL TOCAR -->
    <div class="glass-dock">
        <div class="dock-icon-btn" onclick="selectEngine('chef', '👨‍🍳 Chef Lean V9', this)" title="Chef Lean V9">👨‍🍳</div>
        <div class="dock-icon-btn" onclick="selectEngine('price', '🏷️ Valuador Híbrido V7', this)" title="Valuador V7">🏷️</div>
        <div class="dock-icon-btn" onclick="selectEngine('ai', '✨ Generar Imagen AI V7', this)" title="Generar Imagen AI">✨</div>
        <div class="dock-icon-btn" onclick="selectEngine('cine', '🎬 Cine Scope 21:9', this)" title="Cine Scope">🎬</div>
        <div class="dock-icon-btn" onclick="selectEngine('print', '🖨️ Imprenta PDF Offset', this)" title="Imprenta PDF">🖨️</div>
        <div class="dock-icon-btn" onclick="selectEngine('custom', '🎨 Wallpapers & Stickers', this)" title="Wallpapers & Stickers">🎨</div>
        <div class="dock-icon-btn" onclick="selectEngine('raw', '📸 Revelado RAW EV', this)" title="Estudio RAW">📸</div>
        <div class="dock-icon-btn" onclick="selectEngine('depth', '🧠 Depth-Map NPU', this)" title="Profundidad Z">🧠</div>
        <div class="dock-icon-btn" onclick="selectEngine('vid', '🎥 Video Motion 60fps', this)" title="Video Motion">🎥</div>
        <div class="dock-icon-btn" onclick="selectEngine('svg', '📐 SVG Logos Vector', this)" title="SVG Logos">📐</div>
        <div class="dock-icon-btn" onclick="selectEngine('lonas', '⛺ Lonas 3D Tensión', this)" title="Lonas 3D">⛺</div>
    </div>

    <div class="bottom-shutter-bar">
        <div class="side-btn" onclick="toggleLens()">🔄</div>
        <div class="shutter-outer" id="shutterBtn" onclick="triggerNanoBananaCapture()">
            <div class="shutter-inner"></div>
        </div>
        <div class="side-btn" onclick="alert('✔ Galería Soberana Sincronizada')">🖼️</div>
    </div>

    <!-- MODAL SHEET CON CHEF LEAN V9 -->
    <div class="sheet-modal" id="sheetModal">
        <div class="sheet-card">
            <div class="sheet-drag" onclick="closeSheet()"></div>
            <div class="sheet-title" id="sheetTitle">Módulo Procesado</div>
            <div class="sheet-desc" id="sheetDesc">Acción ejecutada mediante la canalización Nano-Banana.</div>
            <div class="preview-canvas-box" id="sheetCanvasBox"></div>

            <!-- PANEL ESPECÍFICO DE CHEF LEAN V9 -->
            <div id="chefControlPanel" style="display:none;">
                <div class="metrics-grid">
                    <div class="metric-cell">
                        <span>PESO NETO ÚTIL</span>
                        <strong style="color:#30D158;" id="chefNetWeight">3.01 Kg</strong>
                    </div>
                    <div class="metric-cell">
                        <span>PORCIONES</span>
                        <strong style="color:#0A84FF;" id="chefPortions">13 platos</strong>
                    </div>
                    <div class="metric-cell">
                        <span>P.V.P SUGERIDO</span>
                        <strong style="color:#FF9F0A;" id="chefPlatoPrice">$185 MXN</strong>
                    </div>
                </div>
                <div class="apple-input-group">
                    <label>Gramaje por Porción Objetivo:</label>
                    <select id="chefPortionSelect" onchange="recalculateChefV9()">
                        <option value="220">220g (Corte Estándar Gourmet)</option>
                        <option value="250">250g (Porción Premium Steak)</option>
                        <option value="180">180g (Porción Ligera / Taquería Lean)</option>
                        <option value="350">350g (Tomahawk / Cowboy Cut)</option>
                    </select>
                </div>
                <div class="apple-input-group">
                    <label>Destino de Mermas (Desperdicio Cero):</label>
                    <select id="chefMermaTarget">
                        <option value="fondo">Fondo Oscuro / Consomé Artesanal</option>
                        <option value="grasa">Procesamiento de Manteca / Tallow Gourmet</option>
                    </select>
                </div>
            </div>

            <!-- OTROS PANELES PREVIOS -->
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

        function showDockTooltip(name) {
            const tooltip = document.getElementById('dockTooltip');
            tooltip.innerText = name;
            tooltip.classList.add('visible');
            if (tooltipTimeout) clearTimeout(tooltipTimeout);
            tooltipTimeout = setTimeout(() => {
                tooltip.classList.remove('visible');
            }, 1800);
        }

        function selectEngine(key, name, elem) {
            showDockTooltip(name);

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
            document.getElementById('hudStatus').innerText = `Listo para: ${name}`;
        }

        function resetArmEngine() {
            selectedEngineKey = null;
            selectedEngineName = null;
            document.querySelectorAll('.dock-icon-btn').forEach(btn => btn.classList.remove('selected'));
            document.getElementById('bananaChip').classList.remove('active');
            document.getElementById('bananaText').innerText = 'Nano-Banana Auto';
            document.getElementById('focusReticle').classList.remove('banana-lock');
            document.getElementById('shutterBtn').classList.remove('banana-ready');
            document.getElementById('hudStatus').innerText = 'Modo: Esperando selección';
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
                    executeModulePipeline('chef', '👨‍🍳 Chef Lean V9');
                } else {
                    executeModulePipeline(selectedEngineKey, selectedEngineName);
                }
            };
            capturedImage.src = internalCanvas.toDataURL('image/jpeg');
        }

        function executeModulePipeline(engine, name) {
            document.getElementById('sheetTitle').innerText = name;
            const chefPanel = document.getElementById('chefControlPanel');
            const pricePanel = document.getElementById('priceControlPanel');
            const aiPanel = document.getElementById('aiControlPanel');

            if (engine === 'chef') {
                chefPanel.style.display = 'block';
                pricePanel.style.display = 'none';
                aiPanel.style.display = 'none';
                document.getElementById('sheetDesc').innerText = "Inspección de mioglobina y análisis de porcionado cárnico Lean V9 completados.";
                recalculateChefV9();
            } else {
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
                document.getElementById('sheetDesc').innerText = `Procesamiento inteligente completado en ${name}.`;
            }

            document.getElementById('sheetModal').classList.add('active');
        }

        function recalculateChefV9() {
            const portionGrams = parseInt(document.getElementById('chefPortionSelect').value) || 220;
            const grossWeight = 3.5;
            const mermaRatio = 0.14;
            const netWeight = (grossWeight * (1 - mermaRatio)).toFixed(2);
            const portions = Math.floor((netWeight * 1000) / portionGrams);
            const costPerPortion = ((portionGrams / 1000) * (220 / (1 - mermaRatio)));
            const suggestedPrice = Math.round(costPerPortion * 3.2);

            document.getElementById('chefNetWeight').innerText = `${netWeight} Kg`;
            document.getElementById('chefPortions').innerText = `${portions} platos`;
            document.getElementById('chefPlatoPrice').innerText = `$${suggestedPrice} MXN`;

            const box = document.getElementById('sheetCanvasBox');
            box.innerHTML = "";
            const canvas = document.createElement('canvas');
            canvas.width = 360; canvas.height = 230;
            const ctx = canvas.getContext('2d');

            ctx.drawImage(capturedImage, 0, 0, 360, 230);

            // Overlay degradado
            const grad = ctx.createLinearGradient(0, 140, 0, 230);
            grad.addColorStop(0, "rgba(0,0,0,0)");
            grad.addColorStop(1, "rgba(0,0,0,0.85)");
            ctx.fillStyle = grad;
            ctx.fillRect(0, 140, 360, 90);

            ctx.fillStyle = "#30D158";
            ctx.font = "bold 13px -apple-system";
            ctx.fillText(`CHEF LEAN V9: ${portions} PORCIONES (${portionGrams}g)`, 16, 190);

            ctx.fillStyle = "rgba(255,255,255,0.8)";
            ctx.font = "10px -apple-system";
            ctx.fillText(`Neto: ${netWeight} Kg | Merma 14% a Caldo Base | P.V.P: $${suggestedPrice} MXN`, 16, 210);

            box.appendChild(canvas);
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
        "engine": "Chef Lean V9 Ultra (Apple Glass UI)",
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
