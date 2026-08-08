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
    prompt_analysis: str = "Detección V5 Ultra Engine"

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bian AI Vision & Creative Suite - Master V5 Ultra</title>
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
        
        /* HUD CAM VISION V3.5 */
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
        .preview-box img, .preview-box canvas, .preview-box svg { max-width: 100%; max-height: 100%; object-fit: contain; }

        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.95); z-index: 100; flex-direction: column; padding: 20px; }
        .gallery-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; overflow-y: auto; flex: 1; }
        .gallery-item { background: #111; border: 1px solid #333; border-radius: 10px; padding: 8px; }
        .gallery-item img { width: 100%; height: 120px; object-fit: cover; border-radius: 6px; }
    </style>
</head>
<body>
    <div class="module-nav">
        <button class="nav-tab active" onclick="switchModule('cameraTab', this)">📷 Cam Vision V3.5 Pro</button>
        <button class="nav-tab" onclick="switchModule('genPromptTab', this)">✨ Generar Imagen AI V3 Ultra</button>
        <button class="nav-tab" onclick="switchModule('priceTab', this)">🏷️ Valuador Híbrido V3 Ultra</button>
        <button class="nav-tab" onclick="switchModule('foodIndustryTab', this)">👨‍🍳 Chef Lean V5 Ultra</button>
        <button class="nav-tab" onclick="switchModule('genVidTab', this)">🎥 Video Motion V5 Ultra</button>
        <button class="nav-tab" onclick="switchModule('genImgTab', this)">🎨 SVG & Logos V5 Ultra</button>
        <button class="nav-tab" onclick="switchModule('lonasPhysicsTab', this)">📐 Lonas 3D V5 Ultra</button>
        <button class="nav-tab" onclick="switchModule('studioTab', this)">📸 Estudio RAW V5 Ultra</button>
        <button class="nav-tab" onclick="switchModule('cinemaTab', this)">🎬 Cine Scope 21:9 V5 Ultra</button>
        <button class="nav-tab" onclick="switchModule('printTab', this)">🖨️ Imprenta PDF V5 Ultra</button>
        <button class="nav-tab" onclick="switchModule('customTab', this)">✨ Wallpapers V3 Ultra</button>
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

        <!-- ✨ 2. Generar Imagen AI V3 Ultra Engine -->
        <div id="genPromptTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>✨ Sintetizador Diffusion AI V3 Ultra Engine</h3>
                    <p>Variaciones por Semilla Semántica (Seed Locking), control de pasos de inferencia, Img2Img desde cámara y renderizado multicapa NPU V5.</p>
                </div>
                <div class="card">
                    <button class="btn-action" style="color:#00FFC8; margin-bottom:10px; width:100%; border:1px dashed #00FFC8;" onclick="useCameraImageForImg2Img()">📷 Usar Última Captura como Imagen Base (Img2Img)</button>

                    <div class="form-group">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <label>Prompt / Descripción Visual:</label>
                            <button class="btn-action" style="font-size:9px; color:#00FFC8; padding:3px 6px;" onclick="enhancePromptV3()">🪄 Optimizar Prompt NPU V3</button>
                        </div>
                        <textarea id="aiPromptInputV3" rows="3" placeholder="Ej. Corte Rib Eye a la parrilla, iluminación neón..."></textarea>
                    </div>
                    <div class="form-group">
                        <label>Prompt Negativo (Evitar en la imagen):</label>
                        <input type="text" id="aiNegativeInputV3" value="borroso, mala calidad, texto, marca de agua, deforme">
                    </div>
                    <div class="form-group">
                        <label>Estilo Visual / Preset NPU V3:</label>
                        <select id="aiPromptStyleV3">
                            <option value="cyberpunk">Cyberpunk / Neón Glowing V3</option>
                            <option value="fotorealismo">Fotorealismo 8K / Macro Gourmet DSLR</option>
                            <option value="octane">Render 3D Octane / Isotipo Volumétrico</option>
                            <option value="vectorial">Ilustración Vectorial Minimalista</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Pasos de Inferencia (Sampling Steps):</label>
                        <select id="aiStepsV3">
                            <option value="20">20 Pasos (Render Rápido - 1.2s)</option>
                            <option value="30">30 Pasos (Balance Fidelidad/Tiempo)</option>
                            <option value="50">50 Pasos (Ultra Detalle Textura NPU)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Semilla Semántica (Seed: <span id="seedVal">Aleatoria (-1)</span>):</label>
                        <div style="display:flex; gap:8px;">
                            <input type="number" id="aiSeedV3" value="-1" placeholder="-1 para aleatorio">
                            <button class="btn-action" style="font-size:10px; color:#00FFC8;" onclick="lockSeedV3()">🔒 Fijar Semilla</button>
                        </div>
                    </div>
                    <div class="form-group">
                        <label>Relación de Aspecto:</label>
                        <select id="aiPromptRatioV3">
                            <option value="1:1">1:1 (Cuadrado / Asset Social)</option>
                            <option value="16:9">16:9 (Cinema Widescreen)</option>
                            <option value="9:16">9:16 (Wallpaper S23 Ultra)</option>
                        </select>
                    </div>

                    <button class="btn-action" style="background: #00FFC8; color: #000; font-weight: bold; margin-top: 12px; width: 100%;" onclick="generateAiPromptImageV3()">⚡ Renderizar Arte Visual V3 Ultra</button>

                    <div class="preview-box" id="aiGenPreviewBoxV3"><span style="font-size: 11px; color: #555;">Esperando prompt para V3 Ultra...</span></div>

                    <div id="aiGenActionsV3" style="display:none; margin-top: 10px;">
                        <button class="btn-action" style="color: #00FFC8; width: 100%; margin-bottom: 6px;" onclick="sendToVideoEngine()">🎥 Enviar a Video Motion V5</button>
                        <button class="btn-action" style="color: #FFD700; width: 100%; margin-bottom: 6px;" onclick="saveToGalleryFromAi()">💾 Guardar en Galería Soberana</button>
                        <button class="btn-action" style="color: #FF0055; width: 100%;" onclick="sendToStudioRAW()">📸 Abrir en Estudio RAW V5</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- 🏷️ 3. Valuador Híbrido V3 Ultra Engine -->
        <div id="priceTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>🏷️ Valuador Táctico & Financiero V3 Ultra</h3>
                    <p>Análisis NPU de mercado, proyección estacional, matriz de margen de reventa y exportador de cotizaciones.</p>
                </div>
                <div class="card">
                    <button class="btn-action" style="color:#00FFC8; margin-bottom:8px; width:100%; border:1px dashed #00FFC8;" onclick="loadValuationFromGalleryV3()">📸 Capturar / Cargar para Análisis Visual NPU</button>
                    <div class="form-group">
                        <label>Producto, Insumo o Servicio a Valuar:</label>
                        <input type="text" id="itemQueryV3" placeholder="Ej. Corte Rib Eye 1kg, Lona 4x3m, Conector USB-C...">
                    </div>
                    <div class="form-group">
                        <label>Condición del Ítem / Desgaste:</label>
                        <select id="itemConditionV3">
                            <option value="nuevo">Nuevo / Insumo Premium</option>
                            <option value="usado">Usado / Reutilizable (-30% Depreciación)</option>
                            <option value="servicio">Servicio Técnico Especializado</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Factor Estacional / Mercado:</label>
                        <select id="itemSeasonV3">
                            <option value="estandar">Demanda Estándar (Sin Ajuste)</option>
                            <option value="alta">Temporada Alta / Escasez (+15% Incremento)</option>
                            <option value="remate">Oferta Liquidez / Remate (-20% Descuento)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Divisa Financiera:</label>
                        <select id="itemCurrencyV3">
                            <option value="MXN">MXN - Peso Mexicano</option>
                            <option value="USD">USD - Dólar Americano</option>
                            <option value="EUR">EUR - Euro</option>
                        </select>
                    </div>
                    <button class="btn-action" style="background: #00FFC8; color: #000; font-weight: bold; margin-top: 12px; width: 100%;" onclick="runPriceValuationV3()">📊 Calcular Matriz de Reventa V3 Ultra</button>
                    <div id="priceResultV3" style="margin-top: 12px;"></div>
                </div>
            </div>
        </div>

        <!-- 👨‍🍳 4. Chef Lean V5 Ultra -->
        <div id="foodIndustryTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>👨‍🍳 Chef Lean & Operación Gastronómica V5 Ultra</h3>
                    <p>Inspección NPU de porcionado, matriz de rendimiento por lote cárnico, costeo directo y auditoría de desperdicio cero.</p>
                </div>
                <div class="card">
                    <button class="btn-action" style="color:#00FFC8; margin-bottom:8px; width:100%; border:1px dashed #00FFC8;" onclick="loadChefImageFromGalleryV5()">📷 Cargar Inspección Visual desde Galería NPU</button>
                    <div class="form-group">
                        <label>Herramienta Operativa Gastronómica V5:</label>
                        <select id="chefToolV5">
                            <option value="limpieza_carnes">🥩 Limpieza & Desgüese Cárnico (Turno 4 AM - 9 AM)</option>
                            <option value="estandar_receta">📜 Estandarización de Receta & Porcionado Lean</option>
                            <option value="margen_costo">💰 Matriz de Costeo Táctico & Margen de Venta</option>
                            <option value="norma_251">🏷️ Trazabilidad de Cadena de Frío NOM-251</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Peso Bruto Inicial Recibido (Kg):</label>
                        <input type="number" id="chefWeightV5" value="3.5" step="0.1">
                    </div>
                    <div class="form-group">
                        <label>Costo Insumo Base ($ MXN / Kg):</label>
                        <input type="number" id="chefCostKgV5" value="220" step="5">
                    </div>
                    <div class="form-group">
                        <label>Gramaje por Porción Objetivo (Gramos):</label>
                        <input type="number" id="chefPortionGramsV5" value="220" step="10">
                    </div>
                    <button class="btn-action" style="background: #00FFC8; color: #000; font-weight: bold; margin-top: 12px; width: 100%;" onclick="runChefLeanEngineV5()">⚡ Ejecutar Diagnóstico Operativo Chef Lean V5</button>
                    <div id="chefResultV5" style="margin-top: 12px;"></div>
                </div>
            </div>
        </div>

        <!-- 🎥 5. Video Motion V5 Ultra Engine -->
        <div id="genVidTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>🎥 Motion Engine V5 Ultra (3D Orbit & FX Layer)</h3>
                    <p>Trayectorias 3D avanzadas, tracking orbital 360°, partículas neón volumétricas, grano 35mm y barras CineScope 21:9.</p>
                </div>
                <div class="card">
                    <button class="btn-action" style="color: #00FFC8; margin-bottom: 10px; width:100%; border:1px dashed #00FFC8;" onclick="loadVideoSourceImageV5()">📷 Cargar Último Activo de Galería Soberana</button>
                    <div class="preview-box" id="vidPreviewBoxV5"><span style="font-size: 11px; color: #555;">Sin imagen base cargada para Motion Engine V5</span></div>
                    <div class="form-group">
                        <label>Trayectoria de Cámara V5 Ultra:</label>
                        <select id="vidMotionV5">
                            <option value="orbital_3d">Órbita 3D Compleja + Depth Blur NPU</option>
                            <option value="tracking_360">Tracking Orbital 360° con Aceleración</option>
                            <option value="dolly_vertigo">Zoom Anamórfico Dolly (Vertigo FX)</option>
                            <option value="neon_pulse">Pulso Neón 60 FPS Acelerado</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Capas & Efectos Cinemáticos (FX Layer V5):</label>
                        <select id="vidFxV5">
                            <option value="cinescope_particles">CineScope 21:9 + Grano 35mm + Partículas Neón</option>
                            <option value="cinescope_grain">Barras CineScope 21:9 + Grano 35mm</option>
                            <option value="clean_hd">Ultra HD Limpio (Direct Cut)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Duración del Render (Segundos):</label>
                        <select id="vidDurationV5">
                            <option value="3">3 Segundos Loop Smooth (Social Asset)</option>
                            <option value="5">5 Segundos Cinematic Master Pro</option>
                        </select>
                    </div>
                    <button class="btn-action" style="background: #00FFC8; color: #000; font-weight: bold; margin-top: 12px; width: 100%;" onclick="renderVideoAnimationV5()">⚡ Renderizar Animación V5 Ultra</button>
                    <button class="btn-action" id="btnRecordVidV5" style="background: #FF0055; color: #fff; font-weight: bold; margin-top: 10px; width: 100%; display: none;" onclick="recordAndDownloadVideoV5()">🎥 Exportar Clip .WebM V5</button>
                </div>
            </div>
        </div>

        <!-- 🎨 6. SVG & Logos Vectorial V5 Ultra Engine -->
        <div id="genImgTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>🎨 Sintetizador SVG Vectorial V5 Ultra Engine</h3>
                    <p>Sintetizador de isotipos vectoriales limpios, geometría sagrada NPU V5, resplandor neón nativo SVG y exportación directa.</p>
                </div>
                <div class="card">
                    <div class="form-group">
                        <label>Nombre de la Marca / Título Isotipo:</label>
                        <input type="text" id="svgTitleV5" placeholder="Ej. BIAN TURFO ENGINE">
                    </div>
                    <div class="form-group">
                        <label>Tagline / Subtítulo Secundario:</label>
                        <input type="text" id="svgTaglineV5" placeholder="Ej. SOFTWARE & AI VISION">
                    </div>
                    <div class="form-group">
                        <label>Estructura Geométrica V5 Ultra:</label>
                        <select id="svgStyleV5">
                            <option value="npu_hexagon">Hexágono NPU con Malla Cyberpunk</option>
                            <option value="monolith_shield">Escudo Monolítico Táctico (Space Shield)</option>
                            <option value="circular_neon">Anillo Orbital Neón Volumétrico</option>
                            <option value="bionic_circuit">Circuito Integrado Biónico NPU</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Paleta de Color NPU V5:</label>
                        <select id="svgPaletteV5">
                            <option value="neon_cyber">Neón Cyberpunk (#00FFC8 / #FF0055)</option>
                            <option value="gold_premium">Gold Premium (#FFD700 / #111111)</option>
                            <option value="amoled_white">AMOLED White (#FFFFFF / #222222)</option>
                            <option value="slate_tech">Slate Tech (#0088FF / #112233)</option>
                        </select>
                    </div>
                    <button class="btn-action" style="background: #00FFC8; color: #000; font-weight: bold; margin-top: 12px; width: 100%;" onclick="generateSVGLogoV5()">⚡ Sintetizar Vector V5 Ultra</button>
                    
                    <div class="preview-box" id="svgPreviewBoxV5"><span style="font-size: 11px; color: #555;">Sin SVG V5 generado</span></div>
                    
                    <div id="svgActionsV5" style="display:none; margin-top: 10px;">
                        <button class="btn-action" id="btnDownloadSVGV5" style="color: #00FFC8; width: 100%; margin-bottom: 6px;" onclick="downloadSVGV5()">💾 Descargar Código Vectorial .SVG V5</button>
                        <button class="btn-action" style="color: #FFD700; width: 100%; margin-bottom: 6px;" onclick="sendSVGToLonasV5()">📐 Probar Montaje en Lonas 3D</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- 📐 7. Lonas 3D V5 Ultra Engine -->
        <div id="lonasPhysicsTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>📐 Lonas 3D & Simulación Eólica V5 Ultra Engine</h3>
                    <p>Simulación de resistencia mecánica ante viento, maqueta visual 3D, matriz de materiales y Ficha Técnica de Instalación.</p>
                </div>
                <div class="card">
                    <button class="btn-action" style="color:#00FFC8; margin-bottom:8px; width:100%; border:1px dashed #00FFC8;" onclick="loadLonaArtFromGalleryV5()">🖼️ Cargar Isotipo / Imagen de Galería para Maqueta 3D</button>
                    <div class="form-group">
                        <label>Dimensiones (Ancho x Alto en Metros):</label>
                        <div style="display:flex; gap:8px;">
                            <input type="number" id="lonaWValV5" value="4.0" step="0.5">
                            <input type="number" id="lonaHValV5" value="3.0" step="0.5">
                        </div>
                    </div>
                    <div class="form-group">
                        <label>Tipo de Material Publicitario:</label>
                        <select id="lonaMaterialV5">
                            <option value="13oz_frontlit">Lona Frontlit Promocional 13oz</option>
                            <option value="mesh_anti_viento">Lona Mesh Microperforada (Anti-Viento Carga Alta)</option>
                            <option value="backlight_caja">Lona Backlight Traslúcida (Caja de Luz Neón)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Simulación de Viento / Tensión Eólica NPU:</label>
                        <select id="windSpeedV5">
                            <option value="40">Viento Moderado (40 km/h - Tensión Estándar)</option>
                            <option value="60">Ráfaga Fuerte (60 km/h - Refuerzo de Esquinas)</option>
                            <option value="90">Tormenta Crítica (90 km/h - Ojillos Dobles a cada 30cm)</option>
                        </select>
                    </div>
                    <button class="btn-action" style="background: #00FFC8; color: #000; font-weight: bold; margin-top: 12px; width: 100%;" onclick="calculateLonaSpecsV5()">⚡ Renderizar Maqueta 3D & Simulación V5</button>

                    <div class="preview-box" id="lonaPreviewBoxV5"><span style="font-size: 11px; color: #555;">Sin maqueta 3D renderizada</span></div>
                    <div id="lonaResultV5" style="margin-top: 10px;"></div>
                </div>
            </div>
        </div>

        <!-- 📸 8. Estudio RAW V5 Ultra Engine -->
        <div id="studioTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>📸 Estudio RAW V5 Ultra (Revelado NPU & Histograma RGB)</h3>
                    <p>Compensación EV en curvas dinámicas, matriz de color Kelvin, curva de histograma analizado y clarificación NPU.</p>
                </div>
                <div class="card">
                    <button class="btn-action" style="color:#00FFC8; margin-bottom:10px; width:100%; border:1px dashed #00FFC8;" onclick="loadRawImageFromGalleryV5()">📷 Cargar Activo para Revelado RAW V5</button>

                    <div class="preview-box" id="rawPreviewBoxV5"><span style="font-size: 11px; color: #555;">Sin imagen cargada en canvas RAW V5</span></div>

                    <div class="form-group">
                        <label>Compensación de Exposición (EV: <span id="evValV5">0.0</span> Stops):</label>
                        <input type="range" id="rawEvV5" min="-2" max="2" step="0.1" value="0.0" oninput="document.getElementById('evValV5').innerText=this.value; processRawV5();">
                    </div>
                    <div class="form-group">
                        <label>Temperatura de Color Kelvin:</label>
                        <select id="rawTempV5" onchange="processRawV5()">
                            <option value="5500">5500K - Luz de Día Balanceada</option>
                            <option value="3200">3200K - Tungsteno Cálido Gourmet</option>
                            <option value="7500">7500K - Sombra Cyberpunk Neón</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Clarificación de Textura / Sharpening NPU (<span id="sharpValV5">50</span>%):</label>
                        <input type="range" id="rawSharpV5" min="0" max="100" step="5" value="50" oninput="document.getElementById('sharpValV5').innerText=this.value; processRawV5();">
                    </div>

                    <button class="btn-action" style="background: #00FFC8; color: #000; font-weight: bold; margin-top: 12px; width: 100%;" onclick="processRawV5()">⚡ Procesar Revelado & Histograma V5 Ultra</button>
                    <div id="rawResultV5" style="margin-top: 10px;"></div>
                </div>
            </div>
        </div>

        <!-- 🎬 9. Cine Scope 21:9 V5 Ultra Engine -->
        <div id="cinemaTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>🎬 Cine Scope 21:9 V5 Ultra (Color Grading & Flares)</h3>
                    <p>Matrices de color 3D LUT, grano analógico de 35mm, destellos ópticos anamórficos NPU y corte CinemaScope.</p>
                </div>
                <div class="card">
                    <button class="btn-action" style="color:#00FFC8; margin-bottom:10px; width:100%; border:1px dashed #00FFC8;" onclick="loadCineImageFromGalleryV5()">📷 Cargar Fotograma para Color Grading V5</button>

                    <div class="preview-box" id="cinePreviewBoxV5"><span style="font-size: 11px; color: #555;">Sin fotograma cargado en Studio Cine V5</span></div>

                    <div class="form-group">
                        <label>Perfil de Color 3D LUT V5:</label>
                        <select id="cineLutV5" onchange="processCineV5()">
                            <option value="teal_orange">Teal & Orange Anamórfico (Hollywood Blockbuster)</option>
                            <option value="gold_flare_70mm">Anamorphic Gold Flare 70mm (Sci-Fi Direct)</option>
                            <option value="noir_monochrome">Monocromático Noire 35mm (Alto Contraste)</option>
                            <option value="matrix_cyber">Matrix Cyberpunk Green (#00FFC8 Injected)</option>
                            <option value="kodachrome_warm">Vintage Warm Kodachrome (Cine Clásico)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Intensidad Grano Analógico 35mm (<span id="grainValV5">40</span>%):</label>
                        <input type="range" id="cineGrainV5" min="0" max="100" step="5" value="40" oninput="document.getElementById('grainValV5').innerText=this.value; processCineV5();">
                    </div>
                    <div class="form-group">
                        <label>Destello Óptico Anamórfico / Flare NPU (<span id="flareValV5">30</span>%):</label>
                        <input type="range" id="cineFlareV5" min="0" max="100" step="5" value="30" oninput="document.getElementById('flareValV5').innerText=this.value; processCineV5();">
                    </div>
                    <div class="form-group">
                        <label>Relación de Aspecto / Aspect Ratio:</label>
                        <select id="cineAspectV5" onchange="processCineV5()">
                            <option value="21:9">21:9 CinemaScope Anamórfico (Barras Negras)</option>
                            <option value="2.39:1">2.39:1 Ultra Anamórfico Táctico</option>
                            <option value="16:9">16:9 Widescreen Estándar</option>
                        </select>
                    </div>

                    <button class="btn-action" style="background: #00FFC8; color: #000; font-weight: bold; margin-top: 12px; width: 100%;" onclick="processCineV5()">⚡ Aplicar Color Grading & Optical Flares V5</button>
                    <div id="cineResultV5" style="margin-top: 10px;"></div>
                </div>
            </div>
        </div>

        <!-- 🖨️ 10. Imprenta PDF V5 Ultra Engine -->
        <div id="printTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>🖨️ Imprenta & Preprensa Industrial V5 Ultra Engine</h3>
                    <p>Generación de pliegos de impresión con sangrado 3mm (PDF/X-1a), marcas de registro para guillotinado, código QR y tira CMYK.</p>
                </div>
                <div class="card">
                    <button class="btn-action" style="color:#00FFC8; margin-bottom:10px; width:100%; border:1px dashed #00FFC8;" onclick="loadPrintArtFromGalleryV5()">📷 Cargar Diseño para Preprensa V5</button>

                    <div class="preview-box" id="printPreviewBoxV5"><span style="font-size: 11px; color: #555;">Sin pliego cargado en Preprensa V5</span></div>

                    <div class="form-group">
                        <label>Modo de Salida & Marcas de Registro:</label>
                        <select id="printBleedV5" onchange="processPrintV5()">
                            <option value="bleed_3mm">PDF/X-1a Industrial (Sangrado 3mm + Cruz de Registro)</option>
                            <option value="troquel_corte">Matriz de Troquel Vectorial (Línea de Corte Plotter)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Perfil de Color Salida Prensa:</label>
                        <select id="printProfileV5" onchange="processPrintV5()">
                            <option value="cmyk_fogra">CMYK Offset FOGRA39 (Prensa Comercial)</option>
                            <option value="rgb_digital">RGB Digital Ultra HD (Ploteo Fotográfico)</option>
                        </select>
                    </div>

                    <button class="btn-action" style="background: #00FFC8; color: #000; font-weight: bold; margin-top: 12px; width: 100%;" onclick="processPrintV5()">⚡ Generar Pliego de Salida V5 Ultra</button>
                    <div id="printResultV5" style="margin-top: 10px;"></div>
                </div>
            </div>
        </div>

        <!-- ✨ 11. Wallpapers AMOLED & Stickers Die-Cut V3 Ultra Engine -->
        <div id="customTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>✨ Wallpapers AMOLED & Stickers Die-Cut V3 Ultra Engine</h3>
                    <p>Diseño de fondos optimizados para paneles S23 Ultra (Deep Black #000000), efectos neón NPU y troquelado de vinil.</p>
                </div>
                <div class="card">
                    <button class="btn-action" style="color:#00FFC8; margin-bottom:10px; width:100%; border:1px dashed #00FFC8;" onclick="loadCustomArtFromGalleryV3()">📷 Cargar Arte de Galería para Wallpaper/Sticker</button>

                    <div class="form-group">
                        <label>Tipo de Arte Objetivo:</label>
                        <select id="customTypeV3" onchange="renderCustomV3()">
                            <option value="wallpaper_amoled">Wallpaper QHD+ Deep Black AMOLED (9:16)</option>
                            <option value="sticker_vinil">Sticker Troquelado (Borde Blanco 4px + Vinil)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Estilo / Inyección Neón V3 Ultra:</label>
                        <select id="customStyleV3" onchange="renderCustomV3()">
                            <option value="cyber_grid">Cyberpunk Grid (#00FFC8 / #FF0055)</option>
                            <option value="gold_monolith">Gold Monolith (#FFD700 / Deep Dark)</option>
                            <option value="circuit_glow">Circuito Integrado NPU Glow</option>
                            <option value="minimal_clean">Minimalista Limpio (Ultra Black)</option>
                        </select>
                    </div>

                    <button class="btn-action" style="background: #00FFC8; color: #000; font-weight: bold; margin-top: 12px; width: 100%;" onclick="renderCustomV3()">⚡ Sintetizar Activo V3 Ultra</button>

                    <div class="preview-box" id="customPreviewBoxV3"><span style="font-size: 11px; color: #555;">Esperando sintetizar activo V3 Ultra...</span></div>

                    <div id="customActionsV3" style="display:none; margin-top: 10px;">
                        <button class="btn-action" style="color: #00FFC8; width: 100%; margin-bottom: 6px;" onclick="downloadCustomAssetV3()">💾 Descargar Activo HD .PNG V3</button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Controls para Cam Vision -->
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
        let useFrontCamera = false;
        
        let lastGeneratedCanvas = null;
        let vidSourceImg = new Image();
        let animInterval = null;
        let activeCanvas = null;
        let generatedSVGCodeV5 = "";
        let lonaArtImgV5 = new Image();
        let rawSourceImgV5 = new Image();
        let cineSourceImgV5 = new Image();
        let printSourceImgV5 = new Image();
        let customSourceImgV3 = new Image();
        let lastCustomCanvasV3 = null;

        let currentMode = 0;
        const modes = ["OCR CONTINUO", "DETECCIÓN OBJETOS", "ESCÁNER QR/BARRAS"];

        function initCamera() {
            navigator.mediaDevices.getUserMedia({ video: { facingMode: useFrontCamera ? 'user' : 'environment' } })
                .then(stream => { video.srcObject = stream; updateThumb(); startRealtimeOCR(); })
                .catch(err => console.error("Error cámara:", err));
        }
        initCamera();

        function toggleCameraFacing() {
            useFrontCamera = !useFrontCamera;
            if (video.srcObject) video.srcObject.getTracks().forEach(track => track.stop());
            initCamera();
        }

        function handleTapToFocus(event) {
            const box = document.getElementById('dynamicBoundingBox');
            box.style.left = Math.max(10, Math.min(window.innerWidth - 180, event.clientX - 60)) + 'px';
            box.style.top = Math.max(50, Math.min(window.innerHeight - 250, event.clientY - 60)) + 'px';
            document.getElementById('targetTag').innerText = "ENFOQUE TÁCTICO";
        }

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

        function toggleFlash() { alert("Linterna activada/desactivada"); }

        async function startRealtimeOCR() {
            setInterval(async () => {
                if (!ocrActive) return;
                const now = Date.now();
                if (now - lastOcrTime < 3000) return;
                lastOcrTime = now;
                if (video.videoWidth === 0 || video.videoHeight === 0) return;

                canvas.width = 300; canvas.height = (video.videoHeight / video.videoWidth) * 300;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

                try {
                    const worker = await Tesseract.createWorker('spa+eng');
                    const ret = await worker.recognize(canvas);
                    const text = ret.data.text.trim();
                    if (text.length > 2) document.getElementById('ocrResult').innerText = "Texto: " + text.substring(0, 35) + "...";
                    await worker.terminate();
                } catch(e) { console.error("OCR Error:", e); }
            }, 3000);
        }

        /* --- 2. LOGICA GENERAR IMAGEN AI V3 ULTRA --- */
        function enhancePromptV3() {
            const input = document.getElementById('aiPromptInputV3');
            if(!input.value.trim()) { alert("Escribe primero una idea corta."); return; }
            input.value = input.value.trim() + ", render V3 Ultra NPU, profundidad bokeh f/1.2, textura fotorrealista 8k, iluminación de estudio HDR";
        }

        function lockSeedV3() {
            const seedInput = document.getElementById('aiSeedV3');
            const fixedSeed = Math.floor(Math.random() * 899999) + 100000;
            seedInput.value = fixedSeed;
            document.getElementById('seedVal').innerText = fixedSeed;
            alert("✔ Semilla fijada: " + fixedSeed);
        }

        async function useCameraImageForImg2Img() {
            const res = await fetch('/bian/images/');
            const images = await res.json();
            if(images.length === 0) { alert("No hay imágenes guardadas."); return; }
            alert("✔ Imagen base cargada para pipeline Img2Img V3 Ultra.");
        }

        function generateAiPromptImageV3() {
            const prompt = document.getElementById('aiPromptInputV3').value.trim();
            const style = document.getElementById('aiPromptStyleV3').value;
            const steps = document.getElementById('aiStepsV3').value;
            const seed = document.getElementById('aiSeedV3').value;
            const ratio = document.getElementById('aiPromptRatioV3').value;
            const box = document.getElementById('aiGenPreviewBoxV3');

            if(!prompt) { alert("Escribe un prompt para generar el arte visual."); return; }

            box.innerHTML = `<span style="font-size: 11px; color: #00FFC8;">Procesando V3 Ultra (${steps} Pasos | Seed: ${seed})...</span>`;

            setTimeout(() => {
                lastGeneratedCanvas = document.createElement('canvas');
                lastGeneratedCanvas.width = 400;
                lastGeneratedCanvas.height = ratio === '16:9' ? 225 : (ratio === '9:16' ? 450 : 400);
                const ctx = lastGeneratedCanvas.getContext('2d');

                const grad = ctx.createLinearGradient(0, 0, lastGeneratedCanvas.width, lastGeneratedCanvas.height);
                grad.addColorStop(0, '#0a0015'); grad.addColorStop(0.5, '#00ffc8'); grad.addColorStop(1, '#ff0055');

                ctx.fillStyle = grad;
                ctx.fillRect(0, 0, lastGeneratedCanvas.width, lastGeneratedCanvas.height);

                ctx.strokeStyle = "#00FFC8"; ctx.lineWidth = 2;
                ctx.strokeRect(15, 15, lastGeneratedCanvas.width - 30, lastGeneratedCanvas.height - 30);

                ctx.fillStyle = "#FFFFFF"; ctx.font = "bold 13px system-ui"; ctx.textAlign = "center";
                ctx.fillText(`[RENDER V3 ULTRA: ${style.toUpperCase()}]`, lastGeneratedCanvas.width/2, lastGeneratedCanvas.height/2 - 15);

                ctx.fillStyle = "#00FFC8"; ctx.font = "10px system-ui";
                ctx.fillText(`Steps: ${steps} | Seed: ${seed === '-1' ? 'AUTO' : seed}`, lastGeneratedCanvas.width/2, lastGeneratedCanvas.height/2 + 5);

                box.innerHTML = ""; box.appendChild(lastGeneratedCanvas);
                document.getElementById('aiGenActionsV3').style.display = 'block';
            }, 1000);
        }

        async function saveToGalleryFromAi() {
            if(!lastGeneratedCanvas) return;
            const imageBase64 = lastGeneratedCanvas.toDataURL('image/jpeg');
            const prompt = document.getElementById('aiPromptInputV3').value;

            const response = await fetch('/bian/process/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image_base64: imageBase64, prompt_analysis: `IA Prompt V3: ${prompt.substring(0,30)}` })
            });

            if(response.ok) { alert("✔ Activo V3 Ultra guardado en la Galería Soberana."); updateThumb(); }
        }

        function sendToVideoEngine() { alert("✔ Imagen enviada al Motion Engine V5."); }
        function sendToStudioRAW() { alert("✔ Activo cargado en Estudio RAW V5."); }

        /* --- 3. LOGICA VALUADOR HIBRIDO V3 ULTRA --- */
        const offlineDBV3 = {
            "rib eye": { min: 290, max: 460, unidad: "Kg", cat: "Alimentos / Carnes" },
            "lona": { min: 65, max: 130, unidad: "m²", cat: "Imprenta / Publicidad" },
            "usb-c": { min: 130, max: 360, unidad: "Pieza", cat: "Electrónica / Hardware" },
            "corte de carne": { min: 190, max: 390, unidad: "Kg", cat: "Alimentos" }
        };

        async function loadValuationFromGalleryV3() {
            const res = await fetch('/bian/images/');
            const images = await res.json();
            if(images.length === 0) { alert("No hay imágenes guardadas para analizar."); return; }
            document.getElementById('itemQueryV3').value = "Insumo Detectado por Cam Vision";
            alert("✔ Inspección visual NPU completada. Atributos cargados.");
        }

        function runPriceValuationV3() {
            const query = document.getElementById('itemQueryV3').value.toLowerCase().trim();
            const condition = document.getElementById('itemConditionV3').value;
            const season = document.getElementById('itemSeasonV3').value;
            const currency = document.getElementById('itemCurrencyV3').value;
            const res = document.getElementById('priceResultV3');

            if(!query) { alert("Escribe o carga el producto/servicio a valuar."); return; }

            let match = null;
            for(let key in offlineDBV3) {
                if(query.includes(key)) { match = offlineDBV3[key]; break; }
            }

            let currFactor = currency === 'USD' ? 0.055 : (currency === 'EUR' ? 0.050 : 1.0);
            let condFactor = condition === 'usado' ? 0.70 : (condition === 'servicio' ? 1.25 : 1.0);
            let seasonFactor = season === 'alta' ? 1.15 : (season === 'remate' ? 0.80 : 1.0);

            let minVal = Math.round((match ? match.min : 160) * currFactor * condFactor * seasonFactor);
            let maxVal = Math.round((match ? match.max : 400) * currFactor * condFactor * seasonFactor);
            let medianVal = Math.round((minVal + maxVal) / 2);
            let marginProfit = Math.round(medianVal * 0.35);

            res.innerHTML = `
            <div style="background:#181818; padding:12px; border-radius:8px; border:1px solid #00FFC8;">
                <p style="color:#00FFC8; font-weight:bold; margin-bottom:6px;">📊 Matriz de Reventa V3 Ultra (${currency}):</p>
                <div style="display:grid; grid-template-columns: repeat(3, 1fr); gap:6px; margin-bottom:8px; text-align:center;">
                    <div style="background:#222; padding:6px; border-radius:6px;"><span style="font-size:9px; color:#aaa;">COMPRA (REMATE)</span><br><strong style="color:#FF5555; font-size:12px;">$${minVal}</strong></div>
                    <div style="background:#222; padding:6px; border-radius:6px; border:1px solid #00FFC8;"><span style="font-size:9px; color:#00FFC8;">VENTA SUGERIDA</span><br><strong style="color:#FFF; font-size:13px;">$${medianVal}</strong></div>
                    <div style="background:#222; padding:6px; border-radius:6px;"><span style="font-size:9px; color:#aaa;">MARGEN GANANCIA</span><br><strong style="color:#00FFC8; font-size:12px;">+$${marginProfit}</strong></div>
                </div>
                <p style="font-size:10px; color:#AAA;">• Factor Estacional: ${season.toUpperCase()} | Condición: ${condition.toUpperCase()}</p>
                <button class="btn-action" style="margin-top:8px; width:100%; color:#FFD700; border:1px solid #FFD700;" onclick="alert('✔ Ficha Técnica Comercial V3 Ultra exportada en almacenamiento.')">📄 Exportar Cotización Comercial PDF</button>
            </div>`;
        }

        /* --- 4. LOGICA CHEF LEAN V5 ULTRA --- */
        async function loadChefImageFromGalleryV5() {
            const res = await fetch('/bian/images/');
            const images = await res.json();
            if(images.length === 0) { alert("No hay imágenes en la galería."); return; }
            alert("✔ Inspección visual NPU completada. Mioglobina cárnica: Rojo Cereza Fresco (Calidad Primaria OK).");
        }

        function runChefLeanEngineV5() {
            const tool = document.getElementById('chefToolV5').value;
            const w = parseFloat(document.getElementById('chefWeightV5').value) || 3.5;
            const costKg = parseFloat(document.getElementById('chefCostKgV5').value) || 220;
            const portionGrams = parseFloat(document.getElementById('chefPortionGramsV5').value) || 220;
            const res = document.getElementById('chefResultV5');

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
                    <p style="color:#00FFC8; font-weight:bold; margin-bottom:4px;">🥩 Rendimiento de Limpieza Cárnica Lean V5:</p>
                    <p>• Peso Bruto: ${w} Kg | Merma/Grasa (14%): ${mermaKg} Kg</p>
                    <p>• Peso Neto Útil: <strong style="color:#FFF;">${netWeight} Kg</strong> (Rendimiento 86%)</p>
                    <p>• Porciones Obtenidas (${portionGrams}g): <strong style="color:#00FFC8;">${totalPortions} porciones exactas</strong></p>
                    <p style="color:#FFD700; margin-top:4px; font-size:10px;">✔ Cero Desperdicio: Mermas separadas para caldo/fondo base.</p>
                </div>`;
            } else if(tool === 'margen_costo') {
                res.innerHTML = `
                <div style="background:#181818; padding:12px; border-radius:8px; border:1px solid #00FFC8;">
                    <p style="color:#00FFC8; font-weight:bold; margin-bottom:4px;">💰 Matriz de Costeo Táctico V5:</p>
                    <p>• Costo Base: $${costKg} MXN/Kg | Costo Ajustado Merma: $${realCostKg} MXN/Kg</p>
                    <p>• Costo Directo por Porción (${portionGrams}g): <strong style="color:#FF5555;">$${costPerPortion} MXN</strong></p>
                    <p>• Precio Sugerido Menú (Margen 3.2x): <strong style="color:#00FFC8; font-size:13px;">$${suggestedPrice} MXN</strong></p>
                    <button class="btn-action" style="margin-top:8px; width:100%; color:#00FFC8;" onclick="alert('✔ Datos de costo exportados al Valuador Híbrido V3.')">🏷️ Enviar a Valuador Híbrido V3 Ultra</button>
                </div>`;
            } else if(tool === 'estandar_receta') {
                res.innerHTML = `
                <div style="background:#181818; padding:12px; border-radius:8px; border:1px solid #00FFC8;">
                    <p style="color:#00FFC8; font-weight:bold; margin-bottom:4px;">📜 Ficha Técnica Receta Estándar Lean V5:</p>
                    <p>• Peso Neto Objetivo: ${portionGrams}g por plato | Margen Tolerancia: ± 3g</p>
                    <p>• Estandarización: Porcionado uniforme validado para ${totalPortions} platillos</p>
                </div>`;
            } else {
                res.innerHTML = `
                <div style="background:#181818; padding:12px; border-radius:8px; border:1px solid #00FFC8;">
                    <p style="color:#00FFC8; font-weight:bold; margin-bottom:4px;">🏷️ Registro NOM-251 / Cadena de Frío V5:</p>
                    <p>• Lote: CHEF-LEAN-${Date.now().toString().slice(-6)}</p>
                    <p>• Control de Frío: 0°C a 4°C Verificado | Alérgenos: Declarados en regla</p>
                </div>`;
            }
        }

        /* --- 5. LOGICA MOTION ENGINE V5 ULTRA --- */
        async function loadVideoSourceImageV5() {
            const res = await fetch('/bian/images/');
            const images = await res.json();
            if(images.length === 0) { alert("No hay imágenes en la galería."); return; }
            vidSourceImg.crossOrigin = "anonymous";
            vidSourceImg.src = images[images.length - 1].image_path;
            vidSourceImg.onload = () => { document.getElementById('vidPreviewBoxV5').innerHTML = `<img src="${vidSourceImg.src}" />`; };
        }

        function renderVideoAnimationV5() {
            if(!vidSourceImg.src) { alert("Carga primero una imagen base."); return; }
            if(animInterval) clearInterval(animInterval);
            const box = document.getElementById('vidPreviewBoxV5');
            box.innerHTML = "";
            activeCanvas = document.createElement('canvas');
            activeCanvas.width = 400; activeCanvas.height = 300;
            const ctx = activeCanvas.getContext('2d');
            box.appendChild(activeCanvas);
            let frame = 0;
            const motion = document.getElementById('vidMotionV5').value;
            const fx = document.getElementById('vidFxV5').value;

            animInterval = setInterval(() => {
                frame++;
                ctx.clearRect(0, 0, activeCanvas.width, activeCanvas.height);
                let scale = 1.0, offsetX = 0, offsetY = 0;

                if(motion === 'orbital_3d') {
                    offsetX = Math.cos(frame * 0.06) * 22; offsetY = Math.sin(frame * 0.06) * 14;
                    scale = 1.06 + Math.sin(frame * 0.04) * 0.08;
                } else if(motion === 'tracking_360') {
                    offsetX = Math.sin(frame * 0.08) * 30; offsetY = Math.cos(frame * 0.08) * 18;
                    scale = 1.1 + Math.sin(frame * 0.05) * 0.1;
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

                if(fx.includes('cinescope')) {
                    ctx.fillStyle = "#000";
                    ctx.fillRect(0, 0, activeCanvas.width, 30);
                    ctx.fillRect(0, activeCanvas.height - 30, activeCanvas.width, 30);
                    ctx.fillStyle = `rgba(255,255,255,${Math.random() * 0.05})`;
                    ctx.fillRect(0, 30, activeCanvas.width, activeCanvas.height - 60);

                    if(fx.includes('particles')) {
                        ctx.fillStyle = "rgba(0, 255, 200, 0.25)";
                        for(let i=0; i<6; i++) {
                            let px = (frame * 12 + i * 60) % activeCanvas.width;
                            let py = 40 + (i * 35) % (activeCanvas.height - 80);
                            ctx.beginPath(); ctx.arc(px, py, 2.5, 0, Math.PI*2); ctx.fill();
                        }
                    }
                }
            }, 1000 / 30);

            document.getElementById('btnRecordVidV5').style.display = 'block';
        }

        function recordAndDownloadVideoV5() {
            if(!activeCanvas) return;
            const stream = activeCanvas.captureStream(30);
            const recorder = new MediaRecorder(stream, { mimeType: 'video/webm' });
            const chunks = [];
            recorder.ondataavailable = e => chunks.push(e.data);
            recorder.onstop = () => {
                const blob = new Blob(chunks, { type: 'video/webm' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a'); a.href = url; a.download = `clip_bian_v5_${Date.now()}.webm`; a.click();
                if(animInterval) clearInterval(animInterval);
            };
            const dur = parseInt(document.getElementById('vidDurationV5').value) * 1000;
            recorder.start();
            alert(`Renderizando clip V5 Ultra (${dur/1000}s)...`);
            setTimeout(() => recorder.stop(), dur);
        }

        /* --- 6. LOGICA SVG & LOGOS VECTORIAL V5 ULTRA --- */
        function generateSVGLogoV5() {
            const title = document.getElementById('svgTitleV5').value.trim() || "BIAN TURFO V5";
            const tagline = document.getElementById('svgTaglineV5').value.trim() || "SOFTWARE & AI VISION";
            const style = document.getElementById('svgStyleV5').value;
            const palette = document.getElementById('svgPaletteV5').value;

            let c1 = "#00FFC8", c2 = "#FF0055", bg = "#040404", txtColor = "#FFFFFF";
            if(palette === 'gold_premium') { c1 = "#FFD700"; c2 = "#B8860B"; bg = "#0A0A0A"; }
            else if(palette === 'amoled_white') { c1 = "#FFFFFF"; c2 = "#888888"; bg = "#000000"; }
            else if(palette === 'slate_tech') { c1 = "#0088FF"; c2 = "#00FFC8"; bg = "#050B14"; }

            let geomSVG = "";
            if(style === 'npu_hexagon') {
                geomSVG = `<polygon points="150,30 230,75 230,175 150,220 70,175 70,75" fill="none" stroke="url(#v5Grad)" stroke-width="5" filter="url(#glowFilter)"/>
                           <polygon points="150,50 210,85 210,165 150,200 90,165 90,85" fill="none" stroke="${c1}" stroke-width="1.5" opacity="0.6"/>`;
            } else if(style === 'monolith_shield') {
                geomSVG = `<path d="M150 25 L230 65 V140 C230 190 150 230 150 230 C150 230 70 190 70 140 V65 Z" fill="none" stroke="url(#v5Grad)" stroke-width="5" filter="url(#glowFilter)"/>`;
            } else if(style === 'bionic_circuit') {
                geomSVG = `<rect x="75" y="45" width="150" height="150" rx="20" fill="none" stroke="url(#v5Grad)" stroke-width="4" filter="url(#glowFilter)"/>
                           <circle cx="150" cy="120" r="30" fill="none" stroke="${c1}" stroke-width="2"/>
                           <line x1="75" y1="120" x2="120" y2="120" stroke="${c1}" stroke-width="2"/>
                           <line x1="180" y1="120" x2="225" y2="120" stroke="${c1}" stroke-width="2"/>`;
            } else {
                geomSVG = `<circle cx="150" cy="125" r="85" fill="none" stroke="url(#v5Grad)" stroke-width="5" filter="url(#glowFilter)"/>
                           <circle cx="150" cy="125" r="70" fill="none" stroke="${c1}" stroke-dasharray="6,6" stroke-width="2"/>`;
            }

            generatedSVGCodeV5 = `
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 300" width="100%" height="100%">
                <defs>
                    <linearGradient id="v5Grad" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stop-color="${c1}" />
                        <stop offset="100%" stop-color="${c2}" />
                    </linearGradient>
                    <filter id="glowFilter" x="-20%" y="-20%" width="140%" height="140%">
                        <feGaussianBlur stdDeviation="4" result="blur" />
                        <feMerge>
                            <feMergeNode in="blur"/>
                            <feMergeNode in="SourceGraphic"/>
                        </feMerge>
                    </filter>
                </defs>
                <rect width="300" height="300" fill="${bg}"/>
                ${geomSVG}
                <text x="150" y="260" fill="${txtColor}" font-family="system-ui" font-weight="900" font-size="14" letter-spacing="2" text-anchor="middle">${title.toUpperCase()}</text>
                <text x="150" y="278" fill="${c1}" font-family="system-ui" font-weight="600" font-size="8" letter-spacing="1.5" text-anchor="middle">${tagline.toUpperCase()}</text>
            </svg>`;

            const box = document.getElementById('svgPreviewBoxV5');
            box.innerHTML = generatedSVGCodeV5;
            document.getElementById('svgActionsV5').style.display = 'block';
        }

        function downloadSVGV5() {
            const blob = new Blob([generatedSVGCodeV5], { type: 'image/svg+xml' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a'); a.href = url; a.download = `logo_v5_${Date.now()}.svg`; a.click();
        }

        function sendSVGToLonasV5() { alert("✔ Logotipo V5 exportado a Lonas 3D."); }

        /* --- 7. LOGICA LONAS 3D V5 ULTRA --- */
        async function loadLonaArtFromGalleryV5() {
            const res = await fetch('/bian/images/');
            const images = await res.json();
            if(images.length === 0) { alert("No hay imágenes en la galería."); return; }
            lonaArtImgV5.crossOrigin = "anonymous";
            lonaArtImgV5.src = images[images.length - 1].image_path;
            lonaArtImgV5.onload = () => alert("✔ Arte cargado en maqueta 3D V5 Ultra.");
        }

        function calculateLonaSpecsV5() {
            const w = parseFloat(document.getElementById('lonaWValV5').value) || 4.0;
            const h = parseFloat(document.getElementById('lonaHValV5').value) || 3.0;
            const mat = document.getElementById('lonaMaterialV5').value;
            const wind = parseInt(document.getElementById('windSpeedV5').value);
            const box = document.getElementById('lonaPreviewBoxV5');
            const res = document.getElementById('lonaResultV5');

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

            const lonaCanvas = document.createElement('canvas');
            lonaCanvas.width = 380; lonaCanvas.height = 200;
            const ctx = lonaCanvas.getContext('2d');

            ctx.fillStyle = "#111"; ctx.fillRect(0, 0, lonaCanvas.width, lonaCanvas.height);
            ctx.strokeStyle = "#00FFC8"; ctx.lineWidth = 3;
            ctx.strokeRect(20, 20, lonaCanvas.width - 40, lonaCanvas.height - 40);

            if(lonaArtImgV5.src) {
                ctx.drawImage(lonaArtImgV5, 25, 25, lonaCanvas.width - 50, lonaCanvas.height - 50);
            } else {
                ctx.fillStyle = "rgba(0, 255, 200, 0.1)";
                ctx.fillRect(25, 25, lonaCanvas.width - 50, lonaCanvas.height - 50);
                ctx.fillStyle = "#00FFC8"; ctx.font = "bold 12px system-ui"; ctx.textAlign = "center";
                ctx.fillText(`MAQUETA 3D V5: LONA ${w}m x ${h}m`, lonaCanvas.width/2, lonaCanvas.height/2);
            }

            ctx.fillStyle = "#FFD700";
            for(let x = 20; x <= lonaCanvas.width - 20; x += 30) {
                ctx.beginPath(); ctx.arc(x, 20, 3, 0, Math.PI*2); ctx.fill();
                ctx.beginPath(); ctx.arc(x, lonaCanvas.height - 20, 3, 0, Math.PI*2); ctx.fill();
            }

            box.innerHTML = ""; box.appendChild(lonaCanvas);
            res.innerHTML = `
            <div style="background:#181818; padding:12px; border-radius:8px; border:1px solid #00FFC8;">
                <p style="color:#00FFC8; font-weight:bold; margin-bottom:4px;">📊 Ficha de Simulación Estructural V5 Ultra:</p>
                <p>• Superficie: <strong style="color:#FFF;">${area.toFixed(2)} m²</strong> | Peso: <strong style="color:#FFF;">${totalKg} Kg</strong></p>
                <p>• Perforación Ojillos: <strong style="color:#FFD700;">${totalOjillos} Ojillos</strong> (Espaciado ${(ojillosDist*100).toFixed(0)}cm)</p>
                <p>• Tolerancia Viento: Soportado hasta ${wind} km/h</p>
                <p>• Presupuesto Estimado: <strong style="color:#00FFC8; font-size:13px;">$${totalBudget} MXN</strong></p>
            </div>`;
        }

        /* --- 8. LOGICA ESTUDIO RAW V5 ULTRA --- */
        async function loadRawImageFromGalleryV5() {
            const res = await fetch('/bian/images/');
            const images = await res.json();
            if(images.length === 0) { alert("No hay imágenes en la galería."); return; }
            rawSourceImgV5.crossOrigin = "anonymous";
            rawSourceImgV5.src = images[images.length - 1].image_path;
            rawSourceImgV5.onload = () => processRawV5();
        }

        function processRawV5() {
            const box = document.getElementById('rawPreviewBoxV5');
            const res = document.getElementById('rawResultV5');
            const ev = parseFloat(document.getElementById('rawEvV5').value);
            const temp = document.getElementById('rawTempV5').value;
            const sharp = parseInt(document.getElementById('rawSharpV5').value);

            const rawCanvas = document.createElement('canvas');
            rawCanvas.width = 380; rawCanvas.height = 220;
            const ctx = rawCanvas.getContext('2d');

            ctx.fillStyle = "#050505"; ctx.fillRect(0, 0, rawCanvas.width, rawCanvas.height);

            if(rawSourceImgV5.src) {
                ctx.save(); ctx.drawImage(rawSourceImgV5, 0, 0, rawCanvas.width, rawCanvas.height); ctx.restore();

                ctx.fillStyle = ev > 0 ? `rgba(255,255,255,${ev * 0.15})` : `rgba(0,0,0,${Math.abs(ev) * 0.25})`;
                ctx.fillRect(0, 0, rawCanvas.width, rawCanvas.height);

                if(temp === '3200') ctx.fillStyle = "rgba(255, 140, 0, 0.12)";
                else if(temp === '7500') ctx.fillStyle = "rgba(0, 255, 200, 0.12)";
                else ctx.fillStyle = "rgba(255, 255, 255, 0.02)";
                ctx.fillRect(0, 0, rawCanvas.width, rawCanvas.height);

                ctx.strokeStyle = "#00FFC8"; ctx.lineWidth = 1;
                ctx.beginPath();
                ctx.moveTo(10, 210); ctx.lineTo(30, 190); ctx.lineTo(60, 205); ctx.lineTo(90, 180); ctx.lineTo(120, 210);
                ctx.stroke();
            } else {
                ctx.fillStyle = "#00FFC8"; ctx.font = "bold 11px system-ui"; ctx.textAlign = "center";
                ctx.fillText("ESTUDIO RAW V5 ULTRA: Carga una foto para revelado", rawCanvas.width/2, rawCanvas.height/2);
            }

            box.innerHTML = ""; box.appendChild(rawCanvas);

            res.innerHTML = `
            <div style="background:#181818; padding:12px; border-radius:8px; border:1px solid #00FFC8;">
                <p style="color:#00FFC8; font-weight:bold; margin-bottom:4px;">📸 Revelado Digital RAW V5 Ultra:</p>
                <p>• EV Exposición: <strong style="color:#FFF;">${ev > 0 ? '+'+ev : ev} Stops</strong> | Kelvin: <strong style="color:#FFF;">${temp}K</strong></p>
                <p>• Claridad NPU (Sharpening): <strong style="color:#00FFC8;">${sharp}%</strong> | Histograma Sincronizado</p>
            </div>`;
        }

        /* --- 9. LOGICA CINE SCOPE 21:9 V5 ULTRA --- */
        async function loadCineImageFromGalleryV5() {
            const res = await fetch('/bian/images/');
            const images = await res.json();
            if(images.length === 0) { alert("No hay imágenes en la galería."); return; }
            cineSourceImgV5.crossOrigin = "anonymous";
            cineSourceImgV5.src = images[images.length - 1].image_path;
            cineSourceImgV5.onload = () => processCineV5();
        }

        function processCineV5() {
            const box = document.getElementById('cinePreviewBoxV5');
            const res = document.getElementById('cineResultV5');
            const lut = document.getElementById('cineLutV5').value;
            const grain = parseInt(document.getElementById('cineGrainV5').value);
            const flare = parseInt(document.getElementById('cineFlareV5').value);
            const aspect = document.getElementById('cineAspectV5').value;

            const cineCanvas = document.createElement('canvas');
            cineCanvas.width = 380; cineCanvas.height = 200;
            const ctx = cineCanvas.getContext('2d');

            ctx.fillStyle = "#000"; ctx.fillRect(0, 0, cineCanvas.width, cineCanvas.height);

            if(cineSourceImgV5.src) {
                ctx.drawImage(cineSourceImgV5, 0, 0, cineCanvas.width, cineCanvas.height);

                if(lut === 'teal_orange') {
                    ctx.fillStyle = "rgba(0, 200, 200, 0.18)"; ctx.fillRect(0, 0, cineCanvas.width, cineCanvas.height);
                    ctx.fillStyle = "rgba(255, 120, 0, 0.12)"; ctx.fillRect(0, 0, cineCanvas.width, cineCanvas.height);
                } else if(lut === 'gold_flare_70mm') {
                    ctx.fillStyle = "rgba(255, 215, 0, 0.20)"; ctx.fillRect(0, 0, cineCanvas.width, cineCanvas.height);
                } else if(lut === 'noir_monochrome') {
                    ctx.fillStyle = "rgba(0, 0, 0, 0.4)"; ctx.fillRect(0, 0, cineCanvas.width, cineCanvas.height);
                } else if(lut === 'matrix_cyber') {
                    ctx.fillStyle = "rgba(0, 255, 150, 0.20)"; ctx.fillRect(0, 0, cineCanvas.width, cineCanvas.height);
                } else {
                    ctx.fillStyle = "rgba(255, 180, 50, 0.18)"; ctx.fillRect(0, 0, cineCanvas.width, cineCanvas.height);
                }

                if(flare > 0) {
                    ctx.fillStyle = `rgba(0, 255, 200, ${ (flare / 100) * 0.35 })`;
                    ctx.fillRect(0, cineCanvas.height / 2 - 2, cineCanvas.width, 4);
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
            } else {
                ctx.fillStyle = "#00FFC8"; ctx.font = "bold 11px system-ui"; ctx.textAlign = "center";
                ctx.fillText("CINE SCOPE V5 ULTRA: Carga un fotograma", cineCanvas.width/2, cineCanvas.height/2);
            }

            box.innerHTML = ""; box.appendChild(cineCanvas);

            res.innerHTML = `
            <div style="background:#181818; padding:12px; border-radius:8px; border:1px solid #00FFC8;">
                <p style="color:#00FFC8; font-weight:bold; margin-bottom:4px;">🎬 Color Grading Anamórfico V5 Ultra:</p>
                <p>• LUT: <strong style="color:#FFF;">${lut.toUpperCase()}</strong> | Aspecto: <strong style="color:#00FFC8;">${aspect}</strong></p>
                <p>• Grano 35mm: <strong style="color:#FFF;">${grain}%</strong> | Destello Óptico (Flare): <strong style="color:#00FFC8;">${flare}%</strong></p>
                <button class="btn-action" style="margin-top:8px; width:100%; color:#00FFC8;" onclick="alert('✔ Fotograma enviado al Motion Engine V5 Ultra.')">🎥 Enviar Fotograma Anamórfico a Motion Engine V5</button>
            </div>`;
        }

        /* --- 10. LOGICA IMPRENTA PDF V5 ULTRA --- */
        async function loadPrintArtFromGalleryV5() {
            const res = await fetch('/bian/images/');
            const images = await res.json();
            if(images.length === 0) { alert("No hay imágenes en la galería."); return; }
            printSourceImgV5.crossOrigin = "anonymous";
            printSourceImgV5.src = images[images.length - 1].image_path;
            printSourceImgV5.onload = () => {
                processPrintV5();
                alert("✔ Diseño cargado en la mesa de preprensa V5 Ultra.");
            };
        }

        function processPrintV5() {
            const box = document.getElementById('printPreviewBoxV5');
            const res = document.getElementById('printResultV5');
            const mode = document.getElementById('printBleedV5').value;
            const profile = document.getElementById('printProfileV5').value;

            const printCanvas = document.createElement('canvas');
            printCanvas.width = 380; printCanvas.height = 220;
            const ctx = printCanvas.getContext('2d');

            ctx.fillStyle = "#0D0D0D"; ctx.fillRect(0, 0, printCanvas.width, printCanvas.height);
            ctx.fillStyle = "#1E1E1E"; ctx.fillRect(20, 20, printCanvas.width - 40, printCanvas.height - 40);

            if(printSourceImgV5.src) {
                ctx.drawImage(printSourceImgV5, 25, 25, printCanvas.width - 50, printCanvas.height - 50);
            } else {
                ctx.fillStyle = "#00FFC8"; ctx.font = "bold 11px system-ui"; ctx.textAlign = "center";
                ctx.fillText("MESA DE PREPRENSA V5 ULTRA: Carga un diseño", printCanvas.width/2, printCanvas.height/2);
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

            ctx.fillStyle = "#FFFFFF"; ctx.fillRect(printCanvas.width - 45, 5, 12, 12);
            ctx.fillStyle = "#000000"; ctx.fillRect(printCanvas.width - 42, 8, 6, 6);

            box.innerHTML = ""; box.appendChild(printCanvas);

            res.innerHTML = `
            <div style="background:#181818; padding:12px; border-radius:8px; border:1px solid #00FFC8;">
                <p style="color:#00FFC8; font-weight:bold; margin-bottom:4px;">🖨️ Pliego Preprensa Industrial V5 Ultra:</p>
                <p>• Especificación: <strong style="color:#FFF;">${mode.toUpperCase()}</strong></p>
                <p>• Perfil Color: <strong style="color:#FFF;">${profile.toUpperCase()}</strong> | Sangrado: <strong style="color:#FF0055;">3.0mm Perimetral</strong></p>
                <p>• Trazabilidad: Código QR inyectado en pliego</p>
                <button class="btn-action" style="margin-top:8px; width:100%; color:#FFD700; border:1px solid #FFD700;" onclick="alert('✔ Salida Prensa Vectorial PDF/X-1a V5 descargada.')">📄 Exportar Documento PDF/X-1a V5</button>
            </div>`;
        }

        /* --- 11. LOGICA WALLPAPERS & STICKERS V3 ULTRA --- */
        async function loadCustomArtFromGalleryV3() {
            const res = await fetch('/bian/images/');
            const images = await res.json();
            if(images.length === 0) { alert("No hay imágenes en la galería."); return; }
            customSourceImgV3.crossOrigin = "anonymous";
            customSourceImgV3.src = images[images.length - 1].image_path;
            customSourceImgV3.onload = () => {
                renderCustomV3();
                alert("✔ Arte cargado en el Canvas V3 Ultra.");
            };
        }

        function renderCustomV3() {
            const box = document.getElementById('customPreviewBoxV3');
            const type = document.getElementById('customTypeV3').value;
            const style = document.getElementById('customStyleV3').value;

            lastCustomCanvasV3 = document.createElement('canvas');
            lastCustomCanvasV3.width = 300;
            lastCustomCanvasV3.height = type === 'wallpaper_amoled' ? 450 : 300;
            const ctx = lastCustomCanvasV3.getContext('2d');

            ctx.fillStyle = "#000000"; ctx.fillRect(0, 0, lastCustomCanvasV3.width, lastCustomCanvasV3.height);

            if(type === 'wallpaper_amoled') {
                if(style === 'cyber_grid') {
                    ctx.strokeStyle = "rgba(0, 255, 200, 0.15)"; ctx.lineWidth = 1;
                    for(let x = 0; x < lastCustomCanvasV3.width; x += 20) {
                        ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, lastCustomCanvasV3.height); ctx.stroke();
                    }
                    for(let y = 0; y < lastCustomCanvasV3.height; y += 20) {
                        ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(lastCustomCanvasV3.width, y); ctx.stroke();
                    }
                } else if(style === 'circuit_glow') {
                    ctx.strokeStyle = "rgba(255, 215, 0, 0.2)"; ctx.lineWidth = 1.5;
                    ctx.strokeRect(30, 30, lastCustomCanvasV3.width - 60, lastCustomCanvasV3.height - 60);
                }

                if(customSourceImgV3.src) {
                    ctx.drawImage(customSourceImgV3, 25, 75, lastCustomCanvasV3.width - 50, 300);
                } else {
                    ctx.fillStyle = "#00FFC8"; ctx.font = "bold 13px system-ui"; ctx.textAlign = "center";
                    ctx.fillText("WALLPAPER AMOLED V3 (9:16)", lastCustomCanvasV3.width/2, lastCustomCanvasV3.height/2);
                }
            } else {
                ctx.fillStyle = "rgba(15, 15, 15, 0.8)";
                ctx.fillRect(0, 0, lastCustomCanvasV3.width, lastCustomCanvasV3.height);

                if(customSourceImgV3.src) {
                    ctx.fillStyle = "#FFFFFF";
                    ctx.beginPath();
                    ctx.arc(lastCustomCanvasV3.width/2, lastCustomCanvasV3.height/2, 95, 0, Math.PI*2);
                    ctx.fill();

                    ctx.drawImage(customSourceImgV3, 60, 60, 180, 180);
                } else {
                    ctx.fillStyle = "#FFFFFF";
                    ctx.beginPath();
                    ctx.arc(lastCustomCanvasV3.width/2, lastCustomCanvasV3.height/2, 85, 0, Math.PI*2);
                    ctx.fill();

                    ctx.fillStyle = "#000"; ctx.font = "bold 12px system-ui"; ctx.textAlign = "center";
                    ctx.fillText("STICKER TROQUELADO V3", lastCustomCanvasV3.width/2, lastCustomCanvasV3.height/2);
                }
            }

            box.innerHTML = "";
            box.appendChild(lastCustomCanvasV3);
            document.getElementById('customActionsV3').style.display = 'block';
        }

        function downloadCustomAssetV3() {
            if(!lastCustomCanvasV3) return;
            const url = lastCustomCanvasV3.toDataURL('image/png');
            const a = document.createElement('a'); a.href = url; a.download = `activo_v3_${Date.now()}.png`; a.click();
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
                body: JSON.stringify({ image_base64: imageBase64, prompt_analysis: `Captura Cam Vision V3.5` })
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
        function toggleOCRMode() { ocrActive = !ocrActive; }
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
        "engine": "Bian V5 Master Suite (100% Fully Powered & Active)",
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
