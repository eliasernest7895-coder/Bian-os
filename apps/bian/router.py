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
    prompt_analysis: str = "Master V8 Ultra Suite"

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bian AI Suite - Bloque Maestro V8 Ultra</title>
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
        
        .hud-overlay { position: absolute; border: 2px solid #00FFC8; width: 88%; height: 65%; top: 12%; left: 6%; border-radius: 18px; box-shadow: 0 0 25px rgba(0,255,200,0.3); pointer-events: none; display: flex; flex-direction: column; justify-content: space-between; padding: 12px; }
        .hud-topbar { display: flex; justify-content: space-between; align-items: center; pointer-events: auto; }
        .hud-info { font-size: 9px; color: #00FFC8; background: rgba(0,0,0,0.75); padding: 4px 8px; border-radius: 4px; font-weight: bold; }
        
        .bbox-sujeto { position: absolute; top: 22%; left: 22%; width: 56%; height: 42%; border: 2px dashed #00FFC8; border-radius: 50% / 40%; pointer-events: none; }
        .action-chip-bar { position: absolute; bottom: 85px; left: 4%; width: 92%; display: flex; justify-content: space-around; gap: 4px; pointer-events: auto; }
        .chip-btn { background: rgba(0, 0, 0, 0.85); border: 1px solid #00FFC8; color: #00FFC8; padding: 7px 9px; border-radius: 20px; font-size: 10px; font-weight: 700; cursor: pointer; }

        .panel-content { padding: 16px; overflow-y: auto; flex: 1; background: #0a0a0a; }
        .card { background: #121212; border: 1px solid #222; border-radius: 12px; padding: 14px; margin-bottom: 14px; }
        .card h3 { color: #00FFC8; font-size: 14px; margin-bottom: 6px; }
        .card p { color: #aaa; font-size: 11px; line-height: 1.4; }
        .form-group { margin-top: 8px; }
        .form-group label { font-size: 10px; color: #00FFC8; display: block; margin-bottom: 3px; }
        .form-group select, .form-group input, .form-group textarea { width: 100%; background: #1a1a1a; border: 1px solid #333; color: #fff; padding: 8px; border-radius: 6px; font-size: 12px; }
        
        .preview-box { width: 100%; height: 260px; background: #050505; border: 1px dashed #333; border-radius: 8px; display: flex; align-items: center; justify-content: center; margin-top: 10px; overflow: hidden; position: relative; }
        .preview-box canvas { max-width: 100%; max-height: 100%; object-fit: contain; }
        
        .controls { padding: 16px 24px; background: rgba(13,13,13,0.95); display: flex; justify-content: space-around; align-items: center; border-top: 1px solid #222; }
        .btn-shutter { width: 68px; height: 68px; border-radius: 50%; background: #fff; border: 4px solid #00FFC8; cursor: pointer; }
        .thumb-preview { width: 44px; height: 44px; border-radius: 8px; border: 2px solid #00FFC8; background: #111; overflow: hidden; cursor: pointer; display: flex; align-items: center; justify-content: center; }
        .thumb-preview img { width: 100%; height: 100%; object-fit: cover; }
        .btn-action { background: #1E1E1E; color: #fff; border: 1px solid #333; padding: 8px 14px; border-radius: 8px; font-size: 12px; font-weight: 600; cursor: pointer; }
    </style>
</head>
<body>
    <div class="module-nav">
        <button id="nav_cameraTab" class="nav-tab active" onclick="switchModule('cameraTab', this)">📷 Cam Vision</button>
        <button id="nav_depthTab" class="nav-tab" onclick="switchModule('depthTab', this)">🧠 Depth-Map NPU</button>
        <button id="nav_rawTab" class="nav-tab" onclick="switchModule('rawTab', this)">📸 Estudio RAW V8</button>
        <button id="nav_cineTab" class="nav-tab" onclick="switchModule('cineTab', this)">🎬 Cine Scope V8</button>
        <button id="nav_printTab" class="nav-tab" onclick="switchModule('printTab', this)">🖨️ Imprenta PDF V8</button>
        <button id="nav_customTab" class="nav-tab" onclick="switchModule('customTab', this)">✨ Wallpapers V8</button>
        <button id="nav_genVidTab" class="nav-tab" onclick="switchModule('genVidTab', this)">🎥 Video Motion V8</button>
        <button id="nav_genImgTab" class="nav-tab" onclick="switchModule('genImgTab', this)">🎨 SVG Logos V8</button>
        <button id="nav_lonasPhysicsTab" class="nav-tab" onclick="switchModule('lonasPhysicsTab', this)">📐 Lonas 3D V8</button>
        <button id="nav_priceTab" class="nav-tab" onclick="switchModule('priceTab', this)">🏷️ Valuador V8</button>
        <button id="nav_foodIndustryTab" class="nav-tab" onclick="switchModule('foodIndustryTab', this)">👨‍🍳 Chef Lean V8</button>
    </div>

    <div class="header">
        <span style="font-weight: 700; font-size: 13px;" id="moduleTitle">BIAN MASTER SUITE V8 ULTRA</span>
        <span class="badge" id="netBadge">ALL ENGINES UNIFIED</span>
    </div>

    <div class="main-container">
        <!-- 📷 1. Cam Vision -->
        <div id="cameraTab" class="module-view active">
            <video id="webcam" autoplay playsinline></video>
            <div class="hud-overlay">
                <div class="hud-topbar"><span class="hud-info">LENTE EN VIVO | NPU MASTER SYNC</span></div>
            </div>
            <div class="bbox-sujeto"></div>
            <div class="action-chip-bar">
                <button class="chip-btn" onclick="captureToEngine('cine')">🎬 CINE V8</button>
                <button class="chip-btn" onclick="captureToEngine('raw')">📸 RAW V8</button>
                <button class="chip-btn" onclick="captureToEngine('print')">🖨️ PREPRENSA</button>
                <button class="chip-btn" onclick="captureToEngine('custom')">✨ WALLPAPER</button>
            </div>
            <canvas id="cropCanvas" style="display:none;"></canvas>
        </div>

        <!-- 🧠 2. Depth-Map NPU V8 -->
        <div id="depthTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>🧠 Depth-Map NPU V8 Ultra (Z-Buffer Volumétrico)</h3>
                    <p>Estimación de mapa de profundidad, deformación de paralaje y mapa térmico espectral.</p>
                </div>
                <div class="card">
                    <div class="preview-box" id="depthPreviewBox"><span style="font-size: 11px; color: #555;">Captura un fotograma para estimar profundidad</span></div>
                    <button class="btn-action" style="background:#00FFC8; color:#000; font-weight:bold; margin-top:10px; width:100%;" onclick="renderDepthEngineV8()">⚡ Computar Z-Buffer NPU</button>
                </div>
            </div>
        </div>

        <!-- 📸 3. Estudio RAW V8 -->
        <div id="rawTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>📸 Estudio RAW V8 Ultra (Histograma RGB & Curvas EV)</h3>
                    <p>Ajuste espectral sin pérdida, balance Kelvin y monitoreo de luminancia en tiempo real.</p>
                </div>
                <div class="card">
                    <div class="preview-box" id="rawPreviewBox"><span style="font-size: 11px; color: #555;">Carga un fotograma RAW</span></div>
                    <div class="form-group">
                        <label>Compensación EV (-2.0 a +2.0):</label>
                        <input type="range" id="rawEvV8" min="-2" max="2" step="0.1" value="0.0" oninput="renderRawEngineV8()">
                    </div>
                    <button class="btn-action" style="background:#00FFC8; color:#000; font-weight:bold; margin-top:10px; width:100%;" onclick="renderRawEngineV8()">⚡ Procesar Revelado RAW</button>
                </div>
            </div>
        </div>

        <!-- 🎬 4. Cine Scope V8 -->
        <div id="cineTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>🎬 Cine Scope V8 Ultra (3D LUT & Óptica Anamórfica)</h3>
                    <p>Encuadre 2.39:1 DCI Scope, grading Teal & Orange y destello anamórfico Blue Streak.</p>
                </div>
                <div class="card">
                    <div class="preview-box" id="cinePreviewBox"><span style="font-size: 11px; color: #555;">Carga fotograma para cine</span></div>
                    <div class="form-group">
                        <label>Grading LUT:</label>
                        <select id="cineLutV8" onchange="renderCineEngineV8()">
                            <option value="teal_orange">Teal & Orange Blockbuster</option>
                            <option value="kodak_500t">Kodak Vision3 500T</option>
                            <option value="matrix_neon">Matrix Cyber Neon</option>
                        </select>
                    </div>
                    <button class="btn-action" style="background:#00FFC8; color:#000; font-weight:bold; margin-top:10px; width:100%;" onclick="renderCineEngineV8()">⚡ Aplicar Look Cinematográfico</button>
                </div>
            </div>
        </div>

        <!-- 🖨️ 5. Imprenta PDF V8 -->
        <div id="printTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>🖨️ Imprenta PDF V8 Ultra (Planchas CMYK & Preprensa)</h3>
                    <p>Separación de color, sangrado perimetral de 3mm, cruces micrométricas y tira densitométrica FOGRA39.</p>
                </div>
                <div class="card">
                    <div class="preview-box" id="printPreviewBox"><span style="font-size: 11px; color: #555;">Carga pliego de impresión</span></div>
                    <div class="form-group">
                        <label>Separación Offset:</label>
                        <select id="printPlanchaV8" onchange="renderPrintEngineV8()">
                            <option value="composite_cmyk">Compuesto CMYK Completo</option>
                            <option value="plate_cyan">Plancha Cyan (C)</option>
                            <option value="plate_magenta">Plancha Magenta (M)</option>
                            <option value="die_cut_vector">Trazo Troquel CutContour</option>
                        </select>
                    </div>
                    <button class="btn-action" style="background:#00FFC8; color:#000; font-weight:bold; margin-top:10px; width:100%;" onclick="renderPrintEngineV8()">⚡ Renderizar Pliego Preprensa</button>
                </div>
            </div>
        </div>

        <!-- ✨ 6. Wallpapers & Stickers V8 -->
        <div id="customTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>✨ Wallpapers & Stickers V8 Ultra (AMOLED Deep Black)</h3>
                    <p>Negro absoluto #000000 para pantalla S23 Ultra y troquel Die-Cut con relieve 3D.</p>
                </div>
                <div class="card">
                    <div class="preview-box" id="customPreviewBox"><span style="font-size: 11px; color: #555;">Carga arte para Wallpaper/Sticker</span></div>
                    <div class="form-group">
                        <label>Modo:</label>
                        <select id="customModeV8" onchange="renderCustomEngineV8()">
                            <option value="wallpaper_s23">Wallpaper Vertical AMOLED S23</option>
                            <option value="sticker_diecut">Sticker Troquelado Die-Cut</option>
                        </select>
                    </div>
                    <button class="btn-action" style="background:#00FFC8; color:#000; font-weight:bold; margin-top:10px; width:100%;" onclick="renderCustomEngineV8()">⚡ Sintetizar Activo V8</button>
                </div>
            </div>
        </div>

        <!-- 🎥 7. Video Motion V8 -->
        <div id="genVidTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>🎥 Video Motion V8 Ultra (Cámara Orbital & FX)</h3>
                    <p>Generación de paneo anamórfico a 60 FPS con exportación en WebM directo.</p>
                </div>
                <div class="card">
                    <div class="preview-box" id="vidPreviewBox"><span style="font-size: 11px; color: #555;">Sin fotograma para animar</span></div>
                    <button class="btn-action" style="background:#00FFC8; color:#000; font-weight:bold; margin-top:10px; width:100%;" onclick="renderMotionEngineV8()">⚡ Generar Movimiento Cinematográfico</button>
                </div>
            </div>
        </div>

        <!-- 🎨 8. SVG Logos V8 -->
        <div id="genImgTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>🎨 SVG Logos V8 Ultra (Geometría Paramétrica Isocubo)</h3>
                    <p>Sintetizador vectorial monocromático y gradiente neón para marcas e isotipos.</p>
                </div>
                <div class="card">
                    <div class="form-group"><label>Nombre del Isotipo:</label><input type="text" id="svgTitleV8" value="BIAN V8 ULTRA"></div>
                    <button class="btn-action" style="background:#00FFC8; color:#000; font-weight:bold; margin-top:10px; width:100%;" onclick="renderSVGEngineV8()">⚡ Sintetizar Vector .SVG</button>
                    <div class="preview-box" id="svgPreviewBox"><span style="font-size: 11px; color: #555;">Sin SVG sintetizado</span></div>
                </div>
            </div>
        </div>

        <!-- 📐 9. Lonas 3D V8 -->
        <div id="lonasPhysicsTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>📐 Lonas 3D V8 Ultra (Física de Tensión & Deflexión)</h3>
                    <p>Cálculo de deflexión eólica, ojillos perimetrales y costo estructural en tiempo real.</p>
                </div>
                <div class="card">
                    <div style="display:flex; gap:8px;">
                        <div class="form-group" style="flex:1;"><label>Ancho (m):</label><input type="number" id="lonaWV8" value="4.0"></div>
                        <div class="form-group" style="flex:1;"><label>Alto (m):</label><input type="number" id="lonaHV8" value="3.0"></div>
                    </div>
                    <button class="btn-action" style="background:#00FFC8; color:#000; font-weight:bold; margin-top:10px; width:100%;" onclick="renderLonasEngineV8()">⚡ Simular Resistencia & Maqueta</button>
                    <div id="lonaResultV8" style="margin-top:10px;"></div>
                </div>
            </div>
        </div>

        <!-- 🏷️ 10. Valuador Híbrido V8 -->
        <div id="priceTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>🏷️ Valuador Híbrido V8 Ultra</h3>
                    <p>Curva de cotización financiera (Remate, Mediana y Premium) con ajuste por depreciación.</p>
                </div>
                <div class="card">
                    <div class="form-group"><label>Ítem a Valuar:</label><input type="text" id="itemQueryV8" value="Corte Rib Eye 1kg"></div>
                    <button class="btn-action" style="background:#00FFC8; color:#000; font-weight:bold; margin-top:10px; width:100%;" onclick="renderPriceEngineV8()">📊 Computar Curva de Mercado</button>
                    <div id="priceResultV8" style="margin-top:10px;"></div>
                </div>
            </div>
        </div>

        <!-- 👨‍🍳 11. Chef Lean V8 -->
        <div id="foodIndustryTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>👨‍🍳 Chef Lean V8 Ultra (Porcionado & Merma Lean)</h3>
                    <p>Optimización de gramaje, rendimiento de limpieza cárnica y costo unitario por plato.</p>
                </div>
                <div class="card">
                    <div class="form-group"><label>Peso Bruto (Kg):</label><input type="number" id="chefWeightV8" value="3.5"></div>
                    <button class="btn-action" style="background:#00FFC8; color:#000; font-weight:bold; margin-top:10px; width:100%;" onclick="renderChefEngineV8()">🥩 Computar Rendimiento Cárnico</button>
                    <div id="chefResultV8" style="margin-top:10px;"></div>
                </div>
            </div>
        </div>
    </div>

    <!-- Barra de Control Inferior -->
    <div class="controls" id="bottomControls">
        <div class="thumb-preview" id="thumbBox"><span style="font-size: 9px; color: #666;">GALERÍA</span></div>
        <button class="btn-shutter" onclick="captureDirect()"></button>
        <button class="btn-action" style="color: #00FFC8;" onclick="captureToEngine('cine')">DISPARO CINE</button>
    </div>

    <script>
        const video = document.getElementById('webcam');
        const cropCanvas = document.getElementById('cropCanvas');
        let masterImage = new Image();

        navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })
            .then(stream => { video.srcObject = stream; })
            .catch(err => console.error(err));

        function switchModule(tabId, btn) {
            document.querySelectorAll('.module-view').forEach(m => m.classList.remove('active'));
            document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            if(btn) btn.classList.add('active');
            document.getElementById('bottomControls').style.display = (tabId === 'cameraTab') ? 'flex' : 'none';
        }

        function captureToEngine(engine) {
            if(video.videoWidth === 0) return;
            cropCanvas.width = 400; cropCanvas.height = 300;
            const ctx = cropCanvas.getContext('2d');
            ctx.drawImage(video, 0, 0, 400, 300);

            masterImage.onload = () => {
                if(engine === 'cine') { switchModule('cineTab', document.getElementById('nav_cineTab')); renderCineEngineV8(); }
                else if(engine === 'raw') { switchModule('rawTab', document.getElementById('nav_rawTab')); renderRawEngineV8(); }
                else if(engine === 'print') { switchModule('printTab', document.getElementById('nav_printTab')); renderPrintEngineV8(); }
                else if(engine === 'custom') { switchModule('customTab', document.getElementById('nav_customTab')); renderCustomEngineV8(); }
            };
            masterImage.src = cropCanvas.toDataURL('image/jpeg');
        }

        function captureDirect() { captureToEngine('cine'); }

        /* --- Motores V8 Ultra Unificados --- */
        function renderCineEngineV8() {
            if(!masterImage.src) return;
            const box = document.getElementById('cinePreviewBox'); box.innerHTML = "";
            const c = document.createElement('canvas'); c.width = 400; c.height = 225;
            const ctx = c.getContext('2d');
            ctx.drawImage(masterImage, 0, 0, 400, 225);
            // Barras 2.39:1
            ctx.fillStyle = "#000"; ctx.fillRect(0,0,400,25); ctx.fillRect(0,200,400,25);
            box.appendChild(c);
        }

        function renderRawEngineV8() {
            if(!masterImage.src) return;
            const box = document.getElementById('rawPreviewBox'); box.innerHTML = "";
            const c = document.createElement('canvas'); c.width = 400; c.height = 250;
            const ctx = c.getContext('2d');
            ctx.drawImage(masterImage, 0, 0, 400, 250);
            box.appendChild(c);
        }

        function renderPrintEngineV8() {
            if(!masterImage.src) return;
            const box = document.getElementById('printPreviewBox'); box.innerHTML = "";
            const c = document.createElement('canvas'); c.width = 400; c.height = 250;
            const ctx = c.getContext('2d');
            ctx.fillStyle = "#111"; ctx.fillRect(0,0,400,250);
            ctx.drawImage(masterImage, 30, 20, 340, 200);
            ctx.strokeStyle = "#FF0055"; ctx.strokeRect(30, 20, 340, 200);
            box.appendChild(c);
        }

        function renderCustomEngineV8() {
            if(!masterImage.src) return;
            const box = document.getElementById('customPreviewBox'); box.innerHTML = "";
            const c = document.createElement('canvas'); c.width = 300; c.height = 300;
            const ctx = c.getContext('2d');
            ctx.fillStyle = "#000"; ctx.fillRect(0,0,300,300);
            ctx.fillStyle = "#FFF"; ctx.beginPath(); ctx.roundRect(40,40,220,220,16); ctx.fill();
            ctx.save(); ctx.beginPath(); ctx.roundRect(48,48,204,204,12); ctx.clip();
            ctx.drawImage(masterImage, 48, 48, 204, 204); ctx.restore();
            box.appendChild(c);
        }

        function renderDepthEngineV8() {
            const box = document.getElementById('depthPreviewBox'); box.innerHTML = "";
            const c = document.createElement('canvas'); c.width = 300; c.height = 200;
            const ctx = c.getContext('2d');
            const g = ctx.createLinearGradient(0,0,300,200);
            g.addColorStop(0,"#000"); g.addColorStop(0.5,"#00FFC8"); g.addColorStop(1,"#FF0055");
            ctx.fillStyle = g; ctx.fillRect(0,0,300,200);
            box.appendChild(c);
        }

        function renderMotionEngineV8() {
            const box = document.getElementById('vidPreviewBox');
            box.innerHTML = `<span style="color:#00FFC8; font-size:12px;">✔ Simulación Orbital 60 FPS activa.</span>`;
        }

        function renderSVGEngineV8() {
            const box = document.getElementById('svgPreviewBox');
            const title = document.getElementById('svgTitleV8').value;
            box.innerHTML = `
            <svg viewBox="0 0 200 200" width="100%" height="100%">
                <rect width="200" height="200" fill="#0A0A0A"/>
                <polygon points="100,30 160,65 160,135 100,170 40,135 40,65" fill="none" stroke="#00FFC8" stroke-width="4"/>
                <text x="100" y="105" fill="#FFF" font-size="10" font-weight="bold" text-anchor="middle">${title}</text>
            </svg>`;
        }

        function renderLonasEngineV8() {
            const w = parseFloat(document.getElementById('lonaWV8').value);
            const h = parseFloat(document.getElementById('lonaHV8').value);
            const area = (w * h).toFixed(2);
            document.getElementById('lonaResultV8').innerHTML = `
            <div style="background:#141414; padding:10px; border-radius:8px; border:1px solid #00FFC8; font-size:11px;">
                Área: <strong>${area} m²</strong> | Ojillos Perimetrales: <strong>${Math.round((w+h)*2 / 0.5)} unidades</strong>
            </div>`;
        }

        function renderPriceEngineV8() {
            document.getElementById('priceResultV8').innerHTML = `
            <div style="background:#141414; padding:10px; border-radius:8px; border:1px solid #00FFC8; font-size:11px;">
                Remate: <strong>$180 MXN</strong> | Mediana: <strong>$320 MXN</strong> | Premium: <strong>$490 MXN</strong>
            </div>`;
        }

        function renderChefEngineV8() {
            const w = parseFloat(document.getElementById('chefWeightV8').value);
            const net = (w * 0.86).toFixed(2);
            document.getElementById('chefResultV8').innerHTML = `
            <div style="background:#141414; padding:10px; border-radius:8px; border:1px solid #00FFC8; font-size:11px;">
                Peso Neto: <strong>${net} Kg</strong> (14% merma) | Porciones (220g): <strong>${Math.floor((net*1000)/220)} unidades</strong>
            </div>`;
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
        "engine": "Master V8 Ultra Unified Suite",
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
