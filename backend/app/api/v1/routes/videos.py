#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Routes API pour les vidéos
Upload, traitement, listage, téléchargement
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Query
from fastapi.responses import FileResponse
from typing import List, Optional
from pathlib import Path
import shutil
import tempfile
from datetime import datetime

from app.services.video import VideoService
from app.core.database import Database
from app.utils.file_hash import calculate_file_hash
import app.models.video

import logging
logger = logging.getLogger(__name__)

router = APIRouter()


# ========== 1. UPLOAD ==========
@router.post("/upload", response_model=dict)
async def upload_video(
    file: UploadFile = File(...),
    model_type: Optional[str] = Query("objects", pattern="^(employees|objects|both)$"),
    confidence: Optional[float] = Query(0.3, ge=0.1, le=1.0),
    background_tasks: BackgroundTasks = None
):
    """Upload une vidéo - CHAQUE UPLOAD = NOUVELLE ENTRÉE"""
    allowed_extensions = [".mp4", ".avi", ".mov", ".mkv"]
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Extension non supportée. Extensions acceptées : {', '.join(allowed_extensions)}"
        )
    
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            tmp_path = tmp_file.name
        
        result = await VideoService.upload_video(
            tmp_path,
            file.filename,
            model_type=model_type,
            confidence=confidence
        )
        
        logger.info(f"✅ Vidéo uploadée : {result['video_id']}")
        
        return result
    
    except Exception as e:
        logger.error(f"❌ Erreur upload vidéo : {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erreur upload : {str(e)}")
    
    finally:
        file.file.close()


