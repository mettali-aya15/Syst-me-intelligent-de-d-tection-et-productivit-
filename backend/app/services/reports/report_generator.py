#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Générateur de rapports exportables
Génère des fichiers PDF, Excel, CSV
"""

from typing import Dict, List, Optional
from datetime import datetime, date
from pathlib import Path
import json

import logging
logger = logging.getLogger(__name__)


class ReportGenerator:
    """Générateur de rapports exportables"""
    
    @staticmethod
    async def generate_json_report(
        report_data: Dict,
        output_dir: str = "data/reports"
    ) -> str:
        """
        Générer un rapport au format JSON
        
        Args:
            report_data: Données du rapport
            output_dir: Dossier de sortie
        
        Returns:
            Chemin du fichier généré
        """
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"report_{timestamp}.json"
            filepath = output_path / filename
            
            # Convertir les dates en string pour JSON
            def json_serializer(obj):
                if isinstance(obj, (datetime, date)):
                    return obj.isoformat()
                raise TypeError(f"Type {type(obj)} not serializable")
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, default=json_serializer, ensure_ascii=False)
            
            logger.info(f"✅ Rapport JSON généré : {filepath}")
            
            return str(filepath)
        
        except Exception as e:
            logger.error(f"❌ Erreur génération JSON : {e}")
            raise
    
    @staticmethod
    async def generate_csv_report(
        data: List[Dict],
        headers: List[str],
        output_dir: str = "data/reports",
        filename: str = None
    ) -> str:
        """
        Générer un rapport au format CSV
        
        Args:
            data: Données à exporter
            headers: En-têtes des colonnes
            output_dir: Dossier de sortie
            filename: Nom du fichier (optionnel)
        
        Returns:
            Chemin du fichier généré
        """
        try:
            import csv
            
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"report_{timestamp}.csv"
            
            filepath = output_path / filename
            
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                
                for row in data:
                    # Convertir dates en string
                    processed_row = {}
                    for key, value in row.items():
                        if isinstance(value, (datetime, date)):
                            processed_row[key] = value.isoformat()
                        else:
                            processed_row[key] = value
                    
                    writer.writerow(processed_row)
            
            logger.info(f"✅ Rapport CSV généré : {filepath}")
            
            return str(filepath)
        
        except Exception as e:
            logger.error(f"❌ Erreur génération CSV : {e}")
            raise
    
    @staticmethod
    async def generate_text_summary(
        report_data: Dict,
        output_dir: str = "data/reports"
    ) -> str:
        """
        Générer un résumé textuel lisible
        
        Args:
            report_data: Données du rapport
            output_dir: Dossier de sortie
        
        Returns:
            Chemin du fichier généré
        """
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"summary_{timestamp}.txt"
            filepath = output_path / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("RAPPORT CAMIA-FACTORY\n")
                f.write("=" * 80 + "\n\n")
                f.write(f"Généré le : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
                
                # Écrire le contenu de manière lisible
                ReportGenerator._write_dict_recursive(f, report_data, indent=0)
            
            logger.info(f"✅ Résumé textuel généré : {filepath}")
            
            return str(filepath)
        
        except Exception as e:
            logger.error(f"❌ Erreur génération résumé : {e}")
            raise
    
    @staticmethod
    def _write_dict_recursive(file, data: Dict, indent: int = 0):
        """
        Écrire un dictionnaire de manière récursive et lisible
        
        Args:
            file: Fichier ouvert
            data: Données à écrire
            indent: Niveau d'indentation
        """
        indent_str = "  " * indent
        
        for key, value in data.items():
            if isinstance(value, dict):
                file.write(f"{indent_str}{key}:\n")
                ReportGenerator._write_dict_recursive(file, value, indent + 1)
            elif isinstance(value, list):
                file.write(f"{indent_str}{key}:\n")
                for item in value:
                    if isinstance(item, dict):
                        ReportGenerator._write_dict_recursive(file, item, indent + 2)
                        file.write("\n")
                    else:
                        file.write(f"{indent_str}  - {item}\n")
            else:
                # Formater les dates
                if isinstance(value, (datetime, date)):
                    value = value.strftime('%d/%m/%Y %H:%M:%S')
                
                file.write(f"{indent_str}{key}: {value}\n")
    
    @staticmethod
    async def export_daily_report(
        target_date: date,
        format: str = "json",
        output_dir: str = "data/reports"
    ) -> str:
        """
        Exporter un rapport journalier dans le format souhaité
        
        Args:
            target_date: Date du rapport
            format: Format d'export ("json", "csv", "txt")
            output_dir: Dossier de sortie
        
        Returns:
            Chemin du fichier généré
        """
        from .daily_report import DailyReportGenerator
        from core.database import Database
        
        try:
            # Récupérer le rapport
            reports_collection = Database.get_collection("daily_reports")
            report_doc = await reports_collection.find_one({"date": target_date})
            
            if not report_doc:
                # Générer le rapport s'il n'existe pas
                report = await DailyReportGenerator.generate_report(target_date)
                report_data = report.dict(by_alias=False)
            else:
                report_data = report_doc
            
            # Exporter selon le format
            if format == "json":
                return await ReportGenerator.generate_json_report(report_data, output_dir)
            
            elif format == "csv":
                # Préparer les données pour CSV
                csv_data = []
                
                # Ligne de résumé
                csv_data.append({
                    "date": target_date,
                    "total_videos": report_data.get("total_videos_processed", 0),
                    "total_detections": report_data.get("total_detections", 0),
                    "productivity_score": report_data.get("productivity_score", 0),
                    "employees_present": len(report_data.get("employees_present", [])),
                    "employees_absent": len(report_data.get("employees_absent", []))
                })
                
                headers = ["date", "total_videos", "total_detections", "productivity_score", 
                          "employees_present", "employees_absent"]
                
                return await ReportGenerator.generate_csv_report(
                    csv_data, 
                    headers, 
                    output_dir,
                    filename=f"rapport_{target_date}.csv"
                )
            
            elif format == "txt":
                return await ReportGenerator.generate_text_summary(report_data, output_dir)
            
            else:
                raise ValueError(f"Format non supporté : {format}")
        
        except Exception as e:
            logger.error(f"❌ Erreur export rapport : {e}")
            raise
    
    @staticmethod
    async def generate_productivity_chart_data(
        start_date: date,
        end_date: date
    ) -> Dict:
        """
        Générer les données pour un graphique de productivité
        
        Args:
            start_date: Date de début
            end_date: Date de fin
        
        Returns:
            Données formatées pour graphiques (Chart.js, etc.)
        """
        from core.database import Database
        
        try:
            reports_collection = Database.get_collection("daily_reports")
            cursor = reports_collection.find({
                "date": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            }).sort("date", 1)
            
            reports = await cursor.to_list(length=None)
            
            # Format Chart.js
            chart_data = {
                "labels": [],
                "datasets": [
                    {
                        "label": "Score de productivité",
                        "data": [],
                        "borderColor": "rgb(75, 192, 192)",
                        "tension": 0.1
                    },
                    {
                        "label": "Vidéos traitées",
                        "data": [],
                        "borderColor": "rgb(255, 99, 132)",
                        "tension": 0.1
                    }
                ]
            }
            
            for report in reports:
                chart_data["labels"].append(report["date"].strftime("%d/%m"))
                chart_data["datasets"][0]["data"].append(report.get("productivity_score", 0))
                chart_data["datasets"][1]["data"].append(report.get("total_videos_processed", 0))
            
            return chart_data
        
        except Exception as e:
            logger.error(f"❌ Erreur génération données graphique : {e}")
            raise