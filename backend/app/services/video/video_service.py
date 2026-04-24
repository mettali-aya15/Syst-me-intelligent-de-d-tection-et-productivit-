#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Service de gestion des vidéos - COMPTAGE PAR LIGNE ADAPTATIF
"""

import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, List
from collections import defaultdict
import cv2
from bson import ObjectId
import numpy as np

from app.models.video import VideoUpload, VideoCreate, VideoStatus
from app.models.detection import FrameDetection, BoundingBox
from app.core.config import settings
from app.services.ai import FrameProcessor

import logging
logger = logging.getLogger(__name__)


class VideoService:
    """Service de gestion des vidéos"""
    
    @staticmethod
    def _get_db():
        """Obtenir Database avec import tardif"""
        from app.core.database import Database
        if Database.db is None:
            raise Exception("Database not connected")
        return Database
    
    @staticmethod
    async def upload_video(file_path: str, filename: str) -> dict:
        """Upload et enregistrer une vidéo"""
        Database = VideoService._get_db()
        
        try:
            upload_dir = Path(settings.UPLOAD_DIR)
            upload_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_extension = Path(filename).suffix
            new_filename = f"{Path(filename).stem}_{timestamp}{file_extension}"
            destination = upload_dir / new_filename
            
            shutil.copy(file_path, destination)
            
            cap = cv2.VideoCapture(str(destination))
            
            if not cap.isOpened():
                raise ValueError("Impossible de lire la vidéo")
            
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps if fps > 0 else 0
            
            cap.release()
            
            video_data = VideoCreate(
                filename=new_filename,
                file_path=str(destination),
                duration=duration,
                fps=fps,
                width=width,
                height=height,
                total_frames=total_frames
            )
            
            video = VideoUpload(**video_data.dict())
            
            collection = Database.get_collection("video_uploads")
            video_dict = video.dict(by_alias=True, exclude={"id"})
            result = await collection.insert_one(video_dict)
            
            logger.info(f"✅ Vidéo uploadée : {new_filename}")
            
            return {
                "video_id": str(result.inserted_id),
                "filename": new_filename,
                "duration": duration,
                "fps": fps,
                "resolution": f"{width}x{height}",
                "total_frames": total_frames,
                "status": "uploaded"
            }
        
        except Exception as e:
            logger.error(f"❌ Erreur upload vidéo : {e}")
            raise
    
    @staticmethod
    def count_unique_objects_smart(frames_detections: List[FrameDetection], line_counts: dict = None) -> dict:
        """
        Méthode Finale : Zone-Based Occupancy Counting (Sans dépendance aux Track IDs)
        Compte le nombre maximum d'employés présents simultanément dans des zones définies
        en utilisant un algorithme anti-chevauchement (NMS).
        """
        if not frames_detections:
            return {}
        
        unique_objects = {}
        
        # ✅ 1. PRODUITS : Via Lignes (Inchangé)
        if line_counts and "produit" in line_counts:
            unique_objects["produit"] = line_counts["produit"]["TOTAL"]
            logger.info(f"📦 Produits (via Lignes): {unique_objects['produit']}")
        else:
            unique_objects["produit"] = 0

        # ✅ 2. DÉFINITION DES ZONES (Exemple: Gauche et Droite)
        # Ajustez ces bornes si votre caméra a une perspective différente
        ZONES = {
            "zone_gauche": {"x_min": 0.0, "x_max": 0.5, "y_min": 0.0, "y_max": 1.0},
            "zone_droite": {"x_min": 0.5, "x_max": 1.0, "y_min": 0.0, "y_max": 1.0}
        }
        
        EMPLOYEE_TERMS = {'employé', 'employee actif', 'employee inactif'}
        
        # Stockage pour chaque frame: { zone_name: count }
        frame_zone_occupancy = []

        for frame_det in frames_detections:
            zone_counts = {z: 0 for z in ZONES}
            
            # Filtrer uniquement les employés
            employee_dets = [d for d in frame_det.detections if d.class_name.lower() in EMPLOYEE_TERMS]
            
            # Pour chaque zone, compter les employés uniques non-chevauchants
            for zone_name, bounds in ZONES.items():
                zone_dets = []
                for det in employee_dets:
                    cx = det.bbox.x + (det.bbox.width / 2)
                    cy = det.bbox.y + (det.bbox.height / 2)
                    
                    # Vérifier si le centre de la boîte est dans la zone
                    if (bounds["x_min"] <= cx <= bounds["x_max"] and 
                        bounds["y_min"] <= cy <= bounds["y_max"]):
                        zone_dets.append(det)
                
                # ✅ ALGORITHME ANTI-CHEVAUCHEMENT (NMS Simplifié)
                # Trier par confiance décroissante pour garder les meilleures détections
                zone_dets.sort(key=lambda x: x.confidence, reverse=True)
                
                kept_dets = []
                for det in zone_dets:
                    is_overlapping = False
                    d1_x1 = det.bbox.x
                    d1_y1 = det.bbox.y
                    d1_x2 = det.bbox.x + det.bbox.width
                    d1_y2 = det.bbox.y + det.bbox.height
                    
                    for kept in kept_dets:
                        k_x1 = kept.bbox.x
                        k_y1 = kept.bbox.y
                        k_x2 = kept.bbox.x + kept.bbox.width
                        k_y2 = kept.bbox.y + kept.bbox.height
                        
                        # Calculer l'intersection (IoU)
                        xx1 = max(d1_x1, k_x1)
                        yy1 = max(d1_y1, k_y1)
                        xx2 = min(d1_x2, k_x2)
                        yy2 = min(d1_y2, k_y2)
                        
                        w = max(0, xx2 - xx1)
                        h = max(0, yy2 - yy1)
                        inter = w * h
                        
                        area1 = (d1_x2 - d1_x1) * (d1_y2 - d1_y1)
                        area2 = (k_x2 - k_x1) * (k_y2 - k_y1)
                        union = area1 + area2 - inter
                        
                        iou = inter / union if union > 0 else 0
                        
                        # Si chevauchement > 30%, on considère que c'est la même personne (doublon)
                        if iou > 0.3: 
                            is_overlapping = True
                            break
                    
                    if not is_overlapping:
                        kept_dets.append(det)
                
                zone_counts[zone_name] = len(kept_dets)
            
            frame_zone_occupancy.append(zone_counts)

        # ✅ 3. CALCUL FINAL
        # Le nombre d'employés est le MAXIMUM de personnes vues simultanément dans toutes les zones combinées
        if frame_zone_occupancy:
            max_employees_left = max([f["zone_gauche"] for f in frame_zone_occupancy])
            max_employees_right = max([f["zone_droite"] for f in frame_zone_occupancy])
            
            # Total unique employees is the sum of max simultaneous in each disjoint zone
            total_employees = max_employees_left + max_employees_right
        else:
            total_employees = 0
        
        unique_objects['employé'] = total_employees
        
        logger.info(f"👥 Employés Uniques (Zone Occupancy): {total_employees}")
        logger.info(f"   Max Gauche: {max_employees_left if frame_zone_occupancy else 0}, Max Droite: {max_employees_right if frame_zone_occupancy else 0}")
        
        return unique_objects
    @staticmethod
    async def process_video(
        video_id: str,
        confidence: Optional[float] = None,
        model_type: str = "both",
        websocket=None
    ) -> dict:
        """Traiter une vidéo avec comptage par ligne adaptatif"""
        Database = VideoService._get_db()
        
        try:
            collection = Database.get_collection("video_uploads")
            video_doc = await collection.find_one({"_id": ObjectId(video_id)})
            
            if not video_doc:
                raise ValueError(f"Vidéo introuvable : {video_id}")
            
            video = VideoUpload(**video_doc)
            
            await collection.update_one(
                {"_id": ObjectId(video_id)},
                {"$set": {"status": VideoStatus.PROCESSING}}
            )
            
            annotated_dir = Path(settings.ANNOTATED_DIR)
            annotated_dir.mkdir(parents=True, exist_ok=True)
            
            annotated_filename = f"{Path(video.filename).stem}_annotated{Path(video.filename).suffix}"
            annotated_path = annotated_dir / annotated_filename
            
            conf = confidence if confidence is not None else settings.CONFIDENCE_THRESHOLD
            
            def progress_callback(current, total):
                progress = int((current / total) * 100)
                if current % 30 == 0:
                    logger.info(f"📍 {current}/{total} ({progress}%)")
            
            logger.info(f"🎥 {video.filename} | {video.duration:.1f}s @ {video.fps}fps")
            logger.info(f"🎯 Conf={conf}, Model={model_type}")
            
            processor = FrameProcessor()
            
            # Utiliser le comptage par ligne adaptatif (Méthode de FrameProcessor)
            frames_detections, metadata, line_counts = processor.process_video_with_line_counting(
                video_path=str(video.file_path),
                output_path=str(annotated_path),
                conf=conf,
                model_type=model_type,
                progress_callback=progress_callback
            )
            
            logger.info(f"🔍 Comptage objets uniques...")
            unique_objects = VideoService.count_unique_objects_smart(frames_detections, line_counts)
            
            detections_collection = Database.get_collection("video_detections")
            
            total_detections = 0
            summary = {}
            
            for frame_detection in frames_detections:
                for detection in frame_detection.detections:
                    detection_doc = {
                        "video_id": ObjectId(video_id),
                        "frame_number": frame_detection.frame_number,
                        "timestamp": frame_detection.timestamp,
                        "class_name": detection.class_name,
                        "confidence": detection.confidence,
                        "bbox": detection.bbox.dict(),
                        "source": detection.source,
                        "processed_at": datetime.now()
                    }
                    
                    await detections_collection.insert_one(detection_doc)
                    
                    total_detections += 1
                    summary[detection.class_name] = summary.get(detection.class_name, 0) + 1
            
            await collection.update_one(
                {"_id": ObjectId(video_id)},
                {
                    "$set": {
                        "status": VideoStatus.COMPLETED,
                        "annotated_path": str(annotated_path),
                        "total_detections": total_detections,
                        "summary": summary,
                        "unique_objects": unique_objects,
                        "processed_at": datetime.now()
                    }
                }
            )
            
            logger.info(f"✅ Total: {total_detections} | Uniques: {unique_objects}")
            
            return {
                "video_id": video_id,
                "status": "completed",
                "total_detections": total_detections,
                "summary": summary,
                "unique_objects": unique_objects
            }
        
        except Exception as e:
            logger.error(f"❌ Erreur: {e}")
            
            collection = Database.get_collection("video_uploads")
            await collection.update_one(
                {"_id": ObjectId(video_id)},
                {"$set": {"status": VideoStatus.FAILED}}
            )
            
            raise
    
    @staticmethod
    async def get_video(video_id: str) -> Optional[VideoUpload]:
        """Récupérer vidéo"""
        Database = VideoService._get_db()
        collection = Database.get_collection("video_uploads")
        video_doc = await collection.find_one({"_id": ObjectId(video_id)})
        return VideoUpload(**video_doc) if video_doc else None
    
    @staticmethod
    async def list_videos(status: Optional[VideoStatus] = None, limit: int = 50, skip: int = 0) -> List[VideoUpload]:
        """Lister vidéos"""
        Database = VideoService._get_db()
        collection = Database.get_collection("video_uploads")
        query = {}
        if status:
            query["status"] = status
        cursor = collection.find(query).sort("uploaded_at", -1).skip(skip).limit(limit)
        videos = await cursor.to_list(length=limit)
        return [VideoUpload(**v) for v in videos]
    
    @staticmethod
    async def delete_video(video_id: str) -> bool:
        """Supprimer vidéo"""
        Database = VideoService._get_db()
        
        try:
            collection = Database.get_collection("video_uploads")
            video_doc = await collection.find_one({"_id": ObjectId(video_id)})
            
            if not video_doc:
                return False
            
            video = VideoUpload(**video_doc)
            
            if Path(video.file_path).exists():
                Path(video.file_path).unlink()
            
            if video.annotated_path and Path(video.annotated_path).exists():
                Path(video.annotated_path).unlink()
            
            detections_collection = Database.get_collection("video_detections")
            await detections_collection.delete_many({"video_id": ObjectId(video_id)})
            
            await collection.delete_one({"_id": ObjectId(video_id)})
            
            logger.info(f"✅ Supprimé: {video_id}")
            
            return True
        
        except Exception as e:
            logger.error(f"❌ Erreur: {e}")
            return False