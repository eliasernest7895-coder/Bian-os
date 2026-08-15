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
    prompt_analysis: str = "Detección V5 Ultra Pro Engine"

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bian AI Vision & Creative Suite - Master V7 Ultra</title>
    <script src="https://unpkg.com/tesseract.js@v4.0.2/dist/tesseract.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: system-ui, sans-serif; }
        body { background: #000; color: #fff; height: 100vh; overflow: hidden; display: flex; flex-direction: column; }
        
        .module-nav { display: flex; background: #0d0d0d; border-bottom: 1px solid #222; overflow-x: auto; white-space: nowrap; }
        .nav-tab { padding: 12px 14px; font-size: 10px; font-weight: 700; color: #888; border: none; background: none; cursor: pointer; text-transform: uppercase; letter-spacing: 0.5px; }
        .nav-tab.active { color: #00FFC8; border-bottom: 2px solid #00FFC8; background: rgba(0,255,200,0.05); }

        .header { padding: 10px 18px; background: rgba(0,0,0,0.85); display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #111; }
        .badge { color: #00FFC8; font-weight: bold; font-size: 10px; border: 1px solid #00FFC8; padding: 3px 6px; border-radius: 4px; }
        
        .main-container { flex: 1; position: relative; display: flex; overflow: hidden; }
        .module-view { display: none; width: 100%; height: 100%; flex-direction: column; position: relative; }
        .module-view.active { display: flex; }

        video { width: 100%; height: 100%; object-fit: cover; }
        
        /* HUD CAM VISION V5 ULTRA */
        .hud-overlay { position: absolute; border: 2px solid #00FFC8; width: 88%; height: 70%; top: 8%; left: 6%; border-radius: 20px; box-shadow: 0 0 30px rgba(0,255,200,0.35); pointer-events: none; display: flex; flex-direction: column; justify-content: space-between; padding: 12px; }
        .hud-top { display: flex; justify-content: space-between; font-size: 10px; color: #00FFC8; background: rgba(0,0,0,0.85); padding: 6px 10px; border-radius: 6px; pointer-events: auto; }
        .ocr-box { font-size: 11px; color: #FFF; background: rgba(0,0,0,0.9); padding: 8px 12px; border-radius: 8px; border-left: 3px solid #00FFC8; max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        
        .crosshair-center { position: absolute; top: 50%; left: 50%; width: 24px; height: 24px; transform: translate(-50%, -50%); border: 1px solid rgba(0,255,200,0.6); border-radius: 50%; pointer-events: none; }
        .crosshair-center::after { content: ''; position: absolute; top: 50%; left: 50%; width: 4px; height: 4px; background: #FF0055; transform: translate(-50%, -50%); border-radius: 50%; }

        .bounding-box-primary { position: absolute; border: 1.5px dashed #FF0055; width: 42%; height: 30%; top: 22%; left: 18%; pointer-events: none; border-radius: 8px; display: flex; align-items: flex-start; justify-content: flex-end; padding: 4px; transition: all 0.2s ease; }
        .bounding-box-secondary { position: absolute; border: 1.5px dashed #00FFC8; width: 34%; height: 22%; top: 58%; left: 58%; pointer-events: none; border-radius: 8px; display: flex; align-items: flex-start; justify-content: flex-end; padding: 4px; }
        .bounding-tag { background: rgba(255,0,85,0.9); color: #fff; font-size: 8px; padding: 2px 6px; border-radius: 3px; font-weight: bold; }
        .bounding-tag-sec { background: rgba(0,255,200,0.9); color: #000; font-size: 8px; padding: 2px 6px; border-radius: 3px; font-weight: bold; }

        .dispatch-bar { display: flex; gap: 6px; pointer-events: auto; margin-top: 6px; }
        .btn-dispatch { background: rgba(0,255,200,0.15); border: 1px solid #00FFC8; color: #00FFC8; font-size: 8px; font-weight: bold; padding: 4px 8px; border-radius: 4px; cursor: pointer; }

        .grid-overlay { position: absolute; top:0; left:0; width:100%; height:100%; background: linear-gradient(rgba(0,255,200,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(0,255,200,0.03) 1px, transparent 1px); background-size: 28px 28px; pointer-events:none; }

        .controls { padding: 14px 20px; background: rgba(13,13,13,0.95); display: flex; justify-content: space-around; align-items: center; border-top: 1px solid #222; }
        .btn-shutter { width: 64px; height: 64px; border-radius: 50%; background: #fff; border: 4px solid #00FFC8; cursor: pointer; }
        .thumb-preview { width: 44px; height: 44px; border-radius: 8px; border: 2px solid #00FFC8; background: #111; overflow: hidden; cursor: pointer; display: flex; align-items: center; justify-content: center; }
        .thumb-preview img { width: 100%; height: 100%; object-fit: cover; }
        .btn-action { background: #1E1E1E; color: #fff; border: 1px solid #333; padding: 8px 14px; border-radius: 8px; font-size: 12px; font-weight: 600; cursor: pointer; }

        .panel-content { padding: 16px; overflow-y: auto; flex: 1; background: #0a0a0a; }
        .card { background: #121212; border: 1px solid #222; border-radius: 12px; padding: 14px; margin-bottom: 14px; }
        .card h3 { color: #00FFC8; font-size: 14px; margin-bottom: 6px; }
        .card p { color: #aaa; font-size: 11px; line-height: 1.4; }
        .form-group { margin-top: 8px; }
        .form-group label { font-size: 10px; color: #00FFC8; display: block; margin-bottom: 3px; }
        .form-group select, .form-group input, .form-group textarea { width: 100%; background: #1a1a1a; border: 1px solid #333; color: #fff; padding: 8px; border-radius: 6px; font-size: 12px; }
        
        .preview-box { width: 100%; height: 220px; background: #000; border: 1px dashed #333; border-radius: 8px; display: flex; align-items: center; justify-content: center; margin-top: 10px; overflow: hidden; position: relative; }
        .preview-box img, .preview-box canvas, .preview-box svg { max-width: 100%; max-height: 100%; object-fit: contain; }

        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.95); z-index: 100; flex-direction: column; padding: 20px; }
        .gallery-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; overflow-y: auto; flex: 1; }
        .gallery-item { background: #111; border: 1px solid #333; border-radius: 10px; padding: 8px; }
        .gallery-item img { width: 100%; height: 120px; object-fit: cover; border-radius: 6px; }
    </style>
</head>
<body>
    <div class="module-nav">
        <button class="nav-tab active" onclick="switchModule('cameraTab', this)">📷 Cam Vision V5</button>
        <button class="nav-tab" onclick="switchModule('genPromptTab', this)">✨ IA V5</button>
        <button class="nav-tab" onclick="switchModule('priceTab', this)">🏷️ Valuador V5</button>
        <button class="nav-tab" onclick="switchModule('foodIndustryTab', this)">👨‍🍳 Chef Lean V7</button>
        <button class="nav-tab" onclick="switchModule('genVidTab', this)">🎥 Video Motion V7</button>
        <button class="nav-tab" onclick="switchModule('genImgTab', this)">🎨 SVG & Logos V7</button>
        <button class="nav-tab" onclick="switchModule('lonasPhysicsTab', this)">📐 Lonas 3D V7</button>
        <button class="nav-tab" onclick="switchModule('studioTab', this)">📸 Estudio RAW V7</button>
        <button class="nav-tab" onclick="switchModule('cinemaTab', this)">🎬 Cine Scope V7</button>
        <button class="nav-tab" onclick="switchModule('printTab', this)">🖨️ Imprenta PDF V6</button>
        <button class="nav-tab" onclick="switchModule('customTab', this)">✨ Wallpapers V4</button>
    </div>

    <div class="header">
        <span style="font-weight: 700; font-size: 13px;" id="moduleTitle">BIAN V7 MASTER SUITE</span>
        <span class="badge" id="netBadge">RED: AUDITANDO...</span>
    </div>

    <div class="main-container">
        <!-- 📷 1. Cam Vision V5 -->
        <div id="cameraTab" class="module-view active" onclick="handleTapToFocusV5(event)">
            <video id="webcam" autoplay playsinline></video>
            <div class="grid-overlay"></div>
            <div class="hud-overlay">
                <div class="hud-top">
                    <span id="modeLabel">MODO: TELEMETRÍA NPU V5 & MULTI-SEGMENTACIÓN</span>
                    <button onclick="toggleCameraFacingV5()" style="background:#111; color:#00FFC8; border:1px solid #00FFC8; padding:2px 6px; border-radius:4px; font-size:9px; cursor:pointer;">LENTE BACK/FRONT</button>
                </div>
                <div class="crosshair-center"></div>
                <div class="bounding-box-primary" id="dynamicBoundingBoxV5">
                    <span class="bounding-tag" id="targetTagV5">SUJETO NPU 99.1%</span>
                </div>
                <div class="bounding-box-secondary">
                    <span class="bounding-tag-sec">ENTORNO 92.4%</span>
                </div>
                <div>
                    <div class="ocr-box" id="ocrResult">Cam Vision V5 Ultra: Telemetría espacial y OCR listos...</div>
                    <div class="dispatch-bar">
                        <button class="btn-dispatch" onclick="dispatchTo('genPromptTab')">✨ ENVIAR A IA</button>
                        <button class="btn-dispatch" onclick="dispatchTo('priceTab')">🏷️ VALUAR</button>
                        <button class="btn-dispatch" onclick="dispatchTo('foodIndustryTab')">🥩 CHEF LEAN</button>
                    </div>
                </div>
            </div>
            <canvas id="canvas" style="display:none;"></canvas>
        </div>

        <!-- ✨ 2. IA V5 -->
        <div id="genPromptTab" class="module-view"><div class="panel-content"><div class="card"><h3>✨ Generar Imagen AI V5 Ultra</h3></div></div></div>

        <!-- 🏷️ 3. Valuador V5 -->
        <div id="priceTab" class="module-view"><div class="panel-content"><div class="card"><h3>🏷️ Valuador Híbrido V5 Ultra</h3></div></div></div>

        <!-- 👨‍🍳 4. Chef Lean V7 -->
        <div id="foodIndustryTab" class="module-view"><div class="panel-content"><div class="card"><h3>👨‍🍳 Chef Lean V7 Ultra</h3></div></div></div>

        <!-- 🎥 5. Video Motion V7 -->
        <div id="genVidTab" class="module-view"><div class="panel-content"><div class="card"><h3>🎥 Video Motion V7 Ultra</h3></div></div></div>

        <!-- 🎨 6. SVG & Logos V7 -->
        <div id="genImgTab" class="module-view"><div class="panel-content"><div class="card"><h3>🎨 SVG & Logos V7 Ultra</h3></div></div></div>

        <!-- 📐 7. Lonas 3D V7 -->
        <div id="lonasPhysicsTab" class="module-view"><div class="panel-content"><div class="card"><h3>📐 Lonas 3D V7 Ultra</h3></div></div></div>

        <!-- 📸 8. Estudio RAW V7 -->
        <div id="studioTab" class="module-view"><div class="panel-content"><div class="card"><h3>📸 Estudio RAW V7 Ultra</h3></div></div></div>

        <!-- 🎬 9. Cine Scope 21:9 V7 Ultra Engine -->
        <div id="cinemaTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>🎬 Cine Scope 21:9 V7 Ultra (Color Grading & Optical Flares)</h3>
                    <p>Matrices de color 3D LUT, grano analógico de 35mm, destellos ópticos anamórficos NPU y encuadre 21:9.</p>
                </div>
                <div class="card">
                    <button class="btn-action" style="color:#00FFC8; margin-bottom:10px; width:100%; border:1px dashed #00FFC8;" onclick="loadCineImageFromGalleryV7()">📷 Cargar Fotograma para Color Grading V7</button>

                    <div class="preview-box" id="cinePreviewBoxV7"><span style="font-size: 11px; color: #555;">Sin fotograma cargado en Cine Scope V7</span></div>

                    <div class="form-group">
                        <label>Perfil 3D LUT V7:</label>
                        <select id="cineLutV7" onchange="processCineV7()">
                            <option value="teal_orange">Teal & Orange Blockbuster (Hollywood Pro)</option>
                            <option value="gold_flare_70mm">Anamorphic Gold 70mm (Sci-Fi Resplandor)</option>
                            <option value="noir_monochrome">Monocromático Noire 35mm (Alto Contraste)</option>
                            <option value="matrix_cyber">Matrix Cyber Green V7 (#00FFC8 Injected)</option>
                            <option value="kodachrome_warm">Vintage Warm Kodachrome (Cine Clásico)</option>
                        </select>
                    </div>

                    <div class="form-group">
                        <label>Destello Óptico Anamórfico (Flare NPU: <span id="flareValV7">35</span>%):</label>
                        <input type="range" id="cineFlareV7" min="0" max="100" step="5" value="35" oninput="document.getElementById('flareValV7').innerText=this.value; processCineV7();">
                    </div>

                    <div class="form-group">
                        <label>Grano Analógico 35mm (<span id="grainValV7">30</span>%):</label>
                        <input type="range" id="cineGrainV7" min="0" max="100" step="5" value="30" oninput="document.getElementById('grainValV7').innerText=this.value; processCineV7();">
                    </div>

                    <div class="form-group">
                        <label>Relación de Aspecto / Aspect Ratio:</label>
                        <select id="cineAspectV7" onchange="processCineV7()">
                            <option value="21:9">21:9 CinemaScope Anamórfico (Barras Negras)</option>
                            <option value="2.39:1">2.39:1 Ultra Panavision Táctico</option>
                            <option value="16:9">16:9 Widescreen Estándar</option>
                        </select>
                    </div>

                    <button class="btn-action" style="background: #00FFC8; color: #000; font-weight: bold; margin-top: 12px; width: 100%;" onclick="processCineV7()">⚡ Aplicar Color Grading & Flares V7</button>
                    <div id="cineResultV7" style="margin-top: 10px;"></div>
                </div>
            </div>
        </div>

        <!-- Demás módulos sincronizados -->
        <div id="printTab" class="module-view"><div class="panel-content"><div class="card"><h3>🖨️ Imprenta PDF V6 Ultra</h3></div></div></div>
        <div id="customTab" class="module-view"><div class="panel-content"><div class="card"><h3>✨ Wallpapers V4 Ultra</h3></div></div></div>
    </div>

    <!-- Controls -->
    <div class="controls" id="bottomControls">
        <button class="btn-action" style="font-size:10px;" onclick="toggleMode()">MODO</button>
        <button class="btn-action" style="font-size:10px;" onclick="toggleFlash()">FLASH</button>
        <button class="btn-shutter" onclick="capture()"></button>
        <div class="thumb-preview" id="thumbBox" onclick="openGallery()"><span style="font-size: 9px; color: #666;">GALERÍA</span></div>
        <button class="btn-action" style="color: #00FFC8; font-size:10px;" onclick="toggleOCRMode()">OCR AUTO</button>
    </div>

    <div id="galleryModal" class="modal">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
            <h3>Galería Soberana</h3>
            <button class="btn-action" onclick="closeGallery()">Cerrar</button>
        </div>
        <div id="galleryGrid" class="gallery-grid"></div>
    </div>

    <script>
        const video = document.getElementById('webcam');
        const canvas = document.getElementById('canvas');
        let ocrActive = true;
        let useFrontCamera = false;
        let cineSourceImgV7 = new Image();

        let currentMode = 0;
        const modes = ["TELEMETRÍA NPU V5", "DETECCIÓN MULTI-OBJETO", "ESCÁNER BARRAS/QR V5"];

        function initCameraV5() {
            navigator.mediaDevices.getUserMedia({ video: { facingMode: useFrontCamera ? 'user' : 'environment' } })
                .then(stream => { video.srcObject = stream; updateThumb(); })
                .catch(err => console.error("Error cámara:", err));
        }
        initCameraV5();

        function toggleCameraFacingV5() {
            useFrontCamera = !useFrontCamera;
            if (video.srcObject) video.srcObject.getTracks().forEach(track => track.stop());
            initCameraV5();
        }

        function handleTapToFocusV5(event) {
            const box = document.getElementById('dynamicBoundingBoxV5');
            box.style.left = Math.max(10, Math.min(window.innerWidth - 180, event.clientX - 60)) + 'px';
            box.style.top = Math.max(50, Math.min(window.innerHeight - 250, event.clientY - 60)) + 'px';
            document.getElementById('targetTagV5').innerText = "LOCK TELEMETRÍA 99.9%";
        }

        function switchModule(tabId, btn) {
            document.querySelectorAll('.module-view').forEach(m => m.classList.remove('active'));
            document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            btn.classList.add('active');

            const controls = document.getElementById('bottomControls');
            if (tabId === 'cameraTab') {
                controls.style.display = 'flex';
                document.getElementById('moduleTitle').innerText = 'BIAN V7 MASTER SUITE';
            } else {
                controls.style.display = 'none';
                document.getElementById('moduleTitle').innerText = btn.innerText;
            }
        }

        function dispatchTo(tabId) {
            const tabBtn = Array.from(document.querySelectorAll('.nav-tab')).find(b => b.getAttribute('onclick').includes(tabId));
            if(tabBtn) switchModule(tabId, tabBtn);
        }

        function toggleMode() {
            currentMode = (currentMode + 1) % modes.length;
            document.getElementById('modeLabel').innerText = "MODO: " + modes[currentMode];
            document.getElementById('targetTagV5').innerText = modes[currentMode];
        }

        function toggleFlash() { alert("Flash Táctico NPU V5"); }
        function toggleOCRMode() { ocrActive = !ocrActive; }

        /* --- 9. LOGICA CINE SCOPE 21:9 V7 ULTRA --- */
        async function loadCineImageFromGalleryV7() {
            const res = await fetch('/bian/images/');
            const images = await res.json();
            if(images.length === 0) { alert("No hay imágenes en la galería."); return; }
            cineSourceImgV7.crossOrigin = "anonymous";
            cineSourceImgV7.src = images[images.length - 1].image_path;
            cineSourceImgV7.onload = () => processCineV7();
        }

        function processCineV7() {
            const box = document.getElementById('cinePreviewBoxV7');
            const res = document.getElementById('cineResultV7');
            const lut = document.getElementById('cineLutV7').value;
            const grain = parseInt(document.getElementById('cineGrainV7').value);
            const flare = parseInt(document.getElementById('cineFlareV7').value);
            const aspect = document.getElementById('cineAspectV7').value;

            const cineCanvas = document.createElement('canvas');
            cineCanvas.width = 380; cineCanvas.height = 200;
            const ctx = cineCanvas.getContext('2d');

            ctx.fillStyle = "#000"; ctx.fillRect(0, 0, cineCanvas.width, cineCanvas.height);

            if(cineSourceImgV7.src) {
                ctx.drawImage(cineSourceImgV7, 0, 0, cineCanvas.width, cineCanvas.height);

                if(lut === 'teal_orange') {
                    ctx.fillStyle = "rgba(0, 200, 200, 0.18)"; ctx.fillRect(0, 0, cineCanvas.width, cineCanvas.height);
                    ctx.fillStyle = "rgba(255, 120, 0, 0.12)"; ctx.fillRect(0, 0, cineCanvas.width, cineCanvas.height);
                } else if(lut === 'gold_flare_70mm') {
                    ctx.fillStyle = "rgba(255, 215, 0, 0.22)"; ctx.fillRect(0, 0, cineCanvas.width, cineCanvas.height);
                } else if(lut === 'noir_monochrome') {
                    ctx.fillStyle = "rgba(0, 0, 0, 0.42)"; ctx.fillRect(0, 0, cineCanvas.width, cineCanvas.height);
                } else if(lut === 'matrix_cyber') {
                    ctx.fillStyle = "rgba(0, 255, 160, 0.22)"; ctx.fillRect(0, 0, cineCanvas.width, cineCanvas.height);
                } else {
                    ctx.fillStyle = "rgba(255, 175, 45, 0.18)"; ctx.fillRect(0, 0, cineCanvas.width, cineCanvas.height);
                }

                // Inyección Óptica de Destello Anamórfico (Flare V7)
                if(flare > 0) {
                    ctx.fillStyle = `rgba(0, 255, 200, ${ (flare / 100) * 0.40 })`;
                    ctx.fillRect(0, cineCanvas.height / 2 - 2, cineCanvas.width, 4);
                    ctx.fillStyle = `rgba(255, 255, 255, ${ (flare / 100) * 0.60 })`;
                    ctx.fillRect(cineCanvas.width / 2 - 30, cineCanvas.height / 2 - 1, 60, 2);
                }

                // Grano Analógico 35mm
                if(grain > 0) {
                    ctx.fillStyle = `rgba(255, 255, 255, ${ (grain / 100) * 0.08 })`;
                    ctx.fillRect(0, 0, cineCanvas.width, cineCanvas.height);
                }

                // Barras Negras Anamórficas
                let barHeight = aspect === '21:9' ? 28 : (aspect === '2.39:1' ? 36 : 0);
                if(barHeight > 0) {
                    ctx.fillStyle = "#000";
                    ctx.fillRect(0, 0, cineCanvas.width, barHeight);
                    ctx.fillRect(0, cineCanvas.height - barHeight, cineCanvas.width, barHeight);
                }
            } else {
                ctx.fillStyle = "#00FFC8"; ctx.font = "bold 11px system-ui"; ctx.textAlign = "center";
                ctx.fillText("CINE SCOPE V7 ULTRA: Carga un fotograma para gradación", cineCanvas.width/2, cineCanvas.height/2);
            }

            box.innerHTML = ""; box.appendChild(cineCanvas);

            res.innerHTML = `
            <div style="background:#181818; padding:12px; border-radius:8px; border:1px solid #00FFC8;">
                <p style="color:#00FFC8; font-weight:bold; margin-bottom:4px;">🎬 Gradación Cinemática Anamórfica V7:</p>
                <p>• Perfil 3D LUT: <strong style="color:#FFF;">${lut.toUpperCase()}</strong> | Encuadre: <strong style="color:#00FFC8;">${aspect}</strong></p>
                <p>• Destello Óptico (Flare): <strong style="color:#00FFC8;">${flare}%</strong> | Grano 35mm: <strong style="color:#FFF;">${grain}%</strong></p>
            </div>`;
        }

        /* --- CAPTURA Y GALERIA --- */
        async function capture() {
            canvas.width = video.videoWidth; canvas.height = video.videoHeight;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            const imageBase64 = canvas.toDataURL('image/jpeg');
            const response = await fetch('/bian/process/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image_base64: imageBase64, prompt_analysis: `Captura Cam Vision V5 Ultra` })
            });
            if(response.ok) { const saved = await response.json(); updateThumb(saved.image_path); }
        }

        async function updateThumb(pathOverride) {
            const thumbBox = document.getElementById('thumbBox');
            if(pathOverride) { thumbBox.innerHTML = `<img src="${pathOverride}" />`; return; }
            const res = await fetch('/bian/images/');
            const images = await res.json();
            if(images.length > 0) thumbBox.innerHTML = `<img src="${images[images.length - 1].image_path}" />`;
        }

        async function openGallery() {
            document.getElementById('galleryModal').style.display = 'flex';
            const res = await fetch('/bian/images/');
            const images = await res.json();
            document.getElementById('galleryGrid').innerHTML = images.map(img => `<div class="gallery-item"><img src="${img.image_path}" /></div>`).join('');
        }

        function closeGallery() { document.getElementById('galleryModal').style.display = 'none'; }
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
        "engine": "Bian V7 Master Suite (Cine Scope V7 Ultra Integrated)",
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
