#!/usr/bin/env python3
"""
Test YOLOv8 avec POST-TRAITEMENT INTELLIGENT
Corrige automatiquement les confusions de classes en utilisant des règles métier
"""

from ultralytics import YOLO
import cv2
import numpy as np
from pathlib import Path
import os

# =============================================================================
# CONFIGURATION
# =============================================================================

MODEL_PATH = r"C:\Users\eyama\OneDrive\Bureau\camIA-factory\backend\runs\detect\runs\detect\camIA_factory_v2_22classes\weights\best.pt"
VIDEO_PATH = r"C:\Users\eyama\OneDrive\Bureau\camIA-factory\backend\data\videos\barista_vlog.mp4"
OUTPUT_DIR = r"C:\Users\eyama\OneDrive\Bureau\camIA-factory\backend\test_results_postprocessed"

# Seuils de confiance personnalisés par classe
CLASS_CONFIDENCE_THRESHOLDS = {
    10: 0.35,  # client (éviter confusion avec employé)
    13: 0.40,  # employé_inactif (rare, seuil plus élevé)
    15: 0.45,  # machine_arrêtée (confusion avec machine)
    19: 0.35,  # tables_vides (confusion avec tables)
}

# Mapping des noms de classes (22 classes)
CLASS_NAMES = {
    0: "Adem", 1: "Alena", 2: "Ali", 3: "Amelie", 4: "Amir",
    5: "Ibtihel", 6: "Insaf", 7: "Mohamed", 8: "Sami", 9: "Seline",
    10: "client", 11: "employé", 12: "employé_actif", 13: "employé_inactif",
    14: "machine", 15: "machine_arrêtée", 16: "porte_verte", 17: "produit",
    18: "tables", 19: "tables_vides", 20: "temp", 21: "table"
}

# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================

def calculate_distance(box1, box2):
    """Calcule la distance euclidienne entre les centres de deux boxes"""
    center1 = ((box1[0] + box1[2]) / 2, (box1[1] + box1[3]) / 2)
    center2 = ((box2[0] + box2[2]) / 2, (box2[1] + box2[3]) / 2)
    return np.sqrt((center1[0] - center2[0])**2 + (center1[1] - center2[1])**2)


def box_overlaps_vertically(box1, box2, threshold=0.5):
    """Vérifie si deux boxes se chevauchent verticalement"""
    y1_min, y1_max = box1[1], box1[3]
    y2_min, y2_max = box2[1], box2[3]
    
    overlap = min(y1_max, y2_max) - max(y1_min, y2_min)
    if overlap <= 0:
        return False
    
    height1 = y1_max - y1_min
    height2 = y2_max - y2_min
    
    return overlap / min(height1, height2) > threshold


def is_box_above(box1, box2):
    """Vérifie si box1 est au-dessus de box2"""
    center1_y = (box1[1] + box1[3]) / 2
    center2_y = (box2[1] + box2[3]) / 2
    return center1_y < center2_y


# =============================================================================
# RÈGLES DE POST-TRAITEMENT
# =============================================================================

def apply_postprocessing_rules(detections):
    """
    Applique les règles métier pour corriger les confusions
    
    detections: liste de dict avec 'class', 'conf', 'box' (x1, y1, x2, y2)
    """
    
    corrected = []
    
    # Organiser par classe
    by_class = {}
    for det in detections:
        cls = det['class']
        if cls not in by_class:
            by_class[cls] = []
        by_class[cls].append(det)
    
    # RÈGLE 1: CLIENT vs EMPLOYÉ
    # Si une personne (client ou employé) est très proche d'un produit → client
    
    clients = by_class.get(10, [])  # ID 10 = client
    employes = by_class.get(11, []) + by_class.get(12, []) + by_class.get(13, [])  # employé, actif, inactif
    produits = by_class.get(17, [])  # ID 17 = produit
    
    for person in employes:
        is_client = False
        
        for produit in produits:
            dist = calculate_distance(person['box'], produit['box'])
            
            # Si personne à moins de 100px d'un produit → probablement client
            if dist < 100:
                is_client = True
                break
        
        if is_client:
            # Convertir employé en client
            person['class'] = 10  # ID 10 = client
            person['class_name'] = 'client'
            print(f"   ✓ Correction: employé → client (proche produit)")
    
    # RÈGLE 2: TABLES vs TABLES_VIDES
    # Si une table a un produit ou un client au-dessus → tables (occupée)
    
    tables = by_class.get(18, [])  # ID 18 = tables
    tables_vides = by_class.get(19, [])  # ID 19 = tables_vides
    
    for table_vide in tables_vides:
        is_occupied = False
        
        # Vérifier si un produit est au-dessus
        for produit in produits:
            if is_box_above(produit['box'], table_vide['box']):
                if box_overlaps_vertically(produit['box'], table_vide['box']):
                    is_occupied = True
                    break
        
        # Vérifier si un client est proche
        if not is_occupied:
            for client in clients:
                dist = calculate_distance(client['box'], table_vide['box'])
                if dist < 120:
                    is_occupied = True
                    break
        
        if is_occupied:
            # Convertir table_vide en table occupée
            table_vide['class'] = 18  # ID 18 = tables
            table_vide['class_name'] = 'tables'
            print(f"   ✓ Correction: tables_vides → tables (produit/client détecté)")
    
    # RÈGLE 3: MACHINE vs MACHINE_ARRÊTÉE
    # (Nécessite tracking entre frames - simplifié ici avec seuil de confiance)
    
    machines_arretees = by_class.get(15, [])  # ID 15 = machine_arrêtée
    
    for machine in machines_arretees:
        # Si confiance faible sur machine_arrêtée, convertir en machine normale
        if machine['conf'] < 0.50:
            machine['class'] = 14  # ID 14 = machine
            machine['class_name'] = 'machine'
            print(f"   ✓ Correction: machine_arrêtée → machine (confiance faible)")
    
    # RÈGLE 4: EMPLOYÉ_INACTIF
    # Si confiance faible, convertir en employé générique
    
    employes_inactifs = by_class.get(13, [])  # ID 13 = employé_inactif
    
    for emp_inactif in employes_inactifs:
        if emp_inactif['conf'] < 0.45:
            emp_inactif['class'] = 11  # ID 11 = employé
            emp_inactif['class_name'] = 'employé'
            print(f"   ✓ Correction: employé_inactif → employé (confiance faible)")
    
    # Collecter toutes les détections
    for cls_detections in by_class.values():
        corrected.extend(cls_detections)
    
    return corrected


