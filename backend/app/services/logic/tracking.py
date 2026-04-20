#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Système de tracking des détections
Track les employés, machines et objets entre les frames
"""

from typing import Dict, List, Set, Tuple
from collections import defaultdict
from datetime import datetime

from app.models.detection import Detection, FrameDetection

import logging
logger = logging.getLogger(__name__)


class DetectionTracker:
    """
    Tracker de détections entre les frames
    Permet de suivre la continuité des objets détectés
    """
    
    def __init__(self):
        self.employee_tracks = defaultdict(list)  # {employee_name: [frame_numbers]}
        self.machine_tracks = defaultdict(list)   # {machine_name: [frame_numbers]}
        self.table_tracks = defaultdict(list)     # {table_name: [frame_numbers]}
        
        self.first_appearance = {}  # {object_name: frame_number}
        self.last_appearance = {}   # {object_name: frame_number}
    
    def process_frame(self, frame_detection: FrameDetection):
        """
        Traiter une frame et mettre à jour le tracking
        
        Args:
            frame_detection: Détections d'une frame
        """
        frame_num = frame_detection.frame_number
        
        for det in frame_detection.detections:
            obj_name = det.class_name
            
            # Enregistrer première apparition
            if obj_name not in self.first_appearance:
                self.first_appearance[obj_name] = frame_num
            
            # Mettre à jour dernière apparition
            self.last_appearance[obj_name] = frame_num
            
            # Ajouter à la track appropriée
            if det.source == "employees":
                self.employee_tracks[obj_name].append(frame_num)
            elif "machine" in obj_name.lower():
                self.machine_tracks[obj_name].append(frame_num)
            elif "table" in obj_name.lower():
                self.table_tracks[obj_name].append(frame_num)
    
    def get_presence_duration(
        self, 
        object_name: str, 
        fps: int
    ) -> float:
        """
        Calculer la durée de présence d'un objet
        
        Args:
            object_name: Nom de l'objet
            fps: FPS de la vidéo
        
        Returns:
            Durée en secondes
        """
        if object_name not in self.first_appearance:
            return 0.0
        
        first = self.first_appearance[object_name]
        last = self.last_appearance[object_name]
        
        duration_frames = last - first + 1
        duration_seconds = duration_frames / fps if fps > 0 else 0
        
        return duration_seconds
    
    def get_presence_rate(
        self, 
        object_name: str, 
        total_frames: int
    ) -> float:
        """
        Calculer le taux de présence d'un objet
        
        Args:
            object_name: Nom de l'objet
            total_frames: Nombre total de frames
        
        Returns:
            Taux [0-1]
        """
        all_tracks = {**self.employee_tracks, **self.machine_tracks, **self.table_tracks}
        
        if object_name not in all_tracks:
            return 0.0
        
        appearances = len(all_tracks[object_name])
        rate = appearances / total_frames if total_frames > 0 else 0
        
        return rate
    
    def get_continuous_presence_periods(
        self, 
        object_name: str,
        max_gap_frames: int = 30
    ) -> List[Tuple[int, int]]:
        """
        Obtenir les périodes de présence continue
        
        Args:
            object_name: Nom de l'objet
            max_gap_frames: Gap maximum entre frames pour considérer comme continue
        
        Returns:
            Liste de (frame_start, frame_end)
        """
        all_tracks = {**self.employee_tracks, **self.machine_tracks, **self.table_tracks}
        
        if object_name not in all_tracks:
            return []
        
        frames = sorted(all_tracks[object_name])
        periods = []
        
        if not frames:
            return periods
        
        period_start = frames[0]
        period_end = frames[0]
        
        for i in range(1, len(frames)):
            current_frame = frames[i]
            gap = current_frame - frames[i-1]
            
            if gap <= max_gap_frames:
                # Continuer la période
                period_end = current_frame
            else:
                # Terminer la période et en commencer une nouvelle
                periods.append((period_start, period_end))
                period_start = current_frame
                period_end = current_frame
        
        # Ajouter la dernière période
        periods.append((period_start, period_end))
        
        return periods
    
    def get_tracking_summary(self, fps: int, total_frames: int) -> Dict:
        """
        Obtenir un résumé complet du tracking
        
        Args:
            fps: FPS de la vidéo
            total_frames: Nombre total de frames
        
        Returns:
            Résumé structuré
        """
        summary = {
            "employees": {},
            "machines": {},
            "tables": {},
            "statistics": {
                "total_employees": len(self.employee_tracks),
                "total_machines": len(self.machine_tracks),
                "total_tables": len(self.table_tracks)
            }
        }
        
        # Employés
        for emp_name, frames in self.employee_tracks.items():
            summary["employees"][emp_name] = {
                "appearances": len(frames),
                "first_seen_frame": self.first_appearance[emp_name],
                "last_seen_frame": self.last_appearance[emp_name],
                "presence_duration_seconds": self.get_presence_duration(emp_name, fps),
                "presence_rate": round(self.get_presence_rate(emp_name, total_frames), 3),
                "continuous_periods": self.get_continuous_presence_periods(emp_name)
            }
        
        # Machines
        for machine_name, frames in self.machine_tracks.items():
            summary["machines"][machine_name] = {
                "appearances": len(frames),
                "first_seen_frame": self.first_appearance[machine_name],
                "last_seen_frame": self.last_appearance[machine_name],
                "activity_duration_seconds": self.get_presence_duration(machine_name, fps),
                "activity_rate": round(self.get_presence_rate(machine_name, total_frames), 3),
                "active_periods": self.get_continuous_presence_periods(machine_name)
            }
        
        # Tables
        for table_name, frames in self.table_tracks.items():
            summary["tables"][table_name] = {
                "appearances": len(frames),
                "occupation_duration_seconds": self.get_presence_duration(table_name, fps),
                "occupation_rate": round(self.get_presence_rate(table_name, total_frames), 3)
            }
        
        return summary
    
    def detect_absences(
        self, 
        expected_objects: List[str], 
        category: str = "employees"
    ) -> List[str]:
        """
        Détecter les objets absents
        
        Args:
            expected_objects: Liste des objets attendus
            category: "employees", "machines", ou "tables"
        
        Returns:
            Liste des objets absents
        """
        track_map = {
            "employees": self.employee_tracks,
            "machines": self.machine_tracks,
            "tables": self.table_tracks
        }
        
        detected = set(track_map.get(category, {}).keys())
        expected = set(expected_objects)
        
        absences = list(expected - detected)
        
        return absences
    
    def is_continuously_present(
        self, 
        object_name: str, 
        min_continuous_frames: int = 100
    ) -> bool:
        """
        Vérifier si un objet est présent de manière continue
        
        Args:
            object_name: Nom de l'objet
            min_continuous_frames: Nombre minimum de frames continues
        
        Returns:
            True si présent continuellement
        """
        periods = self.get_continuous_presence_periods(object_name)
        
        if not periods:
            return False
        
        # Vérifier si au moins une période dépasse le minimum
        for start, end in periods:
            duration = end - start + 1
            if duration >= min_continuous_frames:
                return True
        
        return False