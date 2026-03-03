from datetime import datetime, timedelta
from app.services.workstation_service import get_workstation_by_id, calculate_workstation_productivity

class KPICalculator:
    """
    Calculateur de KPI
    """
    
    @staticmethod
    def calculate_productivity(workstation_id: int, days: int = 7) -> float:
        """
        Calcule la productivité d'une workstation
        """
        return calculate_workstation_productivity(workstation_id, days)
    
    @staticmethod
    def calculate_site_productivity(site_id: int, days: int = 7) -> float:
        """
        Calcule la productivité moyenne d'un site
        """
        # Logique pour calculer la productivité du site
        # (à implémenter selon votre système)
        return 85.5  # Exemple
    
    @staticmethod
    def calculate_machine_utilization(workstation_id: int, days: int = 7) -> float:
        """
        Calcule l'utilisation des workstations
        """
        # Logique pour calculer l'utilisation des workstations
        # (à implémenter selon votre système)
        return 92.3  # Exemple
    
    @staticmethod
    def calculate_employee_efficiency(employee_id: int, days: int = 7) -> float:
        """
        Calcule l'efficacité des employés
        """
        # Logique pour calculer l'efficacité des employés
        # (à implémenter selon votre système)
        return 88.7  # Exemple
    
    @staticmethod
    def get_site_kpi(site_id: int, days: int = 7) -> dict:
        """
        Récupère tous les KPI pour un site
        """
        return {
            "productivity": KPICalculator.calculate_site_productivity(site_id, days),
            "machine_utilization": KPICalculator.calculate_machine_utilization(site_id, days),
            "employee_efficiency": KPICalculator.calculate_employee_efficiency(site_id, days),
            "total_production": 15000  # Exemple
        }
    
    @staticmethod
    def get_workstation_kpi(workstation_id: int, days: int = 7) -> dict:
        """
        Récupère tous les KPI pour une workstation
        """
        return {
            "productivity": KPICalculator.calculate_productivity(workstation_id, days),
            "total_production": 500,  # Exemple
            "working_time": 3600,  # Exemple
            "idle_time": 1800  # Exemple
        }