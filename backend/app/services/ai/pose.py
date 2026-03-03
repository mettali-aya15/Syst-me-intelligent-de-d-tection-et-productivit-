import cv2
import numpy as np

class PoseEstimator:
    """
    Estimateur de pose pour déterminer l'activité des employés
    """
    
    def __init__(self):
        self.model = None  # Modèle de pose (ex: OpenPose)
    
    def estimate_pose(self, frame, person_bbox):
        """
        Estime la pose d'une personne dans une bbox
        """
        # Implémentation de l'estimation de pose
        return {
            "keypoints": [],  # Points clés
            "posture": "STANDING",  # STANDING, SITTING, MOVING
            "confidence": 0.8
        }
    
    def is_employed(self, frame, person_bbox, workstation_bbox):
        """
        Détermine si un employé est actif sur une workstation
        """
        # Vérifie la position relative de la personne par rapport à la workstation
        is_near = self._is_near(person_bbox, workstation_bbox)
        is_working = self._is_working(frame, person_bbox)
        
        return is_near and is_working
    
    def _is_near(self, person_bbox, workstation_bbox):
        """Vérifie si la personne est proche de la workstation"""
        px1, py1, px2, py2 = person_bbox
        mx1, my1, mx2, my2 = workstation_bbox
        
        # Calcul de la distance entre les centres
        p_center = ((px1+px2)/2, (py1+py2)/2)
        m_center = ((mx1+mx2)/2, (my1+my2)/2)
        
        distance = np.sqrt((p_center[0]-m_center[0])**2 + (p_center[1]-m_center[1])**2)
        
        return distance < 100  # seuil arbitraire
    
    def _is_working(self, frame, person_bbox):
        """Vérifie si la personne est en train de travailler"""
        # Utilise l'estimation de pose pour déterminer l'activité
        pose = self.estimate_pose(frame, person_bbox)
        
        # Vérifie si la posture indique un travail actif
        return pose["posture"] != "STANDING"  # Exemple simplifié