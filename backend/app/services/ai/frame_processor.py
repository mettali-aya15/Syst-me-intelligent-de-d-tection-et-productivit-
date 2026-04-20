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
        Traiter une vidéo complète
        
        Args:
            video_path: Chemin de la vidéo
            output_path: Chemin de sortie pour vidéo annotée
            conf: Seuil de confiance
            save_annotated: Sauvegarder la vidéo annotée
            progress_callback: Fonction de callback pour progression
            model_type: Type de modèle à utiliser
        
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
                
                # Détecter dans la frame
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
    
    def process_video_with_line_counting(
    self,
    video_path: str,
    output_path: str,
    conf: float = 0.5,
    model_type: str = "both",
    progress_callback=None
) -> tuple:
        """+
        Traiter vidéo avec 10 lignes + DÉDUPLICATION DES IDs
        """
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError(f"Impossible d'ouvrir la vidéo : {video_path}")
        
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # 10 lignes
        line_positions = {
            "ligne_1": [(0, int(height * 0.10)), (width, int(height * 0.10))],
            "ligne_2": [(0, int(height * 0.20)), (width, int(height * 0.20))],
            "ligne_3": [(0, int(height * 0.30)), (width, int(height * 0.30))],
            "ligne_4": [(0, int(height * 0.40)), (width, int(height * 0.40))],
            "ligne_5": [(0, int(height * 0.50)), (width, int(height * 0.50))],
            "ligne_6": [(0, int(height * 0.60)), (width, int(height * 0.60))],
            "ligne_7": [(0, int(height * 0.70)), (width, int(height * 0.70))],
            "ligne_8": [(0, int(height * 0.80)), (width, int(height * 0.80))],
            "ligne_9": [(0, int(height * 0.90)), (width, int(height * 0.90))],
            "ligne_10": [(0, int(height * 0.95)), (width, int(height * 0.95))]
        }
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        frames_detections = []
        frame_idx = 0
        
        object_model = self.detector.get_object_model()
        
        # Initialiser compteurs
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
        
        # 🎯 ENSEMBLE GLOBAL POUR DÉDUPLICATION
        global_counted_ids = set()
        
        logger.info("="*70)
        logger.info(f"📏 Comptage avec DÉDUPLICATION des IDs")
        logger.info("="*70)
        
        while cap.isOpened():
            success, frame_original = cap.read()
            if not success:
                break
            
            frame_detections = []
            timestamp = frame_idx / fps
            
            if model_type in ["objects", "both"]:
                annotated_frames = {}
                
                for line_name, counter in counters.items():
                    frame_copy = frame_original.copy()
                    
                    results = counter.process(frame_copy)
                    
                    annotated_frames[line_name] = results.plot_im
                    
                    # Mise à jour comptages
                    line_counts[line_name]["IN"] = results.in_count
                    line_counts[line_name]["OUT"] = results.out_count
                    line_counts[line_name]["TOTAL"] = results.in_count + results.out_count
                    
                    # 🎯 DÉDUPLICATION : Ajouter les IDs uniques
                    if hasattr(counter, 'counted_ids') and counter.counted_ids:
                        for track_id in counter.counted_ids:
                            if track_id not in global_counted_ids:
                                global_counted_ids.add(track_id)
                                logger.info(f"✅ Nouveau produit détecté: ID={track_id} par {line_name} (frame {frame_idx})")
                
                frame = annotated_frames["ligne_5"]
                
                # Snapshot avec comptage dédupliqué
                if frame_idx > 0 and frame_idx % 100 == 0:
                    logger.info(f"\n📊 SNAPSHOT Frame {frame_idx}/{total_frames}:")
                    for line_name, counts in sorted(line_counts.items()):
                        logger.info(f"   {line_name}: TOTAL={counts['TOTAL']}")
                    logger.info(f"   🎯 IDs UNIQUES: {len(global_counted_ids)}")
                
                # Parser détections
                counter_centre = counters["ligne_5"]
                if hasattr(counter_centre, 'boxes') and counter_centre.boxes is not None:
                    for box, cls, conf_val in zip(counter_centre.boxes, counter_centre.clss, counter_centre.confs):
                        class_name = counter_centre.names[int(cls)]
                        
                        if class_name.lower() in self.detector.MEDICAL_CLASSES:
                            continue
                        
                        x1, y1, x2, y2 = box
                        
                        detection = Detection(
                            class_name=class_name,
                            confidence=float(conf_val),
                            bbox=BoundingBox(
                                x=float(x1) / width,
                                y=float(y1) / height,
                                width=float(x2 - x1) / width,
                                height=float(y2 - y1) / height
                            ),
                            source="object"
                        )
                        frame_detections.append(detection)
            else:
                frame = frame_original.copy()
            
            # EMPLOYÉS
            if model_type in ["employees", "both"]:
                detections_emp = self.detector.detect_frame(frame, conf=conf, model_type="employees")
                frame_detections.extend(detections_emp)
            
            frames_detections.append(
                FrameDetection(
                    frame_number=frame_idx,
                    timestamp=timestamp,
                    detections=frame_detections
                )
            )
            
            # Afficher comptage dédupliqué sur la vidéo
            cv2.putText(frame, f"UNIQUE IDs: {len(global_counted_ids)}", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
            
            out.write(frame)
            frame_idx += 1
            
            if progress_callback and frame_idx % 30 == 0:
                progress_callback(frame_idx, total_frames)
        
        cap.release()
        out.release()
        
        # 🎯 RÉSULTAT FINAL = NOMBRE D'IDs UNIQUES
        final_count = len(global_counted_ids)
        
        # Pour compatibilité, on garde aussi le maximum
        max_total = max(counts["TOTAL"] for counts in line_counts.values())
        best_line = max(line_counts.items(), key=lambda x: x[1]["TOTAL"])
        
        final_counts = {
            "produit": {
                "IN": final_count,  # Utiliser le comptage dédupliqué
                "OUT": 0,
                "TOTAL": final_count,  # 🎯 COMPTAGE DÉDUPLIQUÉ
                "best_line": "deduplication_globale",
                "max_line_count": max_total,  # Pour comparaison
                "unique_ids": list(global_counted_ids)  # Liste des IDs
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
        
        logger.info("\n" + "="*70)
        logger.info(f"📏 RÉSULTATS FINAUX:")
        logger.info("="*70)
        for line_name, counts in sorted(line_counts.items()):
            logger.info(f"   {line_name}: TOTAL={counts['TOTAL']}")
        logger.info("="*70)
        logger.info(f"📊 MAXIMUM des lignes: {max_total}")
        logger.info(f"🎯 COMPTAGE DÉDUPLIQUÉ: {final_count} produits uniques")
        logger.info(f"📋 IDs uniques: {sorted(global_counted_ids)}")
        logger.info("="*70)
        
        return frames_detections, metadata, final_counts
    
    def draw_detections(self, frame: np.ndarray, detections: List[Detection]) -> np.ndarray:
        """Dessiner les détections sur une frame"""
        annotated = frame.copy()
        h, w = frame.shape[:2]
        
        # Compter par classe
        class_counts = {}
        for det in detections:
            class_counts[det.class_name] = class_counts.get(det.class_name, 0) + 1
        
        # Dessiner chaque détection
        for det in detections:
            x1 = int(det.bbox.x * w)
            y1 = int(det.bbox.y * h)
            x2 = int((det.bbox.x + det.bbox.width) * w)
            y2 = int((det.bbox.y + det.bbox.height) * h)
            
            color = self.detector.get_color(det.class_name)
            
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            
            label = f"{det.class_name} {det.confidence:.2f}"
            (label_w, label_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(annotated, (x1, y1 - label_h - 10), (x1 + label_w, y1), color, -1)
            cv2.putText(annotated, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Afficher compteurs en haut
        y_offset = 30
        for class_name, count in sorted(class_counts.items()):
            color = self.detector.get_color(class_name)
            text = f"{class_name}: {count}"
            cv2.putText(annotated, text, (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            y_offset += 25
        
        return annotated
    
    @staticmethod
    def extract_frame(video_path: str, frame_number: int) -> Optional[np.ndarray]:
        """Extraire une frame spécifique"""
        try:
            cap = cv2.VideoCapture(video_path)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            ret, frame = cap.read()
            cap.release()
            
            return frame if ret else None
        
        except Exception as e:
            logger.error(f"❌ Erreur extraction frame : {e}")
            return None