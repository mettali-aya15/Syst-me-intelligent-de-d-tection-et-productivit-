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
import unicodedata
import re

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
    def normalize_filename(filename: str) -> str:
        """
        Normaliser un nom de fichier en enlevant les accents et caractères spéciaux
        
        Args:
            filename: Nom de fichier original
        
        Returns:
            Nom de fichier normalisé (ASCII seulement)
        """
        path_obj = Path(filename)
        stem = path_obj.stem
        extension = path_obj.suffix
        
        stem = unicodedata.normalize('NFKD', stem)
        stem = stem.encode('ASCII', 'ignore').decode('ASCII')
        stem = re.sub(r'[^\w\-]', '_', stem)
        stem = re.sub(r'_+', '_', stem)
        stem = stem.strip('_')
        
        return f"{stem}{extension}"
    
    @staticmethod
    async def upload_video(
        file_path: str, 
        filename: str,
        model_type: str = "objects",
        confidence: float = 0.3
    ) -> dict:
        """Upload et enregistrer une vidéo"""
        Database = VideoService._get_db()
        
        try:
            upload_dir = Path(settings.UPLOAD_DIR)
            upload_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_extension = Path(filename).suffix
            
            normalized_stem = VideoService.normalize_filename(Path(filename).stem)
            new_filename = f"{normalized_stem}_{timestamp}{file_extension}"
            destination = upload_dir / new_filename
            
            logger.info(f"📝 Nom original: {filename}")
            logger.info(f"📝 Nom normalisé: {new_filename}")
            
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
            
            video_data = {
                "filename": new_filename,
                "file_path": str(destination),
                "duration": duration,
                "fps": fps,
                "width": width,
                "height": height,
                "total_frames": total_frames,
                "model_type": model_type,
                "confidence": confidence,
                "status": VideoStatus.UPLOADED,
                "uploaded_at": datetime.now()
            }
            
            collection = Database.get_collection("video_uploads")
            result = await collection.insert_one(video_data)
            
            logger.info(f"✅ Vidéo uploadée : {new_filename} (model={model_type}, conf={confidence})")
            
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
        """
        if not frames_detections:
            return {}
        
        unique_objects = {}
        
        detected_classes = set()
        for frame_det in frames_detections:
            for detection in frame_det.detections:
                detected_classes.add(detection.class_name.lower())
        
        logger.info(f"🔍 Classes détectées dans la vidéo : {detected_classes}")
        
        if 'produit' in detected_classes:
            if line_counts and "produit" in line_counts:
                product_count = line_counts["produit"]["TOTAL"]
                unique_objects["produit"] = product_count
                logger.info(f"📦 Produits (via Lignes): {product_count}")
            else:
                product_ids = set()
                for frame_det in frames_detections:
                    for det in frame_det.detections:
                        if det.class_name.lower() == 'produit' and det.track_id is not None:
                            product_ids.add(det.track_id)
                if len(product_ids) > 0:
                    unique_objects["produit"] = len(product_ids)
                    logger.info(f"📦 Produits (comptage manuel): {len(product_ids)}")

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
                    logger.info(f"👥 employé inactif: {total_inactive}")
                
                total_active = total_employees - total_inactive
                if total_active > 0:
                    unique_objects['employé actif'] = total_active
                    logger.info(f"👥 employé actif (calculé): {total_active}")
            
            elif 'employé actif' in detected_classes:
                if total_employees > 0:
                    unique_objects['employé actif'] = total_employees
                    logger.info(f"👥 employé actif (classe détectée): {total_employees}")
        
        EMPLOYEE_NAMES = {
            'amelie', 'seline', 'ibtihel', 'ali', 'mohamed', 
            'alena', 'adem', 'amir', 'sami', 'insaf', 'employe'
        }
        
        detected_names = set()
        total_unique_employees = 0
        
        for frame_det in frames_detections:
            for det in frame_det.detections:
                class_lower = det.class_name.lower()
                if det.source == "employee_name" and class_lower in EMPLOYEE_NAMES:
                    detected_names.add(det.class_name)
        
        logger.info(f"👤 Noms détectés : {detected_names}")
        
        for name in detected_names:
            if name.lower() != 'employe':
                unique_objects[name] = 1
                total_unique_employees += 1
                logger.info(f"👤 {name}: 1")
        
        if total_unique_employees > 0:
            unique_objects['employe'] = total_unique_employees
            logger.info(f"👥 employe (TOTAL): {total_unique_employees}")
        
        contextual_objects = {'porte verte', 'porte_verte', 'temps', 'temp'}
        
        for frame_det in frames_detections:
            for det in frame_det.detections:
                class_lower = det.class_name.lower()
                
                if det.source == "employee_name" and class_lower in contextual_objects:
                    if 'porte' in class_lower:
                        normalized_name = 'porte verte'
                    else:
                        normalized_name = 'temps'
                    
                    if normalized_name not in unique_objects:
                        unique_objects[normalized_name] = 1
                        logger.info(f"🏷️ {normalized_name}: 1")
        
        class_counts_per_frame = defaultdict(list)
        
        for frame_detection in frames_detections:
            frame_counts = defaultdict(int)
            for detection in frame_detection.detections:
                class_lower = detection.class_name.lower()
                
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
                continue
            
            non_zero = [c for c in counts if c > 0]
            if not non_zero:
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
                {
                    "$set": {
                        "status": VideoStatus.COMPLETED,
                        "processed_at": datetime.now()
                    }
                }
            )
            
            annotated_dir = Path(settings.ANNOTATED_DIR)
            annotated_dir.mkdir(parents=True, exist_ok=True)
            
            normalized_stem = VideoService.normalize_filename(Path(video.filename).stem)
            annotated_filename = f"{normalized_stem}_annotated{Path(video.filename).suffix}"
            annotated_path = annotated_dir / annotated_filename
            
            conf = confidence if confidence is not None else settings.CONFIDENCE_THRESHOLD
            
            def progress_callback(current, total):
                progress = int((current / total) * 100)
                if current % 30 == 0:
                    logger.info(f"📍 {current}/{total} ({progress}%)")
            
            logger.info(f"🎥 {video.filename} | {video.duration:.1f}s @ {video.fps}fps")
            logger.info(f"🎯 Conf={conf}, Model={model_type}")
            
            processor = FrameProcessor()
            
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

# ✅ Calculer total_detections AVANT la boucle
            total_detections = len([det for frame in frames_detections for det in frame.detections])

# ❌ SUPPRIMER LA BOUCLE COMPLÈTEMENT
# (on ne crée pas detection_doc par frame)

# ✅ Créer UN SEUL document FINAL APRÈS
            final_detection_doc = {
    "video_id": ObjectId(video_id),
    "processed_at": datetime.now(),
    "classes_detectees": unique_objects
}

            await detections_collection.insert_one(final_detection_doc)

            await collection.update_one(
    {"_id": ObjectId(video_id)},
    {
        "$set": {
            "status": VideoStatus.COMPLETED,
            "annotated_path": str(annotated_path),
            "total_detections": total_detections,
            "processed_at": datetime.now()
        }
    }
)
            
            logger.info(f"✅ Total: {total_detections} | Uniques: {unique_objects}")
            
            # ✅ AJOUTÉ : Envoyer les notifications via WebSocket
            await VideoService._send_analysis_notifications(video_id, video_doc, unique_objects)
            
            return {
                "video_id": video_id,
                "status": "completed",
                "total_detections": total_detections,
                "unique_objects": unique_objects
            }
        
        except Exception as e:
            logger.error(f"❌ Erreur: {e}")
            
            # ✅ AJOUTÉ : Récupérer le nom du fichier et notifier l'erreur
            Database = VideoService._get_db()
            collection = Database.get_collection("video_uploads")
            video_doc = await collection.find_one({"_id": ObjectId(video_id)})
            filename = video_doc.get('filename', 'Fichier inconnu') if video_doc else 'Fichier inconnu'
            
            await VideoService._send_error_notification(video_id, filename, str(e))
            
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
    
    @staticmethod
    async def calculate_attendance(video_id: str) -> dict:
        """Calculer la présence/absence des employés pour une vidéo"""
        try:
            from app.services.employee import EmployeeService
            
            video = await VideoService.get_video(video_id)
            if not video or not video.unique_objects:
                return {
                    "total_employees": 0,
                    "present": [],
                    "present_count": 0,
                    "absent": [],
                    "absent_count": 0,
                    "attendance_rate": 0
                }
            
            EMPLOYEE_NAMES = {
                'amelie', 'seline', 'ibtihel', 'ali', 'mohamed',
                'alena', 'adem', 'amir', 'sami', 'insaf', 'aya'
            }
            
            detected_names = []
            for class_name in video.unique_objects.keys():
                class_lower = class_name.lower()
                if class_lower in EMPLOYEE_NAMES:
                    detected_names.append(class_lower)
            
            logger.info(f"👤 Noms détectés dans la vidéo : {detected_names}")
            
            all_employees = await EmployeeService.list_employees(active_only=True)
            
            present_employees = []
            absent_employees = []
            
            for emp in all_employees:
                if emp.name in detected_names:
                    present_employees.append({
                        "id": str(emp.id),
                        "name": emp.name,
                        "full_name": emp.full_name,
                        "department": emp.department,
                        "email": emp.email
                    })
                else:
                    absent_employees.append({
                        "id": str(emp.id),
                        "name": emp.name,
                        "full_name": emp.full_name,
                        "department": emp.department,
                        "email": emp.email
                    })
            
            total = len(all_employees)
            present_count = len(present_employees)
            attendance_rate = (present_count / total * 100) if total > 0 else 0
            
            logger.info(f"👥 Présence: {present_count}/{total} ({attendance_rate:.1f}%)")
            
            return {
                "total_employees": total,
                "present": present_employees,
                "present_count": present_count,
                "absent": absent_employees,
                "absent_count": len(absent_employees),
                "attendance_rate": round(attendance_rate, 1)
            }
        
        except ImportError:
            logger.warning("⚠️ EmployeeService non disponible")
            return {
                "total_employees": 0,
                "present": [],
                "present_count": 0,
                "absent": [],
                "absent_count": 0,
                "attendance_rate": 0
            }
        except Exception as e:
            logger.error(f"❌ Erreur calcul présence : {e}")
            return {
                "total_employees": 0,
                "present": [],
                "present_count": 0,
                "absent": [],
                "absent_count": 0,
                "attendance_rate": 0
            }
    
    # ✅ MÉTHODES WEBSOCKET AJOUTÉES
    @staticmethod
    async def _send_analysis_notifications(
        video_id: str, 
        video_doc: dict, 
        unique_objects: dict
    ):
        """
        Envoyer les notifications d'analyse terminée et d'alertes via WebSocket
        """
        try:
            from app.api.v1.routes.websocket_route import manager
            
            logger.info(f"📨 Préparation notifications pour vidéo {video_id}")
            
            alerts = {
                'machines_stopped': (
                    unique_objects.get('machine arrêtée', 0) or 
                    unique_objects.get('machine arretee', 0)
                ),
                'employees_inactive': (
                    unique_objects.get('employé inactif', 0) or 
                    unique_objects.get('employe inactif', 0)
                ),
                'tables_empty': (
                    unique_objects.get('tables_vides', 0) or 
                    unique_objects.get('table_vide', 0) or
                    unique_objects.get('tables vides', 0)
                ),
                'employees_absent': 0
            }
            
            
            logger.info(f"🚨 Alertes calculées: {alerts}")
            Database = VideoService._get_db()
            notifications_collection = Database.get_collection("notifications")
            
            notifications_to_insert = []
            
            # 1️⃣ NOTIFICATION : Analyse terminée (TOUJOURS)
            notifications_to_insert.append({
                "type": "video_complete",
                "severity": "low",
                "title": "Analyse vidéo terminée",
                "message": f"La vidéo '{video_doc.get('filename')}' a été analysée avec succès",


                "created_at": datetime.now()
            })
            
            # 2️⃣ NOTIFICATION : Machines arrêtées (SI DÉTECTÉES)
            if alerts['machines_stopped'] > 0:
                notifications_to_insert.append({
                    "type": "alert",
                    "severity": "high",
                    "title": "Machine(s) arrêtée(s) détectée(s)",
                    "message": f"{alerts['machines_stopped']} machine(s) arrêtée(s) détectée(s) dans la vidéo '{video_doc.get('filename')}'",


                    "created_at": datetime.now()
                })
            
            # 3️⃣ NOTIFICATION : Employés inactifs (SI DÉTECTÉS)
            if alerts['employees_inactive'] > 0:
                notifications_to_insert.append({
                    "type": "alert",
                    "severity": "medium",
                    "title": "Employé(s) inactif(s) détecté(s)",
                    "message": f"{alerts['employees_inactive']} employé(s) inactif(s) détecté(s) dans la vidéo '{video_doc.get('filename')}'",


                    "created_at": datetime.now()
                })
            
            # 4️⃣ NOTIFICATION : Tables vides (SI DÉTECTÉES)
            if alerts['tables_empty'] > 0:
                notifications_to_insert.append({
                    "type": "alert",
                    "severity": "low",
                    "title": "Table(s) vide(s) détectée(s)",
                    "message": f"{alerts['tables_empty']} table(s) vide(s) détectée(s) dans la vidéo '{video_doc.get('filename')}'",


                    "created_at": datetime.now()
                })
            
            # Insérer toutes les notifications en une seule fois
            if notifications_to_insert:
                result = await notifications_collection.insert_many(notifications_to_insert)
                logger.info(f"✅ {len(result.inserted_ids)} notification(s) sauvegardée(s) dans MongoDB")

            
            message = {
                'type': 'analysis_complete',
                'data': {
                    'video_id': video_id,
                    'filename': video_doc.get('filename'),
                    'status': 'completed',
                    'alerts': alerts
                }
            }
            
            logger.info(f"📤 Envoi notification WebSocket: {message}")
            await manager.broadcast(message)
            logger.info(f"✅ Notification envoyée pour vidéo {video_id}")
        
        except Exception as e:
            logger.error(f"❌ Erreur envoi notification WebSocket: {e}")
    
    @staticmethod
    async def _send_error_notification(video_id: str, filename: str, error: str):
        """
        Envoyer une notification d'erreur via WebSocket
        """
        try:
            from app.api.v1.routes.websocket_route import manager
            
            message = {
                'type': 'analysis_error',
                'data': {
                    'video_id': video_id,
                    'filename': filename,
                    'error': error
                }
            }
            Database = VideoService._get_db()
            notifications_collection = Database.get_collection("notifications")
            
            notification_doc = {
                "type": "video_failed",
                "severity": "high",
                "title": "Erreur d'analyse vidéo",
                "message": f"L'analyse de '{filename}' a échoué : {error}",


                "created_at": datetime.now()
            }
            
            result = await notifications_collection.insert_one(notification_doc)
            logger.info(f"✅ Notification d'erreur sauvegardée dans MongoDB : {result.inserted_id}")
            
            logger.error(f"📤 Envoi notification d'erreur WebSocket: {message}")
            await manager.broadcast(message)
        
        except Exception as e:
            logger.error(f"❌ Erreur envoi notification erreur WebSocket: {e}")












