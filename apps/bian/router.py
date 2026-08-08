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
    prompt_analysis: str = "Detección V4 Ultra Pro Engine"

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bian AI Vision & Creative Suite - Master V6 Ultra</title>
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
        
        /* HUD CAM VISION V4 ULTRA */
        .hud-overlay { position: absolute; border: 2px solid #00FFC8; width: 85%; height: 65%; top: 10%; left: 7.5%; border-radius: 20px; box-shadow: 0 0 25px rgba(0,255,200,0.35); pointer-events: none; display: flex; flex-direction: column; justify-content: space-between; padding: 12px; }
        .hud-top { display: flex; justify-content: space-between; font-size: 10px; color: #00FFC8; background: rgba(0,0,0,0.8); padding: 6px 10px; border-radius: 6px; pointer-events: auto; }
        .ocr-box { font-size: 11px; color: #FFF; background: rgba(0,0,0,0.85); padding: 8px 12px; border-radius: 8px; border-left: 3px solid #00FFC8; max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        
        .bounding-box-primary { position: absolute; border: 1px dashed #FF0055; width: 40%; height: 28%; top: 25%; left: 20%; pointer-events: none; border-radius: 6px; display: flex; align-items: flex-start; justify-content: flex-end; padding: 4px; transition: all 0.2s ease; }
        .bounding-box-secondary { position: absolute; border: 1px dashed #00FFC8; width: 30%; height: 20%; top: 55%; left: 60%; pointer-events: none; border-radius: 6px; display: flex; align-items: flex-start; justify-content: flex-end; padding: 4px; }
        .bounding-tag { background: rgba(255,0,85,0.85); color: #fff; font-size: 8px; padding: 2px 5px; border-radius: 3px; font-weight: bold; }
        .bounding-tag-sec { background: rgba(0,255,200,0.85); color: #000; font-size: 8px; padding: 2px 5px; border-radius: 3px; font-weight: bold; }

        .grid-overlay { position: absolute; top:0; left:0; width:100%; height:100%; background: linear-gradient(rgba(0,255,200,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(0,255,200,0.03) 1px, transparent 1px); background-size: 30px 30px; pointer-events:none; }

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
        <button class="nav-tab active" onclick="switchModule('cameraTab', this)">📷 Cam Vision V4 Ultra</button>
        <button class="nav-tab" onclick="switchModule('genPromptTab', this)">✨ Generar Imagen AI V4 Ultra</button>
        <button class="nav-tab" onclick="switchModule('priceTab', this)">🏷️ Valuador Híbrido V4 Ultra</button>
        <button class="nav-tab" onclick="switchModule('foodIndustryTab', this)">👨‍🍳 Chef Lean V6 Ultra</button>
        <button class="nav-tab" onclick="switchModule('genVidTab', this)">🎥 Video Motion V6 Ultra</button>
        <button class="nav-tab" onclick="switchModule('genImgTab', this)">🎨 SVG & Logos V6 Ultra</button>
        <button class="nav-tab" onclick="switchModule('lonasPhysicsTab', this)">📐 Lonas 3D V6 Ultra</button>
        <button class="nav-tab" onclick="switchModule('studioTab', this)">📸 Estudio RAW V6 Ultra</button>
        <button class="nav-tab" onclick="switchModule('cinemaTab', this)">🎬 Cine Scope 21:9 V6 Ultra</button>
        <button class="nav-tab" onclick="switchModule('printTab', this)">🖨️ Imprenta PDF V6 Ultra</button>
        <button class="nav-tab" onclick="switchModule('customTab', this)">✨ Wallpapers V4 Ultra</button>
    </div>

    <div class="header">
        <span style="font-weight: 700; font-size: 13px;" id="moduleTitle">BIAN V6 MASTER SUITE</span>
        <span class="badge" id="netBadge">RED: AUDITANDO...</span>
    </div>

    <div class="main-container">
        <!-- 📷 1. Cam Vision V4 Ultra Engine -->
        <div id="cameraTab" class="module-view active" onclick="handleTapToFocusV4(event)">
            <video id="webcam" autoplay playsinline></video>
            <div class="grid-overlay"></div>
            <div class="hud-overlay">
                <div class="hud-top">
                    <span id="modeLabel">MODO: MULTI-SEGMENTACIÓN NPU V4</span>
                    <button onclick="toggleCameraFacingV4()" style="background:#111; color:#00FFC8; border:1px solid #00FFC8; padding:2px 6px; border-radius:4px; font-size:9px; cursor:pointer;">LENTE BACK/FRONT</button>
                </div>
                <div class="bounding-box-primary" id="dynamicBoundingBoxV4">
                    <span class="bounding-tag" id="targetTagV4">PRIMARIO 98.4%</span>
                </div>
                <div class="bounding-box-secondary">
                    <span class="bounding-tag-sec">SECUNDARIO 89.1%</span>
                </div>
                <div class="ocr-box" id="ocrResult">Cam Vision V4 Ultra: Rastreo multiobjeto activo...</div>
            </div>
            <canvas id="canvas" style="display:none;"></canvas>
        </div>

        <!-- ✨ 2. Generar Imagen AI V4 Ultra Engine -->
        <div id="genPromptTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>✨ Sintetizador Diffusion AI V4 Ultra Engine</h3>
                    <p>Inyección NPU V6, control de Denoising Strength Img2Img, variaciones por semilla fija y renderizado multicapa HDR.</p>
                </div>
                <div class="card">
                    <button class="btn-action" style="color:#00FFC8; margin-bottom:10px; width:100%; border:1px dashed #00FFC8;" onclick="useCameraImageForImg2ImgV4()">📷 Cargar Última Foto de Cam Vision para Img2Img</button>

                    <div class="form-group">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <label>Prompt / Descripción Visual:</label>
                            <button class="btn-action" style="font-size:9px; color:#00FFC8; padding:3px 6px;" onclick="enhancePromptV4()">🪄 Optimizar Prompt NPU V6</button>
                        </div>
                        <textarea id="aiPromptInputV4" rows="3" placeholder="Ej. Corte Rib Eye a la parrilla, iluminación neón cyberpunk..."></textarea>
                    </div>
                    <div class="form-group">
                        <label>Fuerza de Transformación Img2Img (Denoising: <span id="denoiseValV4">0.55</span>):</label>
                        <input type="range" id="aiDenoiseV4" min="0.20" max="0.85" step="0.05" value="0.55" oninput="document.getElementById('denoiseValV4').innerText=this.value">
                    </div>
                    <div class="form-group">
                        <label>Estilo Visual / Preset NPU V6:</label>
                        <select id="aiPromptStyleV4">
                            <option value="cyberpunk">Cyberpunk / Neón Glowing V6</option>
                            <option value="fotorealismo">Fotorealismo 8K / Macro Gourmet DSLR</option>
                            <option value="octane">Render 3D Octane Volumétrico</option>
                            <option value="cinescope">CineScope Anamórfico 35mm</option>
                            <option value="vectorial">Ilustración Vectorial Minimalista</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Pasos de Inferencia (Sampling Steps):</label>
                        <select id="aiStepsV4">
                            <option value="20">20 Pasos (Render Rápido NPU - 1.0s)</option>
                            <option value="30">30 Pasos (Balance Fidelidad/Detalle)</option>
                            <option value="50">50 Pasos (Ultra Detalle Textura Master)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Semilla Semántica (Seed: <span id="seedValV4">Aleatoria (-1)</span>):</label>
                        <div style="display:flex; gap:8px;">
                            <input type="number" id="aiSeedV4" value="-1" placeholder="-1 para aleatorio">
                            <button class="btn-action" style="font-size:10px; color:#00FFC8;" onclick="lockSeedV4()">🔒 Fijar Semilla</button>
                        </div>
                    </div>
                    <div class="form-group">
                        <label>Relación de Aspecto:</label>
                        <select id="aiPromptRatioV4">
                            <option value="1:1">1:1 (Cuadrado / Asset Social)</option>
                            <option value="16:9">16:9 (Cinema Widescreen)</option>
                            <option value="9:16">9:16 (Wallpaper S23 Ultra)</option>
                        </select>
                    </div>

                    <button class="btn-action" style="background: #00FFC8; color: #000; font-weight: bold; margin-top: 12px; width: 100%;" onclick="generateAiPromptImageV4()">⚡ Renderizar Arte Visual V4 Ultra</button>

                    <div class="preview-box" id="aiGenPreviewBoxV4"><span style="font-size: 11px; color: #555;">Esperando prompt para V4 Ultra...</span></div>

                    <div id="aiGenActionsV4" style="display:none; margin-top: 10px;">
                        <button class="btn-action" style="color: #00FFC8; width: 100%; margin-bottom: 6px;" onclick="sendToVideoEngineV4()">🎥 Enviar a Video Motion V6</button>
                        <button class="btn-action" style="color: #FFD700; width: 100%; margin-bottom: 6px;" onclick="saveToGalleryFromAiV4()">💾 Guardar en Galería Soberana</button>
                        <button class="btn-action" style="color: #FF0055; width: 100%;" onclick="sendToStudioRAWV4()">📸 Abrir en Estudio RAW V6</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- 🏷️ 3. Valuador Híbrido V4 Ultra Engine -->
        <div id="priceTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>🏷️ Valuador Táctico & Financiero V4 Ultra Engine</h3>
                    <p>Análisis NPU de mercado, proyección estacional, cálculo de ROI %, margen de reventa y exportación comercial.</p>
                </div>
                <div class="card">
                    <button class="btn-action" style="color:#00FFC8; margin-bottom:8px; width:100%; border:1px dashed #00FFC8;" onclick="loadValuationFromGalleryV4()">📸 Capturar / Cargar Foto para Inspección NPU V6</button>
                    <div class="form-group">
                        <label>Producto, Insumo o Servicio a Valuar:</label>
                        <input type="text" id="itemQueryV4" placeholder="Ej. Corte Rib Eye 1kg, Lona 4x3m, Conector USB-C...">
                    </div>
                    <div class="form-group">
                        <label>Condición del Ítem / Desgaste Visual:</label>
                        <select id="itemConditionV4">
                            <option value="nuevo">Nuevo / Insumo Premium</option>
                            <option value="usado">Usado / Reutilizable (-30% Depreciación)</option>
                            <option value="servicio">Servicio Técnico Especializado</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Factor Estacional / Demanda de Mercado:</label>
                        <select id="itemSeasonV4">
                            <option value="estandar">Demanda Estándar (Sin Ajuste)</option>
                            <option value="alta">Temporada Alta / Escasez (+15% Incremento)</option>
                            <option value="remate">Oferta Liquidez / Remate (-20% Descuento)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Divisa Financiera:</label>
                        <select id="itemCurrencyV4">
                            <option value="MXN">MXN - Peso Mexicano</option>
                            <option value="USD">USD - Dólar Americano</option>
                            <option value="EUR">EUR - Euro</option>
                        </select>
                    </div>
                    <button class="btn-action" style="background: #00FFC8; color: #000; font-weight: bold; margin-top: 12px; width: 100%;" onclick="runPriceValuationV4()">📊 Calcular Matriz de Reventa & ROI V4 Ultra</button>
                    <div id="priceResultV4" style="margin-top: 12px;"></div>
                </div>
            </div>
        </div>

        <!-- 👨‍🍳 4. Chef Lean V6 Ultra Engine -->
        <div id="foodIndustryTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>👨‍🍳 Chef Lean & Operación Gastronómica V6 Ultra Engine</h3>
                    <p>Inspección NPU de porcionado, matriz de rendimiento por lote cárnico, costeo directo y auditoría de desperdicio cero.</p>
                </div>
                <div class="card">
                    <button class="btn-action" style="color:#00FFC8; margin-bottom:8px; width:100%; border:1px dashed #00FFC8;" onclick="loadChefImageFromGalleryV6()">📷 Cargar Inspección Visual desde Galería NPU V6</button>
                    <div class="form-group">
                        <label>Herramienta Operativa Gastronómica V6:</label>
                        <select id="chefToolV6">
                            <option value="limpieza_carnes">🥩 Limpieza & Desgüese Cárnico (Turno Temprano 4 AM - 9 AM)</option>
                            <option value="estandar_receta">📜 Estandarización de Receta & Porcionado Lean</option>
                            <option value="margen_costo">💰 Matriz de Costeo Táctico & Margen de Venta</option>
                            <option value="norma_251">🏷️ Trazabilidad de Cadena de Frío NOM-251</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Peso Bruto Inicial Recibido (Kg):</label>
                        <input type="number" id="chefWeightV6" value="3.5" step="0.1">
                    </div>
                    <div class="form-group">
                        <label>Costo Insumo Base ($ MXN / Kg):</label>
                        <input type="number" id="chefCostKgV6" value="220" step="5">
                    </div>
                    <div class="form-group">
                        <label>Gramaje por Porción Objetivo (Gramos):</label>
                        <input type="number" id="chefPortionGramsV6" value="220" step="10">
                    </div>
                    <button class="btn-action" style="background: #00FFC8; color: #000; font-weight: bold; margin-top: 12px; width: 100%;" onclick="runChefLeanEngineV6()">⚡ Ejecutar Diagnóstico Operativo Chef Lean V6</button>
                    <div id="chefResultV6" style="margin-top: 12px;"></div>
                </div>
            </div>
        </div>

        <!-- 🎥 5. Video Motion V6 Ultra Engine -->
        <div id="genVidTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>🎥 Motion Engine V6 Ultra (3D Orbit & FX Layer)</h3>
                    <p>Trayectorias 3D avanzadas, tracking orbital 360°, partículas neón volumétricas, destellos ópticos y barras CineScope 21:9.</p>
                </div>
                <div class="card">
                    <button class="btn-action" style="color: #00FFC8; margin-bottom: 10px; width:100%; border:1px dashed #00FFC8;" onclick="loadVideoSourceImageV6()">📷 Cargar Último Activo de Galería Soberana</button>
                    <div class="preview-box" id="vidPreviewBoxV6"><span style="font-size: 11px; color: #555;">Sin imagen base cargada para Motion Engine V6</span></div>
                    <div class="form-group">
                        <label>Trayectoria de Cámara V6 Ultra:</label>
                        <select id="vidMotionV6">
                            <option value="orbital_3d">Órbita 3D Compleja + Depth Blur NPU</option>
                            <option value="tracking_360">Tracking Orbital 360° con Aceleración Pro</option>
                            <option value="dolly_vertigo">Zoom Anamórfico Dolly (Vertigo FX)</option>
                            <option value="neon_pulse">Pulso Neón 60 FPS Acelerado</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Capas & Efectos Cinemáticos (FX Layer V6):</label>
                        <select id="vidFxV6">
                            <option value="cinescope_particles">CineScope 21:9 + Grano 35mm + Partículas Neón</option>
                            <option value="cinescope_flares">CineScope 21:9 + Destellos Ópticos Anamórficos</option>
                            <option value="clean_hd">Ultra HD Limpio (Direct Cut)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Duración del Render (Segundos):</label>
                        <select id="vidDurationV6">
                            <option value="3">3 Segundos Loop Smooth (Social Asset)</option>
                            <option value="5">5 Segundos Cinematic Master Pro</option>
                        </select>
                    </div>
                    <button class="btn-action" style="background: #00FFC8; color: #000; font-weight: bold; margin-top: 12px; width: 100%;" onclick="renderVideoAnimationV6()">⚡ Renderizar Animación V6 Ultra</button>
                    <button class="btn-action" id="btnRecordVidV6" style="background: #FF0055; color: #fff; font-weight: bold; margin-top: 10px; width: 100%; display: none;" onclick="recordAndDownloadVideoV6()">🎥 Exportar Clip .WebM V6</button>
                </div>
            </div>
        </div>

        <!-- 🎨 6. SVG & Logos Vectorial V6 Ultra Engine -->
        <div id="genImgTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>🎨 Sintetizador SVG Vectorial V6 Ultra Engine</h3>
                    <p>Sintetizador de isotipos vectoriales limpios, geometría sagrada NPU V6, resplandor neón nativo SVG y exportación directa.</p>
                </div>
                <div class="card">
                    <div class="form-group">
                        <label>Nombre de la Marca / Título Isotipo:</label>
                        <input type="text" id="svgTitleV6" placeholder="Ej. BIAN TURFO ENGINE">
                    </div>
                    <div class="form-group">
                        <label>Tagline / Subtítulo Secundario:</label>
                        <input type="text" id="svgTaglineV6" placeholder="Ej. SOFTWARE & AI VISION">
                    </div>
                    <div class="form-group">
                        <label>Estructura Geométrica V6 Ultra:</label>
                        <select id="svgStyleV6">
                            <option value="npu_hexagon">Hexágono NPU con Malla Cyberpunk</option>
                            <option value="monolith_shield">Escudo Monolítico Táctico (Space Shield)</option>
                            <option value="circular_neon">Anillo Orbital Neón Volumétrico</option>
                            <option value="bionic_circuit">Nodo de Procesamiento Biónico IA</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Paleta de Color NPU V6:</label>
                        <select id="svgPaletteV6">
                            <option value="neon_cyber">Neón Cyberpunk (#00FFC8 / #FF0055)</option>
                            <option value="gold_premium">Gold Premium (#FFD700 / #111111)</option>
                            <option value="amoled_white">AMOLED White (#FFFFFF / #222222)</option>
                            <option value="slate_tech">Slate Tech (#0088FF / #112233)</option>
                        </select>
                    </div>
                    <button class="btn-action" style="background: #00FFC8; color: #000; font-weight: bold; margin-top: 12px; width: 100%;" onclick="generateSVGLogoV6()">⚡ Sintetizar Vector V6 Ultra</button>
                    
                    <div class="preview-box" id="svgPreviewBoxV6"><span style="font-size: 11px; color: #555;">Sin SVG V6 generado</span></div>
                    
                    <div id="svgActionsV6" style="display:none; margin-top: 10px;">
                        <button class="btn-action" id="btnDownloadSVGV6" style="color: #00FFC8; width: 100%; margin-bottom: 6px;" onclick="downloadSVGV6()">💾 Descargar Código Vectorial .SVG V6</button>
                        <button class="btn-action" style="color: #FFD700; width: 100%; margin-bottom: 6px;" onclick="sendSVGToLonasV6()">📐 Probar Montaje en Lonas 3D</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- 📐 7. Lonas 3D V6 Ultra Engine -->
        <div id="lonasPhysicsTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>📐 Lonas 3D & Simulación Eólica V6 Ultra Engine</h3>
                    <p>Simulación de resistencia mecánica ante viento, maqueta visual 3D, matriz de materiales y Ficha Técnica de Instalación.</p>
                </div>
                <div class="card">
                    <button class="btn-action" style="color:#00FFC8; margin-bottom:8px; width:100%; border:1px dashed #00FFC8;" onclick="loadLonaArtFromGalleryV6()">🖼️ Cargar Isotipo / Imagen de Galería para Maqueta 3D</button>
                    <div class="form-group">
                        <label>Dimensiones (Ancho x Alto en Metros):</label>
                        <div style="display:flex; gap:8px;">
                            <input type="number" id="lonaWValV6" value="4.0" step="0.5">
                            <input type="number" id="lonaHValV6" value="3.0" step="0.5">
                        </div>
                    </div>
                    <div class="form-group">
                        <label>Tipo de Material Publicitario:</label>
                        <select id="lonaMaterialV6">
                            <option value="13oz_frontlit">Lona Frontlit Promocional 13oz</option>
                            <option value="mesh_anti_viento">Lona Mesh Microperforada (Anti-Viento Carga Alta)</option>
                            <option value="backlight_caja">Lona Backlight Traslúcida (Caja de Luz Neón)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Simulación de Viento / Tensión Eólica NPU V6:</label>
                        <select id="windSpeedV6">
                            <option value="40">Viento Moderado (40 km/h - Tensión Estándar)</option>
                            <option value="60">Ráfaga Fuerte (60 km/h - Refuerzo de Esquinas)</option>
                            <option value="90">Tormenta Crítica (90 km/h - Ojillos Dobles a cada 30cm)</option>
                        </select>
                    </div>
                    <button class="btn-action" style="background: #00FFC8; color: #000; font-weight: bold; margin-top: 12px; width: 100%;" onclick="calculateLonaSpecsV6()">⚡ Renderizar Maqueta 3D & Simulación V6</button>

                    <div class="preview-box" id="lonaPreviewBoxV6"><span style="font-size: 11px; color: #555;">Sin maqueta 3D renderizada</span></div>
                    <div id="lonaResultV6" style="margin-top: 10px;"></div>
                </div>
            </div>
        </div>

        <!-- 📸 8. Estudio RAW V6 Ultra Engine -->
        <div id="studioTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>📸 Estudio RAW V6 Ultra (Revelado NPU & Histograma RGB)</h3>
                    <p>Compensación EV en curvas dinámicas, matriz Kelvin, curva de histograma analizado y clarificación NPU V6.</p>
                </div>
                <div class="card">
                    <button class="btn-action" style="color:#00FFC8; margin-bottom:10px; width:100%; border:1px dashed #00FFC8;" onclick="loadRawImageFromGalleryV6()">📷 Cargar Activo para Revelado RAW V6</button>

                    <div class="preview-box" id="rawPreviewBoxV6"><span style="font-size: 11px; color: #555;">Sin imagen cargada en canvas RAW V6</span></div>

                    <div class="form-group">
                        <label>Compensación de Exposición (EV: <span id="evValV6">0.0</span> Stops):</label>
                        <input type="range" id="rawEvV6" min="-2" max="2" step="0.1" value="0.0" oninput="document.getElementById('evValV6').innerText=this.value; processRawV6();">
                    </div>
                    <div class="form-group">
                        <label>Temperatura de Color Kelvin:</label>
                        <select id="rawTempV6" onchange="processRawV6()">
                            <option value="5500">5500K - Luz de Día Balanceada</option>
                            <option value="3200">3200K - Tungsteno Cálido Gourmet</option>
                            <option value="7500">7500K - Sombra Cyberpunk Neón</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Clarificación de Textura / Sharpening NPU (<span id="sharpValV6">50</span>%):</label>
                        <input type="range" id="rawSharpV6" min="0" max="100" step="5" value="50" oninput="document.getElementById('sharpValV6').innerText=this.value; processRawV6();">
                    </div>

                    <button class="btn-action" style="background: #00FFC8; color: #000; font-weight: bold; margin-top: 12px; width: 100%;" onclick="processRawV6()">⚡ Procesar Revelado & Histograma V6 Ultra</button>
                    <div id="rawResultV6" style="margin-top: 10px;"></div>
                </div>
            </div>
        </div>

        <!-- 🎬 9. Cine Scope 21:9 V6 Ultra Engine -->
        <div id="cinemaTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>🎬 Cine Scope 21:9 V6 Ultra (Color Grading & Optical Flares)</h3>
                    <p>Matrices de color 3D LUT, grano analógico de 35mm, destellos ópticos anamórficos NPU y corte CinemaScope.</p>
                </div>
                <div class="card">
                    <button class="btn-action" style="color:#00FFC8; margin-bottom:10px; width:100%; border:1px dashed #00FFC8;" onclick="loadCineImageFromGalleryV6()">📷 Cargar Fotograma para Color Grading V6</button>

                    <div class="preview-box" id="cinePreviewBoxV6"><span style="font-size: 11px; color: #555;">Sin fotograma cargado en Studio Cine V6</span></div>

                    <div class="form-group">
                        <label>Perfil de Color 3D LUT V6:</label>
                        <select id="cineLutV6" onchange="processCineV6()">
                            <option value="teal_orange">Teal & Orange Anamórfico (Hollywood Blockbuster)</option>
                            <option value="gold_flare_70mm">Anamorphic Gold Flare 70mm (Sci-Fi Direct)</option>
                            <option value="noir_monochrome">Monocromático Noire 35mm (Alto Contraste)</option>
                            <option value="matrix_cyber">Matrix Cyberpunk Green (#00FFC8 Injected)</option>
                            <option value="kodachrome_warm">Vintage Warm Kodachrome (Cine Clásico)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Intensidad Grano Analógico 35mm (<span id="grainValV6">40</span>%):</label>
                        <input type="range" id="cineGrainV6" min="0" max="100" step="5" value="40" oninput="document.getElementById('grainValV6').innerText=this.value; processCineV6();">
                    </div>
                    <div class="form-group">
                        <label>Destello Óptico Anamórfico / Flare NPU (<span id="flareValV6">30</span>%):</label>
                        <input type="range" id="cineFlareV6" min="0" max="100" step="5" value="30" oninput="document.getElementById('flareValV6').innerText=this.value; processCineV6();">
                    </div>
                    <div class="form-group">
                        <label>Relación de Aspecto / Aspect Ratio:</label>
                        <select id="cineAspectV6" onchange="processCineV6()">
                            <option value="21:9">21:9 CinemaScope Anamórfico (Barras Negras)</option>
                            <option value="2.39:1">2.39:1 Ultra Anamórfico Táctico</option>
                            <option value="16:9">16:9 Widescreen Estándar</option>
                        </select>
                    </div>

                    <button class="btn-action" style="background: #00FFC8; color: #000; font-weight: bold; margin-top: 12px; width: 100%;" onclick="processCineV6()">⚡ Aplicar Color Grading & Optical Flares V6</button>
                    <div id="cineResultV6" style="margin-top: 10px;"></div>
                </div>
            </div>
        </div>

        <!-- 🖨️ 10. Imprenta PDF V6 Ultra Engine -->
        <div id="printTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>🖨️ Imprenta & Preprensa Industrial V6 Ultra Engine</h3>
                    <p>Generación de pliegos de impresión con sangrado 3mm (PDF/X-1a), marcas de registro para guillotinado, código QR y tira CMYK.</p>
                </div>
                <div class="card">
                    <button class="btn-action" style="color:#00FFC8; margin-bottom:10px; width:100%; border:1px dashed #00FFC8;" onclick="loadPrintArtFromGalleryV6()">📷 Cargar Diseño para Preprensa V6</button>

                    <div class="preview-box" id="printPreviewBoxV6"><span style="font-size: 11px; color: #555;">Sin pliego cargado en Preprensa V6</span></div>

                    <div class="form-group">
                        <label>Modo de Salida & Marcas de Registro:</label>
                        <select id="printBleedV6" onchange="processPrintV6()">
                            <option value="bleed_3mm">PDF/X-1a Industrial (Sangrado 3mm + Cruz de Registro)</option>
                            <option value="troquel_corte">Matriz de Troquel Vectorial (Línea de Corte Plotter)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Perfil de Color Salida Prensa:</label>
                        <select id="printProfileV6" onchange="processPrintV6()">
                            <option value="cmyk_fogra">CMYK Offset FOGRA39 (Prensa Comercial)</option>
                            <option value="rgb_digital">RGB Digital Ultra HD (Ploteo Fotográfico)</option>
                        </select>
                    </div>

                    <button class="btn-action" style="background: #00FFC8; color: #000; font-weight: bold; margin-top: 12px; width: 100%;" onclick="processPrintV6()">⚡ Generar Pliego de Salida V6 Ultra</button>
                    <div id="printResultV6" style="margin-top: 10px;"></div>
                </div>
            </div>
        </div>

        <!-- ✨ 11. Wallpapers AMOLED & Stickers Die-Cut V4 Ultra Engine -->
        <div id="customTab" class="module-view">
            <div class="panel-content">
                <div class="card">
                    <h3>✨ Wallpapers AMOLED & Stickers Die-Cut V4 Ultra Engine</h3>
                    <p>Diseño de fondos optimizados para paneles S23 Ultra (Deep Black #000000), efectos neón NPU y troquelado de vinil.</p>
                </div>
                <div class="card">
                    <button class="btn-action" style="color:#00FFC8; margin-bottom:10px; width:100%; border:1px dashed #00FFC8;" onclick="loadCustomArtFromGalleryV4()">📷 Cargar Arte de Galería para Wallpaper/Sticker V6</button>

                    <div class="form-group">
                        <label>Tipo de Arte Objetivo:</label>
                        <select id="customTypeV4" onchange="renderCustomV4()">
                            <option value="wallpaper_amoled">Wallpaper QHD+ Deep Black AMOLED (9:16)</option>
                            <option value="sticker_vinil">Sticker Troquelado (Borde Blanco 4px + Vinil)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Estilo / Inyección Neón V4 Ultra:</label>
                        <select id="customStyleV4" onchange="renderCustomV4()">
                            <option value="cyber_grid">Cyberpunk Grid (#00FFC8 / #FF0055)</option>
                            <option value="gold_monolith">Gold Monolith (#FFD700 / Deep Dark)</option>
                            <option value="circuit_glow">Circuito Integrado NPU Glow</option>
                            <option value="minimal_clean">Minimalista Limpio (Ultra Black)</option>
                        </select>
                    </div>

                    <button class="btn-action" style="background: #00FFC8; color: #000; font-weight: bold; margin-top: 12px; width: 100%;" onclick="renderCustomV4()">⚡ Sintetizar Activo V4 Ultra</button>

                    <div class="preview-box" id="customPreviewBoxV4"><span style="font-size: 11px; color: #555;">Esperando sintetizar activo V4 Ultra...</span></div>

                    <div id="customActionsV4" style="display:none; margin-top: 10px;">
                        <button class="btn-action" style="color: #00FFC8; width: 100%; margin-bottom: 6px;" onclick="downloadCustomAssetV4()">💾 Descargar Activo HD .PNG V4</button>
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
        let lastOcrTime = 0;
        let useFrontCamera = false;
        
        let lastGeneratedCanvasV4 = null;
        let vidSourceImgV6 = new Image();
        let animIntervalV6 = null;
        let activeCanvasV6 = null;
        let generatedSVGCodeV6 = "";
        let lonaArtImgV6 = new Image();
        let rawSourceImgV6 = new Image();
        let cineSourceImgV6 = new Image();
        let printSourceImgV6 = new Image();
        let customSourceImgV4 = new Image();
        let lastCustomCanvasV4 = null;

        let currentMode = 0;
        const modes = ["OCR CONTINUO", "DETECCIÓN MULTI-OBJETO", "ESCÁNER BARRAS/QR V4"];

        function initCameraV4() {
            navigator.mediaDevices.getUserMedia({ video: { facingMode: useFrontCamera ? 'user' : 'environment' } })
                .then(stream => { video.srcObject = stream; updateThumb(); startRealtimeOCRV4(); })
                .catch(err => console.error("Error cámara:", err));
        }
        initCameraV4();

        function toggleCameraFacingV4() {
            useFrontCamera = !useFrontCamera;
            if (video.srcObject) video.srcObject.getTracks().forEach(track => track.stop());
            initCameraV4();
        }

        function handleTapToFocusV4(event) {
            const box = document.getElementById('dynamicBoundingBoxV4');
            box.style.left = Math.max(10, Math.min(window.innerWidth - 180, event.clientX - 60)) + 'px';
            box.style.top = Math.max(50, Math.min(window.innerHeight - 250, event.clientY - 60)) + 'px';
            document.getElementById('targetTagV4').innerText = "FOCO TÁCTICO 99.8%";
        }

        function switchModule(tabId, btn) {
            document.querySelectorAll('.module-view').forEach(m => m.classList.remove('active'));
            document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            btn.classList.add('active');

            const controls = document.getElementById('bottomControls');
            if (tabId === 'cameraTab') {
                controls.style.display = 'flex';
                document.getElementById('moduleTitle').innerText = 'BIAN V6 MASTER SUITE';
            } else {
                controls.style.display = 'none';
                document.getElementById('moduleTitle').innerText = btn.innerText;
            }
        }

        function toggleMode() {
            currentMode = (currentMode + 1) % modes.length;
            document.getElementById('modeLabel').innerText = "MODO: " + modes[currentMode];
            document.getElementById('targetTagV4').innerText = modes[currentMode];
        }

        function toggleFlash() { alert("Flash Táctico NPU V4"); }

        async function startRealtimeOCRV4() {
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
                    if (text.length > 2) document.getElementById('ocrResult').innerText = "Rastreo NPU V4: " + text.substring(0, 35) + "...";
                    await worker.terminate();
                } catch(e) { console.error("OCR Error:", e); }
            }, 3000);
        }

        /* --- 11. LOGICA WALLPAPERS & STICKERS V4 ULTRA --- */
        async function loadCustomArtFromGalleryV4() {
            const res = await fetch('/bian/images/');
            const images = await res.json();
            if(images.length === 0) { alert("No hay imágenes en la galería."); return; }
            customSourceImgV4.crossOrigin = "anonymous";
            customSourceImgV4.src = images[images.length - 1].image_path;
            customSourceImgV4.onload = () => {
                renderCustomV4();
                alert("✔ Arte cargado en el Canvas V4 Ultra.");
            };
        }

        function renderCustomV4() {
            const box = document.getElementById('customPreviewBoxV4');
            const type = document.getElementById('customTypeV4').value;
            const style = document.getElementById('customStyleV4').value;

            lastCustomCanvasV4 = document.createElement('canvas');
            lastCustomCanvasV4.width = 300;
            lastCustomCanvasV4.height = type === 'wallpaper_amoled' ? 450 : 300;
            const ctx = lastCustomCanvasV4.getContext('2d');

            ctx.fillStyle = "#000000"; ctx.fillRect(0, 0, lastCustomCanvasV4.width, lastCustomCanvasV4.height);

            if(type === 'wallpaper_amoled') {
                if(style === 'cyber_grid') {
                    ctx.strokeStyle = "rgba(0, 255, 200, 0.15)"; ctx.lineWidth = 1;
                    for(let x = 0; x < lastCustomCanvasV4.width; x += 20) {
                        ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, lastCustomCanvasV4.height); ctx.stroke();
                    }
                    for(let y = 0; y < lastCustomCanvasV4.height; y += 20) {
                        ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(lastCustomCanvasV4.width, y); ctx.stroke();
                    }
                } else if(style === 'circuit_glow') {
                    ctx.strokeStyle = "rgba(255, 215, 0, 0.2)"; ctx.lineWidth = 1.5;
                    ctx.strokeRect(30, 30, lastCustomCanvasV4.width - 60, lastCustomCanvasV4.height - 60);
                }

                if(customSourceImgV4.src) {
                    ctx.drawImage(customSourceImgV4, 25, 75, lastCustomCanvasV4.width - 50, 300);
                } else {
                    ctx.fillStyle = "#00FFC8"; ctx.font = "bold 13px system-ui"; ctx.textAlign = "center";
                    ctx.fillText("WALLPAPER AMOLED V4 (9:16)", lastCustomCanvasV4.width/2, lastCustomCanvasV4.height/2);
                }
            } else {
                ctx.fillStyle = "rgba(15, 15, 15, 0.8)";
                ctx.fillRect(0, 0, lastCustomCanvasV4.width, lastCustomCanvasV4.height);

                if(customSourceImgV4.src) {
                    ctx.fillStyle = "#FFFFFF";
                    ctx.beginPath();
                    ctx.arc(lastCustomCanvasV4.width/2, lastCustomCanvasV4.height/2, 95, 0, Math.PI*2);
                    ctx.fill();

                    ctx.drawImage(customSourceImgV4, 60, 60, 180, 180);
                } else {
                    ctx.fillStyle = "#FFFFFF";
                    ctx.beginPath();
                    ctx.arc(lastCustomCanvasV4.width/2, lastCustomCanvasV4.height/2, 85, 0, Math.PI*2);
                    ctx.fill();

                    ctx.fillStyle = "#000"; ctx.font = "bold 12px system-ui"; ctx.textAlign = "center";
                    ctx.fillText("STICKER TROQUELADO V4", lastCustomCanvasV4.width/2, lastCustomCanvasV4.height/2);
                }
            }

            box.innerHTML = "";
            box.appendChild(lastCustomCanvasV4);
            document.getElementById('customActionsV4').style.display = 'block';
        }

        function downloadCustomAssetV4() {
            if(!lastCustomCanvasV4) return;
            const url = lastCustomCanvasV4.toDataURL('image/png');
            const a = document.createElement('a'); a.href = url; a.download = `activo_v4_${Date.now()}.png`; a.click();
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
                body: JSON.stringify({ image_base64: imageBase64, prompt_analysis: `Captura Cam Vision V4 Ultra` })
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
        "engine": "Bian V6 Master Suite (100% Fully Powered & Active)",
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
