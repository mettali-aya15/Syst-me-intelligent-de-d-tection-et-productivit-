// src/app/features/production/services/production.service.ts

import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject, combineLatest } from 'rxjs';
import { tap, map } from 'rxjs/operators';
export interface Production {
  id: string;
  date: string;                // Format: "YYYY-MM-DD"
  shift: 'Matin' | 'Soir' | 'Nuit';
  machineId: string;
  product: string;
  targetQuantity: number;      // Objectif
  actualQuantity: number;      // Réalisé
  efficiency: number;          // %
  defects: number;             // Nombre de défauts
  downtime: number;            // Temps d'arrêt (minutes)
  operatorId: string;
}

export interface ProductionStats {
  totalProduction: number;
  avgEfficiency: number;
  totalDefects: number;
  totalDowntime: number;
}

@Injectable({
  providedIn: 'root'
})
export class ProductionService {
  private readonly API_URL = 'http://localhost:3000/api';
  private http = inject(HttpClient);

  private productionsSubject = new BehaviorSubject<Production[]>([]);
  public productions$ = this.productionsSubject.asObservable();

  /**
   * Récupérer toutes les productions
   */
  getProductions(): Observable<Production[]> {
    return this.http.get<Production[]>(`${this.API_URL}/production`)
      .pipe(
        tap(productions => this.productionsSubject.next(productions))
      );
  }

  /**
   * Récupérer une production par ID
   */
  getProduction(id: string): Observable<Production> {
    return this.http.get<Production>(`${this.API_URL}/production/${id}`);
  }

  /**
   * Créer une nouvelle production
   */
  createProduction(production: Omit<Production, 'id'>): Observable<Production> {
    return this.http.post<Production>(`${this.API_URL}/production`, {
      ...production,
      id: 'prod_' + Date.now()
    }).pipe(
      tap(() => this.getProductions().subscribe())
    );
  }

  /**
   * Mettre à jour une production
   */
  updateProduction(id: string, updates: Partial<Production>): Observable<Production> {
    return this.http.patch<Production>(`${this.API_URL}/production/${id}`, updates)
      .pipe(
        tap(() => this.getProductions().subscribe())
      );
  }

  /**
   * Supprimer une production
   */
  deleteProduction(id: string): Observable<void> {
    return this.http.delete<void>(`${this.API_URL}/production/${id}`)
      .pipe(
        tap(() => this.getProductions().subscribe())
      );
  }

  /**
   * Filtrer par date
   */
  getProductionsByDate(date: string): Observable<Production[]> {
    return this.productions$.pipe(
      map(productions => productions.filter(p => p.date === date))
    );
  }

  /**
   * Filtrer par machine
   */
  getProductionsByMachine(machineId: string): Observable<Production[]> {
    return this.productions$.pipe(
      map(productions => productions.filter(p => p.machineId === machineId))
    );
  }

  /**
   * Calculer les statistiques
   */
  getStats(): Observable<ProductionStats> {
    return this.productions$.pipe(
      map(productions => {
        const total = productions.reduce((sum, p) => sum + p.actualQuantity, 0);
        const avgEff = productions.length > 0
          ? productions.reduce((sum, p) => sum + p.efficiency, 0) / productions.length
          : 0;
        const defects = productions.reduce((sum, p) => sum + p.defects, 0);
        const downtime = productions.reduce((sum, p) => sum + p.downtime, 0);

        return {
          totalProduction: total,
          avgEfficiency: Math.round(avgEff * 10) / 10,
          totalDefects: defects,
          totalDowntime: downtime
        };
      })
    );
  }
}