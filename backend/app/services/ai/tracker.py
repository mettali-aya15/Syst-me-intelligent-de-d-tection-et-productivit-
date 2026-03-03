import numpy as np
from datetime import datetime

class SimpleTracker:
    """
    Tracker simple par centroid (employés)
    """
    def __init__(self, max_distance=50):
        self.objects = {}  # id -> bbox
        self.next_id = 0
        self.max_distance = max_distance
        self.last_update = datetime.utcnow()
        self.max_age = 30  # secondes

    def update(self, detections):
        """
        Met à jour le tracker avec les nouvelles détections
        Retourne : {id: bbox}
        """
        # Mettre à jour les objets existants
        updated_objects = {}
        for det in detections:
            centroid = [(det[0]+det[2])/2, (det[1]+det[3])/2]
            min_dist = float("inf")
            best_id = None
            for oid, obox in self.objects.items():
                ob_centroid = [(obox[0]+obox[2])/2, (obox[1]+obox[3])/2]
                dist = np.linalg.norm(np.array(centroid) - np.array(ob_centroid))
                if dist < min_dist and dist < self.max_distance:
                    min_dist = dist
                    best_id = oid
            if best_id is None:
                updated_objects[self.next_id] = det
                self.next_id += 1
            else:
                updated_objects[best_id] = det
        
        # Supprimer les objets trop anciens
        current_time = datetime.utcnow()
        for oid in list(self.objects.keys()):
            if (current_time - self.objects[oid].get('last_update', current_time)).total_seconds() > self.max_age:
                del updated_objects[oid]
        
        # Mettre à jour les temps de dernière mise à jour
        for oid, bbox in updated_objects.items():
            updated_objects[oid] = {
                'bbox': bbox,
                'last_update': datetime.utcnow()
            }
        
        self.objects = updated_objects
        return {oid: data['bbox'] for oid, data in updated_objects.items()}

class WorkstationTracker:
    """
    Tracker pour les workstations
    """
    def __init__(self, max_distance=100):
        self.workstations = {}  # id -> bbox
        self.next_id = 0
        self.max_distance = max_distance
    
    def update(self, detections, workstation_type=None):
        """
        Met à jour le tracker avec les nouvelles détections de workstations
        """
        updated_workstations = {}
        for det in detections:
            if workstation_type and det['label'] != workstation_type:
                continue
            
            centroid = [(det[0]+det[2])/2, (det[1]+det[3])/2]
            min_dist = float("inf")
            best_id = None
            for wid, wbox in self.workstations.items():
                wb_centroid = [(wbox[0]+wbox[2])/2, (wbox[1]+wbox[3])/2]
                dist = np.linalg.norm(np.array(centroid) - np.array(wb_centroid))
                if dist < min_dist and dist < self.max_distance:
                    min_dist = dist
                    best_id = wid
            if best_id is None:
                updated_workstations[self.next_id] = det
                self.next_id += 1
            else:
                updated_workstations[best_id] = det
        
        self.workstations = updated_workstations
        return {wid: bbox for wid, bbox in updated_workstations.items()}