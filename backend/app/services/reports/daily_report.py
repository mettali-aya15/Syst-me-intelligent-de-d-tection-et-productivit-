#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Générateur de rapports journaliers
Crée des rapports consolidés avec toutes les métriques
"""

from typing import Dict, List, Optional
from datetime import datetime, date, timedelta
from bson import ObjectId

from app.models.kpi import DailyReport, KPISnapshot
from app.services.analytics import KPIService

import logging
logger = logging.getLogger(__name__)


class DailyReportGenerator:
    """Générateur de rapports journaliers"""
    
    @staticmethod
    async def generate_report(target_date: date = None) -> DailyReport:
        """
        Générer un rapport journalier complet
        
        Args:
            target_date: Date du rapport (défaut: aujourd'hui)
        
        Returns:
            DailyReport généré
        """
        if target_date is None:
            target_date = datetime.now().date()
        
        try:
            logger.info(f"📊 Génération rapport journalier : {target_date}")
            
            # Utiliser le KPIService pour générer le rapport
            report = await KPIService.generate_daily_report(target_date)
            
            # Enrichir avec des analyses supplémentaires
            enriched_report = await DailyReportGenerator._enrich_report(report)
            
            logger.info(f"✅ Rapport journalier généré : {target_date}")
            
            return enriched_report
        
        except Exception as e:
            logger.error(f"❌ Erreur génération rapport : {e}")
            raise
    
    @staticmethod
    async def _enrich_report(report: DailyReport) -> DailyReport:
        """
        Enrichir le rapport avec des analyses supplémentaires
        
        Args:
            report: Rapport de base
        
        Returns:
            Rapport enrichi
        """
        # Ajouter des comparaisons avec la veille
        yesterday = report.date - timedelta(days=1)
        
        reports_collection = Database.get_collection("daily_reports")
        yesterday_report = await reports_collection.find_one({"date": yesterday})
        
        if yesterday_report:
            # Calculer les variations
            today_score = report.productivity_score
            yesterday_score = yesterday_report.get("productivity_score", 0)
            
            variation = today_score - yesterday_score
            
            # Ajouter au résumé
            report.summary["comparison_yesterday"] = {
                "productivity_variation": round(variation, 2),
                "trend": "up" if variation > 0 else "down" if variation < 0 else "stable"
            }
        
        return report
    
    @staticmethod
    async def get_weekly_summary(end_date: date = None) -> Dict:
        """
        Obtenir un résumé hebdomadaire
        
        Args:
            end_date: Date de fin (défaut: aujourd'hui)
        
        Returns:
            Résumé de la semaine
        """
        if end_date is None:
            end_date = datetime.now().date()
        
        start_date = end_date - timedelta(days=6)  # 7 jours
        
        try:
            reports_collection = Database.get_collection("daily_reports")
            cursor = reports_collection.find({
                "date": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            }).sort("date", 1)
            
            reports = await cursor.to_list(length=7)
            
            if not reports:
                return {
                    "period": f"{start_date} - {end_date}",
                    "message": "Aucun rapport sur cette période"
                }
            
            # Calculer les moyennes
            avg_productivity = sum(r.get("productivity_score", 0) for r in reports) / len(reports)
            total_videos = sum(r.get("total_videos_processed", 0) for r in reports)
            total_detections = sum(r.get("total_detections", 0) for r in reports)
            
            # Identifier les meilleurs et pires jours
            best_day = max(reports, key=lambda r: r.get("productivity_score", 0))
            worst_day = min(reports, key=lambda r: r.get("productivity_score", 0))
            
            return {
                "period": {
                    "start": start_date,
                    "end": end_date,
                    "days_analyzed": len(reports)
                },
                "averages": {
                    "productivity_score": round(avg_productivity, 2),
                    "videos_per_day": round(total_videos / len(reports), 2),
                    "detections_per_day": round(total_detections / len(reports), 2)
                },
                "totals": {
                    "videos_processed": total_videos,
                    "detections": total_detections
                },
                "highlights": {
                    "best_day": {
                        "date": best_day["date"],
                        "productivity_score": best_day.get("productivity_score", 0)
                    },
                    "worst_day": {
                        "date": worst_day["date"],
                        "productivity_score": worst_day.get("productivity_score", 0)
                    }
                },
                "daily_breakdown": [
                    {
                        "date": r["date"],
                        "productivity_score": r.get("productivity_score", 0),
                        "videos_processed": r.get("total_videos_processed", 0),
                        "employees_present": len(r.get("employees_present", [])),
                        "employees_absent": len(r.get("employees_absent", []))
                    }
                    for r in reports
                ]
            }
        
        except Exception as e:
            logger.error(f"❌ Erreur résumé hebdomadaire : {e}")
            raise
    
    @staticmethod
    async def get_monthly_summary(year: int = None, month: int = None) -> Dict:
        """
        Obtenir un résumé mensuel
        
        Args:
            year: Année (défaut: année actuelle)
            month: Mois (défaut: mois actuel)
        
        Returns:
            Résumé du mois
        """
        now = datetime.now()
        year = year or now.year
        month = month or now.month
        
        # Premier et dernier jour du mois
        start_date = date(year, month, 1)
        
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
        
        try:
            reports_collection = Database.get_collection("daily_reports")
            cursor = reports_collection.find({
                "date": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            }).sort("date", 1)
            
            reports = await cursor.to_list(length=31)
            
            if not reports:
                return {
                    "period": f"{year}-{month:02d}",
                    "message": "Aucun rapport sur ce mois"
                }
            
            # Calculer les statistiques mensuelles
            avg_productivity = sum(r.get("productivity_score", 0) for r in reports) / len(reports)
            total_videos = sum(r.get("total_videos_processed", 0) for r in reports)
            total_detections = sum(r.get("total_detections", 0) for r in reports)
            
            # Compter les jours travaillés
            working_days = len(reports)
            
            # Tendance (régression linéaire simple)
            productivity_scores = [r.get("productivity_score", 0) for r in reports]
            trend = "stable"
            if len(productivity_scores) >= 2:
                first_half_avg = sum(productivity_scores[:len(productivity_scores)//2]) / (len(productivity_scores)//2)
                second_half_avg = sum(productivity_scores[len(productivity_scores)//2:]) / (len(productivity_scores) - len(productivity_scores)//2)
                
                if second_half_avg > first_half_avg + 5:
                    trend = "improving"
                elif second_half_avg < first_half_avg - 5:
                    trend = "declining"
            
            return {
                "period": {
                    "year": year,
                    "month": month,
                    "start_date": start_date,
                    "end_date": end_date,
                    "working_days": working_days
                },
                "statistics": {
                    "avg_productivity_score": round(avg_productivity, 2),
                    "total_videos_processed": total_videos,
                    "total_detections": total_detections,
                    "avg_videos_per_day": round(total_videos / working_days, 2) if working_days > 0 else 0,
                    "trend": trend
                },
                "weekly_breakdown": await DailyReportGenerator._get_weekly_breakdown(reports)
            }
        
        except Exception as e:
            logger.error(f"❌ Erreur résumé mensuel : {e}")
            raise
    
    @staticmethod
    async def _get_weekly_breakdown(reports: List[Dict]) -> List[Dict]:
        """
        Découper les rapports par semaine
        
        Args:
            reports: Liste des rapports journaliers
        
        Returns:
            Breakdown par semaine
        """
        weeks = {}
        
        for report in reports:
            report_date = report["date"]
            # Numéro de semaine
            week_num = report_date.isocalendar()[1]
            
            if week_num not in weeks:
                weeks[week_num] = {
                    "week_number": week_num,
                    "days": [],
                    "avg_productivity": 0,
                    "total_videos": 0
                }
            
            weeks[week_num]["days"].append(report)
        
        # Calculer les moyennes par semaine
        weekly_breakdown = []
        for week_num, week_data in sorted(weeks.items()):
            days = week_data["days"]
            avg_prod = sum(d.get("productivity_score", 0) for d in days) / len(days)
            total_vids = sum(d.get("total_videos_processed", 0) for d in days)
            
            weekly_breakdown.append({
                "week_number": week_num,
                "days_count": len(days),
                "avg_productivity_score": round(avg_prod, 2),
                "total_videos": total_vids
            })
        
        return weekly_breakdown