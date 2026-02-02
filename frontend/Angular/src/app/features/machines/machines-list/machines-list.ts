import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { ProductionService } from '../../production/production';

import { Machine, MachineService } from '../machine';
import { Auth } from '../../../core/auth/auth';
import { Employee, EmployeeService } from '../../employees/employee';


@Component({
  selector: 'app-machines-list',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule,RouterLink],
  templateUrl: './machines-list.html',
  styleUrl: './machines-list.css',
})
export class MachineList implements OnInit {
  private machineService = inject(MachineService);
   private employeeService = inject(EmployeeService);
  private authService = inject(Auth);
  private router = inject(Router);
  private route = inject(ActivatedRoute);
  private fb = inject(FormBuilder);
private productionService = inject(ProductionService);

  machineForm!: FormGroup;
  loading = false;
  machineId: string | null = null;
  machines$ = this.machineService.machines$;
  operators: Employee[] = [];
  stats = {
    total: 0,
    running: 0,
    stopped: 0,
    avgEfficiency: 0
  };
  get isAdmin(): boolean {
    return this.authService.hasRole('admin');
  }

  get isManager(): boolean {
    return this.authService.hasAnyRole(['admin', 'manager']);
  }
  /**  Droits */
  get canManage(): boolean {
    return this.authService.hasAnyRole(['admin','manager']);
  }

  /** Mode édition (id présent et différent de 'new') */
  get isEditMode(): boolean {
    return !!this.machineId && this.machineId !== 'new';
  }

  /**  Mode création (id est explicitement 'new') */
  get isCreateMode(): boolean {
    return this.machineId === 'new';
  }

  ngOnInit(): void {
    this.initForm();
this.loadOperators();
    // Chargement initial des données
    this.machineService.getMachines().subscribe(machines => {
      this.calculateStats(machines);
    });

    // Surveillance des paramètres d'URL pour basculer entre liste/ajout/édition
    this.route.paramMap.subscribe(params => {
      this.machineId = params.get('id');

      if (this.isEditMode && this.machineId) {
        this.loadMachine(this.machineId);
      } else if (this.isCreateMode) {
        this.resetFormForNew();
      } else {
        // Mode liste : on peut éventuellement rafraîchir les données
        this.machineId = null;
      }
    });
  }

  private initForm(): void {
    this.machineForm = this.fb.group({
      name: ['', Validators.required],
      type: ['', Validators.required],
      manufacturer: ['', Validators.required],
      model: ['', Validators.required],
      serialNumber: ['', Validators.required],
      location: ['', Validators.required],
      status: ['running', Validators.required],
      efficiency: [0, [Validators.required, Validators.min(0), Validators.max(100)]],
      productionRate: [0, [Validators.required, Validators.min(0)]],
      lastMaintenance: ['', Validators.required],
      nextMaintenance: ['', Validators.required],
      operatorId: [null]
    });
  }

  private resetFormForNew(): void {
    this.machineForm.reset({
      status: 'running',
      efficiency: 0,
      productionRate: 0,
      lastMaintenance: new Date().toISOString().split('T')[0], // Optionnel: date du jour par défaut
      nextMaintenance: ''
    });
  }

  private loadMachine(id: string): void {
    this.loading = true;
    this.machineService.getMachine(id).subscribe({
      next: (machine) => {
        this.machineForm.patchValue(machine);
        this.loading = false;
      },
      error: () => {
        alert(' Machine introuvable');
        this.loading = false;
        this.goBack();
      }
    });
  }
  private loadOperators(): void {
    this.employeeService.getEmployees().subscribe({
      next: (employees) => {
        // Optionnel : Filtrer pour n'avoir que les opérateurs si votre modèle a un champ 'role'
        // this.operators = employees.filter(e => e.role === 'operator');
        
        // Sinon, on prend tout le monde
        this.operators = employees;
      },
      error: (err) => console.error('Erreur chargement opérateurs', err)
    });
  }
private createInitialProduction(machineId: string, operatorId :string): void {
  const today = new Date().toISOString().split('T')[0];

  this.productionService.createProduction({
    date: today,
    shift: 'Matin',
    machineId: machineId,
    product: 'Produit par défaut',
    targetQuantity: 0,
    actualQuantity: 0,
    efficiency: 0,
    defects: 0,
    downtime: 0,
   operatorId: operatorId || 'unassigned'
 // opérateur transmis
  }).subscribe({
    next: () => console.log('✅ Production initiale créée'),
    error: err => console.error('❌ Erreur création production', err)
  });
}

  onSubmit(): void {
    if (this.machineForm.invalid) {
      this.machineForm.markAllAsTouched(); // Force l'affichage des erreurs
      alert('⚠️ Formulaire invalide');
      return;
    }

    this.loading = true;
    const data = this.machineForm.value;

    const request = this.isEditMode && this.machineId
      ? this.machineService.updateMachine(this.machineId, data)
      : this.machineService.createMachine(data);
if (this.isEditMode && this.machineId) {
  this.machineService.updateMachine(this.machineId, data).subscribe({
    next: () => {
      alert(' Machine modifiée');
      this.loading = false;
      this.goBack();
    },
    error: () => {
      alert('Erreur modification machine');
      this.loading = false;
    }
  });
} else {
  this.machineService.createMachine(data).subscribe({
    next: (machine) => {
      //  AJOUT AUTOMATIQUE DE LA PRODUCTION
      this.createInitialProduction(
  machine.id,
  this.machineForm.value.operatorId
);


      alert(' Machine et production créées');
      this.loading = false;
      this.goBack();
    },
    error: () => {
      alert(' Erreur création machine');
      this.loading = false;
    }
  });
}

  }

  addMachine(): void {
    // Navigue vers /machines/new. Le paramMap.subscribe fera le reste.
    this.router.navigate(['/machines', 'new']);
  }

  editMachine(id: string): void {
    this.router.navigate(['/machines', id]);
  }

  deleteMachine(machine: Machine): void {
    if (!confirm(`Supprimer ${machine.name} ?`)) return;

    this.machineService.deleteMachine(machine.id).subscribe(() => {
      alert('✅ Machine supprimée');
      // Optionnel: rafraîchir la liste si le service ne le fait pas automatiquement via un BehaviorSubject
    });
  }

  goBack(): void {
    this.machineId = null; // Réinitialise l'état local
    this.router.navigate(['/machines']);
  }

  private calculateStats(machines: Machine[]): void {
    if (!machines) return;
    this.stats.total = machines.length;
    this.stats.running = machines.filter(m => m.status === 'running').length;
    this.stats.stopped = machines.filter(m => m.status === 'stopped').length;
    this.stats.avgEfficiency = machines.length
      ? Math.round(machines.reduce((s, m) => s + (m.efficiency || 0), 0) / machines.length)
      : 0;
  }

  getEfficiencyClass(efficiency: number): string {
    if (efficiency >= 85) return 'high';
    if (efficiency >= 70) return 'medium';
    return 'low';
  }

  getStatusLabel(status: Machine['status']): string {
    const labels: Record<string, string> = {
      running: 'EN MARCHE',
      stopped: 'ARRÊTÉE',
      maintenance: 'MAINTENANCE'
    };
    return labels[status] || status;
  }
}