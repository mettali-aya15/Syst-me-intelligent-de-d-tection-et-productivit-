import { Component, OnInit, OnDestroy, AfterViewInit, inject, ChangeDetectorRef, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import Chart from 'chart.js/auto';
import jsPDF from 'jspdf';
import * as XLSX from 'xlsx';
// 🆕 AJOUT 1/4
import { KpiService, KPISnapshotData } from '../../../core/services/kpi.service';

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
  private cdr = inject(ChangeDetectorRef);
  // 🆕 AJOUT 2/4
  private kpiService = inject(KpiService);
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
  renderKey = 0;
  showContent = false; // ✅ AJOUTER ICI


  // ==========================================
  // 🔄 CYCLE DE VIE
  // ==========================================
  ngOnInit(): void {
  // ✅ FORCER la période par défaut au chargement
  this.selectedPeriod = 'video';
  
  this.projectionSummary = {
    period: 'Duree video',
    factor: 1,
    estimatedProducts: 0,
    estimatedThroughput: 0,
    machines: 0,
    employees: 0
  };
  this.showContent = false;
  this.refreshInterval = setInterval(() => this.loadKpiData(), 60000);
}
  
  // ✅ Double appel pour garantir l'affichage au chargement

  ngAfterViewInit(): void {
  setTimeout(() => {
    this.selectedPeriod = 'video';
    this.loadKpiData();
  }, 100);
}

  ngOnDestroy(): void {
    if (this.refreshInterval) clearInterval(this.refreshInterval);
    Object.values(this.charts).forEach(c => c?.destroy());
  }

  // ==========================================
  // 📊 CHARGEMENT DES DONNEES
  // ==========================================
async loadKpiData(): Promise<void> {
  try {
    this.loading = true;
    this.showContent = false;
    this.cdr.detectChanges();

    if (this.selectedPeriod !== 'video') {
      const success = await this.loadTimeBasedKPIs();
      if (!success) await this.loadVideoBasedKPIs();
    } else {
      await this.loadVideoBasedKPIs();
    }

    this.loading = false;
    this.showContent = true;
    this.cdr.detectChanges();

    setTimeout(() => {
      this.createCharts();
      this.cdr.detectChanges();
    }, 200);

  } catch (error) {
    console.error('❌ Erreur chargement KPI:', error);
    this.loading = false;
    this.showContent = true;
    this.cdr.detectChanges();
  }
}
private async loadVideoBasedKPIs(): Promise<void> {
  const noCache = { headers: { 'Cache-Control': 'no-cache', 'Pragma': 'no-cache' } };

  const videos = await this.http.get<any[]>(`${this.apiUrl}/videos/`, noCache).toPromise() || [];
  
  const completed = videos.filter((v: any) => v.status === 'completed') || [];
  if (completed.length === 0) { 
    this.loading = false; 
    return; 
  }
  
  const latestVideo = completed.sort((a: any, b: any) => 
    new Date(b.created_at || b.uploaded_at).getTime() - new Date(a.created_at || a.uploaded_at).getTime()
  )[0];

  this.videoDuration = Number(latestVideo?.duration) || 60;

  try {
    const detectionData = await this.http.get<any>(
      `http://localhost:8000/api/v1/detections/video/${latestVideo._id}`, noCache
    ).toPromise();
    latestVideo.classes_detectees = detectionData?.classes_detectees || {};
    console.log('📊 classes_detectees récupérées:', latestVideo.classes_detectees);
  } catch (err) {
    console.warn('⚠️ Impossible de récupérer les détections:', err);
    latestVideo.classes_detectees = {};
  }

  const historicalVideos = completed.slice(0, 7);
  for (const v of historicalVideos) {
    try {
      const det = await this.http.get<any>(
        `http://localhost:8000/api/v1/detections/video/${v._id}`, noCache
      ).toPromise();
      v.classes_detectees = det?.classes_detectees || {};
    } catch {
      v.classes_detectees = {};
    }
  }

  const baseKPIs = this.calculateKPIsSync(latestVideo);

this.currentVideoKpi = { ...this.projectPerformanceKPIs(baseKPIs, latestVideo) };
this.updateProjectionSummary(baseKPIs.raw, latestVideo);
this.historicalKpis = [...historicalVideos.map((v: any) => this.calculateKPIsSync(v))];
this.kpiCards = [];
this.generateKpiCards();
this.activeAlerts = [];
this.generateAlerts();
this.showContent = true;
this.cdr.detectChanges();
setTimeout(() => {
  this.createCharts();
  this.cdr.detectChanges();
}, 200);

console.log('💾 Sauvegarde des KPIs vidéo dans MongoDB...');
await this.saveKPIsToDB(baseKPIs, latestVideo, 'video');
console.log('✅ KPIs sauvegardés dans MongoDB !');
}
  private async loadTimeBasedKPIs(): Promise<boolean> {
  const url = `${this.apiUrl}/kpis/latest?periode=${this.selectedPeriod}`;
  
  console.log(`⏳ Attente 3s avant GET ${url}`);
  await new Promise(resolve => setTimeout(resolve, 3000));
  
  try {
    console.log(`📡 Requête GET: ${url}`);
    const response = await this.http.get<any>(url).toPromise();
    
    console.log('📦 Response brute du backend:', response);
    
    const kpiData = response?.data || response;
    
    console.log('🔍 kpiData extrait:', kpiData);
    
    if (!kpiData || Object.keys(kpiData).length === 0) {
      console.warn('⚠️ kpiData est vide!');
      return false;
    }
    
    const machines = kpiData.machines || {};
    const production = kpiData.production || {};
    const employes = kpiData.employes || {};
    
    console.log('✅ Données extraites:', { machines, production, employes });

    const raw: RawDetections = {
      machines: machines.machines_actives || machines.total_machines || 0,
      machinesStopped: machines.machines_arretees || 0,
      employees: employes.total_employes || 0,
      employesActifs: employes.employes_actifs || 0,
      employesInactifs: employes.employes_inactifs || 0,
      products: production.unites_produites || production.total_produits || 0,
      clients: 0, 
      tables: 0, 
      tablesEmpty: 0
    };
    
    const kpis: CalculatedKPIs = {
      trs: machines.trs || 0,
      machineEfficiency: machines.performance || 0,
      oee: machines.trs || 0,
      employeeActivity: employes.taux_activite || 0,
      employeeEngagement: employes.taux_presence || 0,
      productivity: employes.productivite_par_employe || 0,
      qualityScore: machines.qualite || production.taux_conformite || 0,
      uptime: machines.disponibilite || 0,
      throughput: production.cadence_production || 0,
      performanceIndex: machines.performance || 0,
      tableOccupancy: 0, 
      serviceLevel: 0,
      riskLevel: 'low', 
      riskScore: 0
    };
    
    const trsValue = kpis.trs;
    kpis.riskLevel = trsValue >= 85 ? 'low' : trsValue >= 70 ? 'medium' : 'high';
    kpis.riskScore = trsValue >= 85 ? 10 : trsValue >= 70 ? 30 : 60;
    
    console.log('✅ KPIs finaux:', {
      trs: kpis.trs,
      machineEfficiency: kpis.machineEfficiency,
      employeeActivity: kpis.employeeActivity,
      productivity: kpis.productivity,
      riskLevel: kpis.riskLevel
    });
    
    // ✅ CRÉER UN OBJET latestVideo FICTIF
    const dummyVideo = {
      _id: 'time-based-' + this.selectedPeriod,
      filename: `Période: ${this.getPeriodLabel()}`,
      created_at: new Date(kpiData.date_debut || new Date()).toISOString(),
      duration: this.getDurationForPeriod()
    };
    
    this.currentVideoKpi = {
      videoId: 'time-based-' + this.selectedPeriod,
      filename: `Période: ${this.getPeriodLabel()}`,
      timestamp: new Date().toLocaleString('fr-FR'),
      uploadedAt: new Date(),
      raw, kpis
    };
    
    console.log('✅ currentVideoKpi MIS À JOUR');
    
    this.updateProjectionSummary(raw, { duration: this.getDurationForPeriod() });
    this.generateKpiCards();
    this.generateAlerts();
    this.createCharts();
    this.cdr.detectChanges();
    
    // ✅ MAINTENANT UTILISER dummyVideo
    console.log('💾 Sauvegarde des KPIs vidéo dans MongoDB...');
    await this.saveKPIsToDB(this.currentVideoKpi, dummyVideo, this.selectedPeriod);
    console.log('✅ KPIs vidéo sauvegardés !');
    
    return true;
    
  } catch (error: any) {
    console.error(`❌ Erreur GET ${url}:`, {
      message: error?.message,
      status: error?.status,
      error: error?.error
    });
    return false;
  }
}
private updateProjectionSummary(baseRaw: RawDetections, videoData: any): void {
  const durationSeconds = Number(videoData?.duration) || this.videoDuration || 60;

  let factor = 1;
  switch (this.selectedPeriod) {
    case 'video': factor = 1; break;
    case 'hour': factor = 3600 / durationSeconds; break;
    case 'day': factor = 86400 / durationSeconds; break;
    case 'week': factor = 604800 / durationSeconds; break;
    case 'month': factor = 2592000 / durationSeconds; break;
  }

  this.projectionSummary = JSON.parse(JSON.stringify({
    period: this.getPeriodLabel(),
    factor: Math.round(factor * 100) / 100,
    machines: baseRaw.machines,
    employees: baseRaw.employesActifs || baseRaw.employees,
    estimatedProducts: Math.round(baseRaw.products * factor),
    estimatedThroughput: Math.round((baseRaw.products / durationSeconds) * factor * 3600)
  }));

  this.renderKey++;
  this.cdr.detectChanges();
}

private projectPerformanceKPIs(baseVideo: VideoKPI, videoData: any): VideoKPI {
  const durationSeconds = Number(videoData?.duration) || 60;
  this.videoDuration = durationSeconds;
  
  let projectionFactor = 1, periodLabel = '';
  switch (this.selectedPeriod) {
    case 'video': projectionFactor = 1; periodLabel = 'Duree de la video'; break;
    case 'hour': projectionFactor = 3600 / durationSeconds; periodLabel = 'Projection 1 heure'; break;
    case 'day': projectionFactor = 86400 / durationSeconds; periodLabel = 'Projection 1 journee'; break;
    case 'week': projectionFactor = 604800 / durationSeconds; periodLabel = 'Projection 1 semaine'; break;
    case 'month': projectionFactor = 2592000 / durationSeconds; periodLabel = 'Projection 1 mois'; break;
  }
  
  // ✅ raw : machines et employés restent pareils (ratios), seules les quantités sont projetées
  const raw: RawDetections = {
    machines: baseVideo.raw.machines,
    machinesStopped: baseVideo.raw.machinesStopped,
    employees: baseVideo.raw.employees,
    employesActifs: baseVideo.raw.employesActifs,        // ✅ pas de projection
    employesInactifs: baseVideo.raw.employesInactifs,    // ✅ pas de projection
    products: Math.round(baseVideo.raw.products * projectionFactor),
    clients: Math.round(baseVideo.raw.clients * projectionFactor),
    tables: baseVideo.raw.tables,
    tablesEmpty: baseVideo.raw.tablesEmpty               // ✅ pas de projection
  };
  
  // ✅ CALCULER LES KPIs AVEC LES RAW PROJETÉS
  const projectedProducts = raw.products;  // Utilise le raw projeté
  const totalMachines = raw.machines + raw.machinesStopped;
  const totalEmployees = raw.employees + raw.employesActifs + raw.employesInactifs;
  const activeEmployees = raw.employesActifs || raw.employees;
  
  const machineEfficiency = totalMachines > 0 ? Math.round((raw.machines / totalMachines) * 100) : 0;
  const availability = totalMachines > 0 ? (raw.machines / totalMachines) : 0;
  const performance = raw.machines > 0 ? Math.min((projectedProducts / (raw.machines * 10 * projectionFactor)), 1) : 0;
  const quality = 0.98;
  const trs = Math.round(availability * performance * quality * 100);
  const employeeActivity = totalEmployees > 0 ? Math.round((activeEmployees / totalEmployees) * 100) : 0;
  const productivity = activeEmployees > 0 ? Math.round(projectedProducts / activeEmployees) : 0;
  const tableOccupancy = raw.tables > 0 ? Math.round(((raw.tables - raw.tablesEmpty) / raw.tables) * 100) : 0;
  const projectedClients = raw.clients;
  const serviceLevel = activeEmployees > 0 ? Math.round((projectedClients / activeEmployees) * 10) / 10 : 0;
  const qualityScore = Math.round((trs + machineEfficiency + employeeActivity) / 3);
  const throughput = projectedProducts > 0 ? Math.min(projectedProducts * 10, 100) : 0;
  const performanceIndex = Math.round((qualityScore + throughput) / 2);
  const { riskLevel, riskScore } = this.calculateRiskForProjection(raw, { 
    machineEfficiency, employeeActivity, trs, projectedProducts, factor: projectionFactor 
  });
  
  return {
    videoId: 'projected',
    filename: `${videoData?.filename} - ${periodLabel}`,
    timestamp: `Base sur l'analyse du ${baseVideo.timestamp}`,
    uploadedAt: baseVideo.uploadedAt, 
    raw,  // ✅ MAINTENANT raw CONTIENT LES VALEURS PROJETÉES
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

  // 🆕 MODIFICATION 3/4 : Ajout async + Promise
  private calculateKPIsSync(video: any): VideoKPI {
    const obj = video?.classes_detectees || {};

    const employees = Number(obj['employe'] || obj['employé'] || obj['employes'] || obj['employés'] || obj['employee'] || obj['employees'] || 0);
    const employesActifs = Number(obj['employe actif'] || obj['employé actif'] || obj['employes actifs'] || obj['employés actifs'] || obj['employee active'] || obj['employees active'] || employees);
    const employesInactifs = Number(obj['employe inactif'] || obj['employé inactif'] || obj['employes inactifs'] || obj['employés inactifs'] || obj['employee inactive'] || obj['employees inactive'] || 0);
    
    const raw: RawDetections = {
      machines: Number(obj['machine'] || obj['machines'] || 0),
      machinesStopped: Number(obj['machine arretee'] || obj['machine arrêtée'] || obj['machines arretees'] || 0),
      employees, employesActifs, employesInactifs,
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
    const productivity = activeEmployees > 0 ? Math.round(raw.products / activeEmployees) : 0;
    const tableOccupancy = raw.tables > 0 ? Math.round(((raw.tables - raw.tablesEmpty) / raw.tables) * 100) : 0;
    const serviceLevel = activeEmployees > 0 ? Math.round((raw.clients / activeEmployees) * 10) / 10 : 0;
    const qualityScore = Math.round((trs + machineEfficiency + employeeActivity) / 3);
    const throughput = raw.products > 0 ? Math.min(raw.products * 10, 100) : 0;
    const performanceIndex = Math.round((qualityScore + throughput) / 2);
    const { riskLevel, riskScore } = this.calculateRisk(raw, { machineEfficiency, employeeActivity, trs });
    
    return {
      videoId: video?._id,
      filename: video?.filename,
      timestamp: new Date(video?.created_at || video?.uploaded_at).toLocaleString('fr-FR'),
      uploadedAt: new Date(video?.created_at || video?.uploaded_at),
      raw,
      kpis: {
        trs, machineEfficiency, oee: trs, employeeActivity, productivity,
        employeeEngagement: employeeActivity, tableOccupancy, serviceLevel, qualityScore,
        uptime: machineEfficiency, throughput, performanceIndex, riskLevel, riskScore
      }
    };
}

  // 🆕 AJOUT 4/4 : Nouvelle fonction complète
  private async saveKPIsToDB(videoKPI: VideoKPI, videoData: any, forcePeriod?: string): Promise<void> {
  try {
    // 🔍 DEBUG: Afficher la période sélectionnée
    console.log('📊 Sauvegarde KPI - Période sélectionnée:', this.selectedPeriod);
    
    const kpiData: KPISnapshotData = {
      video_analysis_id: videoKPI.videoId,
      periode: forcePeriod || this.selectedPeriod,  // ✅ Utilise forcePeriod en priorité
      date_debut: new Date(videoData?.processed_at || videoData?.created_at).toISOString(),
      date_fin: new Date().toISOString(),
    };

    if (videoKPI.raw.products > 0) {
      kpiData.production = {
        taux_productivite: videoKPI.kpis.trs,
        objectif_production: 1000,
        taux_conformite: 95,
        cadence_production: videoKPI.kpis.throughput,
        unites_produites: videoKPI.raw.products,
        objectif_unites: 1000,
        produits_conformes: Math.round(videoKPI.raw.products * 0.95),
        total_produits: videoKPI.raw.products
      };
    }

    if (videoKPI.raw.machines > 0 || videoKPI.raw.machinesStopped > 0) {
      kpiData.machines = {
        trs: videoKPI.kpis.trs,
        disponibilite: videoKPI.kpis.uptime,
        performance: videoKPI.kpis.performanceIndex,
        qualite: videoKPI.kpis.qualityScore,
        taux_panne: videoKPI.raw.machinesStopped > 0 ? 
          (videoKPI.raw.machinesStopped / (videoKPI.raw.machines + videoKPI.raw.machinesStopped)) * 100 : 0,
        mtbf: 0,
        mttr: 45,
        total_machines: videoKPI.raw.machines + videoKPI.raw.machinesStopped,
        machines_actives: videoKPI.raw.machines,
        machines_arretees: videoKPI.raw.machinesStopped,
        temps_productif: this.videoDuration / 60,
        temps_total: this.videoDuration / 60
      };
    }

    const totalEmployees = videoKPI.raw.employees + videoKPI.raw.employesActifs + videoKPI.raw.employesInactifs;
    if (totalEmployees > 0) {
      kpiData.employes = {
        taux_presence: 100,
        taux_activite: videoKPI.kpis.employeeActivity,
        productivite_par_employe: videoKPI.kpis.productivity,
        taux_inactivite: videoKPI.raw.employesInactifs > 0 ? 
          (videoKPI.raw.employesInactifs / totalEmployees) * 100 : 0,
        total_employes: totalEmployees,
        employes_presents: totalEmployees,
        employes_actifs: videoKPI.raw.employesActifs,
        employes_inactifs: videoKPI.raw.employesInactifs
      };
    }

    if (videoKPI.raw.tables > 0) {
      kpiData.tables = {
        total_tables: videoKPI.raw.tables,
        tables_occupees: videoKPI.raw.tables - videoKPI.raw.tablesEmpty,
        tables_vides: videoKPI.raw.tablesEmpty,
        taux_occupation: videoKPI.kpis.tableOccupancy
      };
    }

    if (videoKPI.raw.clients > 0) {
      kpiData.clients = {
        total_clients: videoKPI.raw.clients,
        clients_en_attente: Math.round(videoKPI.raw.clients * 0.1),
        clients_servis: Math.round(videoKPI.raw.clients * 0.9),
        taux_service: 90
      };
    }

    // 🔍 DEBUG: Afficher les données avant envoi
    console.log('📤 Envoi KPI vers backend:', {
      video_id: videoKPI.videoId,
      periode: kpiData.periode,  // ✅ Vérifier que c'est bien la bonne période
      sections: {
        production: !!kpiData.production,
        machines: !!kpiData.machines,
        employes: !!kpiData.employes,
        tables: !!kpiData.tables,
        clients: !!kpiData.clients
      }
    });

    await this.kpiService.saveKPIs(kpiData);
    console.log('✅ KPIs sauvegardés automatiquement dans MongoDB');

  } catch (error: any) {
    console.error('⚠️ Erreur sauvegarde KPIs (non bloquant):', {
      message: error?.message,
      status: error?.status,
      error: error
    });
  }
}

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

  private createCharts(): void {
    setTimeout(() => {
      this.createRadarChart();
      this.createTrendChart();
      this.createQualityChart();
      this.createGaugeCharts();
      this.cdr.detectChanges();
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
          backgroundColor: 'rgba(99, 102, 241, 0.2)', borderColor: '#6366f1',
          pointBackgroundColor: '#6366f1', pointBorderColor: '#fff', pointBorderWidth: 3, pointRadius: 6, borderWidth: 3
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        scales: {
          r: { beginAtZero: true, max: 100, ticks: { stepSize: 20, font: { size: 11, weight: 'bold' }, color: '#64748b' }, grid: { color: '#e2e8f0' }, pointLabels: { font: { size: 12, weight: 'bold' }, color: '#475569' } }
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
          y: { beginAtZero: true, max: 100, grid: { color: '#f1f5f9' }, ticks: { stepSize: 20, font: { size: 11 }, color: '#64748b', callback: (value: any) => value + '%' } },
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
          borderRadius: 8, barThickness: 50
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: false, indexAxis: 'y',
        plugins: { legend: { display: false }, tooltip: { callbacks: { label: (context: any) => { const value = context.parsed.x; return value !== null ? `${value}%` : ''; } } } },
        scales: {
          x: { beginAtZero: true, max: 100, grid: { color: '#f1f5f9' }, ticks: { font: { size: 11 }, color: '#64748b', callback: (value: any) => value + '%' } },
          y: { grid: { display: false }, ticks: { font: { size: 12, weight: 'bold' }, color: '#475569' } }
        }
      }
    });
  }

  private createGaugeCharts(): void {
    const gauges = [
      { id: 'gaugeTRS', value: this.currentVideoKpi?.kpis?.trs || 0, max: 100, color: '#6366f1' },
      { id: 'gaugeMachines', value: this.currentVideoKpi?.kpis?.machineEfficiency || 0, max: 100, color: '#10b981' },
      { id: 'gaugeEmployees', value: this.currentVideoKpi?.kpis?.employeeActivity || 0, max: 100, color: '#3b82f6' }
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

public async exportToPDF(): Promise<void> {
  if (!this.currentVideoKpi) { alert('Aucune donnee a exporter'); return; }
  
  const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
  const pageWidth = doc.internal.pageSize.getWidth();
  const pageHeight = doc.internal.pageSize.getHeight();
  const margin = 18;
  const contentWidth = pageWidth - (2 * margin);
  const r = this.currentVideoKpi.raw;
  const k = this.currentVideoKpi.kpis;
  const totalMachines = r.machines + r.machinesStopped;
  const totalEmployees = r.employees + r.employesActifs + r.employesInactifs;

  // ✅ HELPER: Formatter les grands nombres
  const formatNumber = (n: number): string => {
    if (n >= 1000000000) return (n / 1000000000).toFixed(1) + 'G';
    if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
    if (n >= 1000) return (n / 1000).toFixed(1) + 'K';
    return Number.isInteger(n) ? n.toString() : n.toFixed(1);
  };

  // ============================================================
  // PAGE 1 : COUVERTURE
  // ============================================================
  doc.setFillColor(15, 30, 60);
  doc.rect(0, 0, pageWidth, pageHeight, 'F');

  doc.setFillColor(25, 55, 110);
  doc.triangle(0, 0, pageWidth * 0.7, 0, 0, pageHeight * 0.6, 'F');

  doc.setFillColor(0, 120, 212);
  doc.rect(0, pageHeight * 0.72, pageWidth, 3, 'F');

  doc.setFillColor(0, 120, 212);
  doc.circle(margin + 18, 38, 14, 'F');
  doc.setFillColor(255, 255, 255);
  doc.circle(margin + 18, 38, 9, 'F');
  doc.setFillColor(0, 120, 212);
  doc.circle(margin + 18, 38, 4, 'F');

  doc.setTextColor(255, 255, 255);
  doc.setFontSize(11);
  doc.setFont('helvetica', 'normal');
  doc.text('CAMIA-FACTORY', margin + 36, 33);
  doc.setFontSize(8);
  doc.setTextColor(160, 190, 230);
  doc.text('Systeme Intelligent de Surveillance Industrielle', margin + 36, 40);

  doc.setDrawColor(0, 120, 212);
  doc.setLineWidth(0.4);
  doc.line(margin, 52, pageWidth - margin, 52);

  doc.setTextColor(255, 255, 255);
  doc.setFontSize(32);
  doc.setFont('helvetica', 'bold');
  doc.text('RAPPORT', margin, 80);
  doc.text("D'ANALYSE", margin, 96);
  doc.setFontSize(16);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(0, 120, 212);
  doc.text('Indicateurs de Performance Industrielle', margin, 110);

  const { scoreColor, scoreText } = this.getScoreBadge(k.qualityScore);
  doc.setFillColor(scoreColor[0], scoreColor[1], scoreColor[2]);
  doc.roundedRect(margin, 125, 75, 28, 4, 4, 'F');
  doc.setTextColor(255, 255, 255);
  doc.setFontSize(26);
  doc.setFont('helvetica', 'bold');
  doc.text(`${k.qualityScore}%`, margin + 10, 142);
  doc.setFontSize(9);
  doc.setFont('helvetica', 'normal');
  doc.text('SCORE GLOBAL', margin + 10, 149);

  doc.setFillColor(25, 55, 110);
  doc.roundedRect(margin + 82, 125, 55, 28, 4, 4, 'F');
  doc.setDrawColor(0, 120, 212);
  doc.setLineWidth(0.5);
  doc.roundedRect(margin + 82, 125, 55, 28, 4, 4, 'D');
  doc.setTextColor(255, 255, 255);
  doc.setFontSize(22);
  doc.setFont('helvetica', 'bold');
  doc.text(`${k.trs}%`, margin + 92, 142);
  doc.setFontSize(9);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(160, 190, 230);
  doc.text('TRS GLOBAL', margin + 92, 149);

  doc.setFillColor(25, 45, 85);
  doc.roundedRect(margin, 168, contentWidth, 60, 4, 4, 'F');

  doc.setTextColor(160, 190, 230);
  doc.setFontSize(8);
  doc.setFont('helvetica', 'bold');
  doc.text('INFORMATIONS DU RAPPORT', margin + 8, 178);

  doc.setDrawColor(0, 120, 212);
  doc.setLineWidth(0.3);
  doc.line(margin + 8, 181, margin + 85, 181);

  const videoName = this.currentVideoKpi.filename.substring(0, 45) +
    (this.currentVideoKpi.filename.length > 45 ? '...' : '');
  const analyseDate = new Date().toLocaleDateString('fr-FR', {
    weekday: 'long', day: 'numeric', month: 'long', year: 'numeric',
    hour: '2-digit', minute: '2-digit'
  });

  const infos: Array<[string, string]> = [
    ['Fichier analyse', videoName],
    ['Date du rapport', analyseDate],
    ['Periode couverte', this.getPeriodLabel()],
    ['Duree analysee', this.formatDuration(this.videoDuration)],
    ['Modele IA', 'YOLOv8 Custom — CAMIA Factory']
  ];

  let infoY = 188;
  infos.forEach(([label, value]) => {
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(160, 190, 230);
    doc.setFontSize(7.5);
    doc.text(label + ' :', margin + 8, infoY);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(255, 255, 255);
    const lines = doc.splitTextToSize(value, contentWidth - 65);
    doc.text(lines[0], margin + 55, infoY);
    infoY += 7;
  });

  // ✅ Zone synthèse avec grands nombres formatés
  const synthItems = [
    { label: 'Machines actives', value: `${r.machines}/${totalMachines}` },
    { label: 'Employes actifs', value: `${r.employesActifs}/${totalEmployees}` },
    { label: 'Produits detectes', value: formatNumber(r.products) },
    { label: 'Efficacite machines', value: `${k.machineEfficiency}%` },
  ];

  doc.setFillColor(15, 30, 60);
  doc.roundedRect(margin, 242, contentWidth, 32, 4, 4, 'F');

  const itemWidth = contentWidth / synthItems.length;
  synthItems.forEach((item, i) => {
    const x = margin + i * itemWidth + itemWidth / 2;
    doc.setTextColor(0, 120, 212);
    doc.setFontSize(13);
    doc.setFont('helvetica', 'bold');
    doc.text(item.value, x, 254, { align: 'center' });
    doc.setTextColor(160, 190, 230);
    doc.setFontSize(6.5);
    doc.setFont('helvetica', 'normal');
    doc.text(item.label, x, 261, { align: 'center' });
    if (i < synthItems.length - 1) {
      doc.setDrawColor(25, 55, 110);
      doc.setLineWidth(0.3);
      doc.line(margin + (i + 1) * itemWidth, 245, margin + (i + 1) * itemWidth, 271);
    }
  });

  doc.setFillColor(0, 0, 0, 0);
  doc.setTextColor(100, 130, 170);
  doc.setFontSize(7);
  doc.setFont('helvetica', 'normal');
  doc.text('Rapport genere automatiquement par CAMIA-Factory', pageWidth / 2, pageHeight - 12, { align: 'center' });
  doc.text(new Date().toLocaleDateString('fr-FR'), pageWidth / 2, pageHeight - 7, { align: 'center' });

  // ============================================================
  // HELPER FUNCTIONS LOCALES
  // ============================================================
  const addHeader = (title: string, subtitle?: string) => {
    doc.setFillColor(15, 30, 60);
    doc.rect(0, 0, pageWidth, 22, 'F');
    doc.setFillColor(0, 120, 212);
    doc.rect(0, 20, pageWidth, 2, 'F');
    doc.setTextColor(255, 255, 255);
    doc.setFontSize(13);
    doc.setFont('helvetica', 'bold');
    doc.text(title, margin, 13);
    if (subtitle) {
      doc.setFontSize(8);
      doc.setFont('helvetica', 'normal');
      doc.setTextColor(160, 190, 230);
      // ✅ Tronquer le subtitle pour éviter débordement
      const sub = subtitle.length > 50 ? subtitle.substring(0, 50) + '...' : subtitle;
      doc.text(sub, pageWidth - margin, 13, { align: 'right' });
    }
  };

  const addFooter = (pageNum: number, section: string) => {
    doc.setFillColor(15, 30, 60);
    doc.rect(0, pageHeight - 14, pageWidth, 14, 'F');
    doc.setFillColor(0, 120, 212);
    doc.rect(0, pageHeight - 14, pageWidth, 1, 'F');
    doc.setTextColor(160, 190, 230);
    doc.setFontSize(7);
    doc.setFont('helvetica', 'bold');
    doc.text('CAMIA-Factory', margin, pageHeight - 6);
    doc.setFont('helvetica', 'normal');
    doc.text(`Section : ${section}`, pageWidth / 2, pageHeight - 6, { align: 'center' });
    doc.setTextColor(0, 120, 212);
    doc.setFontSize(9);
    doc.setFont('helvetica', 'bold');
    doc.text(`${pageNum}`, pageWidth - margin, pageHeight - 6, { align: 'right' });
  };

  const addSectionTitle = (title: string, y: number) => {
    doc.setFillColor(0, 120, 212);
    doc.roundedRect(margin, y, 4, 10, 1, 1, 'F');
    doc.setTextColor(15, 30, 60);
    doc.setFontSize(12);
    doc.setFont('helvetica', 'bold');
    doc.text(title, margin + 8, y + 7.5);
    doc.setDrawColor(220, 230, 245);
    doc.setLineWidth(0.3);
    doc.line(margin + 8, y + 11, pageWidth - margin, y + 11);
  };

  const addParagraph = (text: string, y: number, maxWidth?: number): number => {
    doc.setFontSize(9);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(50, 70, 100);
    const lines = doc.splitTextToSize(text, maxWidth || contentWidth);
    lines.forEach((line: string, i: number) => {
      doc.text(line, margin, y + i * 5);
    });
    return y + lines.length * 5;
  };

  const addTable = (headers: string[], rows: string[][], y: number, colWidths?: number[]): number => {
    const colW = colWidths || headers.map(() => contentWidth / headers.length);
    const rh = 9;

    doc.setFillColor(15, 30, 60);
    doc.roundedRect(margin, y, contentWidth, rh, 2, 2, 'F');
    doc.setTextColor(255, 255, 255);
    doc.setFontSize(8.5);
    doc.setFont('helvetica', 'bold');
    let xPos = margin;
    headers.forEach((h, i) => {
      doc.text(h, xPos + 3, y + 6.2);
      xPos += colW[i];
    });
    y += rh;

    rows.forEach((row, ri) => {
      doc.setFillColor(ri % 2 === 0 ? 245 : 255, ri % 2 === 0 ? 248 : 255, ri % 2 === 0 ? 255 : 255);
      doc.rect(margin, y, contentWidth, rh, 'F');
      doc.setDrawColor(210, 220, 240);
      doc.setLineWidth(0.15);
      doc.line(margin, y + rh, margin + contentWidth, y + rh);
      doc.setTextColor(30, 50, 80);
      doc.setFontSize(8);
      xPos = margin;
      row.forEach((cell, ci) => {
        doc.setFont('helvetica', ci === 0 ? 'bold' : 'normal');
        if (ci === row.length - 1 && (cell === 'Excellent' || cell === 'Satisfaisant' || cell === 'A ameliorer' || cell === 'Critique')) {
          const c = cell === 'Excellent' ? [0, 150, 100] : cell === 'Satisfaisant' ? [200, 130, 0] : [200, 50, 50];
          doc.setTextColor(c[0], c[1], c[2]);
          doc.setFont('helvetica', 'bold');
        }
        // ✅ Tronquer le texte si trop long pour la colonne
        const maxCellWidth = colW[ci] - 6;
        const cellLines = doc.splitTextToSize(cell, maxCellWidth);
        doc.text(cellLines[0], xPos + 3, y + 6.2);
        doc.setTextColor(30, 50, 80);
        xPos += colW[ci];
      });
      y += rh;
    });
    return y;
  };

  const addKPICard = (label: string, value: string, evaluation: string, description: string, x: number, y: number, w: number) => {
  doc.setFillColor(245, 248, 255);
  doc.roundedRect(x, y, w, 30, 3, 3, 'F');
  doc.setDrawColor(210, 220, 240);
  doc.setLineWidth(0.3);
  doc.roundedRect(x, y, w, 30, 3, 3, 'D');
  doc.setFillColor(0, 120, 212);
  doc.roundedRect(x, y, 3, 30, 1, 1, 'F');

  const evalColor = evaluation === 'Excellent' ? [0, 150, 100] :
    evaluation === 'Satisfaisant' ? [200, 130, 0] : [200, 50, 50];

  // ✅ Label sur ligne 1
  doc.setTextColor(15, 30, 60);
  doc.setFontSize(8);
  doc.setFont('helvetica', 'bold');
  const labelLines = doc.splitTextToSize(label, w - 10);
  doc.text(labelLines[0], x + 6, y + 7);

  // ✅ Evaluation sur ligne 2 (séparée)
  doc.setTextColor(evalColor[0], evalColor[1], evalColor[2]);
  doc.setFontSize(6.5);
  doc.setFont('helvetica', 'bold');
  doc.text(evaluation.toUpperCase(), x + 6, y + 13);

  // ✅ Valeur sur ligne 3
  doc.setTextColor(0, 120, 212);
  const valFontSize = value.length > 8 ? 10 : 13;
  doc.setFontSize(valFontSize);
  doc.setFont('helvetica', 'bold');
  doc.text(value, x + 6, y + 22);

  // ✅ Description sur ligne 4
  doc.setTextColor(100, 120, 160);
  doc.setFontSize(6);
  doc.setFont('helvetica', 'normal');
  const descLines = doc.splitTextToSize(description, w - 10);
  doc.text(descLines[0], x + 6, y + 27);
};

  // ============================================================
  // PAGE 2 : DÉTECTIONS ET RESSOURCES
  // ============================================================
  doc.addPage();
  let yPos = 30;

  addHeader('DETECTIONS ET RESSOURCES', `Analyse : ${this.currentVideoKpi.filename.substring(0, 30)}`);
  addFooter(2, 'Détections');

  yPos = addParagraph(
    `Les donnees suivantes proviennent de la detection automatique par YOLOv8. Ce modele identifie les equipements, personnes et produits en temps reel et constitue la base de tous les indicateurs calcules.`,
    yPos + 5
  );
  yPos += 8;

  addSectionTitle('PARC MACHINES', yPos);
  yPos += 16;

  const machineParagraph = `Le parc comprend ${totalMachines} equipement(s). Le taux d'efficacite de ${k.machineEfficiency}% ${k.machineEfficiency >= 90 ? 'indique une utilisation optimale' : k.machineEfficiency >= 75 ? 'reflete un fonctionnement satisfaisant' : 'revele une sous-utilisation'}. ${r.machinesStopped > 0 ? `${r.machinesStopped} machine(s) sont a l'arret.` : 'Toutes les machines sont operationnelles.'}`;
  yPos = addParagraph(machineParagraph, yPos);
  yPos += 4;

  yPos = addTable(
    ['Indicateur', 'Valeur', 'Pourcentage', 'Statut'],
    [
      ['Machines actives', r.machines.toString(), `${this.calcPercent(r.machines, totalMachines)}%`, 'En production'],
      ['Machines a l arret', r.machinesStopped.toString(), `${this.calcPercent(r.machinesStopped, totalMachines)}%`, r.machinesStopped > 0 ? 'Impact negatif' : 'Normal'],
      ['Parc total', totalMachines.toString(), '100%', 'Capacite installee'],
      ['Taux d utilisation', `${k.machineEfficiency}%`, '', this.getStatusBadge(k.machineEfficiency, 90, 75)]
    ],
    yPos,
    [55, 35, 40, 44]
  );
  yPos += 12;

  addSectionTitle('RESSOURCES HUMAINES', yPos);
  yPos += 16;

  // ✅ Productivité formatée dans le paragraphe
  const rhParagraph = `L'effectif total detecte est de ${totalEmployees} personne(s). Le taux d'activite de ${k.employeeActivity}% ${k.employeeActivity >= 85 ? 'reflete un excellent engagement' : k.employeeActivity >= 70 ? 'indique un niveau acceptable' : 'signale une inactivite importante'}. La productivite moyenne est de ${formatNumber(k.productivity)} produit(s) par employe actif.`;
  yPos = addParagraph(rhParagraph, yPos);
  yPos += 4;

  // ✅ Productivité formatée dans le tableau
  yPos = addTable(
    ['Indicateur', 'Valeur', 'Pourcentage', 'Statut'],
    [
      ['Employes actifs', r.employesActifs.toString(), `${this.calcPercent(r.employesActifs, totalEmployees)}%`, 'Actifs'],
      ['Employes inactifs', r.employesInactifs.toString(), `${this.calcPercent(r.employesInactifs, totalEmployees)}%`, r.employesInactifs > 2 ? 'Taux eleve' : 'Normal'],
      ['Effectif total', totalEmployees.toString(), '100%', 'Presence totale'],
      ['Taux d activite', `${k.employeeActivity}%`, '', this.getStatusBadge(k.employeeActivity, 85, 70)],
      ['Productivite', `${formatNumber(k.productivity)} p/emp`, '', k.productivity >= 5 ? 'Excellent' : 'A ameliorer']
    ],
    yPos,
    [55, 35, 40, 44]
  );

  // ============================================================
  // PAGE 3 : PRODUCTION
  // ============================================================
  doc.addPage();
  yPos = 30;

  addHeader('PRODUCTION ET OCCUPATION', `Periode : ${this.getPeriodLabel()}`);
  addFooter(3, 'Production');

  addSectionTitle('ANALYSE DE LA PRODUCTION', yPos);
  yPos += 16;

  const hourlyRate = Math.round((r.products / this.videoDuration) * 3600);

  // ✅ Grands nombres formatés dans le paragraphe
  const prodParagraph = `Durant la periode analysee, ${formatNumber(r.products)} produit(s) ont ete detectes. La cadence estimee atteint ${formatNumber(hourlyRate)} produits par heure. Le taux de debit de ${k.throughput}% ${k.throughput >= 80 ? 'demontre une excellente performance' : k.throughput >= 65 ? 'indique un fonctionnement satisfaisant' : 'revele une sous-performance'} operationnelle.`;
  yPos = addParagraph(prodParagraph, yPos);
  yPos += 4;

  // ✅ Grands nombres formatés dans le tableau
  yPos = addTable(
    ['Metrique', 'Valeur', 'Interpretation'],
    [
      ['Volume produit', formatNumber(r.products), 'Unites detectees par YOLOv8'],
      ['Cadence horaire', `${formatNumber(hourlyRate)} p/h`, 'Projection sur 1 heure'],
      ['Taux de debit', `${k.throughput}%`, this.getStatusBadge(k.throughput, 80, 65)],
      ['Clients servis', r.clients.toString(), r.clients > 0 ? 'Activite commerciale' : 'Aucun client detecte']
    ],
    yPos,
    [70, 50, 54]
  );
  yPos += 14;

  if (r.tables > 0) {
    addSectionTitle('OCCUPATION DES ESPACES', yPos);
    yPos += 16;

    const tablesUtilisees = r.tables - r.tablesEmpty;
    const occupParagraph = `Sur ${r.tables} poste(s) disponibles, ${tablesUtilisees} sont actuellement occupes. Le taux d'occupation de ${k.tableOccupancy}% ${k.tableOccupancy >= 75 ? 'temoigne d\'une bonne optimisation' : k.tableOccupancy >= 50 ? 'indique une capacite disponible' : 'signale une sous-utilisation'} de l'espace.`;
    yPos = addParagraph(occupParagraph, yPos);
    yPos += 4;

    yPos = addTable(
      ['Indicateur', 'Valeur', 'Statut'],
      [
        ['Postes totaux', r.tables.toString(), 'Capacite installee'],
        ['Postes occupes', tablesUtilisees.toString(), 'En utilisation'],
        ['Postes libres', r.tablesEmpty.toString(), 'Disponibles'],
        ['Taux d occupation', `${k.tableOccupancy}%`, this.getStatusBadge(k.tableOccupancy, 75, 50)]
      ],
      yPos,
      [70, 50, 54]
    );
    yPos += 14;
  }

  doc.setFillColor(235, 242, 255);
  doc.roundedRect(margin, yPos, contentWidth, 22, 3, 3, 'F');
  doc.setFillColor(0, 120, 212);
  doc.roundedRect(margin, yPos, 3, 22, 1, 1, 'F');
  doc.setTextColor(0, 80, 160);
  doc.setFontSize(8);
  doc.setFont('helvetica', 'bold');
  doc.text('NOTE SUR LES PROJECTIONS', margin + 7, yPos + 8);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(50, 80, 130);
  const noteText = `Les cadences sont extrapolees de la periode d'analyse (${this.formatDuration(this.videoDuration)}). Ces estimations supposent une continuite des conditions observees.`;
  const noteLines = doc.splitTextToSize(noteText, contentWidth - 14);
  noteLines.forEach((l: string, i: number) => doc.text(l, margin + 7, yPos + 15 + i * 4.5));

  // ============================================================
  // PAGE 4 : KPIs
  // ============================================================
  doc.addPage();
  yPos = 30;

  addHeader('INDICATEURS DE PERFORMANCE', 'Calcules selon normes ISO et Six Sigma');
  addFooter(4, 'KPIs');

  yPos = addParagraph(
    `Les indicateurs cles evaluent l'efficacite operationnelle selon quatre dimensions : Production, Ressources Humaines, Qualite et Performance globale. Chaque indicateur est compare aux seuils industriels standards.`,
    yPos + 3
  );
  yPos += 10;

  addSectionTitle('PERFORMANCE PRODUCTION', yPos);
  yPos += 15;

  const cardW = (contentWidth - 8) / 3;
  addKPICard('TRS Global', `${k.trs}%`, this.getEvaluationLabel(k.trs, 85, 70), 'Taux de Rendement Synthetique', margin, yPos, cardW);
  addKPICard('OEE', `${k.oee}%`, this.getEvaluationLabel(k.oee, 85, 70), 'Overall Equipment Effectiveness', margin + cardW + 4, yPos, cardW);
  addKPICard('Efficacite Machines', `${k.machineEfficiency}%`, this.getEvaluationLabel(k.machineEfficiency, 90, 75), 'Machines actives sur parc total', margin + (cardW + 4) * 2, yPos, cardW);
  yPos += 34;

  addSectionTitle('PERFORMANCE RESSOURCES HUMAINES', yPos);
  yPos += 15;

  const cardW2 = (contentWidth - 8) / 3;
  addKPICard('Activite Employes', `${k.employeeActivity}%`, this.getEvaluationLabel(k.employeeActivity, 85, 70), 'Employes actifs sur effectif total', margin, yPos, cardW2);
  addKPICard('Engagement RH', `${k.employeeEngagement}%`, this.getEvaluationLabel(k.employeeEngagement, 85, 70), 'Presence active et impliquee', margin + cardW2 + 4, yPos, cardW2);
  // ✅ Productivité formatée dans la card
  addKPICard('Productivite', formatNumber(k.productivity), this.getEvaluationLabel(k.productivity * 20, 85, 70), 'Produits par employe actif', margin + (cardW2 + 4) * 2, yPos, cardW2);
  yPos += 34;

  addSectionTitle('QUALITE ET EXCELLENCE', yPos);
  yPos += 15;

  const cardW3 = (contentWidth - 12) / 4;
  addKPICard('Score Qualite', `${k.qualityScore}%`, this.getEvaluationLabel(k.qualityScore, 85, 70), 'Indice global qualite', margin, yPos, cardW3);
  addKPICard('Disponibilite', `${k.uptime}%`, this.getEvaluationLabel(k.uptime, 90, 75), 'Uptime equipements', margin + cardW3 + 4, yPos, cardW3);
  addKPICard('Debit Production', `${k.throughput}%`, this.getEvaluationLabel(k.throughput, 80, 65), 'Cadence / Capacite max', margin + (cardW3 + 4) * 2, yPos, cardW3);
  addKPICard('Indice Performance', `${k.performanceIndex}%`, this.getEvaluationLabel(k.performanceIndex, 85, 70), 'Synthese qualite + debit', margin + (cardW3 + 4) * 3, yPos, cardW3);
  yPos += 34;

  doc.setFillColor(248, 250, 255);
  doc.roundedRect(margin, yPos, contentWidth, 16, 3, 3, 'F');
  const legendItems = [
    { label: 'EXCELLENT', color: [0, 150, 100] as [number,number,number] },
    { label: 'SATISFAISANT', color: [200, 130, 0] as [number,number,number] },
    { label: 'A AMELIORER / CRITIQUE', color: [200, 50, 50] as [number,number,number] }
  ];
  const legendW = contentWidth / legendItems.length;
  legendItems.forEach((item, i) => {
    const lx = margin + i * legendW + 8;
    doc.setFillColor(item.color[0], item.color[1], item.color[2]);
    doc.circle(lx + 3, yPos + 8, 3, 'F');
    doc.setTextColor(50, 70, 100);
    doc.setFontSize(7.5);
    doc.setFont('helvetica', 'bold');
    doc.text(item.label, lx + 9, yPos + 9.5);
  });

  // ============================================================
  // PAGE 5 : GRAPHIQUES
  // ============================================================
  doc.addPage();
  yPos = 30;

  addHeader('VISUALISATIONS GRAPHIQUES', 'Analyse historique et comparaisons');
  addFooter(5, 'Graphiques');

  yPos = addParagraph(
    `Les graphiques suivants offrent une representation visuelle des KPIs. Le radar permet une vue d'ensemble immediate de la performance, tandis que les graphiques d'evolution montrent la progression historique sur les 7 dernieres analyses.`,
    yPos + 3
  );
  yPos += 10;

  try {
    // ✅ AVANT chaque addImage, vérifier qu'il reste de la place
const radarCanvas = document.getElementById('radarChart') as HTMLCanvasElement;
if (radarCanvas) {
  addSectionTitle('VUE D\'ENSEMBLE PERFORMANCE (RADAR)', yPos);
  yPos += 14;
  const radarImg = radarCanvas.toDataURL('image/png');
  doc.addImage(radarImg, 'PNG', margin, yPos, 88, 68);
  doc.setFillColor(248, 250, 255);
  doc.roundedRect(margin + 92, yPos, contentWidth - 92, 68, 3, 3, 'F');
  doc.setTextColor(15, 30, 60);
  doc.setFontSize(8.5);
  doc.setFont('helvetica', 'bold');
  doc.text('Interpretation', margin + 97, yPos + 10);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(50, 70, 100);
  doc.setFontSize(8);
  const radarText = `Ce radar represente 5 dimensions cles : Efficacite Machines, Activite RH, Occupation, Productivite et TRS. Plus la surface couverte est etendue, meilleure est la performance globale.`;
  const radarLines = doc.splitTextToSize(radarText, contentWidth - 100);
  radarLines.forEach((l: string, i: number) => doc.text(l, margin + 97, yPos + 18 + i * 5));
  yPos += 74;
}

const trendCanvas = document.getElementById('trendChart') as HTMLCanvasElement;
if (trendCanvas) {
  // ✅ Nouvelle page si pas assez de place
  if (yPos + 80 > pageHeight - 20) { doc.addPage(); addHeader('VISUALISATIONS GRAPHIQUES', ''); addFooter(5, 'Graphiques'); yPos = 30; }
  addSectionTitle('EVOLUTION HISTORIQUE TRS ET EFFICACITE', yPos);
  yPos += 14;
  const trendImg = trendCanvas.toDataURL('image/png');
  doc.addImage(trendImg, 'PNG', margin, yPos, 88, 62);
  doc.setFillColor(248, 250, 255);
  doc.roundedRect(margin + 92, yPos, contentWidth - 92, 62, 3, 3, 'F');
  doc.setTextColor(15, 30, 60);
  doc.setFontSize(8.5);
  doc.setFont('helvetica', 'bold');
  doc.text('Interpretation', margin + 97, yPos + 10);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(50, 70, 100);
  doc.setFontSize(8);
  const trendText = `La courbe bleue represente le TRS global, la courbe verte en pointilles l'efficacite des machines. Ces tendances permettent d'identifier les progressions ou degradations de performance dans le temps.`;
  const trendLines = doc.splitTextToSize(trendText, contentWidth - 100);
  trendLines.forEach((l: string, i: number) => doc.text(l, margin + 97, yPos + 18 + i * 5));
  yPos += 68;
}

const qualityCanvas = document.getElementById('qualityChart') as HTMLCanvasElement;
if (qualityCanvas) {
  // ✅ Nouvelle page si pas assez de place
  if (yPos + 72 > pageHeight - 20) { doc.addPage(); addHeader('VISUALISATIONS GRAPHIQUES', ''); addFooter(5, 'Graphiques'); yPos = 30; }
  addSectionTitle('INDICATEURS QUALITE DETAILLES', yPos);
  yPos += 14;
  const qualityImg = qualityCanvas.toDataURL('image/png');
  doc.addImage(qualityImg, 'PNG', margin, yPos, 88, 58);
  doc.setFillColor(248, 250, 255);
  doc.roundedRect(margin + 92, yPos, contentWidth - 92, 58, 3, 3, 'F');
  doc.setTextColor(15, 30, 60);
  doc.setFontSize(8.5);
  doc.setFont('helvetica', 'bold');
  doc.text('Interpretation', margin + 97, yPos + 10);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(50, 70, 100);
  doc.setFontSize(8);
  const qualText = `Comparaison des 4 KPIs qualite : Score global, Disponibilite, Debit de production et Indice de Performance. L'objectif industriel standard est 85% minimum sur chaque indicateur.`;
  const qualLines = doc.splitTextToSize(qualText, contentWidth - 100);
  qualLines.forEach((l: string, i: number) => doc.text(l, margin + 97, yPos + 18 + i * 5));
}
  } catch (error) {
    console.warn('Erreur capture graphiques:', error);
    doc.setFontSize(9);
    doc.setTextColor(200, 50, 50);
    doc.text('Les graphiques n\'ont pas pu etre captures.', margin, yPos + 10);
  }

  // ============================================================
  // PAGE 6 : CONCLUSION ET RECOMMANDATIONS
  // ============================================================
  doc.addPage();
  yPos = 30;

  addHeader('CONCLUSION ET RECOMMANDATIONS', `Score global : ${k.qualityScore}% — ${this.getScoreBadge(k.qualityScore).scoreText}`);
  addFooter(6, 'Conclusion');

  addSectionTitle('BILAN GLOBAL', yPos);
  yPos += 16;

  const conclusionText = `La performance globale est ${k.qualityScore >= 85 ? 'excellente' : k.qualityScore >= 70 ? 'satisfaisante' : 'a ameliorer'} avec un score de ${k.qualityScore}%. Le TRS de ${k.trs}% ${k.trs >= 85 ? 'depasse les standards industriels (objectif 85%)' : k.trs >= 70 ? 'est conforme aux objectifs' : 'necessite des actions correctives urgentes'}. Les machines fonctionnent a ${k.machineEfficiency}% d'efficacite ${k.machineEfficiency >= 90 ? ', ce qui est optimal' : ', avec une marge de progression identifiee'}. ${r.machinesStopped > 0 ? `${r.machinesStopped} machine(s) a l'arret impactent la production.` : 'Aucune machine n\'est a l\'arret, situation positive.'} ${k.employeeActivity < 70 ? `L'activite des employes a ${k.employeeActivity}% indique un potentiel d'optimisation important.` : `L'activite du personnel a ${k.employeeActivity}% est satisfaisante.`}`;
  yPos = addParagraph(conclusionText, yPos);
  yPos += 12;

  addSectionTitle('SYNTHESE DES INDICATEURS', yPos);
  yPos += 14;

  yPos = addTable(
    ['Indicateur', 'Valeur', 'Seuil', 'Evaluation'],
    [
      ['TRS Global', `${k.trs}%`, '85%', this.getEvaluationLabel(k.trs, 85, 70)],
      ['Efficacite Machines', `${k.machineEfficiency}%`, '90%', this.getEvaluationLabel(k.machineEfficiency, 90, 75)],
      ['Activite Employes', `${k.employeeActivity}%`, '85%', this.getEvaluationLabel(k.employeeActivity, 85, 70)],
      ['Score Qualite', `${k.qualityScore}%`, '85%', this.getEvaluationLabel(k.qualityScore, 85, 70)],
      ['Disponibilite', `${k.uptime}%`, '90%', this.getEvaluationLabel(k.uptime, 90, 75)],
      ['Debit Production', `${k.throughput}%`, '80%', this.getEvaluationLabel(k.throughput, 80, 65)],
      ['Indice Performance', `${k.performanceIndex}%`, '85%', this.getEvaluationLabel(k.performanceIndex, 85, 70)]
    ],
    yPos,
    [60, 35, 35, 44]
  );
  yPos += 12;

  addSectionTitle('RECOMMANDATIONS PRIORITAIRES', yPos);
  yPos += 14;

  const recommendations: Array<{ titre: string; detail: string; priority: string }> = [];

  if (k.trs < 85) recommendations.push({
    titre: 'Optimiser le TRS',
    detail: `TRS actuel : ${k.trs}% (objectif : 85%). Analyser les causes d'arret et optimiser les temps de changement.`,
    priority: k.trs < 70 ? 'URGENT' : 'IMPORTANT'
  });
  if (k.employeeActivity < 70) recommendations.push({
    titre: 'Ameliorer l\'activite employes',
    detail: `Taux actuel : ${k.employeeActivity}%. Reorganiser les flux de travail et reduire les temps d'attente.`,
    priority: 'IMPORTANT'
  });
  if (r.machinesStopped > 0) recommendations.push({
    titre: 'Maintenance preventive',
    detail: `${r.machinesStopped} machine(s) a l'arret. Planifier une intervention de maintenance corrective.`,
    priority: 'URGENT'
  });
  if (k.productivity < 5) recommendations.push({
    titre: 'Augmenter la productivite',
    detail: `Productivite actuelle : ${formatNumber(k.productivity)} prod/emp. Former le personnel et optimiser les processus.`,
    priority: 'MODERE'
  });

  if (recommendations.length === 0) {
    recommendations.push({
      titre: 'Maintenir les performances',
      detail: 'Tous les indicateurs sont dans les objectifs. Poursuivre la surveillance reguliere.',
      priority: 'INFO'
    });
    recommendations.push({
      titre: 'Amelioration continue',
      detail: 'Viser l\'excellence operationnelle par des cycles d\'optimisation reguliers.',
      priority: 'INFO'
    });
  }

  recommendations.forEach((rec, idx) => {
    const priorityColor: [number, number, number] =
      rec.priority === 'URGENT' ? [200, 50, 50] :
      rec.priority === 'IMPORTANT' ? [200, 130, 0] :
      rec.priority === 'MODERE' ? [0, 120, 212] :
      [0, 150, 100];

    doc.setFillColor(248, 250, 255);
    doc.roundedRect(margin, yPos, contentWidth, 20, 3, 3, 'F');
    doc.setFillColor(priorityColor[0], priorityColor[1], priorityColor[2]);
    doc.roundedRect(margin, yPos, 3, 20, 1, 1, 'F');

    doc.setFillColor(priorityColor[0], priorityColor[1], priorityColor[2]);
    doc.roundedRect(pageWidth - margin - 28, yPos + 4, 28, 8, 2, 2, 'F');
    doc.setTextColor(255, 255, 255);
    doc.setFontSize(6.5);
    doc.setFont('helvetica', 'bold');
    doc.text(rec.priority, pageWidth - margin - 14, yPos + 9.5, { align: 'center' });

    doc.setTextColor(15, 30, 60);
    doc.setFontSize(9);
    doc.setFont('helvetica', 'bold');
    doc.text(`${idx + 1}. ${rec.titre}`, margin + 7, yPos + 8);
    doc.setTextColor(60, 80, 110);
    doc.setFontSize(7.5);
    doc.setFont('helvetica', 'normal');
    const recLines = doc.splitTextToSize(rec.detail, contentWidth - 45);
    doc.text(recLines[0], margin + 7, yPos + 15);

    yPos += 24;
  });

  yPos = Math.max(yPos + 8, pageHeight - 50);
  doc.setFillColor(15, 30, 60);
  doc.roundedRect(margin, yPos, contentWidth, 18, 3, 3, 'F');
  doc.setTextColor(160, 190, 230);
  doc.setFontSize(7.5);
  doc.setFont('helvetica', 'italic');
  doc.text(
    `Rapport genere automatiquement par CAMIA-Factory le ${new Date().toLocaleDateString('fr-FR')} a ${new Date().toLocaleTimeString('fr-FR')}. Pour une analyse approfondie, consultez le tableau de bord en temps reel.`,
    pageWidth / 2,
    yPos + 10,
    { align: 'center', maxWidth: contentWidth - 10 }
  );

  // ============================================================
  // SAUVEGARDE
  // ============================================================
  const pdfTimestamp = new Date().toISOString().split('T')[0];
  const pdfTimeStr = new Date().toTimeString().split(' ')[0].replace(/:/g, '-');
  const pdfFilename = `CAMIA_Rapport_${pdfTimestamp}_${pdfTimeStr}.pdf`;
  doc.save(pdfFilename);
  console.log('✅ Rapport PDF genere:', pdfFilename);

  const pdfBlob = doc.output('blob') as Blob;
  const pdfBase64 = await new Promise<string>((resolve) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      const result = reader.result as string;
      resolve(result.split(',')[1]);
    };
    reader.readAsDataURL(pdfBlob);
  });

  try {
    const response = await this.http.post<any>(
      `${this.apiUrl}/reports/rapports/save`,
      {
        video_id: this.currentVideoKpi?.videoId,
        periode: this.selectedPeriod,
        pdf_base64: pdfBase64,
        kpi_snapshot: this.currentVideoKpi?.kpis
      }
    ).toPromise();
    console.log('✅ Rapport sauvegardé dans MongoDB:', response);
    alert('✅ Rapport généré et sauvegardé !');
  } catch (error) {
    console.error('⚠️ Rapport généré mais pas sauvegardé:', error);
    alert('✅ Rapport généré (sauvegarde échouée)');
  }
}


  public getRiskLabel(level: string): string { 
    return level === 'low' ? 'faible' : level === 'medium' ? 'modere' : 'eleve'; 
  }
  public getPerformanceAssessment(value: number, excellent: number, good: number): string { 
    if (value >= excellent) return 'excellente, depassant les standards'; 
    if (value >= good) return 'satisfaisante, conforme aux objectifs'; 
    return 'en-dessous des seuils'; 
  }
  public getMachineAssessment(value: number): string { 
    if (value >= 90) return 'excellente'; 
    if (value >= 75) return 'satisfaisante'; 
    return 'sous-utilisation'; 
  }
  public getRHAssessment(value: number): string { 
    if (value >= 85) return 'excellent engagement'; 
    if (value >= 70) return 'acceptable'; 
    return 'problematique d\'inactivite'; 
  }
  public getProductionAssessment(value: number, excellent: number, good: number): string { 
    if (value >= excellent) return 'excellente performance'; 
    if (value >= good) return 'fonctionnement satisfaisant'; 
    return 'sous-performance'; 
  }
  public getOccupancyAssessment(value: number, excellent: number, good: number): string { 
    if (value >= excellent) return 'bonne optimisation'; 
    if (value >= good) return 'capacite disponible'; 
    return 'sous-utilisation'; 
  }
  public getScoreBadge(score: number): { scoreColor: number[]; scoreText: string } { 
    if (score >= 85) return { scoreColor: [16, 185, 129], scoreText: 'EXCELLENT' }; 
    if (score >= 70) return { scoreColor: [245, 158, 11], scoreText: 'SATISFAISANT' }; 
    return { scoreColor: [239, 68, 68], scoreText: 'CRITIQUE' }; 
  }
  public getStatusBadge(value: number, excellent: number, good: number): string { 
    if (value >= excellent) return 'Excellent'; 
    if (value >= good) return 'Satisfaisant'; 
    return 'A ameliorer'; 
  }
  public getEvaluationLabel(value: number, excellent: number, good: number): string { 
    if (value >= excellent) return 'Excellent'; 
    if (value >= good) return 'Satisfaisant'; 
    return 'Critique'; 
  }
  public calcPercent(part: number, total: number): number { 
    return total > 0 ? Math.round((part / total) * 100) : 0; 
  }
  public formatDuration(seconds: number): string { 
    const mins = Math.floor(seconds / 60); 
    const secs = Math.round(seconds % 60); 
    return mins > 0 ? `${mins}min ${secs}s` : `${secs}s`; 
  }

  private addPageHeader(doc: jsPDF, title: string, yPos: number): void {
    const pageWidth = doc.internal.pageSize.getWidth();
    doc.setFillColor(99, 102, 241); doc.rect(0, 0, pageWidth, 12, 'F');
    doc.setTextColor(255, 255, 255); doc.setFontSize(14); doc.setFont('helvetica', 'bold');
    doc.text(title, pageWidth / 2, 8, { align: 'center' });
  }
  private addSubsectionTitle(doc: jsPDF, title: string, yPos: number): void {
    doc.setFillColor(99, 102, 241); doc.roundedRect(20, yPos, 100, 8, 2, 2, 'F');
    doc.setTextColor(255, 255, 255); doc.setFontSize(10); doc.setFont('helvetica', 'bold');
    doc.text(title, 23, yPos + 5.5);
  }
  private addCleanTable(doc: jsPDF, data: string[][], yPos: number, headers: string[]): number {
    const pageWidth = doc.internal.pageSize.getWidth(); const m = 20;
    const cw = pageWidth - (2 * m);
    const colW = headers.map(() => cw / headers.length); const rh = 8;
    doc.setFillColor(99, 102, 241); doc.rect(m, yPos, cw, rh, 'F');
    doc.setTextColor(255, 255, 255); doc.setFontSize(9); doc.setFont('helvetica', 'bold');
    headers.forEach((h, i) => { const x = m + colW.slice(0, i).reduce((a, b) => a + b, 0); doc.text(h, x + 2, yPos + 5.5); });
    yPos += rh;
    data.forEach((row, ri) => {
      if (ri % 2 === 0) { doc.setFillColor(248, 250, 252); doc.rect(m, yPos, cw, rh, 'F'); }
      doc.setDrawColor(226, 232, 240); doc.setLineWidth(0.1); doc.rect(m, yPos, cw, rh);
      doc.setTextColor(51, 65, 85); doc.setFontSize(8.5);
      row.forEach((cell, ci) => { const x = m + colW.slice(0, ci).reduce((a, b) => a + b, 0); doc.setFont('helvetica', ci === 0 ? 'bold' : 'normal'); const lines = doc.splitTextToSize(cell, colW[ci] - 4); doc.text(lines[0], x + 2, yPos + 5.5); });
      yPos += rh;
    }); return yPos;
  }
  private addKPISubsection(doc: jsPDF, title: string, kpiData: Array<[string, string, string, string]>, yPos: number): void {
    const pageWidth = doc.internal.pageSize.getWidth(); const m = 20; const cw = pageWidth - (2 * m);
    doc.setFontSize(12); doc.setFont('helvetica', 'bold'); doc.setTextColor(15, 23, 42); doc.text(title, m, yPos); yPos += 8;
    kpiData.forEach((row, i) => {
      if (i % 2 === 0) { doc.setFillColor(248, 250, 252); doc.rect(m, yPos, cw, 16, 'F'); }
      doc.setDrawColor(226, 232, 240); doc.setLineWidth(0.2); doc.rect(m, yPos, cw, 16);
      doc.setTextColor(15, 23, 42); doc.setFontSize(10); doc.setFont('helvetica', 'bold'); doc.text(row[0], m + 3, yPos + 6);
      doc.setFont('helvetica', 'bold'); doc.setTextColor(99, 102, 241); doc.text(row[1], m + 70, yPos + 6);
      const ec = row[2] === 'Excellent' ? [16, 185, 129] : row[2] === 'Satisfaisant' ? [245, 158, 11] : [239, 68, 68];
      doc.setTextColor(ec[0], ec[1], ec[2]); doc.setFont('helvetica', 'bold'); doc.setFontSize(9); doc.text(row[2], m + 105, yPos + 6);
      doc.setFont('helvetica', 'italic'); doc.setFontSize(8); doc.setTextColor(71, 85, 105);
      const dl = doc.splitTextToSize(row[3], cw - 10);
      dl.forEach((l: string, idx: number) => { doc.text(l, m + 3, yPos + 11 + (idx * 3.5)); });
      yPos += 16;
    });
  }
  private addChartSection(doc: jsPDF, title: string, desc: string, canvas: HTMLCanvasElement, x: number, y: number, w: number, h: number, cw: number): void {
    doc.setFontSize(12); doc.setFont('helvetica', 'bold'); doc.setTextColor(15, 23, 42); doc.text(title, x, y); y += 8;
    const img = canvas.toDataURL('image/png'); doc.addImage(img, 'PNG', x, y, w, h);
    doc.setFontSize(9); doc.setFont('helvetica', 'normal'); doc.setTextColor(71, 85, 105);
    const el = doc.splitTextToSize(desc, cw - w - 10);
    el.forEach((l: string, i: number) => { doc.text(l, x + w + 5, y + 5 + (i * 4)); });
  }
  private addInfoBox(doc: jsPDF, x: number, y: number, w: number, title: string, content: string): void {
    doc.setFillColor(241, 245, 249); doc.roundedRect(x, y, w, 35, 3, 3, 'F');
    doc.setFontSize(10); doc.setFont('helvetica', 'bold'); doc.setTextColor(15, 23, 42); doc.text(title, x + 5, y + 8);
    doc.setFontSize(9); doc.setFont('helvetica', 'normal'); doc.setTextColor(51, 65, 85);
    const lines = doc.splitTextToSize(content, w - 10);
    lines.forEach((l: string, i: number) => { doc.text(l, x + 5, y + 16 + (i * 4)); });
  }
  private addEnhancedFooter(doc: jsPDF, pn: number, section: string): void {
    const ph = doc.internal.pageSize.getHeight(); const pw = doc.internal.pageSize.getWidth();
    doc.setDrawColor(226, 232, 240); doc.setLineWidth(0.3); doc.line(20, ph - 20, pw - 20, ph - 20);
    doc.setFillColor(248, 250, 252); doc.rect(0, ph - 19, pw, 19, 'F');
    doc.setFontSize(8); doc.setTextColor(100, 116, 139); doc.setFont('helvetica', 'bold'); doc.text('CAMIA-Factory', 20, ph - 12);
    doc.setFont('helvetica', 'normal'); doc.setFontSize(7); doc.text('Systeme Intelligent de Surveillance Industrielle', 20, ph - 8);
    doc.setFontSize(7); doc.text(`Section : ${section}`, pw / 2, ph - 10, { align: 'center' });
    doc.setFontSize(9); doc.setFont('helvetica', 'bold'); doc.setTextColor(99, 102, 241); doc.text(`Page ${pn}`, pw - 20, ph - 10, { align: 'right' });
  }

  public exportToExcel(): void {
    if (!this.currentVideoKpi) { alert('Aucune donnee a exporter'); return; }
    const wb = XLSX.utils.book_new();
    const r = this.currentVideoKpi.raw;
    const k = this.currentVideoKpi.kpis;
    
    const resumeData = [
      ['RAPPORT D\'ANALYSE CAMIA-FACTORY'], ['Systeme de Surveillance et d\'Analyse Industrielle'], [''],
      ['INFORMATIONS GENERALES'], ['Fichier analyse', this.currentVideoKpi.filename],
      ['Date d\'analyse', this.currentVideoKpi.timestamp], ['Date de generation', new Date().toLocaleString('fr-FR')],
      ['Periode', this.getPeriodLabel()], ['Duree video (secondes)', this.videoDuration.toString()],
      ['Duree video (minutes)', (this.videoDuration / 60).toFixed(2)], [''],
      ['SYNTHESE GLOBALE'], ['Score Global de Performance', `${k?.qualityScore || 0}%`, this.getEvaluationLabel(k?.qualityScore || 0, 85, 70)],
      ['Niveau de risque', this.getRiskLabel(k?.riskLevel || 'low'), `Score: ${k?.riskScore || 0}/100`],
      ['TRS Global', `${k?.trs || 0}%`, this.getEvaluationLabel(k?.trs || 0, 85, 70)], [''],
      ['RESUME RESSOURCES'], ['Machines actives', r.machines.toString()],
      ['Machines totales', (r.machines + r.machinesStopped).toString()],
      ['Employes actifs', r.employesActifs.toString()],
      ['Employes totaux', (r.employees + r.employesActifs + r.employesInactifs).toString()],
      ['Produits detectes', r.products.toString()], [''],
      ['EVALUATION RAPIDE'], ['Efficacite Machines', `${k?.machineEfficiency || 0}%`, this.getEvaluationLabel(k?.machineEfficiency || 0, 90, 75)],
      ['Activite Employes', `${k?.employeeActivity || 0}%`, this.getEvaluationLabel(k?.employeeActivity || 0, 85, 70)],
      ['Productivite', `${k?.productivity || 0} prod/emp`, this.getEvaluationLabel((k?.productivity || 0) * 20, 85, 70)]
    ];
    const wsResume = XLSX.utils.aoa_to_sheet(resumeData);
    wsResume['!cols'] = [{ wch: 30 }, { wch: 35 }, { wch: 20 }];
    XLSX.utils.book_append_sheet(wb, wsResume, 'Resume');

    const excelTimestamp = new Date().toISOString().split('T')[0];
    const excelTimeStr = new Date().toTimeString().split(' ')[0].replace(/:/g, '-');
    const excelFilename = `CAMIA_Data_Complete_${excelTimestamp}_${excelTimeStr}.xlsx`;
    XLSX.writeFile(wb, excelFilename);
    console.log('✅ Excel genere:', excelFilename);
  }

  private getRiskLabelText(level: string): string {
    switch (level) { case 'low': return 'FAIBLE'; case 'medium': return 'MODERE'; case 'high': return 'ELEVE'; default: return 'INCONNU'; }
  }

  private addPageFooter(doc: jsPDF, pageNumber: number): void {
    const pageWidth = doc.internal.pageSize.getWidth();
    const pageHeight = doc.internal.pageSize.getHeight();
    doc.setFillColor(248, 250, 252);
    doc.rect(0, pageHeight - 15, pageWidth, 15, 'F');
    doc.setFontSize(8); doc.setTextColor(100, 116, 139); doc.setFont('helvetica', 'normal');
    doc.text('CAMIA-Factory - Systeme de Surveillance Intelligente', pageWidth / 2, pageHeight - 8, { align: 'center' });
    doc.setFont('helvetica', 'italic'); doc.setFontSize(7);
    doc.text(`Page ${pageNumber}`, pageWidth / 2, pageHeight - 4, { align: 'center' });
  }

  public getRiskColor(level: string): string {
    switch (level) { case 'high': return '#ef4444'; case 'medium': return '#f59e0b'; default: return '#10b981'; }
  }
  public getTrendIcon(trend?: string): string {
    switch (trend) { case 'up': return 'fas fa-arrow-up'; case 'down': return 'fas fa-arrow-down'; default: return 'fas fa-minus'; }
  }
  public getPeriodLabel(): string {
    const labels: any = { 'video': 'Duree video', 'hour': 'Derniere heure', 'day': "Aujourd'hui", 'week': '7 derniers jours', 'month': '30 derniers jours' };
    return labels[this.selectedPeriod] || '';
  }
  public getDurationForPeriod(): number {
  switch (this.selectedPeriod) {
    case 'hour': return 3600; 
    case 'day': return 86400;
    case 'week': return 604800; 
    case 'month': return 2592000;
    default: return this.videoDuration || 60;
  }
} 
  public refresh(): void { this.loadKpiData(); }
  public navigateToVideo(videoId: string): void { this.router.navigate(['/admin/videos', videoId]); }
public async onPeriodChange(): Promise<void> {
  console.log(`🔄 Changement de periode: ${this.selectedPeriod}`);
  
  if (this.selectedPeriod === 'video') {
    await this.loadVideoBasedKPIs();
    return;
  }
  
  this.loading = true;
  this.showContent = false;
  this.cdr.detectChanges();
  
  const noCache = { headers: { 'Cache-Control': 'no-cache', 'Pragma': 'no-cache' } };
  
  try {
    const videos = await this.http.get<any[]>(`${this.apiUrl}/videos/`, noCache).toPromise() || [];
    const completed = videos.filter(v => v.status === 'completed') || [];
    
    if (completed.length === 0) {
      await this.loadVideoBasedKPIs();
      return;
    }
    
    const latestVideo = completed.sort((a: any, b: any) => 
      new Date(b.created_at || b.uploaded_at).getTime() - new Date(a.created_at || a.uploaded_at).getTime()
    )[0];

    this.videoDuration = Number(latestVideo?.duration) || 60;

    try {
      const detectionData = await this.http.get<any>(
        `http://localhost:8000/api/v1/detections/video/${latestVideo._id}`, noCache
      ).toPromise();
      latestVideo.classes_detectees = detectionData?.classes_detectees || {};
    } catch (err) {
      latestVideo.classes_detectees = {};
    }

    const historicalVideos = completed.slice(0, 7);
    for (const v of historicalVideos) {
      try {
        const det = await this.http.get<any>(
          `http://localhost:8000/api/v1/detections/video/${v._id}`, noCache
        ).toPromise();
        v.classes_detectees = det?.classes_detectees || {};
      } catch {
        v.classes_detectees = {};
      }
    }
    
    const baseKPIs = this.calculateKPIsSync(latestVideo);
    const projectedKPIs = this.projectPerformanceKPIs(baseKPIs, latestVideo);
    
    this.currentVideoKpi = { ...projectedKPIs };
    this.updateProjectionSummary(baseKPIs.raw, latestVideo);
    this.historicalKpis = [...historicalVideos.map((v: any) => this.calculateKPIsSync(v))];
    this.kpiCards = [];
    this.generateKpiCards();
    this.activeAlerts = [];
    this.generateAlerts();

    // ✅ loading=false ET showContent=true EN MÊME TEMPS
    this.loading = false;
    this.showContent = true;
    this.cdr.detectChanges();

    setTimeout(() => {
      this.createCharts();
      this.cdr.detectChanges();
    }, 200);

    await this.saveKPIsToDB(projectedKPIs, latestVideo, this.selectedPeriod);
    
  } catch (error) {
    console.error('❌ Erreur:', error);
    this.loading = false;
    this.showContent = true;
    this.cdr.detectChanges();
    await this.loadVideoBasedKPIs();
  }
}
  
  get productionKPIs(): KPICard[] { return this.kpiCards.filter(k => k.category === 'production'); }
  get rhKPIs(): KPICard[] { return this.kpiCards.filter(k => k.category === 'rh'); }
  get logistiqueKPIs(): KPICard[] { return this.kpiCards.filter(k => k.category === 'logistique'); }
  get qualiteKPIs(): KPICard[] { return this.kpiCards.filter(k => k.category === 'qualite'); }
}
