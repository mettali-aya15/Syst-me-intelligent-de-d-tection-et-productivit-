import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { forkJoin } from 'rxjs';
export interface RapportData {
  employees: any[];
  machines: any[];
  production: any[];
  kpis: any[];
}

@Injectable({ providedIn: 'root' })
export class RapportsService {
  private API = 'http://localhost:3000';

  constructor(private http: HttpClient) {}

  getAllRapportData() {
    return forkJoin({
      employees: this.http.get<any[]>(`${this.API}/api/employees`),
      machines: this.http.get<any[]>(`${this.API}/api/machines`),
      production: this.http.get<any[]>(`${this.API}/api/production`),
      kpis: this.http.get<any[]>(`${this.API}/api/kpis`)
    });
  }
}
