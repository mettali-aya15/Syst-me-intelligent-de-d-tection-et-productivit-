from pathlib import Path
from collections import Counter

print("=" * 60)
print("ANALYSE DES CLASSES DANS LES LABELS")
print("=" * 60)

labels_dir = Path(r"C:\Users\eyama\OneDrive\Bureau\camIA-factory\yolo\detection_final\labels_backup")

# Compter toutes les classes utilisées
all_classes = Counter()
file_class_samples = {}

for label_file in labels_dir.glob("*.txt"):
    with open(label_file, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if not parts:
                continue
            
            class_id = int(parts[0])
            all_classes[class_id] += 1
            
            # Garder un exemple de fichier pour chaque classe
            if class_id not in file_class_samples:
                file_class_samples[class_id] = label_file.name

print(f"\n📊 CLASSES TROUVÉES DANS VOS FICHIERS:")
print(f"\n{'Classe ID':<12} {'Count':<12} {'Exemple fichier'}")
print("-" * 70)

for class_id in sorted(all_classes.keys()):
    count = all_classes[class_id]
    example = file_class_samples.get(class_id, "")
    print(f"{class_id:<12} {count:<12} {example}")

print(f"\n{'TOTAL':<12} {sum(all_classes.values()):<12}")

print(f"\n" + "=" * 60)
print("CORRESPONDANCE SUPPOSÉE (basée sur Label Studio):")
print("=" * 60)

label_studio_classes = [
    "Benign",           # 0
    "Malignant",        # 1  
    "Normal",           # 2
    "client",           # 3
    "employé",          # 4
    "employé actif",    # 5
    "employé inactif",  # 6
    "machine",          # 7
    "machine arrêtée",  # 8
    "produit",          # 9
    "tables",           # 10
    "tables_vides"      # 11
]

print(f"\nLabel Studio IDs:")
for i, name in enumerate(label_studio_classes):
    print(f"  {i}: {name}")

print(f"\n" + "=" * 60)
print("ANALYSE DÉTAILLÉE DE FICHIERS EXEMPLES:")
print("=" * 60)

# Analyser quelques fichiers spécifiques
test_files = [
    "0ba30f5e__delice_factory_frame_00008.txt",  # produits
    "7a341d28__barista_vlog_frame_02987.txt",   # employés + machines
    "8dffb339__Lean-manufacturing_frame_00003.txt"  # produits + employés
]

for filename in test_files:
    filepath = labels_dir / filename
    if filepath.exists():
        print(f"\n📄 {filename}:")
        class_count = Counter()
        
        with open(filepath, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if parts:
                    class_count[int(parts[0])] += 1
        
        for class_id in sorted(class_count.keys()):
            print(f"   Classe {class_id}: {class_count[class_id]} annotations")

print(f"\n" + "=" * 60)
print("HYPOTHÈSES DE MAPPING:")
print("=" * 60)

print(f"""
Basé sur l'analyse:

HYPOTHÈSE 1 (Label Studio direct - classes 3-11):
  3 → produit (beaucoup de petits objets)
  4 → employé
  5 → employé actif
  7 → machine
  ...

HYPOTHÈSE 2 (Déjà converti une fois - classes 0-8):
  0 → client
  1 → machine (grandes boîtes)
  2 → employé actif
  3 → produit (nombreux petits objets)
  4 → employé
  ...

Vérifiez manuellement dans Label Studio quel ID correspond à quoi !
""")