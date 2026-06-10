from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ==========================================
# 📊 MODÈLES KPI PAR SECTION
# ==========================================

class ProductionKPI(BaseModel):
    taux_productivite: float = 0.0
    objectif_production: int = 1000
    taux_conformite: float = 95.0
    cadence_production: float = 0.0
    unites_produites: int = 0
    objectif_unites: int = 1000
    produits_conformes: int = 0
    total_produits: int = 0


class MachinesKPI(BaseModel):
    trs: float = 0.0
    disponibilite: float = 0.0
    performance: float = 0.0
    qualite: float = 0.0
    taux_panne: float = 0.0
    mtbf: float = 0.0
    mttr: float = 45.0
    total_machines: int = 0
    machines_actives: int = 0
    machines_arretees: int = 0
    temps_productif: float = 0.0
    temps_total: float = 0.0


class EmployesKPI(BaseModel):
    taux_presence: float = 100.0
    taux_activite: float = 0.0
    productivite_par_employe: float = 0.0
    taux_inactivite: float = 0.0
    total_employes: int = 0
    employes_presents: int = 0
    employes_actifs: int = 0
    employes_inactifs: int = 0


class TablesKPI(BaseModel):
    total_tables: int = 0
    tables_occupees: int = 0
    tables_vides: int = 0
    taux_occupation: float = 0.0


class ClientsKPI(BaseModel):
    total_clients: int = 0
    clients_en_attente: int = 0
    clients_servis: int = 0
    taux_service: float = 0.0


# ==========================================
# 📦 MODÈLE PRINCIPAL KPI SNAPSHOT
# ==========================================

class KPISnapshot(BaseModel):
    """
    Snapshot complet des KPIs à un instant donné
    Tous les champs sont optionnels sauf periode
    """
    # Métadonnées (optionnelles)
    video_analysis_id: Optional[str] = None
    periode: str = "video"  # video, hour, day, week, month
    date_debut: Optional[datetime] = None
    date_fin: Optional[datetime] = None
    
    # Sections KPI (toutes optionnelles)
    production: Optional[ProductionKPI] = None
    machines: Optional[MachinesKPI] = None
    employes: Optional[EmployesKPI] = None
    tables: Optional[TablesKPI] = None
    clients: Optional[ClientsKPI] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }