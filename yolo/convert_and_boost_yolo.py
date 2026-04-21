#!/usr/bin/env python3
"""
Préparation Dataset V3 - CAMIA Factory
153 images (133 anciennes + 20 portraits)
Amélioration de la détection des employés nommés
"""

import os
import shutil
import random
from pathlib import Path
import yaml

# =============================================================================
# CONFIGURATION
# =============================================================================

DATASET_SOURCE = r"C:\Users\eyama\OneDrive\Bureau\camIA-factory\yolo\project-10-at-2026-04-05-01-32-41fea5c6"
DATASET_OUTPUT = r"C:\Users\eyama\OneDrive\Bureau\camIA-factory\yolo\dataset_v3"

TRAIN_RATIO = 0.70
VAL_RATIO = 0.20
TEST_RATIO = 0.10

# MAPPING DES CLASSES (supprimer Benign, Normal, Malignant)
CLASS_ID_MAPPING = {
    0: 0,    # Adem
    1: 1,    # Alena
    2: 2,    # Ali
    3: 3,    # Amelie
    4: 4,    # Amir
    # 5: Benign (SUPPRIMÉ)
    6: 5,    # Ibtihel
    7: 6,    # Insaf
    # 8: Malignant (SUPPRIMÉ)
    9: 7,    # Mohamed
    # 10: Normal (SUPPRIMÉ)
    11: 8,   # Sami
    12: 9,   # Seline
    13: 10,  # client
    14: 11,  # employé
    15: 12,  # employé actif
    16: 13,  # employé inactif
    17: 14,  # machine
    18: 15,  # machine arrêtée
    19: 16,  # porte_verte
    20: 17,  # produit
    21: 18,  # tables
    22: 19,  # tables_vides
    23: 20,  # temp
    24: 21,  # table
}

# 22 CLASSES FINALES
FINAL_CLASSES = [
    "Adem",              # 0
    "Alena",             # 1
    "Ali",               # 2
    "Amelie",            # 3
    "Amir",              # 4
    "Ibtihel",           # 5
    "Insaf",             # 6
    "Mohamed",           # 7
    "Sami",              # 8
    "Seline",            # 9
    "client",            # 10
    "employé",           # 11
    "employé actif",     # 12
    "employé inactif",   # 13
    "machine",           # 14
    "machine arrêtée",   # 15
    "porte_verte",       # 16
    "produit",           # 17
    "tables",            # 18
    "tables_vides",      # 19
    "temp",              # 20
    "table",             # 21
]

# Classes rares
RARE_CLASSES = [10, 13, 15, 19]

# IDs des employés nommés
NAMED_EMPLOYEES = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9}

# =============================================================================
# FONCTIONS
# =============================================================================

def create_directory_structure(base_path):
    """Crée la structure de répertoires"""
    for split in ['train', 'val', 'test']:
        (Path(base_path) / split / 'images').mkdir(parents=True, exist_ok=True)
        (Path(base_path) / split / 'labels').mkdir(parents=True, exist_ok=True)
    print(f"✓ Structure créée: {base_path}")


def process_label_file(label_path):
    """Traite un fichier label"""
    with open(label_path, 'r') as f:
        lines = f.readlines()
    
    new_lines = []
    classes_found = set()
    
    for line in lines:
        parts = line.strip().split()
        if not parts:
            continue
        
        old_class_id = int(parts[0])
        
        if old_class_id in CLASS_ID_MAPPING:
            new_class_id = CLASS_ID_MAPPING[old_class_id]
            parts[0] = str(new_class_id)
            new_lines.append(' '.join(parts) + '\n')
            classes_found.add(new_class_id)
    
    return new_lines, classes_found


def get_image_label_pairs(source_path):
    """Récupère les paires image/label"""
    images_dir = Path(source_path) / 'images'
    labels_dir = Path(source_path) / 'labels'
    
    # Chercher les images (.jpg et .png)
    image_files = list(images_dir.glob('*.jpg')) + list(images_dir.glob('*.png'))
    
    pairs = []
    portraits = 0
    scenes = 0
    total_before = 0
    total_after = 0
    skipped = 0
    
    for img_file in image_files:
        label_file = labels_dir / (img_file.stem + '.txt')
        
        if not label_file.exists():
            continue
        
        with open(label_file, 'r') as f:
            original = [l for l in f.readlines() if l.strip()]
            total_before += len(original)
        
        new_lines, classes = process_label_file(label_file)
        total_after += len(new_lines)
        
        if not new_lines:
            skipped += 1
            continue
        
        # Vérifier si c'est un portrait (employé nommé uniquement)
        is_portrait = (len(classes) == 1 and 
                      list(classes)[0] in NAMED_EMPLOYEES)
        
        if is_portrait:
            portraits += 1
        else:
            scenes += 1
        
        has_rare = any(cls in RARE_CLASSES for cls in classes)
        has_named = any(cls in NAMED_EMPLOYEES for cls in classes)
        
        pairs.append({
            'image': img_file,
            'label': label_file,
            'name': img_file.name,
            'processed_labels': new_lines,
            'classes': classes,
            'has_rare': has_rare,
            'has_named': has_named,
            'is_portrait': is_portrait
        })
    
    print(f"\n✓ {len(pairs)} paires valides")
    print(f"  - Portraits employés: {portraits}")
    print(f"  - Scènes complexes: {scenes}")
    print(f"  - Images ignorées: {skipped}")
    print(f"  - Annotations avant: {total_before}")
    print(f"  - Annotations après: {total_after}")
    print(f"  - Supprimées: {total_before - total_after}")
    
    return pairs


