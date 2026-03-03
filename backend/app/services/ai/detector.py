import torch
from typing import List, Dict, Any
from app.models.workstation import Workstation

class YOLODetector:
    """
    Détecteur YOLO pour les workstations et les employés
    """
    
    def __init__(self, model_name="yolov5s", device="cpu"):
        self.model = torch.hub.load(
            "ultralytics/yolov5",
            model_name,
            pretrained=True
        )
        self.device = device
        if device == "cuda":
            self.model.cuda()
    
    def detect(self, frame) -> List[Dict]:
        """
        Détecte les objets dans une frame
        Retourne : [{"label": str, "confidence": float, "bbox": [x1,y1,x2,y2]}]
        """
        results = self.model(frame)
        detections = []

        for *box, conf, cls in results.xyxy[0].tolist():
            label = self.model.names[int(cls)]
            detections.append({
                "label": label,
                "confidence": float(conf),
                "bbox": [int(x) for x in box]
            })

        return detections

    def detect_workstations(self, frame, workstation_type: str = None) -> List[Dict]:
        """
        Détecte spécifiquement les workstations
        """
        detections = self.detect(frame)
        workstations = []
        
        for det in detections:
            if det['label'] == workstation_type or workstation_type is None:
                workstations.append(det)
                
        return workstations
    
    def detect_employees(self, frame) -> List[Dict]:
        """
        Détecte spécifiquement les employés
        """
        detections = self.detect(frame)
        return [det for det in detections if det['label'] == 'person']

def is_sitting(person_bbox) -> bool:
    """
    Détection très simple : si bbox hauteur < 60% machine height → assis
    """
    x1, y1, x2, y2 = person_bbox
    height = y2 - y1
    if height < 120:  # seuil arbitraire, calibrer selon caméra
        return True
    return False

def is_absent(person_bbox, workstation_bbox) -> bool:
    """
    Détection très simple : si personne hors bbox workstation → absent
    """
    px1, py1, px2, py2 = person_bbox
    mx1, my1, mx2, my2 = workstation_bbox
    # Vérifier si les bboxes ne se chevauchent pas
    if px2 < mx1 or px1 > mx2 or py2 < my1 or py1 > my2:
        return True
    return False