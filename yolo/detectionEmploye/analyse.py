#!/usr/bin/env python3
"""
Analyse complète du dataset YOLO pour détection de visages d'employés
"""

import os
from collections import defaultdict
from pathlib import Path

# Classes définies
CLASSES = {
    0: "Adem",
    1: "Alena", 
    2: "Ali",
    3: "Amelie",
    4: "Amir",
    5: "Benign",      # À SUPPRIMER - classe médicale
    6: "Ibtihel",
    7: "Insaf",
    8: "Malignant",   # À SUPPRIMER - classe médicale
    9: "Mohamed",
    10: "Normal",     # À SUPPRIMER - classe médicale
    11: "Sami",
    12: "Seline",
    13: "employe",    # Redondant avec "employé"
    14: "porte_verte",
    15: "temp",       # Employé temporaire
    16: "employé"     # Redondant avec "employe"
}

CLASSES_PROPRES = {
    0: "Adem",
    1: "Alena", 
    2: "Ali",
    3: "Amelie",
    4: "Amir",
    5: "Ibtihel",
    6: "Insaf",
    7: "Mohamed",
    8: "Sami",
    9: "Seline",
    10: "temp",        # Employé temporaire
    11: "porte_verte"  # Si nécessaire
}

def analyze_annotations(labels_content):
    """Analyse les annotations fournies"""
    
    stats = defaultdict(lambda: {"count": 0, "images": set(), "total_boxes": 0})
    
    # Parse les données
    lines = labels_content.strip().split('\n')
    current_file = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Détection du nom de fichier
        if line.endswith(':'):
            current_file = line[:-1]
            continue
        
        # Parse annotation YOLO: class_id x_center y_center width height
        parts = line.split()
        if len(parts) >= 5:
            try:
                class_id = int(parts[0])
                if class_id in CLASSES:
                    class_name = CLASSES[class_id]
                    stats[class_name]["count"] += 1
                    stats[class_name]["total_boxes"] += 1
                    if current_file:
                        stats[class_name]["images"].add(current_file)
            except ValueError:
                pass
    
    return stats

def print_analysis(stats):
    """Affiche l'analyse complète"""
    
    print("=" * 80)
    print("ANALYSE DU DATASET - DÉTECTION DE VISAGES D'EMPLOYÉS")
    print("=" * 80)
    print()
    
    # Statistiques par classe
    print("📊 DISTRIBUTION DES CLASSES:")
    print("-" * 80)
    print(f"{'Classe':<20} {'Images':<10} {'Boxes':<10} {'Statut'}")
    print("-" * 80)
    
    total_images = 0
    total_boxes = 0
    
    # Employés nommés
    employes_nommes = ["Adem", "Alena", "Ali", "Amelie", "Amir", "Ibtihel", "Insaf", "Mohamed", "Sami", "Seline"]
    
    print("\n👤 EMPLOYÉS NOMMÉS:")
    for emp in employes_nommes:
        if emp in stats:
            img_count = len(stats[emp]["images"])
            box_count = stats[emp]["total_boxes"]
            total_images += img_count
            total_boxes += box_count
            status = "✅ OK" if img_count >= 2 else "⚠️  FAIBLE"
            print(f"{emp:<20} {img_count:<10} {box_count:<10} {status}")
    
    # Classe temp
    print("\n⏳ EMPLOYÉS TEMPORAIRES:")
    if "temp" in stats:
        img_count = len(stats["temp"]["images"])
        box_count = stats["temp"]["total_boxes"]
        status = "✅ OK" if img_count >= 20 else "❌ INSUFFISANT"
        print(f"{'temp':<20} {img_count:<10} {box_count:<10} {status}")
        total_images += img_count
        total_boxes += box_count
    
    # Classes problématiques
    print("\n❌ CLASSES À NETTOYER:")
    problematic = ["employe", "employé", "Benign", "Malignant", "Normal"]
    for cls in problematic:
        if cls in stats:
            img_count = len(stats[cls]["images"])
            box_count = stats[cls]["total_boxes"]
            print(f"{cls:<20} {img_count:<10} {box_count:<10} ⚠️  À SUPPRIMER")
    
    # Autres classes
    print("\n🚪 AUTRES CLASSES:")
    if "porte_verte" in stats:
        img_count = len(stats["porte_verte"]["images"])
        box_count = stats["porte_verte"]["total_boxes"]
        print(f"{'porte_verte':<20} {img_count:<10} {box_count:<10} ℹ️  Optionnel")
    
    print("\n" + "=" * 80)
    print(f"TOTAL: {total_images} images | {total_boxes} boxes")
    print("=" * 80)
    
    # Problèmes identifiés
    print("\n🔍 PROBLÈMES IDENTIFIÉS:")
    print("-" * 80)
    
    problems = []
    
    if "temp" in stats and len(stats["temp"]["images"]) < 20:
        problems.append("❌ Classe 'temp' sous-représentée (besoin de 50+ images minimum)")
    
    if "employe" in stats or "employé" in stats:
        problems.append("⚠️  Classes redondantes 'employe' et 'employé' à fusionner")
    
    if "Benign" in stats or "Malignant" in stats or "Normal" in stats:
        problems.append("❌ Classes médicales non pertinentes à supprimer")
    
    for emp in employes_nommes:
        if emp in stats and len(stats[emp]["images"]) < 2:
            problems.append(f"⚠️  '{emp}' a trop peu d'images (recommandé: 5+ par personne)")
    
    if problems:
        for p in problems:
            print(f"  {p}")
    else:
        print("  ✅ Aucun problème majeur détecté")
    
    print()
    print("=" * 80)

# Données d'analyse
annotations_data = """
000db9bd__Ali:
2 0.5368633764128428 0.49582338902147965 0.9262732471743144 0.9653937947494033

0de1f6bd__temp_dariver_frame_00012:
12 0.21263590559533277 0.5214797136038186 0.18644921771413414 0.17899761336515518
2 0.6316229116945107 0.4952267303102626 0.20739856801909312 0.1813842482100238
13 0.862423760275789 0.6211217183770884 0.2625828692654468 0.7124105011933173
13 0.2042561654733492 0.6312649164677804 0.30376557942190396 0.46062052505966583
13 0.6159108989657915 0.5829355608591885 0.2891010342084327 0.4379474940334129
15 0.493357199681782 0.1467780429594272 0.5761071333863697 0.1479713603818616
0 0.901180058339963 0.4767303102625299 0.19763988332007415 0.35202863961813835
14 0.4968575974542558 0.21599045346062049 0.9895253248475196 0.14558472553699284

6b7ba1ee__Mohamed:
9 0.519954919119597 0.486873508353222 0.8267037920975869 0.7756563245823389

9ea09ea1__Sami:
11 0.5080277717509222 0.4988066825775656 0.9340420915599914 0.9618138424821002

0231a03b__Amir:
4 0.5341572343391857 0.49701670644391405 0.8837874240884709 0.8914081145584726

449121dc__Seline:
12 0.49208071165111733 0.4946300715990454 0.9138641787806465 0.9797136038186157

a776aa0d__Insaf:
7 0.5055464049211739 0.5 0.9889071901576524 0.9856801909307876

aba4e177__Adem:
0 0.45477326968973747 0.48926014319809064 0.8036533871856067 0.9164677804295941

b925a278__Ibtihel:
6 0.5043245007445485 0.4982100238663485 0.991350998510903 0.9868735083532221

e3e6832c__Alena:
1 0.5151714037752223 0.49761336515513127 0.9102299848123236 0.9403341288782816

bc46f3fc__Amélie:
3 0.5118861932234604 0.49582338902147965 0.9762276135530792 0.9653937947494033
"""

if __name__ == "__main__":
    stats = analyze_annotations(annotations_data)
    print_analysis(stats)