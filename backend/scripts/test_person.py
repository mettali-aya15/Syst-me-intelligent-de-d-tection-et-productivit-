#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST MODÈLE 13 CLASSES - CAMIA-Factory
temp ET employe SÉPARÉS
"""

from ultralytics import YOLO
import cv2
from pathlib import Path
import time
from datetime import datetime

# Configuration - 13 CLASSES
CLASSES = {
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
    10: "employe",       # SÉPARÉ
    11: "porte_verte",
    12: "temp"           # SÉPARÉ
}

# Chemins
MODEL_PATH = r"C:\Users\eyama\OneDrive\Bureau\camIA-factory\yolo\detectionEmploye_clean_v2\runs\detect\runs\detect\employee_faces_v2\weights\best.pt"
VIDEO_PATH = r"C:\Users\eyama\OneDrive\Bureau\camIA-factory\backend\data\videos\temp_d'aarivée.mp4"
OUTPUT_DIR = r"C:\Users\eyama\OneDrive\Bureau\camIA-factory\backend\data\results"

def test_13_classes():
    """Test du modèle 13 classes"""
    
    print("\n" + "=" * 80)
    print("TEST MODÈLE 13 CLASSES (temp ET employe SÉPARÉS)")
    print("=" * 80)
    print(f"\n📊 RÉSULTATS FINAUX:")
    print(f"   mAP@0.5    : 0.924 (EXCELLENT ✅)")
    print(f"   mAP@0.5-95 : 0.705")
    print(f"   Precision  : 0.827")
    print(f"   Recall     : 0.895")
    print()
    
    # Vérifier modèle
    if not Path(MODEL_PATH).exists():
        print(f"❌ Modèle introuvable: {MODEL_PATH}")
        return
    
    # Vérifier vidéo
    if not Path(VIDEO_PATH).exists():
        print(f"❌ Vidéo introuvable: {VIDEO_PATH}")
        return
    
    # Créer output
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    
    print(f"📦 Chargement modèle...")
    model = YOLO(MODEL_PATH)
    
    # Ouvrir vidéo
    cap = cv2.VideoCapture(VIDEO_PATH)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"\n📹 Vidéo: {width}x{height} @ {fps}fps ({total_frames} frames)")
    
    # Préparer sortie
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_video = Path(OUTPUT_DIR) / f"test_13classes_{timestamp}.mp4"
    output_log = Path(OUTPUT_DIR) / f"log_13classes_{timestamp}.txt"
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(output_video), fourcc, fps, (width, height))
    
    # Stats
    stats = {
        'total_detections': 0,
        'temp_count': 0,
        'employe_count': 0,
        'permanent_count': 0,
        'detections_par_classe': {name: 0 for name in CLASSES.values()}
    }
    
    frame_count = 0
    temps_total = 0
    
    print(f"\n🎬 TRAITEMENT...")
    print(f"   🔴 Rouge = temp | 🟠 Orange = employe | 🔵 Bleu = permanents")
    print()
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Inférence
        start = time.time()
        results = model(frame, conf=0.5, verbose=False)
        temps_total += (time.time() - start) * 1000
        
        # Traiter détections
        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = float(box.conf[0])
                cls = int(box.cls[0])
                nom = CLASSES[cls]
                
                stats['total_detections'] += 1
                stats['detections_par_classe'][nom] += 1
                
                # Couleur selon classe
                if cls == 12:  # temp
                    stats['temp_count'] += 1
                    couleur = (0, 0, 255)  # Rouge
                elif cls == 10:  # employe
                    stats['employe_count'] += 1
                    couleur = (0, 140, 255)  # Orange
                elif cls == 11:  # porte
                    couleur = (0, 255, 0)  # Vert
                else:  # Permanent
                    stats['permanent_count'] += 1
                    couleur = (255, 0, 0)  # Bleu
                
                # Dessiner
                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), couleur, 2)
                
                label = f"{nom} {conf:.2f}"
                cv2.rectangle(frame, (int(x1), int(y1)-25), (int(x1)+len(label)*10, int(y1)), couleur, -1)
                cv2.putText(frame, label, (int(x1), int(y1)-5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)
        
        # Info frame
        cv2.putText(frame, f"Frame: {frame_count}/{total_frames}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
        cv2.putText(frame, f"TEMP:{stats['temp_count']} | EMP:{stats['employe_count']} | PERM:{stats['permanent_count']}", 
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,255), 2)
        
        out.write(frame)
        cv2.imshow('Test 13 Classes', frame)
        
        if frame_count % 30 == 0:
            print(f"   Frame {frame_count}/{total_frames} | TEMP:{stats['temp_count']} EMP:{stats['employe_count']}")
        
        frame_count += 1
        
        if cv2.waitKey(1) & 0xFF == 27:
            break
    
    cap.release()
    out.release()
    cv2.destroyAllWindows()
    
    # Résultats
    fps_moy = frame_count / (temps_total / 1000) if temps_total > 0 else 0
    
    print(f"\n" + "=" * 80)
    print("✅ TEST TERMINÉ")
    print("=" * 80)
    
    print(f"\n📊 STATISTIQUES:")
    print(f"   Frames: {frame_count}/{total_frames}")
    print(f"   FPS moyen: {fps_moy:.1f}")
    print(f"   Détections totales: {stats['total_detections']}")
    
    print(f"\n🔍 DISTINCTION temp vs employe:")
    print(f"   TEMP (classe 12)    : {stats['temp_count']:>4} détections")
    print(f"   EMPLOYE (classe 10) : {stats['employe_count']:>4} détections")
    print(f"   PERMANENTS (0-9)    : {stats['permanent_count']:>4} détections")
    
    print(f"\n📋 DÉTAIL PAR CLASSE:")
    print("-" * 80)
    for nom, count in sorted(stats['detections_par_classe'].items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            print(f"   {nom:<15} : {count:>5} détections")
    
    print(f"\n💾 FICHIERS:")
    print(f"   📹 {output_video}")
    print(f"   📄 {output_log}")
    
    # Log
    with open(output_log, 'w', encoding='utf-8') as f:
        f.write("TEST MODÈLE 13 CLASSES - CAMIA-FACTORY\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Date: {datetime.now()}\n")
        f.write(f"Modèle: {MODEL_PATH}\n")
        f.write(f"Vidéo: {VIDEO_PATH}\n\n")
        f.write(f"PERFORMANCES MODÈLE:\n")
        f.write(f"  mAP@0.5    : 0.924\n")
        f.write(f"  mAP@0.5-95 : 0.705\n")
        f.write(f"  Precision  : 0.827\n")
        f.write(f"  Recall     : 0.895\n\n")
        f.write(f"DÉTECTIONS:\n")
        f.write(f"  TEMP      : {stats['temp_count']}\n")
        f.write(f"  EMPLOYE   : {stats['employe_count']}\n")
        f.write(f"  PERMANENTS: {stats['permanent_count']}\n\n")
        f.write(f"DÉTAIL:\n")
        for nom, count in sorted(stats['detections_par_classe'].items(), key=lambda x: x[1], reverse=True):
            if count > 0:
                f.write(f"  {nom:<15} : {count:>5}\n")
    
    print(f"\n✅ Log sauvegardé")
    print("=" * 80)

if __name__ == "__main__":
    test_13_classes()