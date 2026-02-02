import { Component, inject, OnInit, AfterViewInit, OnDestroy } from '@angular/core';
import { Auth } from '../../core/auth/auth';
import { AdminDashboard } from "./admin-dashboard/admin-dashboard";
import { EmpList } from "../employees/emp-list/emp-list";
import {  RouterOutlet } from "@angular/router";
import { RapportsComponent } from "../repots/rapports/rapports";

import { CommonModule } from '@angular/common';
import { Chart, registerables } from 'chart.js';
Chart.register(...registerables);
import { ViewChild, ElementRef } from '@angular/core';
import { KPI, KpiService } from './kpi';

// Vérifie le chemin vers ton service

@Component({
  selector: 'app-admin',
  standalone: true,
  templateUrl: './admin.html',
  imports: [AdminDashboard, EmpList, RouterOutlet, RapportsComponent,CommonModule]
})
export class Admin implements OnInit, AfterViewInit, OnDestroy{

  constructor(private authService: Auth) {}

  logout(): void {
    this.authService.logout();
    // Le service va automatiquement vider le localStorage 
    // et rediriger vers /login comme tu l'as programmé dans auth.ts
  }
  @ViewChild('productionChart') productionChartRef!: ElementRef<HTMLCanvasElement>;
@ViewChild('efficiencyChart') efficiencyChartRef!: ElementRef<HTMLCanvasElement>;
@ViewChild('defectsChart') defectsChartRef!: ElementRef<HTMLCanvasElement>;
@ViewChild('downtimeChart') downtimeChartRef!: ElementRef<HTMLCanvasElement>;

private kpiService = inject(KpiService);
  
  kpis$ = this.kpiService.kpis$;

  // Références aux charts
  private productionChart?: Chart;
  private efficiencyChart?: Chart;
  private defectsChart?: Chart;
  private downtimeChart?: Chart;

  ngOnInit(): void {
    this.kpiService.getKpis().subscribe();
  }

 // Dans votre classe DashboardComponent

now = new Date();

// Helper pour retourner une classe CSS simple
getTrendClass(trend: 'up' | 'down' | 'stable'): string {
  switch(trend) {
    case 'up': return 'trend-up';
    case 'down': return 'trend-down';
    default: return 'trend-neutral';
  }
}

// Calcul pourcentage
getProgressPercentage(kpi: any): number {
  if (!kpi.target || kpi.target === 0) return 0;
  const pct = (kpi.value / kpi.target) * 100;
  return Math.min(pct, 100); // Bloquer à 100% visuellement
}
  getKpiCardClass(kpi: KPI): string {
    if (kpi.value >= kpi.target && kpi.trend === 'up') return 'trend-up';
    if (kpi.value < kpi.target && kpi.trend === 'down') return 'trend-down';
    return 'trend-stable';
  }

  getKpiHeaderClass(kpi: KPI): string {
    if (kpi.value >= kpi.target && kpi.trend === 'up') return 'trend-up';
    if (kpi.value < kpi.target && kpi.trend === 'down') return 'trend-down';
    return 'trend-stable';
  }

  getKpiValueClass(kpi: KPI): string {
    return kpi.value >= kpi.target ? 'target-achieved' : 'target-not-achieved';
  }

  getTrendIconClass(kpi: KPI): string {
    return `trend-${kpi.trend}`;
  }

  getProgressFillClass(kpi: KPI): string {
    return kpi.value >= kpi.target ? 'target-achieved' : 'target-not-achieved';
  }

  getChangeBadgeClass(kpi: KPI): string {
    if (kpi.changePercent > 0) return 'positive';
    if (kpi.changePercent < 0) return 'negative';
    return 'neutral';
  }

 ngAfterViewInit(): void {
  this.createCharts();
}


  ngOnDestroy(): void {
    // Détruire les charts pour éviter les fuites mémoire
    this.productionChart?.destroy();
    this.efficiencyChart?.destroy();
    this.defectsChart?.destroy();
    this.downtimeChart?.destroy();
  }

  private createCharts(): void {
    this.createProductionChart();
    this.createEfficiencyChart();
    this.createDefectsChart();
    this.createDowntimeChart();
  }
private createProductionChart(): void {
  if (!this.productionChartRef) return;

  const ctx = this.productionChartRef.nativeElement.getContext('2d');
  if (!ctx) return;

  this.productionChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'],
      datasets: [
        {
          label: 'Production (unités)',
          data: [2800, 3050, 2900, 3200, 3100, 2700, 2400]
        }
      ]
    }
  });
}

private createEfficiencyChart() {
  const ctx = this.efficiencyChartRef.nativeElement.getContext('2d');
  if (!ctx) return;

  this.efficiencyChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: ['Lun','Mar','Mer','Jeu','Ven','Sam','Dim'],
      datasets: [{ label: 'Efficacité %', data: [88,92,90,94,91,89,87] }]
    }
  });
}
private createDefectsChart() {
  const ctx = this.defectsChartRef.nativeElement.getContext('2d');
  if (!ctx) return;

  this.defectsChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Conformes', 'Défauts'],
      datasets: [{ data: [98.2, 1.8] }]
    }
  });
}
private createDowntimeChart() {
  const ctx = this.downtimeChartRef.nativeElement.getContext('2d');
  if (!ctx) return;

  this.downtimeChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['Lun','Mar','Mer','Jeu','Ven','Sam','Dim'],
      datasets: [{ label: 'Temps arrêt', data: [120,105,95,110,100,130,115] }]
    }
  });
}









}