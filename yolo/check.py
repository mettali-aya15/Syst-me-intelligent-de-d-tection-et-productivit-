#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import shutil
import random
from pathlib import Path

# Configuration
SEED = 42
TRAIN_RATIO = 0.8
BASE_DIR = Path(__file__).parent.resolve()
IMG_DIR = BASE_DIR / "images"
LBL_DIR = BASE_DIR / "labels"

random.seed(SEED)

def main():
    print("="*60)
    print("🚀 PRÉPARATION DU DATASET YOLO (Label Studio → Ultralytics)")
    print("="*60)

    if not IMG_DIR.exists() or not LBL_DIR.exists():
        print("❌ Erreur : Les dossiers 'images/' et/ou 'labels/' sont introuvables.")
        print("   Place ce script à la racine de ton projet et relance-le.")
        return

    # ---------------------------------------------------------
    # 1️⃣ RENOMMER LES LABELS (supprimer le préfixe hash__)
    # ---------------------------------------------------------
    print("\n🔄 Étape 1 : Nettoyage des noms de fichiers labels...")
    renamed = 0
    for lbl in LBL_DIR.glob("*.txt"):
        if "__" in lbl.stem:
            original = lbl.stem.split("__", 1)[1]
            new_lbl = lbl.with_name(f"{original}.txt")
            if not new_lbl.exists():
                lbl.rename(new_lbl)
                renamed += 1
            else:
                print(f"   ⚠️ Conflit ignoré : {lbl.name} (cible existe déjà)")
    print(f"   ✅ {renamed} labels renommés avec succès.")

    # ---------------------------------------------------------
    # 2️⃣ VÉRIFIER LES PAIRES IMAGE/LABEL
    # ---------------------------------------------------------
    print("\n🔍 Étape 2 : Vérification des paires image/label...")
    img_exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    
    # Filtrer uniquement les fichiers image (ignore server.py, etc.)
    img_files = {f.name for f in IMG_DIR.glob("*") if f.suffix.lower() in img_exts}
    lbl_files = {f.name for f in LBL_DIR.glob("*.txt")}
    
    img_stems = {f.rsplit(".", 1)[0] for f in img_files}
    lbl_stems = {f.rsplit(".", 1)[0] for f in lbl_files}
    
    missing_lbl = img_stems - lbl_stems
    missing_img = lbl_stems - img_stems
    valid_stems = list(img_stems & lbl_stems)
    
    if missing_lbl: print(f"   ⚠️ {len(missing_lbl)} images sans label")
    if missing_img: print(f"   ⚠️ {len(missing_img)} labels sans image")
    print(f"   ✅ {len(valid_stems)} paires valides prêtes au split.")

    if not valid_stems:
        print("❌ Aucune paire valide trouvée. Vérifie tes dossiers.")
        return

    # ---------------------------------------------------------
    # 3️⃣ SPLIT 80/20 & CRÉATION DES DOSSIERS
    # ---------------------------------------------------------
    print("\n📦 Étape 3 : Split 80/20 et création des dossiers...")
    random.shuffle(valid_stems)
    split_idx = int(len(valid_stems) * TRAIN_RATIO)
    train_stems = valid_stems[:split_idx]
    val_stems   = valid_stems[split_idx:]

    # Chemins de sortie
    paths = {
        "train_img": BASE_DIR / "train" / "images",
        "train_lbl": BASE_DIR / "train" / "labels",
        "val_img":   BASE_DIR / "val"   / "images",
        "val_lbl":   BASE_DIR / "val"   / "labels"
    }
    for p in paths.values():
        p.mkdir(parents=True, exist_ok=True)

    def copy_pair(stems, dst_img, dst_lbl):
        for stem in stems:
            # Trouver l'image avec la bonne extension
            for ext in img_exts:
                src_img = IMG_DIR / f"{stem}{ext}"
                if src_img.exists():
                    shutil.copy2(src_img, dst_img / src_img.name)
                    break
            src_lbl = LBL_DIR / f"{stem}.txt"
            if src_lbl.exists():
                shutil.copy2(src_lbl, dst_lbl / src_lbl.name)

    copy_pair(train_stems, paths["train_img"], paths["train_lbl"])
    copy_pair(val_stems,   paths["val_img"],   paths["val_lbl"])
    print(f"   ✅ Train: {len(train_stems)} | Val: {len(val_stems)}")

    # ---------------------------------------------------------
    # 4️⃣ GÉNÉRER DATA.YAML
    # ---------------------------------------------------------
    print("\n📝 Étape 4 : Génération de data.yaml...")
    class_names = [
        "Adem", "Alena", "Ali", "Amelie", "Amir", "Benign", "Ibtihel", "Insaf",
        "Malignant", "Mohamed", "Normal", "Sami", "Seline", "client", "employé",
        "employé actif", "employé inactif", "machine", "machine arrêtée", "porte_verte",
        "produit", "tables", "tables_vides", "temp", "table"
    ]
    
    yaml_lines = [
        f"path: {BASE_DIR.as_posix()}",  # Chemin absolu en format POSIX pour compatibilité YOLO/Windows
        "train: train/images",
        "val: val/images",
        "",
        f"nc: {len(class_names)}",
        "names:"
    ]
    for i, name in enumerate(class_names):
        yaml_lines.append(f"  {i}: {name}")
        
    yaml_path = BASE_DIR / "data.yaml"
    with open(yaml_path, "w", encoding="utf-8") as f:
        f.write("\n".join(yaml_lines) + "\n")
    print(f"   ✅ data.yaml créé : {yaml_path}")

    # ---------------------------------------------------------
    # 🏁 RÉCAPITULATIF
    # ---------------------------------------------------------
    print("\n" + "="*60)
    print("🎉 DATASET PRÊT POUR L'ENTRAÎNEMENT !")
    print("="*60)
    print("📁 Structure créée :")
    print("   project-root/")
    print("   ├── train/images  & train/labels")
    print("   ├── val/images    & val/labels")
    print("   └── data.yaml")
    print("\n🚀 Lance l'entraînement avec :")
    print(f"   yolo train data=\"{yaml_path}\" model=yolo11n.pt epochs=100 imgsz=640 batch=16")

if __name__ == "__main__":
    main()