# ========== 2. ANALYZE (NOUVEAU !) ==========
@router.post("/{video_id}/analyze", status_code=200)
async def analyze_video(
    video_id: str,
    background_tasks: BackgroundTasks
):
    """
    Démarre l'analyse d'une vidéo uploadée
    """
    try:
        from bson import ObjectId
        
        logger.info(f"🎬 Démarrage analyse pour vidéo: {video_id}")
        
        # Récupérer la vidéo
        Database_conn = VideoService._get_db()
        video_doc = await Database_conn.get_collection("video_uploads").find_one({"_id": ObjectId(video_id)})
        
        if not video_doc:
            raise HTTPException(status_code=404, detail="Vidéo non trouvée")
        
        if video_doc.get("status") != "uploaded":
            raise HTTPException(
                status_code=400, 
                detail=f"Vidéo déjà en cours d'analyse ou terminée (status: {video_doc.get('status')})"
            )
        
        # Récupérer les paramètres sauvegardés
        model_type = video_doc.get("model_type", "both")
        confidence = video_doc.get("confidence", 0.3)
        
        logger.info(f"🎯 Paramètres analyse: model={model_type}, conf={confidence}")
        
        # Lancer l'analyse en arrière-plan
        background_tasks.add_task(
            VideoService.process_video,
            video_id=video_id,
            model_type=model_type,
            confidence=confidence
        )
        
        logger.info(f"✅ Analyse démarrée en arrière-plan pour: {video_id}")
        
        return {
            "message": "Analyse démarrée",
            "video_id": video_id,
            "status": "analyzing"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur démarrage analyse: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ========== 3. PROCESS ==========
@router.post("/{video_id}/process", response_model=dict)
async def process_video(
    video_id: str,
    confidence: Optional[float] = Query(None, ge=0.1, le=1.0),
    model_type: Optional[str] = Query(None, pattern="^(employees|objects|both)$")
):
    """
    Traiter une vidéo (détection YOLO)
    
    Si confidence et model_type ne sont pas fournis, 
    utilise les valeurs sauvegardées lors de l'upload
    """
    try:
        from bson import ObjectId
        
        Database_conn = VideoService._get_db()
        video_doc = await Database_conn.get_collection("video_uploads").find_one({"_id": ObjectId(video_id)})
        
        if not video_doc:
            raise HTTPException(status_code=404, detail="Vidéo non trouvée")
        
        final_confidence = confidence if confidence is not None else video_doc.get("confidence", 0.3)
        final_model_type = model_type if model_type is not None else video_doc.get("model_type", "objects")
        
        logger.info(f"🎯 Process vidéo {video_id}: model={final_model_type}, conf={final_confidence}")
        
        result = await VideoService.process_video(
            video_id=video_id,
            confidence=final_confidence,
            model_type=final_model_type
        )
        
        return result
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Erreur traitement vidéo : {e}")
        raise HTTPException(status_code=500, detail=f"Erreur traitement : {str(e)}")


# ========== 4. DOWNLOAD ==========
@router.get("/{video_id}/download")
async def download_video(video_id: str, annotated: bool = False):
    """Télécharger une vidéo"""
    try:
        video = await VideoService.get_video(video_id)
        
        if not video:
            raise HTTPException(status_code=404, detail="Vidéo introuvable")
        
        if annotated:
            if not video.annotated_path:
                raise HTTPException(
                    status_code=404,
                    detail="Vidéo annotée non disponible. Traitez d'abord la vidéo."
                )
            file_path = video.annotated_path
        else:
            file_path = video.file_path
        
        if not Path(file_path).exists():
            raise HTTPException(status_code=404, detail="Fichier vidéo introuvable sur le disque")
        
        return FileResponse(
            path=file_path,
            media_type="video/mp4",
            filename=Path(file_path).name
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur téléchargement vidéo : {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== 5. CORRECT COUNTS ==========
@router.patch("/{video_id}/correct-counts")
async def correct_object_counts(
    video_id: str,
    corrected_counts: dict
):
    """Corriger manuellement le comptage d'objets"""
    try:
        result = await VideoService.manually_correct_counts(video_id, corrected_counts)
        return result
    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== 6. GET SINGLE VIDEO (IMPORTANT !) ==========
@router.get("/{video_id}", response_model=dict)
async def get_video(video_id: str):
    """
    Obtenir les détails d'une vidéo
    
    - **video_id**: ID de la vidéo
    
    Returns:
        Détails complets de la vidéo
    """
    try:
        video = await VideoService.get_video(video_id)
        
        if not video:
            raise HTTPException(status_code=404, detail="Vidéo introuvable")
        
        return {
            "id": str(video.id),
            "_id": str(video.id),
            "filename": video.filename,
            "file_path": video.file_path,
            "annotated_path": video.annotated_path,
            "duration": video.duration,
            "fps": video.fps,
            "width": video.width,
            "height": video.height,
            "total_frames": video.total_frames,
            "status": video.status,
            "model_type": getattr(video, 'model_type', 'both'),
            "total_detections": video.total_detections,
            "unique_objects": video.unique_objects,
            "uploaded_at": video.uploaded_at,
            "processed_at": video.processed_at
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur récupération vidéo : {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== 6.5. STREAM VIDEO (NOUVEAU !) ==========
@router.get("/{video_id}/stream")
async def stream_video(video_id: str):
    """
    Streamer la vidéo annotée
    
    ✅ Gère les caractères spéciaux dans les noms de fichiers
    
    Returns:
        Fichier vidéo en streaming
    """
    try:
        import os
        
        video = await VideoService.get_video(video_id)
        
        if not video:
            raise HTTPException(status_code=404, detail="Vidéo introuvable")
        
        if not video.annotated_path:
            raise HTTPException(status_code=404, detail="Vidéo annotée non disponible")
        
        # Vérifier que le fichier existe
        if not os.path.exists(video.annotated_path):
            logger.error(f"❌ Fichier introuvable : {video.annotated_path}")
            raise HTTPException(status_code=404, detail="Fichier vidéo introuvable")
        
        logger.info(f"🎥 Streaming vidéo : {video.annotated_path}")
        
        return FileResponse(
            path=video.annotated_path,
            media_type="video/mp4",
            filename=video.filename
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur streaming vidéo : {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== 7. ATTENDANCE (MODIFIÉ !) ==========
@router.get("/{video_id}/attendance", response_model=dict)
async def get_video_attendance(video_id: str):
    """
    Obtenir le rapport de présence/absence pour une vidéo
    
    ✅ NOUVEAU : Retourne un rapport vide si model_type != employees/both
    
    Returns:
        Rapport avec employés présents, absents et taux de présence
    """
    try:
        # ✅ AJOUTÉ : Vérifier le model_type de la vidéo
        video = await VideoService.get_video(video_id)
        
        if not video:
            raise HTTPException(status_code=404, detail="Vidéo introuvable")
        
        video_model_type = getattr(video, 'model_type', 'both')
        
        # ✅ CONDITION : Calculer présence SEULEMENT si employees/both
        if video_model_type in ["employees", "both"]:
            logger.info(f"👥 Calcul présence pour vidéo {video_id} (model_type={video_model_type})")
            attendance = await VideoService.calculate_attendance(video_id)
            
            # ✅ NOUVEAU : Envoyer notifications si des absents
            if attendance.get("absent_count", 0) > 0:
                try:
                    from app.services.notification import NotificationService
                    await NotificationService.notify_absences(
                        video_id=video_id,
                        absent_employees=attendance["absent"]
                    )
                    logger.info(f"📧 {attendance['absent_count']} notifications d'absence envoyées")
                except ImportError:
                    logger.warning("⚠️ NotificationService non disponible")
                except Exception as e:
                    logger.warning(f"⚠️ Erreur envoi notifications : {e}")
            
            return attendance
        else:
            # ✅ RETOURNER RAPPORT VIDE si model_type = objects
            logger.info(f"⏭️ Pas de rapport de présence (model_type={video_model_type})")
            return {
                "total_employees": 0,
                "present": [],
                "present_count": 0,
                "absent": [],
                "absent_count": 0,
                "attendance_rate": 0,
                "message": f"Rapport non disponible pour model_type='{video_model_type}'"
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur récupération présence : {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== 8. DELETE ==========
@router.delete("/{video_id}")
async def delete_video(video_id: str):
    """Supprimer une vidéo"""
    try:
        success = await VideoService.delete_video(video_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Vidéo introuvable")
        
        return {"message": "Vidéo supprimée avec succès", "video_id": video_id}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur suppression vidéo : {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== 9. LIST (À LA TOUTE FIN !) ==========
@router.get("/", response_model=List[dict])
async def list_videos(
    status: Optional[app.models.video.VideoStatus] = None,
    limit: int = Query(100, ge=1, le=500),
    skip: int = Query(0, ge=0)
):
    """
    
    - **status**: Filtrer par statut (uploaded, processing, completed, failed)
    - **limit**: Nombre maximum de résultats
    - **skip**: Nombre de résultats à sauter
    
    Returns:
    """
    try:
        videos = await VideoService.list_videos(status=status, limit=limit, skip=skip)
        
        return [
            {
                "id": str(video.id),
                "_id": str(video.id),
                "filename": video.filename,
                "duration": video.duration,
                "fps": video.fps,
                "total_frames": video.total_frames,
                "resolution": f"{video.width}x{video.height}",
                "status": video.status,
                "model_type": getattr(video, 'model_type', 'both'),
                "total_detections": video.total_detections,
                "unique_objects": video.unique_objects,
                "created_at": video.uploaded_at,
                "uploaded_at": video.uploaded_at,
                "processed_at": video.processed_at
            }
            for video in videos
        ]
    
    except Exception as e:
        logger.error(f"❌ Erreur listage vidéos : {e}")
        raise HTTPException(status_code=500, detail=str(e))
