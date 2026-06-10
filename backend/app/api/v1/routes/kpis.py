from fastapi import APIRouter, HTTPException
from typing import List, Optional
from app.models.kpi import KPISnapshot
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import logging
import os

router = APIRouter()
logger = logging.getLogger(__name__)

# ==========================================
# 🔌 CONNEXION MONGODB
# ==========================================

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "camia_factory")

client = AsyncIOMotorClient(MONGODB_URL)
database = client[DATABASE_NAME]
kpis_collection = database["kpis"]


# ==========================================
# 💾 SAUVEGARDE KPI - ✅ CORRIGÉE
# ==========================================

@router.post("/save", status_code=201)
async def save_kpi(kpi_data: KPISnapshot):
    """
    Sauvegarde ou met à jour un snapshot KPI
    ✅ FIX: Maintenant utilise video_analysis_id ET periode comme clé unique
    - Si (video_analysis_id + periode) existe : update
    - Sinon : création nouveau document
    """
    try:
        # Convertir en dict et ne garder que les champs fournis
        kpi_dict = kpi_data.dict(exclude_unset=True, exclude_none=True)
        
        # Ajouter timestamp de création si nouveau
        if "created_at" not in kpi_dict:
            kpi_dict["created_at"] = datetime.now()
        
        # Convertir les datetimes en ISO string pour MongoDB
        for date_field in ["date", "date_debut", "date_fin", "created_at"]:
            if date_field in kpi_dict and kpi_dict[date_field]:
                if isinstance(kpi_dict[date_field], datetime):
                    kpi_dict[date_field] = kpi_dict[date_field].isoformat()
        
        # ✅ FIX: Chercher par video_analysis_id ET periode
        if kpi_data.video_analysis_id and kpi_data.periode:
            
            # Créer la clé composite unique
            query_filter = {
                "video_analysis_id": kpi_data.video_analysis_id,
                "periode": kpi_data.periode  # ✅ AJOUT CRITIQUE
            }
            
            result = await kpis_collection.update_one(
                query_filter,
                {"$set": kpi_dict},
                upsert=True
            )
            
            if result.upserted_id:
                logger.info(f"✅ KPI créé : {result.upserted_id} (vidéo: {kpi_data.video_analysis_id}, période: {kpi_data.periode})")
                return {
                    "message": "KPI créé avec succès",
                    "id": str(result.upserted_id),
                    "video_analysis_id": kpi_data.video_analysis_id,
                    "periode": kpi_data.periode
                }
            else:
                logger.info(f"✅ KPI mis à jour pour vidéo {kpi_data.video_analysis_id} (période: {kpi_data.periode})")
                return {
                    "message": "KPI mis à jour avec succès",
                    "video_analysis_id": kpi_data.video_analysis_id,
                    "periode": kpi_data.periode
                }
        else:
            # Créer nouveau document sans video_analysis_id
            result = await kpis_collection.insert_one(kpi_dict)
            logger.info(f"✅ KPI créé : {result.inserted_id}")
            return {
                "message": "KPI créé avec succès",
                "id": str(result.inserted_id)
            }
            
    except Exception as e:
        logger.error(f"❌ Erreur sauvegarde KPI: {str(e)}")
        logger.error(f"📦 Données reçues: {kpi_data.dict()}")
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")


# ==========================================
# 📖 RÉCUPÉRATION KPI
# ==========================================

@router.get("/history/{video_analysis_id}")
async def get_kpi_history(video_analysis_id: str):
    """Récupère l'historique KPI d'une vidéo spécifique (toutes les périodes)"""
    try:
        kpis = await kpis_collection.find(
            {"video_analysis_id": video_analysis_id}
        ).sort("created_at", -1).to_list(length=100)
        
        # Convertir ObjectId en string
        for kpi in kpis:
            kpi["_id"] = str(kpi["_id"])
        
        return {"data": kpis, "count": len(kpis)}
    except Exception as e:
        logger.error(f"❌ Erreur récupération historique: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/latest")
async def get_latest_kpi(periode: Optional[str] = None):
    """
    Récupère le dernier KPI sauvegardé 
    ✅ FIX: Utilise aggregation pipeline au lieu de find_one + sort
    - Si periode fournie : filtre par période
    - Sinon : retourne le dernier peu importe la période
    """
    try:
        query = {}
        if periode:
            query["periode"] = periode
            logger.info(f"🔍 Recherche KPI avec période: {periode}")
        
        # ✅ Utiliser aggregation pipeline pour plus de fiabilité
        pipeline = [
            {"$match": query},
            {"$sort": {"created_at": -1}},
            {"$limit": 1}
        ]
        
        results = await kpis_collection.aggregate(pipeline).to_list(length=1)
        
        if not results:
            logger.warning(f"⚠️ Aucun KPI trouvé pour la requête: {query}")
            raise HTTPException(status_code=404, detail=f"Aucun KPI trouvé {f'pour période {periode}' if periode else ''}")
        
        kpi = results[0]
        kpi["_id"] = str(kpi["_id"])
        logger.info(f"✅ KPI trouvé : {kpi.get('_id')} (période: {kpi.get('periode')})")
        return {"data": kpi}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur récupération dernier KPI: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{kpi_id}")
