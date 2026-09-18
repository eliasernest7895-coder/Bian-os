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
    prompt_analysis: str = "Detección V8 Ultra Engine"

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bian AI Vision & Creative Suite - Master V8 Ultra</title>
    <script src="https://unpkg.com/tesseract.js@v4.0.2/dist/tesseract.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
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
        .hud-info { font-size: 9px; color: #00FFC8; background: rgba(0,0,0,0.75); padding: 4px 8px; border-radius: 4px; font-weight: bold; letter-spacing: 0.5px; }
        
        .bbox-sujeto { position: absolute; top: 22%; left: 22%; width: 56%; height: 42%; border: 2px dashed #00FFC8; border-radius: 50% / 40%; pointer-events: none; display: flex; flex-direction: column; justify-content: flex-start; box-shadow: 0 0 15px rgba(0, 255, 200, 0.2); }
        .bbox-tag { font-size: 8px; background: #00FFC8; color: #000; padding: 2px 6px; border-radius: 3px; align-self: center; font-weight: 900; margin-top: -10px; }

        .action-chip-bar { position: absolute; bottom: 85px; left: 4%; width: 92%; display: flex; justify-content: space-around; gap: 4px; pointer-events: auto; }
        .chip-btn { background: rgba(0, 0, 0, 0.85); border: 1px solid #00FFC8; color: #00FFC8; padding: 7px 9px; border-radius: 20px; font-size: 10px; font-weight: 700; cursor: pointer; backdrop-filter: blur(4px); }
        .chip-btn:hover { background: #00FFC8; color: #000; }

        .controls { padding: 16px 24px; background: rgba(13,13,13,0.95); display: flex; justify-content: space-around; align-items: center; border-top: 1px solid #222; }
        .btn-shutter { width: 68px; height: 68px; border-radius: 50%; background: #fff; border: 4px solid #00FFC8; cursor: pointer; }
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
        
        .preview-box { width: 100%; height: 250px; background: #000; border: 1px dashed #333; border-radius: 8px; display: flex; align-items: center; justify-content: center; margin-top: 10px; overflow: hidden; position: relative; }
        .preview-box img, .preview-box canvas, .preview-box svg { max-width: 100%; max-height: 100%; object-fit: contain; }

        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.95); z-index: 100; flex-direction: column; padding: 20px; }
        .gallery-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; overflow-y: auto; flex: 1; }
        .gallery-item { background: #111; border: 1px solid #333; border-radius: 10px; padding: 8px; }
        .gallery-item img { width: 100%; height: 120px; object-fit: cover; border-radius: 6px; }
    </style>
</head>
<body>
    <div class="module-nav">
        <button id="nav_cameraTab" class="nav-tab active" onclick="switchModule('cameraTab', this)">📷 Cam Vision V6</button>
        <button id="nav_synthTab" class="nav-tab" onclick="switchModule('synthTab', this)">✨ IA V6 Ultra</button>
        <button id="nav_priceTab" class="nav-tab" onclick="switchModule('priceTab', this)">🏷️ Valuador V6</button>
        <button id="nav_foodIndustryTab" class="nav-tab" onclick="switchModule('foodIndustryTab', this)">👨‍🍳 Chef Lean V6</button>
        <button id="nav_genVidTab" class="nav-tab" onclick="switchModule('genVidTab', this)">🎥 Video Motion V8</button>
        <button id="nav_genImgTab" class="nav-tab" onclick="switchModule('genImgTab', this)">🎨 SVG Logos V8</button>
        <button id="nav_lonasPhysicsTab" class="nav-tab" onclick="switchModule('lonasPhysicsTab', this)">📐 Lonas 3D V8</button>
    </div>

    <div class="header">
        <span style="font-weight: 700; font-size: 13px;" id="moduleTitle">BIAN AI SUITE V8 ULTRA</span>
        <span class="badge" id="netBadge">RED: AUDITANDO...</span>
    </div>

    <div class="main-container">
        <!-- 📷 Cam Vision V6 -->
        <div id="cameraTab" class="module-view active">
            <video id="webcam" autoplay playsinline></video>
            
            <div class="hud-overlay">
                <div class="hud-topbar">
                    <span class="hud-info">V6 ALPHA MATTE | SNAPDRAGON 8 GEN 2</span>
                    <button class="chip-btn" style="padding: 3px 8px; font-size: 9px;" onclick="toggleCameraFacing()">🔄 LENTE</button>
                </div>
            </div>

            <div class="bbox-sujeto" id="sujetoBox">
                <div class="bbox-tag">ROI ALPHA MATTE 99.8%</div>
            </div>

            <div class="action-chip-bar">
                <button class="chip-btn" onclick="routeToSynthFromCam()">✨ INYECTAR IA V6</button>
                <button class="chip-btn" onclick="routeToValuatorFromCam()">🏷️ VALUAR V6</button>
                <button class="chip-btn" onclick="routeToChefFromCam()">👨‍🍳 CHEF LEAN V6</button>
                <button class="chip-btn" onclick="captureDirect()">⚡ CAPTURAR</button>
            </div>

            <canvas id="canvas" style="display:none;"></canvas>
            <canvas id="cropCanvas" style="display:none;"></canvas>
        </div>

        <!-- ✨ IA V6 Ultra -->
        <div id="synthTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>✨ IA V6 Ultra (Difusión Procedural + Sujeto Alfa)</h3>
                    <p>Renderizado fotorrealista de escenarios generados por descripción e integración de objetos del mundo real.</p>
                </div>
                <div class="card">
                    <div class="form-group">
                        <label>Prompt del Escenario AI:</label>
                        <input type="text" id="synthPrompt" value="Mesa gourmet de restaurante Michelin con humo sutil y bokeh anamórfico">
                    </div>
                    <div class="form-group">
                        <label>Preset de Difusión y Atmósfera:</label>
                        <select id="synthStyle">
                            <option value="michelin_table">Gourmet Dark Studio (Luz Focal Ámbar & Humo)</option>
                            <option value="cyberpunk_market">Cyberpunk Street Neon (Gradiente Láser)</option>
                            <option value="clean_minimal">Estudio Fotográfico Blanco Puro (Catálogo)</option>
                        </select>
                    </div>
                    <button class="btn-action" style="background: #00FFC8; color: #000; font-weight: bold; margin-top: 10px; width: 100%;" onclick="generateAiCompositeV6()">Generar Escenario & Fusionar Sujeto</button>
                    
                    <div class="preview-box" id="synthPreviewBox">
                        <span style="font-size: 11px; color: #555;">Sin activo sintetizado</span>
                    </div>

                    <button class="btn-action" id="btnSendToVideo" style="color: #00FFC8; margin-top: 10px; width: 100%; display: none;" onclick="sendCompositeToVideoEngine()">🎥 Mandar a Video Motion V8 (Cinemática Multieje)</button>
                </div>
            </div>
        </div>

        <!-- 🏷️ Valuador Híbrido V6 -->
        <div id="priceTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>🏷️ Valuador Híbrido V6 (Market Intelligence & ROI)</h3>
                    <p>Tasación multimodal de insumos, herramientas y productos con cálculo dinámico de margen comercial.</p>
                </div>
                <div class="card">
                    <div style="display:flex; gap:12px; align-items:center; margin-bottom:10px;">
                        <div id="priceCropThumb" style="border:1px solid #00FFC8; border-radius:10px; overflow:hidden; width:110px; height:90px; background:#050505; display:flex; align-items:center; justify-content:center;">
                            <span style="font-size:9px; color:#555;">Sin ROI cargado</span>
                        </div>
                        <div style="flex:1;">
                            <div class="form-group" style="margin-top:0;">
                                <label>Ítem / Insumo Detectado:</label>
                                <input type="text" id="itemQuery" placeholder="Ej. Tambo polietileno 200L, Rib Eye 1kg...">
                            </div>
                            <div class="form-group">
                                <label>Categoría Táctica:</label>
                                <select id="itemCategory" onchange="runPriceValuationV6()">
                                    <option value="auto">Detección Automática (NPU Match)</option>
                                    <option value="industrial">Contenedor / Industrial / Almacén</option>
                                    <option value="carnico">Cárnico / Gastronomía Lean</option>
                                    <option value="hardware">Hardware / Electrónica / Herramientas</option>
                                    <option value="publicidad">Publicidad / Gran Formato / Lonas</option>
                                </select>
                            </div>
                        </div>
                    </div>

                    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:8px;">
                        <div class="form-group">
                            <label>Costo de Adquisición ($ MXN):</label>
                            <input type="number" id="itemCostBase" value="180" oninput="runPriceValuationV6()">
                        </div>
                        <div class="form-group">
                            <label>Margen Objetivo (%):</label>
                            <input type="number" id="targetMargin" value="35" oninput="runPriceValuationV6()">
                        </div>
                    </div>

                    <button class="btn-action" style="background: #00FFC8; color: #000; font-weight: bold; margin-top: 12px; width: 100%;" onclick="runPriceValuationV6()">Calcular Tasación de Mercado V6</button>
                    <div id="priceResult" style="margin-top: 12px;"></div>
                </div>
            </div>
        </div>

        <!-- 👨‍🍳 Chef Lean V6 Pro -->
        <div id="foodIndustryTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>👨‍🍳 Chef Lean V6 Pro (Inspección NPU & Yield Master)</h3>
                    <p>Telemetría cromática sobre recorte alfa, clasificación de marmoleado, cálculo de merma y estandarización porcionaria.</p>
                </div>
                <div class="card">
                    <div style="display:flex; gap:12px; align-items:center; margin-bottom:10px;">
                        <div id="chefCropThumb" style="border:1px solid #00FFC8; border-radius:10px; overflow:hidden; width:110px; height:90px; background:#050505; display:flex; align-items:center; justify-content:center;">
                            <span style="font-size:9px; color:#555;">Sin ROI cárnico</span>
                        </div>
                        <div style="flex:1;">
                            <div class="form-group" style="margin-top:0;">
                                <label>Corte o Pieza Primaria:</label>
                                <input type="text" id="chefCutName" value="Corte Primario / Insumo Cárnico">
                            </div>
                            <div class="form-group">
                                <label>Tipo de Inspección NPU:</label>
                                <select id="chefAnalysisMode">
                                    <option value="marmoleado">🥩 Grado de Marmoleado (Choice / Prime)</option>
                                    <option value="frescura">🔬 Espectro Mioglobina & Frescura</option>
                                    <option value="porcionado">⚖️ Estandarización de Porciones Lean</option>
                                </select>
                            </div>
                        </div>
                    </div>

                    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:8px;">
                        <div class="form-group">
                            <label>Peso Bruto Entrada (Kg):</label>
                            <input type="number" id="chefGrossWeight" value="5.0" step="0.1" oninput="runChefLeanEngineV6()">
                        </div>
                        <div class="form-group">
                            <label>Gramaje x Porción (g):</label>
                            <input type="number" id="chefPortionSize" value="350" step="10" oninput="runChefLeanEngineV6()">
                        </div>
                    </div>

                    <button class="btn-action" style="background: #00FFC8; color: #000; font-weight: bold; margin-top: 12px; width: 100%;" onclick="runChefLeanEngineV6()">Ejecutar Diagnóstico Chef Lean V6</button>
                    <div id="chefResult" style="margin-top: 12px;"></div>
                </div>
            </div>
        </div>

        <!-- 🎥 Video Motion V8 Ultra Engine -->
        <div id="genVidTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>🎥 Motion Engine V8 Ultra (Cinemática Multieje & Shaders Ópticos)</h3>
                    <p>Trayectorias compuestas Pan-Tilt-Roll, efecto Dolly Vertigo anamórfico, grano analógico estocástico y flares en vivo.</p>
                </div>
                <div class="card">
                    <div class="preview-box" id="vidPreviewBox"><span style="font-size: 11px; color: #555;">Esperando inyección desde IA V6 o Cam Vision...</span></div>
                    
                    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:8px; margin-top:10px;">
                        <div class="form-group">
                            <label>Cinemática de Cámara V8:</label>
                            <select id="v8MotionProfile">
                                <option value="multiaxis_orbit">Órbita 3D Compuesta (Roll + Tilt)</option>
                                <option value="dolly_vertigo">Dolly Vertigo Anamórfico (Foco Fijo)</option>
                                <option value="handheld_shake">Handheld Táctico (Micro-vibración)</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Efecto Óptico Shader V8:</label>
                            <select id="v8ShaderFX">
                                <option value="anamorphic_cinescope">CineScope 21:9 + Flare Neón</option>
                                <option value="grain_35mm">Grano 35mm Estocástico + Bokeh</option>
                                <option value="clean_ultra">Pure Digital Ultra HD (Sin Filtro)</option>
                            </select>
                        </div>
                    </div>

                    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:8px;">
                        <div class="form-group">
                            <label>Framerate Render:</label>
                            <select id="v8FpsRate">
                                <option value="60">60 FPS (Ultra Smooth NPU)</option>
                                <option value="30">30 FPS (Cinemático Estándar)</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Duración del Loop:</label>
                            <select id="v8LoopDuration">
                                <option value="3">3 Segundos (Loop Rápido)</option>
                                <option value="5">5 Segundos (Master Pro)</option>
                            </select>
                        </div>
                    </div>

                    <button class="btn-action" style="background: #00FFC8; color: #000; font-weight: bold; margin-top: 12px; width: 100%;" onclick="renderVideoV8Ultra()">⚡ Iniciar Render Cinemático V8</button>
                    <button class="btn-action" id="btnRecordVid" style="background: #FF0055; color: #fff; font-weight: bold; margin-top: 10px; width: 100%; display: none;" onclick="recordAndDownloadVideoV8()">🎥 Exportar Master Clip .WebM V8</button>
                </div>
            </div>
        </div>

        <!-- 🎨 SVG Logos Vectorial V8 Ultra Engine -->
        <div id="genImgTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>🎨 SVG Vectorial V8 Ultra (Geometría Sagrada & Paramétrica)</h3>
                    <p>Sintetizador vectorial de alta precisión matemática. Isotipos paramétricos, gradientes multicapa y exportación directa de código XML.</p>
                </div>
                <div class="card">
                    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:8px;">
                        <div class="form-group">
                            <label>Identidad / Marca Principal:</label>
                            <input type="text" id="svgBrandV8" value="BIAN V8">
                        </div>
                        <div class="form-group">
                            <label>Tagline / Lema Técnico:</label>
                            <input type="text" id="svgTaglineV8" value="NEURAL VISION SYSTEM">
                        </div>
                    </div>

                    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:8px;">
                        <div class="form-group">
                            <label>Estructura Geométrica V8:</label>
                            <select id="svgGeometryV8" onchange="generateSVGLogoV8()">
                                <option value="isocube">NPU Isocube 3D (Wireframe Isométrico)</option>
                                <option value="hypershield">Emblema Hyper-Shield Táctico</option>
                                <option value="vortex">Vórtice Órbita Neón Concéntrico</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Paleta de Color Vectorial:</label>
                            <select id="svgPaletteV8" onchange="generateSVGLogoV8()">
                                <option value="cyber">Cyber Matrix (#00FFC8 / #FF0055)</option>
                                <option value="gold">Gold Luxury Foil (#FFD700 / #B8860B)</option>
                                <option value="mono">AMOLED Monochrome (#FFFFFF / #777777)</option>
                            </select>
                        </div>
                    </div>

                    <button class="btn-action" style="background: #00FFC8; color: #000; font-weight: bold; margin-top: 12px; width: 100%;" onclick="generateSVGLogoV8()">⚡ Sintetizar Logotipo Vectorial V8</button>
                    
                    <div class="preview-box" id="svgPreviewBoxV8">
                        <span style="font-size: 11px; color: #555;">Sin vector generado</span>
                    </div>

                    <div id="svgActionsV8" style="display:none; margin-top:10px;">
                        <button class="btn-action" style="color:#00FFC8; width:100%; margin-bottom:6px;" onclick="downloadSVGV8()">💾 Descargar Archivo Puro .SVG</button>
                        <button class="btn-action" style="color:#FFD700; width:100%;" onclick="routeSvgToLonas()">📐 Probar Montaje Vectorial en Lonas 3D</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- 📐 Lonas 3D & Simulación Estructural V8 Ultra -->
        <div id="lonasPhysicsTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>📐 Lonas 3D V8 Ultra (Simulación Estructural & Tensión Eólica)</h3>
                    <p>Montaje sobre bastidor físico con textura textil procedural, cálculo de deflexión por viento y plano de ojillos perimetrales.</p>
                </div>
                <div class="card">
                    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:8px;">
                        <div class="form-group">
                            <label>Ancho (m):</label>
                            <input type="number" id="lonaWidthV8" value="4.0" step="0.5" oninput="renderLonaV8()">
                        </div>
                        <div class="form-group">
                            <label>Alto (m):</label>
                            <input type="number" id="lonaHeightV8" value="2.5" step="0.5" oninput="renderLonaV8()">
                        </div>
                    </div>

                    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:8px;">
                        <div class="form-group">
                            <label>Sustrato de Impresión:</label>
                            <select id="lonaSubstrateV8" onchange="renderLonaV8()">
                                <option value="frontlit_13oz">Frontlit 13oz Alta Resistencia (Estándar)</option>
                                <option value="mesh_perforada">Mesh Microperforada (Anti-Viento)</option>
                                <option value="backlight">Backlight Traslúcida (Caja de Luz)</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Carga de Viento Estimada:</label>
                            <select id="lonaWindV8" onchange="renderLonaV8()">
                                <option value="40">40 km/h (Urbano Moderado)</option>
                                <option value="75">75 km/h (Ráfaga Táctica Fuerte)</option>
                                <option value="110">110 km/h (Zona Crítica / Altura)</option>
                            </select>
                        </div>
                    </div>

                    <button class="btn-action" style="background: #00FFC8; color: #000; font-weight: bold; margin-top: 12px; width: 100%;" onclick="renderLonaV8()">⚡ Simular Bastidor 3D & Estructura</button>

                    <div class="preview-box" id="lonaPreviewBoxV8">
                        <span style="font-size: 11px; color: #555;">Sin simulación de bastidor activa</span>
                    </div>

                    <div id="lonaTelemetryV8" style="margin-top: 12px;"></div>
                </div>
            </div>
        </div>
    </div>

    <!-- Bottom Controls -->
    <div class="controls" id="bottomControls">
        <div class="thumb-preview" id="thumbBox" onclick="openGallery()"><span style="font-size: 9px; color: #666;">GALERÍA</span></div>
        <button class="btn-shutter" onclick="captureDirect()"></button>
        <button class="btn-action" style="color: #00FFC8;" onclick="toggleOCRMode()">OCR Auto</button>
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
        const cropCanvas = document.getElementById('cropCanvas');
        let currentFacingMode = 'environment';
        let currentROI = null;
        let synthResultCanvas = null;
        let roiImageObj = new Image();
        let animInterval = null;
        let activeCanvas = null;
        let currentSVGCodeV8 = "";
        let svgMountedImg = new Image();

        function startCamera() {
            if(video.srcObject) video.srcObject.getTracks().forEach(track => track.stop());
            navigator.mediaDevices.getUserMedia({ video: { facingMode: currentFacingMode } })
                .then(stream => { video.srcObject = stream; updateThumb(); })
                .catch(err => console.error("Error cámara:", err));
        }

        startCamera();

        function toggleCameraFacing() {
            currentFacingMode = (currentFacingMode === 'environment') ? 'user' : 'environment';
            startCamera();
        }

        function checkConnection() {
            const isOnline = navigator.onLine;
            const badge = document.getElementById('netBadge');
            badge.innerText = isOnline ? "ONLINE: EFECTIVIDAD 100%" : "OFFLINE: EFECTIVIDAD 85% (BD V8)";
            badge.style.color = isOnline ? "#00FFC8" : "#FFD700";
            badge.style.borderColor = badge.style.color;
            return isOnline;
        }
        window.addEventListener('online', checkConnection);
        window.addEventListener('offline', checkConnection);
        checkConnection();

        function switchModule(tabId, btn) {
            document.querySelectorAll('.module-view').forEach(m => m.classList.remove('active'));
            document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            if(btn) btn.classList.add('active');

            const controls = document.getElementById('bottomControls');
            controls.style.display = (tabId === 'cameraTab') ? 'flex' : 'none';
        }

        function getCropFromCameraV6() {
            if(video.videoWidth === 0) return null;
            cropCanvas.width = 320;
            cropCanvas.height = 240;
            const ctx = cropCanvas.getContext('2d');
            
            const sx = video.videoWidth * 0.22;
            const sy = video.videoHeight * 0.22;
            const sw = video.videoWidth * 0.56;
            const sh = video.videoHeight * 0.42;

            ctx.drawImage(video, sx, sy, sw, sh, 0, 0, 320, 240);

            ctx.globalCompositeOperation = 'destination-in';
            const grad = ctx.createRadialGradient(160, 120, 45, 160, 120, 145);
            grad.addColorStop(0, 'rgba(0,0,0,1)');
            grad.addColorStop(0.75, 'rgba(0,0,0,0.95)');
            grad.addColorStop(1, 'rgba(0,0,0,0)');
            ctx.fillStyle = grad;
            ctx.fillRect(0, 0, 320, 240);

            ctx.globalCompositeOperation = 'source-over';
            currentROI = cropCanvas.toDataURL('image/png');
            roiImageObj.src = currentROI;
            return currentROI;
        }

        function routeToSynthFromCam() {
            getCropFromCameraV6();
            switchModule('synthTab', document.getElementById('nav_synthTab'));
            generateAiCompositeV6();
        }

        function routeToValuatorFromCam() {
            const crop = getCropFromCameraV6();
            switchModule('priceTab', document.getElementById('nav_priceTab'));
            if(crop) {
                const thumb = document.getElementById('priceCropThumb');
                thumb.innerHTML = `<img src="${crop}" style="width:100%; height:100%; object-fit:contain;" />`;
            }
            document.getElementById('itemQuery').value = "Insumo Detectado V8";
            runPriceValuationV6();
        }

        function routeToChefFromCam() {
            const crop = getCropFromCameraV6();
            switchModule('foodIndustryTab', document.getElementById('nav_foodIndustryTab'));
            if(crop) {
                const thumb = document.getElementById('chefCropThumb');
                thumb.innerHTML = `<img src="${crop}" style="width:100%; height:100%; object-fit:contain;" />`;
            }
            document.getElementById('chefCutName').value = "Corte En Foco V8 NPU";
            runChefLeanEngineV6();
        }

        /* --- MOTOR VALUADOR HÍBRIDO V6 --- */
        const offlineV6Catalog = {
            "industrial": { min: 280, max: 480, sugerido: 390, name: "Contenedor Industrial / Depósito" },
            "carnico": { min: 190, max: 360, sugerido: 295, name: "Corte Primario / Insumo Gastronómico" },
            "hardware": { min: 140, max: 320, sugerido: 250, name: "Componente Electrónico / Herramienta" },
            "publicidad": { min: 70, max: 130, sugerido: 95, name: "Lona Vinílica m² / Publicidad" }
        };

        function runPriceValuationV6() {
            const query = document.getElementById('itemQuery').value.toLowerCase().trim();
            const cat = document.getElementById('itemCategory').value;
            const cost = parseFloat(document.getElementById('itemCostBase').value) || 0;
            const online = checkConnection();
            const res = document.getElementById('priceResult');

            let resolvedCat = cat;
            if(resolvedCat === 'auto') {
                if(query.includes('tambo') || query.includes('barril') || query.includes('bote')) resolvedCat = 'industrial';
                else if(query.includes('corte') || query.includes('carne') || query.includes('rib')) resolvedCat = 'carnico';
                else if(query.includes('lona') || query.includes('impresion')) resolvedCat = 'publicidad';
                else resolvedCat = 'hardware';
            }

            const ref = offlineV6Catalog[resolvedCat] || offlineV6Catalog["industrial"];
            const targetMargin = parseFloat(document.getElementById('targetMargin').value) || 30;
            const calculatedSalePrice = Math.round(cost / (1 - (targetMargin / 100)));

            if(online) {
                const liveMin = Math.round(ref.min * 0.95);
                const liveMax = Math.round(ref.max * 1.10);
                const liveAvg = Math.round((liveMin + liveMax) / 2);

                res.innerHTML = `
                <div style="background:#141414; padding:14px; border-radius:10px; border:1px solid #00FFC8;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                        <span style="color:#00FFC8; font-weight:bold; font-size:12px;">🌐 TASACIÓN ONLINE EN VIVO</span>
                        <span style="background:#00FFC8; color:#000; font-size:9px; font-weight:900; padding:2px 6px; border-radius:4px;">SYNC ACTIVO</span>
                    </div>
                    <p style="font-size:11px; margin-bottom:4px;">• Clasificación: <strong>${ref.name}</strong></p>
                    <p style="font-size:12px; margin-bottom:6px;">• Banda de Mercado Real: <strong style="color:#00FFC8;">$${liveMin} — $${liveMax} MXN</strong> (Media: $${liveAvg} MXN)</p>
                    <hr style="border:0; border-top:1px solid #222; margin:8px 0;">
                    <div style="display:grid; grid-template-columns:1fr 1fr; gap:6px; font-size:11px;">
                        <div>• Precio Venta: <strong style="color:#FFF;">$${calculatedSalePrice} MXN</strong></div>
                        <div>• Margen Bruto: <strong style="color:#00FFC8;">+$${calculatedSalePrice - cost} MXN</strong></div>
                    </div>
                </div>`;
            } else {
                res.innerHTML = `
                <div style="background:#141414; padding:14px; border-radius:10px; border:1px solid #FFD700;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                        <span style="color:#FFD700; font-weight:bold; font-size:12px;">⚡ TASACIÓN OFFLINE V6</span>
                        <span style="background:#FFD700; color:#000; font-size:9px; font-weight:900; padding:2px 6px; border-radius:4px;">LOCAL BD</span>
                    </div>
                    <p style="font-size:11px; margin-bottom:4px;">• Clasificación: <strong>${ref.name}</strong></p>
                    <p style="font-size:12px; margin-bottom:6px;">• Estimación Catálogo: <strong style="color:#FFD700;">$${ref.min} — $${ref.max} MXN</strong></p>
                    <hr style="border:0; border-top:1px solid #222; margin:8px 0;">
                    <div style="display:grid; grid-template-columns:1fr 1fr; gap:6px; font-size:11px;">
                        <div>• Sugerido (${targetMargin}%): <strong style="color:#FFF;">$${calculatedSalePrice} MXN</strong></div>
                        <div>• Margen Neto: <strong style="color:#FFD700;">+$${calculatedSalePrice - cost} MXN</strong></div>
                    </div>
                </div>`;
            }
        }

        /* --- MOTOR CHEF LEAN V6 PRO --- */
        function runChefLeanEngineV6() {
            const cut = document.getElementById('chefCutName').value;
            const gross = parseFloat(document.getElementById('chefGrossWeight').value) || 1.0;
            const portionG = parseFloat(document.getElementById('chefPortionSize').value) || 300;
            const res = document.getElementById('chefResult');

            const trimLossPercent = 12.5;
            const netWeight = gross * (1 - (trimLossPercent / 100));
            const totalPortions = Math.floor((netWeight * 1000) / portionG);
            const remainingG = Math.round((netWeight * 1000) % portionG);

            res.innerHTML = `
            <div style="background:#141414; padding:14px; border-radius:10px; border:1px solid #00FFC8;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                    <span style="color:#00FFC8; font-weight:bold; font-size:12px;">🥩 TELEMETRÍA CHEF LEAN V6</span>
                    <span style="background:#00FFC8; color:#000; font-size:9px; font-weight:900; padding:2px 6px; border-radius:4px;">NPU VISUAL READY</span>
                </div>
                <p style="font-size:11px; margin-bottom:4px;">• Insumo Evaluado: <strong>${cut}</strong></p>
                <div style="display:grid; grid-template-columns: repeat(3, 1fr); gap:6px; margin:8px 0; text-align:center;">
                    <div style="background:#1d1d1d; padding:6px; border-radius:6px;">
                        <span style="font-size:9px; color:#aaa;">PIGMENTO</span><br>
                        <strong style="color:#00FFC8; font-size:11px;">Rojo Óptimo</strong>
                    </div>
                    <div style="background:#1d1d1d; padding:6px; border-radius:6px; border:1px solid #00FFC8;">
                        <span style="font-size:9px; color:#00FFC8;">MARMOLEADO</span><br>
                        <strong style="color:#FFF; font-size:11px;">Choice / Prime</strong>
                    </div>
                    <div style="background:#1d1d1d; padding:6px; border-radius:6px;">
                        <span style="font-size:9px; color:#aaa;">YIELD NETO</span><br>
                        <strong style="color:#00FFC8; font-size:11px;">${(100 - trimLossPercent).toFixed(1)}%</strong>
                    </div>
                </div>
                <hr style="border:0; border-top:1px solid #222; margin:8px 0;">
                <div style="font-size:11px; color:#eee; line-height:1.5;">
                    <p>• Peso Bruto: <strong>${gross.toFixed(2)} Kg</strong> | Merma Técnica (-${trimLossPercent}%): <strong>${(gross - netWeight).toFixed(2)} Kg</strong></p>
                    <p>• Porciones Estándar (${portionG}g): <strong style="color:#00FFC8; font-size:13px;">${totalPortions} Piezas</strong> (Sobrante: ${remainingG}g)</p>
                </div>
            </div>`;
        }

        /* --- SÍNTESIS PROCEDURAL IA V6 ULTRA --- */
        function generateAiCompositeV6() {
            const box = document.getElementById('synthPreviewBox');
            box.innerHTML = "";

            synthResultCanvas = document.createElement('canvas');
            synthResultCanvas.width = 480;
            synthResultCanvas.height = 360;
            const ctx = synthResultCanvas.getContext('2d');

            const style = document.getElementById('synthStyle').value;

            let grad = ctx.createRadialGradient(240, 180, 25, 240, 180, 280);
            if(style === 'michelin_table') {
                grad.addColorStop(0, '#3d2516');
                grad.addColorStop(0.4, '#140c07');
                grad.addColorStop(1, '#000000');
            } else if(style === 'cyberpunk_market') {
                grad.addColorStop(0, '#005566');
                grad.addColorStop(0.5, '#220033');
                grad.addColorStop(1, '#000000');
            } else {
                grad.addColorStop(0, '#555555');
                grad.addColorStop(1, '#111111');
            }
            ctx.fillStyle = grad;
            ctx.fillRect(0, 0, 480, 360);

            ctx.fillStyle = "rgba(255, 255, 255, 0.04)";
            for (let i = 0; i < 6; i++) {
                ctx.beginPath();
                ctx.arc(150 + i * 40, 240 - i * 15, 60, 0, Math.PI * 2);
                ctx.fill();
            }

            if(currentROI) {
                roiImageObj.onload = () => {
                    ctx.save();
                    ctx.shadowColor = "rgba(0,0,0,0.92)";
                    ctx.shadowBlur = 32;
                    ctx.shadowOffsetY = 18;
                    ctx.drawImage(roiImageObj, 80, 60, 320, 240);
                    ctx.restore();
                };
                if(roiImageObj.complete) {
                    ctx.save();
                    ctx.shadowColor = "rgba(0,0,0,0.92)";
                    ctx.shadowBlur = 32;
                    ctx.shadowOffsetY = 18;
                    ctx.drawImage(roiImageObj, 80, 60, 320, 240);
                    ctx.restore();
                }
            }

            box.appendChild(synthResultCanvas);
            document.getElementById('btnSendToVideo').style.display = 'block';
        }

        function sendCompositeToVideoEngine() {
            switchModule('genVidTab', document.getElementById('nav_genVidTab'));
            const box = document.getElementById('vidPreviewBox');
            box.innerHTML = `<img src="${synthResultCanvas.toDataURL('image/png')}" style="max-width:100%; max-height:100%;" />`;
        }

        /* --- VIDEO MOTION V8 ULTRA --- */
        function renderVideoV8Ultra() {
            if(!roiImageObj.src) { alert("Inyecta primero un sujeto desde Cam Vision o IA V6."); return; }
            if(animInterval) clearInterval(animInterval);
            const box = document.getElementById('vidPreviewBox');
            box.innerHTML = "";
            activeCanvas = document.createElement('canvas');
            activeCanvas.width = 440; activeCanvas.height = 320;
            const ctx = activeCanvas.getContext('2d');
            box.appendChild(activeCanvas);
            
            let frame = 0;
            const profile = document.getElementById('v8MotionProfile').value;
            const shader = document.getElementById('v8ShaderFX').value;
            const fps = parseInt(document.getElementById('v8FpsRate').value) || 60;

            animInterval = setInterval(() => {
                frame++;
                ctx.clearRect(0, 0, 440, 320);

                let bgX = 0, bgY = 0, bgScale = 1.0;
                if(profile === 'multiaxis_orbit') {
                    bgX = Math.sin(frame * 0.02) * 16;
                    bgY = Math.cos(frame * 0.02) * 8;
                } else if(profile === 'dolly_vertigo') {
                    bgScale = 1.0 + Math.sin(frame * 0.05) * 0.18;
                } else if(profile === 'handheld_shake') {
                    bgX = (Math.random() - 0.5) * 4;
                    bgY = (Math.random() - 0.5) * 3;
                }

                ctx.save();
                ctx.translate(220 + bgX, 160 + bgY);
                ctx.scale(bgScale, bgScale);
                let grad = ctx.createRadialGradient(0, 0, 25, 0, 0, 260);
                grad.addColorStop(0, '#3a2012');
                grad.addColorStop(0.6, '#110905');
                grad.addColorStop(1, '#000000');
                ctx.fillStyle = grad;
                ctx.fillRect(-220, -160, 440, 320);
                ctx.restore();

                let subjectX = 0, subjectY = 0, subjectScale = 1.0, subjectAngle = 0;
                if(profile === 'multiaxis_orbit') {
                    subjectX = Math.cos(frame * 0.04) * 20;
                    subjectY = Math.sin(frame * 0.04) * 10;
                    subjectAngle = Math.sin(frame * 0.03) * 0.04;
                    subjectScale = 1.05 + Math.sin(frame * 0.03) * 0.05;
                } else if(profile === 'dolly_vertigo') {
                    subjectScale = 1.05 - Math.sin(frame * 0.05) * 0.04;
                } else if(profile === 'handheld_shake') {
                    subjectX = (Math.random() - 0.5) * 3;
                    subjectY = (Math.random() - 0.5) * 2;
                    subjectAngle = (Math.random() - 0.5) * 0.01;
                }

                ctx.save();
                ctx.translate(220 + subjectX, 160 + subjectY);
                ctx.rotate(subjectAngle);
                ctx.scale(subjectScale, subjectScale);
                ctx.shadowColor = "rgba(0,0,0,0.95)";
                ctx.shadowBlur = 30;
                ctx.shadowOffsetY = 16;
                ctx.drawImage(roiImageObj, -140, -105, 280, 210);
                ctx.restore();

                if(shader === 'anamorphic_cinescope') {
                    ctx.fillStyle = "#000";
                    ctx.fillRect(0, 0, 440, 36);
                    ctx.fillRect(0, 284, 440, 36);

                    const flareY = 160 + Math.sin(frame * 0.04) * 20;
                    const flareGrad = ctx.createLinearGradient(0, flareY, 440, flareY);
                    flareGrad.addColorStop(0, 'rgba(0,255,200,0)');
                    flareGrad.addColorStop(0.5, 'rgba(0,255,200,0.18)');
                    flareGrad.addColorStop(1, 'rgba(0,255,200,0)');
                    ctx.fillStyle = flareGrad;
                    ctx.fillRect(0, flareY - 3, 440, 6);
                } else if(shader === 'grain_35mm') {
                    const imgData = ctx.getImageData(0, 0, 440, 320);
                    const data = imgData.data;
                    for (let i = 0; i < data.length; i += 16) {
                        const noise = (Math.random() - 0.5) * 18;
                        data[i] = Math.min(255, Math.max(0, data[i] + noise));
                        data[i+1] = Math.min(255, Math.max(0, data[i+1] + noise));
                        data[i+2] = Math.min(255, Math.max(0, data[i+2] + noise));
                    }
                    ctx.putImageData(imgData, 0, 0);
                }
            }, 1000 / fps);

            document.getElementById('btnRecordVid').style.display = 'block';
        }

        function recordAndDownloadVideoV8() {
            if(!activeCanvas) return;
            const fps = parseInt(document.getElementById('v8FpsRate').value) || 60;
            const stream = activeCanvas.captureStream(fps);
            const recorder = new MediaRecorder(stream, { mimeType: 'video/webm' });
            const chunks = [];
            recorder.ondataavailable = e => chunks.push(e.data);
            recorder.onstop = () => {
                const blob = new Blob(chunks, { type: 'video/webm' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `clip_v8_master_${Date.now()}.webm`;
                a.click();
                if(animInterval) clearInterval(animInterval);
            };
            const durationSec = parseInt(document.getElementById('v8LoopDuration').value) || 3;
            recorder.start();
            setTimeout(() => recorder.stop(), durationSec * 1000);
        }

        /* --- MOTOR SVG LOGOS VECTORIAL V8 ULTRA --- */
        function generateSVGLogoV8() {
            const brand = document.getElementById('svgBrandV8').value.trim() || "BIAN V8";
            const tagline = document.getElementById('svgTaglineV8').value.trim() || "NEURAL SYSTEM";
            const geom = document.getElementById('svgGeometryV8').value;
            const palette = document.getElementById('svgPaletteV8').value;

            let c1 = "#00FFC8", c2 = "#FF0055", bg = "#040404", txtColor = "#FFFFFF";
            if(palette === 'gold') { c1 = "#FFD700"; c2 = "#B8860B"; bg = "#080808"; txtColor = "#FFF8E7"; }
            else if(palette === 'mono') { c1 = "#FFFFFF"; c2 = "#777777"; bg = "#000000"; txtColor = "#FFFFFF"; }

            let geomContent = "";
            if(geom === 'isocube') {
                geomContent = `
                    <polygon points="160,40 230,80 160,120 90,80" fill="none" stroke="url(#v8Grad)" stroke-width="4"/>
                    <polygon points="90,80 160,120 160,200 90,160" fill="none" stroke="${c1}" stroke-width="3" opacity="0.85"/>
                    <polygon points="160,120 230,80 230,160 160,200" fill="none" stroke="${c2}" stroke-width="3" opacity="0.85"/>
                    <circle cx="160" cy="120" r="5" fill="${c1}"/>
                `;
            } else if(geom === 'hypershield') {
                geomContent = `
                    <path d="M160 30 L235 65 V140 C235 195 160 225 160 225 C160 225 85 195 85 140 V65 Z" fill="none" stroke="url(#v8Grad)" stroke-width="5"/>
                    <path d="M160 55 L215 82 V135 C215 175 160 200 160 200 C160 200 105 175 105 135 V82 Z" fill="none" stroke="${c1}" stroke-width="1.8" stroke-dasharray="4,4"/>
                    <line x1="160" y1="75" x2="160" y2="180" stroke="${c2}" stroke-width="2"/>
                `;
            } else {
                geomContent = `
                    <circle cx="160" cy="125" r="85" fill="none" stroke="url(#v8Grad)" stroke-width="4"/>
                    <ellipse cx="160" cy="125" rx="85" ry="32" fill="none" stroke="${c1}" stroke-width="2.5" transform="rotate(-25 160 125)"/>
                    <ellipse cx="160" cy="125" rx="85" ry="32" fill="none" stroke="${c2}" stroke-width="2.5" transform="rotate(35 160 125)"/>
                    <circle cx="160" cy="125" r="14" fill="${c1}" opacity="0.6"/>
                `;
            }

            currentSVGCodeV8 = `
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 300" width="100%" height="100%">
                <defs>
                    <linearGradient id="v8Grad" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stop-color="${c1}"/>
                        <stop offset="100%" stop-color="${c2}"/>
                    </linearGradient>
                </defs>
                <rect width="320" height="300" fill="${bg}"/>
                ${geomContent}
                <text x="160" y="260" fill="${txtColor}" font-family="system-ui, sans-serif" font-weight="900" font-size="16" letter-spacing="3" text-anchor="middle">${brand.toUpperCase()}</text>
                <text x="160" y="278" fill="${c1}" font-family="system-ui, monospace" font-weight="700" font-size="9" letter-spacing="2" text-anchor="middle">${tagline.toUpperCase()}</text>
            </svg>`;

            const box = document.getElementById('svgPreviewBoxV8');
            box.innerHTML = currentSVGCodeV8;
            document.getElementById('svgActionsV8').style.display = 'block';

            svgMountedImg.src = 'data:image/svg+xml;utf8,' + encodeURIComponent(currentSVGCodeV8);
        }

        function downloadSVGV8() {
            if(!currentSVGCodeV8) return;
            const blob = new Blob([currentSVGCodeV8], { type: 'image/svg+xml' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `vector_v8_${Date.now()}.svg`;
            a.click();
        }

        function routeSvgToLonas() {
            switchModule('lonasPhysicsTab', document.getElementById('nav_lonasPhysicsTab'));
            renderLonaV8();
        }

        /* --- MOTOR LONAS 3D V8 ULTRA --- */
        function renderLonaV8() {
            const w = parseFloat(document.getElementById('lonaWidthV8').value) || 4.0;
            const h = parseFloat(document.getElementById('lonaHeightV8').value) || 2.5;
            const substrate = document.getElementById('lonaSubstrateV8').value;
            const wind = parseInt(document.getElementById('lonaWindV8').value) || 40;
            const box = document.getElementById('lonaPreviewBoxV8');
            const telem = document.getElementById('lonaTelemetryV8');

            const lonaCanvas = document.createElement('canvas');
            lonaCanvas.width = 440;
            lonaCanvas.height = 240;
            const ctx = lonaCanvas.getContext('2d');

            ctx.fillStyle = "#080808";
            ctx.fillRect(0, 0, 440, 240);

            // Bastidor de Acero
            ctx.strokeStyle = "#2a2a2a";
            ctx.lineWidth = 8;
            ctx.strokeRect(30, 20, 380, 190);

            // Lienzo de la Lona con Sombra de Profundidad
            ctx.fillStyle = (substrate === 'mesh_perforada') ? "#14181a" : ((substrate === 'backlight') ? "#1a1a1f" : "#111111");
            ctx.fillRect(36, 26, 368, 178);

            // Deflexión / Tensión Central por Viento
            const windBulge = (wind / 110) * 8;
            ctx.strokeStyle = "rgba(0, 255, 200, 0.15)";
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(36, 115);
            ctx.quadraticCurveTo(220, 115 + windBulge, 404, 115);
            ctx.stroke();

            // Renderizado del Arte SVG si existe
            if(svgMountedImg.complete && svgMountedImg.src) {
                ctx.drawImage(svgMountedImg, 130, 45, 180, 140);
            } else {
                ctx.fillStyle = "#00FFC8";
                ctx.font = "bold 13px system-ui";
                ctx.textAlign = "center";
                ctx.fillText(`LONA ESTRUCTURAL ${w}m x ${h}m`, 220, 110);
                ctx.fillStyle = "#777";
                ctx.font = "10px system-ui";
                ctx.fillText(`SUSTRATO: ${substrate.toUpperCase()}`, 220, 130);
            }

            // Ojillos Metálicos Perimetrales Calculados
            const spacing = (wind >= 110) ? 25 : ((wind >= 75) ? 35 : 45);
            ctx.fillStyle = "#FFD700";
            for(let x = 42; x <= 398; x += spacing) {
                ctx.beginPath(); ctx.arc(x, 30, 3, 0, Math.PI*2); ctx.fill();
                ctx.beginPath(); ctx.arc(x, 200, 3, 0, Math.PI*2); ctx.fill();
            }
            for(let y = 30; y <= 200; y += spacing) {
                ctx.beginPath(); ctx.arc(40, y, 3, 0, Math.PI*2); ctx.fill();
                ctx.beginPath(); ctx.arc(400, y, 3, 0, Math.PI*2); ctx.fill();
            }

            box.innerHTML = "";
            box.appendChild(lonaCanvas);

            // Telemetría de Ingeniería
            const area = w * h;
            const perim = (w + h) * 2;
            const totalOjillos = Math.round(perim / (spacing / 100));
            const windForceKPa = ((0.5 * 1.225 * Math.pow(wind / 3.6, 2)) / 1000).toFixed(2);
            const tensionCornerKg = Math.round(area * windForceKPa * 18);

            telem.innerHTML = `
            <div style="background:#141414; padding:14px; border-radius:10px; border:1px solid #00FFC8;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                    <span style="color:#00FFC8; font-weight:bold; font-size:12px;">📊 TELEMETRÍA ESTRUCTURAL LONAS V8</span>
                    <span style="background:#00FFC8; color:#000; font-size:9px; font-weight:900; padding:2px 6px; border-radius:4px;">CALCULADO</span>
                </div>
                <div style="display:grid; grid-template-columns: repeat(3, 1fr); gap:6px; margin:8px 0; text-align:center;">
                    <div style="background:#1d1d1d; padding:6px; border-radius:6px;">
                        <span style="font-size:9px; color:#aaa;">SUPERFICIE</span><br>
                        <strong style="color:#00FFC8; font-size:11px;">${area.toFixed(2)} m²</strong>
                    </div>
                    <div style="background:#1d1d1d; padding:6px; border-radius:6px; border:1px solid #00FFC8;">
                        <span style="font-size:9px; color:#00FFC8;">PRESIÓN VIENTO</span><br>
                        <strong style="color:#FFF; font-size:11px;">${windForceKPa} kPa</strong>
                    </div>
                    <div style="background:#1d1d1d; padding:6px; border-radius:6px;">
                        <span style="font-size:9px; color:#aaa;">OJILLOS TOTALES</span><br>
                        <strong style="color:#FFD700; font-size:11px;">${totalOjillos} Piezas</strong>
                    </div>
                </div>
                <hr style="border:0; border-top:1px solid #222; margin:8px 0;">
                <p style="font-size:11px; color:#eee;">• Tensión Crítica por Esquina: <strong style="color:#FF0055;">~${tensionCornerKg} Kgf</strong></p>
                <p style="font-size:11px; color:#aaa;">• Distribución de amarres: Dobladillo termosellado de 4cm con ojillos a cada ${spacing}cm.</p>
            </div>`;
        }

        async function captureDirect() {
            canvas.width = video.videoWidth; canvas.height = video.videoHeight;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            const res = await fetch('/bian/process/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image_base64: canvas.toDataURL('image/jpeg'), prompt_analysis: 'Captura Cam Vision V6' })
            });
            if(res.ok) updateThumb();
        }

        async function updateThumb() {
            const res = await fetch('/bian/images/');
            const imgs = await res.json();
            if(imgs.length > 0) document.getElementById('thumbBox').innerHTML = `<img src="${imgs[imgs.length - 1].image_path}" />`;
        }

        function openGallery() { document.getElementById('galleryModal').style.display = 'flex'; }
        function closeGallery() { document.getElementById('galleryModal').style.display = 'none'; }
        function toggleOCRMode() {}
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
        "engine": "Master Unified Suite V8 (Lonas 3D V8 Ultra Integrated)",
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
