from flask import Flask, request, jsonify
import cv2
import requests
from datetime import datetime
import os
import time
import numpy as np

# ============== CONFIGURACIÓN ==============

BACKEND_URL = "http://98.86.218.95:8000"
DISPOSITIVO_ID = "laptop-01"

TEMP_FOLDER = "/tmp/capturas"
os.makedirs(TEMP_FOLDER, exist_ok=True)

# ============== INICIALIZACIÓN CÁMARA (OPENCV) ==============

print("Inicializando cámara de laptop con OpenCV...")

cam = cv2.VideoCapture(0, cv2.CAP_V4L2)
  # 0 = cámara por defecto

# Opcional: mejorar calidad de captura
cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

time.sleep(1)

if not cam.isOpened():
    raise Exception("✗ No se pudo acceder a la cámara de la laptop")

print("Cámara inicializada correctamente")

# ============== INICIALIZACIÓN SERVIDOR ==============

app = Flask(__name__)

# ============== FUNCIONES ==============

def tomar_foto():
    """Captura una foto usando la webcam."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ruta = os.path.join(TEMP_FOLDER, f"captura_{timestamp}.jpg")

    ret, frame = cam.read()
    if not ret:
        raise Exception("✗ Error al capturar imagen desde la webcam")

    cv2.imwrite(ruta, frame)
    print(f"Foto capturada: {ruta}")

    return ruta


def enviar_al_backend(ruta_imagen):
    """Envía la imagen al backend para procesamiento."""
    try:
        with open(ruta_imagen, "rb") as f:
            files = {"imagen": f}
            data = {"dispositivo_id": DISPOSITIVO_ID}

            print(f"Enviando al backend: {BACKEND_URL}/captura")
            response = requests.post(
                f"{BACKEND_URL}/captura",
                files=files,
                data=data,
                timeout=60
            )

        if response.status_code == 200:
            resultado = response.json()
            print(f"✓ Procesado: {resultado['data']['especie']} - {resultado['data']['accion']}")
            os.remove(ruta_imagen)
            return True
        else:
            print(f"✗ Error del backend: {response.status_code}")
            print(f"  Respuesta: {response.text}")
            return False

    except Exception as e:
        print(f"✗ Error al enviar: {e}")
        return False

# ============== ENDPOINTS ==============

@app.route("/disparar", methods=["POST"])
def disparar():
    print("\n" + "="*50)
    print("¡Señal recibida del sensor!")
    print("="*50)

    try:
        ruta_foto = tomar_foto()
        exito = enviar_al_backend(ruta_foto)

        if exito:
            return jsonify({"status": "ok", "mensaje": "Captura procesada"}), 200
        else:
            return jsonify({"status": "error", "mensaje": "Error al procesar"}), 500

    except Exception as e:
        print(f"✗ Error: {e}")
        return jsonify({"status": "error", "mensaje": str(e)}), 500


@app.route("/estado", methods=["GET"])
def estado():
    return jsonify({"status": "ok", "camara": "activa"})

# ============== EJECUTAR ==============

if __name__ == "__main__":
    print("\n" + "="*50)
    print("=== Monitor de Fauna - Laptop ===")
    print("="*50)
    print(f"Backend configurado: {BACKEND_URL}")
    print(f"Escuchando en: http://0.0.0.0:5000")
    print("Esperando señales del sensor...")
    print("="*50 + "\n")

    app.run(host="0.0.0.0", port=5000, debug=False)