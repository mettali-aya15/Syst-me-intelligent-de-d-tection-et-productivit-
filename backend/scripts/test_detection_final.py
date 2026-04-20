import cv2
from ultralytics import YOLO
from pathlib import Path
import sys
import time

# 🔧 CONFIGURATION DES CHEMINS ABSOLUS
# Chemin exact du modèle entraîné (basé sur votre log d'entraînement)
MODEL_PATH = Path(r"C:\Users\eyama\OneDrive\Bureau\camIA-factory\yolo_fin\cleaned_dataset\runs\detect\runs\train\camia_factory_v1\weights\best.pt")

# Chemin de la vidéo à tester
VIDEO_PATH = Path(r"C:\Users\eyama\OneDrive\Bureau\camIA-factory\backend\data\videos\barista_vlog.mp4")

# Chemin de sortie pour la vidéo résultat
OUTPUT_PATH = VIDEO_PATH.parent / f"resultat_final_{time.strftime('%Y%m%d_%H%M%S')}.mp4"

# ⚙️ PARAMÈTRES DE PRÉCISION (Crucial pour éviter les doublons)
CONFIDENCE_THRESHOLD = 0.50  # Seuil minimum de confiance (augmente pour moins de faux positifs)
IOU_THRESHOLD = 0.45         # Seuil de chevauchement (baisse pour fusionner les boîtes doubles)

def main():
    print("--- DIAGNOSTIC INITIAL ---")
    
    # 1. Vérification des fichiers
    if not MODEL_PATH.exists():
        print(f"❌ ERREUR CRITIQUE: Modèle introuvable à :\n{MODEL_PATH}")
        print("Vérifiez que l'entraînement s'est bien terminé.")
        return
        
    if not VIDEO_PATH.exists():
        print(f"❌ ERREUR: Vidéo introuvable à :\n{VIDEO_PATH}")
        return
    
    print(f"✅ Modèle chargé: {MODEL_PATH.name}")
    print(f"✅ Vidéo cible: {VIDEO_PATH.name}")

    # 2. Chargement du modèle
    try:
        model = YOLO(str(MODEL_PATH))
        print(f"📊 Classes disponibles: {list(model.names.values())}")
    except Exception as e:
        print(f"❌ Erreur lors du chargement du modèle: {e}")
        return

    # 3. Préparation de la vidéo
    cap = cv2.VideoCapture(str(VIDEO_PATH))
    if not cap.isOpened():
        print("❌ Impossible d'ouvrir la vidéo.")
        return

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Configuration de l'enregistrement
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(OUTPUT_PATH), fourcc, fps, (width, height))

    print(f"\n🚀 Démarrage de l'inférence précise...")
    print(f"   Paramètres: Conf={CONFIDENCE_THRESHOLD}, IoU={IOU_THRESHOLD}")
    print(f"   Appuyez sur 'q' pour quitter prématurément.\n")

    frame_count = 0
    start_time = time.time()

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        
        # Affichage de la progression toutes les 50 frames
        if frame_count % 50 == 0:
            elapsed = time.time() - start_time
            fps_real = frame_count / elapsed if elapsed > 0 else 0
            print(f"   Progression: {frame_count}/{total_frames} frames ({fps_real:.1f} FPS réel)")

        # INFÉRENCE YOLO OPTIMISÉE
        # verbose=False pour ne pas encombrer la console
        results = model.predict(
            source=frame, 
            conf=CONFIDENCE_THRESHOLD, 
            iou=IOU_THRESHOLD,
            imgsz=640, 
            verbose=False,
            device='cpu' # Force l'utilisation du CPU si pas de GPU détecté
        )
        
        # Génération de l'image annotée (boîtes + labels)
        annotated_frame = results[0].plot()
        
        # Sauvegarde dans la vidéo de sortie
        out.write(annotated_frame)
        
        # Affichage temps réel (redimensionné pour tenir à l'écran)
        display_h = 720
        display_w = int(width * (display_h / height))
        resized_display = cv2.resize(annotated_frame, (display_w, display_h))
        
        cv2.imshow("CamIA Detection Finale", resized_display)

        # Touche 'q' pour quitter
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("\n⏹️ Arrêt demandé par l'utilisateur.")
            break

    # Nettoyage final
    cap.release()
    out.release()
    cv2.destroyAllWindows()
    
    total_time = time.time() - start_time
    print(f"\n✅ Terminé !")
    print(f"⏱️ Temps total: {total_time:.2f}s")
    print(f"💾 Vidéo sauvegardée sous : {OUTPUT_PATH}")

if __name__ == "__main__":
    main()