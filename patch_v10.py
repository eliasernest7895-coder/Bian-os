with open('apps/bian/router.py', 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Estilos CSS: borde perimetral, luz y transición
edge_styles = """
        /* BORDE PERIMETRAL DINAMICO Y LUZ AMBIENTAL */
        .edge-screen-border {
            position: fixed; inset: 0; pointer-events: none; z-index: 80;
            border: 2px solid transparent;
            box-shadow: inset 0 0 0px transparent;
            transition: border-color 0.6s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.6s cubic-bezier(0.16, 1, 0.3, 1);
        }
        .ambient-fade-light {
            position: fixed; inset: 0; pointer-events: none; z-index: 25;
            background: radial-gradient(circle at 50% 50%, rgba(255,255,255,0.22) 0%, transparent 70%);
            opacity: 0;
            transition: opacity 1.8s ease-out;
        }
        .ambient-fade-light.flash {
            opacity: 1;
            transition: opacity 0.08s ease-in;
        }
        .viewport {
            transition: background 0.6s ease;
        }
"""

# 2. Capas visuales HTML
html_layers = """
    <div class="edge-screen-border" id="screenEdgeBorder"></div>
    <div class="ambient-fade-light" id="ambientLightLayer"></div>
"""

# 3. Lógica JS unificada (Temas, sonidos, bordes y swipe touch)
engine_core_js = """
        const moduleThemes = {
            'pano': { color: '#00FFC8', bg: 'radial-gradient(circle, rgba(0,255,200,0.15) 0%, #000 85%)', freq: [440, 660, 880], type: 'sine' },
            'timelapse': { color: '#FF3B30', bg: 'radial-gradient(circle, rgba(255,59,48,0.18) 0%, #000 85%)', freq: [220, 440, 880], type: 'sawtooth' },
            'scan': { color: '#00D2FF', bg: 'radial-gradient(circle, rgba(0,210,255,0.15) 0%, #000 85%)', freq: [520, 780, 1040], type: 'triangle' },
            'night': { color: '#5E5CE6', bg: 'radial-gradient(circle, rgba(94,92,230,0.2) 0%, #000 85%)', freq: [180, 270, 360], type: 'sine' },
            'macro': { color: '#30D158', bg: 'radial-gradient(circle, rgba(48,209,88,0.16) 0%, #000 85%)', freq: [880, 1100, 1320], type: 'triangle' },
            'portrait': { color: '#FFD60A', bg: 'radial-gradient(circle, rgba(255,214,10,0.18) 0%, #000 85%)', freq: [330, 495, 660], type: 'sine' },
            'lonas': { color: '#FF9500', bg: 'radial-gradient(circle, rgba(255,149,0,0.18) 0%, #000 85%)', freq: [150, 300, 450], type: 'square' },
            'custom': { color: '#FF2D55', bg: 'radial-gradient(circle, rgba(255,45,85,0.18) 0%, #000 85%)', freq: [400, 600, 900], type: 'sine' },
            'print': { color: '#32ADE6', bg: 'radial-gradient(circle, rgba(50,173,230,0.16) 0%, #000 85%)', freq: [300, 450, 600], type: 'sawtooth' },
            'cine': { color: '#FF375F', bg: 'radial-gradient(circle, rgba(255,55,95,0.2) 0%, #000 85%)', freq: [130, 195, 260], type: 'sine' },
            'raw': { color: '#34C759', bg: 'radial-gradient(circle, rgba(52,199,89,0.16) 0%, #000 85%)', freq: [600, 750, 900], type: 'triangle' },
            'svg': { color: '#FFCC00', bg: 'radial-gradient(circle, rgba(255,204,0,0.18) 0%, #000 85%)', freq: [700, 850, 1050], type: 'square' },
            'vid': { color: '#BF5AF2', bg: 'radial-gradient(circle, rgba(191,90,242,0.18) 0%, #000 85%)', freq: [260, 390, 520], type: 'sawtooth' },
            'depth': { color: '#AF52DE', bg: 'radial-gradient(circle, rgba(175,82,222,0.18) 0%, #000 85%)', freq: [200, 350, 500], type: 'sine' },
            'chef': { color: '#FF9F0A', bg: 'radial-gradient(circle, rgba(255,159,10,0.18) 0%, #000 85%)', freq: [320, 480, 640], type: 'triangle' },
            'price': { color: '#63E6E2', bg: 'radial-gradient(circle, rgba(99,230,226,0.18) 0%, #000 85%)', freq: [480, 640, 800], type: 'sine' },
            'ai': { color: '#0A84FF', bg: 'radial-gradient(circle, rgba(10,132,255,0.2) 0%, #000 85%)', freq: [500, 750, 1000], type: 'sine' }
        };

        function playModuleUniqueSound(key) {
            try {
                const theme = moduleThemes[key];
                if (!theme) return;
                const ctx = getAudioContext();
                const now = ctx.currentTime;
                theme.freq.forEach((f, i) => {
                    const osc = ctx.createOscillator();
                    const gain = ctx.createGain();
                    osc.connect(gain);
                    gain.connect(ctx.destination);
                    osc.type = theme.type || 'sine';
                    osc.frequency.setValueAtTime(f, now + (i * 0.04));
                    gain.gain.setValueAtTime(0.001, now + (i * 0.04));
                    gain.gain.linearRampToValueAtTime(0.14, now + (i * 0.04) + 0.015);
                    gain.gain.exponentialRampToValueAtTime(0.0001, now + (i * 0.04) + 0.28);
                    osc.start(now + (i * 0.04));
                    osc.stop(now + (i * 0.04) + 0.29);
                });
            } catch(e) {}
        }

        function applyModuleColorAndEdge(key) {
            const theme = moduleThemes[key];
            const border = document.getElementById('screenEdgeBorder');
            const viewport = document.getElementById('viewportArea');
            const ambient = document.getElementById('ambientLightLayer');

            if (border && viewport && ambient) {
                if (theme) {
                    border.style.borderColor = theme.color;
                    border.style.boxShadow = `inset 0 0 28px ${theme.color}, 0 0 15px ${theme.color}`;
                    viewport.style.background = theme.bg;
                    ambient.style.background = `radial-gradient(circle at 50% 50%, ${theme.color}44 0%, transparent 70%)`;
                } else {
                    border.style.borderColor = 'transparent';
                    border.style.boxShadow = 'none';
                    viewport.style.background = '#000';
                }

                ambient.classList.remove('flash');
                void ambient.offsetWidth;
                ambient.classList.add('flash');
                setTimeout(() => { ambient.classList.remove('flash'); }, 80);
            }
        }

        // Gestos táctiles: Swipe arriba abre; Swipe abajo bloquea
        let globalTouchStartY = 0;
        window.addEventListener('touchstart', (e) => {
            globalTouchStartY = e.touches[0].clientY;
        }, { passive: true });

        window.addEventListener('touchend', (e) => {
            const touchEndY = e.changedTouches[0].clientY;
            const deltaY = globalTouchStartY - touchEndY;
            const lockscreen = document.getElementById('lockscreen');
            if (!lockscreen) return;
            const isUnlocked = lockscreen.classList.contains('unlocked');

            if (!isUnlocked && deltaY > 35) {
                triggerGiftUnlock();
            } else if (isUnlocked && deltaY < -70 && globalTouchStartY < 140) {
                lockscreen.classList.remove('unlocked');
                const giftBox = document.getElementById('giftUnlockBtn');
                if (giftBox) giftBox.classList.remove('fly');
                applyModuleColorAndEdge(null);
            }
        }, { passive: true });
"""

if 'edge-screen-border' not in c:
    c = c.replace('</style>', edge_styles + '\n    </style>')
    c = c.replace('<body>', '<body>\n' + html_layers)

if 'function playModuleUniqueSound' not in c:
    c = c.replace('function playSignatureProSound(key) {', engine_core_js + '\n        function playSignatureProSound(key) {')
    c = c.replace('playSignatureProSound(key);', 'playSignatureProSound(key);\n            playModuleUniqueSound(key);\n            applyModuleColorAndEdge(key);')
    c = c.replace('resetArmEngine();', 'resetArmEngine();\n            applyModuleColorAndEdge(null);')

with open('apps/bian/router.py', 'w', encoding='utf-8') as f:
    f.write(c)

print("✔ Parche V10 compilado y aplicado sin errores.")
