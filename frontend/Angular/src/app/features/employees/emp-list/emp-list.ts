import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { EmployeeService, Employee } from '../services/employee.service';

@Component({
  selector: 'app-emp-list',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './emp-list.html',
  styleUrls: ['./emp-list.css']
})
export class EmpListComponent implements OnInit {
  employees: Employee[] = [];
  filteredEmployees: Employee[] = [];
  loading = true;
  error = '';

  searchTerm = '';
  filterActive: 'all' | 'active' | 'inactive' = 'active';

  // ✅ GETTERS POUR LE COMPTAGE
  get activeCount(): number {
    return this.employees.filter(e => e.active).length;
  }

  get inactiveCount(): number {
    return this.employees.filter(e => !e.active).length;
  }

  showModal = false;
  modalMode: 'create' | 'edit' = 'create';
  currentEmployee: Partial<Employee> = {};

  constructor(private employeeService: EmployeeService) {}

  ngOnInit(): void {
    this.loadEmployees();
  }

  loadEmployees(): void {
    this.loading = true;
    this.employeeService.getEmployees(false).subscribe({
      next: (data: Employee[]) => {
        this.employees = data;
        this.applyFilters();
        this.loading = false;
      },
      error: (err: any) => {
        this.error = 'Erreur lors du chargement des employés';
        this.loading = false;
        console.error(err);
      }
    });
  }

  applyFilters(): void {
    let result = [...this.employees];

    if (this.filterActive === 'active') {
      result = result.filter(e => e.active);
    } else if (this.filterActive === 'inactive') {
      result = result.filter(e => !e.active);
    }

    if (this.searchTerm) {
      const term = this.searchTerm.toLowerCase();
      result = result.filter(e =>
        e.full_name.toLowerCase().includes(term) ||
        e.name.toLowerCase().includes(term) ||
        e.email?.toLowerCase().includes(term) ||
        e.department?.toLowerCase().includes(term)
      );
    }

    this.filteredEmployees = result;
  }

  onSearchChange(): void {
    this.applyFilters();
  }

  onFilterChange(): void {
    this.applyFilters();
  }

  openCreateModal(): void {
    this.modalMode = 'create';
    this.currentEmployee = {
      name: '',
      full_name: '',
      email: '',
      department: 'Production',
      active: true
    };
    this.showModal = true;
  }

  openEditModal(employee: Employee): void {
    this.modalMode = 'edit';
    this.currentEmployee = { ...employee };
    this.showModal = true;
  }

  closeModal(): void {
    this.showModal = false;
    this.currentEmployee = {};
  }

  saveEmployee(): void {
    if (!this.currentEmployee.name || !this.currentEmployee.full_name) {
      alert('Veuillez remplir les champs obligatoires');
      return;
    }

    this.currentEmployee.name = this.currentEmployee.name!.toLowerCase();

    if (this.modalMode === 'create') {
      this.employeeService.createEmployee(this.currentEmployee).subscribe({
        next: () => {
          this.loadEmployees();
          this.closeModal();
        },
        error: (err: any) => {
          alert('Erreur lors de la création');
          console.error(err);
        }
      });
    } else {
      const id = this.currentEmployee._id || this.currentEmployee.id;
      if (id) {
        this.employeeService.updateEmployee(id, this.currentEmployee).subscribe({
          next: () => {
            this.loadEmployees();
            this.closeModal();
          },
          error: (err: any) => {
            alert('Erreur lors de la mise à jour');
            console.error(err);
          }
        });
      }
    }
  }

  toggleStatus(employee: Employee): void {
    const id = employee._id || employee.id;
    if (id) {
      this.employeeService.updateEmployee(id, { active: !employee.active }).subscribe({
        next: () => {
          this.loadEmployees();
        },
        error: (err: any) => {
          alert('Erreur lors de la modification du statut');
          console.error(err);
        }
      });
    }
  }

  deleteEmployee(employee: Employee): void {
    if (confirm(`Êtes-vous sûr de vouloir désactiver ${employee.full_name} ?`)) {
      this.toggleStatus(employee);
    }
  }
}