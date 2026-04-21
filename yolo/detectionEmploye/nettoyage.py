#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nettoyage dataset YOLO - CAMIA-Factory
SANS fusion entre temp et employe (classes séparées)
"""

import os
import shutil
from pathlib import Path
from collections import defaultdict

# Mapping des classes - SANS FUSION
CLASS_MAPPING = {
    0: 0,    # Adem
    1: 1,    # Alena
    2: 2,    # Ali
    3: 3,    # Amelie
    4: 4,    # Amir
    5: None, # Benign → SUPPRIMER
    6: 5,    # Ibtihel
    7: 6,    # Insaf
    8: None, # Malignant → SUPPRIMER
    9: 7,    # Mohamed
    10: None,# Normal → SUPPRIMER
    11: 8,   # Sami
    12: 9,   # Seline
    13: 10,  # employe → GARDER SÉPARÉ
    14: 11,  # porte_verte
    15: 12,  # temp → GARDER SÉPARÉ
    16: 10   # employé → employe (même chose avec accent)
}

CLASSES_FINALES = {
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
    10: "employe",      # CLASSE SÉPARÉE
    11: "porte_verte",
    12: "temp"          # CLASSE SÉPARÉE
}

def nettoyer_fichier_label(input_path, output_path):
    """Nettoie un fichier label YOLO"""
    
    lignes_nettoyees = []
    stats = defaultdict(int)
    
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            for ligne in f:
                ligne = ligne.strip()
                if not ligne:
                    continue
                
                parties = ligne.split()
                if len(parties) < 5:
                    continue
                
                try:
                    ancien_id = int(parties[0])
                    nouveau_id = CLASS_MAPPING.get(ancien_id)
                    
                    # Ignorer classes supprimées
                    if nouveau_id is None:
                        stats['supprimé'] += 1
                        continue
                    
                    # Reconstruire avec nouveau ID
                    parties[0] = str(nouveau_id)
                    lignes_nettoyees.append(' '.join(parties))
                    stats[CLASSES_FINALES[nouveau_id]] += 1
                    
                except (ValueError, KeyError):
                    continue
    
    except Exception as e:
        print(f"❌ Erreur lecture {input_path.name}: {e}")
        return False, stats
    
    # Écrire fichier nettoyé
    if lignes_nettoyees:
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lignes_nettoyees) + '\n')
            return True, stats
        except Exception as e:
            print(f"❌ Erreur écriture {output_path.name}: {e}")
            return False, stats
    
    return False, stats

def traiter_dataset(source_dir, output_dir):
    """Traitement complet du dataset"""
    
    source_dir = Path(source_dir)
    output_dir = Path(output_dir)
    
    source_images = source_dir / "images"
    source_labels = source_dir / "labels"
    
    output_images = output_dir / "images"
    output_labels = output_dir / "labels"
    
    # Créer répertoires
    output_images.mkdir(parents=True, exist_ok=True)
    output_labels.mkdir(parents=True, exist_ok=True)
    
    stats_globales = defaultdict(int)
    traites = 0
    ignores = 0
    
    print("\n" + "=" * 80)
    print("🧹 NETTOYAGE DU DATASET (temp ET employe SÉPARÉS)")
    print("=" * 80)
    print()
    
    fichiers_labels = list(source_labels.glob("*.txt"))
    total = len(fichiers_labels)
    
    print(f"📊 {total} fichiers de labels trouvés\n")
    
    for idx, fichier_label in enumerate(fichiers_labels, 1):
        nom_base = fichier_label.stem
        
        # Chercher image correspondante
        fichier_image = None
        for ext in ['.jpg', '.png', '.jpeg', '.JPG', '.PNG']:
            candidat = source_images / f"{nom_base}{ext}"
            if candidat.exists():
                fichier_image = candidat
                break
        
        if not fichier_image:
            print(f"⚠️  [{idx}/{total}] Image manquante: {nom_base}")
            ignores += 1
            continue
        
        # Nettoyer label
        output_label = output_labels / fichier_label.name
        
        succes, stats = nettoyer_fichier_label(fichier_label, output_label)
        
        if succes:
            # Copier image
            output_image = output_images / fichier_image.name
            try:
                shutil.copy2(fichier_image, output_image)
                traites += 1
                
                for cls, count in stats.items():
                    stats_globales[cls] += count
                
                if traites % 10 == 0:
                    print(f"✅ [{traites}/{total}] En cours...")
                    
            except Exception as e:
                print(f"❌ Erreur copie {fichier_image.name}: {e}")
                ignores += 1
        else:
            ignores += 1
    
    print(f"\n" + "=" * 80)
    print("✅ NETTOYAGE TERMINÉ")
    print("=" * 80)
    print(f"\n📊 RÉSULTATS:")
    print(f"   ✅ {traites} paires traitées")
    print(f"   ⚠️  {ignores} fichiers ignorés")
    
    print(f"\n📋 ANNOTATIONS PAR CLASSE:")
    print("-" * 80)
    
    # Séparer les catégories pour affichage
    employes = ["Adem", "Alena", "Ali", "Amelie", "Amir", "Ibtihel", "Insaf", "Mohamed", "Sami", "Seline"]
    
    print("\n👤 EMPLOYÉS NOMMÉS:")
    for emp in employes:
        if emp in stats_globales:
            print(f"   {emp:<15} : {stats_globales[emp]:>3} annotations")
    
    print("\n⚠️  CLASSES GÉNÉRIQUES:")
    if "employe" in stats_globales:
        print(f"   {'employe':<15} : {stats_globales['employe']:>3} annotations")
    if "temp" in stats_globales:
        print(f"   {'temp':<15} : {stats_globales['temp']:>3} annotations")
    
    print("\n🚪 AUTRES:")
    if "porte_verte" in stats_globales:
        print(f"   {'porte_verte':<15} : {stats_globales['porte_verte']:>3} annotations")
    
    print(f"\n📁 Dataset nettoyé: {output_dir}")
    print("=" * 80)
    
    return traites, ignores

def creer_data_yaml(output_dir):
    """Crée le fichier data.yaml"""
    
    output_dir = Path(output_dir)
    
    contenu = f"""# Configuration YOLO - Détection employés CAMIA-Factory
