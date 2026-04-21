from pathlib import Path
from collections import Counter, defaultdict
import statistics

print("=" * 70)
print("ANALYSE COMPLÈTE DES LABELS YOLO")
print("=" * 70)

labels_dir = Path(r"C:\Users\eyama\OneDrive\Bureau\camIA-factory\yolo\detection_final\labels")

# Toutes les classes YOLO possibles
ALL_CLASSES = [
    "client",           # 0
    "machine",          # 1
    "machine arrêtée",  # 2
    "produit",          # 3
    "employé",          # 4
    "employé actif",    # 5
    "employé inactif",  # 6
    "tables",           # 7
    "tables_vides"      # 8
]

# Statistiques globales
class_counts = Counter()
video_source_stats = defaultdict(lambda: Counter())
total_boxes = 0
total_files = 0

# Statistiques de taille de boîtes
box_sizes = defaultdict(list)  # Pour chaque classe

print(f"\n📂 Analyse du dossier: {labels_dir}")

# Parcourir tous les fichiers
for label_file in labels_dir.glob("*.txt"):
    total_files += 1
    
    # Extraire la source vidéo
    filename = label_file.stem
    if '__' in filename:
        video_source = filename.split('__')[1].rsplit('_frame_', 1)[0]
    else:
        video_source = "unknown"
    
    # Lire le fichier
    with open(label_file, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if not parts or len(parts) < 5:
                continue
            
            try:
                class_id = int(parts[0])
                x_center = float(parts[1])
                y_center = float(parts[2])
                width = float(parts[3])
                height = float(parts[4])
                
                # Compter
                class_counts[class_id] += 1
                video_source_stats[video_source][class_id] += 1
                total_boxes += 1
                
                # Taille de la boîte (aire)
                box_area = width * height
                box_sizes[class_id].append(box_area)
                
            except (ValueError, IndexError) as e:
                print(f"⚠️  Erreur dans {label_file.name}: {line.strip()}")

# ========================================
# RAPPORT GLOBAL
# ========================================
print(f"\n" + "=" * 70)
print("📊 STATISTIQUES GLOBALES")
print("=" * 70)

print(f"\nFichiers analysés: {total_files}")
print(f"Annotations totales: {total_boxes}")
print(f"Sources vidéo: {len(video_source_stats)}")

# ========================================
# DISTRIBUTION PAR CLASSE
# ========================================
print(f"\n" + "=" * 70)
print("📈 DISTRIBUTION PAR CLASSE")
print("=" * 70)

print(f"\n{'ID':<5} {'Classe':<20} {'Count':<10} {'%':<8} {'Graphique'}")
print("-" * 70)

for class_id in range(len(ALL_CLASSES)):
    count = class_counts.get(class_id, 0)
    pct = (count / total_boxes * 100) if total_boxes > 0 else 0
    bar_length = int(pct / 2)
    bar = "█" * bar_length
    
    status = "✅" if count > 0 else "❌"
    print(f"{class_id:<5} {ALL_CLASSES[class_id]:<20} {count:<10} {pct:>6.1f}%  {bar} {status}")

print(f"\n{'TOTAL':<5} {'':<20} {total_boxes:<10} 100.0%")

# ========================================
# TAILLE DES BOÎTES
# ========================================
print(f"\n" + "=" * 70)
print("📏 TAILLE MOYENNE DES BOÎTES (aire normalisée)")
print("=" * 70)

print(f"\n{'Classe':<20} {'Min':<10} {'Moyenne':<10} {'Max':<10} {'Médiane':<10}")
print("-" * 70)

for class_id in range(len(ALL_CLASSES)):
    if class_id in box_sizes and box_sizes[class_id]:
        sizes = box_sizes[class_id]
        min_size = min(sizes)
        avg_size = statistics.mean(sizes)
        max_size = max(sizes)
        median_size = statistics.median(sizes)
        
        print(f"{ALL_CLASSES[class_id]:<20} {min_size:<10.4f} {avg_size:<10.4f} {max_size:<10.4f} {median_size:<10.4f}")

# ========================================
# PAR SOURCE VIDÉO
# ========================================
print(f"\n" + "=" * 70)
print("📹 DISTRIBUTION PAR SOURCE VIDÉO")
print("=" * 70)

print(f"\n{'Source':<35} {'Frames':<10} {'Boxes':<10} {'Classes utilisées'}")
print("-" * 70)

for source in sorted(video_source_stats.keys()):
    frame_count = sum(1 for f in labels_dir.glob("*.txt") 
                     if source in f.stem)
    box_count = sum(video_source_stats[source].values())
    classes_used = [str(c) for c in sorted(video_source_stats[source].keys())]
    classes_str = ','.join(classes_used)
    
    print(f"{source:<35} {frame_count:<10} {box_count:<10} {classes_str}")

# ========================================
# DÉSÉQUILIBRE
# ========================================
print(f"\n" + "=" * 70)
print("⚖️  ANALYSE DU DÉSÉQUILIBRE")
print("=" * 70)

if total_boxes > 0:
    # Classes avec annotations
    classes_with_data = [c for c in class_counts.keys() if class_counts[c] > 0]
    
    if len(classes_with_data) > 1:
        max_count = max(class_counts[c] for c in classes_with_data)
        min_count = min(class_counts[c] for c in classes_with_data)
        ratio = max_count / min_count if min_count > 0 else float('inf')
        
        max_class = max(classes_with_data, key=lambda c: class_counts[c])
        min_class = min(classes_with_data, key=lambda c: class_counts[c])
        
        print(f"\nClasse dominante: {ALL_CLASSES[max_class]} ({class_counts[max_class]} annotations)")
        print(f"Classe minoritaire: {ALL_CLASSES[min_class]} ({class_counts[min_class]} annotations)")
        print(f"Ratio déséquilibre: {ratio:.1f}:1")
        
        if ratio > 100:
            print(f"\n🔴 DÉSÉQUILIBRE CRITIQUE (>{ratio:.0f}:1)")
            print(f"   → Le modèle aura du mal à apprendre les classes minoritaires")
        elif ratio > 50:
            print(f"\n🟠 DÉSÉQUILIBRE SÉVÈRE ({ratio:.1f}:1)")
            print(f"   → Envisager data augmentation ou class weights")
        elif ratio > 10:
            print(f"\n🟡 DÉSÉQUILIBRE MODÉRÉ ({ratio:.1f}:1)")
            print(f"   → Acceptable mais peut affecter les performances")
        else:
            print(f"\n🟢 DÉSÉQUILIBRE ACCEPTABLE ({ratio:.1f}:1)")

# ========================================
# CLASSES MANQUANTES
# ========================================
missing_classes = [i for i in range(len(ALL_CLASSES)) if class_counts.get(i, 0) == 0]

if missing_classes:
    print(f"\n" + "=" * 70)
    print("❌ CLASSES SANS ANNOTATIONS")
    print("=" * 70)
    
    for class_id in missing_classes:
        print(f"   {class_id}: {ALL_CLASSES[class_id]}")
    
    print(f"\n⚠️  Ces classes ne pourront PAS être apprises par le modèle")

# ========================================
# CLASSES INSUFFISANTES
# ========================================
insufficient_classes = [i for i in range(len(ALL_CLASSES)) 
                       if 0 < class_counts.get(i, 0) < 20]

if insufficient_classes:
    print(f"\n" + "=" * 70)
    print("⚠️  CLASSES AVEC PEU D'EXEMPLES (<20)")
    print("=" * 70)
    
    for class_id in insufficient_classes:
        print(f"   {class_id}: {ALL_CLASSES[class_id]} ({class_counts[class_id]} annotations)")
    
    print(f"\n💡 Recommandation: ajouter au minimum 50 exemples par classe")

# ========================================
# EXEMPLES DE FICHIERS
# ========================================
print(f"\n" + "=" * 70)
print("📄 EXEMPLES DE FICHIERS PAR CLASSE")
print("=" * 70)

# Trouver un exemple pour chaque classe
class_examples = {}
for label_file in labels_dir.glob("*.txt"):
    with open(label_file, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if parts:
                class_id = int(parts[0])
                if class_id not in class_examples and class_id < len(ALL_CLASSES):
                    class_examples[class_id] = label_file.name

print()
for class_id in range(len(ALL_CLASSES)):
    example = class_examples.get(class_id, "Aucun exemple")
    print(f"{class_id}: {ALL_CLASSES[class_id]:<20} → {example}")

# ========================================
# RECOMMANDATIONS
# ========================================
print(f"\n" + "=" * 70)
print("💡 RECOMMANDATIONS")
print("=" * 70)

print(f"\n1. DATASET:")
print(f"   Total actuel: {total_files} images")
print(f"   Recommandé: 300-500 images minimum pour 9 classes")
print(f"   → Ajouter +{300 - total_files} images")

if missing_classes or insufficient_classes:
    print(f"\n2. CLASSES À AUGMENTER:")
    for class_id in missing_classes + insufficient_classes:
        current = class_counts.get(class_id, 0)
        needed = 50 - current
        print(f"   {ALL_CLASSES[class_id]}: +{needed} exemples minimum")

if ratio > 10:
    print(f"\n3. ÉQUILIBRAGE:")
    print(f"   Ratio actuel: {ratio:.1f}:1")
    print(f"   → Augmenter les classes minoritaires")
    print(f"   → Ou utiliser class_weights pendant l'entraînement")

print(f"\n4. ENTRAÎNEMENT:")
print(f"   Avec ce dataset actuel:")
print(f"   - mAP attendu: 15-25% (faible)")
print(f"   - Classes ignorées: {len(missing_classes)}")
print(f"   - Epochs recommandés: 200-300")

print(f"\n" + "=" * 70)
print("ANALYSE TERMINÉE")
print("=" * 70)