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
from collections import defaultdict
from ultralytics import solutions

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
        Traiter une vidéo complète (Méthode standard sans lignes)
        """
        try:
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                raise ValueError(f"Impossible d'ouvrir la vidéo : {video_path}")
            
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
            
            writer = None
            if save_annotated and output_path:
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                fourcc = cv2.VideoWriter_fourcc(*'avc1')
                writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            frames_detections = []
            frame_number = 0
            
            logger.info(f"🎥 Traitement vidéo : {total_frames} frames (modèle: {model_type})")
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                timestamp = frame_number / fps if fps > 0 else 0
                detections = self.detector.detect_frame(
                    frame, 
                    conf=conf,
                    model_type=model_type
                )
                
                frame_detection = FrameDetection(
                    frame_number=frame_number,
                    timestamp=timestamp,
                    detections=detections
                )
                frames_detections.append(frame_detection)
                
                if save_annotated and writer:
                    annotated_frame = self.draw_detections(frame, detections)
                    writer.write(annotated_frame)
                
                if progress_callback:
                    progress_callback(frame_number, total_frames)
                
                frame_number += 1
            
            cap.release()
            if writer:
                writer.release()
            
            logger.info(f"✅ Traitement terminé : {frame_number} frames analysées")
            return frames_detections, metadata
        
        except Exception as e:
            logger.error(f"❌ Erreur traitement vidéo : {e}")
            raise

    def process_video_with_line_counting(
        self,
        video_path: str,
        output_path: str,
        conf: float = 0.5,
        model_type: str = "both",
        progress_callback=None
    ) -> tuple:
        """
        Traiter vidéo avec comptage par ligne - VERSION CORRIGÉE
        
        STRATÉGIE :
        - ObjectCounter pour les produits (si model_type = objects/both)
        - draw_detections pour les employés (si model_type = employees/both)
        - Pas de boxes en double
        """
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError(f"Impossible d'ouvrir la vidéo : {video_path}")
        
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # 10 lignes horizontales pour les produits
        line_positions = {
            f"ligne_{i}": [(0, int(height * (i/10))), (width, int(height * (i/10)))]
            for i in range(1, 11)
        }
        
        fourcc = cv2.VideoWriter_fourcc(*'avc1')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        frames_detections = []
        frame_idx = 0
        
        object_model = self.detector.get_object_model()
        
        # Initialiser compteurs de lignes
        counters = {}
        line_counts = {}
        
        for line_name, line_pts in line_positions.items():
            counters[line_name] = solutions.ObjectCounter(
                show=False,
                region=line_pts,
                line_width=2,
                model=object_model
            )
            line_counts[line_name] = {"IN": 0, "OUT": 0, "TOTAL": 0}
        
        global_product_ids = set()
        
        logger.info("="*70)
        logger.info(f"📏 Comptage optimisé (model_type={model_type})")
        logger.info("="*70)
        
        while cap.isOpened():
            success, frame_original = cap.read()
            if not success:
                break
            
            timestamp = frame_idx / fps
            all_detections = []
            
            # ========== COLLECTE DES DONNÉES (sans affichage) ==========
            general_detections = self.detector.detect_frame(
                frame_original, 
                conf=conf, 
                model_type=model_type,
                frame_idx=frame_idx
            )
            all_detections.extend(general_detections)
            
            # ✅ Sauvegarder TOUTES les détections
            frames_detections.append(
                FrameDetection(
                    frame_number=frame_idx,
                    timestamp=timestamp,
                    detections=all_detections
                )
            )
            
            # ========== AFFICHAGE SELON model_type ==========
            frame_display = frame_original.copy()
            
            # CAS 1 : model_type contient "objects" → Utiliser ObjectCounter
            if model_type in ["objects", "both"]:
                for line_name, counter in counters.items():
                    frame_copy = frame_original.copy()
                    results = counter.process(frame_copy)
                    
                    # Utiliser ligne centrale pour affichage
                    if line_name == "ligne_5":
                        frame_display = results.plot_im
                    
                    # Stats
                    line_counts[line_name]["IN"] = results.in_count
                    line_counts[line_name]["OUT"] = results.out_count
                    line_counts[line_name]["TOTAL"] = results.in_count + results.out_count
                    
                    # IDs uniques
                    if hasattr(counter, 'counted_ids') and counter.counted_ids:
                        global_product_ids.update(counter.counted_ids)
                
                # Si model_type = "both" → Dessiner AUSSI les employés (sans produits)
                if model_type == "both":
                    non_product_detections = [
                        det for det in all_detections 
                        if det.class_name.lower() != 'produit'
                    ]
                    frame_display = self.draw_detections(frame_display, non_product_detections)
            
            # CAS 2 : model_type = "employees" → Dessiner TOUTES les détections
            elif model_type == "employees":
                frame_display = self.draw_detections(frame_display, all_detections)
            
            # Ajouter compteur produits si applicable
            if model_type in ["objects", "both"] and len(global_product_ids) > 0:
                cv2.putText(
                    frame_display, 
                    f"Produits Uniques: {len(global_product_ids)}", 
                    (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    1.0, 
                    (0, 255, 0), 
                    2
                )
            
            out.write(frame_display)
            frame_idx += 1
            
            if progress_callback and frame_idx % 30 == 0:
                progress_callback(frame_idx, total_frames)
        
        cap.release()
        out.release()
        
        # Résultats
        final_counts = {
            "produit": {
                "TOTAL": len(global_product_ids),
                "unique_ids": list(global_product_ids)
            }
        }
        
        metadata = {
            "total_frames": total_frames,
            "fps": fps,
            "width": width,
            "height": height,
            "duration": total_frames / fps,
            "model_type": model_type
        }
        
        logger.info(f"✅ Traitement terminé. Produits uniques: {len(global_product_ids)}")
        
        return frames_detections, metadata, final_counts
    
    def draw_detections(self, frame: np.ndarray, detections: List[Detection]) -> np.ndarray:
        """
        Dessine les boîtes de détection sur la frame
        
        Args:
            frame: Frame source (peut déjà contenir des annotations)
            detections: Liste des détections à dessiner
        
        Returns:
            Frame annotée
        """
        annotated = frame.copy()
        h, w = frame.shape[:2]
        
        for det in detections:
            # Conversion coordonnées normalisées → pixels
            x1 = int(det.bbox.x * w)
            y1 = int(det.bbox.y * h)
            x2 = int((det.bbox.x + det.bbox.width) * w)
            y2 = int((det.bbox.y + det.bbox.height) * h)
            
            # Couleur selon la classe
            color = self.detector.get_color(det.class_name)
            
            # Dessiner le rectangle
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            
            # Label avec ID si disponible
            label = f"{det.class_name}"
            if det.track_id is not None:
                label += f" #{det.track_id}"
            
            # Background pour le texte
            (label_w, label_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(annotated, (x1, y1 - label_h - 10), (x1 + label_w, y1), color, -1)
            cv2.putText(annotated, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return annotated