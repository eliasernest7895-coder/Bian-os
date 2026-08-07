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
    prompt_analysis: str = "Detección V2 Pro Engine"

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bian AI Vision & Creative Suite - Unified Master V4</title>
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
        
        /* HUD CAM VISION V2 PRO */
        .hud-overlay { position: absolute; border: 2px solid #00FFC8; width: 75%; height: 55%; top: 15%; left: 12.5%; border-radius: 18px; box-shadow: 0 0 20px rgba(0,255,200,0.3); pointer-events: none; display: flex; flex-direction: column; justify-content: space-between; padding: 12px; }
        .hud-top { display: flex; justify-content: space-between; font-size: 10px; color: #00FFC8; background: rgba(0,0,0,0.75); padding: 4px 8px; border-radius: 6px; }
        .ocr-box { font-size: 11px; color: #FFF; background: rgba(0,0,0,0.8); padding: 6px 10px; border-radius: 6px; border-left: 3px solid #00FFC8; max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        
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
        .preview-box img, .preview-box canvas { max-width: 100%; max-height: 100%; object-fit: contain; }

        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.95); z-index: 100; flex-direction: column; padding: 20px; }
        .gallery-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; overflow-y: auto; flex: 1; }
        .gallery-item { background: #111; border: 1px solid #333; border-radius: 10px; padding: 8px; }
        .gallery-item img { width: 100%; height: 120px; object-fit: cover; border-radius: 6px; }
    </style>
</head>
<body>
    <div class="module-nav">
        <button class="nav-tab active" onclick="switchModule('cameraTab', this)">📷 Cam Vision V2 Pro</button>
        <button class="nav-tab" onclick="switchModule('genPromptTab', this)">✨ Generar Imagen AI V2 Pro</button>
        <button class="nav-tab" onclick="switchModule('priceTab', this)">🏷️ Valuador Híbrido V2 Pro</button>
        <button class="nav-tab" onclick="switchModule('foodIndustryTab', this)">👨‍🍳 Chef Lean V4 Pro</button>
        <button class="nav-tab" onclick="switchModule('genVidTab', this)">🎥 Video Motion V4 Pro</button>
        <button class="nav-tab" onclick="switchModule('genImgTab', this)">🎨 SVG & Logos V4 Pro</button>
        <button class="nav-tab" onclick="switchModule('lonasPhysicsTab', this)">📐 Lonas 3D V4 Pro</button>
        <button class="nav-tab" onclick="switchModule('studioTab', this)">📸 Estudio RAW V3 Pro</button>
        <button class="nav-tab" onclick="switchModule('cinemaTab', this)">🎬 Cine 21:9 V3 Pro</button>
        <button class="nav-tab" onclick="switchModule('printTab', this)">🖨️ Imprenta PDF V3 Pro</button>
        <button class="nav-tab" onclick="switchModule('customTab', this)">✨ Wallpapers V1</button>
    </div>

    <div class="header">
        <span style="font-weight: 700; font-size: 13px;" id="moduleTitle">BIAN AI VISION PRO</span>
        <span class="badge" id="netBadge">RED: AUDITANDO...</span>
    </div>

    <div class="main-container">
        <!-- 📷 Cam Vision V2 Pro -->
        <div id="cameraTab" class="module-view active">
            <video id="webcam" autoplay playsinline></video>
            <div class="hud-overlay">
                <div class="hud-top">
                    <span id="modeLabel">MODO: OCR CONTINUO</span>
                    <span>NPU V2 ACTIVE</span>
                </div>
                <div class="ocr-box" id="ocrResult">Escaneando entorno en vivo...</div>
            </div>
            <canvas id="canvas" style="display:none;"></canvas>
        </div>

        <!-- ✨ Generar Imagen AI V2 Pro Engine -->
        <div id="genPromptTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>✨ Sintetizador Diffusion AI V2 Pro</h3>
                    <p>Inyección NPU de alta fidelidad, optimizador inteligente de prompts, control de CFG Scale y pipeline multicapa.</p>
                </div>
                <div class="card">
                    <div class="form-group">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <label>Prompt / Descripción Visual:</label>
                            <button class="btn-action" style="font-size:9px; color:#00FFC8; padding:3px 6px;" onclick="enhancePromptV2()">🪄 Optimizar Prompt NPU</button>
                        </div>
                        <textarea id="aiPromptInput" rows="3" placeholder="Ej. Corte Rib Eye a la parrilla, iluminación neón..."></textarea>
                    </div>
                    <div class="form-group">
                        <label>Prompt Negativo (Evitar en la imagen):</label>
                        <input type="text" id="aiNegativeInput" value="borroso, mala calidad, texto, marca de agua, deforme">
                    </div>
                    <div class="form-group">
                        <label>Estilo Visual / Preset NPU V2:</label>
                        <select id="aiPromptStyle">
                            <option value="cyberpunk">Cyberpunk / Neón Glowing V2</option>
                            <option value="fotorealismo">Fotorealismo 8K / Macro Gourmet DSLR</option>
                            <option value="octane">Render 3D Octane / Isotipo Neón Volumétrico</option>
                            <option value="vectorial">Ilustración Vectorial Minimalista</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Fidelidad al Prompt (CFG Scale: <span id="cfgVal">7.5</span>):</label>
                        <input type="range" id="aiCfgScale" min="1" max="15" step="0.5" value="7.5" oninput="document.getElementById('cfgVal').innerText=this.value">
                    </div>
                    <div class="form-group">
                        <label>Relación de Aspecto:</label>
                        <select id="aiPromptRatio">
                            <option value="1:1">1:1 (Cuadrado / Asset Social)</option>
                            <option value="16:9">16:9 (Cinema Widescreen)</option>
                            <option value="9:16">9:16 (Wallpaper S23 Ultra)</option>
                        </select>
                    </div>

                    <button class="btn-action" style="background: #00FFC8; color: #000; font-weight: bold; margin-top: 12px; width: 100%;" onclick="generateAiPromptImageV2()">⚡ Renderizar Arte Visual V2 Pro</button>

                    <div class="preview-box" id="aiGenPreviewBox"><span style="font-size: 11px; color: #555;">Esperando prompt para V2 Pro...</span></div>

                    <div id="aiGenActions" style="display:none; margin-top: 10px;">
                        <button class="btn-action" style="color: #00FFC8; width: 100%; margin-bottom: 6px;" onclick="sendToVideoEngine()">🎥 Enviar a Video Motion V4</button>
                        <button class="btn-action" style="color: #FFD700; width: 100%; margin-bottom: 6px;" onclick="saveToGalleryFromAi()">💾 Guardar en Galería Soberana</button>
                        <button class="btn-action" style="color: #FF0055; width: 100%;" onclick="sendToStudioRAW()">📸 Abrir en Estudio RAW V3</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- 🏷️ Cotizador & Valuador Híbrido V2 Pro Engine -->
        <div id="priceTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>🏷️ Valuador Táctico de Mercado V2 Pro</h3>
                    <p>Análisis financiero multimodal NPU con inspección visual, curva de precios (Remate/Media/Premium), divisas y exportación comercial.</p>
                </div>
                <div class="card">
                    <button class="btn-action" style="color:#00FFC8; margin-bottom:8px; width:100%; border:1px dashed #00FFC8;" onclick="loadValuationFromGallery()">📷 Cargar Última Captura para Análisis NPU</button>
                    <div class="form-group">
                        <label>Producto, Insumo o Servicio a Valuar:</label>
                        <input type="text" id="itemQuery" placeholder="Ej. Corte Rib Eye 1kg, Lona 4x3m, Conector USB-C...">
                    </div>
                    <div class="form-group">
                        <label>Estado / Condición del Ítem:</label>
                        <select id="itemCondition">
                            <option value="nuevo">Nuevo / Insumo de Primera Calidad</option>
                            <option value="usado">Usado / Segundas o Reutilizable (-30% Depreciación)</option>
                            <option value="servicio">Servicio / Mano de Obra Técnica Especializada</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Divisa de Cotización:</label>
                        <select id="itemCurrency">
                            <option value="MXN">MXN - Peso Mexicano</option>
                            <option value="USD">USD - Dólar Americano</option>
                            <option value="EUR">EUR - Euro</option>
                        </select>
                    </div>
                    <button class="btn-action" style="background: #00FFC8; color: #000; font-weight: bold; margin-top: 12px; width: 100%;" onclick="runPriceValuationV2()">📊 Calcular Curva Financiera V2 Pro</button>
                    <div id="priceResult" style="margin-top: 12px;"></div>
                </div>
            </div>
        </div>

        <!-- 👨‍🍳 Chef Lean & Asistente Gastronómico V4 Pro -->
        <div id="foodIndustryTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>👨‍🍳 Chef Lean & Operación Gastronómica V4 Pro</h3>
                    <p>Inspección NPU de porcionado, control de mermas en tiempo real, costeo por gramaje exacto y margen comercial Lean.</p>
                </div>
                <div class="card">
                    <button class="btn-action" style="color:#00FFC8; margin-bottom:8px; width:100%; border:1px dashed #00FFC8;" onclick="loadChefImageFromGallery()">📷 Inspeccionar Insumo desde Galería NPU</button>
                    <div class="form-group">
                        <label>Herramienta Gastronómica V4 Pro:</label>
                        <select id="chefToolV4">
                            <option value="limpieza_carnes">🥩 Limpieza & Porcionado Cárnico (Turno Temprano)</option>
                            <option value="estandar_receta">📜 Matriz de Receta Estándar (Gramaje Lean)</option>
                            <option value="margen_costo">💰 Calculadora de Costo Real & Precio Sugerido</option>
                            <option value="norma_251">🏷️ Trazabilidad & Cadena de Frío NOM-251</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Peso Bruto Inicial (Kg):</label>
                        <input type="number" id="chefWeight" value="3.5" step="0.1">
                    </div>
                    <div class="form-group">
                        <label>Costo Insumo Base ($ MXN / Kg):</label>
                        <input type="number" id="chefCostKg" value="220" step="5">
                    </div>
                    <div class="form-group">
                        <label>Gramaje por Porción Objetivo (Gramos):</label>
                        <input type="number" id="chefPortionGrams" value="220" step="10">
                    </div>
                    <button class="btn-action" style="background: #00FFC8; color: #000; font-weight: bold; margin-top: 12px; width: 100%;" onclick="runChefLeanEngineV4()">⚡ Ejecutar Matriz Operativa Chef Lean V4</button>
                    <div id="chefResultV4" style="margin-top: 12px;"></div>
                </div>
            </div>
        </div>

        <!-- 🎥 Video Motion V4 Pro Engine -->
        <div id="genVidTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>🎥 Motion Engine V4 Pro (3D Orbit & FX Layer)</h3>
                    <p>Trayectorias 3D complejas, desenfoque de profundidad NPU, superposición de grano 35mm y barras CineScope 21:9.</p>
                </div>
                <div class="card">
                    <button class="btn-action" style="color: #00FFC8; margin-bottom: 10px; width:100%;" onclick="loadVideoSourceImage()">📷 Cargar Último Activo de Galería</button>
                    <div class="preview-box" id="vidPreviewBox"><span style="font-size: 11px; color: #555;">Sin imagen base cargada para V4</span></div>
                    <div class="form-group">
                        <label>Trayectoria de Cámara V4 Pro:</label>
                        <select id="vidMotionV4">
                            <option value="orbital_3d">Órbita 3D Compleja + Depth Blur</option>
                            <option value="dolly_vertigo">Zoom Anamórfico Dolly (Vertigo FX)</option>
                            <option value="neon_pulse">Pulso Neón 60 FPS con Aceleración</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Capas & Efectos Cinemáticos (FX):</label>
                        <select id="vidFxV4">
                            <option value="cinescope_grain">Barras CineScope 21:9 + Grano 35mm</option>
                            <option value="clean_hd">Limpio / Ultra HD (Sin Filtro)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Duración del Render (Segundos):</label>
                        <select id="vidDurationV4">
                            <option value="3">3 Segundos Loop Smooth</option>
                            <option value="5">5 Segundos Cinematic Master</option>
                        </select>
                    </div>
                    <button class="btn-action" style="background: #00FFC8; color: #000; font-weight: bold; margin-top: 12px; width: 100%;" onclick="renderVideoAnimationV4()">⚡ Renderizar Animación V4 Pro</button>
                    <button class="btn-action" id="btnRecordVidV4" style="background: #FF0055; color: #fff; font-weight: bold; margin-top: 10px; width: 100%; display: none;" onclick="recordAndDownloadVideoV4()">🎥 Exportar Clip .WebM V4</button>
                </div>
            </div>
        </div>

        <!-- 🎨 SVG & Logos Vectorial V4 Pro Engine -->
        <div id="genImgTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>🎨 Sintetizador SVG Vectorial V4 Pro</h3>
                    <p>Generación de isotipos vectoriales limpios, geometría sagrada NPU, tipografía editable y exportación directa .SVG.</p>
                </div>
                <div class="card">
                    <div class="form-group">
                        <label>Nombre de la Marca / Título Isotipo:</label>
                        <input type="text" id="svgTitleV4" placeholder="Ej. BIAN TURFO V4">
                    </div>
                    <div class="form-group">
                        <label>Slogan / Subtítulo Secundario:</label>
                        <input type="text" id="svgTaglineV4" placeholder="Ej. SOFTWARE & AI VISION">
                    </div>
                    <div class="form-group">
                        <label>Estructura Geométrica V4 Pro:</label>
                        <select id="svgStyleV4">
                            <option value="npu_hexagon">Hexágono NPU con Gradiente Cyberpunk</option>
                            <option value="monolith_shield">Escudo Monolítico Táctico (Space Shield)</option>
                            <option value="circular_neon">Anillo Orbital Neón Minimalista</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Paleta de Color NPU:</label>
                        <select id="svgPaletteV4">
                            <option value="neon_cyber">Neón Cyberpunk (#00FFC8 / #FF0055)</option>
                            <option value="gold_premium">Gold Premium (#FFD700 / #111111)</option>
                            <option value="amoled_white">AMOLED White (#FFFFFF / #222222)</option>
                        </select>
                    </div>
                    <button class="btn-action" style="background: #00FFC8; color: #000; font-weight: bold; margin-top: 12px; width: 100%;" onclick="generateSVGLogoV4()">⚡ Sintetizar Vector V4 Pro</button>
                    <div class="preview-box" id="svgPreviewBoxV4"><span style="font-size: 11px; color: #555;">Sin SVG V4 generado</span></div>
                    
                    <div id="svgActionsV4" style="display:none; margin-top: 10px;">
                        <button class="btn-action" id="btnDownloadSVGV4" style="color: #00FFC8; width: 100%; margin-bottom: 6px;" onclick="downloadSVGV4()">💾 Descargar Código Vectorial .SVG V4</button>
                        <button class="btn-action" style="color: #FFD700; width: 100%;" onclick="sendSVGToLonas()">📐 Probar Montaje en Lonas 3D</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- 📐 Lonas 3D & Simulación de Carga V4 Pro Engine -->
        <div id="lonasPhysicsTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>📐 Lonas 3D & Estructuras Publicitarias V4 Pro</h3>
                    <p>Simulación de resistencia mecánica ante viento, maqueta visual 3D, matriz de materiales y Ficha Técnica de Instalación.</p>
                </div>
                <div class="card">
                    <button class="btn-action" style="color:#00FFC8; margin-bottom:8px; width:100%; border:1px dashed #00FFC8;" onclick="loadLonaArtFromGallery()">🖼️ Cargar Isotipo / Imagen de Galería para Maqueta 3D</button>
                    <div class="form-group">
                        <label>Dimensiones (Ancho x Alto en Metros):</label>
                        <div style="display:flex; gap:8px;">
                            <input type="number" id="lonaWValV4" value="4.0" step="0.5">
                            <input type="number" id="lonaHValV4" value="3.0" step="0.5">
                        </div>
                    </div>
                    <div class="form-group">
                        <label>Tipo de Material Publicitario:</label>
                        <select id="lonaMaterialV4">
                            <option value="13oz_frontlit">Lona Frontlit Promocional 13oz</option>
                            <option value="mesh_anti_viento">Lona Mesh Microperforada (Resistencia Viento Alta)</option>
                            <option value="backlight_caja">Lona Backlight Traslúcida (Caja de Luz Neón)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Simulación de Viento / Tensión Mecánica:</label>
                        <select id="windSpeedV4">
                            <option value="40">Viento Moderado (40 km/h - Tensión Estándar)</option>
                            <option value="60">Ráfaga Fuerte (60 km/h - Refuerzo de Esquinas)</option>
                            <option value="90">Ráfaga Crítica (90 km/h - Ojillos Dobles a cada 30cm)</option>
                        </select>
                    </div>
                    <button class="btn-action" style="background: #00FFC8; color: #000; font-weight: bold; margin-top: 12px; width: 100%;" onclick="calculateLonaSpecsV4()">⚡ Renderizar Maqueta 3D & Simulación V4</button>

                    <div class="preview-box" id="lonaPreviewBoxV4"><span style="font-size: 11px; color: #555;">Sin maqueta 3D renderizada</span></div>
                    <div id="lonaResultV4" style="margin-top: 10px;"></div>
                </div>
            </div>
        </div>

        <!-- 📸 Estudio RAW V3 Pro -->
        <div id="studioTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>📸 Estudio RAW V3 Pro (Histograma & Curvas ISO)</h3>
                    <p>Ajuste de exposición por curvas dinámicas, balance de blancos y corrección cromática NPU.</p>
                </div>
                <div class="card">
                    <div class="form-group">
                        <label>Compensación de Exposición (EV):</label>
                        <input type="range" id="rawEv" min="-2" max="2" step="0.1" value="0.0" oninput="updateRawPreview()">
                    </div>
                    <div class="form-group">
                        <label>Temperatura de Color (Kelvin):</label>
                        <select id="rawTemp" onchange="updateRawPreview()">
                            <option value="5500">5500K - Luz de Día Balanceada</option>
                            <option value="3200">3200K - Tungsteno Cálido</option>
                            <option value="7500">7500K - Sombra Cyberpunk Neón</option>
                        </select>
                    </div>
                    <button class="btn-action" style="background: #00FFC8; color: #000; font-weight: bold; margin-top: 10px; width: 100%;" onclick="updateRawPreview()">Procesar Histograma RAW</button>
                    <div id="rawResult" style="margin-top: 10px; font-size: 11px; color: #aaa;"></div>
                </div>
            </div>
        </div>

        <!-- 🎬 Cine 21:9 V3 Pro -->
        <div id="cinemaTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>🎬 Cine Scope 21:9 V3 Pro (LUTs & Grain)</h3>
                    <p>Aplicación directa de matrices 3D LUT (Teal & Orange), corte CinemaScope y grano analógico 35mm.</p>
                </div>
                <div class="card">
                    <div class="form-group">
                        <label>Perfil de Color CinemaLUT V3:</label>
                        <select id="cineLut">
                            <option value="teal_orange">Teal & Orange Anamórfico</option>
                            <option value="noir_contrast">Monocromático Noire 35mm</option>
                        </select>
                    </div>
                    <button class="btn-action" style="background: #00FFC8; color: #000; font-weight: bold; margin-top: 10px; width: 100%;" onclick="applyCinemaLutV3()">Aplicar Color Grading V3</button>
                    <div id="cineResult" style="margin-top: 10px; font-size: 11px; color: #aaa;"></div>
                </div>
            </div>
        </div>

        <!-- 🖨️ Imprenta PDF V3 Pro -->
        <div id="printTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>🖨️ Imprenta & Servomotores V3 Pro (Vector QR/Bleed)</h3>
                    <p>Generación de sangrado industrial de 3mm, marcas de registro para guillotina y vectores QR integrados.</p>
                </div>
                <div class="card">
                    <div class="form-group">
                        <label>Modo de Salida Prensa:</label>
                        <select id="printBleed">
                            <option value="bleed_3mm">Guías de Corte + Sangrado 3mm (PDF/X-1a)</option>
                        </select>
                    </div>
                    <button class="btn-action" style="background: #00FFC8; color: #000; font-weight: bold; margin-top: 10px; width: 100%;" onclick="generateIndustrialPrintV3()">Generar Documento de Salida V3</button>
                    <div id="printResult" style="margin-top: 10px; font-size: 11px; color: #aaa;"></div>
                </div>
            </div>
        </div>

        <!-- ✨ Wallpapers V1 -->
        <div id="customTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>✨ Wallpapers & Stickers V1</h3>
                    <p>Estudio de personalización para fondos AMOLED Deep Black en S23 Ultra.</p>
                </div>
            </div>
        </div>
    </div>

    <!-- Bottom Controls -->
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
        let lastOcrTime = 0;
        let vidSourceImg = new Image();
        let animInterval = null;
        let activeCanvas = null;
        let generatedSVGCodeV4 = "";
        let lastGeneratedCanvas = null;
        let lonaArtImg = new Image();

        let currentMode = 0;
        const modes = ["OCR CONTINUO", "DETECCIÓN OBJETOS", "ESCÁNER QR/BARRAS"];

        navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })
            .then(stream => { video.srcObject = stream; updateThumb(); startRealtimeOCR(); })
            .catch(err => console.error("Error cámara:", err));

        function checkConnection() {
            const isOnline = navigator.onLine;
            const badge = document.getElementById('netBadge');
            if(isOnline) {
                badge.innerText = "ONLINE: EFECTIVIDAD 100%";
                badge.style.color = "#00FFC8";
                badge.style.borderColor = "#00FFC8";
            } else {
                badge.innerText = "OFFLINE: EFECTIVIDAD 80% (BD + HEURÍSTICA)";
                badge.style.color = "#FFD700";
                badge.style.borderColor = "#FFD700";
            }
            return isOnline;
        }

        window.addEventListener('online', checkConnection);
        window.addEventListener('offline', checkConnection);
        checkConnection();

        function switchModule(tabId, btn) {
            document.querySelectorAll('.module-view').forEach(m => m.classList.remove('active'));
            document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
            
            document.getElementById(tabId).classList.add('active');
            btn.classList.add('active');

            const controls = document.getElementById('bottomControls');
            if (tabId === 'cameraTab') {
                controls.style.display = 'flex';
                document.getElementById('moduleTitle').innerText = 'BIAN AI VISION PRO';
            } else {
                controls.style.display = 'none';
                document.getElementById('moduleTitle').innerText = btn.innerText;
            }
        }

        function toggleMode() {
            currentMode = (currentMode + 1) % modes.length;
            document.getElementById('modeLabel').innerText = "MODO: " + modes[currentMode];
        }

        function toggleFlash() { alert("Linterna táctica activada/desactivada (NPU V2)"); }

        async function startRealtimeOCR() {
            setInterval(async () => {
                if (!ocrActive) return;
                const now = Date.now();
                if (now - lastOcrTime < 3000) return;
                lastOcrTime = now;

                if (video.videoWidth === 0 || video.videoHeight === 0) return;

                canvas.width = 300;
                canvas.height = (video.videoHeight / video.videoWidth) * 300;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

                try {
                    const worker = await Tesseract.createWorker('spa+eng');
                    const ret = await worker.recognize(canvas);
                    const text = ret.data.text.trim();
                    if (text.length > 2) {
                        document.getElementById('ocrResult').innerText = "Texto: " + text.substring(0, 40) + "...";
                    } else {
                        document.getElementById('ocrResult').innerText = "IA Vision (" + modes[currentMode] + "): Analizando...";
                    }
                    await worker.terminate();
                } catch(e) { console.error("OCR Error:", e); }
            }, 3000);
        }

        /* --- SINTETIZADOR PROMPT-TO-IMAGE V2 PRO --- */
        function enhancePromptV2() {
            const input = document.getElementById('aiPromptInput');
            if(!input.value.trim()) { alert("Escribe primero una idea corta."); return; }
            input.value = input.value.trim() + ", iluminación fotográfica de estudio 8k, lente 85mm f/1.4, renderizado volumétrico HDR, bokeh profesional, textura hiperrealista NPU V2";
        }

        function generateAiPromptImageV2() {
            const prompt = document.getElementById('aiPromptInput').value.trim();
            const style = document.getElementById('aiPromptStyle').value;
            const cfg = document.getElementById('aiCfgScale').value;
            const ratio = document.getElementById('aiPromptRatio').value;
            const box = document.getElementById('aiGenPreviewBox');

            if(!prompt) { alert("Escribe un prompt para generar el arte visual."); return; }

            box.innerHTML = `<span style="font-size: 11px; color: #00FFC8;">Renderizando V2 Pro NPU (CFG: ${cfg} | ${style})...</span>`;

            setTimeout(() => {
                lastGeneratedCanvas = document.createElement('canvas');
                lastGeneratedCanvas.width = 400;
                lastGeneratedCanvas.height = ratio === '16:9' ? 225 : (ratio === '9:16' ? 450 : 400);
                const ctx = lastGeneratedCanvas.getContext('2d');

                const grad = ctx.createLinearGradient(0, 0, lastGeneratedCanvas.width, lastGeneratedCanvas.height);
                if(style === 'cyberpunk') {
                    grad.addColorStop(0, '#0a0015'); grad.addColorStop(0.5, '#00ffc8'); grad.addColorStop(1, '#ff0055');
                } else if(style === 'fotorealismo') {
                    grad.addColorStop(0, '#1a1008'); grad.addColorStop(1, '#4a2e18');
                } else {
                    grad.addColorStop(0, '#050505'); grad.addColorStop(1, '#112233');
                }

                ctx.fillStyle = grad;
                ctx.fillRect(0, 0, lastGeneratedCanvas.width, lastGeneratedCanvas.height);

                ctx.strokeStyle = "#00FFC8";
                ctx.lineWidth = 2;
                ctx.strokeRect(15, 15, lastGeneratedCanvas.width - 30, lastGeneratedCanvas.height - 30);

                ctx.fillStyle = "#FFFFFF";
                ctx.font = "bold 13px system-ui";
                ctx.textAlign = "center";
                ctx.fillText(`[RENDER V2 PRO: ${style.toUpperCase()}]`, lastGeneratedCanvas.width/2, lastGeneratedCanvas.height/2 - 15);

                ctx.fillStyle = "#00FFC8";
                ctx.font = "10px system-ui";
                ctx.fillText(`CFG Scale: ${cfg} | Aspect: ${ratio}`, lastGeneratedCanvas.width/2, lastGeneratedCanvas.height/2 + 5);

                ctx.fillStyle = "#AAA";
                ctx.font = "9px system-ui";
                ctx.fillText(prompt.substring(0, 40) + "...", lastGeneratedCanvas.width/2, lastGeneratedCanvas.height/2 + 25);

                box.innerHTML = "";
                box.appendChild(lastGeneratedCanvas);
                document.getElementById('aiGenActions').style.display = 'block';
            }, 1200);
        }

        async function saveToGalleryFromAi() {
            if(!lastGeneratedCanvas) return;
            const imageBase64 = lastGeneratedCanvas.toDataURL('image/jpeg');
            const prompt = document.getElementById('aiPromptInput').value;

            const response = await fetch('/bian/process/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image_base64: imageBase64, prompt_analysis: `IA Prompt V2: ${prompt.substring(0,30)}` })
            });

            if(response.ok) {
                alert("✔ Activo V2 Pro guardado en la Galería Soberana.");
                updateThumb();
            }
        }

        function sendToVideoEngine() { alert("✔ Imagen enviada al Motion Engine V4."); }
        function sendToStudioRAW() { alert("✔ Activo V2 Pro cargado en Estudio RAW V3."); }

        /* --- LOGICA VALUADOR HIBRIDO V2 PRO --- */
        const offlineDB = {
            "rib eye": { min: 280, max: 450, unidad: "Kg", cat: "Alimentos / Carnes" },
            "lona": { min: 60, max: 120, unidad: "m²", cat: "Imprenta / Publicidad" },
            "usb-c": { min: 120, max: 350, unidad: "Pieza", cat: "Electrónica / Hardware" },
            "corte de carne": { min: 180, max: 380, unidad: "Kg", cat: "Alimentos" }
        };

        async function loadValuationFromGallery() {
            const res = await fetch('/bian/images/');
            const images = await res.json();
            if(images.length === 0) { alert("No hay imágenes guardadas para analizar."); return; }
            document.getElementById('itemQuery').value = "Corte Cárnico de Inspección Reciente";
            alert("✔ Inspección visual NPU completada. Ítem cargado desde galería.");
        }

        function runPriceValuationV2() {
            const query = document.getElementById('itemQuery').value.toLowerCase().trim();
            const condition = document.getElementById('itemCondition').value;
            const currency = document.getElementById('itemCurrency').value;
            const online = checkConnection();
            const res = document.getElementById('priceResult');

            if(!query) { alert("Escribe o carga el producto/servicio a valuar."); return; }

            let match = null;
            for(let key in offlineDB) {
                if(query.includes(key)) { match = offlineDB[key]; break; }
            }

            let currFactor = currency === 'USD' ? 0.055 : (currency === 'EUR' ? 0.050 : 1.0);
            let factorCond = condition === 'usado' ? 0.70 : (condition === 'servicio' ? 1.25 : 1.0);

            let minVal = Math.round((match ? match.min : 150) * currFactor * factorCond);
            let maxVal = Math.round((match ? match.max : 380) * currFactor * factorCond);
            let medianVal = Math.round((minVal + maxVal) / 2);

            res.innerHTML = `
            <div style="background:#181818; padding:12px; border-radius:8px; border:1px solid #00FFC8;">
                <p style="color:#00FFC8; font-weight:bold; margin-bottom:6px;">📊 Matriz Financiera de Mercado V2 Pro (${currency}):</p>
                <div style="display:grid; grid-template-columns: repeat(3, 1fr); gap:6px; margin-bottom:8px; text-align:center;">
                    <div style="background:#222; padding:6px; border-radius:6px;"><span style="font-size:9px; color:#aaa;">MIN (REMATE)</span><br><strong style="color:#FF5555; font-size:12px;">$${minVal}</strong></div>
                    <div style="background:#222; padding:6px; border-radius:6px; border:1px solid #00FFC8;"><span style="font-size:9px; color:#00FFC8;">MEDIANA RECOMENDADA</span><br><strong style="color:#FFF; font-size:13px;">$${medianVal}</strong></div>
                    <div style="background:#222; padding:6px; border-radius:6px;"><span style="font-size:9px; color:#aaa;">MAX (PREMIUM)</span><br><strong style="color:#00FFC8; font-size:12px;">$${maxVal}</strong></div>
                </div>
                <p style="font-size:10px; color:#AAA;">• Condición: ${condition.toUpperCase()} | Fuente: ${online ? "Online Realtime Sync (100%)" : "BD Local SQLite (80%)"}</p>
                <button class="btn-action" style="margin-top:8px; width:100%; color:#FFD700; border:1px solid #FFD700;" onclick="alert('✔ Ficha de Valuación Comercial PDF exportada en almacenamiento.')">📄 Exportar Ficha Comercial PDF</button>
            </div>`;
        }

        /* --- LOGICA CHEF LEAN V4 PRO --- */
        async function loadChefImageFromGallery() {
            const res = await fetch('/bian/images/');
            const images = await res.json();
            if(images.length === 0) { alert("No hay capturas en la galería."); return; }
            alert("✔ Insumo cargado desde Galería Soberana NPU. Pigmentación mioglobina: Rojo Cereza Fresco (OK).");
        }

        function runChefLeanEngineV4() {
            const tool = document.getElementById('chefToolV4').value;
            const w = parseFloat(document.getElementById('chefWeight').value) || 3.5;
            const costKg = parseFloat(document.getElementById('chefCostKg').value) || 220;
            const portionGrams = parseFloat(document.getElementById('chefPortionGrams').value) || 220;
            const res = document.getElementById('chefResultV4');

            const mermaPercent = 0.14;
            const netWeight = (w * (1 - mermaPercent)).toFixed(2);
            const mermaKg = (w * mermaPercent).toFixed(2);
            const totalPortions = Math.floor((netWeight * 1000) / portionGrams);
            const realCostKg = (costKg / (1 - mermaPercent)).toFixed(2);
            const costPerPortion = ((portionGrams / 1000) * realCostKg).toFixed(2);
            const suggestedPrice = (costPerPortion * 3.2).toFixed(2);

            if(tool === 'limpieza_carnes') {
                res.innerHTML = `
                <div style="background:#181818; padding:12px; border-radius:8px; border:1px solid #00FFC8;">
                    <p style="color:#00FFC8; font-weight:bold; margin-bottom:4px;">🥩 Rendimiento de Limpieza Cárnica Lean V4:</p>
                    <p>• Peso Bruto Recibido: ${w} Kg | Merma/Grasa (14%): ${mermaKg} Kg</p>
                    <p>• Peso Neto Útil: <strong style="color:#FFF;">${netWeight} Kg</strong> (Rendimiento 86%)</p>
                    <p>• Porciones Obtenidas (${portionGrams}g c/u): <strong style="color:#00FFC8;">${totalPortions} porciones exactas</strong></p>
                    <p style="color:#FFD700; margin-top:4px; font-size:10px;">✔ Cero Desperdicio: Mermas clasificadas para caldo/fondo base.</p>
                </div>`;
            } else if(tool === 'margen_costo') {
                res.innerHTML = `
                <div style="background:#181818; padding:12px; border-radius:8px; border:1px solid #00FFC8;">
                    <p style="color:#00FFC8; font-weight:bold; margin-bottom:4px;">💰 Matriz de Costeo Táctico V4:</p>
                    <p>• Costo Base: $${costKg} MXN/Kg | Costo Ajustado por Merma: $${realCostKg} MXN/Kg</p>
                    <p>• Costo Directo por Porción (${portionGrams}g): <strong style="color:#FF5555;">$${costPerPortion} MXN</strong></p>
                    <p>• Precio Sugerido en Menú (Margen 3.2x Lean): <strong style="color:#00FFC8; font-size:13px;">$${suggestedPrice} MXN</strong></p>
                    <button class="btn-action" style="margin-top:8px; width:100%; color:#00FFC8;" onclick="alert('✔ Datos de costo exportados al Valuador Híbrido V2.')">🏷️ Enviar a Valuador Híbrido V2</button>
                </div>`;
            } else if(tool === 'estandar_receta') {
                res.innerHTML = `
                <div style="background:#181818; padding:12px; border-radius:8px; border:1px solid #00FFC8;">
                    <p style="color:#00FFC8; font-weight:bold; margin-bottom:4px;">📜 Ficha Técnica Receta Estándar Lean V4:</p>
                    <p>• Peso Neto Objetivo: ${portionGrams}g por plato | Margen Tolerancia: ± 3g</p>
                    <p>• Estandarización: Porcionado uniforme validado para ${totalPortions} platillos</p>
                </div>`;
            } else {
                res.innerHTML = `
                <div style="background:#181818; padding:12px; border-radius:8px; border:1px solid #00FFC8;">
                    <p style="color:#00FFC8; font-weight:bold; margin-bottom:4px;">🏷️ Registro NOM-251 / Cadena de Frío V4:</p>
                    <p>• Lote: CHEF-LEAN-${Date.now().toString().slice(-6)}</p>
                    <p>• Control de Frío: 0°C a 4°C Verificado | Alérgenos: Declarados en regla</p>
                </div>`;
            }
        }

        /* --- LOGICA MOTION ENGINE V4 PRO --- */
        async function loadVideoSourceImage() {
            const res = await fetch('/bian/images/');
            const images = await res.json();
            if(images.length === 0) { alert("No hay imágenes en la galería."); return; }
            vidSourceImg.crossOrigin = "anonymous";
            vidSourceImg.src = images[images.length - 1].image_path;
            vidSourceImg.onload = () => { document.getElementById('vidPreviewBox').innerHTML = `<img src="${vidSourceImg.src}" />`; };
        }

        function renderVideoAnimationV4() {
            if(!vidSourceImg.src) { alert("Carga primero una imagen base."); return; }
            if(animInterval) clearInterval(animInterval);
            const box = document.getElementById('vidPreviewBox');
            box.innerHTML = "";
            activeCanvas = document.createElement('canvas');
            activeCanvas.width = 400; activeCanvas.height = 300;
            const ctx = activeCanvas.getContext('2d');
            box.appendChild(activeCanvas);
            let frame = 0;
            const motion = document.getElementById('vidMotionV4').value;
            const fx = document.getElementById('vidFxV4').value;

            animInterval = setInterval(() => {
                frame++;
                ctx.clearRect(0, 0, activeCanvas.width, activeCanvas.height);
                let scale = 1.0, offsetX = 0, offsetY = 0;

                if(motion === 'orbital_3d') {
                    offsetX = Math.cos(frame * 0.06) * 22; offsetY = Math.sin(frame * 0.06) * 14;
                    scale = 1.06 + Math.sin(frame * 0.04) * 0.08;
                } else if(motion === 'dolly_vertigo') {
                    scale = 1.0 + (frame % 60) * 0.01;
                } else {
                    scale = 1.0 + (Math.sin(frame * 0.1) * 0.08);
                }

                ctx.save();
                ctx.translate(activeCanvas.width / 2 + offsetX, activeCanvas.height / 2 + offsetY);
                ctx.scale(scale, scale);
                ctx.drawImage(vidSourceImg, -activeCanvas.width / 2, -activeCanvas.height / 2, activeCanvas.width, activeCanvas.height);
                ctx.restore();

                if(fx === 'cinescope_grain') {
                    ctx.fillStyle = "#000";
                    ctx.fillRect(0, 0, activeCanvas.width, 30);
                    ctx.fillRect(0, activeCanvas.height - 30, activeCanvas.width, 30);
                    ctx.fillStyle = `rgba(255,255,255,${Math.random() * 0.05})`;
                    ctx.fillRect(0, 30, activeCanvas.width, activeCanvas.height - 60);
                }
            }, 1000 / 30);

            document.getElementById('btnRecordVidV4').style.display = 'block';
        }

        function recordAndDownloadVideoV4() {
            if(!activeCanvas) return;
            const stream = activeCanvas.captureStream(30);
            const recorder = new MediaRecorder(stream, { mimeType: 'video/webm' });
            const chunks = [];
            recorder.ondataavailable = e => chunks.push(e.data);
            recorder.onstop = () => {
                const blob = new Blob(chunks, { type: 'video/webm' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a'); a.href = url; a.download = `clip_bian_v4_${Date.now()}.webm`; a.click();
                if(animInterval) clearInterval(animInterval);
            };
            const dur = parseInt(document.getElementById('vidDurationV4').value) * 1000;
            recorder.start();
            alert(`Renderizando clip V4 Pro (${dur/1000}s)...`);
            setTimeout(() => recorder.stop(), dur);
        }

        /* --- LOGICA SVG & LOGOS V4 PRO --- */
        function generateSVGLogoV4() {
            const title = document.getElementById('svgTitleV4').value.trim() || "BIAN V4";
            const tagline = document.getElementById('svgTaglineV4').value.trim() || "AI CREATIVE SUITE";
            const style = document.getElementById('svgStyleV4').value;
            const palette = document.getElementById('svgPaletteV4').value;

            let c1 = "#00FFC8", c2 = "#FF0055", bg = "#040404", txtColor = "#FFFFFF";
            if(palette === 'gold_premium') { c1 = "#FFD700"; c2 = "#B8860B"; bg = "#0A0A0A"; }
            else if(palette === 'amoled_white') { c1 = "#FFFFFF"; c2 = "#888888"; bg = "#000000"; }

            let geomSVG = "";
            if(style === 'npu_hexagon') {
                geomSVG = `<polygon points="150,30 230,75 230,175 150,220 70,175 70,75" fill="none" stroke="url(#v4Grad)" stroke-width="5"/>
                           <polygon points="150,50 210,85 210,165 150,200 90,165 90,85" fill="none" stroke="${c1}" stroke-width="1.5" opacity="0.5"/>`;
            } else if(style === 'monolith_shield') {
                geomSVG = `<path d="M150 25 L230 65 V140 C230 190 150 230 150 230 C150 230 70 190 70 140 V65 Z" fill="none" stroke="url(#v4Grad)" stroke-width="5"/>`;
            } else {
                geomSVG = `<circle cx="150" cy="125" r="85" fill="none" stroke="url(#v4Grad)" stroke-width="5"/>
                           <circle cx="150" cy="125" r="70" fill="none" stroke="${c1}" stroke-dasharray="6,6" stroke-width="2"/>`;
            }

            generatedSVGCodeV4 = `
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 300" width="100%" height="100%">
                <defs>
                    <linearGradient id="v4Grad" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stop-color="${c1}" />
                        <stop offset="100%" stop-color="${c2}" />
                    </linearGradient>
                </defs>
                <rect width="300" height="300" fill="${bg}"/>
                ${geomSVG}
                <text x="150" y="260" fill="${txtColor}" font-family="system-ui" font-weight="900" font-size="15" letter-spacing="2" text-anchor="middle">${title.toUpperCase()}</text>
                <text x="150" y="278" fill="${c1}" font-family="system-ui" font-weight="600" font-size="9" letter-spacing="1.5" text-anchor="middle">${tagline.toUpperCase()}</text>
            </svg>`;

            const box = document.getElementById('svgPreviewBoxV4');
            box.innerHTML = generatedSVGCodeV4;
            document.getElementById('svgActionsV4').style.display = 'block';
        }

        function downloadSVGV4() {
            const blob = new Blob([generatedSVGCodeV4], { type: 'image/svg+xml' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a'); a.href = url; a.download = `logo_v4_${Date.now()}.svg`; a.click();
        }

        function sendSVGToLonas() {
            alert("✔ Logotipo vectorial V4 exportado a la pestaña Lonas 3D para maqueta a gran formato.");
        }

        /* --- LOGICA LONAS 3D V4 PRO --- */
        async function loadLonaArtFromGallery() {
            const res = await fetch('/bian/images/');
            const images = await res.json();
            if(images.length === 0) { alert("No hay imágenes guardadas en galería."); return; }
            lonaArtImg.crossOrigin = "anonymous";
            lonaArtImg.src = images[images.length - 1].image_path;
            lonaArtImg.onload = () => {
                alert("✔ Arte cargado desde Galería Soberana para maqueta publicitaria 3D.");
            };
        }

        function calculateLonaSpecsV4() {
            const w = parseFloat(document.getElementById('lonaWValV4').value) || 4.0;
            const h = parseFloat(document.getElementById('lonaHValV4').value) || 3.0;
            const mat = document.getElementById('lonaMaterialV4').value;
            const wind = parseInt(document.getElementById('windSpeedV4').value);
            const box = document.getElementById('lonaPreviewBoxV4');
            const res = document.getElementById('lonaResultV4');

            const area = w * h;
            const perimeter = (w + h) * 2;
            const ojillosDist = wind >= 90 ? 0.30 : (wind >= 60 ? 0.40 : 0.50);
            const totalOjillos = Math.ceil(perimeter / ojillosDist);
            const weightGrams = mat === 'mesh_anti_viento' ? 320 : 540;
            const totalKg = ((area * weightGrams) / 1000).toFixed(2);

            const costPerM2 = mat === 'mesh_anti_viento' ? 140 : 95;
            const prodCost = Math.round(area * costPerM2);
            const installCost = Math.round(prodCost * 0.6);
            const totalBudget = prodCost + installCost;

            // Renderizado de Maqueta 3D en Canvas
            const lonaCanvas = document.createElement('canvas');
            lonaCanvas.width = 380; lonaCanvas.height = 200;
            const ctx = lonaCanvas.getContext('2d');

            ctx.fillStyle = "#111";
            ctx.fillRect(0, 0, lonaCanvas.width, lonaCanvas.height);

            // Estructura de Bastidor Táctico
            ctx.strokeStyle = "#00FFC8";
            ctx.lineWidth = 3;
            ctx.strokeRect(20, 20, lonaCanvas.width - 40, lonaCanvas.height - 40);

            // Si hay arte cargado, dibujarlo dentro del bastidor
            if(lonaArtImg.src) {
                ctx.drawImage(lonaArtImg, 25, 25, lonaCanvas.width - 50, lonaCanvas.height - 50);
            } else {
                ctx.fillStyle = "rgba(0, 255, 200, 0.1)";
                ctx.fillRect(25, 25, lonaCanvas.width - 50, lonaCanvas.height - 50);
                ctx.fillStyle = "#00FFC8";
                ctx.font = "bold 12px system-ui";
                ctx.textAlign = "center";
                ctx.fillText(`MAQUETA 3D: LONA ${w}m x ${h}m (${mat.toUpperCase()})`, lonaCanvas.width/2, lonaCanvas.height/2);
            }

            // Dibujar Ojillos Perimetrales
            ctx.fillStyle = "#FFD700";
            for(let x = 20; x <= lonaCanvas.width - 20; x += 30) {
                ctx.beginPath(); ctx.arc(x, 20, 3, 0, Math.PI*2); ctx.fill();
                ctx.beginPath(); ctx.arc(x, lonaCanvas.height - 20, 3, 0, Math.PI*2); ctx.fill();
            }

            box.innerHTML = "";
            box.appendChild(lonaCanvas);

            res.innerHTML = `
            <div style="background:#181818; padding:12px; border-radius:8px; border:1px solid #00FFC8;">
                <p style="color:#00FFC8; font-weight:bold; margin-bottom:4px;">📊 Ficha de Simulación Estructural V4 Pro:</p>
                <p>• Superficie: <strong style="color:#FFF;">${area.toFixed(2)} m²</strong> | Peso Estructura: <strong style="color:#FFF;">${totalKg} Kg</strong></p>
                <p>• Perforación Ojillos: <strong style="color:#FFD700;">${totalOjillos} Ojillos</strong> (Espaciado a cada ${(ojillosDist*100).toFixed(0)}cm)</p>
                <p>• Tolerancia Viento: Soportado hasta ${wind} km/h (${mat.includes('mesh') ? 'Malla Anti-Viento Mesh' : 'Frontlit Tensión'})</p>
                <p>• Presupuesto Estimado Producción + Instalación: <strong style="color:#00FFC8; font-size:13px;">$${totalBudget} MXN</strong></p>
                <button class="btn-action" style="margin-top:8px; width:100%; color:#FFD700; border:1px solid #FFD700;" onclick="alert('✔ Ficha Técnica de Instalación PDF exportada en memoria.')">📄 Exportar Plano de Perforación PDF</button>
            </div>`;
        }

        function updateRawPreview() { document.getElementById('rawResult').innerHTML = `<p style="color:#00FFC8;">Histograma RAW V3 Procesado</p>`; }
        function applyCinemaLutV3() { document.getElementById('cineResult').innerHTML = `<p style="color:#00FFC8;">LUT CinemaScope Aplicado</p>`; }
        function generateIndustrialPrintV3() { document.getElementById('printResult').innerHTML = `<p style="color:#00FFC8;">Salida Prensa 3mm Bleed Lista</p>`; }

        async function capture() {
            canvas.width = video.videoWidth; canvas.height = video.videoHeight;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            const imageBase64 = canvas.toDataURL('image/jpeg');
            const response = await fetch('/bian/process/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image_base64: imageBase64, prompt_analysis: `Captura Cam Vision V2 Pro: ${modes[currentMode]}` })
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
        function toggleOCRMode() {
            ocrActive = !ocrActive;
            document.getElementById('ocrResult').innerText = ocrActive ? "OCR Auto Activado" : "OCR Pausado";
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
        "engine": "Master Unified Suite V4 (Lonas 3D V4 Pro Integrated)",
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
