import os
import subprocess
import sys

print("[⚡] EL GUANTE DE THANOS: Iniciando chasquido de sincronización y despliegue...")

# 1. Verificar estructura de directorios crítica
directories = [
    "apps/bian",
    "apps/bian/static",
    "apps/bian/templates",
    "storage/bian"
]

for d in directories:
    os.makedirs(d, exist_ok=True)
    print(f"[✓] Directorio verificado: {d}")

# 2. Limpieza de cachés de Python
subprocess.run("find . -name '__pycache__' -type d -exec rm -r {} +", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("[✓] Cachés de Python eliminadas. Entorno limpio.")

# 3. Verificar e instalar dependencias si faltan
print("[i] Verificando e instalando FastAPI y Uvicorn...")
subprocess.run([sys.executable, "-m", "pip", "install", "fastapi", "uvicorn", "pydantic", "sqlmodel"], check=False)

# 4. Lanzar el servidor Uvicorn
print("[🚀] CHASQUIDO COMPLETADO. Levantando servidor Bian Master Suite...")
cmd = ["uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000", "--reload"]
try:
    subprocess.run(cmd)
except KeyboardInterrupt:
    print("\n[■] Servidor detenido por el usuario.")
