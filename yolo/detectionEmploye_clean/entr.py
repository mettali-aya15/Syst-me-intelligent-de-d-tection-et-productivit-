#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script d'entraînement YOLOv8 - Détection visages employés CAMIA-Factory
Optimisé pour petit dataset avec augmentation intensive
"""

from ultralytics import YOLO
import torch
from pathlib import Path

def entrainer_detecteur_visages():
    """Lance l'entraînement du modèle YOLOv8"""
    
    print("\n" + "=" * 80)
    print("ENTRAÎNEMENT YOLO - DÉTECTION VISAGES EMPLOYÉS")
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
        print(f"\n💡 Exécutez d'abord: python nettoyer_dataset.py")
        return
    
    print(f"📝 Configuration: {data_yaml.absolute()}")
    
    # Confirmation
    print("\n⚙️  CONFIGURATION ENTRAÎNEMENT:")
    print("   Modèle: YOLOv8n (nano, rapide)")
    print("   Epochs: 150")
    print("   Batch: 16")
    print("   Image size: 640x640")
    print("   Augmentation: INTENSIVE")
    
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
        patience=30,              # Early stopping après 30 epochs sans amélioration
        save=True,
        save_period=10,           # Sauvegarder tous les 10 epochs
        
        # Augmentation INTENSIVE (critique pour petit dataset)
        hsv_h=0.015,             # Variation teinte
        hsv_s=0.7,               # Variation saturation
        hsv_v=0.4,               # Variation luminosité
        degrees=15,              # Rotation ±15°
        translate=0.1,           # Translation 10%
        scale=0.5,               # Scale ±50%
        shear=2,                 # Shear 2°
        perspective=0.0,         # Pas de perspective
        flipud=0.0,              # Pas de flip vertical
        fliplr=0.5,              # Flip horizontal 50%
        mosaic=1.0,              # Mosaic augmentation
        mixup=0.15,              # Mixup 15%
        copy_paste=0.1,          # Copy-paste 10%
        
        # Hyperparamètres optimisés
        lr0=0.001,               # Learning rate initial (conservateur)
        lrf=0.01,                # Learning rate final
        momentum=0.937,
        weight_decay=0.0005,
        warmup_epochs=5,         # Warm-up sur 5 epochs
        warmup_momentum=0.8,
        warmup_bias_lr=0.1,
        
        # Optimiseur
        optimizer='AdamW',       # AdamW souvent meilleur pour petits datasets
        
        # Sauvegarde et monitoring
        project='runs/detect',
        name='employee_faces',
        exist_ok=True,
        
        # Autres
        pretrained=True,
        verbose=True,
        seed=42,                 # Reproductibilité
        deterministic=True,
        single_cls=False,        # Multi-classes
        rect=False,
        cos_lr=False,
        close_mosaic=10,
        amp=True,                # Mixed precision (plus rapide)
        fraction=1.0,
        val=True,
        plots=True               # Génère graphiques de résultats
    )
    
    print("\n" + "=" * 80)
    print("✅ ENTRAÎNEMENT TERMINÉ")
    print("=" * 80)
    
    # Chemins résultats
    best_model = Path("runs/detect/employee_faces/weights/best.pt")
    results_dir = Path("runs/detect/employee_faces")
    
    print(f"\n📊 RÉSULTATS:")
    print(f"   Meilleur modèle: {best_model}")
    print(f"   Dernier modèle:  {results_dir / 'weights/last.pt'}")
    print(f"   Graphiques:      {results_dir / 'results.png'}")
    print(f"   Confusion matrix: {results_dir / 'confusion_matrix.png'}")
    
    print(f"\n💡 PROCHAINES ÉTAPES:")
    print(f"   1. Vérifier métriques dans: {results_dir}")
    print(f"   2. Tester le modèle: python tester_modele.py")
    print(f"   3. Si mAP > 0.80: intégrer dans CAMIA-Factory")
    print(f"   4. Si mAP < 0.80: ajouter plus de données")
    print()
    
    return results

def afficher_metriques(results):
    """Affiche les métriques finales"""
    
    if results is None:
        return
    
    print("\n" + "=" * 80)
    print("📈 MÉTRIQUES FINALES")
    print("=" * 80)
    
    # Note: Les métriques exactes dépendent de la version ultralytics
    # Ces infos sont dans runs/detect/employee_faces/results.csv
    
    results_csv = Path("runs/detect/employee_faces/results.csv")
    if results_csv.exists():
        print(f"\n📊 Consultez les métriques détaillées dans:")
        print(f"   {results_csv}")
    
    print(f"\n💡 CRITÈRES DE SUCCÈS:")
    print(f"   ✅ mAP@0.5 > 0.80 (80% précision)")
    print(f"   ✅ Precision > 0.85")
    print(f"   ✅ Recall > 0.80")
    print()

if __name__ == "__main__":
    results = entrainer_detecteur_visages()
    afficher_metriques(results)