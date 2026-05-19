import { Component, OnInit, OnDestroy, AfterViewInit, inject, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import Chart from 'chart.js/auto';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import * as XLSX from 'xlsx';

// ==========================================
// 📋 INTERFACES
// ==========================================
export interface RawDetections {
  machines: number;
  machinesStopped: number;
  employees: number;
  employesActifs: number;
  employesInactifs: number;
  products: number;
  clients: number;
  tables: number;
  tablesEmpty: number;
}

export interface CalculatedKPIs {
  trs: number;
  machineEfficiency: number;
  oee: number;
  employeeActivity: number;
  productivity: number;
  employeeEngagement: number;
  tableOccupancy: number;
  serviceLevel: number;
  qualityScore: number;
  uptime: number;
  throughput: number;
  performanceIndex: number;
  riskLevel: 'low' | 'medium' | 'high';
  riskScore: number;
}

export interface VideoKPI {
  videoId: string;
  filename: string;
  timestamp: string;
  uploadedAt: Date;
  raw: RawDetections;
  kpis: CalculatedKPIs;
  projectedMetrics?: {
    estimatedProducts: number;
    estimatedThroughput: number;
    factor: number;
    periodLabel: string;
  };
}

export interface KPICard {
  label: string;
  value: number | string;
  unit: string;
  trend?: 'up' | 'down' | 'stable';
  trendValue?: number;
  color: string;
  icon: string;
  description: string;
  category: 'production' | 'rh' | 'logistique' | 'qualite';
  isProjected?: boolean;
}

@Component({
  selector: 'app-kpi-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './kpi-dashboard.component.html',
  styleUrls: ['./kpi-dashboard.component.scss']
})
export class KpiDashboardComponent implements OnInit, OnDestroy, AfterViewInit {
  private http = inject(HttpClient);
  private router = inject(Router);
  private cdr = inject(ChangeDetectorRef); // ✅ AJOUT : Pour forcer mise à jour UI
  private apiUrl = 'http://localhost:8000/api/v1';
  
  private charts: { [key: string]: Chart } = {};
  private refreshInterval: any;
  
  loading = true;
  selectedPeriod: 'hour' | 'day' | 'week' | 'month' | 'video' = 'video';
  
  currentVideoKpi: VideoKPI | null = null;
  historicalKpis: VideoKPI[] = [];
  kpiCards: KPICard[] = [];
  
  projectionSummary = {
    period: '',
    factor: 0,
    estimatedProducts: 0,
    estimatedThroughput: 0,
    machines: 0,
    employees: 0
  };
  
  videoDuration: number = 60;
  
  comparisonData = { currentPeriod: 0, previousPeriod: 0, percentageChange: 0 };
  Math = Math;
  
  activeAlerts: Array<{ type: string; message: string; severity: 'warning' | 'critical' | 'info'; }> = [];

  // ==========================================
  // 🔄 CYCLE DE VIE
  // ==========================================
  ngOnInit(): void {
    this.loadKpiData();
    this.refreshInterval = setInterval(() => this.loadKpiData(), 60000);
  }

  ngAfterViewInit(): void {
    setTimeout(() => this.createCharts(), 500);
  }

  ngOnDestroy(): void {
    if (this.refreshInterval) clearInterval(this.refreshInterval);
    Object.values(this.charts).forEach(c => c?.destroy());
  }

  // ==========================================
  // 📊 CHARGEMENT DES DONNEES - CORRIGÉ
  // ==========================================
  async loadKpiData(): Promise<void> {
    try {
      this.loading = true;
      console.log('🔄 Début chargement KPI - Période:', this.selectedPeriod);
      
      // ✅ Si période temporelle sélectionnée
      if (this.selectedPeriod !== 'video') {
        console.log('⏰ Tentative chargement KPI temporel...');
        const success = await this.loadTimeBasedKPIs();
        
        if (!success) {
          console.warn('⚠️ Chargement temporel échoué, fallback vers vidéo');
          await this.loadVideoBasedKPIs();
        }
      } else {
        console.log('🎥 Chargement KPI depuis vidéo...');
        await this.loadVideoBasedKPIs();
      }
      
      this.loading = false;
      this.cdr.detectChanges(); // ✅ AJOUT : Force mise à jour UI
      console.log('✅ Chargement KPI terminé');
      
    } catch (error) {
      console.error('❌ Erreur chargement KPI:', error);
      this.loading = false;
    }
  }

  // ✅ CORRECTION : Extraction correcte de response.data
  private async loadTimeBasedKPIs(): Promise<boolean> {
  const periodeMap: { [key: string]: string } = {
    'hour': 'heure',
    'day': 'jour', 
    'week': 'semaine',
    'month': 'mois'
  };
  
  const periode = periodeMap[this.selectedPeriod];
  const url = `${this.apiUrl}/kpis/global/today?periode=${periode}`;
  
  console.log('📡 Appel API:', url);
  
  try {
    const response = await this.http.get<any>(url).toPromise();
    console.log('📊 Réponse API brute:', response);
    
    const kpiData = response.data || response;
    console.log('📊 kpiData (data extrait):', kpiData);
    console.log('🔍 kpiData.machines:', kpiData.machines);
    console.log('🔍 kpiData.employes:', kpiData.employes);
    console.log('🔍 kpiData.production:', kpiData.production);
    
    // ✅ Helper amélioré avec logging
    const getNum = (obj: any, ...paths: string[]): number => {
      console.log(`  🔎 Recherche de: ${paths.join(' | ')}`);
      for (const path of paths) {
        const keys = path.split('.');
        let val = obj;
        console.log(`    Chemin: ${path} -> clés:`, keys);
        for (const key of keys) {
          if (val && typeof val === 'object') {
            val = val[key];
            console.log(`      ${key} =`, val);
          } else { 
            val = undefined; 
            break; 
          }
        }
        if (typeof val === 'number' && !isNaN(val)) {
          console.log(`    ✅ Trouvé: ${val}`);
          return val;
        }
      }
      console.log(`    ❌ Non trouvé, retourne 0`);
      return 0;
    };
    
    // ✅ Mapping DIRECT sans helper pour tester
    const raw: RawDetections = {
      machines: kpiData.machines?.machines_actives || kpiData.machines?.total_machines || 0,
      machinesStopped: kpiData.machines?.machines_arretees || 0,
      employees: kpiData.employes?.total_employes || 0,
      employesActifs: kpiData.employes?.employes_actifs || 0,
      employesInactifs: kpiData.employes?.employes_inactifs || 0,
      products: kpiData.production?.total_produits || kpiData.production?.unites_produites || 0,
      clients: 0,
      tables: 0,
      tablesEmpty: 0
    };
    
    console.log('📊 raw après mapping:', raw);
    
    const kpis: CalculatedKPIs = {
      trs: kpiData.machines?.trs || 0,
      machineEfficiency: kpiData.machines?.performance || 0,
      oee: kpiData.machines?.trs || 0,
      employeeActivity: kpiData.employes?.taux_activite || 0,
      employeeEngagement: kpiData.employes?.taux_presence || 0,
      productivity: kpiData.employes?.productivite_par_employe || 0,
      qualityScore: kpiData.machines?.qualite || kpiData.production?.taux_conformite || 0,
      uptime: kpiData.machines?.disponibilite || 0,
      throughput: kpiData.production?.cadence_production || 0,
      performanceIndex: kpiData.machines?.performance || 0,
      tableOccupancy: 0,
      serviceLevel: 0,
      riskLevel: (kpiData.machines?.trs >= 85 ? 'low' : kpiData.machines?.trs >= 70 ? 'medium' : 'high') as 'low' | 'medium' | 'high',
      riskScore: kpiData.machines?.trs >= 85 ? 10 : kpiData.machines?.trs >= 70 ? 30 : 60
    };
    
    console.log('📊 kpis après mapping:', kpis);
    
    if (typeof kpis.trs !== 'number' || isNaN(kpis.trs) || kpis.trs === 0) {
      console.warn('⚠️ TRS invalide:', kpis.trs);
      // return false; // Temporairement commenté pour voir ce qui s'affiche
    }
    
    this.currentVideoKpi = {
      videoId: 'time-based',
      filename: `Période: ${this.getPeriodLabel()}`,
      timestamp: new Date().toLocaleString('fr-FR'),
      uploadedAt: new Date(),
      raw: raw,
      kpis: kpis
    };
    
    this.updateProjectionSummary(raw, { duration: this.getDurationForPeriod() });
    this.generateKpiCards();
    this.generateAlerts();
    this.createCharts();
    
    this.cdr.detectChanges(); // ✅ AJOUT : Force mise à jour UI après chargement temporel
    
    console.log('✅ KPIs temporels chargés');
    return true;
    
  } catch (error) {
    console.error(`❌ Erreur chargement KPIs pour ${periode}:`, error);
    return false;
  }
}

  private async loadVideoBasedKPIs(): Promise<void> {
    const videos = await this.http.get<any[]>(`${this.apiUrl}/videos/`).toPromise();
    const completed = videos?.filter(v => v.status === 'completed') || [];
    
    if (completed.length === 0) { 
      this.loading = false; 
      return; 
    }
    
    const latestVideo = completed.sort((a, b) => 
      new Date(b.created_at || b.uploaded_at).getTime() - new Date(a.created_at || a.uploaded_at).getTime()
    )[0];
    
    console.log('🎯 Vidéo de référence:', latestVideo.filename);
    console.log('📊 Données brutes:', latestVideo.unique_objects);
    
    const baseKPIs = this.calculateKPIs(latestVideo);
    console.log('📈 KPIs calculés:', baseKPIs);
    
    this.currentVideoKpi = this.projectPerformanceKPIs(baseKPIs, latestVideo);
    this.updateProjectionSummary(baseKPIs.raw, latestVideo);
    
    this.historicalKpis = completed.slice(0, 7).map(v => this.calculateKPIs(v));
    this.generateKpiCards();
    this.generateAlerts();
    this.createCharts();
    
    this.cdr.detectChanges(); // ✅ AJOUT : Force mise à jour UI après chargement vidéo
  }

  private getDurationForPeriod(): number {
    switch (this.selectedPeriod) {
      case 'hour': return 3600;
      case 'day': return 86400;
      case 'week': return 604800;
      case 'month': return 2592000;
      default: return this.videoDuration || 60;
    }
  }

  // ==========================================
  // 📈 PROJECTION DES PERFORMANCES
  // ==========================================
  private updateProjectionSummary(baseRaw: RawDetections, videoData: any): void {
    const durationSeconds = Number(videoData.duration) || this.getDurationForPeriod();
    let factor = 1;
    
    switch (this.selectedPeriod) {
      case 'video': factor = 1; break;
      case 'hour': factor = 3600 / durationSeconds; break;
      case 'day': factor = 86400 / durationSeconds; break;
      case 'week': factor = 604800 / durationSeconds; break;
      case 'month': factor = 2592000 / durationSeconds; break;
    }
    
    this.projectionSummary = {
      period: this.getPeriodLabel(),
      factor: Math.round(factor * 100) / 100,
      machines: baseRaw.machines,
      employees: baseRaw.employesActifs,
      estimatedProducts: Math.round(baseRaw.products * factor),
      estimatedThroughput: Math.round((baseRaw.products / durationSeconds) * factor * 3600)
    };
    
    console.log('📊 Résumé projection:', this.projectionSummary);
  }

  private projectPerformanceKPIs(baseVideo: VideoKPI, videoData: any): VideoKPI {
    const durationSeconds = Number(videoData.duration) || 60;
    this.videoDuration = durationSeconds;
    
    let projectionFactor = 1;
    let periodLabel = '';
    
    switch (this.selectedPeriod) {
      case 'video': projectionFactor = 1; periodLabel = 'Duree de la video'; break;
      case 'hour': projectionFactor = 3600 / durationSeconds; periodLabel = 'Projection 1 heure'; break;
      case 'day': projectionFactor = 86400 / durationSeconds; periodLabel = 'Projection 1 journee'; break;
      case 'week': projectionFactor = 604800 / durationSeconds; periodLabel = 'Projection 1 semaine'; break;
      case 'month': projectionFactor = 2592000 / durationSeconds; periodLabel = 'Projection 1 mois'; break;
    }
    
    const raw: RawDetections = { ...baseVideo.raw };
    const projectedProducts = Math.round(baseVideo.raw.products * projectionFactor);
    
    const totalMachines = raw.machines + raw.machinesStopped;
    const totalEmployees = raw.employees + raw.employesActifs + raw.employesInactifs;
    const activeEmployees = raw.employesActifs || raw.employees;
    
    const machineEfficiency = totalMachines > 0 ? Math.round((raw.machines / totalMachines) * 100) : 0;
    const availability = totalMachines > 0 ? (raw.machines / totalMachines) : 0;
    const performance = raw.machines > 0 ? Math.min((projectedProducts / (raw.machines * 10 * projectionFactor)), 1) : 0;
    const quality = 0.98;
    const trs = Math.round(availability * performance * quality * 100);
    
    const employeeActivity = totalEmployees > 0 ? Math.round((activeEmployees / totalEmployees) * 100) : 0;
    const productivity = activeEmployees > 0 ? Math.round((projectedProducts / activeEmployees) * 10) / 10 : 0;
    
    const tableOccupancy = raw.tables > 0 ? Math.round(((raw.tables - raw.tablesEmpty) / raw.tables) * 100) : 0;
    const projectedClients = Math.round(raw.clients * projectionFactor);
    const serviceLevel = activeEmployees > 0 ? Math.round((projectedClients / activeEmployees) * 10) / 10 : 0;
    
    const qualityScore = Math.round((trs + machineEfficiency + employeeActivity) / 3);
    const throughput = projectedProducts > 0 ? Math.min(projectedProducts * 10, 100) : 0;
    const performanceIndex = Math.round((qualityScore + throughput) / 2);
    
    const { riskLevel, riskScore } = this.calculateRiskForProjection(raw, { 
      machineEfficiency, employeeActivity, trs, projectedProducts, factor: projectionFactor 
    });
    
    return {
      videoId: 'projected',
      filename: `${videoData.filename} - ${periodLabel}`,
      timestamp: `Base sur l'analyse du ${baseVideo.timestamp}`,
      uploadedAt: baseVideo.uploadedAt,
      raw,
      projectedMetrics: {
        estimatedProducts: projectedProducts,
        estimatedThroughput: Math.round((baseVideo.raw.products / durationSeconds) * projectionFactor * 3600),
        factor: projectionFactor,
        periodLabel
      },
      kpis: {
        trs, machineEfficiency, oee: trs, employeeActivity, productivity,
        employeeEngagement: employeeActivity, tableOccupancy, serviceLevel, qualityScore,
        uptime: machineEfficiency, throughput, performanceIndex, riskLevel, riskScore
      }
    };
  }

  // ==========================================
  // 🧮 CALCULS KPI (DONNEES REELLES)
  // ==========================================
  private calculateKPIs(video: any): VideoKPI {
    const obj = video.unique_objects || {};
    
    const employees = Number(
      obj['employe'] || obj['employé'] || obj['employes'] || obj['employés'] || obj['employee'] || obj['employees'] || 0
    );
    const employesActifs = Number(
      obj['employe actif'] || obj['employé actif'] || obj['employes actifs'] || obj['employés actifs'] || obj['employee active'] || obj['employees active'] || employees
    );
    const employesInactifs = Number(
      obj['employe inactif'] || obj['employé inactif'] || obj['employes inactifs'] || obj['employés inactifs'] || obj['employee inactive'] || obj['employees inactive'] || 0
    );
    
    const raw: RawDetections = {
      machines: Number(obj['machine'] || obj['machines'] || 0),
      machinesStopped: Number(obj['machine arretee'] || obj['machine arrêtée'] || obj['machines arretees'] || 0),
      employees: employees,
      employesActifs: employesActifs,
      employesInactifs: employesInactifs,
      products: Number(obj['produit'] || obj['produits'] || obj['product'] || obj['products'] || 0),
      clients: Number(obj['client'] || obj['clients'] || 0),
      tables: Number(obj['table'] || obj['tables'] || 0),
      tablesEmpty: Number(obj['table vide'] || obj['table_vides'] || obj['tables_vides'] || obj['tables vides'] || 0)
    };
    
    const totalMachines = raw.machines + raw.machinesStopped;
    const totalEmployees = raw.employees + raw.employesActifs + raw.employesInactifs;
    const activeEmployees = raw.employesActifs || raw.employees;
    
    const machineEfficiency = totalMachines > 0 ? Math.round((raw.machines / totalMachines) * 100) : 0;
    const availability = totalMachines > 0 ? (raw.machines / totalMachines) : 0;
    const performance = raw.machines > 0 ? Math.min((raw.products / (raw.machines * 10)), 1) : 0;
    const trs = Math.round(availability * performance * 0.98 * 100);
    
    const employeeActivity = totalEmployees > 0 ? Math.round((activeEmployees / totalEmployees) * 100) : 0;
    const productivity = activeEmployees > 0 ? Math.round((raw.products / activeEmployees) * 10) / 10 : 0;
    const tableOccupancy = raw.tables > 0 ? Math.round(((raw.tables - raw.tablesEmpty) / raw.tables) * 100) : 0;
    const serviceLevel = activeEmployees > 0 ? Math.round((raw.clients / activeEmployees) * 10) / 10 : 0;
    
    const qualityScore = Math.round((trs + machineEfficiency + employeeActivity) / 3);
    const throughput = raw.products > 0 ? Math.min(raw.products * 10, 100) : 0;
    const performanceIndex = Math.round((qualityScore + throughput) / 2);
    
    const { riskLevel, riskScore } = this.calculateRisk(raw, { machineEfficiency, employeeActivity, trs });
    
    return {
      videoId: video._id,
      filename: video.filename,
      timestamp: new Date(video.created_at || video.uploaded_at).toLocaleString('fr-FR'),
      uploadedAt: new Date(video.created_at || video.uploaded_at),
      raw,
      kpis: {
        trs, machineEfficiency, oee: trs, employeeActivity, productivity,
        employeeEngagement: employeeActivity, tableOccupancy, serviceLevel, qualityScore,
        uptime: machineEfficiency, throughput, performanceIndex, riskLevel, riskScore
      }
    };
  }

  // ==========================================
  // ⚠️ CALCUL DES RISQUES
  // ==========================================
  private calculateRisk(raw: RawDetections, kpis: { machineEfficiency: number; employeeActivity: number; trs: number }): { riskLevel: 'low' | 'medium' | 'high'; riskScore: number } {
    let riskScore = 0;
    if (raw.machinesStopped > 0) riskScore += 30;
    if (raw.employesInactifs > 2) riskScore += 20;
    if (kpis.machineEfficiency < 70) riskScore += 25;
    if (kpis.employeeActivity < 60) riskScore += 15;
    if (kpis.trs < 60) riskScore += 10;
    
    let riskLevel: 'low' | 'medium' | 'high';
    if (riskScore >= 50) riskLevel = 'high';
    else if (riskScore >= 25) riskLevel = 'medium';
    else riskLevel = 'low';
    
    return { riskLevel, riskScore: Math.min(riskScore, 100) };
  }

  private calculateRiskForProjection(raw: RawDetections, metrics: { 
    machineEfficiency: number; employeeActivity: number; trs: number;
    projectedProducts: number; factor: number;
  }): { riskLevel: 'low' | 'medium' | 'high'; riskScore: number } {
    
    let riskScore = 0;
    if (raw.machinesStopped > 0) riskScore += 30;
    if (raw.employesInactifs > 2) riskScore += 20;
    if (metrics.machineEfficiency < 70) riskScore += 25;
    if (metrics.employeeActivity < 60) riskScore += 15;
    if (metrics.trs < 60) riskScore += 10;
    if (metrics.factor > 100 && metrics.trs > 90) riskScore += 5;
    
    let riskLevel: 'low' | 'medium' | 'high';
    if (riskScore >= 50) riskLevel = 'high';
    else if (riskScore >= 25) riskLevel = 'medium';
    else riskLevel = 'low';
    
    return { riskLevel, riskScore: Math.min(riskScore, 100) };
  }

  // ==========================================
  // 🎴 GENERATION DES CARTES UI
  // ==========================================
  private generateKpiCards(): void {
    if (!this.currentVideoKpi) return;
    const k = this.currentVideoKpi.kpis;
    const r = this.currentVideoKpi.raw;
    const isProjected = this.selectedPeriod !== 'video';
    
    this.kpiCards = [];
    
    this.kpiCards.push({ label: 'TRS Global', value: k.trs, unit: '%', trend: k.trs >= 85 ? 'up' : k.trs >= 70 ? 'stable' : 'down', trendValue: 0, color: k.trs >= 85 ? '#10b981' : k.trs >= 70 ? '#f59e0b' : '#ef4444', icon: 'fas fa-tachometer-alt', description: 'Taux de Rendement Synthetique' + (isProjected ? ' (estime)' : ''), category: 'production', isProjected });
    this.kpiCards.push({ label: 'Efficacite Machines', value: k.machineEfficiency, unit: '%', trend: k.machineEfficiency >= 90 ? 'up' : 'stable', trendValue: 0, color: k.machineEfficiency >= 90 ? '#10b981' : k.machineEfficiency >= 70 ? '#f59e0b' : '#ef4444', icon: 'fas fa-cogs', description: `${r.machines} actives / ${r.machines + r.machinesStopped} totales`, category: 'production', isProjected: false });
    this.kpiCards.push({ label: 'OEE', value: k.oee, unit: '%', trend: k.oee >= 85 ? 'up' : 'stable', color: '#6366f1', icon: 'fas fa-chart-line', description: 'Overall Equipment Effectiveness' + (isProjected ? ' (estime)' : ''), category: 'production', isProjected });
    
    this.kpiCards.push({ label: 'Activite Employes', value: k.employeeActivity, unit: '%', trend: k.employeeActivity >= 85 ? 'up' : 'stable', trendValue: 0, color: k.employeeActivity >= 85 ? '#10b981' : k.employeeActivity >= 60 ? '#f59e0b' : '#ef4444', icon: 'fas fa-users', description: `${r.employesActifs} actifs / ${r.employees + r.employesActifs + r.employesInactifs} totaux`, category: 'rh', isProjected: false });
    this.kpiCards.push({ label: 'Productivite', value: k.productivity, unit: 'prod/emp', trend: k.productivity >= 5 ? 'up' : 'stable', color: '#3b82f6', icon: 'fas fa-boxes', description: 'Produits par employe' + (isProjected ? ' (estime)' : ''), category: 'rh', isProjected });
    
    if (r.tables > 0) {
      this.kpiCards.push({ label: 'Occupation Tables', value: k.tableOccupancy, unit: '%', trend: k.tableOccupancy >= 75 ? 'up' : 'stable', color: k.tableOccupancy >= 75 ? '#10b981' : '#8b5cf6', icon: 'fas fa-table', description: `${r.tables - r.tablesEmpty}/${r.tables} utilisees`, category: 'logistique', isProjected: false });
    }
    if (r.clients > 0) {
      this.kpiCards.push({ label: 'Niveau Service', value: k.serviceLevel, unit: 'cli/emp', color: '#6366f1', icon: 'fas fa-user-tie', description: 'Clients par employe' + (isProjected ? ' (estime)' : ''), category: 'logistique', isProjected });
    }
    
    this.kpiCards.push({ label: 'Score Qualite', value: k.qualityScore, unit: '%', trend: k.qualityScore >= 85 ? 'up' : 'stable', color: k.qualityScore >= 85 ? '#10b981' : k.qualityScore >= 70 ? '#f59e0b' : '#ef4444', icon: 'fas fa-star', description: 'Indice de qualite global' + (isProjected ? ' (estime)' : ''), category: 'qualite', isProjected });
    this.kpiCards.push({ label: 'Disponibilite', value: k.uptime, unit: '%', trend: k.uptime >= 90 ? 'up' : 'stable', color: '#10b981', icon: 'fas fa-check-circle', description: 'Uptime des equipements', category: 'qualite', isProjected: false });
    this.kpiCards.push({ label: 'Debit Production', value: k.throughput, unit: '%', trend: k.throughput >= 80 ? 'up' : 'stable', color: '#6366f1', icon: 'fas fa-shipping-fast', description: 'Cadence de production' + (isProjected ? ' (estimee)' : ''), category: 'qualite', isProjected });
    this.kpiCards.push({ label: 'Indice Performance', value: k.performanceIndex, unit: '%', trend: k.performanceIndex >= 85 ? 'up' : 'stable', color: k.performanceIndex >= 85 ? '#10b981' : k.performanceIndex >= 70 ? '#f59e0b' : '#ef4444', icon: 'fas fa-trophy', description: 'Performance globale' + (isProjected ? ' (estimee)' : ''), category: 'qualite', isProjected });
  }

  private generateAlerts(): void {
    this.activeAlerts = [];
    if (!this.currentVideoKpi) return;
    
    const k = this.currentVideoKpi.kpis;
    const r = this.currentVideoKpi.raw;
    const isProjected = this.selectedPeriod !== 'video';
    const note = isProjected ? ' (estime)' : '';
    
    if (r.machinesStopped > 0) this.activeAlerts.push({ type: 'machine', message: `${r.machinesStopped} machine(s) a l'arret - Impact production`, severity: 'critical' });
    if (k.trs < 70) this.activeAlerts.push({ type: 'performance', message: `TRS${note} critique a ${k.trs}% (objectif: 85%)`, severity: 'critical' });
    if (k.employeeActivity < 70) this.activeAlerts.push({ type: 'rh', message: `Activite employes${note} faible: ${k.employeeActivity}%`, severity: 'warning' });
    if (r.tables > 0 && k.tableOccupancy < 50) this.activeAlerts.push({ type: 'logistique', message: `Occupation tables${note} faible: ${k.tableOccupancy}%`, severity: 'warning' });
    
    if (this.activeAlerts.length === 0) {
      this.activeAlerts.push({ type: 'success', message: isProjected ? 'Tous indicateurs estimes dans les objectifs' : 'Tous indicateurs reels dans les objectifs', severity: 'info' });
    }
  }

  // ==========================================
  // 📊 GRAPHIQUES CHART.JS
  // ==========================================
  private createCharts(): void {
    setTimeout(() => {
      this.createRadarChart();
      this.createTrendChart();
      this.createQualityChart();
      this.createGaugeCharts();
      this.cdr.detectChanges(); // ✅ AJOUT : Force mise à jour après création graphiques
    }, 200);
  }

  private createRadarChart(): void {
    const canvas = document.getElementById('radarChart') as HTMLCanvasElement;
    if (!canvas) return;
    if (this.charts['radar']) this.charts['radar'].destroy();
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const k = this.currentVideoKpi?.kpis;
    if (!k) return;
    
    this.charts['radar'] = new Chart(ctx, {
      type: 'radar',
      data: {
        labels: ['Efficacite Machines', 'Activite RH', 'Occupation', 'Productivite', 'TRS'],
        datasets: [{
          label: 'Performance (%)',
          data: [k.machineEfficiency, k.employeeActivity, k.tableOccupancy, Math.min(k.productivity * 20, 100), k.trs],
          backgroundColor: 'rgba(99, 102, 241, 0.2)',
          borderColor: '#6366f1',
          pointBackgroundColor: '#6366f1',
          pointBorderColor: '#fff',
          pointBorderWidth: 3,
          pointRadius: 6,
          borderWidth: 3
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        scales: {
          r: {
            beginAtZero: true, max: 100,
            ticks: { stepSize: 20, font: { size: 11, weight: 'bold' }, color: '#64748b' },
            grid: { color: '#e2e8f0' },
            pointLabels: { font: { size: 12, weight: 'bold' }, color: '#475569' }
          }
        },
        plugins: { legend: { display: false } }
      }
    });
  }

  private createTrendChart(): void {
    const canvas = document.getElementById('trendChart') as HTMLCanvasElement;
    if (!canvas) return;
    if (this.charts['trend']) this.charts['trend'].destroy();
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    const labels = this.historicalKpis.map((h, i) => `V${this.historicalKpis.length - i}`);
    const trsData = this.historicalKpis.map(h => h.kpis.trs);
    const machineData = this.historicalKpis.map(h => h.kpis.machineEfficiency);
    
    this.charts['trend'] = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [
          { label: 'TRS (%)', data: trsData, borderColor: '#6366f1', backgroundColor: '#6366f120', tension: 0.4, fill: true, borderWidth: 3, pointRadius: 5, pointBackgroundColor: '#6366f1', pointBorderColor: '#fff', pointBorderWidth: 2 },
          { label: 'Efficacite Machines (%)', data: machineData, borderColor: '#10b981', backgroundColor: 'transparent', tension: 0.4, borderWidth: 2, pointRadius: 4, pointBackgroundColor: '#10b981', pointBorderColor: '#fff', pointBorderWidth: 2, borderDash: [5, 5] }
        ]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { position: 'top', labels: { font: { size: 12, weight: 'bold' }, padding: 15, usePointStyle: true } } },
        scales: {
          y: { beginAtZero: true, max: 100, grid: { color: '#f1f5f9' }, ticks: { stepSize: 20, font: { size: 11 }, color: '#64748b', callback: (value) => value + '%' } },
          x: { grid: { display: false }, ticks: { font: { size: 11 }, color: '#64748b' } }
        }
      }
    });
  }

  private createQualityChart(): void {
    const canvas = document.getElementById('qualityChart') as HTMLCanvasElement;
    if (!canvas) return;
    if (this.charts['quality']) this.charts['quality'].destroy();
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const k = this.currentVideoKpi?.kpis;
    if (!k) return;
    
    this.charts['quality'] = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: ['Score Qualite', 'Disponibilite', 'Debit', 'Performance'],
        datasets: [{
          data: [k.qualityScore, k.uptime, k.throughput, k.performanceIndex],
          backgroundColor: ['#10b981', '#6366f1', '#8b5cf6', '#f59e0b'],
          borderRadius: 8,
          barThickness: 50
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: false, indexAxis: 'y',
        plugins: {
          legend: { display: false },
          tooltip: { callbacks: { label: (context) => { const value = context.parsed.x; return value !== null ? `${value}%` : ''; } } }
        },
        scales: {
          x: { beginAtZero: true, max: 100, grid: { color: '#f1f5f9' }, ticks: { font: { size: 11 }, color: '#64748b', callback: (value) => value + '%' } },
          y: { grid: { display: false }, ticks: { font: { size: 12, weight: 'bold' }, color: '#475569' } }
        }
      }
    });
  }

  private createGaugeCharts(): void {
    const gauges = [
      { id: 'gaugeTRS', value: this.currentVideoKpi?.kpis.trs || 0, max: 100, color: '#6366f1' },
      { id: 'gaugeMachines', value: this.currentVideoKpi?.kpis.machineEfficiency || 0, max: 100, color: '#10b981' },
      { id: 'gaugeEmployees', value: this.currentVideoKpi?.kpis.employeeActivity || 0, max: 100, color: '#3b82f6' }
    ];
    
    gauges.forEach(gauge => {
      const canvas = document.getElementById(gauge.id) as HTMLCanvasElement;
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      if (!ctx) return;
      
      const size = 150;
      canvas.width = size; canvas.height = size;
      const centerX = size / 2; const centerY = size / 2; const radius = size / 2 - 10;
      
      ctx.beginPath(); ctx.arc(centerX, centerY, radius, 0, 2 * Math.PI);
      ctx.strokeStyle = '#e2e8f0'; ctx.lineWidth = 12; ctx.stroke();
      
      const percentage = gauge.value / gauge.max;
      const endAngle = -Math.PI / 2 + (2 * Math.PI * percentage);
      
      ctx.beginPath(); ctx.arc(centerX, centerY, radius, -Math.PI / 2, endAngle);
      ctx.strokeStyle = gauge.color; ctx.lineWidth = 12; ctx.lineCap = 'round'; ctx.stroke();
      
      ctx.fillStyle = '#0f172a'; ctx.font = 'bold 32px sans-serif';
      ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.fillText(`${gauge.value}%`, centerX, centerY);
    });
  }

  // ==========================================
  // 📄 EXPORT PDF PROFESSIONNEL
  // ==========================================
  public exportToPDF(): void {
    if (!this.currentVideoKpi) {
      alert('Aucune donnee a exporter');
      return;
    }

    const doc = new jsPDF();
    const pageWidth = doc.internal.pageSize.getWidth();
    const pageHeight = doc.internal.pageSize.getHeight();
    let yPosition = 20;

    // --- PAGE 1: COUVERTURE ---
    doc.setFillColor(99, 102, 241);
    doc.rect(0, 0, pageWidth, 85, 'F');
    doc.setFillColor(79, 70, 229);
    doc.rect(0, 85, pageWidth, 3, 'F');
    
    doc.setFillColor(255, 255, 255);
    doc.circle(pageWidth / 2, 35, 18, 'F');
    doc.setFillColor(99, 102, 241);
    doc.setFontSize(24);
    doc.setFont('helvetica', 'bold');
    doc.text('CF', pageWidth / 2, 40, { align: 'center' });
    
    doc.setTextColor(255, 255, 255);
    doc.setFontSize(28);
    doc.setFont('helvetica', 'bold');
    doc.text('RAPPORT D ANALYSE', pageWidth / 2, 62, { align: 'center' });
    doc.setFontSize(16);
    doc.setFont('helvetica', 'normal');
    doc.text('CAMIA-FACTORY', pageWidth / 2, 72, { align: 'center' });
    
    doc.setFontSize(10);
    doc.setFont('helvetica', 'italic');
    doc.text('Systeme de Surveillance Intelligente', pageWidth / 2, 80, { align: 'center' });
    
    yPosition = 100;
    
    doc.setFillColor(248, 250, 252);
    doc.roundedRect(15, yPosition, pageWidth - 30, 55, 4, 4, 'F');
    doc.setFillColor(99, 102, 241);
    doc.rect(15, yPosition, 4, 55, 'F');
    
    doc.setTextColor(15, 23, 42);
    doc.setFontSize(12);
    doc.setFont('helvetica', 'bold');
    doc.text('INFORMATIONS DE L ANALYSE', 25, yPosition + 10);
    
    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(51, 65, 85);
    
    const videoName = this.currentVideoKpi.filename.replace(' - Duree de la video', '').replace(' - Projection', '').substring(0, 50);
    
    doc.text('Fichier video :', 25, yPosition + 22);
    doc.setFont('helvetica', 'bold');
    doc.text(videoName, 60, yPosition + 22);
    
    doc.setFont('helvetica', 'normal');
    doc.text('Date d analyse :', 25, yPosition + 30);
    doc.setFont('helvetica', 'bold');
    const analyseDate = new Date().toLocaleDateString('fr-FR', { day: '2-digit', month: 'long', year: 'numeric' });
    doc.text(analyseDate, 60, yPosition + 30);
    
    doc.setFont('helvetica', 'normal');
    doc.text('Periode analysee :', 25, yPosition + 38);
    doc.setFont('helvetica', 'bold');
    doc.text(this.getPeriodLabel(), 65, yPosition + 38);
    
    doc.setFont('helvetica', 'normal');
    doc.text('Duree video :', 25, yPosition + 46);
    doc.setFont('helvetica', 'bold');
    doc.text(`${this.videoDuration} secondes`, 55, yPosition + 46);
    
    yPosition += 70;
    
    const scoreGlobal = this.currentVideoKpi.kpis.qualityScore;
    const scoreColor = scoreGlobal >= 85 ? [16, 185, 129] : scoreGlobal >= 70 ? [245, 158, 11] : [239, 68, 68];
    
    doc.setFillColor(scoreColor[0], scoreColor[1], scoreColor[2]);
    doc.roundedRect(15, yPosition, pageWidth - 30, 38, 4, 4, 'F');
    
    doc.setTextColor(255, 255, 255);
    doc.setFontSize(14);
    doc.setFont('helvetica', 'bold');
    doc.text('SCORE GLOBAL DE PERFORMANCE', pageWidth / 2, yPosition + 13, { align: 'center' });
    
    doc.setFontSize(32);
    doc.text(`${scoreGlobal}%`, pageWidth / 2, yPosition + 28, { align: 'center' });
    
    yPosition += 50;
    
    doc.setTextColor(15, 23, 42);
    doc.setFontSize(13);
    doc.setFont('helvetica', 'bold');
    doc.text('RESUME EXECUTIF', 15, yPosition);
    yPosition += 3;
    
    doc.setDrawColor(99, 102, 241);
    doc.setLineWidth(0.5);
    doc.line(15, yPosition, 65, yPosition);
    yPosition += 7;
    
    doc.setFillColor(241, 245, 249);
    doc.roundedRect(15, yPosition, pageWidth - 30, 48, 4, 4, 'F');
    
    doc.setFontSize(9.5);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(51, 65, 85);
    
    const r = this.currentVideoKpi.raw;
    const k = this.currentVideoKpi.kpis;
    
    const resumeText = `Cette analyse porte sur une periode de ${this.videoDuration} secondes de surveillance de l'usine. Durant cette periode, ${r.machines} machine(s) etai(en)t active(s) sur un total de ${r.machines + r.machinesStopped}, avec ${r.employesActifs} employe(s) actif(s) sur ${r.employees + r.employesActifs + r.employesInactifs} au total. La production a genere ${r.products} produit(s) avec un TRS de ${k.trs}%, indiquant une performance ${k.trs >= 85 ? 'excellente' : k.trs >= 70 ? 'satisfaisante' : 'critique'}. Le niveau de risque operationnel est ${k.riskLevel === 'low' ? 'faible' : k.riskLevel === 'medium' ? 'modere' : 'eleve'}.`;
    
    const resumeLines = doc.splitTextToSize(resumeText, pageWidth - 40);
    resumeLines.forEach((line: string, index: number) => {
      doc.text(line, 20, yPosition + 7 + (index * 5));
    });
    
    doc.setFillColor(248, 250, 252);
    doc.rect(0, pageHeight - 15, pageWidth, 15, 'F');
    doc.setFontSize(8);
    doc.setTextColor(100, 116, 139);
    doc.setFont('helvetica', 'normal');
    doc.text('CAMIA-Factory - Systeme de Surveillance Intelligente', pageWidth / 2, pageHeight - 8, { align: 'center' });
    doc.setFont('helvetica', 'italic');
    doc.setFontSize(7);
    doc.text('Document confidentiel - Usage interne uniquement', pageWidth / 2, pageHeight - 4, { align: 'center' });

    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').split('T')[0];
    const filename = `CAMIA_Rapport_${timestamp}_${Date.now()}.pdf`;
    doc.save(filename);
    console.log('Rapport PDF professionnel genere:', filename);
  }

  // ==========================================
  // 📊 EXPORT EXCEL
  // ==========================================
  public exportToExcel(): void {
    if (!this.currentVideoKpi) {
      alert('Aucune donnee a exporter');
      return;
    }

    const wb = XLSX.utils.book_new();
    const r = this.currentVideoKpi.raw;
    const k = this.currentVideoKpi.kpis;
    
    const infoData = [
      ['RAPPORT D ANALYSE CAMIA-FACTORY'],
      [''],
      ['Fichier analyse', this.currentVideoKpi.filename],
      ['Date d analyse', this.currentVideoKpi.timestamp],
      ['Periode', this.getPeriodLabel()],
      ['Date de generation', new Date().toLocaleString('fr-FR')]
    ];
    const wsInfo = XLSX.utils.aoa_to_sheet(infoData);
    XLSX.utils.book_append_sheet(wb, wsInfo, 'Informations');

    const detectionsData = [
      ['Categorie', 'Valeur'],
      ['Machines actives', r.machines],
      ['Machines arretees', r.machinesStopped],
      ['Total machines', r.machines + r.machinesStopped],
      ['Employes actifs', r.employesActifs],
      ['Employes inactifs', r.employesInactifs],
      ['Total employes', r.employees + r.employesActifs + r.employesInactifs],
      ['Produits detectes', r.products],
      ['Clients', r.clients],
      ['Tables totales', r.tables],
      ['Tables vides', r.tablesEmpty],
      ['Tables utilisees', r.tables - r.tablesEmpty]
    ];
    const wsDetections = XLSX.utils.aoa_to_sheet(detectionsData);
    XLSX.utils.book_append_sheet(wb, wsDetections, 'Detections');

    const kpiData = [
      ['Indicateur', 'Valeur', 'Unite', 'Evaluation'],
      ['TRS Global', k.trs, '%', k.trs >= 85 ? 'Excellent' : k.trs >= 70 ? 'Acceptable' : 'Critique'],
      ['Efficacite Machines', k.machineEfficiency, '%', k.machineEfficiency >= 90 ? 'Excellent' : 'Acceptable'],
      ['OEE', k.oee, '%', k.oee >= 85 ? 'Excellent' : 'Acceptable'],
      ['Activite Employes', k.employeeActivity, '%', k.employeeActivity >= 85 ? 'Excellent' : 'Acceptable'],
      ['Productivite', k.productivity, 'prod/emp', k.productivity >= 5 ? 'Excellent' : 'Acceptable'],
      ['Occupation Tables', k.tableOccupancy, '%', k.tableOccupancy >= 75 ? 'Excellent' : 'Acceptable'],
      ['Score Qualite', k.qualityScore, '%', k.qualityScore >= 85 ? 'Excellent' : 'Acceptable'],
      ['Disponibilite', k.uptime, '%', k.uptime >= 90 ? 'Excellent' : 'Acceptable'],
      ['Debit Production', k.throughput, '%', k.throughput >= 80 ? 'Excellent' : 'Acceptable'],
      ['Indice Performance', k.performanceIndex, '%', k.performanceIndex >= 85 ? 'Excellent' : 'Acceptable']
    ];
    const wsKPI = XLSX.utils.aoa_to_sheet(kpiData);
    XLSX.utils.book_append_sheet(wb, wsKPI, 'KPI');

    const riskData = [
      ['EVALUATION DES RISQUES'],
      [''],
      ['Niveau de risque', this.getRiskLabel(k.riskLevel)],
      ['Score de risque', k.riskScore + '/100'],
      [''],
      ['ALERTES ACTIVES'],
      ['Type', 'Message', 'Severite']
    ];
    
    this.activeAlerts.forEach(alert => {
      riskData.push([alert.type, alert.message, alert.severity]);
    });
    
    const wsRisk = XLSX.utils.aoa_to_sheet(riskData);
    XLSX.utils.book_append_sheet(wb, wsRisk, 'Risques & Alertes');

    const timestamp = new Date().toISOString().split('T')[0];
    const filename = `CAMIA_Data_${timestamp}_${Date.now()}.xlsx`;
    XLSX.writeFile(wb, filename);
    console.log('Excel genere:', filename);
  }

  // ==========================================
  // 🛠️ UTILITAIRES
  // ==========================================
  private addPageFooter(doc: jsPDF, pageNumber: number): void {
    const pageWidth = doc.internal.pageSize.getWidth();
    const pageHeight = doc.internal.pageSize.getHeight();
    doc.setFillColor(248, 250, 252);
    doc.rect(0, pageHeight - 15, pageWidth, 15, 'F');
    doc.setFontSize(8);
    doc.setTextColor(100, 116, 139);
    doc.setFont('helvetica', 'normal');
    doc.text('CAMIA-Factory - Systeme de Surveillance Intelligente', pageWidth / 2, pageHeight - 8, { align: 'center' });
    doc.setFont('helvetica', 'italic');
    doc.setFontSize(7);
    doc.text(`Page ${pageNumber}`, pageWidth / 2, pageHeight - 4, { align: 'center' });
  }

  public getRiskColor(level: string): string {
    switch (level) { case 'high': return '#ef4444'; case 'medium': return '#f59e0b'; default: return '#10b981'; }
  }
  public getRiskLabel(level: string): string {
    switch (level) { case 'high': return 'CRITIQUE'; case 'medium': return 'ATTENTION'; default: return 'NORMAL'; }
  }
  public getTrendIcon(trend?: string): string {
    switch (trend) { case 'up': return 'fas fa-arrow-up'; case 'down': return 'fas fa-arrow-down'; default: return 'fas fa-minus'; }
  }
  public getPeriodLabel(): string {
    const labels: any = { 'video': 'Duree video', 'hour': 'Derniere heure', 'day': "Aujourd'hui", 'week': '7 derniers jours', 'month': '30 derniers jours' };
    return labels[this.selectedPeriod] || '';
  }
  public refresh(): void { this.loadKpiData(); }
  public navigateToVideo(videoId: string): void { this.router.navigate(['/admin/videos', videoId]); }
  public onPeriodChange(): void { 
    console.log(`🔄 Changement de periode: ${this.selectedPeriod}`); 
    this.loadKpiData(); 
  }
  
  get productionKPIs(): KPICard[] { return this.kpiCards.filter(k => k.category === 'production'); }
  get rhKPIs(): KPICard[] { return this.kpiCards.filter(k => k.category === 'rh'); }
  get logistiqueKPIs(): KPICard[] { return this.kpiCards.filter(k => k.category === 'logistique'); }
  get qualiteKPIs(): KPICard[] { return this.kpiCards.filter(k => k.category === 'qualite'); }
}