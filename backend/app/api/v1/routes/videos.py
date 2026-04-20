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

from app.services.video import VideoService
import app.models.video

import logging
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/upload", response_model=dict)
async def upload_video(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """
    Upload une vidéo
    
    - **file**: Fichier vidéo (mp4, avi, mov)
    
    Returns:
        Informations de la vidéo uploadée
    """
    # Vérifier l'extension
    allowed_extensions = [".mp4", ".avi", ".mov", ".mkv"]
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Extension non supportée. Extensions acceptées : {', '.join(allowed_extensions)}"
        )
    
    # Sauvegarder temporairement
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            tmp_path = tmp_file.name
        
        # Enregistrer en DB
        result = await VideoService.upload_video(tmp_path, file.filename)
        
        logger.info(f"✅ Vidéo uploadée : {result['video_id']}")
        
        return result
    
    except Exception as e:
        logger.error(f"❌ Erreur upload vidéo : {e}")
        raise HTTPException(status_code=500, detail=f"Erreur upload : {str(e)}")
    
    finally:
        file.file.close()


@router.post("/{video_id}/process", response_model=dict)
async def process_video(
    video_id: str,
    confidence: Optional[float] = Query(None, ge=0.1, le=1.0),
    model_type: Optional[str] = Query("both", pattern="^(employees|objects|both)$")  # ✅ pattern au lieu de regex
):
    """
    Traiter une vidéo (détection YOLO)
    
    - **video_id**: ID de la vidéo
    - **confidence**: Seuil de confiance (optionnel, défaut: 0.5)
    - **model_type**: Type de modèle à utiliser
        - "employees": Uniquement détection employés
        - "objects": Uniquement détection objets  
        - "both": Les deux modèles (défaut)
    
    Returns:
        Résultats du traitement
    """
    try:
        result = await VideoService.process_video(
            video_id=video_id,
            confidence=confidence,
            model_type=model_type
        )
        
        return result
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Erreur traitement vidéo : {e}")
        raise HTTPException(status_code=500, detail=f"Erreur traitement : {str(e)}")


@router.get("/", response_model=List[dict])
async def list_videos(
    status: Optional[app.models.video.VideoStatus] = None,
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0)
):
    """
    Lister les vidéos
    
    - **status**: Filtrer par statut (uploaded, processing, completed, failed)
    - **limit**: Nombre maximum de résultats
    - **skip**: Nombre de résultats à sauter
    
    Returns:
        Liste des vidéos
    """
    try:
        videos = await VideoService.list_videos(status=status, limit=limit, skip=skip)
        
        return [
            {
                "id": str(video.id),
                "filename": video.filename,
                "duration": video.duration,
                "fps": video.fps,
                "resolution": f"{video.width}x{video.height}",
                "status": video.status,
                "total_detections": video.total_detections,
                "uploaded_at": video.uploaded_at,
                "processed_at": video.processed_at
            }
            for video in videos
        ]
    
    except Exception as e:
        logger.error(f"❌ Erreur listage vidéos : {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{video_id}", response_model=dict)
async def get_video(video_id: str):
    """
    Obtenir les détails d'une vidéo
    
    - **video_id**: ID de la vidéo
    
    Returns:
        Détails de la vidéo
    """
    try:
        video = await VideoService.get_video(video_id)
        
        if not video:
            raise HTTPException(status_code=404, detail="Vidéo introuvable")
        
        return {
            "id": str(video.id),
            "filename": video.filename,
            "file_path": video.file_path,
            "annotated_path": video.annotated_path,
            "duration": video.duration,
            "fps": video.fps,
            "width": video.width,
            "height": video.height,
            "total_frames": video.total_frames,
            "status": video.status,
            "total_detections": video.total_detections,
            "summary": video.summary,
            "unique_objects": video.unique_objects,  # ✅ AJOUTÉ
            "uploaded_at": video.uploaded_at,
            "processed_at": video.processed_at
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur récupération vidéo : {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{video_id}/download")
async def download_video(video_id: str, annotated: bool = False):
    """
    Télécharger une vidéo
    
    - **video_id**: ID de la vidéo
    - **annotated**: Télécharger la version annotée (défaut: false)
    
    Returns:
        Fichier vidéo
    """
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


@router.delete("/{video_id}")
async def delete_video(video_id: str):
    """
    Supprimer une vidéo
    
    - **video_id**: ID de la vidéo
    
    Returns:
        Message de confirmation
    """
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
@router.patch("/{video_id}/correct-counts")
async def correct_object_counts(
    video_id: str,
    corrected_counts: dict
):
    """
    Corriger manuellement le comptage d'objets
    
    Body:
    {
        "employé": 12,
        "machine": 2,
        "produit": 50
    }
    """
    try:
        result = await VideoService.manually_correct_counts(video_id, corrected_counts)
        return result
    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        raise HTTPException(status_code=500, detail=str(e))