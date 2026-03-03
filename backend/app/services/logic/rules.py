from datetime import datetime
from app.models.workstation import Workstation
from app.services.workstation_service import get_workstation_by_id

class WorkstationRules:
    """
    Règles métier pour les workstations
    """
    
    @staticmethod
    def is_workstation_productive(workstation_id: int, start_time: datetime, end_time: datetime) -> bool:
        """
        Vérifie si une workstation est productive sur une période
        """
        # Logique pour déterminer si la workstation est productive
        # (à implémenter selon votre système)
        return True
    
    @staticmethod
    def get_workstation_type(workstation_id: int) -> str:
        """
        Récupère le type de workstation
        """
        workstation = get_workstation_by_id(workstation_id)
        if workstation:
            return workstation.workstation_type
        return "UNKNOWN"
    
    @staticmethod
    def get_workstation_state(workstation_id: int) -> str:
        """
        Récupère l'état actuel de la workstation
        """
        # Logique pour déterminer l'état (WORKING, IDLE, etc.)
        return "IDLE"
    
    @staticmethod
    def calculate_productivity(workstation_id: int, start_time: datetime, end_time: datetime) -> float:
        """
        Calcule la productivité d'une workstation
        """
        # Logique pour calculer la productivité
        return 85.5  # Exemple