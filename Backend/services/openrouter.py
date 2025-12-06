import httpx
import base64
import os
import json


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = "nvidia/nemotron-nano-12b-v2-vl:free"


async def analizar_imagen(ruta_imagen: str) -> dict:
    with open(ruta_imagen, "rb") as f:
        imagen_base64 = base64.b64encode(f.read()).decode("utf-8")

    extension = ruta_imagen.split(".")[-1].lower()
    mime_types = {"jpg": "image/jpeg",
                  "jpeg": "image/jpeg", "png": "image/png"}
    mime_type = mime_types.get(extension, "image/jpeg")

    prompt = """Analiza esta imagen de una cámara de monitoreo de fauna silvestre.

Responde ÚNICAMENTE con un JSON válido (sin markdown ni texto adicional):
{
    "especie": "nombre de la especie detectada o 'No detectado' si no hay animal",
    "accion": "descripción breve de lo que está haciendo el animal",
    "confianza": 0.85
}

El campo confianza debe ser un número entre 0 y 1."""

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "HTTP-Referer": "http://localhost",
                    "X-Title": "Monitoreo Fauna",
                    "Content-Type": "application/json"
                },

                json={
                    "model": OPENROUTER_MODEL,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:{mime_type};base64,{imagen_base64}"
                                    }
                                }
                            ]
                        }
                    ],
                    "max_tokens": 200
                }
            )

            resultado = response.json()

            # Verificar si hay error
            if "error" in resultado:
                print(f"Error de OpenRouter: {resultado['error']}")
                raise Exception(f"OpenRouter error: {resultado['error']}")

            print(f"Respuesta completa: {resultado}")  # Debug

            contenido = resultado["choices"][0]["message"]["content"]

            # Limpiar markdown si existe
            contenido = contenido.replace(
                "```json", "").replace("```", "").strip()

            analisis = json.loads(contenido)
            return analisis

    except Exception as e:
        print(f"Error en analizar_imagen: {e}")
        raise
