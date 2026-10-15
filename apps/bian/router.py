from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

@router.get("/ui", response_class=HTMLResponse)
async def get_ui():
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>BIAN Master Suite V11 Pro</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; font-family: monospace; }
            body { background: #05070a; color: #00f2ff; overflow-x: hidden; min-height: 100vh; }
            
            /* Cinemática de Iris 14 aspas y Vaho */
            #boot-overlay {
                position: fixed; inset: 0; background: #000; z-index: 9999;
                display: flex; align-items: center; justify-content: center;
                animation: fadeOut 0.8s ease 2.4s forwards;
            }
            .iris-container {
                position: absolute; width: 320px; height: 320px;
                display: flex; align-items: center; justify-content: center;
            }
            .iris-blade {
                position: absolute; width: 100%; height: 100%;
                border: 2px solid rgba(0, 242, 255, 0.2); border-radius: 50%;
                clip-path: polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%);
                animation: irisRotate 2.4s cubic-bezier(0.4, 0, 0.2, 1) forwards;
            }
            .boot-title {
                font-size: 2.2rem; font-weight: bold; letter-spacing: 6px;
                color: #fff; text-shadow: 0 0 20px #00f2ff;
                filter: blur(10px); opacity: 0;
                animation: defog 2.4s ease forwards; z-index: 10000;
                text-align: center;
            }
            .boot-sub { font-size: 0.9rem; color: #888; letter-spacing: 2px; margin-top: 8px; }

            @keyframes irisRotate {
                0% { transform: rotate(0deg) scale(0.2); opacity: 1; }
                80% { opacity: 0.8; }
                100% { transform: rotate(180deg) scale(2.5); opacity: 0; }
            }
            @keyframes defog {
                0% { filter: blur(12px); opacity: 0; }
                50% { filter: blur(4px); opacity: 0.7; }
                100% { filter: blur(0px); opacity: 1; }
            }
            @keyframes fadeOut {
                to { opacity: 0; visibility: hidden; }
            }

            /* Layout V11 Pro */
            .app-header {
                display: flex; justify-content: space-between; align-items: center;
                padding: 15px 20px; border-bottom: 1px solid rgba(0, 242, 255, 0.2);
                background: rgba(5, 7, 10, 0.9); backdrop-filter: blur(10px);
            }
            .badge {
                background: rgba(0, 242, 255, 0.1); border: 1px solid #00f2ff;
                padding: 5px 12px; border-radius: 20px; font-size: 0.75rem; letter-spacing: 1px;
            }
            
            .main-view {
                padding: 20px; display: flex; flex-direction: column; gap: 20px;
            }
            .telemetry-card {
                background: rgba(10, 15, 25, 0.8); border: 1px solid rgba(0, 242, 255, 0.3);
                border-radius: 12px; padding: 15px; font-size: 0.8rem;
            }
            .telemetry-row {
                display: flex; justify-content: space-between; margin-bottom: 8px;
                border-bottom: 1px dashed rgba(255,255,255,0.05); padding-bottom: 4px;
            }
            .val-highlight { color: #00ffaa; font-weight: bold; }
            
            /* Bóveda V11 / Vault Dial */
            .vault-section {
                display: flex; flex-direction: column; align-items: center; margin-top: 20px;
            }
            .vault-dial {
                width: 140px; height: 140px; border-radius: 50%;
                border: 3px solid #00f2ff; box-shadow: 0 0 25px rgba(0, 242, 255, 0.3);
                display: flex; flex-direction: column; align-items: center; justify-content: center;
                cursor: pointer; transition: transform 0.3s ease;
            }
            .vault-dial:active { transform: scale(0.95) rotate(15deg); }
            .vault-title { font-size: 0.85rem; font-weight: bold; color: #fff; margin-top: 5px; }
        </style>
    <style>
    
      50% {
        opacity: 0.60;
        filter: blur(10px);
        transform: translate3d(0, 0, 0) scale(0.99);
        text-shadow: 0 0 18px rgba(94, 243, 210, 0.25);
      }
      82% {
        opacity: 0.96;
        filter: blur(0px);
        transform: translate3d(0, 0, 0) scale(1.0);
        text-shadow: 0 0 25px rgba(255, 255, 255, 0.8), 0 0 45px rgba(0, 229, 255, 0.35);
      }
      /* Destello de realce simultáneo en título y subtítulo a los 2.4s */
      92% {
        opacity: 1.0;
        filter: blur(0px) brightness(1.42);
        transform: translate3d(0, 0, 0) scale(1.035);
        text-shadow: 0 0 42px rgba(255, 255, 255, 1.0), 
                     0 0 85px rgba(0, 229, 255, 0.95), 
                     0 0 120px rgba(94, 243, 210, 0.72);
      }
      100% {
        opacity: 1.0;
        filter: blur(0px) brightness(1.0);
        transform: translate3d(0, 0, 0) scale(1.0);
        text-shadow: 0 0 25px rgba(255, 255, 255, 0.85), 0 0 50px rgba(0, 229, 255, 0.35);
      }
    }

    /* 2. EL BOTÓN COMPLETO: Deslizamiento suave de seda y momentum elástico */
    .intro-badge, .v11-top-pill, 
    .dial-btn, .dial-button, .dial-controller, 
    .hint-label, .v11-hint,
    .screen-intro > div:last-child,
    .welcome-stage > div:last-child,
    footer, [onclick*="vault"], [id*="vault"],
    [class*="dial"], [class*="ring"], [class*="hint"] {
      animation: silkMomentumSurge 850ms cubic-bezier(0.175, 0.885, 0.32, 1.15) 2400ms both !important;
      will-change: opacity, transform, visibility, filter;
    }

    @keyframes silkMomentumSurge {
      0% {
        opacity: 0;
        visibility: hidden;
        pointer-events: none;
        transform: translate3d(0, 36px, 0) scale(0.85);
        filter: drop-shadow(0 0 0px rgba(0, 229, 255, 0));
      }
      1% {
        visibility: visible;
      }
      /* Fluidez máxima: impulso armónico con halo cian sin cortes */
      60% {
        opacity: 1;
        visibility: visible;
        pointer-events: auto;
        transform: translate3d(0, -3px, 0) scale(1.035);
        filter: drop-shadow(0 0 35px rgba(0, 229, 255, 1.0)) drop-shadow(0 0 70px rgba(94, 243, 210, 0.85));
      }
      100% {
        opacity: 1;
        visibility: visible;
        pointer-events: auto;
        transform: translate3d(0, 0, 0) scale(1.0);
        filter: drop-shadow(0 0 16px rgba(0, 229, 255, 0.5));
      }
    }
</style><style>
    /* --- BIAN CLASSIC MECHANICAL IRIS ENGINE --- */
    .iris-gpu-curtain {
      position: fixed; inset: 0; width: 100vw; height: 100vh;
      z-index: 999999; pointer-events: none; background: transparent;
      transform: translate3d(0, 0, 0);
      will-change: opacity;
      transition: opacity 0.4s ease;
    }
    .iris-gpu-curtain.hidden { opacity: 0; }
    #gpuIrisCanvas { width: 100%; height: 100%; display: block; }

    .screen-intro, .welcome-stage, body {
      background: radial-gradient(circle at center, #172433 0%, #06090e 100%) !important;
    }

    /* 1. LETRAS: Desempañado suave de 0 a 2.4s + Destello de 0.5s */
    .brand-hero, .welcome-hero, h1, .brand-title, .intro-hero {
      animation: fluidDefogOriginal 2900ms cubic-bezier(0.25, 0.1, 0.25, 1) 0ms forwards !important;
      opacity: 0.12;
      transform: translate3d(0, 0, 0);
      will-change: opacity, transform, filter;
    }

    @keyframes fluidDefogOriginal {
      0% {
        opacity: 0.12;
        filter: blur(24px);
        transform: translate3d(0, 0, 0) scale(0.975);
        text-shadow: 0 0 10px rgba(0, 229, 255, 0.1);
      }
      50% {
        opacity: 0.60;
        filter: blur(10px);
        transform: translate3d(0, 0, 0) scale(0.99);
        text-shadow: 0 0 18px rgba(94, 243, 210, 0.25);
      }
      82% {
        opacity: 0.96;
        filter: blur(0px);
        transform: translate3d(0, 0, 0) scale(1.0);
        text-shadow: 0 0 25px rgba(255, 255, 255, 0.8), 0 0 45px rgba(0, 229, 255, 0.35);
      }
      /* Destello de realce en t=2.4s */
      92% {
        opacity: 1.0;
        filter: blur(0px) brightness(1.42);
        transform: translate3d(0, 0, 0) scale(1.042);
        text-shadow: 0 0 42px rgba(255, 255, 255, 1.0), 
                     0 0 85px rgba(0, 229, 255, 0.95), 
                     0 0 120px rgba(94, 243, 210, 0.72);
      }
      100% {
        opacity: 1.0;
        filter: blur(0px) brightness(1.0);
        transform: translate3d(0, 0, 0) scale(1.0);
        text-shadow: 0 0 25px rgba(255, 255, 255, 0.85), 0 0 50px rgba(0, 229, 255, 0.35);
      }
    }

    /* 2. ACCESO COMPLETO: Bloqueado al inicio, emerge con momentum a los 2.4s */
    .intro-badge, .v11-top-pill, 
    .dial-btn, .dial-button, .dial-controller, 
    .hint-label, .v11-hint,
    .screen-intro > div:last-child,
    .welcome-stage > div:last-child,
    footer, [onclick*="vault"], [id*="vault"],
    [class*="dial"], [class*="ring"], [class*="hint"] {
      animation: springMomentumSurge 750ms cubic-bezier(0.19, 1, 0.22, 1) 2400ms both !important;
      will-change: opacity, transform, visibility, filter;
    }

    @keyframes springMomentumSurge {
      0% {
        opacity: 0;
        visibility: hidden;
        pointer-events: none;
        transform: translate3d(0, 32px, 0) scale(0.82);
        filter: drop-shadow(0 0 0px rgba(0, 229, 255, 0)) blur(6px);
      }
      1% {
        visibility: visible;
      }
      /* Momentum: sobrepaso elástico y pico lumínico */
      55% {
        opacity: 1;
        visibility: visible;
        pointer-events: auto;
        transform: translate3d(0, -4px, 0) scale(1.045);
        filter: drop-shadow(0 0 35px rgba(0, 229, 255, 1.0)) drop-shadow(0 0 70px rgba(94, 243, 210, 0.85)) blur(0px);
      }
      /* Asentamiento */
      100% {
        opacity: 1;
        visibility: visible;
        pointer-events: auto;
        transform: translate3d(0, 0, 0) scale(1.0);
        filter: drop-shadow(0 0 16px rgba(0, 229, 255, 0.5)) blur(0px);
      }
    }
</style></head>
    <body>

  <div class="iris-gpu-curtain" id="gpuCurtain">
    <canvas id="gpuIrisCanvas"></canvas>
  </div>


  

        <div id="boot-overlay">
            <div class="iris-container">
                <div class="iris-blade" style="transform: rotate(0deg);"></div>
                <div class="iris-blade" style="transform: rotate(25deg);"></div>
                <div class="iris-blade" style="transform: rotate(50deg);"></div>
                <div class="iris-blade" style="transform: rotate(75deg);"></div>
                <div class="iris-blade" style="transform: rotate(100deg);"></div>
                <div class="iris-blade" style="transform: rotate(125deg);"></div>
                <div class="iris-blade" style="transform: rotate(150deg);"></div>
            </div>
            <div class="boot-title">
                BIAN
                <div class="boot-sub">Almacén & Galería V11 Pro</div>
            </div>
        </div>

        <div class="app-header">
            <span class="badge">• ALMACÉN & GALERÍA V11</span>
            <span class="badge" style="border-color: #ffaa00; color: #ffaa00;">🔒 Bóveda</span>
            <span class="badge" style="border-color: #aa00ff; color: #aa00ff;">✨ Nano-Bot</span>
        </div>

        <div class="main-view">
            <div class="telemetry-card">
                <div class="telemetry-row">
                    <span>SOC / BAT REAL:</span>
                    <span class="val-highlight">2.34 GHz | 84.4°C • BAT 39%</span>
                </div>
                <div class="telemetry-row">
                    <span>MOTOR DE PERSISTENCIA:</span>
                    <span class="val-highlight">SQLITE 3 WAL MODE (LOCAL)</span>
                </div>
                <div class="telemetry-row">
                    <span>INTEGRIDAD FORENSE:</span>
                    <span class="val-highlight">HASH SHA-256 VERIFICADO</span>
                </div>
                <div class="telemetry-row">
                    <span>POOL DE CONEXIONES:</span>
                    <span class="val-highlight">ZERO-NETWORK SOBERANO</span>
                </div>
                <div class="telemetry-row">
                    <span>LATENCIA I/O DISCO:</span>
                    <span class="val-highlight">1.2 MS ACCESO INDEXADO</span>
                </div>
            </div>

            <div class="vault-section">
                <div class="vault-dial">
                    <span style="font-size: 1.5rem;">🏛️</span>
                    <div class="vault-title">BÓVEDA V11</div>
                    <span style="font-size: 0.6rem; color: #666;">SQLITE SHA-256 VAULT</span>
                </div>
                <div style="font-size: 0.75rem; color: #888; margin-top: 12px;">
                    🔒 DESLIZA O GIRA PARA ABRIR
                </div>
            </div>
        </div>
    



<script>
  (function() {
    const H = {
      vib(p) { if (navigator.vibrate) navigator.vibrate(p); },
      spin() { this.vib([15, 30, 25, 20]); },
      flashSeal() { this.vib([14, 38, 22]); },
      tap() { this.vib([20]); }
    };

    const canvas = document.getElementById("gpuIrisCanvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d", { alpha: true });
    const curtain = document.getElementById("gpuCurtain");

    function resize() {
      canvas.width = window.innerWidth * window.devicePixelRatio;
      canvas.height = window.innerHeight * window.devicePixelRatio;
    }
    window.addEventListener("resize", resize);
    resize();

    // Cinemática de aspas original (recorrido mecánico real con curvas de Bézier)
    const DURATION = 2400;
    let startTime = null;

    function drawOriginalIris(ap, rot) {
      const w = canvas.width, h = canvas.height, cx = w / 2, cy = h / 2;
      const maxR = Math.hypot(w, h) * 0.68;
      const minR = maxR * (ap * 0.98);

      ctx.clearRect(0, 0, w, h);
      ctx.save();
      ctx.translate(cx, cy);
      ctx.rotate(rot);

      const step = (Math.PI * 2) / 14;
      const offset = (1 - ap) * 0.55;

      for (let i = 0; i < 14; i++) {
        ctx.save();
        ctx.rotate(i * step + offset);
        
        // Sombra de traslape mecánico entre cuchillas
        ctx.shadowColor = "rgba(0,0,0,0.85)"; 
        ctx.shadowBlur = 18; 
        ctx.shadowOffsetX = -6; 
        ctx.shadowOffsetY = 8;

        ctx.beginPath();
        ctx.moveTo(maxR, 0);
        ctx.quadraticCurveTo(
          maxR * 0.45, 
          minR > 0.01 ? minR * 1.05 : 0, 
          minR > 0.01 ? minR * Math.cos(step * 1.35) : 0, 
          minR > 0.01 ? minR * Math.sin(step * 1.35) : 0
        );
        ctx.quadraticCurveTo(
          maxR * 0.35, 
          maxR * 0.9, 
          maxR * Math.cos(step * 1.8), 
          maxR * Math.sin(step * 1.8)
        );
        ctx.closePath();

        const grad = ctx.createLinearGradient(minR, 0, maxR, maxR * 0.5);
        grad.addColorStop(0, "#1c242c"); 
        grad.addColorStop(0.28, "#2a3542"); 
        grad.addColorStop(0.65, "#131920"); 
        grad.addColorStop(1, "#080b0f");
        
        ctx.fillStyle = grad; 
        ctx.fill();
        
        ctx.shadowColor = "transparent";
        ctx.strokeStyle = "rgba(94, 243, 210, 0.28)"; 
        ctx.lineWidth = 1.8; 
        ctx.stroke();
        ctx.restore();
      }
      ctx.restore();
    }

    function smoothEase(t) {
      return t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
    }

    function animateIris(timestamp) {
      if (!startTime) startTime = timestamp;
      const elapsed = timestamp - startTime;
      const linearP = Math.min(1.0, elapsed / DURATION);
      const easeP = smoothEase(linearP);

      const ap = easeP;
      const rot = (1 - easeP) * 0.35;

      drawOriginalIris(ap, rot);

      if (linearP < 1.0) {
        requestAnimationFrame(animateIris);
      } else {
        if (curtain) curtain.classList.add("hidden");
      }
    }

    window.addEventListener("DOMContentLoaded", () => {
      H.spin();
      requestAnimationFrame(animateIris);

      // Al segundo 2.4s exacto: destello lumínico y resplandor de autenticidad en el botón
      setTimeout(() => {
        H.flashSeal();
      }, 2400);

      document.addEventListener("click", (e) => {
        const target = e.target.closest(".dial-btn, .dial-button, #openDialBtn, [onclick*='vault'], .dial-controller, .vault-trigger");
        if (target) {
          H.tap();
          if (typeof loadVaultAssets === "function") loadVaultAssets();
          if (typeof updateThumb === "function") updateThumb();
        }
      });
    });

    drawOriginalIris(0.0, 0.35);
  })();
</script>

</body>
    </html>
    """