# =============================================================================
# FONCTION DE TEST
# =============================================================================

def test_with_postprocessing():
    """Teste le modèle avec post-traitement"""
    
    print("\n" + "="*70)
    print("🎬 TEST AVEC POST-TRAITEMENT INTELLIGENT")
    print("="*70 + "\n")
    
    # Vérifier les fichiers
    if not os.path.exists(MODEL_PATH):
        print(f"❌ Modèle introuvable: {MODEL_PATH}")
        return
    
    if not os.path.exists(VIDEO_PATH):
        print(f"❌ Vidéo introuvable: {VIDEO_PATH}")
        return
    
    print(f"✅ Modèle: {MODEL_PATH}")
    print(f"✅ Vidéo: {VIDEO_PATH}\n")
    
    # Charger le modèle
    print("📦 Chargement du modèle...")
    model = YOLO(MODEL_PATH)
    print("✅ Modèle chargé\n")
    
    # Ouvrir la vidéo
    cap = cv2.VideoCapture(VIDEO_PATH)
    
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"📊 Vidéo: {width}x{height} @ {fps} FPS ({total_frames} frames)\n")
    
    # Préparer la sortie
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_video_path = os.path.join(OUTPUT_DIR, "output_postprocessed.mp4")
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))
    
    # Traiter frame par frame
    print("🔄 Traitement en cours...\n")
    
    frame_count = 0
    total_corrections = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        
        # Inférence
        results = model.predict(frame, conf=0.25, verbose=False)[0]
        
        # Convertir en format pour post-traitement
        detections = []
        for box in results.boxes:
            cls = int(box.cls)
            conf = float(box.conf)
            xyxy = box.xyxy[0].cpu().numpy()
            
            # Appliquer seuil de confiance personnalisé
            min_conf = CLASS_CONFIDENCE_THRESHOLDS.get(cls, 0.25)
            if conf < min_conf:
                continue
            
            detections.append({
                'class': cls,
                'class_name': CLASS_NAMES.get(cls, f"class_{cls}"),
                'conf': conf,
                'box': xyxy
            })
        
        # Appliquer post-traitement
        if frame_count % 30 == 0:  # Afficher tous les 30 frames
            print(f"Frame {frame_count}/{total_frames}")
        
        corrected_detections = apply_postprocessing_rules(detections)
        
        # Dessiner les détections corrigées
        for det in corrected_detections:
            x1, y1, x2, y2 = map(int, det['box'])
            cls_name = det['class_name']
            conf = det['conf']
            
            # Couleur selon la classe
            if 'client' in cls_name:
                color = (0, 255, 0)  # Vert
            elif 'employé' in cls_name:
                color = (255, 0, 0)  # Bleu
            elif 'machine' in cls_name:
                color = (0, 0, 255)  # Rouge
            elif 'table' in cls_name:
                color = (255, 255, 0)  # Cyan
            else:
                color = (255, 255, 255)  # Blanc
            
            # Dessiner bbox
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            # Label
            label = f"{cls_name} {conf:.2f}"
            cv2.putText(frame, label, (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # Sauvegarder frame
        out.write(frame)
    
    # Nettoyer
    cap.release()
    out.release()
    
    print("\n" + "="*70)
    print("✅ TRAITEMENT TERMINÉ")
    print("="*70)
    print(f"\n📊 Statistiques:")
    print(f"   Frames traitées: {frame_count}")
    print(f"\n📁 Vidéo sauvegardée:")
    print(f"   {output_video_path}")
    print(f"\n💡 Pour voir:")
    print(f"   start {output_video_path}")
    print("="*70 + "\n")


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    test_with_postprocessing()