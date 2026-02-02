// src/app/features/production/production-list/production-list.component.ts

import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { forkJoin, map } from 'rxjs';

import { Auth } from '../../../core/auth/auth';
import { Production, ProductionService } from '../production';
import { Machine, MachineService } from '../../machines/machine';
import { Employee, EmployeeService } from '../../employees/employee';

import { Router, RouterLink } from '@angular/router';

interface ProductionStats {
  totalProduction: number;
  averageEfficiency: number;
  totalDefects: number;
  totalDowntime: number;
  productionByShift: { shift: string; quantity: number }[];
  productionByMachine: { machine: string; quantity: number }[];
  efficiencyTrend: { date: string; efficiency: number }[];
}

@Component({
  selector: 'app-production-list',
  standalone: true,
  imports: [CommonModule, FormsModule,RouterLink],
  templateUrl: "./production-list.html",
  styleUrl: "./production-list.css"
})
export class ProductionList implements OnInit {
  private productionService = inject(ProductionService);
  private machineService = inject(MachineService);
  private employeeService = inject(EmployeeService);
  private authService = inject(Auth);

  productions$ = this.productionService.productions$;
  filteredProductions$ = this.productions$;
  
  machines: Machine[] = [];
  employees: Employee[] = [];

  // Filtres
  filterDate = '';
  filterMachine = '';
  filterShift = '';

  // Statistiques calculées
  stats: ProductionStats = {
    totalProduction: 0,
    averageEfficiency: 0,
    totalDefects: 0,
    totalDowntime: 0,
    productionByShift: [],
    productionByMachine: [],
    efficiencyTrend: []
  };

  loading = true;

  get canManage(): boolean {
    return this.authService.hasAnyRole(['admin', 'manager']);
  }

  ngOnInit(): void {
    this.loadData();
  }

  private loadData(): void {
  this.loading = true;

  // forkJoin permet d'attendre que TOUTES les requêtes soient finies
  forkJoin({
    employees: this.employeeService.getEmployees(),
    machines: this.machineService.getMachines(),
    productions: this.productionService.getProductions()
  }).subscribe({
    next: (data) => {
      // 1. On stocke les données de référence
      this.employees = data.employees;
      this.machines = data.machines;
      
      console.log(`✅ ${this.employees.length} employés chargés`);
      console.log(`✅ ${this.machines.length} machines chargées`);

      // 2. Maintenant que les machines sont chargées, on peut calculer les stats
      // Les noms de machines seront corrects car this.machines est rempli
      this.calculateStats(data.productions);
      
      this.loading = false;
    },
    error: (err) => {
      console.error('❌ Erreur lors du chargement des données:', err);
      this.loading = false;
    }
  });
}

  //  Calculer les statistiques
  private calculateStats(productions: Production[]): void {
    if (productions.length === 0) {
      this.loading = false;
      return;
    }

    // Total production
    this.stats.totalProduction = productions.reduce((sum, p) => sum + p.actualQuantity, 0);

    // Efficacité moyenne
    const totalEfficiency = productions.reduce((sum, p) => sum + p.efficiency, 0);
    this.stats.averageEfficiency = totalEfficiency / productions.length;

    // Total défauts
    this.stats.totalDefects = productions.reduce((sum, p) => sum + p.defects, 0);

    // Total temps d'arrêt
    this.stats.totalDowntime = productions.reduce((sum, p) => sum + p.downtime, 0);

    // Production par shift
    const shiftMap = new Map<string, number>();
    productions.forEach(p => {
      const current = shiftMap.get(p.shift) || 0;
      shiftMap.set(p.shift, current + p.actualQuantity);
    });
    this.stats.productionByShift = Array.from(shiftMap.entries()).map(([shift, quantity]) => ({
      shift,
      quantity
    }));

   // Production par machine (Version corrigée pour tout afficher)
this.stats.productionByMachine = this.machines.map(machine => {
  // 1. On cherche toutes les productions pour cette machine spécifique
  const machineProds = productions.filter(p => p.machineId === machine.id);
  
  // 2. On additionne les quantités
  const quantity = machineProds.reduce((sum, p) => sum + p.actualQuantity, 0);

  return {
    machine: machine.name, // Le nom est sûr d'être bon car on vient de la liste des machines
    quantity: quantity
  };
});

// Optionnel : Trier pour mettre les plus grosses productions en haut
this.stats.productionByMachine.sort((a, b) => b.quantity - a.quantity);

    // Tendance d'efficacité par date
    const dateMap = new Map<string, { total: number; count: number }>();
    productions.forEach(p => {
      const current = dateMap.get(p.date) || { total: 0, count: 0 };
      dateMap.set(p.date, {
        total: current.total + p.efficiency,
        count: current.count + 1
      });
    });
    this.stats.efficiencyTrend = Array.from(dateMap.entries())
      .map(([date, data]) => ({
        date,
        efficiency: data.total / data.count
      }))
      .sort((a, b) => a.date.localeCompare(b.date));
  }

  //  Filtres
  applyFilters(): void {
    this.filteredProductions$ = this.productions$.pipe(
      map(productions => {
        let filtered = productions;

        if (this.filterDate) {
          filtered = filtered.filter(p => p.date === this.filterDate);
        }

        if (this.filterMachine) {
          filtered = filtered.filter(p => p.machineId === this.filterMachine);
        }

        if (this.filterShift) {
          filtered = filtered.filter(p => p.shift === this.filterShift);
        }

        // Recalculer les stats avec les données filtrées
        this.calculateStats(filtered);

        return filtered;
      })
    );
  }

  resetFilters(): void {
    this.filterDate = '';
    this.filterMachine = '';
    this.filterShift = '';
    this.filteredProductions$ = this.productions$;
    
    // Recharger les données complètes
    this.loadData();
  }

  // Helpers
  getMachineName(machineId: string): string {
    const machine = this.machines.find(m => m.id === machineId);
    return machine ? machine.name : 'Machine inconnue';
  }

  getOperatorName(operatorId: string): string {
    const operator = this.employees.find(e => e.id === operatorId);
    return operator ? `${operator.firstName} ${operator.lastName}` : 'Non assigné';
  }

  getEfficiencyClass(efficiency: number): string {
    if (efficiency >= 95) return 'excellent';
    if (efficiency >= 85) return 'good';
    if (efficiency >= 70) return 'average';
    return 'poor';
  }

  getEfficiencyColor(efficiency: number): string {
    if (efficiency >= 95) return '#10b981';
    if (efficiency >= 85) return '#3b82f6';
    if (efficiency >= 70) return '#f59e0b';
    return '#ef4444';
  }

  //  Calculs pour les graphiques
  getShiftPercentage(quantity: number): number {
    return this.stats.totalProduction > 0 
      ? (quantity / this.stats.totalProduction) * 100 
      : 0;
  }

  getMachinePercentage(quantity: number): number {
    return this.stats.totalProduction > 0 
      ? (quantity / this.stats.totalProduction) * 100 
      : 0;
  }

  getMaxEfficiency(): number {
    return Math.max(...this.stats.efficiencyTrend.map(t => t.efficiency), 100);
  }

  getEfficiencyHeight(efficiency: number): number {
    const max = this.getMaxEfficiency();
    return max > 0 ? (efficiency / max) * 100 : 0;
  }
}