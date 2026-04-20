import cv2
from ultralytics import YOLO
from pathlib import Path

# Chemins exacts basés sur votre structure
MODEL_PATH = Path(r"C:\Users\eyama\OneDrive\Bureau\camIA-factory\yolo_fin\cleaned_dataset\runs\detect\runs\train\camia_factory_v1\weights\best.pt")
VIDEO_PATH = Path(r"C:\Users\eyama\OneDrive\Bureau\camIA-factory\backend\data\videos\workflow-factory.mp4")
OUTPUT_PATH = VIDEO_PATH.parent / "resultat_iou_005.mp4"

def main():
    if not MODEL_PATH.exists() or not VIDEO_PATH.exists():
        print("❌ Fichiers introuvables.")
        return

    model = YOLO(str(MODEL_PATH))
    cap = cv2.VideoCapture(str(VIDEO_PATH))
    
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(OUTPUT_PATH), fourcc, fps, (width, height))

    print("🚀 Inférence avec IoU=0.45 (Nettoyage des doublons)...")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break

        # C'EST ICI QUE LA CORRECTION S'OPÈRE
        results = model.predict(
            source=frame, 
            conf=0.50, 
            iou=0.45,  # Valeur critique pour supprimer l'effet "traînée"
            verbose=False
        )
        
        annotated_frame = results[0].plot()
        out.write(annotated_frame)
        
        display_h = 720
        display_w = int(width * (display_h / height))
        cv2.imshow("Detection Propre", cv2.resize(annotated_frame, (display_w, display_h)))

        if cv2.waitKey(1) & 0xFF == ord('q'): break

    cap.release()
    out.release()
    cv2.destroyAllWindows()
    print(f"✅ Terminé : {OUTPUT_PATH}")

if __name__ == "__main__":
    main()