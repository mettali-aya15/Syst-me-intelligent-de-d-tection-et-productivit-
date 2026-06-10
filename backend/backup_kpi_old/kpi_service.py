#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Service KPI par Vidéo avec sections optionnelles
Calcule les KPI pour UNE vidéo spécifique avec PROJECTION selon la période
AVEC SAUVEGARDE AUTOMATIQUE DANS MONGODB
AVEC KPI Tables et Clients
AVEC PÉRIODES DYNAMIQUES: heure, jour, semaine, mois
"""
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from bson import ObjectId
from app.models.kpi import (
    KPIGlobal,
    KPIProductionComplete,
    KPIMachinesComplete,
    KPIEmployesComplete,
    KPITablesComplete,
    KPIClientsComplete
)
from app.core.database import Database
import logging

logger = logging.getLogger(__name__)


class KPIService:
    """Service de calcul des KPI pour une vidéo individuelle avec projection temporelle"""
    
    @staticmethod
    async def calculate_kpi_for_video(
        video_id: str,
        periode: str = "heure"
    ) -> KPIGlobal:
        """
        Calculer les KPI pour UNE vidéo spécifique avec PROJECTION selon la période
        """
        logger.info(f"📊 Calcul KPI pour vidéo {video_id} - Période: {periode}")
        
        videos_collection = Database.get_collection("video_uploads")
        video = await videos_collection.find_one({"_id": ObjectId(video_id)})
        
        if not video:
            raise ValueError(f"Vidéo {video_id} non trouvée")
        if video.get('status') != 'completed':
            raise ValueError(f"Vidéo {video_id} non processée")
        
        unique_objects = video.get('unique_objects', {})
        
        # ✅ CALCULER LE FACTEUR DE PROJECTION SELON LA PÉRIODE
        duree_video = video.get('duration', 30)
        if duree_video <= 0: duree_video = 30
        
        facteur_projection = KPIService._get_projection_factor(periode, duree_video)
        logger.info(f"📈 Facteur de projection ({periode}): {facteur_projection}x")
        
        # Vérifier ce qui existe
        has_products = unique_objects.get('produit', 0) > 0
        has_machines = unique_objects.get('machine', 0) > 0
        has_employees = unique_objects.get('employé', 0) > 0 or unique_objects.get('employe', 0) > 0
        has_tables = unique_objects.get('tables', 0) > 0 or unique_objects.get('tables_vides', 0) > 0
        has_clients = unique_objects.get('client', 0) > 0
        
        # Calculer les KPI avec projection
        production_kpi = await KPIService._calculate_production_kpi(video, facteur_projection) if has_products else None
        machines_kpi = await KPIService._calculate_machines_kpi(video) if has_machines else None
        employes_kpi = await KPIService._calculate_employes_kpi(video, production_kpi.unites_produites if production_kpi else 0) if has_employees else None
        tables_kpi = await KPIService._calculate_tables_kpi(video) if has_tables else None
        clients_kpi = await KPIService._calculate_clients_kpi(video, facteur_projection) if has_clients else None
        
        # Dates selon la période
        date_debut, date_fin = KPIService._get_period_dates(periode)
        
        kpi_global = KPIGlobal(
            date=datetime.now(),
            periode=periode,  # ✅ Utilise le paramètre
            date_debut=date_debut,
            date_fin=date_fin,
            production=production_kpi,
            machines=machines_kpi,
            employes=employes_kpi,
            tables=tables_kpi,
            clients=clients_kpi,
            nombre_videos=1
        )
        
        await KPIService._save_kpi_global(kpi_global)
        return kpi_global
    
    @staticmethod
    async def calculate_kpi_global(
        periode: str = "jour",
        date_debut: Optional[datetime] = None,
        date_fin: Optional[datetime] = None
    ) -> KPIGlobal:
        """
        ✅ MÉTHODE MANQUANTE AJOUTÉE
        Calculer les KPI pour la DERNIÈRE vidéo processée avec projection
        """
        logger.info(f"📊 Calcul KPI global période : {periode}")
        
        videos_collection = Database.get_collection("video_uploads")
        video = await videos_collection.find_one(
            {"status": "completed"},
            sort=[("processed_at", -1)]
        )
        
        if not video:
            raise ValueError("Aucune vidéo processée trouvée")
        
        video_id = str(video['_id'])
        logger.info(f"📹 Dernière vidéo : {video.get('filename')} (ID: {video_id})")
        
        # ✅ Appelle calculate_kpi_for_video avec la période
        return await KPIService.calculate_kpi_for_video(video_id, periode=periode)
    
    @staticmethod
    def _get_projection_factor(periode: str, duree_video_secondes: float) -> float:
        """Calculer le facteur de projection selon la période"""
        if duree_video_secondes <= 0:
            duree_video_secondes = 30
        
        projections = {
            "heure": 3600,
            "jour": 86400,
            "semaine": 604800,
            "mois": 2592000
        }
        
        duree_cible = projections.get(periode, 86400)
        return round(duree_cible / duree_video_secondes, 2)
    
    @staticmethod
    def _get_period_dates(periode: str):
        """Obtenir les dates de début et fin selon la période"""
        now = datetime.now()
        
        if periode == "heure":
            date_debut = now.replace(minute=0, second=0, microsecond=0)
            date_fin = date_debut + timedelta(hours=1)
        elif periode == "jour":
            date_debut = now.replace(hour=0, minute=0, second=0, microsecond=0)
            date_fin = date_debut + timedelta(days=1)
        elif periode == "semaine":
            days_since_monday = now.weekday()
            date_debut = (now - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
            date_fin = date_debut + timedelta(weeks=1)
        elif periode == "mois":
            date_debut = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if now.month == 12:
                date_fin = now.replace(year=now.year+1, month=1, day=1)
            else:
                date_fin = now.replace(month=now.month+1, day=1)
        else:
            date_debut = now.replace(hour=0, minute=0, second=0, microsecond=0)
            date_fin = date_debut + timedelta(days=1)
        
        return date_debut, date_fin
    
    @staticmethod
    async def _calculate_production_kpi(video: Dict, facteur_projection: float = 1.0) -> KPIProductionComplete:
        """Calculer les KPI de production avec projection"""
        unique_objects = video.get('unique_objects', {})
        summary = video.get('summary', {})
        
        total_produits = unique_objects.get('produit', 0) or summary.get('produit', 0) or 0
        total_produits_projetes = int(total_produits * facteur_projection)
        produits_conformes = int(total_produits_projetes * 0.95)
        
        duree = video.get('duration', 30)
        total_duree_heures = duree / 3600 if duree > 0 else 1
        objectif_unites = 1000 * facteur_projection
        
        taux_productivite = total_produits_projetes / total_duree_heures if total_duree_heures > 0 else 0
        objectif_production = min((total_produits_projetes / objectif_unites) * 100, 100) if objectif_unites > 0 else 0
        taux_conformite = (produits_conformes / total_produits_projetes) * 100 if total_produits_projetes > 0 else 100
        cadence_production = total_produits_projetes / (total_duree_heures * 60) if total_duree_heures > 0 else 0
        
        return KPIProductionComplete(
            taux_productivite=round(taux_productivite, 1),
            objectif_production=round(objectif_production, 1),
            taux_conformite=round(taux_conformite, 1),
            cadence_production=round(cadence_production, 2),
            unites_produites=total_produits_projetes,
            objectif_unites=objectif_unites,
            produits_conformes=produits_conformes,
            total_produits=total_produits_projetes
        )
    
    @staticmethod
    async def _calculate_machines_kpi(video: Dict) -> KPIMachinesComplete:
        """Calculer les KPI machines"""
        unique_objects = video.get('unique_objects', {})
        machines = unique_objects.get('machine', 0) or 0
        machines_arret = unique_objects.get('machine arrêtée', 0) or unique_objects.get('machine arretee', 0) or 0
        
        if machines > 0 and machines_arret > 0:
            total_machines = machines
            machines_actives = machines - machines_arret
            machines_arretees = machines_arret
        elif machines > 0:
            total_machines = machines
            machines_actives = machines
            machines_arretees = 0
        else:
            total_machines = machines_arret
            machines_actives = 0
            machines_arretees = machines_arret
        
        duree_secondes = video.get('duration', 30)
        temps_total_minutes = duree_secondes / 60
        temps_total_heures = duree_secondes / 3600
        
        disponibilite = 100.0 if machines_arretees == 0 else ((machines_actives / total_machines) * 100 if total_machines > 0 else 100)
        performance = 90.0
        qualite = 95.0
        trs = (disponibilite / 100) * (performance / 100) * (qualite / 100) * 100
        
        return KPIMachinesComplete(
            trs=round(trs, 1),
            disponibilite=round(disponibilite, 1),
            performance=round(performance, 1),
            qualite=round(qualite, 1),
            taux_panne=(machines_arretees/total_machines*100) if total_machines>0 else 0,
            mtbf=temps_total_heures,
            mttr=45.0,
            total_machines=total_machines,
            machines_actives=machines_actives,
            machines_arretees=machines_arretees,
            temps_productif=temps_total_minutes,
            temps_total=temps_total_minutes
        )
    
    @staticmethod
    async def _calculate_employes_kpi(video: Dict, unites_produites: int) -> KPIEmployesComplete:
        """Calculer les KPI employés"""
        unique_objects = video.get('unique_objects', {})
        employes_actifs = unique_objects.get('employé', 0) or unique_objects.get('employe', 0) or 0
        employes_inactifs = unique_objects.get('employé inactif', 0) or unique_objects.get('employe inactif', 0) or 0
        
        total_employes = employes_actifs + employes_inactifs if employes_actifs > 0 or employes_inactifs > 0 else 1
        taux_activite = (employes_actifs / total_employes * 100) if total_employes > 0 else 0
        
        return KPIEmployesComplete(
            taux_presence=100.0,
            taux_activite=round(taux_activite, 1),
            productivite_par_employe=unites_produites/employes_actifs if employes_actifs>0 else 0,
            taux_inactivite=(employes_inactifs/total_employes*100) if total_employes>0 else 0,
            total_employes=total_employes,
            employes_presents=total_employes,
            employes_actifs=employes_actifs,
            employes_inactifs=employes_inactifs
        )
    
    @staticmethod
    async def _calculate_tables_kpi(video: Dict) -> KPITablesComplete:
        """Calculer les KPI tables"""
        unique_objects = video.get('unique_objects', {})
        total = unique_objects.get('tables', 0) or 0
        vides = unique_objects.get('tables_vides', 0) or 0
        occupees = max(0, total - vides)
        taux = (occupees / total * 100) if total > 0 else 0
        
        return KPITablesComplete(total_tables=total, tables_occupees=occupees, tables_vides=vides, taux_occupation=round(taux, 1))
    
    @staticmethod
    async def _calculate_clients_kpi(video: Dict, facteur_projection: float = 1.0) -> KPIClientsComplete:
        """Calculer les KPI clients avec projection"""
        unique_objects = video.get('unique_objects', {})
        clients = unique_objects.get('client', 0) or 0
        clients_projetes = int(clients * facteur_projection)
        
        return KPIClientsComplete(
            total_clients=clients_projetes,
            clients_en_attente=int(clients_projetes * 0.1),
            clients_servis=int(clients_projetes * 0.9),
            taux_service=90.0
        )
    
    @staticmethod
    async def _save_kpi_global(kpi: KPIGlobal) -> str:
        """Sauvegarder un KPI Global dans MongoDB"""
        kpi_collection = Database.get_collection("kpi_global")
        kpi_dict = kpi.model_dump(by_alias=True, exclude={"id"}, exclude_none=True)
        result = await kpi_collection.insert_one(kpi_dict)
        logger.info(f"💾 KPI Global sauvegardé : {result.inserted_id}")
        return str(result.inserted_id)
    
    @staticmethod
    async def get_kpi_history(days: int = 30, periode: Optional[str] = None) -> List[KPIGlobal]:
        """Récupérer l'historique des KPI"""
        kpi_collection = Database.get_collection("kpi_global")
        query = {"date": {"$gte": datetime.now() - timedelta(days=days)}}
        if periode:
            query["periode"] = periode
        
        cursor = kpi_collection.find(query).sort("date", -1)
        kpi_list = await cursor.to_list(length=None)
        return [KPIGlobal(**kpi) for kpi in kpi_list]
    
    @staticmethod
    async def get_latest_kpi(periode: str = "jour") -> Optional[KPIGlobal]:
        """Récupérer le KPI le plus récent"""
        kpi_collection = Database.get_collection("kpi_global")
        kpi_dict = await kpi_collection.find_one({"periode": periode}, sort=[("date", -1)])
        return KPIGlobal(**kpi_dict) if kpi_dict else None