def stratified_split(pairs, train_ratio, val_ratio, test_ratio):
    """Split stratifié intelligent"""
    
    # Séparer portraits et scènes
    portraits = [p for p in pairs if p['is_portrait']]
    scenes_with_rare = [p for p in pairs if not p['is_portrait'] and p['has_rare']]
    scenes_normal = [p for p in pairs if not p['is_portrait'] and not p['has_rare']]
    
    print(f"\n📊 Analyse pour split:")
    print(f"  - Portraits: {len(portraits)}")
    print(f"  - Scènes avec classes rares: {len(scenes_with_rare)}")
    print(f"  - Scènes normales: {len(scenes_normal)}")
    
    # Mélanger chaque groupe
    random.shuffle(portraits)
    random.shuffle(scenes_with_rare)
    random.shuffle(scenes_normal)
    
    # Split portraits (important pour bien apprendre les employés)
    if portraits:
        n_train = max(1, int(len(portraits) * train_ratio))
        n_val = max(1, int(len(portraits) * val_ratio))
        
        portraits_train = portraits[:n_train]
        portraits_val = portraits[n_train:n_train + n_val]
        portraits_test = portraits[n_train + n_val:]
    else:
        portraits_train = portraits_val = portraits_test = []
    
    # Split scènes rares
    if scenes_with_rare:
        n_train = max(1, int(len(scenes_with_rare) * train_ratio))
        n_val = max(1, int(len(scenes_with_rare) * val_ratio))
        
        rare_train = scenes_with_rare[:n_train]
        rare_val = scenes_with_rare[n_train:n_train + n_val]
        rare_test = scenes_with_rare[n_train + n_val:]
    else:
        rare_train = rare_val = rare_test = []
    
    # Split scènes normales
    if scenes_normal:
        n_train = int(len(scenes_normal) * train_ratio)
        n_val = int(len(scenes_normal) * val_ratio)
        
        normal_train = scenes_normal[:n_train]
        normal_val = scenes_normal[n_train:n_train + n_val]
        normal_test = scenes_normal[n_train + n_val:]
    else:
        normal_train = normal_val = normal_test = []
    
    # Combiner
    train_pairs = portraits_train + rare_train + normal_train
    val_pairs = portraits_val + rare_val + normal_val
    test_pairs = portraits_test + rare_test + normal_test
    
    # Mélanger
    random.shuffle(train_pairs)
    random.shuffle(val_pairs)
    random.shuffle(test_pairs)
    
    total = len(pairs)
    
    print(f"\n✓ Split stratifié:")
    print(f"  - Train: {len(train_pairs)} images ({len(train_pairs)/total*100:.1f}%)")
    print(f"    • Portraits: {len(portraits_train)}")
    print(f"    • Scènes rares: {len(rare_train)}")
    print(f"  - Val: {len(val_pairs)} images ({len(val_pairs)/total*100:.1f}%)")
    print(f"    • Portraits: {len(portraits_val)}")
    print(f"    • Scènes rares: {len(rare_val)}")
    print(f"  - Test: {len(test_pairs)} images ({len(test_pairs)/total*100:.1f}%)")
    print(f"    • Portraits: {len(portraits_test)}")
    print(f"    • Scènes rares: {len(rare_test)}")
    
    return {
        'train': train_pairs,
        'val': val_pairs,
        'test': test_pairs
    }


