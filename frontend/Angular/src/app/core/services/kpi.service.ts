import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class KpiService {
  private apiUrl = `${environment.apiUrl}/api/v1/kpis`;

  constructor(private http: HttpClient) {}

  /**
   * ✅ CORRIGÉ : Ajout du paramètre periode
   */
  getKpiToday(periode: 'heure' | 'jour' | 'semaine' | 'mois' = 'jour'): Observable<any> {
  const params = new HttpParams().set('periode', periode);
  return this.http.get(`${this.apiUrl}/global/today`, { params });
}

  getKpiWeek(): Observable<any> {
    return this.http.get(`${this.apiUrl}/global/week`);
  }

  getKpiMonth(): Observable<any> {
    return this.http.get(`${this.apiUrl}/global/month`);
  }

  getKpiHistory(days: number = 30): Observable<any> {
    return this.http.get(`${this.apiUrl}/history?days=${days}`);
  }

  getProductionTrend(days: number = 7): Observable<any> {
    return this.http.get(`${this.apiUrl}/production/trend?days=${days}`);
  }

  getTrsTrend(days: number = 7): Observable<any> {
    return this.http.get(`${this.apiUrl}/machines/trs-trend?days=${days}`);
  }

  calculateKpiForVideo(videoId: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/videos/${videoId}/calculate`, {});
  }
}