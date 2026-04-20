import cv2
from ultralytics import YOLO
from pathlib import Path
import time

# 🔧 CONFIGURATION
VIDEO_PATH = Path(r"C:\Users\eyama\OneDrive\Bureau\camIA-factory\backend\data\videos\barista1.mp4")
MODEL_PATH = Path(r"C:\Users\eyama\OneDrive\Bureau\camIA-factory\yolo_image\project-dection\runs\detect\train\weights\best.pt")
OUTPUT_PATH = VIDEO_PATH.parent / f"output_{VIDEO_PATH.name}"
CONFIDENCE = 0.35  # Seuil de détection
IMG_SIZE = 640     # Taille d'inférence

def main():
    if not VIDEO_PATH.exists():
        print(f"❌ Vidéo introuvable: {VIDEO_PATH}")
        return
    if not MODEL_PATH.exists():
        print(f"❌ Modèle introuvable: {MODEL_PATH}")
        return

    print(f"🎬 Chargement du modèle...")
    model = YOLO(str(MODEL_PATH))
    print(f"✅ Modèle chargé | Classes: {model.names}")

    cap = cv2.VideoCapture(str(VIDEO_PATH))
    if not cap.isOpened():
        print("❌ Impossible d'ouvrir la vidéo")
        return

    # Infos vidéo
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"📊 Vidéo: {width}x{height} @ {fps}fps | {total_frames} frames")

    # Sauvegarde vidéo
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(OUTPUT_PATH), fourcc, fps, (width, height))

    print(f"🚀 Démarrage de l'inférence... (appuyez sur 'q' pour quitter)")
    start_time = time.time()
    frame_count = 0
    detections_log = {}

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        if frame_count % 10 == 0:
            print(f"📍 Frame {frame_count}/{total_frames}")

        # Inférence YOLO
        results = model(frame, conf=CONFIDENCE, imgsz=IMG_SIZE, verbose=False)
        result = results[0]

        # Comptage par classe
        for cls_id in result.boxes.cls.cpu().numpy():
            cls_name = model.names[int(cls_id)]
            detections_log[cls_name] = detections_log.get(cls_name, 0) + 1

        # Dessin des boîtes
        for box in result.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = float(box.conf[0])
            cls_id = int(box.cls[0])
            label = f"{model.names[cls_id]} {conf:.2f}"

            # Couleur par classe (simple hash)
            color = tuple(int(c) for c in [(cls_id * 50) % 255, (cls_id * 100) % 255, (cls_id * 150) % 255])
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        # Infos en overlay
        elapsed = time.time() - start_time
        current_fps = frame_count / elapsed if elapsed > 0 else 0
        cv2.putText(frame, f"FPS: {current_fps:.1f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, f"Frame: {frame_count}/{total_frames}", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # Affichage + sauvegarde
        cv2.imshow("YOLO Detection", frame)
        out.write(frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("⏹️ Arrêt demandé par l'utilisateur")
            break

    # Nettoyage
    cap.release()
    out.release()
    cv2.destroyAllWindows()

    # Résumé
    print(f"\n✅ Terminé ! Vidéo sauvegardée: {OUTPUT_PATH}")
    print(f"📈 Statistiques de détection:")
    for cls, count in sorted(detections_log.items(), key=lambda x: x[1], reverse=True):
        print(f"   • {cls}: {count} détections")

if __name__ == "__main__":
    main()