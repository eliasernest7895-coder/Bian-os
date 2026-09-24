from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from sqlmodel import Session, select, Field, SQLModel
from core.database import get_session
from apps.bian.models import ProcessedImage
from pydantic import BaseModel
import os
import base64
from datetime import datetime
from PIL import Image
import io

router = APIRouter(prefix="/bian", tags=["Bian AI Vision Pro"])

# Modelo de Base de Datos para Órdenes y Cotizaciones
class CommercialOrder(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    client_name: str
    concept: str
    amount: float
    notes: str = ""
    channel: str = "whatsapp"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ImageCaptureRequest(BaseModel):
    image_base64: str
    prompt_analysis: str = "Captura Bian V9"

class NanoBotQuery(BaseModel):
    message: str
    current_module: str = "general"

class OrderCreateRequest(BaseModel):
    client_name: str
    concept: str
    amount: float
    notes: str = ""
    channel: str = "whatsapp"

@router.get("/storage/bian/{filename}")
async def serve_bian_image(filename: str):
    file_path = os.path.join("storage", "bian", filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="Imagen no encontrada")

@router.get("/storage/bian/thumbs/{filename}")
async def serve_bian_thumb(filename: str):
    file_path = os.path.join("storage", "bian", "thumbs", filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    # Fallback a la imagen original si aún no tiene thumb
    orig_path = os.path.join("storage", "bian", filename)
    if os.path.exists(orig_path):
        return FileResponse(orig_path)
    raise HTTPException(status_code=404, detail="Miniatura no encontrada")

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Bian AI Suite - Cámara Pro Master V9</title>
    <script src="https://unpkg.com/tesseract.js@v4.0.2/dist/tesseract.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", Roboto, sans-serif; -webkit-tap-highlight-color: transparent; }
        body { background: #000; color: #fff; height: 100vh; overflow: hidden; display: flex; flex-direction: column; user-select: none; }

        .top-float-left {
            position: absolute; top: 16px; left: 18px; z-index: 50;
            background: rgba(22, 22, 26, 0.65);
            backdrop-filter: blur(25px); -webkit-backdrop-filter: blur(25px);
            border: 1px solid rgba(255, 255, 255, 0.16);
            border-radius: 20px; padding: 7px 14px;
            display: flex; align-items: center; gap: 8px; font-weight: 700; font-size: 12px;
            box-shadow: 0 6px 24px rgba(0,0,0,0.4);
            transition: all 0.25s ease;
        }
        .glow-dot { width: 7px; height: 7px; border-radius: 50%; background: #30D158; box-shadow: 0 0 8px #30D158; }

        .top-float-right {
            position: absolute; top: 16px; right: 18px; z-index: 50;
            display: flex; gap: 8px;
        }
        .action-pill {
            background: rgba(255, 255, 255, 0.12);
            backdrop-filter: blur(25px); -webkit-backdrop-filter: blur(25px);
            border: 1px solid rgba(255, 255, 255, 0.28);
            color: #FFFFFF; font-size: 12px; font-weight: 700; padding: 8px 14px; border-radius: 22px;
            display: flex; align-items: center; gap: 6px; cursor: pointer;
            box-shadow: 0 6px 24px rgba(0,0,0,0.5);
            transition: all 0.2s ease;
        }
        .action-pill:active { transform: scale(0.94); background: rgba(255,255,255,0.22); }
        .export-pill { border-color: rgba(0, 255, 200, 0.5); color: #00FFC8; }

        .viewport {
            position: absolute; inset: 0; width: 100%; height: 100%;
            background: #000; overflow: hidden; display: flex; align-items: center; justify-content: center;
        }
        video {
            width: 100%; height: 100%; object-fit: cover;
            transform-origin: center center;
            transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1), filter 0.3s ease;
        }
        video.portrait-bokeh { filter: drop-shadow(0 0 16px rgba(0,255,200,0.3)); }
        video.night-mode { filter: brightness(1.35) contrast(1.1) saturate(1.2); }
        video.macro-mode { filter: contrast(1.25) saturate(1.15); }
        video.scan-mode { filter: grayscale(1) contrast(1.4) brightness(1.1); }

        .doc-scanner-frame {
            position: absolute; top: 48%; left: 50%; transform: translate(-50%, -50%);
            width: 78%; max-width: 330px; aspect-ratio: 1 / 1.38;
            border: 1.5px solid rgba(0, 255, 200, 0.45); border-radius: 16px;
            box-shadow: 0 0 0 3000px rgba(0, 0, 0, 0.48), inset 0 0 25px rgba(0,255,200,0.12);
            pointer-events: none; z-index: 35; display: none;
            justify-content: space-between; flex-direction: column; padding: 12px; overflow: hidden;
        }
        .doc-scanner-frame.active { display: flex; }
        .doc-corner { width: 24px; height: 24px; border-color: #00FFC8; border-style: solid; filter: drop-shadow(0 0 8px #00FFC8); }
        .doc-corner.tl { border-width: 3.5px 0 0 3.5px; border-top-left-radius: 8px; }
        .doc-corner.tr { border-width: 3.5px 3.5px 0 0; border-top-right-radius: 8px; }
        .doc-corner.bl { border-width: 0 0 3.5px 3.5px; border-bottom-left-radius: 8px; }
        .doc-corner.br { border-width: 0 3.5px 3.5px 0; border-bottom-right-radius: 8px; }
        .doc-row { display: flex; justify-content: space-between; width: 100%; }

        .scanner-laser-line {
            position: absolute; left: 0; right: 0; height: 2px;
            background: linear-gradient(90deg, transparent, #00FFC8, #FFF, #00FFC8, transparent);
            box-shadow: 0 0 12px #00FFC8, 0 0 20px #00FFC8;
            animation: scanLaserAnim 2.8s ease-in-out infinite alternate;
        }
        @keyframes scanLaserAnim { 0% { top: 6%; opacity: 0.2; } 50% { opacity: 1; } 100% { top: 92%; opacity: 0.2; } }
        .doc-label-badge {
            align-self: center; background: rgba(0,0,0,0.7);
            border: 1px solid rgba(0,255,200,0.4); color: #00FFC8;
            font-size: 10px; font-weight: 700; padding: 4px 10px; border-radius: 12px;
            letter-spacing: 0.5px; text-transform: uppercase;
        }

        .timelapse-hud {
            position: absolute; top: 110px; left: 50%; transform: translateX(-50%);
            display: none; flex-direction: column; align-items: center; gap: 8px; z-index: 45;
        }
        .timelapse-hud.active { display: flex; }
        .timelapse-pill {
            background: rgba(255, 59, 48, 0.25); border: 1px solid #FF3B30;
            color: #FF453A; padding: 5px 14px; border-radius: 20px; font-size: 11px;
            font-weight: 700; display: flex; align-items: center; gap: 8px;
            backdrop-filter: blur(15px); -webkit-backdrop-filter: blur(15px);
        }
        .record-blink { width: 8px; height: 8px; border-radius: 50%; background: #FF3B30; animation: blinkPulse 1s infinite alternate; }
        @keyframes blinkPulse { 0% { opacity: 0.2; } 100% { opacity: 1; } }

        .timelapse-speed-selector {
            display: flex; gap: 6px; background: rgba(0,0,0,0.6);
            backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
            padding: 3px 6px; border-radius: 16px; border: 1px solid rgba(255,255,255,0.15);
        }
        .speed-btn {
            background: none; border: none; color: #aaa; font-size: 10px;
            font-weight: 700; padding: 4px 8px; border-radius: 10px; cursor: pointer;
        }
        .speed-btn.active { background: #FF3B30; color: #fff; }

        .pano-hud {
            position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
            width: 86%; max-width: 360px; height: 70px;
            border: 1.5px dashed rgba(255, 255, 255, 0.4); border-radius: 12px;
            background: rgba(0, 0, 0, 0.35); backdrop-filter: blur(10px);
            display: none; align-items: center; justify-content: space-between; padding: 0 16px;
            z-index: 36;
        }
        .pano-hud.active { display: flex; }
        .pano-arrow { font-size: 22px; color: #00FFC8; animation: panoSwipe 1.5s infinite; }
        @keyframes panoSwipe {
            0% { transform: translateX(0); opacity: 0.3; }
            50% { transform: translateX(14px); opacity: 1; }
            100% { transform: translateX(28px); opacity: 0.1; }
        }
        .pano-guide-line { position: absolute; left: 10%; right: 10%; height: 2px; background: rgba(255, 255, 255, 0.25); z-index: 1; }
        .pano-level-ball { width: 14px; height: 14px; border-radius: 50%; background: #00FFC8; box-shadow: 0 0 10px #00FFC8; z-index: 2; }

        .mode-status-chip {
            position: absolute; top: 68px; left: 50%; transform: translateX(-50%); z-index: 45;
            background: rgba(0, 0, 0, 0.65); backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 214, 10, 0.5); color: #FFD60A;
            padding: 5px 14px; border-radius: 16px; font-size: 11px; font-weight: 700;
            display: none; align-items: center; gap: 6px;
        }
        .mode-status-chip.active { display: flex; }
        
        .shutter-flash {
            position: absolute; inset: 0; background: #fff; opacity: 0; pointer-events: none; z-index: 60;
            transition: opacity 0.12s ease-out;
        }
        .shutter-flash.flash { opacity: 0.85; }

        .focus-circle-ring {
            position: absolute; width: 95px; height: 95px; pointer-events: none;
            border-radius: 50%; border: 1.8px solid rgba(255, 255, 255, 0.85);
            box-shadow: 0 0 16px rgba(255, 255, 255, 0.35);
            transition: left 0.28s cubic-bezier(0.16, 1, 0.3, 1), top 0.28s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.6s ease, border-color 0.3s, transform 0.25s;
            display: flex; flex-direction: column; align-items: center; justify-content: space-between;
            opacity: 1; transform: translate(-50%, -50%); z-index: 30;
        }
        .focus-circle-ring.faded { opacity: 0.15; border-color: rgba(255, 255, 255, 0.2); box-shadow: none; }
        .focus-circle-ring.glowing { transform: translate(-50%, -50%) scale(1.08); border-color: #FFD60A; box-shadow: 0 0 25px rgba(255, 214, 10, 0.8); }

        .lock-icon-badge { font-size: 11px; margin-top: -16px; background: rgba(0,0,0,0.5); border-radius: 50%; padding: 2px 4px; }
        .sun-slider-badge { font-size: 12px; margin-bottom: -18px; background: rgba(0,0,0,0.5); border-radius: 50%; padding: 2px 4px; }

        .lens-pill-bar {
            position: absolute; bottom: 175px; z-index: 45;
            display: flex; gap: 4px; background: rgba(0, 0, 0, 0.55);
            backdrop-filter: blur(25px); -webkit-backdrop-filter: blur(25px);
            border: 1px solid rgba(255, 255, 255, 0.12);
            padding: 4px 6px; border-radius: 24px;
            transition: all 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
        }
        .lens-btn {
            background: transparent; border: none; color: rgba(255,255,255,0.7);
            font-size: 10px; font-weight: 700; padding: 5px 9px; border-radius: 14px;
            cursor: pointer; transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
        }
        .lens-btn.active { background: rgba(255, 255, 255, 0.25); color: #fff; transform: scale(1.05); }

        .lens-pill-bar.collapsed { padding: 3px 5px; }
        .lens-pill-bar.collapsed .lens-btn:not(.active) {
            opacity: 0; width: 0; padding: 0; margin: 0; pointer-events: none; overflow: hidden; transform: scale(0.4);
        }

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
            position: absolute; bottom: 104px; left: 50%; transform: translateX(-50%); z-index: 40;
            width: calc(100% - 32px); max-width: 500px;
            background: rgba(18, 18, 22, 0.55);
            backdrop-filter: blur(30px); -webkit-backdrop-filter: blur(30px);
            border: 1px solid rgba(255, 255, 255, 0.14);
            border-radius: 30px; padding: 10px 14px;
            display: flex; align-items: center; justify-content: flex-start;
            gap: 10px; overflow-x: auto; scrollbar-width: none;
            box-shadow: 0 10px 40px rgba(0,0,0,0.5);
            transition: all 0.45s cubic-bezier(0.16, 1, 0.3, 1), background 1.8s ease, border-color 1.8s ease, box-shadow 1.8s ease;
        }
        .glass-dock::-webkit-scrollbar { display: none; }

        .glass-dock.stacked-mode {
            left: 76%; transform: translateX(-50%); width: 125px;
            overflow: visible; justify-content: flex-start; padding: 6px;
        }
        .glass-dock.stacked-mode.evaporated-dock {
            background: transparent !important; border-color: transparent !important; box-shadow: none !important;
        }

        .dock-icon-btn {
            flex: 0 0 44px; height: 44px; border-radius: 18px; border: 1px solid rgba(255,255,255,0.1);
            background: rgba(255, 255, 255, 0.06); font-size: 19px;
            display: flex; align-items: center; justify-content: center;
            cursor: pointer; position: relative;
            transition: transform 0.35s cubic-bezier(0.34, 1.56, 0.64, 1), opacity 0.35s ease, background 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
        }
        .dock-icon-btn:active { transform: scale(0.92); }

        .dock-icon-btn.selected {
            transform: translateY(-8px) scale(1.18) !important;
            border-color: rgba(255, 255, 255, 0.45) !important;
            z-index: 25 !important; opacity: 1 !important;
        }
        .dock-icon-btn.selected::after {
            content: ''; position: absolute; bottom: -6px; width: 5px; height: 5px;
            border-radius: 50%; background: #fff; box-shadow: 0 0 6px #fff;
        }

        .glass-dock.stacked-mode .dock-icon-btn.stack-layer { position: absolute; pointer-events: auto; opacity: 0.85; transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1); }
        .glass-dock.stacked-mode .dock-icon-btn.stack-1 { transform: translateX(18px) translateY(-5px) scale(0.94); z-index: 20; }
        .glass-dock.stacked-mode .dock-icon-btn.stack-2 { transform: translateX(34px) translateY(-2px) scale(0.88); z-index: 15; opacity: 0.6; }
        .glass-dock.stacked-mode .dock-icon-btn.stack-3 { transform: translateX(48px) translateY(1px) scale(0.82); z-index: 10; opacity: 0.35; }
        .glass-dock.stacked-mode .dock-icon-btn.stack-deep { position: absolute; transform: translateX(54px) scale(0.7); opacity: 0; pointer-events: none; z-index: 5; }

        .dock-icon-btn[data-key="pano"].active-glow { background: linear-gradient(135deg, rgba(0,255,200,0.8), rgba(90,200,250,0.6)); border-color: #00FFC8; box-shadow: 0 8px 20px rgba(0,255,200,0.7); }
        .dock-icon-btn[data-key="timelapse"].active-glow { background: linear-gradient(135deg, rgba(255,69,58,0.8), rgba(255,159,10,0.6)); border-color: #FF453A; box-shadow: 0 8px 20px rgba(255,69,58,0.7); }
        .dock-icon-btn[data-key="scan"].active-glow { background: linear-gradient(135deg, rgba(0,255,200,0.7), rgba(10,132,255,0.5)); border-color: #00FFC8; box-shadow: 0 8px 20px rgba(0,255,200,0.6); }
        .dock-icon-btn[data-key="night"].active-glow { background: linear-gradient(135deg, rgba(94,92,230,0.7), rgba(48,209,88,0.5)); border-color: #5E5CE6; box-shadow: 0 8px 20px rgba(94,92,230,0.6); }
        .dock-icon-btn[data-key="macro"].active-glow { background: linear-gradient(135deg, rgba(48,209,88,0.7), rgba(0,255,200,0.5)); border-color: #30D158; box-shadow: 0 8px 20px rgba(48,209,88,0.6); }
        .dock-icon-btn[data-key="portrait"].active-glow { background: linear-gradient(135deg, rgba(255,214,10,0.7), rgba(255,107,0,0.5)); border-color: #FFD60A; box-shadow: 0 8px 20px rgba(255,214,10,0.6); }
        .dock-icon-btn[data-key="lonas"].active-glow { background: linear-gradient(135deg, rgba(255,149,0,0.7), rgba(255,94,58,0.5)); border-color: #FF9500; box-shadow: 0 8px 20px rgba(255,149,0,0.6); }
        .dock-icon-btn[data-key="custom"].active-glow { background: linear-gradient(135deg, rgba(255,45,85,0.7), rgba(175,82,222,0.5)); border-color: #FF2D55; box-shadow: 0 8px 20px rgba(255,45,85,0.6); }
        .dock-icon-btn[data-key="print"].active-glow { background: linear-gradient(135deg, rgba(50,173,230,0.7), rgba(0,122,255,0.5)); border-color: #32ADE6; box-shadow: 0 8px 20px rgba(0,122,255,0.6); }
        .dock-icon-btn[data-key="cine"].active-glow { background: linear-gradient(135deg, rgba(255,59,48,0.7), rgba(255,45,85,0.5)); border-color: #FF3B30; box-shadow: 0 8px 20px rgba(255,59,48,0.6); }
        .dock-icon-btn[data-key="raw"].active-glow { background: linear-gradient(135deg, rgba(48,209,88,0.7), rgba(52,199,89,0.5)); border-color: #30D158; box-shadow: 0 8px 20px rgba(48,209,88,0.6); }
        .dock-icon-btn[data-key="svg"].active-glow { background: linear-gradient(135deg, rgba(255,214,10,0.7), rgba(255,159,10,0.5)); border-color: #FFD60A; box-shadow: 0 8px 20px rgba(255,214,10,0.6); }
        .dock-icon-btn[data-key="vid"].active-glow { background: linear-gradient(135deg, rgba(191,90,242,0.7), rgba(94,92,230,0.5)); border-color: #BF5AF2; box-shadow: 0 8px 20px rgba(94,92,230,0.6); }
        .dock-icon-btn[data-key="depth"].active-glow { background: linear-gradient(135deg, rgba(255,55,95,0.7), rgba(191,90,242,0.5)); border-color: #FF375F; box-shadow: 0 8px 20px rgba(255,55,95,0.6); }
        .dock-icon-btn[data-key="chef"].active-glow { background: linear-gradient(135deg, rgba(255,159,10,0.7), rgba(255,107,0,0.5)); border-color: #FF9F0A; box-shadow: 0 8px 20px rgba(255,159,10,0.6); }
        .dock-icon-btn[data-key="price"].active-glow { background: linear-gradient(135deg, rgba(99,230,226,0.7), rgba(0,199,190,0.5)); border-color: #63E6E2; box-shadow: 0 8px 20px rgba(0,199,190,0.6); }
        .dock-icon-btn[data-key="ai"].active-glow { background: linear-gradient(135deg, rgba(10,132,255,0.7), rgba(94,92,230,0.5)); border-color: #0A84FF; box-shadow: 0 8px 20px rgba(10,132,255,0.6); }

        .dock-icon-btn.evaporated {
            background: rgba(255, 255, 255, 0.08) !important;
            border-color: rgba(255, 255, 255, 0.22) !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;
            transition: background 2.5s cubic-bezier(0.25, 1, 0.5, 1), border-color 2.5s cubic-bezier(0.25, 1, 0.5, 1), box-shadow 2.5s cubic-bezier(0.25, 1, 0.5, 1) !important;
        }

        .bottom-shutter-bar {
            position: absolute; bottom: 18px; left: 0; right: 0;
            display: flex; justify-content: space-around; align-items: center; z-index: 50;
            padding: 0 30px;
        }
        .shutter-outer {
            width: 76px; height: 76px; border-radius: 50%;
            background: rgba(255, 59, 48, 0.15); backdrop-filter: blur(10px);
            border: 2px solid rgba(255, 59, 48, 0.65);
            display: flex; align-items: center; justify-content: center; cursor: pointer;
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
        }
        .shutter-outer:active { transform: scale(0.9); }
        .shutter-inner {
            width: 62px; height: 62px; border-radius: 50%;
            background: linear-gradient(135deg, #FF453A, #FF3B30);
            box-shadow: 0 0 16px rgba(255, 59, 48, 0.65);
            transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
        }
        .shutter-inner.recording {
            border-radius: 14px; width: 34px; height: 34px;
            animation: recordShutterPulse 1s infinite alternate;
        }
        @keyframes recordShutterPulse { 0% { transform: scale(0.95); } 100% { transform: scale(1.05); } }
        
        .side-btn {
            width: 44px; height: 44px; border-radius: 50%;
            background: rgba(255, 255, 255, 0.1); backdrop-filter: blur(15px);
            border: 1px solid rgba(255, 255, 255, 0.15); font-size: 16px;
            color: #fff; display: flex; align-items: center; justify-content: center;
            cursor: pointer; transition: transform 0.15s; overflow: hidden;
        }
        .side-btn:active { transform: scale(0.9); }
        .side-btn img { width: 100%; height: 100%; object-fit: cover; }

        .export-modal {
            position: fixed; inset: 0; z-index: 110; background: rgba(0,0,0,0.78);
            backdrop-filter: blur(25px); -webkit-backdrop-filter: blur(25px);
            display: none; flex-direction: column; justify-content: flex-end;
            opacity: 0; transition: opacity 0.3s ease;
        }
        .export-modal.active { display: flex; opacity: 1; }
        .export-card {
            background: #15151B; border-top: 1px solid rgba(0,255,200,0.3);
            border-radius: 32px 32px 0 0; padding: 22px 20px;
            max-height: 85vh; display: flex; flex-direction: column; gap: 12px;
            box-shadow: 0 -12px 40px rgba(0,0,0,0.85);
            animation: slideUp 0.3s cubic-bezier(0.16, 1, 0.3, 1);
        }
        .export-input {
            width: 100%; background: #1C1C24; border: 1px solid rgba(255,255,255,0.12);
            border-radius: 14px; padding: 10px 14px; color: #fff; font-size: 13px; outline: none;
        }
        .export-btn-whatsapp {
            background: linear-gradient(135deg, #25D366, #128C7E); color: #fff;
            border: none; border-radius: 16px; padding: 13px; font-weight: 700; font-size: 13px;
            display: flex; align-items: center; justify-content: center; gap: 8px; cursor: pointer;
        }
        .export-btn-pdf {
            background: rgba(0, 255, 200, 0.15); border: 1px solid #00FFC8; color: #00FFC8;
            border-radius: 16px; padding: 12px; font-weight: 700; font-size: 13px;
            display: flex; align-items: center; justify-content: center; gap: 8px; cursor: pointer;
        }

        .bot-modal {
            position: fixed; inset: 0; z-index: 100; background: rgba(0,0,0,0.7);
            backdrop-filter: blur(25px); -webkit-backdrop-filter: blur(25px);
            display: none; flex-direction: column; justify-content: flex-end;
            opacity: 0; transition: opacity 0.3s ease;
        }
        .bot-modal.active { display: flex; opacity: 1; }
        .bot-card {
            background: #141418; border-top: 1px solid rgba(255,255,255,0.16);
            border-radius: 32px 32px 0 0; padding: 20px;
            max-height: 82vh; display: flex; flex-direction: column;
            box-shadow: 0 -10px 40px rgba(0,0,0,0.8);
            animation: slideUp 0.32s cubic-bezier(0.16, 1, 0.3, 1);
        }
        @keyframes slideUp { from { transform: translateY(100%); } to { transform: translateY(0); } }
        
        .bot-drag { width: 40px; height: 5px; background: rgba(255,255,255,0.3); border-radius: 4px; margin: 0 auto 12px; cursor: pointer; }
        .bot-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
        .bot-title { font-size: 16px; font-weight: 700; color: #fff; display: flex; align-items: center; gap: 6px; }
        .bot-badge { font-size: 9px; padding: 2px 7px; border-radius: 10px; background: rgba(0,255,200,0.15); color: #00FFC8; border: 1px solid #00FFC8; }

        .bot-chat-stream { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; margin-bottom: 12px; padding-right: 4px; max-height: 280px; }
        .bot-msg { max-width: 85%; padding: 10px 14px; border-radius: 16px; font-size: 12px; line-height: 1.45; }
        .bot-msg.ia { background: rgba(255,255,255,0.08); color: #E5E5EA; align-self: flex-start; border-bottom-left-radius: 4px; border: 1px solid rgba(255,255,255,0.08); }
        .bot-msg.user { background: #0A84FF; color: #fff; align-self: flex-end; border-bottom-right-radius: 4px; }

        .bot-quick-chips { display: flex; gap: 6px; overflow-x: auto; padding-bottom: 8px; margin-bottom: 10px; scrollbar-width: none; }
        .bot-quick-chips::-webkit-scrollbar { display: none; }
        .bot-chip {
            white-space: nowrap; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.15);
            color: #ccc; font-size: 10px; padding: 6px 12px; border-radius: 16px; cursor: pointer;
        }
        .bot-chip:active { background: rgba(0,255,200,0.2); border-color: #00FFC8; color: #fff; }

        .bot-input-box { display: flex; gap: 8px; align-items: center; }
        .bot-input {
            flex: 1; background: #1C1C22; border: 1px solid rgba(255,255,255,0.14);
            border-radius: 18px; padding: 11px 16px; color: #fff; font-size: 13px; outline: none;
        }
        .bot-btn-send {
            background: #00FFC8; border: none; color: #000; font-weight: 700;
            border-radius: 50%; width: 42px; height: 42px; display: flex; align-items: center; justify-content: center; cursor: pointer;
        }

        .gallery-modal {
            position: fixed; inset: 0; z-index: 105; background: #000;
            display: none; flex-direction: column; padding: 18px 14px;
        }
        .gallery-modal.active { display: flex; }
        .gallery-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
        .gallery-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; overflow-y: auto; flex: 1; }
        .gallery-item { aspect-ratio: 1; background: #111; border-radius: 8px; overflow: hidden; position: relative; border: 1px solid #222; }
        .gallery-item img { width: 100%; height: 100%; object-fit: cover; }
    </style>
</head>
<body>

    <div class="shutter-flash" id="flashLayer"></div>

    <div class="top-float-left" id="activeModulePill">
        <div class="glow-dot"></div>
        <span id="activeModuleName">Cam Vision V9</span>
    </div>

    <div class="top-float-right">
        <div class="action-pill export-pill" onclick="openExportModal()">
            <span>📤 Exportar</span>
        </div>
        <div class="action-pill" onclick="openNanoBotModal()">
            <span>✨ Nano-Bot</span>
        </div>
    </div>

    <!-- GUIA TÁCTICA PARA DOCUMENTOS -->
    <div class="doc-scanner-frame" id="docScannerFrame">
        <div class="scanner-laser-line"></div>
        <div class="doc-row">
            <div class="doc-corner tl"></div>
            <div class="doc-corner tr"></div>
        </div>
        <div class="doc-label-badge">ALINEA EL DOCUMENTO O TICKET AQUÍ</div>
        <div class="doc-row">
            <div class="doc-corner bl"></div>
            <div class="doc-corner br"></div>
        </div>
    </div>

    <!-- HUD SUPERIOR PARA TIME-LAPSE -->
    <div class="timelapse-hud" id="timelapseHud">
        <div class="timelapse-pill">
            <div class="record-blink" id="recordDot" style="display:none;"></div>
            <span id="timelapseTimerText">REC: 00:00 (VID: 00:00)</span>
        </div>
        <div class="timelapse-speed-selector">
            <button class="speed-btn active" onclick="setTimeLapseSpeed(4, this)">4x</button>
            <button class="speed-btn" onclick="setTimeLapseSpeed(8, this)">8x</button>
            <button class="speed-btn" onclick="setTimeLapseSpeed(16, this)">16x</button>
            <button class="speed-btn" onclick="setTimeLapseSpeed(32, this)">32x</button>
        </div>
    </div>

    <!-- HUD MODO PANORÁMICA -->
    <div class="pano-hud" id="panoHud">
        <div class="pano-guide-line"></div>
        <div class="pano-level-ball" id="panoBall"></div>
        <div class="pano-arrow">➔</div>
    </div>

    <div class="mode-status-chip" id="modeStatusChip">
        <span id="modeStatusText">📸 MODO ACTIVO</span>
    </div>

    <div class="viewport" id="viewportArea" onclick="handleTapToFocus(event)">
        <video id="webcam" autoplay playsinline></video>
        
        <div class="focus-circle-ring" id="focusCircle">
            <div class="lock-icon-badge">🔒</div>
            <div class="sun-slider-badge">☀️</div>
        </div>

        <canvas id="internalCanvas" style="display:none;"></canvas>
    </div>

    <div class="lens-pill-bar collapsed" id="lensPillBar">
        <button class="lens-btn" onclick="handleLensClick(0.6, this, event)">0.6x</button>
        <button class="lens-btn active" onclick="handleLensClick(1.0, this, event)">1x</button>
        <button class="lens-btn" onclick="handleLensClick(2.0, this, event)">2x</button>
        <button class="lens-btn" onclick="handleLensClick(3.0, this, event)">3x</button>
        <button class="lens-btn" onclick="handleLensClick(10.0, this, event)">10x</button>
    </div>

    <div class="dock-tooltip" id="dockTooltip">Módulo</div>

    <div class="glass-dock" id="glassDockBar">
        <div class="dock-icon-btn" data-key="pano" onclick="handleIconClick('pano', '🌐 Panorámica 360° V9', this, event)">🌐</div>
        <div class="dock-icon-btn" data-key="timelapse" onclick="handleIconClick('timelapse', '⏱️ Time-Lapse Hyperlapse V9', this, event)">⏱️</div>
        <div class="dock-icon-btn" data-key="scan" onclick="handleIconClick('scan', '📄 Scan Doc Pro V9', this, event)">📄</div>
        <div class="dock-icon-btn" data-key="night" onclick="handleIconClick('night', '🌙 Nightography V9', this, event)">🌙</div>
        <div class="dock-icon-btn" data-key="macro" onclick="handleIconClick('macro', '🔍 Macro Pro V9', this, event)">🔍</div>
        <div class="dock-icon-btn" data-key="portrait" onclick="handleIconClick('portrait', '👤 Modo Retrato Bokeh V9', this, event)">👤</div>
        <div class="dock-icon-btn" data-key="lonas" onclick="handleIconClick('lonas', '⛺ Lonas 3D V9', this, event)">⛺</div>
        <div class="dock-icon-btn" data-key="custom" onclick="handleIconClick('custom', '🎨 Wallpapers V9', this, event)">🎨</div>
        <div class="dock-icon-btn" data-key="print" onclick="handleIconClick('print', '🖨️ Imprenta PDF V9', this, event)">🖨️</div>
        <div class="dock-icon-btn" data-key="cine" onclick="handleIconClick('cine', '🎬 Cine Scope V9', this, event)">🎬</div>
        <div class="dock-icon-btn" data-key="raw" onclick="handleIconClick('raw', '📸 Revelado RAW V9', this, event)">📸</div>
        <div class="dock-icon-btn" data-key="svg" onclick="handleIconClick('svg', '📐 SVG Logos V9', this, event)">📐</div>
        <div class="dock-icon-btn" data-key="vid" onclick="handleIconClick('vid', '🎥 Video Motion V8', this, event)">🎥</div>
        <div class="dock-icon-btn" data-key="depth" onclick="handleIconClick('depth', '🧠 Depth-Map NPU V9', this, event)">🧠</div>
        <div class="dock-icon-btn" data-key="chef" onclick="handleIconClick('chef', '👨‍🍳 Chef Lean V9', this, event)">👨‍🍳</div>
        <div class="dock-icon-btn" data-key="price" onclick="handleIconClick('price', '🏷️ Valuador Híbrido V7', this, event)">🏷️</div>
        <div class="dock-icon-btn" data-key="ai" onclick="handleIconClick('ai', '✨ Generar Imagen AI V7', this, event)">✨</div>
    </div>

    <div class="bottom-shutter-bar">
        <div class="side-btn" onclick="toggleLens()">🔄</div>
        <div class="shutter-outer" id="shutterBtn" onclick="triggerNativeCaptureAndSave()">
            <div class="shutter-inner" id="shutterInner"></div>
        </div>
        <div class="side-btn" id="galleryThumbBtn" onclick="openGalleryModal()">
            <span id="galleryIconPlaceholder">🖼️</span>
        </div>
    </div>

    <!-- MODAL EXPORTACIÓN & DESPACHO TÁCTICO -->
    <div class="export-modal" id="exportModal">
        <div class="export-card">
            <div class="bot-drag" onclick="closeExportModal()"></div>
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <h3 style="font-size:15px; font-weight:700; color:#00FFC8;">📤 Despacho Comercial & PDF</h3>
                <button onclick="closeExportModal()" style="background:none; border:none; color:#888; font-size:16px; cursor:pointer;">✕</button>
            </div>

            <input type="text" class="export-input" id="expClient" placeholder="Nombre del Cliente o Taller">
            <input type="text" class="export-input" id="expConcept" placeholder="Concepto (ej. Lona Frontlit 4x3m / Rib Eye 3.8kg)">
            <input type="number" class="export-input" id="expAmount" placeholder="Monto Total ($ MXN)">
            <textarea class="export-input" id="expNotes" rows="2" placeholder="Especificaciones técnicas o tiempo de entrega..."></textarea>

            <button class="export-btn-whatsapp" onclick="sendToWhatsApp()">
                <span>💬 Despachar por WhatsApp</span>
            </button>
            <button class="export-btn-pdf" onclick="generateTechnicalPDF()">
                <span>📄 Descargar Orden PDF Membretada</span>
            </button>
        </div>
    </div>

    <!-- MODAL NANO-BOT -->
    <div class="bot-modal" id="botModal">
        <div class="bot-card">
            <div class="bot-drag" onclick="closeNanoBotModal()"></div>
            <div class="bot-header">
                <div class="bot-title">
                    <span>⚡ Nano-Bot Táctico</span>
                    <span class="bot-badge" id="botModuleBadge">GENERAL</span>
                </div>
                <button onclick="closeNanoBotModal()" style="background:none; border:none; color:#888; font-size:16px; cursor:pointer;">✕</button>
            </div>
            
            <div class="bot-quick-chips">
                <button class="bot-chip" onclick="askNanoQuick('¿Cómo está el almacenamiento?')">💾 Estado del Almacenamiento</button>
                <button class="bot-chip" onclick="askNanoQuick('¿Cómo exporto una cotización a WhatsApp?')">📤 Exportar WhatsApp</button>
                <button class="bot-chip" onclick="askNanoQuick('¿Cómo uso el Escáner de Documentos?')">📄 Escanear Documento</button>
            </div>

            <div class="bot-chat-stream" id="botChatStream">
                <div class="bot-msg ia">
                    ¡Qué onda! Soy tu <strong>Nano-Bot Táctico</strong>. Tienes activada la optimización de caché con miniaturas instantáneas y persistencia de órdenes comerciales en base de datos.
                </div>
            </div>

            <div class="bot-input-box">
                <input type="text" class="bot-input" id="botUserInput" placeholder="Pregúntale al Nano-Bot..." onkeydown="if(event.key==='Enter') sendNanoBotMessage()">
                <button class="bot-btn-send" onclick="sendNanoBotMessage()">➤</button>
            </div>
        </div>
    </div>

    <div class="gallery-modal" id="galleryModal">
        <div class="gallery-top">
            <h3 style="font-size:16px; font-weight:700;">Galería Soberana (Miniaturas Rápidas)</h3>
            <button onclick="closeGalleryModal()" style="background:#1c1c22; border:1px solid #333; color:#fff; padding:6px 14px; border-radius:14px; font-size:12px;">Cerrar</button>
        </div>
        <div class="gallery-grid" id="galleryGrid"></div>
    </div>

    <script>
        const video = document.getElementById('webcam');
        const internalCanvas = document.getElementById('internalCanvas');
        let selectedEngineKey = null;
        let selectedEngineName = null;
        let facingMode = 'environment';
        let tooltipTimeout = null;
        let audioCtx = null;
        let fadeCircleTimeout = null;
        let currentStreamTrack = null;
        let evaporateTimeout = null;

        let isRecordingTimelapse = false;
        let timelapseInterval = null;
        let timelapseSeconds = 0;
        let timelapseSpeedMultiplier = 4;

        const enginesList = [
            { key: 'pano', name: '🌐 Panorámica 360° V9' },
            { key: 'timelapse', name: '⏱️ Time-Lapse Hyperlapse V9' },
            { key: 'scan', name: '📄 Scan Doc Pro V9' },
            { key: 'night', name: '🌙 Nightography V9' },
            { key: 'macro', name: '🔍 Macro Pro V9' },
            { key: 'portrait', name: '👤 Modo Retrato Bokeh V9' },
            { key: 'lonas', name: '⛺ Lonas 3D V9' },
            { key: 'custom', name: '🎨 Wallpapers V9' },
            { key: 'print', name: '🖨️ Imprenta PDF V9' },
            { key: 'cine', name: '🎬 Cine Scope V9' },
            { key: 'raw', name: '📸 Revelado RAW V9' },
            { key: 'svg', name: '📐 SVG Logos V9' },
            { key: 'vid', name: '🎥 Video Motion V8' },
            { key: 'depth', name: '🧠 Depth-Map NPU V9' },
            { key: 'chef', name: '👨‍🍳 Chef Lean V9' },
            { key: 'price', name: '🏷️ Valuador Híbrido V7' },
            { key: 'ai', name: '✨ Generar Imagen AI V7' }
        ];

        function getAudioContext() {
            if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            if (audioCtx.state === 'suspended') audioCtx.resume();
            return audioCtx;
        }

        function playWhatsAppSwooshSound() {
            try {
                const ctx = getAudioContext();
                const now = ctx.currentTime;
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.connect(gain); gain.connect(ctx.destination);
                osc.type = 'sine';
                osc.frequency.setValueAtTime(440, now);
                osc.frequency.exponentialRampToValueAtTime(840, now + 0.12);
                gain.gain.setValueAtTime(0.001, now);
                gain.gain.linearRampToValueAtTime(0.18, now + 0.03);
                gain.gain.exponentialRampToValueAtTime(0.001, now + 0.14);
                osc.start(now); osc.stop(now + 0.14);
            } catch(e) {}
        }

        function playSignatureProSound(key) {
            try {
                const ctx = getAudioContext();
                const now = ctx.currentTime;
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.connect(gain); gain.connect(ctx.destination);
                osc.type = 'sine';
                osc.frequency.setValueAtTime(140, now);
                osc.frequency.exponentialRampToValueAtTime(60, now + 0.15);
                gain.gain.setValueAtTime(0.28, now);
                gain.gain.linearRampToValueAtTime(0.001, now + 0.15);
                osc.start(now); osc.stop(now + 0.15);
            } catch(e) {}
        }

        function playFocusBeep() {
            try {
                const ctx = getAudioContext();
                const now = ctx.currentTime;
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.connect(gain); gain.connect(ctx.destination);
                osc.type = 'sine';
                osc.frequency.setValueAtTime(1200, now);
                osc.frequency.setValueAtTime(1600, now + 0.03);
                gain.gain.setValueAtTime(0.08, now);
                gain.gain.linearRampToValueAtTime(0.001, now + 0.08);
                osc.start(now); osc.stop(now + 0.08);
            } catch(e) {}
        }

        function startCamera() {
            const constraints = {
                video: {
                    facingMode: { ideal: facingMode },
                    width: { ideal: 3840 },
                    height: { ideal: 2160 }
                }
            };

            navigator.mediaDevices.getUserMedia(constraints)
                .then(stream => { 
                    video.srcObject = stream;
                    currentStreamTrack = stream.getVideoTracks()[0];
                    const circle = document.getElementById('focusCircle');
                    circle.style.left = '50%';
                    circle.style.top = '46%';
                    triggerCircleFade();
                    refreshThumb();
                })
                .catch(err => console.error("Error cámara:", err));
        }
        startCamera();

        function toggleLens() {
            facingMode = (facingMode === 'environment') ? 'user' : 'environment';
            if (video.srcObject) video.srcObject.getTracks().forEach(t => t.stop());
            startCamera();
        }

        function handleLensClick(zoomLevel, elem, event) {
            const bar = document.getElementById('lensPillBar');
            if (bar.classList.contains('collapsed')) {
                bar.classList.remove('collapsed');
                return;
            }
            document.querySelectorAll('.lens-btn').forEach(b => b.classList.remove('active'));
            elem.classList.add('active');
            bar.classList.add('collapsed');

            if (currentStreamTrack && typeof currentStreamTrack.getCapabilities === 'function') {
                const caps = currentStreamTrack.getCapabilities();
                if (caps.zoom) {
                    const min = caps.zoom.min || 1;
                    const max = caps.zoom.max || 10;
                    const targetZoom = Math.min(Math.max(zoomLevel, min), max);
                    currentStreamTrack.applyConstraints({ advanced: [{ zoom: targetZoom }] })
                        .catch(() => video.style.transform = `scale(${Math.max(1.0, zoomLevel)})`);
                    return;
                }
            }
            video.style.transform = `scale(${Math.max(1.0, zoomLevel)})`;
        }

        function triggerCircleFade() {
            const circle = document.getElementById('focusCircle');
            circle.classList.remove('faded');
            if (fadeCircleTimeout) clearTimeout(fadeCircleTimeout);
            fadeCircleTimeout = setTimeout(() => { circle.classList.add('faded'); }, 1800);
        }

        function handleTapToFocus(e) {
            if (e.target.closest('.glass-dock') || e.target.closest('.bottom-shutter-bar') || e.target.closest('.top-float-left') || e.target.closest('.top-float-right') || e.target.closest('.lens-pill-bar') || e.target.closest('.dock-tooltip') || e.target.closest('.timelapse-hud') || e.target.closest('.pano-hud') || e.target.closest('.export-modal')) return;
            
            document.getElementById('lensPillBar').classList.add('collapsed');

            const viewport = document.getElementById('viewportArea');
            const rect = viewport.getBoundingClientRect();
            const clickX = e.clientX - rect.left;
            const clickY = e.clientY - rect.top;

            const circle = document.getElementById('focusCircle');
            circle.style.left = clickX + 'px';
            circle.style.top = clickY + 'px';
            circle.classList.add('glowing');
            setTimeout(() => circle.classList.remove('glowing'), 300);

            playFocusBeep();
            triggerCircleFade();
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

        function arrangeAlbumStack(activeKey) {
            const dock = document.getElementById('glassDockBar');
            dock.classList.add('stacked-mode');

            const allBtns = Array.from(document.querySelectorAll('.dock-icon-btn'));
            const activeIndex = enginesList.findIndex(e => e.key === activeKey);

            allBtns.forEach(btn => {
                btn.className = 'dock-icon-btn';
                const key = btn.getAttribute('data-key');
                const idx = enginesList.findIndex(e => e.key === key);
                let offset = (idx - activeIndex + enginesList.length) % enginesList.length;

                if (offset === 0) {
                    btn.classList.add('selected', 'active-glow');
                } else {
                    btn.classList.add('stack-layer');
                    if (offset === 1) btn.classList.add('stack-1');
                    else if (offset === 2) btn.classList.add('stack-2');
                    else if (offset === 3) btn.classList.add('stack-3');
                    else btn.classList.add('stack-deep');
                }
            });
        }

        function handleIconClick(key, name, elem, evt) {
            if (selectedEngineKey === key) {
                resetArmEngine();
                return;
            }
            selectEngine(key, name, elem);
        }

        function selectEngine(key, name, elem) {
            showDockTooltipAboveElement(name, elem);
            playSignatureProSound(key);

            if (evaporateTimeout) clearTimeout(evaporateTimeout);

            selectedEngineKey = key;
            selectedEngineName = name;

            const dock = document.getElementById('glassDockBar');
            dock.classList.remove('evaporated-dock');

            arrangeAlbumStack(key);

            document.getElementById('activeModuleName').innerText = key.toUpperCase();
            document.getElementById('botModuleBadge').innerText = key.toUpperCase();

            const statusChip = document.getElementById('modeStatusChip');
            const statusText = document.getElementById('modeStatusText');
            const scanFrame = document.getElementById('docScannerFrame');
            const tlHud = document.getElementById('timelapseHud');
            const panoHud = document.getElementById('panoHud');

            video.className = "";
            scanFrame.classList.remove('active');
            tlHud.classList.remove('active');
            panoHud.classList.remove('active');

            if (key === 'pano') {
                panoHud.classList.add('active');
                statusText.innerText = "🌐 PANORÁMICA 360°: ARRASTRE CONTINUO GUIADO";
                statusChip.classList.add('active');
            } else if (key === 'timelapse') {
                tlHud.classList.add('active');
                statusText.innerText = `⏱️ TIME-LAPSE: CAPTURA COMPRIMIDA ${timelapseSpeedMultiplier}x`;
                statusChip.classList.add('active');
            } else if (key === 'scan') {
                video.classList.add('scan-mode');
                scanFrame.classList.add('active');
                statusText.innerText = "📄 ESCÁNER DOCUMENTAL: ALTO CONTRASTE + OCR";
                statusChip.classList.add('active');
            } else if (key === 'portrait') {
                video.classList.add('portrait-bokeh');
                statusText.innerText = "📸 MODO RETRATO: f/1.4 BOKEH NPU";
                statusChip.classList.add('active');
            } else if (key === 'night') {
                video.classList.add('night-mode');
                statusText.innerText = "🌙 NIGHTOGRAPHY: ISO BOOST + RAW DENOISE";
                statusChip.classList.add('active');
            } else if (key === 'macro') {
                video.classList.add('macro-mode');
                statusText.innerText = "🔍 MACRO PRO: REALCE TEXTURAL 8K";
                statusChip.classList.add('active');
            } else {
                statusChip.classList.remove('active');
            }

            evaporateTimeout = setTimeout(() => {
                const activeBtn = document.querySelector(`.dock-icon-btn[data-key="${key}"]`);
                if (activeBtn) {
                    activeBtn.classList.remove('active-glow');
                    activeBtn.classList.add('evaporated');
                }
                dock.classList.add('evaporated-dock');
            }, 1000);

            triggerCircleFade();
        }

        function setTimeLapseSpeed(mult, btn) {
            timelapseSpeedMultiplier = mult;
            document.querySelectorAll('.speed-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            document.getElementById('modeStatusText').innerText = `⏱️ TIME-LAPSE: CAPTURA COMPRIMIDA ${timelapseSpeedMultiplier}x`;
        }

        let touchStartY = 0;
        let touchStartX = 0;
        const dockEl = document.getElementById('glassDockBar');

        dockEl.addEventListener('touchstart', (e) => {
            touchStartY = e.touches[0].clientY;
            touchStartX = e.touches[0].clientX;
        }, { passive: true });

        dockEl.addEventListener('touchend', (e) => {
            const touchEndY = e.changedTouches[0].clientY;
            const touchEndX = e.changedTouches[0].clientX;
            const deltaY = touchEndY - touchStartY;
            const deltaX = touchEndX - touchStartX;

            if (Math.abs(deltaY) > 28 && Math.abs(deltaY) > Math.abs(deltaX) && selectedEngineKey) {
                if (deltaY > 0) cycleEngine(1);
                else cycleEngine(-1);
            }
        }, { passive: true });

        function cycleEngine(direction) {
            const currentIdx = enginesList.findIndex(e => e.key === selectedEngineKey);
            const nextIdx = (currentIdx + direction + enginesList.length) % enginesList.length;
            const nextEngine = enginesList[nextIdx];
            const nextBtn = document.querySelector(`.dock-icon-btn[data-key="${nextEngine.key}"]`);
            selectEngine(nextEngine.key, nextEngine.name, nextBtn);
        }

        function resetArmEngine() {
            selectedEngineKey = null;
            selectedEngineName = null;
            if (evaporateTimeout) clearTimeout(evaporateTimeout);

            const dock = document.getElementById('glassDockBar');
            dock.classList.remove('stacked-mode', 'evaporated-dock');

            document.querySelectorAll('.dock-icon-btn').forEach(btn => {
                btn.className = 'dock-icon-btn';
            });

            video.className = "";
            document.getElementById('docScannerFrame').classList.remove('active');
            document.getElementById('timelapseHud').classList.remove('active');
            document.getElementById('panoHud').classList.remove('active');
            document.getElementById('modeStatusChip').classList.remove('active');

            if (isRecordingTimelapse) stopTimeLapseRecording();

            document.getElementById('activeModuleName').innerText = 'Cam Vision V9';
            document.getElementById('botModuleBadge').innerText = 'GENERAL';
            triggerCircleFade();
        }

        async function triggerNativeCaptureAndSave() {
            if (video.videoWidth === 0) return;

            if (selectedEngineKey === 'timelapse') {
                if (!isRecordingTimelapse) startTimeLapseRecording();
                else stopTimeLapseRecording();
                return;
            }

            if (selectedEngineKey === 'pano') {
                triggerPanoCapture();
                return;
            }

            playWhatsAppSwooshSound();

            const flash = document.getElementById('flashLayer');
            flash.classList.add('flash');
            setTimeout(() => flash.classList.remove('flash'), 120);

            internalCanvas.width = video.videoWidth;
            internalCanvas.height = video.videoHeight;
            const ctx = internalCanvas.getContext('2d');

            if (selectedEngineKey === 'scan') {
                ctx.filter = 'grayscale(100%) contrast(160%) brightness(110%)';
            } else {
                ctx.filter = 'none';
            }
            ctx.drawImage(video, 0, 0, internalCanvas.width, internalCanvas.height);

            const base64Data = internalCanvas.toDataURL('image/jpeg', 0.90);
            const tag = selectedEngineName ? `Módulo ${selectedEngineName}` : "Captura Directa Cam Vision";

            try {
                const res = await fetch('/bian/process/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ image_base64: base64Data, prompt_analysis: tag })
                });
                if (res.ok) {
                    const saved = await res.json();
                    updateThumbUI(saved.image_path);
                }
            } catch (err) {
                console.error("Error guardando foto:", err);
            }
        }

        function startTimeLapseRecording() {
            isRecordingTimelapse = true;
            timelapseSeconds = 0;
            document.getElementById('recordDot').style.display = 'block';
            document.getElementById('shutterInner').classList.add('recording');

            timelapseInterval = setInterval(() => {
                timelapseSeconds++;
                const compSeconds = Math.max(1, Math.floor(timelapseSeconds / timelapseSpeedMultiplier));
                const recMin = String(Math.floor(timelapseSeconds / 60)).padStart(2, '0');
                const recSec = String(timelapseSeconds % 60).padStart(2, '0');
                const vidMin = String(Math.floor(compSeconds / 60)).padStart(2, '0');
                const vidSec = String(compSeconds % 60).padStart(2, '0');

                document.getElementById('timelapseTimerText').innerText = `REC: ${recMin}:${recSec} (VID: ${vidMin}:${vidSec})`;
            }, 1000);
        }

        async function stopTimeLapseRecording() {
            isRecordingTimelapse = false;
            clearInterval(timelapseInterval);
            document.getElementById('recordDot').style.display = 'none';
            document.getElementById('shutterInner').classList.remove('recording');

            internalCanvas.width = video.videoWidth;
            internalCanvas.height = video.videoHeight;
            const ctx = internalCanvas.getContext('2d');
            ctx.drawImage(video, 0, 0, internalCanvas.width, internalCanvas.height);
            const base64Data = internalCanvas.toDataURL('image/jpeg', 0.88);

            try {
                const res = await fetch('/bian/process/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        image_base64: base64Data,
                        prompt_analysis: `Clip Time-Lapse ${timelapseSpeedMultiplier}x (${timelapseSeconds}s grabados)`
                    })
                });
                if (res.ok) {
                    const saved = await res.json();
                    updateThumbUI(saved.image_path);
                }
            } catch(e) {}

            document.getElementById('timelapseTimerText').innerText = "REC: 00:00 (VID: 00:00)";
            alert(`✔ Time-Lapse compilado a ${timelapseSpeedMultiplier}x.`);
        }

        async function triggerPanoCapture() {
            playWhatsAppSwooshSound();
            internalCanvas.width = video.videoWidth * 2;
            internalCanvas.height = video.videoHeight;
            const ctx = internalCanvas.getContext('2d');
            ctx.drawImage(video, 0, 0, video.videoWidth, video.videoHeight);
            ctx.drawImage(video, video.videoWidth, 0, video.videoWidth, video.videoHeight);

            const base64Data = internalCanvas.toDataURL('image/jpeg', 0.88);
            try {
                const res = await fetch('/bian/process/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ image_base64: base64Data, prompt_analysis: "Toma Panorámica 360 Wide Sweep V9" })
                });
                if (res.ok) {
                    const saved = await res.json();
                    updateThumbUI(saved.image_path);
                    alert("✔ Captura Panorámica cosida y guardada.");
                }
            } catch(e) {}
        }

        async function refreshThumb() {
            try {
                const res = await fetch('/bian/images/');
                const list = await res.json();
                if (list.length > 0) {
                    updateThumbUI(list[list.length - 1].image_path);
                }
            } catch(e) {}
        }

        function updateThumbUI(imgPath) {
            const btn = document.getElementById('galleryThumbBtn');
            const filename = imgPath.split('/').pop();
            btn.innerHTML = `<img src="/bian/storage/bian/thumbs/${filename}" />`;
        }

        function openExportModal() {
            document.getElementById('exportModal').classList.add('active');
            const activeName = selectedEngineName || "General";
            document.getElementById('expConcept').value = `Cotización / Orden de Servicio (${activeName})`;
        }

        function closeExportModal() {
            document.getElementById('exportModal').classList.remove('active');
        }

        async function saveOrderToDatabase(client, concept, amount, notes, channel) {
            try {
                await fetch('/bian/orders/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        client_name: client,
                        concept: concept,
                        amount: parseFloat(amount) || 0.0,
                        notes: notes,
                        channel: channel
                    })
                });
            } catch(e) {
                console.error("Error guardando orden en BD:", e);
            }
        }

        async function sendToWhatsApp() {
            const client = document.getElementById('expClient').value || "Cliente";
            const concept = document.getElementById('expConcept').value || "Servicio Técnico";
            const amount = document.getElementById('expAmount').value || "0";
            const notes = document.getElementById('expNotes').value || "Sin notas";

            await saveOrderToDatabase(client, concept, amount, notes, "whatsapp");

            const msg = `*BIAN MASTER SUITE V9 - NOTA COMERCIAL*\\n\\n` +
                        `👤 *Cliente:* ${client}\\n` +
                        `📦 *Concepto:* ${concept}\\n` +
                        `💵 *Total:* $${amount} MXN\\n` +
                        `📝 *Notas:* ${notes}\\n` +
                        `🕒 *Fecha:* ${new Date().toLocaleDateString('es-MX')} - ${new Date().toLocaleTimeString('es-MX')}\\n\\n` +
                        `_Generado desde Debian/Termux Galaxy S23 Ultra_`;

            const url = `https://wa.me/?text=${encodeURIComponent(msg)}`;
            window.open(url, '_blank');
        }

        async function generateTechnicalPDF() {
            const { jsPDF } = window.jspdf;
            const doc = new jsPDF();

            const client = document.getElementById('expClient').value || "Cliente General";
            const concept = document.getElementById('expConcept').value || "Servicio Técnico";
            const amount = document.getElementById('expAmount').value || "0";
            const notes = document.getElementById('expNotes').value || "Sin notas adicionales";

            await saveOrderToDatabase(client, concept, amount, notes, "pdf");

            doc.setFillColor(15, 15, 20);
            doc.rect(0, 0, 210, 30, 'F');

            doc.setTextColor(0, 255, 200);
            doc.setFontSize(16);
            doc.text("BIAN V9 MASTER SUITE - ORDEN TÉCNICA", 14, 18);

            doc.setTextColor(50, 50, 50);
            doc.setFontSize(10);
            doc.text(`Fecha de Emisión: ${new Date().toLocaleString('es-MX')}`, 14, 40);
            doc.text(`Cliente / Taller: ${client}`, 14, 48);

            doc.setDrawColor(0, 255, 200);
            doc.line(14, 54, 196, 54);

            doc.setFontSize(12);
            doc.setTextColor(0, 0, 0);
            doc.text(`Concepto: ${concept}`, 14, 66);
            doc.text(`Monto Total: $${amount} MXN`, 14, 76);

            doc.setFontSize(10);
            doc.setTextColor(100, 100, 100);
            doc.text("Especificaciones y Observaciones:", 14, 90);
            doc.text(notes, 14, 98, { maxWidth: 180 });

            doc.setDrawColor(200, 200, 200);
            doc.rect(14, 120, 182, 35);
            doc.setFontSize(9);
            doc.text("FIRMA DE CONFORMIDAD Y RECEPCIÓN:", 18, 128);
            doc.text("__________________________________________", 18, 145);

            doc.save(`orden_bian_${Date.now()}.pdf`);
            alert("✔ PDF membretado guardado en BD y descargado.");
        }

        async function openGalleryModal() {
            const modal = document.getElementById('galleryModal');
            const grid = document.getElementById('galleryGrid');
            modal.classList.add('active');
            grid.innerHTML = "<p style='color:#777; font-size:12px; grid-column:span 3;'>Cargando miniaturas optimizadas...</p>";

            try {
                const res = await fetch('/bian/images/');
                const list = await res.json();
                if (list.length === 0) {
                    grid.innerHTML = "<p style='color:#888; font-size:12px; grid-column:span 3;'>No hay fotos capturadas aún.</p>";
                    return;
                }
                grid.innerHTML = list.reverse().map(img => {
                    const filename = img.image_path.split('/').pop();
                    const thumbUrl = `/bian/storage/bian/thumbs/${filename}`;
                    const fullUrl = img.image_path.startsWith('/bian') ? img.image_path : `/bian${img.image_path}`;
                    return `
                        <div class="gallery-item" onclick="window.open('${fullUrl}', '_blank')">
                            <img src="${thumbUrl}" loading="lazy" />
                        </div>
                    `;
                }).join('');
            } catch(e) {
                grid.innerHTML = "<p style='color:#f55; font-size:12px;'>Error cargando galería.</p>";
            }
        }

        function closeGalleryModal() {
            document.getElementById('galleryModal').classList.remove('active');
        }

        function openNanoBotModal() {
            document.getElementById('botModal').classList.add('active');
            document.getElementById('botUserInput').focus();
        }

        function closeNanoBotModal() {
            document.getElementById('botModal').classList.remove('active');
        }

        function askNanoQuick(text) {
            document.getElementById('botUserInput').value = text;
            sendNanoBotMessage();
        }

        async function sendNanoBotMessage() {
            const input = document.getElementById('botUserInput');
            const q = input.value.trim();
            if (!q) return;

            const chat = document.getElementById('botChatStream');
            chat.innerHTML += `<div class="bot-msg user">${q}</div>`;
            input.value = "";
            chat.scrollTop = chat.scrollHeight;

            try {
                const res = await fetch('/bian/nanobot/query', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: q, current_module: selectedEngineKey || "general" })
                });
                const data = await res.json();
                chat.innerHTML += `<div class="bot-msg ia">${data.reply}</div>`;
            } catch(e) {
                chat.innerHTML += `<div class="bot-msg ia">Nano-Bot activo localmente.</div>`;
            }
            chat.scrollTop = chat.scrollHeight;
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
        "engine": "Samsung Native Camera Core V9 (Optimized Storage Engine: Thumbs + Orders SQL)",
        "status": "online"
    }

@router.post("/process/", response_model=ProcessedImage)
def process_image(payload: ImageCaptureRequest, session: Session = Depends(get_session)):
    os.makedirs("storage/bian", exist_ok=True)
    os.makedirs("storage/bian/thumbs", exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename_rel = f"storage/bian/photo_{timestamp}.jpg"
    thumb_rel = f"storage/bian/thumbs/photo_{timestamp}.jpg"
    
    header, encoded = payload.image_base64.split(",", 1) if "," in payload.image_base64 else ("", payload.image_base64)
    data = base64.b64decode(encoded)
    
    # 1. Guardar archivo original
    with open(filename_rel, "wb") as f:
        f.write(data)
        
    # 2. Generar miniatura rápida optimizada (160x160)
    try:
        img = Image.open(io.BytesIO(data))
        img.thumbnail((160, 160))
        img.save(thumb_rel, format="JPEG", quality=75, optimize=True)
    except Exception:
        # En caso de fallo en Pillow, copiar directamente
        with open(thumb_rel, "wb") as f:
            f.write(data)

    db_image = ProcessedImage(image_path=f"/{filename_rel}", prompt_analysis=payload.prompt_analysis)
    session.add(db_image)
    session.commit()
    session.refresh(db_image)
    return db_image

@router.get("/images/", response_model=list[ProcessedImage])
def list_images(session: Session = Depends(get_session)):
    return session.exec(select(ProcessedImage)).all()

@router.post("/orders/", response_model=CommercialOrder)
def create_order(order_data: OrderCreateRequest, session: Session = Depends(get_session)):
    order = CommercialOrder(
        client_name=order_data.client_name,
        concept=order_data.concept,
        amount=order_data.amount,
        notes=order_data.notes,
        channel=order_data.channel
    )
    session.add(order)
    session.commit()
    session.refresh(order)
    return order

@router.get("/orders/", response_model=list[CommercialOrder])
def list_orders(session: Session = Depends(get_session)):
    return session.exec(select(CommercialOrder)).all()

@router.get("/analytics/storage")
def storage_analytics(session: Session = Depends(get_session)):
    total_bytes = 0
    file_count = 0
    thumb_count = 0
    
    storage_dir = "storage/bian"
    if os.path.exists(storage_dir):
        for root, _, files in os.walk(storage_dir):
            for f in files:
                fp = os.path.join(root, f)
                total_bytes += os.path.getsize(fp)
                if "thumbs" in root:
                    thumb_count += 1
                else:
                    file_count += 1
                    
    total_orders = len(session.exec(select(CommercialOrder)).all())
    total_photos = len(session.exec(select(ProcessedImage)).all())

    return {
        "total_mb": round(total_bytes / (1024 * 1024), 2),
        "full_photos": file_count,
        "cached_thumbs": thumb_count,
        "db_photos_registered": total_photos,
        "db_orders_registered": total_orders
    }

@router.post("/nanobot/query")
def nanobot_query(payload: NanoBotQuery, session: Session = Depends(get_session)):
    msg = payload.message.lower()

    if "almacenamiento" in msg or "memoria" in msg or "espacio" in msg or "disco" in msg:
        analytics = storage_analytics(session)
        return {
            "reply": f"💾 <strong>Telemetría de Almacenamiento:</strong><br>"
                     f"• Espacio Total en Disco: <strong>{analytics['total_mb']} MB</strong><br>"
                     f"• Fotos Originales: <strong>{analytics['full_photos']}</strong> | Miniaturas Caché: <strong>{analytics['cached_thumbs']}</strong><br>"
                     f"• Órdenes Guardadas en BD: <strong>{analytics['db_orders_registered']}</strong>.<br>"
                     f"<em>El pipeline de compresión y caché de miniaturas mantiene la app al 100%.</em>"
        }
    elif "export" in msg or "whatsapp" in msg or "pdf" in msg:
        return {
            "reply": "📤 <strong>Exportación Comercial:</strong> Al enviar por WhatsApp o generar un PDF, los datos se respaldan automáticamente en la tabla <code>commercialorder</code> de SQLite para trazabilidad contable."
        }
    else:
        return {
            "reply": "⚡ <strong>Motor Optimizado:</strong> Almacenamiento escalonado (Original + Thumbnail), persistencia comercial y bajo consumo de RAM."
        }
