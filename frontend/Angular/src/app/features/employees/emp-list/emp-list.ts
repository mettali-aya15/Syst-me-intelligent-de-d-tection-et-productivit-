import { Component, inject, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterLink } from '@angular/router';
import { FormBuilder, FormGroup, ReactiveFormsModule, FormsModule, Validators } from '@angular/forms'; // Ajout de FormsModule
import { Subject, takeUntil } from 'rxjs'; // Pour la gestion propre des abonnements

import { Auth } from '../../../core/auth/auth';
import { Employee, EmployeeService } from '../employee';

@Component({
  selector: 'app-emp-list',
  standalone: true,
  imports: [CommonModule, RouterLink, ReactiveFormsModule, FormsModule], // Ajout de FormsModule
  templateUrl: './emp-list.html',
  styleUrls: ['./emp-list.css']
})
export class EmpList implements OnInit, OnDestroy {
  private employeeService = inject(EmployeeService);
  private authService = inject(Auth);
  private fb = inject(FormBuilder);
  private destroy$ = new Subject<void>();

  // Données
  allEmployees: Employee[] = [];
  filteredEmployees: Employee[] = [];
  
  // Filtres
  searchQuery: string = '';
  statusFilter: string = 'all';

  // État
  isLoading = true;
  editingEmployee: Employee | null = null;
  editForm!: FormGroup;

  ngOnInit(): void {
    this.initForm();
    this.loadEmployees();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private initForm() {
    this.editForm = this.fb.group({
      firstName: ['', Validators.required],
      lastName: ['', Validators.required],
      email: ['', [Validators.required, Validators.email]],
      position: ['', Validators.required],
      department: ['', Validators.required],
      phone: ['']
    });
  }

  loadEmployees() {
    this.isLoading = true;
    this.employeeService.getEmployees()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (emps) => {
          this.allEmployees = emps;
          this.applyFilters();
          this.isLoading = false;
        },
        error: () => this.isLoading = false
      });
  }

  // LOGIQUE DE FILTRAGE
  onSearch(query: string) {
    this.searchQuery = query.toLowerCase();
    this.applyFilters();
  }

  onStatusChange(status: string) {
    this.statusFilter = status;
    this.applyFilters();
  }

  applyFilters() {
    let filtered = [...this.allEmployees];

    // Recherche textuelle
    if (this.searchQuery) {
      filtered = filtered.filter(e => 
        e.firstName.toLowerCase().includes(this.searchQuery) ||
        e.lastName.toLowerCase().includes(this.searchQuery) ||
        e.email.toLowerCase().includes(this.searchQuery) ||
        e.department.toLowerCase().includes(this.searchQuery) ||
        e.position.toLowerCase().includes(this.searchQuery)
      );
    }

    // Filtre par statut
    if (this.statusFilter !== 'all') {
      filtered = filtered.filter(e => e.status === this.statusFilter);
    }

    this.filteredEmployees = filtered;
  }

  // ... (Garder vos méthodes existantes editEmployee, saveEdit, deleteEmployee, etc.)
  
  get canManage(): boolean { return this.authService.hasAnyRole(['admin', 'manager']); }
  get isAdmin(): boolean { return this.authService.hasRole('admin'); }

  editEmployee(emp: Employee): void {
    if (!this.canManage) return;
    this.editingEmployee = emp;
    this.editForm.patchValue({...emp});
  }

  cancelEdit(): void {
    this.editingEmployee = null;
    this.editForm.reset();
  }

  saveEdit(): void {
    if (this.editForm.valid && this.editingEmployee) {
      this.employeeService.updateEmployee(this.editingEmployee.id, this.editForm.value).subscribe({
        next: () => {
          this.editingEmployee = null;
          // Le service rappellera getEmployees, loadEmployees s'occupera du reste
        }
      });
    }
  }

  deleteEmployee(emp: Employee): void {
    if (!this.isAdmin) return;
    if (confirm(`⚠️ Supprimer définitivement ${emp.firstName} ${emp.lastName} ?`)) {
      this.employeeService.deleteEmployee(emp.id).subscribe();
    }
  }
}