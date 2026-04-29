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
        Comptage intelligent avec SAFEGUARD GLOBAL
        - Produits : Via lignes (seulement si détectés)
        - Employés (best_objects.pt) : Via zones + NMS (seulement si détectés)
        - Noms (best_person.pt) : 1 nom = 1 personne (forcé à 1)
        - Autres : Via statistique SEULEMENT si détectés
        """
        if not frames_detections:
            return {}
        
        unique_objects = {}
        
        # ✅ ÉTAPE 0 : INVENTAIRE COMPLET DES CLASSES DÉTECTÉES
        detected_classes = set()
        for frame_det in frames_detections:
            for detection in frame_det.detections:
                detected_classes.add(detection.class_name.lower())
        
        logger.info(f"🔍 Classes détectées dans la vidéo : {detected_classes}")
        
        # ✅ 1. PRODUITS : Via Lignes SEULEMENT SI DÉTECTÉS
        if 'produit' in detected_classes:
            if line_counts and "produit" in line_counts:
                product_count = line_counts["produit"]["TOTAL"]
                unique_objects["produit"] = product_count
                logger.info(f"📦 Produits (via Lignes): {product_count}")
            else:
                # Comptage manuel par IDs
                product_ids = set()
                for frame_det in frames_detections:
                    for det in frame_det.detections:
                        if det.class_name.lower() == 'produit' and det.track_id is not None:
                            product_ids.add(det.track_id)
                if len(product_ids) > 0:
                    unique_objects["produit"] = len(product_ids)
                    logger.info(f"📦 Produits (comptage manuel): {len(product_ids)}")

        # ✅ 2. EMPLOYÉS (best_objects.pt) : COMPTAGE PAR ZONES + NMS
        ZONES = {
            "zone_gauche": {"x_min": 0.0, "x_max": 0.5, "y_min": 0.0, "y_max": 1.0},
            "zone_droite": {"x_min": 0.5, "x_max": 1.0, "y_min": 0.0, "y_max": 1.0}
        }

        EMPLOYEE_TERMS = {'employé', 'employé actif', 'employé inactif'}

        has_employees = any(
            any(term in class_name for term in EMPLOYEE_TERMS)
            for class_name in detected_classes
        )

        if has_employees:
            # ========== COMPTAGE TOTAL ==========
            frame_zone_occupancy_total = []

            for frame_det in frames_detections:
                zone_counts = {z: 0 for z in ZONES}
                
                employee_dets = []
                for d in frame_det.detections:
                    class_lower = d.class_name.lower()
                    if any(term in class_lower for term in EMPLOYEE_TERMS):
                        employee_dets.append(d)
                
                for zone_name, bounds in ZONES.items():
                    zone_dets = []
                    for det in employee_dets:
                        cx = det.bbox.x + (det.bbox.width / 2)
                        cy = det.bbox.y + (det.bbox.height / 2)
                        
                        if (bounds["x_min"] <= cx <= bounds["x_max"] and 
                            bounds["y_min"] <= cy <= bounds["y_max"]):
                            zone_dets.append(det)
                    
                    # NMS
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
                            
                            if iou > 0.3:
                                is_overlapping = True
                                break
                        
                        if not is_overlapping:
                            kept_dets.append(det)
                    
                    zone_counts[zone_name] = len(kept_dets)
                
                frame_zone_occupancy_total.append(zone_counts)

            if frame_zone_occupancy_total:
                max_total_left = max([f["zone_gauche"] for f in frame_zone_occupancy_total])
                max_total_right = max([f["zone_droite"] for f in frame_zone_occupancy_total])
                total_employees = max_total_left + max_total_right
            else:
                total_employees = 0
            
            unique_objects['employé'] = total_employees
            logger.info(f"👥 employé (TOTAL): {total_employees}")
            logger.info(f"   Max Gauche: {max_total_left if frame_zone_occupancy_total else 0}, Max Droite: {max_total_right if frame_zone_occupancy_total else 0}")
            
            # ========== COMPTAGE INACTIFS ==========
            if 'employé inactif' in detected_classes:
                frame_zone_occupancy_inactive = []

                for frame_det in frames_detections:
                    zone_counts = {z: 0 for z in ZONES}
                    
                    inactive_dets = [d for d in frame_det.detections 
                                    if d.class_name.lower() == 'employé inactif']
                    
                    for zone_name, bounds in ZONES.items():
                        zone_dets = []
                        for det in inactive_dets:
                            cx = det.bbox.x + (det.bbox.width / 2)
                            cy = det.bbox.y + (det.bbox.height / 2)
                            
                            if (bounds["x_min"] <= cx <= bounds["x_max"] and 
                                bounds["y_min"] <= cy <= bounds["y_max"]):
                                zone_dets.append(det)
                        
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
                                
                                if iou > 0.3:
                                    is_overlapping = True
                                    break
                            
                            if not is_overlapping:
                                kept_dets.append(det)
                        
                        zone_counts[zone_name] = len(kept_dets)
                    
                    frame_zone_occupancy_inactive.append(zone_counts)

                if frame_zone_occupancy_inactive:
                    max_inactive_left = max([f["zone_gauche"] for f in frame_zone_occupancy_inactive])
                    max_inactive_right = max([f["zone_droite"] for f in frame_zone_occupancy_inactive])
                    total_inactive = max_inactive_left + max_inactive_right
                else:
                    total_inactive = 0
                
                if total_inactive > 0:
                    unique_objects['employé inactif'] = total_inactive
                    logger.info(f"👥 employé inactif: {total_inactive} (Gauche: {max_inactive_left}, Droite: {max_inactive_right})")
                
                total_active = total_employees - total_inactive
                if total_active > 0:
                    unique_objects['employé actif'] = total_active
                    logger.info(f"👥 employé actif (calculé): {total_active} = {total_employees} - {total_inactive}")
            
            elif 'employé actif' in detected_classes:
                if total_employees > 0:
                    unique_objects['employé actif'] = total_employees
                    logger.info(f"👥 employé actif (classe détectée): {total_employees}")
            else:
                logger.info(f"👥 Pas de sous-classes employé (actif/inactif) détectées")
        
        # ✅ 3. NOMS D'EMPLOYÉS (best_person.pt) : 1 NOM = 1 PERSONNE (FORCÉ À 1)
        EMPLOYEE_NAMES = {
            'amelie', 'seline', 'ibtihel', 'ali', 'mohamed', 
            'alena', 'adem', 'amir', 'sami', 'insaf', 'employe'
        }
        
        # Détecter quels noms sont présents
        detected_names = set()
        total_unique_employees = 0
        
        for frame_det in frames_detections:
            for det in frame_det.detections:
                class_lower = det.class_name.lower()
                if det.source == "employee_name" and class_lower in EMPLOYEE_NAMES:
                    detected_names.add(det.class_name)
        
        logger.info(f"👤 Noms détectés : {detected_names}")
        
        # Compter chaque nom individuellement - FORCÉ À 1
        for name in detected_names:
            # Ne pas compter "employe" comme nom individuel
            if name.lower() != 'employe':
                # ✅ FORCER à 1 (1 nom = 1 personne unique)
                unique_objects[name] = 1
                total_unique_employees += 1
                logger.info(f"👤 {name}: 1")
        
        # ✅ Ajouter le TOTAL "employe"
        if total_unique_employees > 0:
            unique_objects['employe'] = total_unique_employees
            logger.info(f"👥 employe (TOTAL): {total_unique_employees}")
        
        # ✅ Traiter "porte verte" et "temps" séparément (objets contextuels)
        contextual_objects = {'porte verte', 'porte_verte', 'temps', 'temp'}
        
        for frame_det in frames_detections:
            for det in frame_det.detections:
                class_lower = det.class_name.lower()
                
                # Si c'est porte verte ou temps
                if det.source == "employee_name" and class_lower in contextual_objects:
                    # Normaliser le nom
                    if 'porte' in class_lower:
                        normalized_name = 'porte verte'
                    else:
                        normalized_name = 'temps'
                    
                    # Ajouter si pas encore présent
                    if normalized_name not in unique_objects:
                        unique_objects[normalized_name] = 1
                        logger.info(f"🏷️ {normalized_name}: 1 (objet contextuel)")
        
        # ✅ 4. AUTRES CLASSES (machines, tables, etc.) : COMPTAGE STATISTIQUE
        class_counts_per_frame = defaultdict(list)
        
        for frame_detection in frames_detections:
            frame_counts = defaultdict(int)
            for detection in frame_detection.detections:
                class_lower = detection.class_name.lower()
                
                # Exclure produits, employés et noms (déjà comptés)
                if (class_lower not in EMPLOYEE_TERMS and 
                    class_lower != 'produit' and 
                    detection.source != "employee_name"):
                    
                    frame_counts[detection.class_name] += 1
            
            for class_name, count in frame_counts.items():
                class_counts_per_frame[class_name].append(count)
        
        for class_name, counts in class_counts_per_frame.items():
            if class_name in unique_objects:
                continue
            
            class_lower = class_name.lower()
            
            if class_lower not in detected_classes:
                logger.info(f"⚠️ Classe '{class_name}' dans comptage mais pas dans detected_classes - IGNORÉ")
                continue
            
            non_zero = [c for c in counts if c > 0]
            if not non_zero:
                logger.info(f"⚠️ Classe '{class_name}' : aucune frame avec count > 0 - IGNORÉ")
                continue
            
            sorted_counts = sorted(non_zero, reverse=True)
            top_20_percent = max(1, len(sorted_counts) // 5)
            top_values = sorted_counts[:top_20_percent]
            
            median_idx = len(top_values) // 2
            if len(top_values) % 2 == 0:
                result = (top_values[median_idx - 1] + top_values[median_idx]) / 2
            else:
                result = top_values[median_idx]
            
            final_count = int(round(result))
            
            if final_count > 0:
                unique_objects[class_name] = final_count
                logger.info(f"✅ {class_name}: {final_count}")
            else:
                logger.info(f"⚠️ Classe '{class_name}' : final_count = 0 - IGNORÉ")
        
        logger.info(f"🎯 Final: {unique_objects}")
        
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
            
            # Utiliser le comptage par ligne adaptatif
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