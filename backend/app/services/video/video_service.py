#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Service de gestion des vidéos - MÉTHODE STATISTIQUE SIMPLE
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
    def count_unique_objects_smart(frames_detections: List[FrameDetection]) -> dict:
        """
        Comptage intelligent - Méthode statistique TOP 20%
        Pour machines/objets statiques: médiane du TOP 20%
        Pour produits/employés mobiles: maximum observé
        """
        if not frames_detections:
            return {}
        
        class_counts_per_frame = defaultdict(list)
        
        # Collecter les comptages par frame
        for frame_detection in frames_detections:
            frame_counts = defaultdict(int)
            for detection in frame_detection.detections:
                frame_counts[detection.class_name] += 1
            
            for class_name, count in frame_counts.items():
                class_counts_per_frame[class_name].append(count)
        
        unique_objects = {}
        
        # Classes mobiles (produits sur convoyeur)
        MOBILE_CLASSES = ["produit"]
        
        for class_name, counts in class_counts_per_frame.items():
            non_zero = [c for c in counts if c > 0]
            if not non_zero:
                continue
            
            # Pour produits: utiliser MAXIMUM (tous les produits passent)
            if any(mobile in class_name.lower() for mobile in MOBILE_CLASSES):
                result = max(non_zero)
                logger.info(f"📦 {class_name}: MAXIMUM = {result}")
            
            # Pour objets statiques: MÉDIANE du TOP 20%
            else:
                sorted_counts = sorted(non_zero, reverse=True)
                top_20_percent = max(1, len(sorted_counts) // 5)
                top_values = sorted_counts[:top_20_percent]
                
                median_idx = len(top_values) // 2
                if len(top_values) % 2 == 0:
                    result = (top_values[median_idx - 1] + top_values[median_idx]) / 2
                else:
                    result = top_values[median_idx]
                
                logger.info(f"📦 {class_name}: TOP20% médiane = {result:.1f} → {int(round(result))}")
                result = int(round(result))
            
            unique_objects[class_name] = int(round(result))
        
        logger.info(f"🎯 Final: {unique_objects}")
        
        return unique_objects
    
    
    @staticmethod
    async def process_video(
        video_id: str,
        confidence: Optional[float] = None,
        model_type: str = "both",
        websocket=None
    ) -> dict:
        """Traiter une vidéo"""
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
            frames_detections, metadata = processor.process_video(
                video_path=str(video.file_path),
                output_path=str(annotated_path),
                conf=conf,
                save_annotated=True,
                progress_callback=progress_callback,
                model_type=model_type
            )
            
            logger.info(f"🔍 Comptage objets uniques...")
            unique_objects = VideoService.count_unique_objects_smart(frames_detections)
            
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