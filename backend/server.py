from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

IMAGE_FOLDER = r"C:\Users\eyama\OneDrive\Bureau\camIA-factory\backend\data\frames_to_annotate"

# 🔥 DEBUG AU DEMANDE
@app.get("/images/{filename}")
async def get_image(filename: str):
    print("📥 Fichier demandé :", filename)

    file_path = os.path.join(IMAGE_FOLDER, filename)

    if not os.path.exists(file_path):
        print("❌ Introuvable :", file_path)
        return {"error": "Fichier non trouvé"}

    print("✅ Trouvé :", file_path)
    return FileResponse(file_path)

# 🔎 Lister les images
@app.get("/images")
async def list_images():
    files = [f for f in os.listdir(IMAGE_FOLDER) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
    return {"images_disponibles": files}