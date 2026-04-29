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
    
    # ✅ Classes contextuelles à ignorer (de best_person.pt)
    IGNORED_CLASSES = {
        'porte verte',
        'temps'
    }
    
    # ✅ Noms propres d'employés (de best_person.pt)
    EMPLOYEE_NAMES: Set[str] = {
        'amelie', 'seline', 'ibtihel', 'ali', 'mohamed', 
        'alena', 'adem', 'amir', 'sami', 'insaf', 'employe'
    }
    
    def __init__(self):
        logger.info("🔧 Initialisation YOLODetector...")
        
        # Chargement des modèles
        # best_person.pt → Reconnaissance par NOM (amelie, seline, ali, etc.)
        # best_objects.pt → Détection OBJETS + ÉTATS (produit, machine, employé, employé actif, etc.)
        self.employee_model = YOLO(str(settings.EMPLOYEE_MODEL_PATH))  # best_person.pt
        self.object_model = YOLO(str(settings.OBJECT_MODEL_PATH))      # best_objects.pt
        
        logger.info(f"✅ Modèle employés (noms) chargé: {settings.EMPLOYEE_MODEL_PATH}")
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
        conf: float = 0.5,
        model_type: Literal["employees", "objects", "both"] = "both",
        frame_idx: int = 0
    ) -> List[Detection]:
        """
        Détection avec ByteTrack activé et Coordonnées Normalisées.
        
        LOGIQUE CORRIGÉE:
        - model_type="employees" → Utiliser best_person.pt (noms propres)
        - model_type="objects" → Utiliser best_objects.pt (tout : produit, machine, employé, etc.)
        - model_type="both" → Utiliser les 2 modèles
        """
        detections = []
        h, w = frame.shape[:2]

        # ✅ DÉCISION : Quel modèle utiliser
        run_employee_names = model_type in ("employees", "both")  # best_person.pt
        run_objects = model_type in ("objects", "both")           # best_objects.pt

        # 1️⃣ Employee Names Model (best_person.pt) - Reconnaissance par NOM
        if run_employee_names:
            results = self.employee_model.track(
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
                    class_id = int(box.cls[0])
                    class_name = self.employee_model.names[class_id]
                    
                    # ✅ Filtrer classes contextuelles
                    if class_name.lower() in {c.lower() for c in self.IGNORED_CLASSES}:
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
                        class_name=class_name, 
                        confidence=confidence,
                        bbox=BoundingBox(
                            x=float(x1)/w, 
                            y=float(y1)/h, 
                            width=float(x2-x1)/w, 
                            height=float(y2-y1)/h
                        ),
                        source="employee_name",  # ✅ Source = noms propres
                        track_id=track_id
                    ))

        # 2️⃣ Objects Model (best_objects.pt) - Détection TOUT (produit, machine, employé, etc.)
        if run_objects:
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
                    
                    # ✅ PAS DE FILTRAGE en mode "objects"
                    # On veut TOUT : produit, machine, employé, employé actif, etc.
                    
                    # ✅ FILTRAGE SEULEMENT en mode "both" pour éviter doublons
                    if model_type == "both":
                        # Si on utilise les 2 modèles, ignorer les classes "employé" de best_objects.pt
                        # car elles seront détectées par best_person.pt avec les noms
                        if cls_lower in {'employé', 'employé actif', 'employé inactif'}:
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
                        source="object",  # ✅ Source = best_objects.pt
                        track_id=track_id
                    ))

        return detections
    
    def get_color(self, class_name: str) -> tuple:
        """Retourne la couleur associée à une classe"""
        for key, color in self.colors.items():
            if key in class_name.lower():
                return color
        return self.colors["default"]