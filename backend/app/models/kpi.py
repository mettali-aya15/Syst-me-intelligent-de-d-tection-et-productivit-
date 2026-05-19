#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modèles Pydantic pour les KPI
Sections optionnelles selon les détections
AVEC KPI Tables et Clients
AVEC périodes dynamiques : heure, jour, semaine, mois
"""

from pydantic import BaseModel, Field, BeforeValidator
from typing import Optional, Annotated, Literal
from datetime import datetime
from bson import ObjectId

# Convertisseur PyObjectId pour Pydantic v2
PyObjectId = Annotated[str, BeforeValidator(lambda x: str(x) if isinstance(x, ObjectId) else x)]


class KPIProductionComplete(BaseModel):
    """KPI Production complets"""
    taux_productivite: float
    objectif_production: float
    taux_conformite: float
    cadence_production: float
    unites_produites: int
    objectif_unites: int
    produits_conformes: int
    total_produits: int


class KPIMachinesComplete(BaseModel):
    """KPI Machines complets"""
    trs: float
    disponibilite: float
    performance: float
    qualite: float
    taux_panne: float
    mtbf: float
    mttr: float
    total_machines: int
    machines_actives: int
    machines_arretees: int
    temps_productif: float
    temps_total: float


class KPIEmployesComplete(BaseModel):
    """KPI Employés complets"""
    taux_presence: float
    taux_activite: float
    productivite_par_employe: float
    taux_inactivite: float
    total_employes: int
    employes_presents: int
    employes_actifs: int
    employes_inactifs: int


class KPITablesComplete(BaseModel):
    """KPI Tables complets"""
    total_tables: int
    tables_occupees: int
    tables_vides: int
    taux_occupation: float


class KPIClientsComplete(BaseModel):
    """KPI Clients complets"""
    total_clients: int
    clients_en_attente: int
    clients_servis: int
    taux_service: float


class KPIGlobal(BaseModel):
    """
    KPI Global avec sections OPTIONNELLES
    Les sections sont présentes uniquement si les objets correspondants sont détectés
    
    PÉRIODES SUPPORTÉES :
    - "heure" : KPI d'une heure spécifique (ex: 14h-15h)
    - "jour" : KPI d'une journée (ex: 12 mai 2026)
    - "semaine" : KPI d'une semaine (ex: semaine 19/2026)
    - "mois" : KPI d'un mois (ex: mai 2026)
    """
    id: Optional[PyObjectId] = Field(None, alias="_id")
    date: datetime
    
    # ✅ NOUVEAU : Type de période
    periode: Literal["heure", "jour", "semaine", "mois"] = Field(
        ..., 
        description="Type de période: heure, jour, semaine ou mois"
    )
    
    date_debut: datetime
    date_fin: datetime
    
    # Sections optionnelles
    production: Optional[KPIProductionComplete] = None
    machines: Optional[KPIMachinesComplete] = None
    employes: Optional[KPIEmployesComplete] = None
    tables: Optional[KPITablesComplete] = None
    clients: Optional[KPIClientsComplete] = None
    
    nombre_videos: int
    created_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


# ========== CLASSES POUR LES RAPPORTS ==========

class KPISnapshot(BaseModel):
    """Snapshot des KPI pour un rapport"""
    production: Optional[KPIProductionComplete] = None
    machines: Optional[KPIMachinesComplete] = None
    employes: Optional[KPIEmployesComplete] = None
    tables: Optional[KPITablesComplete] = None
    clients: Optional[KPIClientsComplete] = None


class DailyReport(BaseModel):
    """Rapport quotidien"""
    id: Optional[PyObjectId] = Field(None, alias="_id")
    date: datetime
    kpi: KPISnapshot
    summary: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}