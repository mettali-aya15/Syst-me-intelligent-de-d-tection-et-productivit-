import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, firstValueFrom } from 'rxjs';
import { environment } from '../../../environments/environment';

// ==========================================
// 📋 INTERFACES KPI
// ==========================================
export interface KPIProductionData {
  taux_productivite: number;
  objectif_production: number;
  taux_conformite: number;
  cadence_production: number;
  unites_produites: number;
  objectif_unites: number;
  produits_conformes: number;
  total_produits: number;
}

export interface KPIMachinesData {
  trs: number;
  disponibilite: number;
  performance: number;
  qualite: number;
  taux_panne: number;
  mtbf: number;
  mttr: number;
  total_machines: number;
  machines_actives: number;
  machines_arretees: number;
  temps_productif: number;
  temps_total: number;
}

export interface KPIEmployesData {
  taux_presence: number;
  taux_activite: number;
  productivite_par_employe: number;
  taux_inactivite: number;
  total_employes: number;
  employes_presents: number;
  employes_actifs: number;
  employes_inactifs: number;
}

export interface KPITablesData {
  total_tables: number;
  tables_occupees: number;
  tables_vides: number;
  taux_occupation: number;
}

export interface KPIClientsData {
  total_clients: number;
  clients_en_attente: number;
  clients_servis: number;
  taux_service: number;
}

export interface KPISnapshotData {
  video_analysis_id?: string;
  periode: string;
  date_debut: string;
  date_fin: string;
  production?: KPIProductionData;
  machines?: KPIMachinesData;
  employes?: KPIEmployesData;
  tables?: KPITablesData;
  clients?: KPIClientsData;
}

@Injectable({
  providedIn: 'root'
})
export class KpiService {
  private apiUrl = `${environment.apiUrl}/api/v1/kpis`;

  constructor(private http: HttpClient) {}

  // ==========================================
  // 🆕 NOUVELLE MÉTHODE : SAUVEGARDE AUTO
  // ==========================================
  
  /**
   * 💾 Sauvegarder automatiquement les KPIs calculés en TypeScript
   * Appelée automatiquement après chaque calcul
   */
  async saveKPIs(kpis: KPISnapshotData): Promise<any> {
    try {
      const response = await firstValueFrom(
        this.http.post(`${this.apiUrl}/save`, kpis)
      );
      console.log('✅ KPIs sauvegardés automatiquement dans MongoDB:', response);
      return response;
    } catch (error) {
      console.error('❌ Erreur sauvegarde automatique KPIs:', error);
      // Ne pas bloquer l'affichage si la sauvegarde échoue
      return null;
    }
  }

  /**
   * 📊 Récupérer l'historique des KPIs pour une vidéo
   */
  async getKPIHistory(videoAnalysisId: string): Promise<any> {
    try {
      const response: any = await firstValueFrom(
        this.http.get(`${this.apiUrl}/history/${videoAnalysisId}`)
      );
      return response.data || [];
    } catch (error) {
      console.error('❌ Erreur récupération historique KPIs:', error);
      return [];
    }
  }

  /**
   * 🔍 Récupérer le KPI le plus récent
   */
  async getLatestKPI(periode: string = 'video'): Promise<any> {
    try {
      const params = new HttpParams().set('periode', periode);
      const response: any = await firstValueFrom(
        this.http.get(`${this.apiUrl}/latest`, { params })
      );
      return response.data || null;
    } catch (error) {
      console.error('❌ Erreur récupération dernier KPI:', error);
      return null;
    }
  }

  // ==========================================
  // ⚠️ ANCIENNES MÉTHODES - À SUPPRIMER PLUS TARD
  // (On les garde temporairement pour compatibilité)
  // ==========================================

  /**
   * @deprecated Utiliser saveKPIs() à la place
   */
  getKpiToday(periode: 'heure' | 'jour' | 'semaine' | 'mois' = 'jour'): Observable<any> {
    const params = new HttpParams().set('periode', periode);
    return this.http.get(`${this.apiUrl}/global/today`, { params });
  }

  /**
   * @deprecated Utiliser saveKPIs() à la place
   */
  getKpiWeek(): Observable<any> {
    return this.http.get(`${this.apiUrl}/global/week`);
  }

  /**
   * @deprecated Utiliser saveKPIs() à la place
   */
  getKpiMonth(): Observable<any> {
    return this.http.get(`${this.apiUrl}/global/month`);
  }

  /**
   * @deprecated Utiliser getKPIHistory() à la place
   */
  getKpiHistory(days: number = 30): Observable<any> {
    return this.http.get(`${this.apiUrl}/history?days=${days}`);
  }

  /**
   * @deprecated Utiliser saveKPIs() à la place
   */
  getProductionTrend(days: number = 7): Observable<any> {
    return this.http.get(`${this.apiUrl}/production/trend?days=${days}`);
  }

  /**
   * @deprecated Utiliser saveKPIs() à la place
   */
  getTrsTrend(days: number = 7): Observable<any> {
    return this.http.get(`${this.apiUrl}/machines/trs-trend?days=${days}`);
  }

  /**
   * @deprecated Utiliser saveKPIs() à la place
   */
  calculateKpiForVideo(videoId: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/videos/${videoId}/calculate`, {});
  }
}