from datetime import datetime
from app.models.workstation import Workstation
from app.services.workstation_service import get_workstation_by_id
from sqlalchemy.orm import Session

class WorkstationLogic:
    """Logique métier pour n'importe quel type de workstation"""
    
    def __init__(self, workstation_id: int, db: Session = None):
        self.workstation_id = workstation_id
        self.workstation = get_workstation_by_id(db, workstation_id) if db else None
        self.state = "IDLE"
        self.last_event_time = datetime.utcnow()
        self.idle_threshold = 60  # secondes
        
        # Configuration spécifique au type de workstation
        self._configure_type_logic()
    
    def _configure_type_logic(self):
        """Configure la logique selon le type de workstation"""
        if self.workstation and self.workstation.workstation_type == "SEWING":
            self._is_active = self._is_sewing_active
            self._get_productivity = self._get_sewing_productivity
        elif self.workstation and self.workstation.workstation_type == "TABLE":
            self._is_active = self._is_table_active
            self._get_productivity = self._get_table_productivity
        elif self.workstation and self.workstation.workstation_type == "DESK":
            self._is_active = self._is_desk_active
            self._get_productivity = self._get_desk_productivity
        else:
            # Par défaut pour les types inconnus
            self._is_active = self._is_generic_active
            self._get_productivity = self._get_generic_productivity
    
    # --- LOGIQUE SPÉCIFIQUE PAR TYPE ---
    
    def _is_sewing_active(self, detections):
        """Logique pour les workstations de couture"""
        person_detected = any(d['label'] == 'person' for d in detections)
        sitting = any(d['label'] == 'person' and d.get('sitting', False) for d in detections)
        machine_active = any(d['label'] == 'sewing_machine' for d in detections)
        
        return person_detected and sitting and machine_active
    
    def _is_table_active(self, detections):
        """Logique pour les tables de café"""
        person_detected = any(d['label'] == 'person' for d in detections)
        table_occupied = any(d['label'] == 'table' and d.get('occupied', False) for d in detections)
        
        return person_detected and table_occupied
    
    def _is_desk_active(self, detections):
        """Logique pour les postes de bureau"""
        person_detected = any(d['label'] == 'person' for d in detections)
        computer_active = any(d['label'] == 'computer' and d.get('active', False) for d in detections)
        
        return person_detected and computer_active
    
    def _is_generic_active(self, detections):
        """Logique par défaut pour les types inconnus"""
        return any(d['label'] == 'person' for d in detections)
    
    # --- FIN LOGIQUE SPÉCIFIQUE ---
    
    def process_frame(self, detections):
        """Traite une frame et génère des événements"""
        is_active = self._is_active(detections)
        now = datetime.utcnow()
        
        if is_active:
            if self.state != "WORKING":
                self.state = "WORKING"
                self.last_event_time = now
                return {
                    "workstation_id": self.workstation_id,
                    "event": "WORKSTATION_ACTIVE",
                    "time": now
                }
        else:
            if self.state == "WORKING":
                duration = (now - self.last_event_time).total_seconds()
                self.state = "IDLE"
                return {
                    "workstation_id": self.workstation_id,
                    "event": "WORKSTATION_IDLE",
                    "duration": duration,
                    "time": now
                }
        return None
    
    def calculate_productivity(self, start_time, end_time):
        """Calcule la productivité selon le type de workstation"""
        return self._get_productivity(start_time, end_time)
    
    def _get_sewing_productivity(self, start_time, end_time):
        """Calcul de productivité pour les workstations de couture"""
        # Logique spécifique à la couture
        return 85.5  # Exemple
    
    def _get_table_productivity(self, start_time, end_time):
        """Calcul de productivité pour les tables de café"""
        # Logique spécifique aux cafés
        return 78.2  # Exemple
    
    def _get_desk_productivity(self, start_time, end_time):
        """Calcul de productivité pour les postes de bureau"""
        # Logique spécifique aux bureaux
        return 92.1  # Exemple
    
    def _get_generic_productivity(self, start_time, end_time):
        """Calcul de productivité par défaut"""
        return 75.0  # Exemple