async def delete_kpi(kpi_id: str):
    """Supprime un KPI spécifique"""
    try:
        from bson import ObjectId
        
        result = await kpis_collection.delete_one({"_id": ObjectId(kpi_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="KPI non trouvé")
        
        logger.info(f"🗑️ KPI supprimé : {kpi_id}")
        return {"message": "KPI supprimé avec succès"}
    except Exception as e:
        logger.error(f"❌ Erreur suppression KPI: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# 🔄 ROUTES DE COMPATIBILITÉ (anciennes)
# ==========================================

@router.get("/global/today")
async def get_kpi_global_today(periode: str = "jour"):
    """
    Route de compatibilité pour l'ancien système
    Redirige vers /latest avec la période appropriée
    
    Anciennes périodes (français) → Nouvelles périodes (anglais):
    - heure → hour
    - jour → day
    - semaine → week
    - mois → month
    """
    try:
        # Mapper les anciennes périodes vers les nouvelles
        periode_map = {
            "heure": "hour",
            "jour": "day",
            "semaine": "week",
            "mois": "month"
        }
        
        new_periode = periode_map.get(periode, "day")
        
        logger.info(f"📍 Route compatibilité: {periode} → {new_periode}")
        
        # Appeler la nouvelle route
        return await get_latest_kpi(periode=new_periode)
        
    except HTTPException as e:
        # Si aucun KPI trouvé, retourner une structure vide compatible
        if e.status_code == 404:
            logger.warning(f"⚠️ Aucun KPI trouvé pour période {periode}")
            return {
                "data": None,
                "message": f"Aucun KPI disponible pour la période {periode}",
                "status": "not_found"
            }
        raise
    except Exception as e:
        logger.error(f"❌ Erreur route de compatibilité: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/week")
async def get_kpi_week():
    """Route de compatibilité pour /week"""
    logger.info("📍 Route compatibilité: /week")
    try:
        return await get_latest_kpi(periode="week")
    except HTTPException as e:
        if e.status_code == 404:
            return {
                "data": None,
                "message": "Aucun KPI disponible pour la semaine",
                "status": "not_found"
            }
        raise


@router.get("/month")
async def get_kpi_month():
    """Route de compatibilité pour /month"""
    logger.info("📍 Route compatibilité: /month")
    try:
        return await get_latest_kpi(periode="month")
    except HTTPException as e:
        if e.status_code == 404:
            return {
                "data": None,
                "message": "Aucun KPI disponible pour le mois",
                "status": "not_found"
            }
        raise


# ==========================================
# 📊 ROUTES SUPPLÉMENTAIRES (optionnelles)
# ==========================================

@router.get("/videos/{video_id}/calculate")
async def calculate_kpi_for_video(video_id: str):
    """
    Route de compatibilité pour calcul KPI d'une vidéo
    NOTE: Le calcul se fait maintenant côté frontend
    """
    logger.warning(f"⚠️ Route dépréciée appelée: /videos/{video_id}/calculate")
    
    # Chercher si un KPI existe déjà pour cette vidéo
    try:
        kpi = await kpis_collection.find_one(
            {"video_analysis_id": video_id},
            sort=[("created_at", -1)]
        )
        
        if kpi:
            kpi["_id"] = str(kpi["_id"])
            return {
                "data": kpi,
                "message": "KPI récupéré depuis la base de données",
                "note": "Le calcul KPI se fait maintenant côté frontend"
            }
        else:
            return {
                "data": None,
                "message": "Aucun KPI trouvé pour cette vidéo",
                "note": "Rechargez le dashboard frontend pour calculer les KPIs"
            }
            
    except Exception as e:
        logger.error(f"❌ Erreur récupération KPI vidéo: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/all")
async def get_all_kpis(limit: int = 50, skip: int = 0):
    """Récupère tous les KPIs avec pagination"""
    try:
        kpis = await kpis_collection.find().sort(
            "created_at", -1
        ).skip(skip).limit(limit).to_list(length=limit)
        
        total = await kpis_collection.count_documents({})
        
        # Convertir ObjectId en string
        for kpi in kpis:
            kpi["_id"] = str(kpi["_id"])
        
        return {
            "data": kpis,
            "total": total,
            "limit": limit,
            "skip": skip,
            "count": len(kpis)
        }
    except Exception as e:
        logger.error(f"❌ Erreur récupération tous KPIs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))