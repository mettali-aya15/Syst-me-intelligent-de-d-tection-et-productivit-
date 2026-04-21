import os
import shutil
import random
import re
from pathlib import Path

# 🔧 CONFIGURATION
BASE_DIR = Path(r"C:\Users\eyama\OneDrive\Bureau\camIA-factory\yolo_image\project-dection")
IMG_DIR = BASE_DIR / "images"
LAB_DIR = BASE_DIR / "labels"
OUT_DIR = BASE_DIR / "dataset"
TRAIN_RATIO = 0.8
SEED = 42

def clean_filename(name: str) -> str:
    """Remplace %20, espaces et caractères spéciaux par des underscores"""
    name = name.replace("%20", "_").replace(" ", "_")
    return re.sub(r'[^\w\-\.]', '_', name)

def main():
    random.seed(SEED)
    print("🔍 Vérification des dossiers...")
    if not IMG_DIR.exists() or not LAB_DIR.exists():
        print("❌ Erreur: Les dossiers 'images' et/ou 'labels' sont introuvables.")
        return

    print("🧹 Nettoyage des noms de fichiers...")
    valid_pairs = []
    for img_path in IMG_DIR.glob("*.jpg"):
        stem = img_path.stem
        txt_path = LAB_DIR / f"{stem}.txt"

        if not txt_path.exists():
            print(f"⚠️  [SKIP] Pas de label pour {img_path.name}")
            continue

        new_stem = clean_filename(stem)
        if new_stem != stem:
            new_img = img_path.parent / f"{new_stem}.jpg"
            new_txt = txt_path.parent / f"{new_stem}.txt"
            img_path.rename(new_img)
            txt_path.rename(new_txt)
            print(f"  ✅ Renommé: {stem} -> {new_stem}")
        else:
            new_img = img_path
            new_txt = txt_path

        # Vérification rapide du format YOLO
        with open(new_txt, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]
            if not lines:
                print(f"⚠️  [WARN] Label vide: {new_txt.name}")
            for line in lines:
                parts = line.split()
                if len(parts) != 5:
                    print(f"⚠️  [WARN] Format invalide dans {new_txt.name}: {line}")

        valid_pairs.append((new_img, new_txt))

    print(f"📊 {len(valid_pairs)} paires valides trouvées.\n")

    print("📁 Création de la structure train/val...")
    for split in ["train", "val"]:
        (OUT_DIR / split / "images").mkdir(parents=True, exist_ok=True)
        (OUT_DIR / split / "labels").mkdir(parents=True, exist_ok=True)

    random.shuffle(valid_pairs)
    split_idx = int(len(valid_pairs) * TRAIN_RATIO)
    train_list, val_list = valid_pairs[:split_idx], valid_pairs[split_idx:]
    print(f"📈 Split: {len(train_list)} train / {len(val_list)} val")

    def copy_split(file_list, split_name):
        for img_p, lab_p in file_list:
            shutil.copy(img_p, OUT_DIR / split_name / "images" / img_p.name)
            shutil.copy(lab_p, OUT_DIR / split_name / "labels" / lab_p.name)

    copy_split(train_list, "train")
    copy_split(val_list, "val")

    # ✅ CORRECTION: as_posix() évite les backslashes dans le f-string
    dataset_path = OUT_DIR.resolve().as_posix()
    yaml_path = BASE_DIR / "data.yaml"
    
    yaml_content = (
        f"path: {dataset_path}\n"
        "train: train\n"
        "val: val\n"
        "\n"
        "nc: 12\n"
        "names:\n"
        "  0: Benign\n"
        "  1: Malignant\n"
        "  2: Normal\n"
        "  3: client\n"
        "  4: employé\n"
        "  5: employé actif\n"
        "  6: employé inactif\n"
        "  7: machine\n"
        "  8: machine arrêtée\n"
        "  9: produit\n"
        "  10: tables\n"
        "  11: tables_vides\n"
    )

    with open(yaml_path, "w", encoding="utf-8") as f:
        f.write(yaml_content)

    print(f"\n✅ TERMINÉ !")
    print(f"📂 Dataset structuré dans: {OUT_DIR}")
    print(f"📄 YAML généré: {yaml_path}")
    print(f"\n🚀 Commande pour lancer l'entraînement :")
    print(f"   yolo train data={yaml_path} model=yolov8n.pt epochs=100 imgsz=640 batch=16")

if __name__ == "__main__":
    main()