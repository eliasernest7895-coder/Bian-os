# Bian-os
aplicacion de fotos con ia
 BIAN OS - Cloud Entity
​BIAN es una interfaz de inteligencia artificial autónoma diseñada para ejecutarse en la nube.
​🚀 Características
​Génesis Vision: Generación de imágenes (Replicate).
​Nova Chat: Cerebro conversacional (OpenAI).
​Cloud Autonomy: Desplegado en GitHub Pages para máxima conectividad
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <title>Bian OS - Cloud Entity</title>
    
    <!-- Frameworks -->
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;900&display=swap" rel="stylesheet">
    
    <style>
        body { font-family: 'Outfit', sans-serif; background: #000; color: white; margin: 0; height: 100vh; overflow: hidden; }
        .glass { background: rgba(15, 15, 15, 0.8); backdrop-filter: blur(25px); border: 1px solid rgba(255,255,255,0.05); }
        .view { height: calc(100vh - 160px); overflow-y: auto; padding-bottom: 80px; }
        .no-scroll::-webkit-scrollbar { display: none; }
        .tab-active { color: #6366f1; transform: scale(1.1); }
    </style>
</head>
<body class="flex flex-col">

    <!-- HEADER -->
    <header class="p-6 pt-12 flex justify-between items-center glass z-30">
        <div>
            <h1 class="text-3xl font-black italic tracking-tighter">BIAN <span class="text-indigo-500">CLOUD</span></h1>
            <p id="user-status" class="text-[9px] font-bold text-gray-500 uppercase tracking-widest mt-1 italic">Iniciando protocolo...</p>
        </div>
        <div class="flex gap-2">
            <div id="led-net" class="w-2 h-2 rounded-full bg-red-500"></div>
            <div id="led-api" class="w-2 h-2 rounded-full bg-red-500"></div>
        </div>
    </header>

    <!-- CONTENT -->
    <main class="flex-1">
        
        <!-- GENESIS VIEW -->
        <div id="view-genesis" class="view p-6 space-y-6">
            <div class="glass p-6 rounded-[2.5rem] space-y-5">
                <div class="flex items-center gap-3">
                    <i data-lucide="sparkles" class="text-indigo-400"></i>
                    <h3 class="font-bold">Génesis Vision</h3>
                </div>
                <textarea id="p-v" placeholder="Escribe tu visión aquí..." class="w-full bg-black/40 border border-white/10 rounded-2xl p-4 text-sm outline-none focus:border-indigo-500 min-h-[100px] text-white"></textarea>
                <button onclick="generateImage()" id="btn-gen" class="w-full py-4 bg-indigo-600 rounded-2xl font-black active:scale-95 transition shadow-lg shadow-indigo-900/20">GENERAR</button>
                
                <div id="res-box" class="hidden w-full aspect-square rounded-3xl overflow-hidden bg-zinc-900 border border-white/5 relative mt-4">
                    <div id="res-load" class="absolute inset-0 flex flex-col items-center justify-center bg-black/60">
                        <div class="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mb-2"></div>
                        <span class="text-[10px] font-bold text-indigo-400 uppercase tracking-widest">Creando...</span>
                    </div>
                    <img id="res-img" class="w-full h-full object-cover hidden">
                </div>
            </div>
        </div>

        <!-- CHAT VIEW -->
        <div id="view-chat" class="view hidden p-6 flex flex-col">
            <div id="chat-sc" class="flex-1 overflow-y-auto space-y-4 no-scroll mb-4"></div>
            <div class="flex gap-2 glass p-2 rounded-full border border-white/10">
                <input type="text" id="chat-in" placeholder="Dime algo..." class="flex-1 bg-transparent px-6 py-4 text-sm outline-none">
                <button onclick="sendNova()" class="p-4 bg-white text-black rounded-full"><i data-lucide="send" class="w-5 h-5"></i></button>
            </div>
        </div>

        <!-- VAULT VIEW -->
        <div id="view-vault" class="view hidden p-6">
            <div class="glass p-8 rounded-[3rem] space-y-8">
                <h2 class="text-2xl font-black italic">MEMORIA <span class="text-indigo-500 text-3xl">VAULT</span></h2>
                <div class="space-y-4">
                    <div class="space-y-1">
                        <label class="text-[9px] font-bold text-gray-500 uppercase ml-2">OpenAI Key</label>
                        <input type="password" id="oa-k" placeholder="sk-..." class="w-full bg-black/50 border border-white/10 rounded-2xl p-5 text-xs text-indigo-300 outline-none">
                    </div>
                    <div class="space-y-1">
                        <label class="text-[9px] font-bold text-gray-500 uppercase ml-2">Replicate Token</label>
                        <input type="password" id="rp-k" placeholder="r8_..." class="w-full bg-black/50 border border-white/10 rounded-2xl p-5 text-xs text-purple-300 outline-none">
                    </div>
                    <button onclick="saveKeys()" class="w-full py-5 bg-white text-black font-black rounded-[2rem] shadow-2xl uppercase tracking-widest text-[10px] mt-4">Sincronizar Bóveda</button>
                </div>
                <div class="p-5 bg-indigo-900/10 border border-indigo-500/20 rounded-3xl">
                    <p class="text-[10px] text-indigo-300 italic leading-relaxed">Tus llaves se guardan en el almacenamiento local del navegador. No las compartas con nadie.</p>
                </div>
            </div>
        </div>

    </main>

    <!-- NAVIGATION -->
    <nav class="p-6 bg-black/90 border-t border-white/5 flex justify-around items-center sticky bottom-0 z-40 pb-12">
        <button onclick="switchTab('genesis')" id="nav-genesis" class="tab-active transition-all"><i data-lucide="sparkles"></i></button>
        <button onclick="switchTab('chat')" id="nav-chat" class="text-gray-600 transition-all"><i data-lucide="message-square"></i></button>
        <button onclick="switchTab('vault')" id="nav-vault" class="text-gray-600 transition-all"><i data-lucide="key"></i></button>
    </nav>

    <script>
        lucide.createIcons();

        // PERSISTENCIA LOCAL
        let OK = localStorage.getItem('bian_oa') || "";
        let RK = localStorage.getItem('bian_rp') || "";

        function switchTab(id) {
            document.querySelectorAll('.view').forEach(v => v.classList.add('hidden'));
            document.querySelectorAll('nav button').forEach(b => b.classList.remove('tab-active', 'text-indigo-500'));
            document.querySelectorAll('nav button').forEach(b => b.classList.add('text-gray-600'));
            
            document.getElementById('view-' + id).classList.remove('hidden');
            document.getElementById('nav-' + id).classList.add('tab-active', 'text-indigo-500');
            document.getElementById('nav-' + id).classList.remove('text-gray-600');
        }

        function updateStatus() {
            const net = document.getElementById('led-net');
            const api = document.getElementById('led-api');
            const status = document.getElementById('user-status');

            if(navigator.onLine) net.className = "w-2 h-2 rounded-full bg-green-500 shadow-[0_0_8px_#22c55e]";
            if(OK && RK) {
                api.className = "w-2 h-2 rounded-full bg-green-500 shadow-[0_0_8px_#22c55e]";
                status.innerText = "Sistemas Autónomos Online";
            } else {
                status.innerText = "Configuración pendiente";
            }
        }

        function saveKeys() {
            const ok = document.getElementById('oa-k').value.trim();
            const rk = document.getElementById('rp-k').value.trim();
            if(ok) { localStorage.setItem('bian_oa', ok); OK = ok; }
            if(rk) { localStorage.setItem('bian_rp', rk); RK = rk; }
            updateStatus();
            alert("🔑 Memoria sincronizada.");
            switchTab('genesis');
        }

        async function generateImage() {
            const p = document.getElementById('p-v').value;
            const b = document.getElementById('res-box');
            const l = document.getElementById('res-load');
            const i = document.getElementById('res-img');
            const btn = document.getElementById('btn-gen');

            if(!RK || !p) return alert("Falta descripción o llave.");
            b.classList.remove('hidden'); l.classList.remove('hidden'); i.classList.add('hidden');
            btn.disabled = true;

            try {
                const res = await fetch("https://api.replicate.com/v1/predictions", {
                    method: "POST",
                    headers: { "Authorization": `Token ${RK}`, "Content-Type": "application/json" },
                    body: JSON.stringify({ version: "ac732d83545915b4047348fd603c4096043162648a9e9957cd7321e10228384b", input: { prompt: p } })
                });
                const data = await res.json();
                
                const poll = setInterval(async () => {
                    const check = await fetch(data.urls.get, { headers: { "Authorization": `Token ${RK}` } });
                    const st = await check.json();
                    if(st.status === "succeeded") {
                        clearInterval(poll);
                        l.classList.add('hidden');
                        i.src = st.output[0];
                        i.classList.remove('hidden');
                        btn.disabled = false;
                    } else if(st.status === "failed") {
                        clearInterval(poll);
                        alert("Error en la IA.");
                        b.classList.add('hidden');
                        btn.disabled = false;
                    }
                }, 2000);
            } catch(e) { 
                alert("Error de red."); 
                b.classList.add('hidden'); btn.disabled = false;
            }
        }

        async function sendNova() {
            const input = document.getElementById('chat-in');
            const text = input.value;
            if(!OK || !text) return;

            addBubble(text, 'user');
            input.value = "";

            try {
                const res = await fetch("https://api.openai.com/v1/chat/completions", {
                    method: "POST",
                    headers: { "Content-Type": "application/json", "Authorization": `Bearer ${OK}` },
                    body: JSON.stringify({
                        model: "gpt-4o-mini",
                        messages: [{role: "system", content: "Eres Nova, el núcleo de Bian. Inteligente y breve."}, {role: "user", content: text}]
                    })
                });
                const data = await res.json();
                addBubble(data.choices[0].message.content, 'bot');
            } catch(e) {
                addBubble("⚠️ No pude conectar con la nube.", 'bot');
            }
        }

        function addBubble(t, s) {
            const sc = document.getElementById('chat-sc');
            const d = document.createElement('div');
            d.className = s === 'user' ? 'flex justify-end' : 'flex justify-start';
            d.innerHTML = `<div class="${s === 'user' ? 'bg-indigo-600 shadow-lg' : 'bg-white/5 border border-white/10'} p-5 rounded-3xl max-w-[85%] text-sm leading-relaxed">${t}</div>`;
            sc.appendChild(d);
            sc.scrollTop = sc.scrollHeight;
        }

        // Cargar llaves en inputs si existen
        document.getElementById('oa-k').value = OK;
        document.getElementById('rp-k').value = RK;
        updateStatus();
    </script>
</body>
</html>