def copy_files(splits_data, output_path):
    """Copie les fichiers"""
    for split_name, pairs in splits_data.items():
        images_dir = Path(output_path) / split_name / 'images'
        labels_dir = Path(output_path) / split_name / 'labels'
        
        for pair in pairs:
            # Copier l'image
            dest_name = pair['name']
            # Convertir .png en .jpg si nécessaire
            if dest_name.endswith('.png'):
                dest_name = dest_name.replace('.png', '.jpg')
            
            shutil.copy2(pair['image'], images_dir / dest_name)
            
            # Écrire le label
            label_name = dest_name.replace('.jpg', '.txt').replace('.png', '.txt')
            label_path = labels_dir / label_name
            
            with open(label_path, 'w') as f:
                f.writelines(pair['processed_labels'])
    
    print(f"\n✓ Fichiers copiés dans: {output_path}")


def create_data_yaml(output_path):
    """Crée data.yaml"""
    data_yaml = {
        'path': str(Path(output_path).absolute()),
        'train': 'train/images',
        'val': 'val/images',
        'test': 'test/images',
        'nc': len(FINAL_CLASSES),
        'names': FINAL_CLASSES
    }
    
    yaml_path = Path(output_path) / 'data.yaml'
    
    with open(yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(data_yaml, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    print(f"✓ data.yaml créé: {yaml_path}")
    
    return yaml_path


def analyze_dataset(pairs):
    """Analyse la distribution"""
    class_counts = {i: 0 for i in range(len(FINAL_CLASSES))}
    total = 0
    
    for pair in pairs:
        for line in pair['processed_labels']:
            parts = line.strip().split()
            if parts:
                cls = int(parts[0])
                class_counts[cls] += 1
                total += 1
    
    print("\n" + "="*70)
    print("DISTRIBUTION DES CLASSES (DATASET V3)")
    print("="*70)
    print(f"Total annotations: {total}")
    print(f"Nombre de classes: {len(FINAL_CLASSES)}")
    print(f"\n{'Classe':<25} {'ID':<5} {'Count':<10} {'%':<10}")
    print("-"*70)
    
    for cls, count in sorted(class_counts.items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            pct = (count / total) * 100
            marker = "⭐" if cls in NAMED_EMPLOYEES else ("⚠️ " if cls in RARE_CLASSES else "   ")
            print(f"{marker}{FINAL_CLASSES[cls]:<25} {cls:<5} {count:<10} {pct:>6.2f}%")
    
    print("="*70)
    print("\n⭐ Employés nommés (améliorés avec portraits):")
    for cls in NAMED_EMPLOYEES:
        if class_counts[cls] > 0:
            print(f"  - {FINAL_CLASSES[cls]}: {class_counts[cls]} exemples")
    print()


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("\n" + "="*70)
    print("PRÉPARATION DATASET V3 - CAMIA FACTORY")
    print("153 images (133 scènes + 20 portraits)")
    print("Amélioration détection employés nommés")
    print("="*70 + "\n")
    
    if not os.path.exists(DATASET_SOURCE):
        print(f"❌ Source introuvable: {DATASET_SOURCE}")
        return
    
    print(f"📁 Source: {DATASET_SOURCE}")
    print(f"📁 Destination: {DATASET_OUTPUT}\n")
    
    # Structure
    create_directory_structure(DATASET_OUTPUT)
    
    # Traitement
    print("\n🔄 Traitement des labels...")
    pairs = get_image_label_pairs(DATASET_SOURCE)
    
    if not pairs:
        print("❌ Aucune paire trouvée!")
        return
    
    # Analyse
    analyze_dataset(pairs)
    
    # Split
    splits_data = stratified_split(pairs, TRAIN_RATIO, VAL_RATIO, TEST_RATIO)
    
    # Copie
    copy_files(splits_data, DATASET_OUTPUT)
    
    # YAML
    yaml_path = create_data_yaml(DATASET_OUTPUT)
    
    # Résumé
    print("\n" + "="*70)
    print("✅ DATASET V3 PRÊT!")
    print("="*70)
    print(f"\n📊 RÉSUMÉ:")
    print(f"  - Images totales: {len(pairs)}")
    print(f"  - Portraits employés: {sum(1 for p in pairs if p['is_portrait'])}")
    print(f"  - Train: {len(splits_data['train'])}")
    print(f"  - Val: {len(splits_data['val'])}")
    print(f"  - Test: {len(splits_data['test'])}")
    
    print(f"\n💡 AMÉLIORATION PAR RAPPORT À V2:")
    print(f"  - V2: 3-17 exemples par employé nommé")
    print(f"  - V3: 5-19 exemples par employé nommé (+portraits)")
    print(f"  - Meilleure reconnaissance attendue!")
    
    print(f"\n📁 Dataset: {DATASET_OUTPUT}")
    print(f"📄 Config: {yaml_path}")
    
    print(f"\n🚀 PROCHAINE ÉTAPE:")
    print(f"  python train_yolo_v3.py")
    
    print("="*70 + "\n")


if __name__ == "__main__":
    random.seed(42)
    main()