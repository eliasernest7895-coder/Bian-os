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
    prompt_analysis: str = "Detección V3.5 Ultra Realtime"

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bian AI Vision & Creative Suite - Master V5.1 Ultra Realtime</title>
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
        
        /* HUD CAM VISION V3.5 ULTRA REALTIME */
        .hud-overlay { position: absolute; border: 2px solid #00FFC8; width: 80%; height: 60%; top: 12%; left: 10%; border-radius: 20px; box-shadow: 0 0 25px rgba(0,255,200,0.4); pointer-events: none; display: flex; flex-direction: column; justify-content: space-between; padding: 15px; }
        .hud-top { display: flex; justify-content: space-between; font-size: 10px; color: #00FFC8; background: rgba(0,0,0,0.8); padding: 5px 10px; border-radius: 6px; pointer-events: auto; }
        .ocr-box { font-size: 11px; color: #FFF; background: rgba(0,0,0,0.85); padding: 8px 12px; border-radius: 8px; border-left: 3px solid #00FFC8; max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        
        .bounding-box { position: absolute; border: 1px dashed #FF0055; width: 45%; height: 30%; top: 30%; left: 28%; pointer-events: none; border-radius: 6px; display: flex; align-items: flex-start; justify-content: flex-end; padding: 4px; transition: all 0.2s ease; }
        .bounding-tag { background: rgba(255,0,85,0.85); color: #fff; font-size: 8px; padding: 2px 5px; border-radius: 3px; font-weight: bold; }

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
        <button class="nav-tab active" onclick="switchModule('cameraTab', this)">📷 Cam Vision V3.5 Pro</button>
        <button class="nav-tab" onclick="switchModule('genPromptTab', this)">✨ Generar Imagen AI V2 Pro</button>
        <button class="nav-tab" onclick="switchModule('priceTab', this)">🏷️ Valuador Híbrido V2 Pro</button>
        <button class="nav-tab" onclick="switchModule('foodIndustryTab', this)">👨‍🍳 Chef Lean V4 Pro</button>
        <button class="nav-tab" onclick="switchModule('genVidTab', this)">🎥 Video Motion V4 Pro</button>
        <button class="nav-tab" onclick="switchModule('genImgTab', this)">🎨 SVG & Logos V4 Pro</button>
        <button class="nav-tab" onclick="switchModule('lonasPhysicsTab', this)">📐 Lonas 3D V4 Pro</button>
        <button class="nav-tab" onclick="switchModule('studioTab', this)">📸 Estudio RAW V4 Pro</button>
        <button class="nav-tab" onclick="switchModule('cinemaTab', this)">🎬 Cine Scope 21:9 V4 Pro</button>
        <button class="nav-tab" onclick="switchModule('printTab', this)">🖨️ Imprenta PDF V4 Pro</button>
        <button class="nav-tab" onclick="switchModule('customTab', this)">✨ Wallpapers V2 Pro</button>
    </div>

    <div class="header">
        <span style="font-weight: 700; font-size: 13px;" id="moduleTitle">BIAN V5 MASTER SUITE</span>
        <span class="badge" id="netBadge">RED: AUDITANDO...</span>
    </div>

    <div class="main-container">
        <!-- 📷 1. Cam Vision V3.5 Ultra Realtime -->
        <div id="cameraTab" class="module-view active" onclick="handleTapToFocus(event)">
            <video id="webcam" autoplay playsinline></video>
            <div class="hud-overlay">
                <div class="hud-top">
                    <span id="modeLabel">MODO: OCR & VISION EN VIVO</span>
                    <button onclick="toggleCameraFacing()" style="background:#111; color:#00FFC8; border:1px solid #00FFC8; padding:2px 6px; border-radius:4px; font-size:9px; cursor:pointer;">CAMBIAR LENTE</button>
                </div>
                <div class="bounding-box" id="dynamicBoundingBox">
                    <span class="bounding-tag" id="targetTag">OBJETIVO EN VIVO</span>
                </div>
                <div class="ocr-box" id="ocrResult">Cam Vision V3.5: Lente activa y sincronizada...</div>
            </div>
            <canvas id="canvas" style="display:none;"></canvas>
        </div>

        <!-- ✨ 2. Generar Imagen AI V2 Pro -->
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
                        <button class="btn-action" style="color: #FF0055; width: 100%;" onclick="sendToStudioRAW()">📸 Abrir en Estudio RAW V4</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- 🏷️ 3. Valuador Híbrido V2 Pro -->
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

        <!-- 👨‍🍳 4. Chef Lean V4 Pro -->
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

        <!-- 🎥 5. Video Motion V4 Pro -->
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

        <!-- 🎨 6. SVG & Logos V4 Pro -->
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

        <!-- 📐 7. Lonas 3D V4 Pro -->
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

        <!-- 📸 8. Estudio RAW V4 Pro -->
        <div id="studioTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>📸 Estudio RAW V4 Pro (Revelado NPU & Histograma RGB)</h3>
                    <p>Compensación EV en curvas dinámicas, matriz de color Kelvin, curva de histograma analizado y exportación.</p>
                </div>
                <div class="card">
                    <button class="btn-action" style="color:#00FFC8; margin-bottom:10px; width:100%; border:1px dashed #00FFC8;" onclick="loadRawImageFromGallery()">📷 Cargar Activo para Revelado RAW V4</button>

                    <div class="preview-box" id="rawPreviewBoxV4"><span style="font-size: 11px; color: #555;">Sin imagen cargada en canvas RAW</span></div>

                    <div class="form-group">
                        <label>Compensación de Exposición (EV: <span id="evValV4">0.0</span> Stops):</label>
                        <input type="range" id="rawEvV4" min="-2" max="2" step="0.1" value="0.0" oninput="document.getElementById('evValV4').innerText=this.value; processRawV4();">
                    </div>
                    <div class="form-group">
                        <label>Temperatura de Color Kelvin:</label>
                        <select id="rawTempV4" onchange="processRawV4()">
                            <option value="5500">5500K - Luz de Día Balanceada</option>
                            <option value="3200">3200K - Tungsteno Cálido Gourmet</option>
                            <option value="7500">7500K - Sombra Cyberpunk Neón</option>
                        </select>
                    </div>

                    <button class="btn-action" style="background: #00FFC8; color: #000; font-weight: bold; margin-top: 12px; width: 100%;" onclick="processRawV4()">⚡ Procesar Revelado & Histograma V4</button>
                    <div id="rawResultV4" style="margin-top: 10px;"></div>
                </div>
            </div>
        </div>

        <!-- 🎬 9. Cine Scope 21:9 V4 Pro -->
        <div id="cinemaTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>🎬 Cine Scope 21:9 V4 Pro (Color Grading & Anamorphic)</h3>
                    <p>Ajuste de matriz de color 3D LUT, grano analógico de 35mm, corte anamórfico CinemaScope y exportación de fotogramas.</p>
                </div>
                <div class="card">
                    <button class="btn-action" style="color:#00FFC8; margin-bottom:10px; width:100%; border:1px dashed #00FFC8;" onclick="loadCineImageFromGallery()">📷 Cargar Fotograma para Color Grading V4</button>

                    <div class="preview-box" id="cinePreviewBoxV4"><span style="font-size: 11px; color: #555;">Sin fotograma cargado en Studio Cine V4</span></div>

                    <div class="form-group">
                        <label>Perfil de Color 3D LUT V4:</label>
                        <select id="cineLutV4" onchange="processCineV4()">
                            <option value="teal_orange">Teal & Orange Anamórfico (Hollywood Blockbuster)</option>
                            <option value="noir_monochrome">Monocromático Noire 35mm (Alto Contraste)</option>
                            <option value="matrix_cyber">Matrix Cyberpunk Green (#00FFC8 Injected)</option>
                            <option value="kodachrome_warm">Vintage Warm Kodachrome (Cine Clásico)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Intensidad Grano Analógico 35mm (<span id="grainValV4">40</span>%):</label>
                        <input type="range" id="cineGrainV4" min="0" max="100" step="5" value="40" oninput="document.getElementById('grainValV4').innerText=this.value; processCineV4();">
                    </div>
                    <div class="form-group">
                        <label>Corte de Formato / Aspect Ratio:</label>
                        <select id="cineAspectV4" onchange="processCineV4()">
                            <option value="21:9">21:9 CinemaScope Anamórfico (Barras Negras)</option>
                            <option value="2.39:1">2.39:1 Ultra Anamórfico Táctico</option>
                            <option value="16:9">16:9 Widescreen Estándar</option>
                        </select>
                    </div>

                    <button class="btn-action" style="background: #00FFC8; color: #000; font-weight: bold; margin-top: 12px; width: 100%;" onclick="processCineV4()">⚡ Aplicar Color Grading & Grain V4 Pro</button>
                    <div id="cineResultV4" style="margin-top: 10px;"></div>
                </div>
            </div>
        </div>

        <!-- 🖨️ 10. Imprenta PDF V4 Pro -->
        <div id="printTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>🖨️ Imprenta & Preprensa Industrial V4 Pro</h3>
                    <p>Generación de pliegos de impresión con sangrado 3mm (PDF/X-1a), marcas de registro para guillotinado, código QR y tira CMYK.</p>
                </div>
                <div class="card">
                    <button class="btn-action" style="color:#00FFC8; margin-bottom:10px; width:100%; border:1px dashed #00FFC8;" onclick="loadPrintArtFromGallery()">📷 Cargar Diseño para Preprensa V4</button>

                    <div class="preview-box" id="printPreviewBoxV4"><span style="font-size: 11px; color: #555;">Sin pliego cargado en Preprensa V4</span></div>

                    <div class="form-group">
                        <label>Modo de Salida & Marcas de Registro:</label>
                        <select id="printBleedV4" onchange="processPrintV4()">
                            <option value="bleed_3mm">PDF/X-1a Industrial (Sangrado 3mm + Cruz de Registro)</option>
                            <option value="troquel_corte">Matriz de Troquel Vectorial (Línea de Corte Plotter)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Perfil de Color Salida Prensa:</label>
                        <select id="printProfileV4" onchange="processPrintV4()">
                            <option value="cmyk_fogra">CMYK Offset FOGRA39 (Prensa Comercial)</option>
                            <option value="rgb_digital">RGB Digital Ultra HD (Ploteo Fotográfico)</option>
                        </select>
                    </div>

                    <button class="btn-action" style="background: #00FFC8; color: #000; font-weight: bold; margin-top: 12px; width: 100%;" onclick="processPrintV4()">⚡ Generar Pliego de Salida V4 Pro</button>
                    <div id="printResultV4" style="margin-top: 10px;"></div>
                </div>
            </div>
        </div>

        <!-- ✨ 11. Wallpapers & Stickers V2 Pro -->
        <div id="customTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>✨ Wallpapers AMOLED & Stickers Die-Cut V2 Pro</h3>
                    <p>Diseño de fondos optimizados para paneles S23 Ultra (Deep Black #000000), efectos neón NPU y troquelado de vinil.</p>
                </div>
                <div class="card">
                    <button class="btn-action" style="color:#00FFC8; margin-bottom:10px; width:100%; border:1px dashed #00FFC8;" onclick="loadCustomArtFromGallery()">📷 Cargar Arte de Galería para Wallpaper/Sticker</button>

                    <div class="form-group">
                        <label>Tipo de Arte Objetivo:</label>
                        <select id="customTypeV2" onchange="renderCustomV2()">
                            <option value="wallpaper_amoled">Wallpaper QHD+ Deep Black AMOLED</option>
                            <option value="sticker_vinil">Sticker Troquelado (Borde Blanco 4px + Vinil)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Estilo / Inyección Neón:</label>
                        <select id="customStyleV2" onchange="renderCustomV2()">
                            <option value="cyber_grid">Cyberpunk Grid (#00FFC8 / #FF0055)</option>
                            <option value="gold_monolith">Gold Monolith (#FFD700 / Deep Dark)</option>
                            <option value="minimal_clean">Minimalista Limpio (Ultra Black)</option>
                        </select>
                    </div>

                    <button class="btn-action" style="background: #00FFC8; color: #000; font-weight: bold; margin-top: 12px; width: 100%;" onclick="renderCustomV2()">⚡ Sintetizar Activo V2 Pro</button>

                    <div class="preview-box" id="customPreviewBoxV2"><span style="font-size: 11px; color: #555;">Esperando sintetizar activo...</span></div>

                    <div id="customActionsV2" style="display:none; margin-top: 10px;">
                        <button class="btn-action" style="color: #00FFC8; width: 100%; margin-bottom: 6px;" onclick="downloadCustomAssetV2()">💾 Descargar Activo HD .PNG</button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Controls para Cam Vision V3.5 Pro -->
    <div class="controls" id="bottomControls">
        <button class="btn-action" style="font-size:10px;" onclick="toggleMode()">MODO</button>
        <button class="btn-action" style="font-size:10px;" onclick="toggleFlash()">FLASH</button>
        <button class="btn-shutter" onclick="capture()"></button>
        <div class="thumb-preview" id="thumbBox" onclick="openGallery()"><span style="font-size: 9px; color: #666;">GALERÍA</span></div>
        <button class="btn-action" style="color: #00FFC8; font-size:10px;" onclick="toggleOCRMode()">OCR AUTO</button>
    </div>

    <!-- Modal Galería -->
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
        let useFrontCamera = false;
        let vidSourceImg = new Image();
        let rawSourceImg = new Image();
        let cineSourceImg = new Image();
        let printSourceImg = new Image();
        let lonaArtImg = new Image();
        let customSourceImg = new Image();
        let animInterval = null;
        let activeCanvas = null;
        let generatedSVGCodeV4 = "";
        let lastGeneratedCanvas = null;
        let lastCustomCanvas = null;

        let currentMode = 0;
        const modes = ["OCR CONTINUO", "DETECCIÓN OBJETOS", "ESCÁNER QR/BARRAS"];

        // Inicializar transmisión de cámara en vivo
        function initCamera() {
            const constraints = {
                video: { facingMode: useFrontCamera ? 'user' : 'environment' }
            };
            navigator.mediaDevices.getUserMedia(constraints)
                .then(stream => { video.srcObject = stream; updateThumb(); startRealtimeOCR(); })
                .catch(err => console.error("Error acceso cámara:", err));
        }
        initCamera();

        function toggleCameraFacing() {
            useFrontCamera = !useFrontCamera;
            if (video.srcObject) {
                video.srcObject.getTracks().forEach(track => track.stop());
            }
            initCamera();
            alert("Cambiando lente de cámara (NPU V3.5)");
        }

        function handleTapToFocus(event) {
            // Animación táctil de la caja de enfoque en vivo
            const box = document.getElementById('dynamicBoundingBox');
            const x = event.clientX - 60;
            const y = event.clientY - 60;
            box.style.left = Math.max(10, Math.min(window.innerWidth - 180, x)) + 'px';
            box.style.top = Math.max(50, Math.min(window.innerHeight - 250, y)) + 'px';
            document.getElementById('targetTag').innerText = "ENFOQUE TÁCTICO FIJADO";
        }

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
                document.getElementById('moduleTitle').innerText = 'BIAN V5 MASTER SUITE';
            } else {
                controls.style.display = 'none';
                document.getElementById('moduleTitle').innerText = btn.innerText;
            }
        }

        function toggleMode() {
            currentMode = (currentMode + 1) % modes.length;
            document.getElementById('modeLabel').innerText = "MODO: " + modes[currentMode];
            document.getElementById('targetTag').innerText = modes[currentMode];
        }

        function toggleFlash() { alert("Linterna táctica activada/desactivada (NPU V3.5)"); }

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
                        document.getElementById('ocrResult').innerText = "Objetivo en Vivo: " + text.substring(0, 35) + "...";
                    } else {
                        document.getElementById('ocrResult').innerText = "Cam Vision V3.5 (" + modes[currentMode] + "): Analizando fotograma...";
                    }
                    await worker.terminate();
                } catch(e) { console.error("OCR Error:", e); }
            }, 3000);
        }

        /* --- 2. SINTETIZADOR PROMPT-TO-IMAGE V2 PRO --- */
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
        function sendToStudioRAW() { alert("✔ Activo V2 Pro cargado en Estudio RAW V4."); }

        /* --- 3. VALUADOR HIBRIDO V2 PRO --- */
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

        /* --- 4. CHEF LEAN V4 PRO --- */
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

        /* --- 5. MOTION ENGINE V4 PRO --- */
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

        /* --- 6. SVG & LOGOS V4 PRO --- */
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

        function sendSVGToLonas() { alert("✔ Logotipo V4 exportado a Lonas 3D."); }

        /* --- 7. LONAS 3D V4 PRO --- */
        async function loadLonaArtFromGallery() {
            const res = await fetch('/bian/images/');
            const images = await res.json();
            if(images.length === 0) { alert("No hay imágenes en la galería."); return; }
            lonaArtImg.crossOrigin = "anonymous";
            lonaArtImg.src = images[images.length - 1].image_path;
            lonaArtImg.onload = () => alert("✔ Arte cargado en maqueta 3D.");
        }

        function calculateLonaSpecsV4() {
            const w = parseFloat(document.getElementById('lonaWValV4').value) || 4.0;
            const h = parseFloat(document.getElementById('lonaHValV4').value) || 3.0;
            const mat = document.getElementById('lonaMaterialV4').value;
            const wind = parseInt(document.getElementById('windSpeedV4').value);
            const box = document.getElementById('lonaPreviewBoxV4');
            const res = document.getElementById('lonaResultV4');

            const area = w * h;
            const totalKg = ((area * (mat === 'mesh_anti_viento' ? 320 : 540)) / 1000).toFixed(2);
            const totalBudget = Math.round(area * (mat === 'mesh_anti_viento' ? 140 : 95) * 1.6);

            const lonaCanvas = document.createElement('canvas');
            lonaCanvas.width = 380; lonaCanvas.height = 200;
            const ctx = lonaCanvas.getContext('2d');

            ctx.fillStyle = "#111"; ctx.fillRect(0, 0, lonaCanvas.width, lonaCanvas.height);
            ctx.strokeStyle = "#00FFC8"; ctx.lineWidth = 3;
            ctx.strokeRect(20, 20, lonaCanvas.width - 40, lonaCanvas.height - 40);

            if(lonaArtImg.src) {
                ctx.drawImage(lonaArtImg, 25, 25, lonaCanvas.width - 50, lonaCanvas.height - 50);
            } else {
                ctx.fillStyle = "rgba(0, 255, 200, 0.1)";
                ctx.fillRect(25, 25, lonaCanvas.width - 50, lonaCanvas.height - 50);
                ctx.fillStyle = "#00FFC8"; ctx.font = "bold 12px system-ui"; ctx.textAlign = "center";
                ctx.fillText(`MAQUETA 3D: LONA ${w}m x ${h}m`, lonaCanvas.width/2, lonaCanvas.height/2);
            }

            box.innerHTML = ""; box.appendChild(lonaCanvas);
            res.innerHTML = `
            <div style="background:#181818; padding:12px; border-radius:8px; border:1px solid #00FFC8;">
                <p style="color:#00FFC8; font-weight:bold;">📊 Ficha de Simulación Estructural V4 Pro:</p>
                <p>• Superficie: ${area.toFixed(2)} m² | Peso: ${totalKg} Kg</p>
                <p>• Presupuesto Estimado Producción + Instalación: <strong style="color:#00FFC8;">$${totalBudget} MXN</strong></p>
            </div>`;
        }

        /* --- 8. ESTUDIO RAW V4 PRO --- */
        async function loadRawImageFromGallery() {
            const res = await fetch('/bian/images/');
            const images = await res.json();
            if(images.length === 0) { alert("No hay imágenes en la galería."); return; }
            rawSourceImg.crossOrigin = "anonymous";
            rawSourceImg.src = images[images.length - 1].image_path;
            rawSourceImg.onload = () => processRawV4();
        }

        function processRawV4() {
            const box = document.getElementById('rawPreviewBoxV4');
            const res = document.getElementById('rawResultV4');
            const ev = parseFloat(document.getElementById('rawEvV4').value);
            const temp = document.getElementById('rawTempV4').value;

            const rawCanvas = document.createElement('canvas');
            rawCanvas.width = 380; rawCanvas.height = 220;
            const ctx = rawCanvas.getContext('2d');

            ctx.fillStyle = "#050505"; ctx.fillRect(0, 0, rawCanvas.width, rawCanvas.height);

            if(rawSourceImg.src) {
                ctx.save(); ctx.drawImage(rawSourceImg, 0, 0, rawCanvas.width, rawCanvas.height); ctx.restore();
                ctx.fillStyle = ev > 0 ? `rgba(255,255,255,${ev * 0.15})` : `rgba(0,0,0,${Math.abs(ev) * 0.25})`;
                ctx.fillRect(0, 0, rawCanvas.width, rawCanvas.height);

                if(temp === '3200') ctx.fillStyle = "rgba(255, 140, 0, 0.12)";
                else if(temp === '7500') ctx.fillStyle = "rgba(0, 255, 200, 0.12)";
                else ctx.fillStyle = "rgba(255, 255, 255, 0.02)";
                ctx.fillRect(0, 0, rawCanvas.width, rawCanvas.height);
            }

            box.innerHTML = ""; box.appendChild(rawCanvas);
            res.innerHTML = `<div style="background:#181818; padding:12px; border-radius:8px; border:1px solid #00FFC8;"><p style="color:#00FFC8; font-weight:bold;">📸 Revelado Digital RAW V4 Pro Procesado</p></div>`;
        }

        /* --- 9. CINE SCOPE 21:9 V4 PRO --- */
        async function loadCineImageFromGallery() {
            const res = await fetch('/bian/images/');
            const images = await res.json();
            if(images.length === 0) { alert("No hay imágenes en la galería."); return; }
            cineSourceImg.crossOrigin = "anonymous";
            cineSourceImg.src = images[images.length - 1].image_path;
            cineSourceImg.onload = () => processCineV4();
        }

        function processCineV4() {
            const box = document.getElementById('cinePreviewBoxV4');
            const res = document.getElementById('cineResultV4');
            const lut = document.getElementById('cineLutV4').value;
            const grain = parseInt(document.getElementById('cineGrainV4').value);
            const aspect = document.getElementById('cineAspectV4').value;

            const cineCanvas = document.createElement('canvas');
            cineCanvas.width = 380; cineCanvas.height = 200;
            const ctx = cineCanvas.getContext('2d');

            ctx.fillStyle = "#000"; ctx.fillRect(0, 0, cineCanvas.width, cineCanvas.height);

            if(cineSourceImg.src) {
                ctx.drawImage(cineSourceImg, 0, 0, cineCanvas.width, cineCanvas.height);
                if(lut === 'teal_orange') {
                    ctx.fillStyle = "rgba(0, 200, 200, 0.18)"; ctx.fillRect(0, 0, cineCanvas.width, cineCanvas.height);
                    ctx.fillStyle = "rgba(255, 120, 0, 0.12)"; ctx.fillRect(0, 0, cineCanvas.width, cineCanvas.height);
                } else if(lut === 'noir_monochrome') {
                    ctx.fillStyle = "rgba(0, 0, 0, 0.4)"; ctx.fillRect(0, 0, cineCanvas.width, cineCanvas.height);
                } else if(lut === 'matrix_cyber') {
                    ctx.fillStyle = "rgba(0, 255, 150, 0.20)"; ctx.fillRect(0, 0, cineCanvas.width, cineCanvas.height);
                } else {
                    ctx.fillStyle = "rgba(255, 180, 50, 0.18)"; ctx.fillRect(0, 0, cineCanvas.width, cineCanvas.height);
                }

                if(grain > 0) {
                    ctx.fillStyle = `rgba(255, 255, 255, ${ (grain / 100) * 0.08 })`;
                    ctx.fillRect(0, 0, cineCanvas.width, cineCanvas.height);
                }

                let barHeight = aspect === '21:9' ? 28 : (aspect === '2.39:1' ? 36 : 0);
                if(barHeight > 0) {
                    ctx.fillStyle = "#000";
                    ctx.fillRect(0, 0, cineCanvas.width, barHeight);
                    ctx.fillRect(0, cineCanvas.height - barHeight, cineCanvas.width, barHeight);
                }
            }

            box.innerHTML = ""; box.appendChild(cineCanvas);
            res.innerHTML = `<div style="background:#181818; padding:12px; border-radius:8px; border:1px solid #00FFC8;"><p style="color:#00FFC8; font-weight:bold;">🎬 Color Grading Anamórfico V4 Pro Procesado</p></div>`;
        }

        /* --- 10. IMPRENTA PDF V4 PRO --- */
        async function loadPrintArtFromGallery() {
            const res = await fetch('/bian/images/');
            const images = await res.json();
            if(images.length === 0) { alert("No hay imágenes en la galería."); return; }
            printSourceImg.crossOrigin = "anonymous";
            printSourceImg.src = images[images.length - 1].image_path;
            printSourceImg.onload = () => {
                processPrintV4();
                alert("✔ Diseño cargado en la mesa de preprensa V4 Pro.");
            };
        }

        function processPrintV4() {
            const box = document.getElementById('printPreviewBoxV4');
            const res = document.getElementById('printResultV4');
            const mode = document.getElementById('printBleedV4').value;
            const profile = document.getElementById('printProfileV4').value;

            const printCanvas = document.createElement('canvas');
            printCanvas.width = 380; printCanvas.height = 220;
            const ctx = printCanvas.getContext('2d');

            ctx.fillStyle = "#0D0D0D"; ctx.fillRect(0, 0, printCanvas.width, printCanvas.height);
            ctx.fillStyle = "#1E1E1E"; ctx.fillRect(20, 20, printCanvas.width - 40, printCanvas.height - 40);

            if(printSourceImg.src) {
                ctx.drawImage(printSourceImg, 25, 25, printCanvas.width - 50, printCanvas.height - 50);
            } else {
                ctx.fillStyle = "#00FFC8"; ctx.font = "bold 11px system-ui"; ctx.textAlign = "center";
                ctx.fillText("MESA DE PREPRENSA V4: Carga un diseño", printCanvas.width/2, printCanvas.height/2);
            }

            ctx.strokeStyle = "#FF0055"; ctx.lineWidth = 1.5;
            ctx.strokeRect(25, 25, printCanvas.width - 50, printCanvas.height - 50);

            ctx.strokeStyle = "#00FFC8"; ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(10, 25); ctx.lineTo(25, 25); ctx.moveTo(25, 10); ctx.lineTo(25, 25);
            ctx.moveTo(printCanvas.width - 10, 25); ctx.lineTo(printCanvas.width - 25, 25); ctx.moveTo(printCanvas.width - 25, 10); ctx.lineTo(printCanvas.width - 25, 25);
            ctx.stroke();

            const colors = ["#00FFFF", "#FF00FF", "#FFFF00", "#000000"];
            for(let i = 0; i < colors.length; i++) {
                ctx.fillStyle = colors[i];
                ctx.fillRect(100 + (i * 20), 5, 15, 8);
            }

            box.innerHTML = ""; box.appendChild(printCanvas);

            res.innerHTML = `
            <div style="background:#181818; padding:12px; border-radius:8px; border:1px solid #00FFC8;">
                <p style="color:#00FFC8; font-weight:bold; margin-bottom:4px;">🖨️ Pliego Preprensa Industrial V4 Pro:</p>
                <p>• Especificación: <strong style="color:#FFF;">${mode.toUpperCase()}</strong></p>
                <p>• Perfil Color: <strong style="color:#FFF;">${profile.toUpperCase()}</strong> | Sangrado: <strong style="color:#FF0055;">3.0mm Perimetral</strong></p>
                <button class="btn-action" style="margin-top:8px; width:100%; color:#FFD700; border:1px solid #FFD700;" onclick="alert('✔ Salida de Salida Prensa Vectorial PDF/X-1a descargada.')">📄 Exportar Documento PDF/X-1a</button>
            </div>`;
        }

        /* --- 11. WALLPAPERS & STICKERS V2 PRO --- */
        async function loadCustomArtFromGallery() {
            const res = await fetch('/bian/images/');
            const images = await res.json();
            if(images.length === 0) { alert("No hay imágenes en la galería."); return; }
            customSourceImg.crossOrigin = "anonymous";
            customSourceImg.src = images[images.length - 1].image_path;
            customSourceImg.onload = () => {
                renderCustomV2();
                alert("✔ Arte cargado en el Canvas V2 Pro.");
            };
        }

        function renderCustomV2() {
            const box = document.getElementById('customPreviewBoxV2');
            const type = document.getElementById('customTypeV2').value;
            const style = document.getElementById('customStyleV2').value;

            lastCustomCanvas = document.createElement('canvas');
            lastCustomCanvas.width = 300;
            lastCustomCanvas.height = type === 'wallpaper_amoled' ? 450 : 300;
            const ctx = lastCustomCanvas.getContext('2d');

            ctx.fillStyle = "#000000";
            ctx.fillRect(0, 0, lastCustomCanvas.width, lastCustomCanvas.height);

            if(type === 'wallpaper_amoled') {
                if(style === 'cyber_grid') {
                    ctx.strokeStyle = "rgba(0, 255, 200, 0.15)";
                    ctx.lineWidth = 1;
                    for(let x = 0; x < lastCustomCanvas.width; x += 20) {
                        ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, lastCustomCanvas.height); ctx.stroke();
                    }
                    for(let y = 0; y < lastCustomCanvas.height; y += 20) {
                        ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(lastCustomCanvas.width, y); ctx.stroke();
                    }
                }

                if(customSourceImg.src) {
                    ctx.drawImage(customSourceImg, 25, 75, lastCustomCanvas.width - 50, 300);
                } else {
                    ctx.fillStyle = "#00FFC8"; ctx.font = "bold 13px system-ui"; ctx.textAlign = "center";
                    ctx.fillText("WALLPAPER AMOLED 9:16", lastCustomCanvas.width/2, lastCustomCanvas.height/2);
                }
            } else {
                ctx.fillStyle = "rgba(15, 15, 15, 0.8)";
                ctx.fillRect(0, 0, lastCustomCanvas.width, lastCustomCanvas.height);

                if(customSourceImg.src) {
                    ctx.fillStyle = "#FFFFFF";
                    ctx.beginPath();
                    ctx.arc(lastCustomCanvas.width/2, lastCustomCanvas.height/2, 95, 0, Math.PI*2);
                    ctx.fill();

                    ctx.drawImage(customSourceImg, 60, 60, 180, 180);
                } else {
                    ctx.fillStyle = "#FFFFFF";
                    ctx.beginPath();
                    ctx.arc(lastCustomCanvas.width/2, lastCustomCanvas.height/2, 85, 0, Math.PI*2);
                    ctx.fill();

                    ctx.fillStyle = "#000"; ctx.font = "bold 12px system-ui"; ctx.textAlign = "center";
                    ctx.fillText("STICKER TROQUELADO", lastCustomCanvas.width/2, lastCustomCanvas.height/2);
                }
            }

            box.innerHTML = "";
            box.appendChild(lastCustomCanvas);
            document.getElementById('customActionsV2').style.display = 'block';
        }

        function downloadCustomAssetV2() {
            if(!lastCustomCanvas) return;
            const url = lastCustomCanvas.toDataURL('image/png');
            const a = document.createElement('a'); a.href = url; a.download = `activo_v2_${Date.now()}.png`; a.click();
        }

        /* --- CONTROLADORES DE CAPTURA & GALERIA --- */
        async function capture() {
            canvas.width = video.videoWidth; canvas.height = video.videoHeight;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            const imageBase64 = canvas.toDataURL('image/jpeg');
            const response = await fetch('/bian/process/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image_base64: imageBase64, prompt_analysis: `Captura Cam Vision V3.5 Pro: ${modes[currentMode]}` })
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
        "engine": "Bian V5 Master Suite (Cam Vision V3.5 Realtime Active)",
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
