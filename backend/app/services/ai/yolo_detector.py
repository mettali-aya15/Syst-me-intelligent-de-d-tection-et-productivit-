#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Détecteur YOLO - Optimisé pour ByteTrack et Normalisation des Coordonnées
"""

from ultralytics import YOLO
import cv2
import numpy as np
from typing import List, Literal, Set
from pathlib import Path

from app.models.detection import Detection, BoundingBox
from app.core.config import settings

import logging
logger = logging.getLogger(__name__)


class YOLODetector:
    """Gestionnaire des modèles YOLO pour employés et objets"""
    
    # Classes à ignorer (ex: contexte médical si non pertinent)
    MEDICAL_CLASSES = {
        'doctor', 'nurse', 'patient', 'wheelchair', 'hospital bed',
        'stethoscope', 'syringe', 'medical mask', 'thermometer',
        'médecin', 'infirmière', 'fauteuil roulant'
    }
    
    # Noms propres d'employés (pour filtrage en mode 'objects' si nécessaire)
    EMPLOYEE_NAMES: Set[str] = {'amir', 'seline', 'ali', 'adem', 'person'} 
    
    def __init__(self):
        logger.info("🔧 Initialisation YOLODetector...")
        
        # Chargement des modèles
        self.employee_model = YOLO(str(settings.EMPLOYEE_MODEL_PATH))
        self.object_model = YOLO(str(settings.OBJECT_MODEL_PATH))
        
        logger.info(f"✅ Modèle employés chargé: {settings.EMPLOYEE_MODEL_PATH}")
        logger.info(f"✅ Modèle objets chargé: {settings.OBJECT_MODEL_PATH}")
        
        # Couleurs pour l'affichage
        self.colors = {
            "employé": (0, 255, 0),
            "machine": (255, 255, 0),
            "produit": (0, 0, 255),
            "default": (128, 128, 128)
        }
    
    def get_employee_model(self):
        return self.employee_model
    
    def get_object_model(self):
        return self.object_model
    
    def detect_frame(
        self,
        frame: np.ndarray,
        conf: float = 0.5, # Lowered to catch occluded parts
        model_type: Literal["employees", "objects", "both"] = "both",
        frame_idx: int = 0
    ) -> List[Detection]:
        """
        Détection avec ByteTrack activé et Coordonnées Normalisées.
        """
        detections = []
        h, w = frame.shape[:2]

        # ✅ LOGIQUE DE DÉTECTION :
        # On lance toujours le modèle employé pour capturer les humains, 
        # même en mode 'objects', car on a besoin de leurs données pour le comptage.
        
        run_employee = True # Always track humans for occupancy counting
        run_object = model_type in ("objects", "both")

        # 1️⃣ Employee Model (Runs for all modes to ensure human detection)
        if run_employee:
            results = self.employee_model.track(
                frame, 
                conf=conf, 
                iou=0.6, 
                verbose=False,
                persist=True,     # ✅ CRUCIAL for ByteTrack memory
                tracker="bytetrack.yaml", 
                max_det=100       # Increased to catch everyone in crowded scenes
            )
            
            for result in results:
                if result.boxes is None: 
                    continue
                
                for box in result.boxes:
                    class_id = int(box.cls[0])
                    class_name = self.employee_model.names[class_id]
                    
                    # Filter medical classes if needed
                    if class_name.lower() in {c.lower() for c in self.MEDICAL_CLASSES}:
                        continue
                        
                    confidence = float(box.conf[0])
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    
                    track_id = None
                    if hasattr(box, 'id') and box.id is not None:
                        try:
                            track_id = int(box.id[0].cpu().item())
                        except Exception:
                            pass
                    
                    # ✅ NORMALIZATION (0.0 to 1.0) for Zone Logic
                    detections.append(Detection(
                        class_name=class_name, 
                        confidence=confidence,
                        bbox=BoundingBox(
                            x=float(x1)/w, 
                            y=float(y1)/h, 
                            width=float(x2-x1)/w, 
                            height=float(y2-y1)/h
                        ),
                        source="employee", 
                        track_id=track_id
                    ))

        # 2️⃣ Object Model (For machines/products, filtering out humans to avoid duplicates)
        if run_object:
            results = self.object_model.track(
                frame, 
                conf=conf, 
                iou=0.6, 
                verbose=False,
                persist=True, 
                tracker="bytetrack.yaml", 
                max_det=100
            )
            
            for result in results:
                if result.boxes is None: 
                    continue
                
                for box in result.boxes:
                    cls_id = int(box.cls[0])
                    cls_raw = self.object_model.names[cls_id]
                    cls_lower = cls_raw.lower()
                    
                    # 🛡️ Skip humans/medical as they are handled by employee_model
                    if cls_lower in self.EMPLOYEE_NAMES or cls_lower in {c.lower() for c in self.MEDICAL_CLASSES}:
                        continue
                        
                    confidence = float(box.conf[0])
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    
                    track_id = None
                    if hasattr(box, 'id') and box.id is not None:
                        try:
                            track_id = int(box.id[0].cpu().item())
                        except Exception:
                            pass
                    
                    detections.append(Detection(
                        class_name=cls_raw, 
                        confidence=confidence,
                        bbox=BoundingBox(
                            x=float(x1)/w, 
                            y=float(y1)/h, 
                            width=float(x2-x1)/w, 
                            height=float(y2-y1)/h
                        ),
                        source="object", 
                        track_id=track_id
                    ))

        return detections
    
    def get_color(self, class_name: str) -> tuple:
        """Retourne la couleur associée à une classe"""
        for key, color in self.colors.items():
            if key in class_name.lower():
                return color
        return self.colors["default"]