#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Processeur de frames vidéo
Analyse vidéo frame par frame avec YOLO et génère vidéo annotée
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional, Callable, Literal
from pathlib import Path

from app.models.detection import FrameDetection, Detection, BoundingBox
from .yolo_detector import YOLODetector

import logging
logger = logging.getLogger(__name__)


class FrameProcessor:
    """
    Processeur de frames vidéo
    Analyse et annote les vidéos avec détection YOLO
    """
    
    def __init__(self):
        """Initialiser le processeur"""
        self.detector = YOLODetector()
    
    def process_video(
        self,
        video_path: str,
        output_path: Optional[str] = None,
        conf: float = 0.5,
        save_annotated: bool = True,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        model_type: Literal["employees", "objects", "both"] = "both"
    ) -> Tuple[List[FrameDetection], dict]:
        """
        Traiter une vidéo complète
        
        Args:
            video_path: Chemin de la vidéo
            output_path: Chemin de sortie pour vidéo annotée
            conf: Seuil de confiance
            save_annotated: Sauvegarder la vidéo annotée
            progress_callback: Fonction de callback pour progression
            model_type: Type de modèle à utiliser
                - "employees": Uniquement détection employés
                - "objects": Uniquement détection objets
                - "both": Les deux modèles (défaut)
        
        Returns:
            (frames_detections, metadata)
        """
        try:
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                raise ValueError(f"Impossible d'ouvrir la vidéo : {video_path}")
            
            # Métadonnées vidéo
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps if fps > 0 else 0
            
            metadata = {
                "fps": fps,
                "width": width,
                "height": height,
                "total_frames": total_frames,
                "duration": duration,
                "model_type": model_type
            }
            
            # Préparer le writer si nécessaire
            writer = None
            if save_annotated and output_path:
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            frames_detections = []
            frame_number = 0
            
            logger.info(f"🎥 Traitement vidéo : {total_frames} frames (modèle: {model_type})")
            
            while True:
                ret, frame = cap.read()
                
                if not ret:
                    break
                
                # Détecter dans la frame avec le modèle choisi
                timestamp = frame_number / fps if fps > 0 else 0
                detections = self.detector.detect_frame(
                    frame, 
                    conf=conf,
                    model_type=model_type
                )
                
                # Enregistrer les détections
                frame_detection = FrameDetection(
                    frame_number=frame_number,
                    timestamp=timestamp,
                    detections=detections
                )
                frames_detections.append(frame_detection)
                
                # Dessiner les détections si vidéo annotée
                if save_annotated and writer:
                    annotated_frame = self.draw_detections(frame, detections)
                    writer.write(annotated_frame)
                
                # Callback de progression
                if progress_callback:
                    progress_callback(frame_number, total_frames)
                
                frame_number += 1
            
            # Libérer les ressources
            cap.release()
            if writer:
                writer.release()
            
            logger.info(f"✅ Traitement terminé : {frame_number} frames analysées")
            
            return frames_detections, metadata
        
        except Exception as e:
            logger.error(f"❌ Erreur traitement vidéo : {e}")
            raise
    
    def draw_detections(self, frame: np.ndarray, detections: List[Detection]) -> np.ndarray:
        """
        Dessiner les détections sur une frame
        
        Args:
            frame: Frame OpenCV
            detections: Liste des détections
        
        Returns:
            Frame annotée
        """
        annotated = frame.copy()
        h, w = frame.shape[:2]
        
        # Compter par classe
        class_counts = {}
        for det in detections:
            class_counts[det.class_name] = class_counts.get(det.class_name, 0) + 1
        
        # Dessiner chaque détection
        for det in detections:
            # Convertir bbox normalisé en pixels
            x1 = int(det.bbox.x * w)
            y1 = int(det.bbox.y * h)
            w_box = int(det.bbox.width * w)
            h_box = int(det.bbox.height * h)
            x2 = x1 + w_box
            y2 = y1 + h_box
            
            # Couleur selon la source
            color = self.detector.get_color(det.class_name)
            
            # Dessiner rectangle
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            
            # Label
            label = f"{det.class_name} {det.confidence:.2f}"
            
            # Background pour le texte
            (label_w, label_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(annotated, (x1, y1 - label_h - 10), (x1 + label_w, y1), color, -1)
            cv2.putText(annotated, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Afficher les compteurs en haut
        y_offset = 30
        for class_name, count in sorted(class_counts.items()):
            color = self.detector.get_color(class_name)
            text = f"{class_name}: {count}"
            cv2.putText(annotated, text, (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            y_offset += 25
        
        return annotated
    
    @staticmethod
    def extract_frame(video_path: str, frame_number: int) -> Optional[np.ndarray]:
        """
        Extraire une frame spécifique
        
        Args:
            video_path: Chemin de la vidéo
            frame_number: Numéro de la frame
        
        Returns:
            Frame ou None
        """
        try:
            cap = cv2.VideoCapture(video_path)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            ret, frame = cap.read()
            cap.release()
            
            return frame if ret else None
        
        except Exception as e:
            logger.error(f"❌ Erreur extraction frame : {e}")
            return None