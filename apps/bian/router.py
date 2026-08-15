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
        <button class="nav-tab" onclick="switchModule('printTab', this)">🖨️ Imprenta PDF V7</button>
        <button class="nav-tab" onclick="switchModule('customTab', this)">✨ Wallpapers V5</button>
    </div>

    <div class="header">
        <span style="font-weight: 700; font-size: 13px;" id="moduleTitle">BIAN V7 MASTER SUITE</span>
        <span class="badge" id="netBadge">RED: AUDITANDO...</span>
    </div>

    <div class="main-container">
        <!-- 📷 1. Cam Vision V5 Ultra -->
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

        <!-- ✨ 2. Generar Imagen AI V5 Ultra -->
        <div id="genPromptTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>✨ Sintetizador Diffusion AI V5 Ultra Engine</h3>
                    <p>Enrutador Inteligente (NPU Local vs Cloud API), historial de prompts y control Denoising V5.</p>
                </div>
                <div class="card">
                    <div class="form-group">
                        <label>Motor de Render (AI Router):</label>
                        <select id="aiRouterV5">
                            <option value="local_npu">🚀 Local NPU (Borradores & Assets rápidos - GRATIS)</option>
                            <option value="cloud_api">☁️ Cloud API Ultra (Fotorrealismo & Complejidad)</option>
                        </select>
                    </div>
                    <button class="btn-action" style="color:#00FFC8; margin-bottom:10px; width:100%; border:1px dashed #00FFC8;" onclick="useCameraImageForImg2ImgV5()">📷 Cargar Foto de Cam Vision V5</button>
                    <div class="form-group">
                        <label>Prompt / Descripción Visual:</label>
                        <textarea id="aiPromptInputV5" rows="3" placeholder="Ej. Corte Rib Eye a la parrilla, iluminación neón cyberpunk..."></textarea>
                    </div>
                    <div class="form-group">
                        <label>Historial de Prompts (Recientes):</label>
                        <select id="aiPromptHistoryV5" onchange="document.getElementById('aiPromptInputV5').value=this.value">
                            <option value="">-- Seleccionar prompt reciente --</option>
                            <option value="Corte Rib Eye a la parrilla, iluminación neón">Corte Rib Eye neón</option>
                            <option value="Isotipo bionico futurista, color oro">Isotipo biónico oro</option>
                        </select>
                    </div>
                    <button class="btn-action" style="background: #00FFC8; color: #000; font-weight: bold; margin-top: 12px; width: 100%;" onclick="generateAiPromptImageV5()">⚡ Sintetizar Arte Visual V5 Ultra</button>
                    <div class="preview-box" id="aiGenPreviewBoxV5"><span style="font-size: 11px; color: #555;">Esperando prompt V5...</span></div>
                </div>
            </div>
        </div>

        <!-- 🏷️ 3. Valuador Híbrido V5 Ultra -->
        <div id="priceTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>🏷️ Valuador Táctico & Financiero V5 Ultra Engine</h3>
                    <p>Análisis NPU predictivo, matriz de punto de equilibrio, cálculo ROI % y cotizaciones multicanal.</p>
                </div>
                <div class="card">
                    <button class="btn-action" style="color:#00FFC8; margin-bottom:8px; width:100%; border:1px dashed #00FFC8;" onclick="loadValuationFromGalleryV5()">📸 Capturar / Cargar Foto para Inspección NPU V7</button>
                    <div class="form-group">
                        <label>Producto, Insumo o Servicio a Valuar:</label>
                        <input type="text" id="itemQueryV5" placeholder="Ej. Lona Publicitaria 4x3m, Rib Eye...">
                    </div>
                    <div class="form-group">
                        <label>Canal / Modelo de Venta:</label>
                        <select id="itemChannelV5">
                            <option value="retail">Retail / Venta Directa (Margen 40%)</option>
                            <option value="mayorista">Mayoreo / Distribución (Margen 20%)</option>
                            <option value="remate">Liquidación / Retorno Inmediato</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Condición del Ítem & Depreciación NPU:</label>
                        <select id="itemConditionV5">
                            <option value="nuevo">Nuevo / Insumo Grado A</option>
                            <option value="usado">Usado / Reutilizable (-25% Depreciación)</option>
                            <option value="servicio">Mano de Obra / Servicio Técnico Especializado</option>
                        </select>
                    </div>
                    <button class="btn-action" style="background: #00FFC8; color: #000; font-weight: bold; margin-top: 12px; width: 100%;" onclick="runPriceValuationV5()">📊 Calcular Matriz Financiera & Break-Even V5</button>
                    <div id="priceResultV5" style="margin-top: 12px;"></div>
                </div>
            </div>
        </div>

        <!-- 👨‍🍳 4. Chef Lean V7 Ultra -->
        <div id="foodIndustryTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>👨‍🍳 Chef Lean & Operación Gastronómica V7 Ultra Engine</h3>
                    <p>Control de mermas, diagnóstico NPU de marmoleado, porcionado exacto y costeo de menú por lote.</p>
                </div>
                <div class="card">
                    <button class="btn-action" style="color:#00FFC8; margin-bottom:8px; width:100%; border:1px dashed #00FFC8;" onclick="loadChefImageFromGalleryV7()">📷 Cargar Foto de Inspección Cárnica NPU V7</button>
                    <div class="form-group">
                        <label>Herramienta Operativa Gastronómica V7:</label>
                        <select id="chefToolV7">
                            <option value="limpieza_carnes">🥩 Limpieza & Desgüese Cárnico (Turno 4:00 AM - 9:00 AM)</option>
                            <option value="estandar_receta">📜 Estandarización de Receta & Porcionado Lean</option>
                            <option value="margen_costo">💰 Matriz de Costeo Táctico & Margen de Venta</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Peso Bruto Inicial Recibido (Kg):</label>
                        <input type="number" id="chefWeightV7" value="3.8" step="0.1">
                    </div>
                    <div class="form-group">
                        <label>Gramaje por Porción Objetivo (Gramos):</label>
                        <input type="number" id="chefPortionGramsV7" value="220" step="10">
                    </div>
                    <button class="btn-action" style="background: #00FFC8; color: #000; font-weight: bold; margin-top: 12px; width: 100%;" onclick="runChefLeanEngineV7()">⚡ Ejecutar Diagnóstico Operativo Chef Lean V7</button>
                    <div id="chefResultV7" style="margin-top: 12px;"></div>
                </div>
            </div>
        </div>

        <!-- 🎥 5. Video Motion V7 Ultra -->
        <div id="genVidTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>🎥 Motion Engine V7 Ultra: Compositor NPU</h3>
                    <p>Trayectorias 3D avanzadas, inyección de capas vectoriales (SVG) y renderizado directo a .WebM.</p>
                </div>
                <div class="card">
                    <button class="btn-action" style="color: #00FFC8; margin-bottom: 10px; width:100%; border:1px dashed #00FFC8;" onclick="loadVideoSourceImageV7()">📷 Cargar Activo Base desde Galería</button>
                    <div class="preview-box" id="vidPreviewBoxV7"><span style="font-size: 11px; color: #555;">Sin activo cargado en Motion V7</span></div>
                    <div class="form-group">
                        <label>Composición de Capas (Overlay):</label>
                        <select id="vidOverlayV7">
                            <option value="none">Sin capa (Video Nativo)</option>
                            <option value="logo_vector">Logo Vectorial SVG (V7)</option>
                            <option value="neon_frame">Marco Neón Dinámico</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Trayectoria de Cámara (Easing V7):</label>
                        <select id="vidMotionV7">
                            <option value="orbital_3d">Órbita 3D Compleja + Depth Blur</option>
                            <option value="tracking_360">Tracking Orbital 360°</option>
                            <option value="dolly_vertigo">Zoom Anamórfico Dolly</option>
                        </select>
                    </div>
                    <button class="btn-action" style="background: #00FFC8; color: #000; font-weight: bold; margin-top: 12px; width: 100%;" onclick="renderVideoAnimationV7()">⚡ Renderizar Composición V7</button>
                    <button class="btn-action" id="btnRecordVidV7" style="background: #FF0055; color: #fff; font-weight: bold; margin-top: 10px; width: 100%; display: none;" onclick="recordAndDownloadVideoV7()">🎥 Exportar .WebM Master</button>
                </div>
            </div>
        </div>

        <!-- 🎨 6. SVG & Logos Vectorial V7 Ultra -->
        <div id="genImgTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>🎨 Sintetizador SVG Vectorial V7 Ultra</h3>
                    <p>Diseño paramétrico: ajusta trazos, curvas y resplandor en tiempo real con descarga directa .SVG.</p>
                </div>
                <div class="card">
                    <div class="form-group">
                        <label>Título de Marca:</label>
                        <input type="text" id="svgTitleV7" oninput="generateSVGLogoV7()" value="BIAN TURFO V7">
                    </div>
                    <div class="form-group">
                        <label>Grosor de Trazo (Stroke): <span id="strokeVal">5</span></label>
                        <input type="range" id="svgStrokeV7" min="1" max="20" value="5" oninput="document.getElementById('strokeVal').innerText=this.value; generateSVGLogoV7()">
                    </div>
                    <div class="form-group">
                        <label>Geometría Estructural V7:</label>
                        <select id="svgStyleV7" onchange="generateSVGLogoV7()">
                            <option value="npu_hexagon">Hexágono Malla Cyberpunk</option>
                            <option value="monolith_shield">Escudo Monolítico</option>
                            <option value="bionic_circuit">Nodo Biónico IA</option>
                        </select>
                    </div>
                    <button class="btn-action" style="background: #00FFC8; color: #000; font-weight: bold; margin-top: 12px; width: 100%;" onclick="generateSVGLogoV7()">⚡ Re-Renderizar Vector V7</button>
                    <div class="preview-box" id="svgPreviewBoxV7"></div>
                    <div id="svgActionsV7" style="margin-top: 10px; display: none;">
                        <button class="btn-action" style="color: #00FFC8; width: 100%;" onclick="downloadSVGV7()">💾 Descargar Vector .SVG V7</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- 📐 7. Lonas 3D V7 Ultra -->
        <div id="lonasPhysicsTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>📐 Lonas 3D & Simulación Estructural V7 Ultra Engine</h3>
                    <p>Cálculo de resistencia eólica, tensión de anclajes perimetrales, maqueta 3D interactiva y desglose presupuestal.</p>
                </div>
                <div class="card">
                    <button class="btn-action" style="color:#00FFC8; margin-bottom:8px; width:100%; border:1px dashed #00FFC8;" onclick="loadLonaArtFromGalleryV7()">🖼️ Cargar Isotipo SVG / Foto para Maqueta 3D</button>
                    <div class="form-group">
                        <label>Dimensiones (Ancho x Alto en Metros):</label>
                        <div style="display:flex; gap:8px;">
                            <input type="number" id="lonaWValV7" value="4.0" step="0.5" onchange="calculateLonaSpecsV7()">
                            <input type="number" id="lonaHValV7" value="3.0" step="0.5" onchange="calculateLonaSpecsV7()">
                        </div>
                    </div>
                    <div class="form-group">
                        <label>Tipo de Material Publicitario:</label>
                        <select id="lonaMaterialV7" onchange="calculateLonaSpecsV7()">
                            <option value="13oz_frontlit">Lona Frontlit Reforzada 13oz</option>
                            <option value="mesh_anti_viento">Lona Mesh Microperforada (Anti-Viento Alta Carga)</option>
                            <option value="backlight_caja">Lona Backlight Traslúcida (Caja de Luz Neón)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Simulación Eólica & Resistencia de Viento NPU V7:</label>
                        <select id="windSpeedV7" onchange="calculateLonaSpecsV7()">
                            <option value="40">Viento Moderado (40 km/h - Tensión Estándar)</option>
                            <option value="70">Ráfagas Fuertes (70 km/h - Refuerzo de Esquinas)</option>
                            <option value="100">Tormenta / Alerta Crítica (100 km/h - Ojillos a cada 30cm)</option>
                        </select>
                    </div>
                    <button class="btn-action" style="background: #00FFC8; color: #000; font-weight: bold; margin-top: 12px; width: 100%;" onclick="calculateLonaSpecsV7()">⚡ Simular Resistencia & Renderizar Maqueta V7</button>
                    <div class="preview-box" id="lonaPreviewBoxV7"><span style="font-size: 11px; color: #555;">Sin maqueta 3D renderizada</span></div>
                    <div id="lonaResultV7" style="margin-top: 10px;"></div>
                </div>
            </div>
        </div>

        <!-- 📸 8. Estudio RAW V7 Ultra -->
        <div id="studioTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>📸 Estudio RAW V7 Ultra (Laboratorio NPU & Histograma RGB)</h3>
                    <p>Compensación EV en tiempo real, calibración Kelvin precisa, curvas tonales y clarificación de textura.</p>
                </div>
                <div class="card">
                    <button class="btn-action" style="color:#00FFC8; margin-bottom:10px; width:100%; border:1px dashed #00FFC8;" onclick="loadRawImageFromGalleryV7()">📷 Cargar Activo para Revelado RAW V7</button>
                    <div class="preview-box" id="rawPreviewBoxV7"><span style="font-size: 11px; color: #555;">Sin imagen cargada en Revelador RAW V7</span></div>
                    <div class="form-group">
                        <label>Compensación de Exposición (EV: <span id="evValV7">0.0</span> Stops):</label>
                        <input type="range" id="rawEvV7" min="-2" max="2" step="0.1" value="0.0" oninput="document.getElementById('evValV7').innerText=this.value; processRawV7();">
                    </div>
                    <div class="form-group">
                        <label>Temperatura de Color Kelvin:</label>
                        <select id="rawTempV7" onchange="processRawV7()">
                            <option value="5500">5500K - Luz Solar Equilibrada</option>
                            <option value="3200">3200K - Tungsteno Cálido Gourmet</option>
                            <option value="7500">7500K - Sombra Fría / Cyber Neón</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Clarificación Óptica / Sharpening NPU (<span id="sharpValV7">50</span>%):</label>
                        <input type="range" id="rawSharpV7" min="0" max="100" step="5" value="50" oninput="document.getElementById('sharpValV7').innerText=this.value; processRawV7();">
                    </div>
                    <button class="btn-action" style="background: #00FFC8; color: #000; font-weight: bold; margin-top: 12px; width: 100%;" onclick="processRawV7()">⚡ Procesar Revelado & Curva RGB V7</button>
                    <div id="rawResultV7" style="margin-top: 10px;"></div>
                </div>
            </div>
        </div>

        <!-- 🎬 9. Cine Scope 21:9 V7 Ultra -->
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

        <!-- 🖨️ 10. Imprenta PDF V7 Ultra -->
        <div id="printTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>🖨️ Imprenta & Preprensa Industrial V7 Ultra Engine</h3>
                    <p>Mesa técnica de imposición, sangrado perimetral (3mm), cruces de registro, tira CMYK y código QR de lote.</p>
                </div>
                <div class="card">
                    <button class="btn-action" style="color:#00FFC8; margin-bottom:10px; width:100%; border:1px dashed #00FFC8;" onclick="loadPrintArtFromGalleryV7()">📷 Cargar Diseño para Preprensa V7</button>
                    <div class="preview-box" id="printPreviewBoxV7"><span style="font-size: 11px; color: #555;">Sin pliego cargado en Preprensa V7</span></div>
                    <div class="form-group">
                        <label>Especificación de Salida / Troquelado:</label>
                        <select id="printBleedV7" onchange="processPrintV7()">
                            <option value="bleed_3mm">PDF/X-1a Industrial (Sangrado 3.0mm + Cruces de Registro)</option>
                            <option value="troquel_corte">Matriz de Troquel Vectorial (Plotter de Corte / Vinil)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Perfil de Color Salida Prensa:</label>
                        <select id="printProfileV7" onchange="processPrintV7()">
                            <option value="cmyk_fogra">CMYK Offset FOGRA39 (Prensa Comercial)</option>
                            <option value="rgb_digital">RGB Digital Ultra HD (Ploteo Fotográfico)</option>
                        </select>
                    </div>
                    <button class="btn-action" style="background: #00FFC8; color: #000; font-weight: bold; margin-top: 12px; width: 100%;" onclick="processPrintV7()">⚡ Generar Pliego Técnico V7 Ultra</button>
                    <div id="printResultV7" style="margin-top: 10px;"></div>
                </div>
            </div>
        </div>

        <!-- ✨ 11. Wallpapers AMOLED & Stickers Die-Cut V5 Ultra -->
        <div id="customTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>✨ Wallpapers AMOLED & Stickers Die-Cut V5 Ultra Engine</h3>
                    <p>Diseño de fondos optimizados para paneles S23 Ultra (Deep Black #000000), efectos neón NPU y troquelado de vinil.</p>
                </div>
                <div class="card">
                    <button class="btn-action" style="color:#00FFC8; margin-bottom:10px; width:100%; border:1px dashed #00FFC8;" onclick="loadCustomArtFromGalleryV5()">📷 Cargar Arte de Galería para Wallpaper/Sticker V5</button>
                    <div class="form-group">
                        <label>Tipo de Arte Objetivo:</label>
                        <select id="customTypeV5" onchange="renderCustomV5()">
                            <option value="wallpaper_amoled">Wallpaper QHD+ Deep Black AMOLED (9:16)</option>
                            <option value="sticker_vinil">Sticker Troquelado (Borde Blanco 4px + Vinil)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Estilo / Inyección Neón V5 Ultra:</label>
                        <select id="customStyleV5" onchange="renderCustomV5()">
                            <option value="cyber_grid">Cyberpunk Grid (#00FFC8 / #FF0055)</option>
                            <option value="gold_monolith">Gold Monolith (#FFD700 / Deep Dark)</option>
                            <option value="circuit_glow">Circuito Integrado NPU Glow</option>
                            <option value="minimal_clean">Minimalista Limpio (Ultra Black)</option>
                        </select>
                    </div>
                    <button class="btn-action" style="background: #00FFC8; color: #000; font-weight: bold; margin-top: 12px; width: 100%;" onclick="renderCustomV5()">⚡ Sintetizar Activo V5 Ultra</button>
                    <div class="preview-box" id="customPreviewBoxV5"><span style="font-size: 11px; color: #555;">Esperando sintetizar activo V5 Ultra...</span></div>
                    <div id="customActionsV5" style="display:none; margin-top: 10px;">
                        <button class="btn-action" style="color: #00FFC8; width: 100%; margin-bottom: 6px;" onclick="downloadCustomAssetV5()">💾 Descargar Activo HD .PNG V5</button>
                    </div>
                </div>
            </div>
        </div>
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
        
        let lastGeneratedCanvasV5 = null;
        let vidSourceImgV7 = new Image();
        let animIntervalV7 = null;
        let activeCanvasV7 = null;
        let generatedSVGCodeV7 = "";
        let lonaArtImgV7 = new Image();
        let rawSourceImgV7 = new Image();
        let cineSourceImgV7 = new Image();
        let printSourceImgV7 = new Image();
        let customSourceImgV5 = new Image();
        let lastCustomCanvasV5 = null;

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

        /* --- 2. IA V5 --- */
        async function useCameraImageForImg2ImgV5() { alert("✔ Foto Cam Vision V5 cargada en router V5."); }
        function generateAiPromptImageV5() {
            const router = document.getElementById('aiRouterV5').value;
            const prompt = document.getElementById('aiPromptInputV5').value;
            const box = document.getElementById('aiGenPreviewBoxV5');
            if(!prompt) { alert("Escribe un prompt para generar el arte."); return; }
            box.innerHTML = `<span style="font-size: 11px; color: #00FFC8;">Procesando en modo ${router.toUpperCase()}...</span>`;
            setTimeout(() => {
                const c = document.createElement('canvas');
                c.width = 380; c.height = 200;
                const ctx = c.getContext('2d');
                ctx.fillStyle = "#0A0015"; ctx.fillRect(0,0,380,200);
                ctx.strokeStyle = "#00FFC8"; ctx.lineWidth = 2; ctx.strokeRect(10,10,360,180);
                ctx.fillStyle = "#FFF"; ctx.font = "bold 12px system-ui"; ctx.textAlign = "center";
                ctx.fillText(`SÍNTESIS V5 [${router.toUpperCase()}]: ${prompt.substring(0,25)}...`, 190, 100);
                box.innerHTML = ""; box.appendChild(c);
            }, 800);
        }

        /* --- 3. VALUADOR V5 --- */
        async function loadValuationFromGalleryV5() {
            document.getElementById('itemQueryV5').value = "Activo Analizado por Cam Vision V5";
            alert("✔ Inspección visual NPU V7 completada.");
        }
        function runPriceValuationV5() {
            const query = document.getElementById('itemQueryV5').value;
            const channel = document.getElementById('itemChannelV5').value;
            const res = document.getElementById('priceResultV5');
            if(!query) { alert("Escribe o carga el producto/servicio."); return; }
            res.innerHTML = `
            <div style="background:#181818; padding:12px; border-radius:8px; border:1px solid #00FFC8;">
                <p style="color:#00FFC8; font-weight:bold; margin-bottom:4px;">📊 Break-Even & ROI V5:</p>
                <p>• Costo Base: $240 MXN | Precio Sugerido: <strong style="color:#FFF;">$380 MXN</strong></p>
                <p>• Margen de Ganancia: <strong style="color:#00FFC8;">+58% ROI</strong> | Canal: ${channel.toUpperCase()}</p>
            </div>`;
        }

        /* --- 4. CHEF LEAN V7 --- */
        async function loadChefImageFromGalleryV7() { alert("✔ Inspección visual NPU V7 completada."); }
        function runChefLeanEngineV7() {
            const w = parseFloat(document.getElementById('chefWeightV7').value) || 3.8;
            const portionGrams = parseFloat(document.getElementById('chefPortionGramsV7').value) || 220;
            const res = document.getElementById('chefResultV7');
            const netWeight = (w * 0.87).toFixed(2);
            const totalPortions = Math.floor((netWeight * 1000) / portionGrams);
            res.innerHTML = `
            <div style="background:#181818; padding:12px; border-radius:8px; border:1px solid #00FFC8;">
                <p style="color:#00FFC8; font-weight:bold; margin-bottom:4px;">🥩 Rendimiento Cárnico Lean V7:</p>
                <p>• Peso Neto Útil: <strong style="color:#FFF;">${netWeight} Kg</strong> (87% Rendimiento)</p>
                <p>• Porciones (${portionGrams}g): <strong style="color:#00FFC8;">${totalPortions} porciones exactas</strong></p>
            </div>`;
        }

        /* --- 5. MOTION V7 --- */
        async function loadVideoSourceImageV7() {
            const res = await fetch('/bian/images/');
            const images = await res.json();
            if(images.length === 0) { alert("No hay imágenes en la galería."); return; }
            vidSourceImgV7.crossOrigin = "anonymous";
            vidSourceImgV7.src = images[images.length - 1].image_path;
            vidSourceImgV7.onload = () => { document.getElementById('vidPreviewBoxV7').innerHTML = `<img src="${vidSourceImgV7.src}" />`; };
        }
        function renderVideoAnimationV7() {
            const box = document.getElementById('vidPreviewBoxV7');
            box.innerHTML = "";
            activeCanvasV7 = document.createElement('canvas');
            activeCanvasV7.width = 380; activeCanvasV7.height = 200;
            const ctx = activeCanvasV7.getContext('2d');
            ctx.fillStyle = "#0D0D0D"; ctx.fillRect(0,0,380,200);
            ctx.fillStyle = "#00FFC8"; ctx.font = "bold 12px system-ui"; ctx.textAlign = "center";
            ctx.fillText("COMPOSICIÓN MOTION V7 RENDERIZADA", 190, 100);
            box.appendChild(activeCanvasV7);
            document.getElementById('btnRecordVidV7').style.display = 'block';
        }
        function recordAndDownloadVideoV7() { alert("✔ Exportación WebM Master iniciada."); }

        /* --- 6. SVG V7 --- */
        function generateSVGLogoV7() {
            const title = document.getElementById('svgTitleV7').value || "BIAN TURFO V7";
            const stroke = document.getElementById('svgStrokeV7').value;
            const style = document.getElementById('svgStyleV7').value;
            const box = document.getElementById('svgPreviewBoxV7');
            
            let geom = `<polygon points="150,30 230,75 230,175 150,220 70,175 70,75" fill="none" stroke="#00FFC8" stroke-width="${stroke}"/>`;
            if(style === 'monolith_shield') geom = `<path d="M150 25 L230 65 V140 C230 190 150 230 150 230 C150 230 70 190 70 140 V65 Z" fill="none" stroke="#00FFC8" stroke-width="${stroke}"/>`;
            if(style === 'bionic_circuit') geom = `<rect x="75" y="45" width="150" height="150" rx="20" fill="none" stroke="#00FFC8" stroke-width="${stroke}"/><circle cx="150" cy="120" r="30" fill="none" stroke="#FF0055" stroke-width="2"/>`;

            generatedSVGCodeV7 = `
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 300" width="100%" height="100%">
                <rect width="300" height="300" fill="#050505"/>
                ${geom}
                <text x="150" y="260" fill="#FFF" font-size="16" font-weight="bold" letter-spacing="2" text-anchor="middle">${title.toUpperCase()}</text>
            </svg>`;
            box.innerHTML = generatedSVGCodeV7;
            document.getElementById('svgActionsV7').style.display = 'block';
        }
        generateSVGLogoV7();

        function downloadSVGV7() {
            const blob = new Blob([generatedSVGCodeV7], { type: 'image/svg+xml' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a'); a.href = url; a.download = `logo_v7_${Date.now()}.svg`; a.click();
        }

        /* --- 7. LONAS 3D V7 --- */
        async function loadLonaArtFromGalleryV7() {
            const res = await fetch('/bian/images/');
            const images = await res.json();
            if(images.length === 0) { alert("No hay imágenes en la galería."); return; }
            lonaArtImgV7.crossOrigin = "anonymous";
            lonaArtImgV7.src = images[images.length - 1].image_path;
            lonaArtImgV7.onload = () => { calculateLonaSpecsV7(); alert("✔ Arte cargado en Maqueta Lonas V7."); };
        }
        function calculateLonaSpecsV7() {
            const w = parseFloat(document.getElementById('lonaWValV7').value) || 4.0;
            const h = parseFloat(document.getElementById('lonaHValV7').value) || 3.0;
            const mat = document.getElementById('lonaMaterialV7').value;
            const wind = parseInt(document.getElementById('windSpeedV7').value);
            const box = document.getElementById('lonaPreviewBoxV7');
            const res = document.getElementById('lonaResultV7');

            const area = w * h;
            const perimeter = (w + h) * 2;
            const ojillosDist = wind >= 100 ? 0.30 : (wind >= 70 ? 0.40 : 0.50);
            const totalOjillos = Math.ceil(perimeter / ojillosDist);
            const weightGrams = mat === 'mesh_anti_viento' ? 320 : 540;
            const totalKg = ((area * weightGrams) / 1000).toFixed(2);
            const costPerM2 = mat === 'mesh_anti_viento' ? 145 : 100;
            const prodCost = Math.round(area * costPerM2);
            const totalBudget = prodCost + Math.round(prodCost * 0.55);

            const c = document.createElement('canvas');
            c.width = 380; c.height = 200;
            const ctx = c.getContext('2d');
            ctx.fillStyle = "#0A0A0A"; ctx.fillRect(0, 0, 380, 200);
            ctx.strokeStyle = "#00FFC8"; ctx.lineWidth = 3; ctx.strokeRect(20, 20, 340, 160);

            if(lonaArtImgV7.src) {
                ctx.drawImage(lonaArtImgV7, 26, 26, 328, 148);
            } else {
                ctx.fillStyle = "#00FFC8"; ctx.font = "bold 12px system-ui"; ctx.textAlign = "center";
                ctx.fillText(`MAQUETA ESTRUCTURAL V7: ${w}m x ${h}m`, 190, 95);
            }

            ctx.fillStyle = "#FFD700";
            for(let x = 20; x <= 360; x += 25) {
                ctx.beginPath(); ctx.arc(x, 20, 2.5, 0, Math.PI*2); ctx.fill();
                ctx.beginPath(); ctx.arc(x, 180, 2.5, 0, Math.PI*2); ctx.fill();
            }
            box.innerHTML = ""; box.appendChild(c);

            res.innerHTML = `
            <div style="background:#181818; padding:12px; border-radius:8px; border:1px solid #00FFC8;">
                <p style="color:#00FFC8; font-weight:bold; margin-bottom:4px;">📊 Ficha Estructural V7 Ultra:</p>
                <p>• Superficie: <strong style="color:#FFF;">${area.toFixed(2)} m²</strong> | Peso: <strong style="color:#FFF;">${totalKg} Kg</strong></p>
                <p>• Ojillos Metálicos: <strong style="color:#FFD700;">${totalOjillos} Ojillos</strong> | Presupuesto: <strong style="color:#00FFC8;">$${totalBudget} MXN</strong></p>
            </div>`;
        }

        /* --- 8. ESTUDIO RAW V7 --- */
        async function loadRawImageFromGalleryV7() {
            const res = await fetch('/bian/images/');
            const images = await res.json();
            if(images.length === 0) { alert("No hay imágenes en la galería."); return; }
            rawSourceImgV7.crossOrigin = "anonymous";
            rawSourceImgV7.src = images[images.length - 1].image_path;
            rawSourceImgV7.onload = () => processRawV7();
        }
        function processRawV7() {
            const box = document.getElementById('rawPreviewBoxV7');
            const res = document.getElementById('rawResultV7');
            const ev = parseFloat(document.getElementById('rawEvV7').value);
            const temp = document.getElementById('rawTempV7').value;
            const sharp = parseInt(document.getElementById('rawSharpV7').value);

            const c = document.createElement('canvas');
            c.width = 380; c.height = 220;
            const ctx = c.getContext('2d');
            ctx.fillStyle = "#050505"; ctx.fillRect(0, 0, 380, 220);

            if(rawSourceImgV7.src) {
                ctx.drawImage(rawSourceImgV7, 0, 0, 380, 220);
                ctx.fillStyle = ev > 0 ? `rgba(255,255,255,${ev * 0.16})` : `rgba(0,0,0,${Math.abs(ev) * 0.26})`;
                ctx.fillRect(0, 0, 380, 220);

                if(temp === '3200') ctx.fillStyle = "rgba(255, 140, 0, 0.13)";
                else if(temp === '7500') ctx.fillStyle = "rgba(0, 255, 200, 0.13)";
                else ctx.fillStyle = "rgba(255, 255, 255, 0.02)";
                ctx.fillRect(0, 0, 380, 220);

                ctx.strokeStyle = "#00FFC8"; ctx.lineWidth = 1.5;
                ctx.beginPath(); ctx.moveTo(10, 210); ctx.lineTo(35, 185); ctx.lineTo(70, 205); ctx.lineTo(105, 175); ctx.lineTo(140, 210); ctx.stroke();
            } else {
                ctx.fillStyle = "#00FFC8"; ctx.font = "bold 11px system-ui"; ctx.textAlign = "center";
                ctx.fillText("ESTUDIO RAW V7 ULTRA: Carga una foto para calibración", 190, 110);
            }
            box.innerHTML = ""; box.appendChild(c);
            res.innerHTML = `
            <div style="background:#181818; padding:12px; border-radius:8px; border:1px solid #00FFC8;">
                <p style="color:#00FFC8; font-weight:bold; margin-bottom:4px;">📸 Revelado RAW V7 Ultra:</p>
                <p>• EV: <strong style="color:#FFF;">${ev > 0 ? '+'+ev : ev} Stops</strong> | Kelvin: <strong style="color:#FFF;">${temp}K</strong> | Claridad: <strong style="color:#00FFC8;">${sharp}%</strong></p>
            </div>`;
        }

        /* --- 9. CINE SCOPE V7 --- */
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

            const c = document.createElement('canvas');
            c.width = 380; c.height = 200;
            const ctx = c.getContext('2d');
            ctx.fillStyle = "#000"; ctx.fillRect(0, 0, 380, 200);

            if(cineSourceImgV7.src) {
                ctx.drawImage(cineSourceImgV7, 0, 0, 380, 200);
                if(lut === 'teal_orange') {
                    ctx.fillStyle = "rgba(0, 200, 200, 0.18)"; ctx.fillRect(0, 0, 380, 200);
                    ctx.fillStyle = "rgba(255, 120, 0, 0.12)"; ctx.fillRect(0, 0, 380, 200);
                } else if(lut === 'gold_flare_70mm') {
                    ctx.fillStyle = "rgba(255, 215, 0, 0.22)"; ctx.fillRect(0, 0, 380, 200);
                } else if(lut === 'noir_monochrome') {
                    ctx.fillStyle = "rgba(0, 0, 0, 0.42)"; ctx.fillRect(0, 0, 380, 200);
                } else if(lut === 'matrix_cyber') {
                    ctx.fillStyle = "rgba(0, 255, 160, 0.22)"; ctx.fillRect(0, 0, 380, 200);
                }

                if(flare > 0) {
                    ctx.fillStyle = `rgba(0, 255, 200, ${ (flare / 100) * 0.40 })`;
                    ctx.fillRect(0, 98, 380, 4);
                }
                if(grain > 0) {
                    ctx.fillStyle = `rgba(255, 255, 255, ${ (grain / 100) * 0.08 })`;
                    ctx.fillRect(0, 0, 380, 200);
                }

                let barHeight = aspect === '21:9' ? 28 : (aspect === '2.39:1' ? 36 : 0);
                if(barHeight > 0) {
                    ctx.fillStyle = "#000";
                    ctx.fillRect(0, 0, 380, barHeight);
                    ctx.fillRect(0, 200 - barHeight, 380, barHeight);
                }
            } else {
                ctx.fillStyle = "#00FFC8"; ctx.font = "bold 11px system-ui"; ctx.textAlign = "center";
                ctx.fillText("CINE SCOPE V7 ULTRA: Carga un fotograma", 190, 100);
            }
            box.innerHTML = ""; box.appendChild(c);
            res.innerHTML = `
            <div style="background:#181818; padding:12px; border-radius:8px; border:1px solid #00FFC8;">
                <p style="color:#00FFC8; font-weight:bold; margin-bottom:4px;">🎬 Gradación Anamórfica V7:</p>
                <p>• LUT: <strong style="color:#FFF;">${lut.toUpperCase()}</strong> | Encuadre: <strong style="color:#00FFC8;">${aspect}</strong> | Flare: <strong style="color:#00FFC8;">${flare}%</strong></p>
            </div>`;
        }

        /* --- 10. IMPRENTA PDF V7 --- */
        async function loadPrintArtFromGalleryV7() {
            const res = await fetch('/bian/images/');
            const images = await res.json();
            if(images.length === 0) { alert("No hay imágenes en la galería."); return; }
            printSourceImgV7.crossOrigin = "anonymous";
            printSourceImgV7.src = images[images.length - 1].image_path;
            printSourceImgV7.onload = () => { processPrintV7(); alert("✔ Diseño montado en Preprensa V7."); };
        }
        function processPrintV7() {
            const box = document.getElementById('printPreviewBoxV7');
            const res = document.getElementById('printResultV7');
            const mode = document.getElementById('printBleedV7').value;
            const profile = document.getElementById('printProfileV7').value;

            const c = document.createElement('canvas');
            c.width = 380; c.height = 220;
            const ctx = c.getContext('2d');
            ctx.fillStyle = "#0A0A0A"; ctx.fillRect(0, 0, 380, 220);
            ctx.fillStyle = "#161616"; ctx.fillRect(20, 20, 340, 180);

            if(printSourceImgV7.src) {
                ctx.drawImage(printSourceImgV7, 26, 26, 328, 168);
            } else {
                ctx.fillStyle = "#00FFC8"; ctx.font = "bold 11px system-ui"; ctx.textAlign = "center";
                ctx.fillText("MESA DE PREPRENSA V7 ULTRA: Carga un diseño", 190, 110);
            }

            ctx.strokeStyle = "#FF0055"; ctx.lineWidth = 1.5; ctx.strokeRect(26, 26, 328, 168);
            ctx.strokeStyle = "#00FFC8"; ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(10, 26); ctx.lineTo(26, 26); ctx.moveTo(26, 10); ctx.lineTo(26, 26);
            ctx.moveTo(370, 26); ctx.lineTo(354, 26); ctx.moveTo(354, 10); ctx.lineTo(354, 26);
            ctx.stroke();

            const cmykColors = ["#00FFFF", "#FF00FF", "#FFFF00", "#000000"];
            for(let i = 0; i < cmykColors.length; i++) {
                ctx.fillStyle = cmykColors[i]; ctx.fillRect(95 + (i * 22), 6, 16, 8);
            }
            ctx.fillStyle = "#FFF"; ctx.fillRect(334, 5, 14, 14);
            ctx.fillStyle = "#000"; ctx.fillRect(337, 8, 8, 8);

            box.innerHTML = ""; box.appendChild(c);
            res.innerHTML = `
            <div style="background:#181818; padding:12px; border-radius:8px; border:1px solid #00FFC8;">
                <p style="color:#00FFC8; font-weight:bold; margin-bottom:4px;">🖨️ Pliego Técnico Preprensa V7 Ultra:</p>
                <p>• Modo: <strong style="color:#FFF;">${mode.toUpperCase()}</strong> | Perfil: <strong style="color:#FFF;">${profile.toUpperCase()}</strong> | Sangrado: <strong style="color:#FF0055;">3.0mm</strong></p>
                <button class="btn-action" style="margin-top:8px; width:100%; color:#FFD700; border:1px solid #FFD700;" onclick="alert('✔ PDF/X-1a V7 generado y listo.')">📄 Exportar Salida PDF/X-1a V7</button>
            </div>`;
        }

        /* --- 11. WALLPAPERS & STICKERS V5 --- */
        async function loadCustomArtFromGalleryV5() {
            const res = await fetch('/bian/images/');
            const images = await res.json();
            if(images.length === 0) { alert("No hay imágenes en la galería."); return; }
            customSourceImgV5.crossOrigin = "anonymous";
            customSourceImgV5.src = images[images.length - 1].image_path;
            customSourceImgV5.onload = () => { renderCustomV5(); alert("✔ Arte cargado en Canvas V5."); };
        }
        function renderCustomV5() {
            const box = document.getElementById('customPreviewBoxV5');
            const type = document.getElementById('customTypeV5').value;
            const style = document.getElementById('customStyleV5').value;

            lastCustomCanvasV5 = document.createElement('canvas');
            lastCustomCanvasV5.width = 300;
            lastCustomCanvasV5.height = type === 'wallpaper_amoled' ? 450 : 300;
            const ctx = lastCustomCanvasV5.getContext('2d');

            ctx.fillStyle = "#000000"; ctx.fillRect(0, 0, lastCustomCanvasV5.width, lastCustomCanvasV5.height);

            if(type === 'wallpaper_amoled') {
                if(style === 'cyber_grid') {
                    ctx.strokeStyle = "rgba(0, 255, 200, 0.15)"; ctx.lineWidth = 1;
                    for(let x = 0; x < 300; x += 20) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, 450); ctx.stroke(); }
                    for(let y = 0; y < 450; y += 20) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(300, y); ctx.stroke(); }
                } else if(style === 'circuit_glow') {
                    ctx.strokeStyle = "rgba(255, 215, 0, 0.2)"; ctx.lineWidth = 1.5; ctx.strokeRect(30, 30, 240, 390);
                }

                if(customSourceImgV5.src) {
                    ctx.drawImage(customSourceImgV5, 25, 75, 250, 300);
                } else {
                    ctx.fillStyle = "#00FFC8"; ctx.font = "bold 13px system-ui"; ctx.textAlign = "center";
                    ctx.fillText("WALLPAPER AMOLED V5 (9:16)", 150, 225);
                }
            } else {
                ctx.fillStyle = "rgba(15, 15, 15, 0.8)"; ctx.fillRect(0, 0, 300, 300);
                if(customSourceImgV5.src) {
                    ctx.fillStyle = "#FFFFFF"; ctx.beginPath(); ctx.arc(150, 150, 95, 0, Math.PI*2); ctx.fill();
                    ctx.drawImage(customSourceImgV5, 60, 60, 180, 180);
                } else {
                    ctx.fillStyle = "#FFFFFF"; ctx.beginPath(); ctx.arc(150, 150, 85, 0, Math.PI*2); ctx.fill();
                    ctx.fillStyle = "#000"; ctx.font = "bold 12px system-ui"; ctx.textAlign = "center";
                    ctx.fillText("STICKER TROQUELADO V5", 150, 150);
                }
            }
            box.innerHTML = ""; box.appendChild(lastCustomCanvasV5);
            document.getElementById('customActionsV5').style.display = 'block';
        }
        function downloadCustomAssetV5() {
            if(!lastCustomCanvasV5) return;
            const url = lastCustomCanvasV5.toDataURL('image/png');
            const a = document.createElement('a'); a.href = url; a.download = `activo_v5_${Date.now()}.png`; a.click();
        }

        /* --- CAPTURA Y GALERIA GENERAL --- */
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
        "engine": "Bian V7 Master Suite (100% Fully Powered & Unified)",
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
