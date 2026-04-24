# scripts/train_local.py
from ultralytics import YOLO
import os

dataset_dir = "data/datasets"
yaml_path = os.path.join(dataset_dir, "data.yaml")

# ✅ Correction : vérifie et corrige les noms si nécessaire
import yaml
with open(yaml_path, 'r') as f:
    data = yaml.safe_load(f)

# Forcer les noms sans espace (optionnel, mais recommandé)
if 'names' in data:
    data['names'] = [n.replace(" ", "_").replace("é", "e").replace("è", "e") for n in data['names']]
    # Ex: 'machine arraitee' → 'machine_arraitee'

with open(yaml_path, 'w') as f:
    yaml.dump(data, f, default_flow_style=False)

print(f"[INFO] Classes corrigées : {data['names']}")

# Entraînement
model = YOLO("yolov8n.pt")
model.train(
    data=yaml_path,
    epochs=100,
    imgsz=640,
    batch=8,
    name="productivity_v1",
    patience=15,
    project="runs/detect"
)