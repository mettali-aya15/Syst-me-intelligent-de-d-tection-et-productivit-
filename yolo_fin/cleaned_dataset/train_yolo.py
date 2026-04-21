"""
Script d'entraînement YOLOv8 pour CAMIA-Factory
Utilise le dataset nettoyé avec 9 classes
"""

from ultralytics import YOLO
import torch
from pathlib import Path
import yaml

def create_dataset_yaml(dataset_path, train_ratio=0.8):
    """
    Créer le fichier data.yaml pour YOLOv8
    
    Args:
        dataset_path: Chemin vers le dossier cleaned_dataset
        train_ratio: Ratio pour le split train/val (0.8 = 80% train, 20% val)
    """
    
    dataset_path = Path(dataset_path)
    
    # Split train/val
    images_dir = dataset_path / "images"
    labels_dir = dataset_path / "labels"
    
    all_images = sorted(list(images_dir.glob("*.jpg")))
    total = len(all_images)
    train_count = int(total * train_ratio)
    
    # Créer les dossiers train/val
    train_images_dir = dataset_path / "train" / "images"
    train_labels_dir = dataset_path / "train" / "labels"
    val_images_dir = dataset_path / "val" / "images"
    val_labels_dir = dataset_path / "val" / "labels"
    
    train_images_dir.mkdir(parents=True, exist_ok=True)
    train_labels_dir.mkdir(parents=True, exist_ok=True)
    val_images_dir.mkdir(parents=True, exist_ok=True)
    val_labels_dir.mkdir(parents=True, exist_ok=True)
    
    # Copier les fichiers
    import shutil
    
    print(f"Split du dataset : {train_count} train / {total - train_count} val")
    
    for i, img_path in enumerate(all_images):
        label_path = labels_dir / f"{img_path.stem}.txt"
        
        if i < train_count:
            # Train
            shutil.copy2(img_path, train_images_dir / img_path.name)
            if label_path.exists():
                shutil.copy2(label_path, train_labels_dir / label_path.name)
        else:
            # Val
            shutil.copy2(img_path, val_images_dir / img_path.name)
            if label_path.exists():
                shutil.copy2(label_path, val_labels_dir / label_path.name)
    
    # Créer le fichier YAML
    yaml_config = {
        'path': str(dataset_path.absolute()),
        'train': 'train/images',
        'val': 'val/images',
        'test': '',  # Optionnel
        
        'nc': 9,  # Nombre de classes
        'names': [
            'client',
            'employé',
            'employé actif',
            'employé inactif',
            'machine',
            'machine arrêtée',
            'produit',
            'tables',
            'tables_vides'
        ]
    }
    
    yaml_path = dataset_path / "dataset.yaml"
    with open(yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(yaml_config, f, default_flow_style=False, allow_unicode=True)
    
    print(f"✓ Fichier YAML créé : {yaml_path}")
    print(f"✓ Split effectué : train={train_count}, val={total - train_count}")
    
    return yaml_path


def train_yolo(
    yaml_path,
    model_size='n',  # n, s, m, l, x
    epochs=100,
    imgsz=640,
    batch=16,
    device='cpu',  # 'cpu' ou 0 pour GPU
    project='runs/train',
    name='camia_factory'
):
    """
    Entraîner le modèle YOLOv8
    
    Args:
        yaml_path: Chemin vers dataset.yaml
        model_size: Taille du modèle (n=nano, s=small, m=medium, l=large, x=xlarge)
        epochs: Nombre d'époques
        imgsz: Taille des images
        batch: Taille du batch
        device: 'cpu' ou 0 pour GPU
        project: Dossier de sortie
        name: Nom de l'expérience
    """
    
    print("\n" + "="*60)
    print("ENTRAÎNEMENT YOLOV8 - CAMIA-FACTORY")
    print("="*60)
    
    # Vérifier CUDA
    if device == 0:
        if torch.cuda.is_available():
            print(f"✓ GPU détecté : {torch.cuda.get_device_name(0)}")
        else:
            print("⚠️  GPU non disponible, utilisation du CPU")
            device = 'cpu'
    else:
        print("🖥️  Utilisation du CPU")
    
    # Charger le modèle pré-entraîné
    model_name = f'yolov8{model_size}.pt'
    print(f"\n📦 Chargement du modèle : {model_name}")
    model = YOLO(model_name)
    
    # Afficher les paramètres d'entraînement
    print("\n📋 Paramètres d'entraînement :")
    print(f"  - Dataset : {yaml_path}")
    print(f"  - Modèle : YOLOv8{model_size}")
    print(f"  - Époques : {epochs}")
    print(f"  - Taille image : {imgsz}")
    print(f"  - Batch size : {batch}")
    print(f"  - Device : {device}")
    
    # Entraîner
    print("\n🚀 Démarrage de l'entraînement...\n")
    
    results = model.train(
        data=str(yaml_path),
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        device=device,
        project=project,
        name=name,
        patience=50,  # Early stopping
        save=True,
        save_period=10,  # Sauvegarder tous les 10 epochs
        plots=True,  # Générer des graphiques
        verbose=True,
        
        # Augmentation de données
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        degrees=0.0,
        translate=0.1,
        scale=0.5,
        shear=0.0,
        perspective=0.0,
        flipud=0.0,
        fliplr=0.5,
        mosaic=1.0,
        mixup=0.0,
        copy_paste=0.0
    )
    
    print("\n" + "="*60)
    print("ENTRAÎNEMENT TERMINÉ")
    print("="*60)
    
    # Afficher les résultats
    print(f"\n📊 Résultats finaux :")
    print(f"  - mAP50 : {results.results_dict.get('metrics/mAP50(B)', 'N/A')}")
    print(f"  - mAP50-95 : {results.results_dict.get('metrics/mAP50-95(B)', 'N/A')}")
    
    best_model = Path(project) / name / "weights" / "best.pt"
    last_model = Path(project) / name / "weights" / "last.pt"
    
    print(f"\n💾 Modèles sauvegardés :")
    print(f"  - Meilleur : {best_model}")
    print(f"  - Dernier : {last_model}")
    
    return model, results


def validate_model(model_path, yaml_path, imgsz=640, device='cpu'):
    """
    Valider le modèle entraîné
    """
    print("\n" + "="*60)
    print("VALIDATION DU MODÈLE")
    print("="*60)
    
    model = YOLO(model_path)
    
    results = model.val(
        data=yaml_path,
        imgsz=imgsz,
        device=device,
        plots=True
    )
    
    print(f"\n📊 Résultats de validation :")
    print(f"  - mAP50 : {results.box.map50}")
    print(f"  - mAP50-95 : {results.box.map}")
    print(f"  - Precision : {results.box.mp}")
    print(f"  - Recall : {results.box.mr}")
    
    return results


def test_inference(model_path, image_path, conf=0.25, save=True):
    """
    Tester l'inférence sur une image
    """
    print("\n" + "="*60)
    print("TEST D'INFÉRENCE")
    print("="*60)
    
    model = YOLO(model_path)
    
    results = model.predict(
        source=image_path,
        conf=conf,
        save=save,
        show_labels=True,
        show_conf=True
    )
    
    print(f"\n✓ Inférence effectuée")
    print(f"  - Détections : {len(results[0].boxes)}")
    
    return results


if __name__ == "__main__":
    # Configuration des chemins
    dataset_path = r"C:\Users\eyama\OneDrive\Bureau\camIA-factory\yolo_fin\cleaned_dataset"
    
    # ÉTAPE 1 : Créer le YAML et split train/val
    print("ÉTAPE 1 : Préparation du dataset")
    yaml_path = create_dataset_yaml(dataset_path, train_ratio=0.8)
    
    # ÉTAPE 2 : Entraîner le modèle
    print("\nÉTAPE 2 : Entraînement")
    
    # Configuration pour CPU (adapter selon tes ressources)
    model, results = train_yolo(
        yaml_path=yaml_path,
        model_size='n',  # YOLOv8n (le plus rapide pour CPU)
        epochs=100,
        imgsz=640,
        batch=8,  # Batch size petit pour CPU
        device='cpu',  # Changer à 0 si GPU disponible
        project='runs/train',
        name='camia_factory_v1'
    )
    
    # ÉTAPE 3 : Validation
    print("\nÉTAPE 3 : Validation")
    best_model_path = "runs/train/camia_factory_v1/weights/best.pt"
    validate_model(best_model_path, yaml_path, device='cpu')
    
    # ÉTAPE 4 : Test sur une image (optionnel)
    # test_image = dataset_path / "val/images" / "01001b3d__frame_429.jpg"
    # if test_image.exists():
    #     test_inference(best_model_path, str(test_image))
    
    print("\n✅ Pipeline d'entraînement terminé !")