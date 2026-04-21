#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script d'entraînement YOLOv8 - 13 classes (temp et employe séparés)
Détection visages employés CAMIA-Factory
"""

from ultralytics import YOLO
import torch
from pathlib import Path

def entrainer_detecteur_visages():
    """Lance l'entraînement du modèle YOLOv8"""
    
    print("\n" + "=" * 80)
    print("ENTRAÎNEMENT YOLO - 13 CLASSES (temp ET employe SÉPARÉS)")
    print("=" * 80)
    
    # Vérifier GPU
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"\n🖥️  Device: {device}")
    
    if device == 'cpu':
        print("⚠️  GPU non détecté, entraînement sera LENT")
        print("   Recommandé: installer CUDA + PyTorch GPU")
    
    # Vérifier data.yaml
    data_yaml = Path("data.yaml")
    if not data_yaml.exists():
        print(f"\n❌ Fichier data.yaml introuvable!")
        print(f"   Cherché dans: {data_yaml.absolute()}")
        print(f"\n💡 Exécutez d'abord: python nettoyage_sans_fusion.py")
        return
    
    print(f"📝 Configuration: {data_yaml.absolute()}")
    
    # Confirmation
    print("\n⚙️  CONFIGURATION ENTRAÎNEMENT:")
    print("   Modèle: YOLOv8n (nano, rapide)")
    print("   Classes: 13 (temp ET employe séparés)")
    print("   Epochs: 150")
    print("   Batch: 16")
    print("   Image size: 640x640")
    print("   Augmentation: INTENSIVE")
    
    print("\n📋 CLASSES:")
    print("   0-9  : Employés nommés (10)")
    print("   10   : employe (générique)")
    print("   11   : porte_verte")
    print("   12   : temp (temporaire)")
    
    reponse = input("\n🚀 Lancer l'entraînement? (o/n): ").strip().lower()
    if reponse not in ['o', 'oui', 'y', 'yes']:
        print("❌ Annulé")
        return
    
    # Charger modèle pré-entraîné
    print("\n📦 Chargement du modèle YOLOv8n...")
    model = YOLO('yolov8n.pt')
    
    # Entraînement
    print("\n🚀 DÉMARRAGE ENTRAÎNEMENT...")
    print("=" * 80)
    
    results = model.train(
        data=str(data_yaml),
        epochs=150,
        imgsz=640,
        batch=16,
        device=device,
        
        # Optimisation pour petit dataset
        patience=30,
        save=True,
        save_period=10,
        
        # Augmentation INTENSIVE
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        degrees=15,
        translate=0.1,
        scale=0.5,
        shear=2,
        perspective=0.0,
        flipud=0.0,
        fliplr=0.5,
        mosaic=1.0,
        mixup=0.15,
        copy_paste=0.1,
        
        # Hyperparamètres
        lr0=0.001,
        lrf=0.01,
        momentum=0.937,
        weight_decay=0.0005,
        warmup_epochs=5,
        warmup_momentum=0.8,
        warmup_bias_lr=0.1,
        
        # Optimiseur
        optimizer='AdamW',
        
        # Sauvegarde et monitoring
        project='runs/detect',
        name='employee_faces_v2',
        exist_ok=True,
        
        # Autres
        pretrained=True,
        verbose=True,
        seed=42,
        deterministic=True,
        single_cls=False,
        rect=False,
        cos_lr=False,
        close_mosaic=10,
        amp=True,
        fraction=1.0,
        val=True,
        plots=True
    )
    
    print("\n" + "=" * 80)
    print("✅ ENTRAÎNEMENT TERMINÉ")
    print("=" * 80)
    
    # Chemins résultats
    best_model = Path("runs/detect/employee_faces_v2/weights/best.pt")
    results_dir = Path("runs/detect/employee_faces_v2")
    
    print(f"\n📊 RÉSULTATS:")
    print(f"   Meilleur modèle: {best_model}")
    print(f"   Dernier modèle:  {results_dir / 'weights/last.pt'}")
    print(f"   Graphiques:      {results_dir / 'results.png'}")
    print(f"   Confusion matrix: {results_dir / 'confusion_matrix.png'}")
    
    print(f"\n💡 PROCHAINES ÉTAPES:")
    print(f"   1. Vérifier métriques dans: {results_dir}")
    print(f"   2. Comparer performances temp vs employe")
    print(f"   3. Tester le modèle sur vidéo")
    print(f"   4. Si bon: intégrer dans CAMIA-Factory")
    print()
    
    return results

if __name__ == "__main__":
    entrainer_detecteur_visages()