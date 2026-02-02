import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { BehaviorSubject, Observable, tap } from 'rxjs';
// src/app/features/kpis/models/kpi.model.ts

export interface KPI {
  id: string;
  name: string;
  value: number;
  unit: string;
  target: number;
  trend: 'up' | 'down' | 'stable';
  changePercent: number;
  period: string;
}
@Injectable({
  providedIn: 'root',
})
export class KpiService {
  
  private readonly API_URL = 'http://localhost:3000/api';
  private http = inject(HttpClient);

  private kpisSubject = new BehaviorSubject<KPI[]>([]);
  public kpis$ = this.kpisSubject.asObservable();

  getKpis(): Observable<KPI[]> {
    return this.http.get<KPI[]>(`${this.API_URL}/kpis`)
      .pipe(
        tap(kpis => {
          this.kpisSubject.next(kpis);
          console.log('✅ KPIs chargés:', kpis);
        })
      );
  }

  updateKpi(id: string, data: Partial<KPI>): Observable<KPI> {
    return this.http.patch<KPI>(`${this.API_URL}/kpis/${id}`, data)
      .pipe(
        tap(() => this.getKpis().subscribe())
      );
  }
  
}
