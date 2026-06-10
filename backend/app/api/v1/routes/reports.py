from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from datetime import datetime
from bson import ObjectId
import base64
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()


class RapportRequest(BaseModel):
    """Modèle pour sauvegarder un rapport"""
    video_id: str
    periode: str
    pdf_base64: str
    kpi_snapshot: dict


@router.get("/daily/export")
async def export_daily_report(target_date: str, format: str = "json"):
    """Exporter un rapport journalier"""
    try:
        return {"status": "ok", "date": target_date, "format": format}
    except Exception as e:
        logger.error(f"❌ Erreur export rapport : {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/productivity/chart-data")
async def get_productivity_chart_data(start_date: str, end_date: str):
    """Obtenir les données pour graphique de productivité"""
    try:
        return {"status": "ok", "start": start_date, "end": end_date}
    except Exception as e:
        logger.error(f"❌ Erreur données graphique : {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate/custom")
async def generate_custom_report(report_data: dict, format: str = "json"):
    """Générer un rapport personnalisé"""
    try:
        return {"status": "ok", "format": format}
    except Exception as e:
        logger.error(f"❌ Erreur génération rapport personnalisé : {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rapports/save")
async def save_rapport(data: RapportRequest):
    """Sauvegarder un rapport PDF généré"""
    try:
        # 1️⃣ Créer le dossier rapports
        from app.core.config import settings
        rapports_dir = Path(settings.UPLOAD_DIR).parent / "rapports"
        rapports_dir.mkdir(parents=True, exist_ok=True)
        
        # 2️⃣ Générer le nom du fichier
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        filename = f"CAMIA_Rapport_{timestamp}.pdf"
        filepath = rapports_dir / filename
        
        # 3️⃣ Décoder et sauvegarder le PDF
        print(f"📥 Décodage PDF... (taille base64: {len(data.pdf_base64)} caractères)")
        pdf_bytes = base64.b64decode(data.pdf_base64)
        print(f"✅ Décodé: {len(pdf_bytes)} bytes")
        
        with open(filepath, 'wb') as f:
            f.write(pdf_bytes)
        
        print(f"💾 Fichier sauvegardé: {filepath}")
        
        # 4️⃣ Sauvegarder dans MongoDB
        from app.core.database import Database
        database = Database.get_collection("rapports")
        
        rapport_doc = {
            "video_id": ObjectId(data.video_id) if data.video_id and data.video_id != 'projected' else data.video_id,
            "filename": filename,
            "file_path": str(filepath),
            "file_size": len(pdf_bytes),
            "periode": data.periode,
            "kpi_snapshot": data.kpi_snapshot,
            "generated_at": datetime.utcnow(),
            "download_count": 0,
            "last_downloaded_at": None
        }
        
        result = await database.insert_one(rapport_doc)
        logger.info(f"✅ Rapport sauvegardé MongoDB : {result.inserted_id}")
        
        return {
            "rapport_id": str(result.inserted_id),
            "filename": filename,
            "download_url": f"/api/v1/reports/rapports/{result.inserted_id}/download",
            "generated_at": rapport_doc["generated_at"].isoformat()
        }
    
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        logger.error(f"❌ Erreur sauvegarde rapport : {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rapports/")
async def get_rapports():
    """Lister tous les rapports"""
    try:
        from app.core.database import Database
        database = Database.get_collection("rapports")
        rapports = await database.find({}).sort("generated_at", -1).to_list(None)
        
        return [
            {
                "id": str(r["_id"]),
                "filename": r["filename"],
                "periode": r.get("periode"),
                "generated_at": r["generated_at"].isoformat() if r.get("generated_at") else None,
                "download_count": r.get("download_count", 0)
            }
            for r in rapports
        ]
    
    except Exception as e:
        logger.error(f"❌ Erreur récupération rapports : {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rapports/{rapport_id}/download")
async def download_rapport(rapport_id: str):
    """Télécharger un rapport"""
    try:
        from app.core.database import Database
        database = Database.get_collection("rapports")
        rapport = await database.find_one({"_id": ObjectId(rapport_id)})
        
        if not rapport:
            raise HTTPException(status_code=404, detail="Rapport non trouvé")
        
        filepath = Path(rapport["file_path"])
        
        if not filepath.exists():
            raise HTTPException(status_code=404, detail="Fichier non trouvé")
        
        # Incrémenter le compteur
        await database.update_one(
            {"_id": ObjectId(rapport_id)},
            {
                "$set": {
                    "download_count": rapport.get("download_count", 0) + 1,
                    "last_downloaded_at": datetime.utcnow()
                }
            }
        )
        
        return FileResponse(
            path=filepath,
            media_type="application/pdf",
            filename=rapport["filename"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur téléchargement rapport : {e}")
        raise HTTPException(status_code=500, detail=str(e))
