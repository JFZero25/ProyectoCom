from flask import Flask, request, jsonify
import cv2
from flask import Flask, request, jsonify
from picamera2 import Picamera2
import requests
from datetime import datetime
import os
import time
import cv2   # solo para guardar el frame
import numpy as np

# ============== CONFIGURACIÓN ==============

# Backend (tu servidor con FastAPI)
BACKEND_URL = "http://98.86.218.95:8000"  
DISPOSITIVO_ID = "raspberry-01"

# Carpeta temporal para fotos
TEMP_FOLDER = "/tmp/capturas"
os.makedirs(TEMP_FOLDER, exist_ok=True)

# ============== INICIALIZACIÓN CÁMARA ==============

print("Inicializando cámara CSI con Picamera2...")

picam2 = Picamera2()

# Configuración para fotos (still)
config = picam2.create_still_configuration()
picam2.configure(config)

picam2.start()
time.sleep(1)  # Dejar que la cámara estabilice exposición, ganancia, etc.

print("Cámara inicializada correctamente")

# ============== INICIALIZACIÓN SERVIDOR ==============

app = Flask(__name__)

# ============== FUNCIONES ==============

def tomar_foto():
    """Captura una foto con Picamera2 y retorna la ruta."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ruta = os.path.join(TEMP_FOLDER, f"captura_{timestamp}.jpg")

    # Capturar imagen como array numpy (RGB)
    frame = picam2.capture_array()

    # Guardar usando OpenCV
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
    """Endpoint que recibe la señal del sensor RAK11200."""
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
    """Health check."""
    return jsonify({"status": "ok", "camara": "activa"})

# ============== EJECUTAR ==============

if __name__ == "__main__":
    print("\n" + "="*50)
    print("=== Monitor de Fauna - Script Cámara ===")
    print("="*50)
    print(f"Backend configurado: {BACKEND_URL}")
    print(f"Escuchando en: http://0.0.0.0:5000")
    print("Esperando señales del sensor...")
    print("="*50 + "\n")

    app.run(host="0.0.0.0", port=5000, debug=False)