from ultralytics import YOLO
import torch

print("=" * 60)
print("ENTRAÎNEMENT YOLOV8 - CAMIA FACTORY")
print("=" * 60)

# Vérifier GPU
device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f"\n🖥️  Device: {device}")

if device == 'cuda':
    print(f"   GPU: {torch.cuda.get_device_name(0)}")
    print(f"   VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

# Charger le modèle pré-entraîné
model = YOLO('yolov8n.pt')

print(f"\n📦 Modèle: YOLOv8n")
print(f"   Paramètres: {sum(p.numel() for p in model.model.parameters()) / 1e6:.2f}M")

# Configuration d'entraînement
print(f"\n⚙️  Configuration:")
config = {
    'data': 'data.yaml',
    'epochs': 150,
    'imgsz': 640,
    'batch': 16,
    'patience': 0,  # 0 = désactiver Early Stopping
    'save': True,
    'project': 'runs/detect',
    'name': 'camia_factory',
    'exist_ok': True,
    'pretrained': True,
    'optimizer': 'AdamW',
    'lr0': 0.001,
    'lrf': 0.01,
    'momentum': 0.937,
    'weight_decay': 0.0005,
    'warmup_epochs': 5,
    'warmup_momentum': 0.8,
    'warmup_bias_lr': 0.1,
    'box': 7.5,
    'cls': 0.5,
    'dfl': 1.5,
    'pose': 12.0,
    'kobj': 1.0,
    'label_smoothing': 0.0,
    'nbs': 64,
    'hsv_h': 0.015,
    'hsv_s': 0.7,
    'hsv_v': 0.4,
    'degrees': 10.0,
    'translate': 0.1,
    'scale': 0.5,
    'shear': 2.0,
    'perspective': 0.0001,
    'flipud': 0.0,
    'fliplr': 0.5,
    'mosaic': 1.0,
    'mixup': 0.15,
    'copy_paste': 0.3,
    'device': device,
    'workers': 8,
    'close_mosaic': 10,
    'amp': True,
    'fraction': 1.0,
    'profile': False,
    'overlap_mask': True,
    'mask_ratio': 4,
    'dropout': 0.0,
    'val': True,
    'plots': True,
    'save_json': False,
    'save_hybrid': False,
    'conf': None,
    'iou': 0.7,
    'max_det': 300,
    'half': False,
    'dnn': False,
    'verbose': True,
}

for key, value in config.items():
    if key not in ['device', 'data']:
        print(f"   {key}: {value}")

print(f"\n🚀 Démarrage de l'entraînement...")
print(f"   Ceci peut prendre 30-60 minutes selon votre GPU\n")

# Lancer l'entraînement
results = model.train(**config)

print(f"\n" + "=" * 60)
print("ENTRAÎNEMENT TERMINÉ")
print("=" * 60)

# Afficher les résultats
print(f"\n📊 Résultats finaux:")
print(f"   mAP50: {results.results_dict.get('metrics/mAP50(B)', 0):.3f}")
print(f"   mAP50-95: {results.results_dict.get('metrics/mAP50-95(B)', 0):.3f}")
print(f"   Precision: {results.results_dict.get('metrics/precision(B)', 0):.3f}")
print(f"   Recall: {results.results_dict.get('metrics/recall(B)', 0):.3f}")

print(f"\n📁 Modèle sauvegardé:")
print(f"   Meilleur: runs/detect/camia_factory/weights/best.pt")
print(f"   Dernier: runs/detect/camia_factory/weights/last.pt")

print(f"\n📈 Visualisations:")
print(f"   runs/detect/camia_factory/results.png")
print(f"   runs/detect/camia_factory/confusion_matrix.png")

print(f"\n🧪 Test du modèle:")
print(f"   yolo predict model=runs/detect/camia_factory/weights/best.pt source=val/images")