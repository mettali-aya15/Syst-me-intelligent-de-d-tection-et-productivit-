import os
import json
from urllib.parse import quote  # pour encoder les noms d'image

# ⚡️ CONFIGURATION
IMAGE_URL_BASE = "http://127.0.0.1:3000"
IMAGE_FOLDER = r"C:\Users\eyama\OneDrive\Bureau\camIA-factory\backend\data\frames_to_annotate"
OUTPUT_JSON = "labelstudio_image6.json"

# Lister toutes les images dans le dossier
image_files = [f for f in os.listdir(IMAGE_FOLDER) if f.lower().endswith((".jpg", ".jpeg", ".png"))]

# Générer les objets JSON pour Label Studio
json_data = []

for img in image_files:
    encoded_img = quote(img)  # encode les espaces et caractères spéciaux
    json_data.append({
        "data": {
            "image": f"{IMAGE_URL_BASE}/{encoded_img}"
        }
    })

# Écrire dans le fichier JSON
with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(json_data, f, indent=2, ensure_ascii=False)

print(f"✅ JSON généré avec {len(image_files)} images : {OUTPUT_JSON}")