from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from services.openrouter import analizar_imagen
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient
from services.openrouter import analizar_imagen
from bson import ObjectId
import datetime
from typing import Optional
import os
import uuid
from fastapi.responses import FileResponse


# ============== CONFIGURACIÓN ==============

MONGODB_URL = "mongodb://localhost:27017"
DATABASE_NAME = "monitoreo_fauna"
COLLECTION_NAME = "avistamientos"
PHOTOS_FOLDER = "Photos"

os.makedirs(PHOTOS_FOLDER, exist_ok=True)

# ============== INICIALIZACIÓN ==============

app = FastAPI(
    title="API Monitoreo de Fauna",
    description="Backend para sistema de monitoreo de animales",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = MongoClient(MONGODB_URL)
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]

# ============== MODELOS ==============

def serialize_avistamiento(doc):
    return {
        "id": str(doc["_id"]),
        "timestamp": doc["timestamp"].isoformat(),
        "especie": doc["especie"],
        "accion": doc["accion"],
        "confianza": doc["confianza"],
        "imagen_url": doc["imagen_url"],
        "dispositivo_id": doc["dispositivo_id"]
    }

# ============== ENDPOINTS ==============

@app.get("/")
def root():
    return FileResponse("templates/index.html")

@app.post("/captura")
async def recibir_captura(
    imagen: UploadFile = File(...),
    dispositivo_id: str = Form(...)
):
    try:
        print("="*50)
        print("1. Recibiendo captura...")
        
        # 1. Guardar imagen
        extension = imagen.filename.split(".")[-1] if "." in imagen.filename else "jpg"
        nombre_archivo = f"{uuid.uuid4()}.{extension}"
        ruta_imagen = os.path.join(PHOTOS_FOLDER, nombre_archivo)
        
        print(f"2. Guardando imagen en: {ruta_imagen}")
        contenido = await imagen.read()
        with open(ruta_imagen, "wb") as f:
            f.write(contenido)
        print(f"   ✓ Imagen guardada ({len(contenido)} bytes)")
        
        # 2. Analizar con IA (OpenRouter)
        print("3. Llamando a OpenRouter...")
        analisis = await analizar_imagen(ruta_imagen)
        print(f"   ✓ Análisis recibido: {analisis}")
        
        # 3. Guardar en MongoDB
        print("4. Guardando en MongoDB...")
        documento = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc),
            "especie": analisis["especie"],
            "accion": analisis["accion"],
            "confianza": analisis["confianza"],
            "imagen_url": f"/photos/{nombre_archivo}",
            "dispositivo_id": dispositivo_id
        }
        
        resultado = collection.insert_one(documento)
        documento["_id"] = resultado.inserted_id
        print(f"   ✓ Guardado con ID: {resultado.inserted_id}")
        print("="*50)
        
        return {
            "status": "success",
            "message": "Captura procesada correctamente",
            "data": serialize_avistamiento(documento)
        }
    
    except Exception as e:
        import traceback
        print("="*50)
        print("ERROR COMPLETO:")
        print(traceback.format_exc())
        print("="*50)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/avistamientos")
def listar_avistamientos(
    limite: int = 50,
    especie: Optional[str] = None
):
    try:
        filtro = {}
        if especie:
            filtro["especie"] = {"$regex": especie, "$options": "i"}
        
        cursor = collection.find(filtro).sort("timestamp", -1).limit(limite)
        avistamientos = [serialize_avistamiento(doc) for doc in cursor]
        
        return {
            "status": "success",
            "total": len(avistamientos),
            "data": avistamientos
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/avistamientos/{id}")
def obtener_avistamiento(id: str):
    try:
        documento = collection.find_one({"_id": ObjectId(id)})
        
        if not documento:
            raise HTTPException(status_code=404, detail="Avistamiento no encontrado")
        
        return {
            "status": "success",
            "data": serialize_avistamiento(documento)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/avistamientos/{id}")
def eliminar_avistamiento(id: str):
    try:
        # Buscar documento para obtener la imagen
        documento = collection.find_one({"_id": ObjectId(id)})
        
        if not documento:
            raise HTTPException(status_code=404, detail="Avistamiento no encontrado")
        
        # Eliminar imagen del sistema de archivos
        nombre_imagen = documento["imagen_url"].split("/")[-1]
        ruta_imagen = os.path.join(PHOTOS_FOLDER, nombre_imagen)
        if os.path.exists(ruta_imagen):
            os.remove(ruta_imagen)
        
        # Eliminar de MongoDB
        collection.delete_one({"_id": ObjectId(id)})
        
        return {
            "status": "success",
            "message": "Avistamiento eliminado correctamente"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/estadisticas")
def obtener_estadisticas():
    try:
        total = collection.count_documents({})
        
        # Agrupar por especie
        pipeline = [
            {"$group": {"_id": "$especie", "cantidad": {"$sum": 1}}},
            {"$sort": {"cantidad": -1}}
        ]
        por_especie = list(collection.aggregate(pipeline))
        
        return {
            "status": "success",
            "data": {
                "total_avistamientos": total,
                "por_especie": [
                    {"especie": item["_id"], "cantidad": item["cantidad"]}
                    for item in por_especie
                ]
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============== SERVIR IMÁGENES ==============

from fastapi.staticfiles import StaticFiles

# Montar carpeta Photos para servir imágenes
app.mount("/photos", StaticFiles(directory=PHOTOS_FOLDER), name="Photos")


# ============== EJECUTAR ==============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)