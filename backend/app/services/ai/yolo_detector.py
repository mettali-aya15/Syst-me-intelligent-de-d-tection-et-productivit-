#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Détecteur YOLO
Charge les modèles et effectue les détections
"""

from ultralytics import YOLO
import cv2
import numpy as np
from typing import List, Literal
from pathlib import Path

from app.models.detection import Detection, BoundingBox
from app.core.config import settings

import logging
logger = logging.getLogger(__name__)


class YOLODetector:
    """Détecteur YOLO pour employés et objets"""
    
    # Classes médicales à filtrer
    MEDICAL_CLASSES = {
        'doctor', 'nurse', 'patient', 'wheelchair', 'hospital bed',
        'stethoscope', 'syringe', 'medical mask', 'thermometer',
        'blood pressure monitor', 'iv stand', 'stretcher', 'crutches',
        'médecin', 'infirmière', 'patient', 'fauteuil roulant',
        'lit hôpital', 'stéthoscope', 'seringue', 'masque médical'
    }
    
    def __init__(self):
        """Initialiser les modèles YOLO"""
        logger.info("🔧 Initialisation YOLODetector...")
        
        # Charger les modèles
        self.employee_model = YOLO(str(settings.EMPLOYEE_MODEL_PATH))
        self.object_model = YOLO(str(settings.OBJECT_MODEL_PATH))
        
        logger.info(f"✅ Modèle employés: {settings.EMPLOYEE_MODEL_PATH}")
        logger.info(f"✅ Modèle objets: {settings.OBJECT_MODEL_PATH}")
        
        # Couleurs pour les classes
        self.colors = {
            "employé": (0, 255, 0),
            "employé actif": (0, 200, 0),
            "employé inactif": (0, 150, 0),
            "client": (255, 0, 0),
            "produit": (0, 0, 255),
            "machine": (255, 255, 0),
            "table": (255, 165, 0),
        }
    
    def get_employee_model(self):
        """Retourner le modèle employé"""
        return self.employee_model
    
    def get_object_model(self):
        """Retourner le modèle objet"""
        return self.object_model
    
    def detect_frame(
        self,
        frame: np.ndarray,
        conf: float = 0.5,
        model_type: Literal["employees", "objects", "both"] = "both"
    ) -> List[Detection]:
        """
        Détecter objets dans une frame
        
        Args:
            frame: Frame OpenCV (BGR)
            conf: Seuil de confiance
            model_type: Type de modèle
        
        Returns:
            Liste de détections
        """
        detections = []
        
        # Détection employés
        if model_type in ["employees", "both"]:
            results_emp = self.employee_model(frame, conf=conf, verbose=False)
            detections.extend(self._parse_results(results_emp, "employee"))
        
        # Détection objets
        if model_type in ["objects", "both"]:
            results_obj = self.object_model(frame, conf=conf, verbose=False)
            detections.extend(self._parse_results(results_obj, "object"))
        
        return detections
    
    def _parse_results(self, results, source: str) -> List[Detection]:
        """Parser les résultats YOLO"""
        detections = []
        
        if not results or len(results) == 0:
            return detections
        
        result = results[0]
        
        if result.boxes is None or len(result.boxes) == 0:
            return detections
        
        for box in result.boxes:
            cls_id = int(box.cls[0])
            class_name = result.names[cls_id]
            
            # Filtrer classes médicales
            if self._is_medical_class(class_name):
                continue
            
            confidence = float(box.conf[0])
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            
            detection = Detection(
                class_name=class_name,
                confidence=confidence,
                bbox=BoundingBox(
                    x=float(x1),
                    y=float(y1),
                    width=float(x2 - x1),
                    height=float(y2 - y1)
                ),
                source=source
            )
            detections.append(detection)
        
        return detections
    
    def _is_medical_class(self, class_name: str) -> bool:
        """Vérifier si c'est une classe médicale"""
        return class_name.lower() in self.MEDICAL_CLASSES
    
    def get_color(self, class_name: str) -> tuple:
        """Obtenir couleur pour une classe"""
        for key, color in self.colors.items():
            if key in class_name.lower():
                return color
        return (128, 128, 128)