# Généré automatiquement
# temp et employe sont des classes SÉPARÉES

path: {output_dir.absolute()}
train: images
val: images

nc: {len(CLASSES_FINALES)}

names:
"""
    
    for class_id, nom in sorted(CLASSES_FINALES.items()):
        contenu += f"  {class_id}: {nom}\n"
    
    yaml_path = output_dir / "data.yaml"
    
    try:
        with open(yaml_path, 'w', encoding='utf-8') as f:
            f.write(contenu)
        
        print("\n" + "=" * 80)
        print("📝 FICHIER data.yaml CRÉÉ")
        print("=" * 80)
        print(f"📍 {yaml_path}")
        print()
        print("📋 CLASSES CONFIGURÉES (13 classes):")
        print("-" * 80)
        for class_id, nom in sorted(CLASSES_FINALES.items()):
            print(f"   {class_id:>2}: {nom}")
        print()
        
        return yaml_path
        
    except Exception as e:
        print(f"❌ Erreur création data.yaml: {e}")
        return None

def main():
    """Fonction principale"""
    
    print("\n" + "=" * 80)
    print("NETTOYAGE DATASET YOLO - CAMIA-FACTORY")
    print("temp et employe = CLASSES SÉPARÉES")
    print("=" * 80)
    
    # Chemins
    repertoire_actuel = Path(__file__).parent
    source = repertoire_actuel
    destination = repertoire_actuel.parent / "detectionEmploye_clean_v2"
    
    print(f"\n📂 Source      : {source}")
    print(f"📂 Destination : {destination}")
    print()
    print("⚠️  IMPORTANT: temp et employe seront des classes distinctes")
    print()
    
    # Confirmation
    reponse = input("🔄 Continuer? (o/n): ").strip().lower()
    if reponse not in ['o', 'oui', 'y', 'yes']:
        print("❌ Annulé")
        return
    
    # Traiter
    traites, ignores = traiter_dataset(source, destination)
    
    if traites == 0:
        print("⚠️  Aucun fichier traité")
        return
    
    # Créer data.yaml
    creer_data_yaml(destination)
    
    print("\n💡 PROCHAINES ÉTAPES:")
    print("   1. Vérifier le dataset dans:", destination)
    print("   2. Lancer: cd", destination)
    print("   3. Lancer: python entrainer_yolo.py")
    print()
    print("📊 DIFFÉRENCES AVEC PRÉCÉDENT:")
    print("   ✅ temp (classe 12) = employés temporaires")
    print("   ✅ employe (classe 10) = employés génériques")
    print("   → DEUX CLASSES DISTINCTES")
    print()

if __name__ == "__main__":
    main()