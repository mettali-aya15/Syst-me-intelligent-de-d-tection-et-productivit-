import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import cv2
from datetime import datetime
from ultralytics import YOLO
from app.core.logger import get_logger

logger = get_logger("VIDEO_TEST")

# ✅ VIDÉO ADAPTÉE (usine textile)
VIDEO_PATH = "data/videos/factory.mp4"

def run_video_test():
    # ✅ CHARGER YOLOv8 DIRECTEMENT
    logger.info("📥 Chargement YOLOv8n...")
    model = YOLO("yolov8n.pt")
    logger.info("✅ YOLOv8 prêt")
    
    # ✅ OUVIR LA VIDÉO
    cap = cv2.VideoCapture(VIDEO_PATH)
    if not cap.isOpened():
        raise RuntimeError(f"❌ Impossible d'ouvrir la vidéo: {VIDEO_PATH}")
    
    # ✅ OBTENIR LE FPS RÉEL DE LA VIDÉO
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    logger.info(f"📹 Vidéo: {total_frames} frames @ {fps:.1f} FPS")
    
    # ✅ INITIALISER LES COMPTEURS
    frame_count = 0
    detected_employees = set()  # Utilise un set pour éviter les doublons
    detected_workstations = set()   # Utilise un set pour éviter les doublons
    working_time = 0
    idle_time = 0
    
    start_time = datetime.utcnow()
    logger.info("🎬 Début de l'analyse vidéo...")
    print("=" * 60)
    
    # ✅ BOUCLE DE TRAITEMENT
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        
        # ✅ TRAITER 1 FRAME SUR 5 POUR PERFORMANCE
        if frame_count % 5 != 0:
            continue
        
        # ✅ DÉTECTION AVEC SUIVI D'OBJETS (CORRIGÉ)
        results = model.track(frame, persist=True, classes=[0], conf=0.3)
        
        # ✅ COMPTER LES DÉTECTIONS UNIQUES (CORRIGÉ)
        current_employees = set()
        current_workstations = set()
        
        for box in results[0].boxes:
            cls_id = int(box.cls[0])
            track_id = int(box.id[0]) if box.id is not None else None
            
            if track_id is not None:
                # ✅ FILTRAGE DES DÉTECTIONS DE PERSONNES (OPTIMISÉ POUR LES USINES)
                if cls_id == 0:  # Personne = employé
                    # ✅ VÉRIFICATION DE LA HAUTEUR (filtrage des faux positifs)
                    height = box.xyxy[0][3] - box.xyxy[0][1]
                    width = box.xyxy[0][2] - box.xyxy[0][0]
                    
                    # ✅ CRITÈRES POUR LES USINES
                    # - Hauteur minimale : 20% de la hauteur de l'image
                    # - Ratio hauteur/largeur : entre 1.5 et 3.0 (personnes verticales)
                    if (height > frame.shape[0] * 0.20 and 
                        width > 0 and
                        1.5 < height / width < 3.0):
                        current_employees.add(track_id)
        
        # Ajoute les objets détectés à la liste globale
        detected_employees.update(current_employees)
        detected_workstations.update(current_workstations)
        
        # ✅ CALCULER LE TEMPS DE TRAVAIL
        if len(current_employees) > 0 and len(current_workstations) > 0:
            working_time += 1
        else:
            idle_time += 1
        
        # ✅ AFFICHAGE EN TEMPS RÉEL
        if frame_count % 30 == 0:
            progress = (frame_count / total_frames) * 100
            print(f"⏳ {progress:>5.1f}% | Frames: {frame_count}/{total_frames} | "
                  f"Employés: {len(current_employees)} | Workstations: {len(current_workstations)} | "
                  f"Travail: {working_time} frames | Inactif: {idle_time} frames")
    
    cap.release()
    
    # ✅ OBTENIR LE TEMPS DE FIN
    end_time = datetime.utcnow()
    
    # ✅ CALCUL CORRECT DE LA DURÉE ANALYSÉE
    frame_interval = 5  # 1 frame sur 5
    total_frames_processed = working_time + idle_time
    
    # ✅ VÉRIFICATION POUR ÉVITER LES ERREURS
    max_frames = total_frames // frame_interval
    if total_frames_processed > max_frames:
        total_frames_processed = max_frames
    
    analyzed_seconds = (total_frames_processed * frame_interval) / fps
    
    # ✅ CALCUL DES KPI
    if analyzed_seconds > 0:
        productivity = (working_time / total_frames_processed) * 100
        workstation_utilization = (len(detected_workstations) / max(len(detected_employees), 1)) * 100
    else:
        productivity = 0.0
        workstation_utilization = 0.0
    
    # ✅ AFFICHAGE DU RAPPORT
    print("\n" + "=" * 60)
    print("📊 RAPPORT KPI FINAL")
    print("=" * 60)
    print(f" Durée analysée: {analyzed_seconds:.1f} secondes")
    print(f"Employés détectés: {len(detected_employees)}")
    print(f"Workstations détectées: {len(detected_workstations)}")
    print(f"Temps de travail: {working_time} frames ({working_time * frame_interval / fps:.1f}s)")
    print(f"Temps inactif: {idle_time} frames ({idle_time * frame_interval / fps:.1f}s)")
    print(f"Productivité: {productivity:.1f}%")
    print(f"Utilisation workstations: {workstation_utilization:.1f}%")
    print("=" * 60)
    
    logger.info("✅ Analyse vidéo terminée avec succès")
    return {
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "analyzed_seconds": analyzed_seconds,
        "working_time": working_time * frame_interval / fps,
        "idle_time": idle_time * frame_interval / fps,
        "productivity": productivity,
        "workstation_utilization": workstation_utilization,
        "detected_employees": len(detected_employees),
        "detected_workstations": len(detected_workstations)
    }

if __name__ == "__main__":
    run_video_test()