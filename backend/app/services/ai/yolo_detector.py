#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Détecteur YOLO - 2 modèles séparés avec comptage stable (Médiane)
Modèle 1: Détection visages employés (best_person.pt)
Modèle 2: Détection objets café (best_objects.pt)
"""

from ultralytics import YOLO
import cv2
import numpy as np
from typing import List, Dict, Optional, Literal
from pathlib import Path
import logging

from app.models.detection import Detection, BoundingBox
from app.core.config import settings

logger = logging.getLogger(__name__)


class YOLODetector:
    """
    Détecteur YOLO avec 2 modèles séparés et comptage robuste
    """
    
    def __init__(self):
        """Initialiser les 2 modèles YOLO"""
        
        # Chemins des modèles
        self.model_employees_path = Path(settings.MODEL_EMPLOYEES_PATH)
        self.model_general_path = Path(settings.MODEL_GENERAL_PATH)
        
        # Charger les modèles
        self.model_employees = None
        self.model_general = None
        self._load_models()
        
        # Définir les couleurs
        self.colors = {
            # ===== MODÈLE EMPLOYÉS (best_person.pt) =====
            "Adem": (255, 0, 0), "Alena": (255, 0, 0), "Ali": (255, 0, 0),
            "Amelie": (255, 0, 0), "Amir": (255, 0, 0), "Ibtihel": (255, 0, 0),
            "Insaf": (255, 0, 0), "Mohamed": (255, 0, 0), "Sami": (255, 0, 0),
            "Seline": (255, 0, 0),
            "employe": (0, 140, 255),
            "temp": (0, 0, 255),
            "porte_verte": (0, 255, 0),
            
            # ===== MODÈLE OBJETS (best_objects.pt) =====
            "Benign": (100, 100, 100), "Malignant": (100, 100, 100), "Normal": (100, 100, 100),
            "client": (255, 165, 0),
            "employé": (0, 200, 255),
            "employé actif": (0, 255, 0),
            "employé inactif": (128, 128, 128),
            "machine": (255, 255, 0),
            "machine arrêtée": (0, 0, 200),
            "produit": (255, 0, 255),
            "tables": (200, 200, 0),
            "tables_vides": (150, 150, 150),
            "default": (255, 255, 255)
        }
    
    def _load_models(self):
        """Charger les 2 modèles YOLO"""
        try:
            if self.model_employees_path.exists():
                logger.info(f"📦 Chargement modèle employés : {self.model_employees_path}")
                self.model_employees = YOLO(str(self.model_employees_path))
                logger.info(f"✅ Modèle employés chargé")
            else:
                logger.warning(f"⚠️ Modèle employés introuvable")
            
            if self.model_general_path.exists():
                logger.info(f"📦 Chargement modèle objets : {self.model_general_path}")
                self.model_general = YOLO(str(self.model_general_path))
                logger.info(f"✅ Modèle objets chargé")
            else:
                logger.warning(f"⚠️ Modèle objets introuvable")
        except Exception as e:
            logger.error(f"❌ Erreur chargement modèles : {e}")
            raise
    
    def detect_frame(
        self, 
        frame: np.ndarray, 
        conf: float = 0.5,
        iou: float = 0.45,
        model_type: Optional[Literal["employees", "objects", "both"]] = "both"
    ) -> List[Detection]:
        """Détecter dans une frame avec choix du modèle"""
        all_detections = []
        
        if model_type in ["employees", "both"] and self.model_employees:
            employees_detections = self._detect_with_model(
                frame, self.model_employees, source="employees", conf=conf, iou=iou
            )
            all_detections.extend(employees_detections)
        
        if model_type in ["objects", "both"] and self.model_general:
            general_detections = self._detect_with_model(
                frame, self.model_general, source="general", conf=conf, iou=iou
            )
            all_detections.extend(general_detections)
        
        return all_detections
    
    def _detect_with_model(
        self,
        frame: np.ndarray,
        model: YOLO,
        source: str,
        conf: float,
        iou: float
    ) -> List[Detection]:
        """Détecter avec un modèle spécifique"""
        detections = []
        IGNORED_CLASSES = ["Benign", "Malignant", "Normal"]
        
        try:
            results = model(frame, conf=conf, iou=iou, verbose=False)
            h, w = frame.shape[:2]
            
            for result in results:
                if result.boxes is None:
                    continue
                    
                for box in result.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    confidence = float(box.conf[0])
                    cls_id = int(box.cls[0])
                    class_name = model.names[cls_id]
                    
                    if class_name in IGNORED_CLASSES:
                        continue
                    
                    bbox = BoundingBox(
                        x=float(x1 / w),
                        y=float(y1 / h),
                        width=float((x2 - x1) / w),
                        height=float((y2 - y1) / h)
                    )
                    
                    detection = Detection(
                        class_name=class_name,
                        confidence=confidence,
                        bbox=bbox,
                        source=source
                    )
                    detections.append(detection)
        except Exception as e:
            logger.error(f"❌ Erreur détection ({source}) : {e}")
        
        return detections

    def count_unique_objects_stable(self, all_detections: List[List[Detection]]) -> Dict[str, int]:
        """
        Calcule le nombre d'objets uniques en utilisant la MÉDIANE sur toutes les frames.
        Cela élimine les pics temporaires et donne une valeur représentative de la présence réelle.
        """
        if not all_detections:
            return {}

        # 1. Historique des comptes par classe pour chaque frame
        class_counts_history: Dict[str, List[int]] = {}

        for frame_detections in all_detections:
            current_frame_counts: Dict[str, int] = {}
            
            for detection in frame_detections:
                cls_name = detection.class_name
                if cls_name in ["Benign", "Malignant", "Normal"]:
                    continue
                current_frame_counts[cls_name] = current_frame_counts.get(cls_name, 0) + 1
            
            for cls_name, count in current_frame_counts.items():
                if cls_name not in class_counts_history:
                    class_counts_history[cls_name] = []
                class_counts_history[cls_name].append(count)

        # 2. Calculer la médiane pour chaque classe
        final_counts: Dict[str, int] = {}
        
        for cls_name, counts_list in class_counts_history.items():
            if not counts_list:
                continue
            
            median_count = int(np.median(counts_list))
            
            if median_count > 0:
                final_counts[cls_name] = median_count

        return final_counts
    
    def get_color(self, class_name: str) -> tuple:
        """Obtenir la couleur pour une classe"""
        return self.colors.get(class_name, self.colors["default"])
    
    def get_detection_stats(self, detections: List[Detection]) -> Dict:
        """Obtenir les statistiques des détections pour une frame unique"""
        stats = {
            "total": len(detections),
            "employees": {"permanent": 0, "temp": 0, "unidentified": 0},
            "objects": 0,
            "by_class": {}
        }
        
        permanent_employees = ["Adem", "Alena", "Ali", "Amelie", "Amir", 
                              "Ibtihel", "Insaf", "Mohamed", "Sami", "Seline"]
        
        for det in detections:
            class_name = det.class_name
            stats["by_class"][class_name] = stats["by_class"].get(class_name, 0) + 1
            
            if det.source == "employees":
                if class_name in permanent_employees:
                    stats["employees"]["permanent"] += 1
                elif class_name == "temp":
                    stats["employees"]["temp"] += 1
                elif class_name == "employe":
                    stats["employees"]["unidentified"] += 1
            elif det.source == "general":
                stats["objects"] += 1
        
        return stats