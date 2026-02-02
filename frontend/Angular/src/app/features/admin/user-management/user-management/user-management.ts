import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, FormsModule, ReactiveFormsModule, Validators } from '@angular/forms';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';


import { Auth } from '../../../../core/auth/auth';
import { User, UserManagementService, UserUpdateDto } from '../user-mangmnt';
import { RouterLink } from '@angular/router';


@Component({
  selector: 'app-user-management',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule,FormsModule, RouterLink],
  templateUrl: './user-management.html',
  styleUrls: ['./user-management.css']
})
export class UserManagementComponent implements OnInit, OnDestroy {
  users: User[] = [];
  filteredUsers: User[] = [];
  
  // Stats

  managerCount = 0;
  operatorCount = 0;

  // Modals
  showEditModal = false;
  showDeleteModal = false;

  // Forms
  editForm!: FormGroup;
  searchQuery = '';
  roleFilter = 'all';

  // Current actions
  currentEditUser: User | null = null;
  currentDeleteUser: User | null = null;

  // Loading states
  isLoading = false;
  isSubmitting = false;

  private destroy$ = new Subject<void>();

  constructor(
    private userManagementService: UserManagementService,
    private authService: Auth,
    private formBuilder: FormBuilder
  ) {}

  ngOnInit(): void {
    this.initEditForm();
    this.loadUsers();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  // =============================
  // INITIALIZATION
  // =============================
  private initEditForm(): void {
    this.editForm = this.formBuilder.group({
      firstName: ['', [Validators.required, Validators.minLength(2)]],
      lastName: ['', [Validators.required, Validators.minLength(2)]],
      email: ['', [Validators.required, Validators.email]],
      phone: [''],
      role: ['operator', [Validators.required]],
      department: ['']
    });
  }

  // =============================
  // DATA LOADING
  // =============================
  loadUsers(): void {
    this.isLoading = true;

    this.userManagementService.getAllUsers()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (users) => {
          // Exclure l'utilisateur connecté (admin actuel)
          const currentUser = this.authService.currentUserValue;
          this.users = users.filter(u => u.id !== currentUser?.id);
          this.filteredUsers = [...this.users];
          this.updateStats();
          this.isLoading = false;
        },
        error: (error) => {
          console.error('❌ Erreur chargement utilisateurs:', error);
          this.isLoading = false;
        }
      });
  }

  private updateStats(): void {
   
    this.managerCount = this.users.filter(u => u.role === 'manager').length;
    this.operatorCount = this.users.filter(u => u.role === 'operator').length;
  }

  // =============================
  // FILTERING & SEARCH
  // =============================
  onSearch(query: string): void {
    this.searchQuery = query.toLowerCase();
    this.applyFilters();
  }

  onRoleFilterChange(role: string): void {
    this.roleFilter = role;
    this.applyFilters();
  }

  private applyFilters(): void {
    let filtered = [...this.users];

    // Filtre par rôle
    if (this.roleFilter !== 'all') {
      filtered = filtered.filter(u => u.role === this.roleFilter);
    }

    // Filtre par recherche
    if (this.searchQuery) {
      filtered = filtered.filter(u =>
        u.firstName?.toLowerCase().includes(this.searchQuery) ||
        u.lastName?.toLowerCase().includes(this.searchQuery) ||
        u.email?.toLowerCase().includes(this.searchQuery) ||
        u.company?.toLowerCase().includes(this.searchQuery)
      );
    }

    this.filteredUsers = filtered;
  }

  // =============================
  // EDIT USER
  // =============================
  openEditModal(user: User): void {
    this.currentEditUser = user;
    this.editForm.patchValue({
      firstName: user.firstName,
      lastName: user.lastName,
      email: user.email,
      phone: user.phone || '',
      role: user.role,
      department: user.department || ''
    });
    this.showEditModal = true;
  }

  closeEditModal(): void {
    this.showEditModal = false;
    this.currentEditUser = null;
    this.editForm.reset();
  }

  onSubmitEdit(): void {
    if (this.editForm.invalid || !this.currentEditUser) {
      return;
    }

    this.isSubmitting = true;
    const updateData: UserUpdateDto = this.editForm.value;

    this.userManagementService.updateUser(this.currentEditUser.id, updateData)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (updatedUser) => {
          console.log('✅ Utilisateur modifié:', updatedUser);
          
          // Mettre à jour la liste locale
          const index = this.users.findIndex(u => u.id === updatedUser.id);
          if (index !== -1) {
            this.users[index] = updatedUser;
            this.applyFilters();
          }

          this.isSubmitting = false;
          this.closeEditModal();
          this.showSuccessMessage('Utilisateur modifié avec succès !');
        },
        error: (error) => {
          console.error('❌ Erreur modification:', error);
          this.isSubmitting = false;
          this.showErrorMessage('Erreur lors de la modification');
        }
      });
  }

  // =============================
  // DELETE USER
  // =============================
  openDeleteModal(user: User): void {
    this.currentDeleteUser = user;
    this.showDeleteModal = true;
  }

  closeDeleteModal(): void {
    this.showDeleteModal = false;
    this.currentDeleteUser = null;
  }

  confirmDelete(): void {
    if (!this.currentDeleteUser) {
      return;
    }

    this.isSubmitting = true;
    const userId = this.currentDeleteUser.id;
    const userEmail = this.currentDeleteUser.email;

    this.userManagementService.deleteUser(userId, userEmail)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          console.log('✅ Utilisateur supprimé:', userId);
          
          // Retirer de la liste locale
          this.users = this.users.filter(u => u.id !== userId);
          this.applyFilters();
          this.updateStats();

          this.isSubmitting = false;
          this.closeDeleteModal();
          this.showSuccessMessage('Utilisateur supprimé avec succès !');
        },
        error: (error) => {
          console.error('❌ Erreur suppression:', error);
          this.isSubmitting = false;
          this.showErrorMessage('Erreur lors de la suppression');
        }
      });
  }

  // =============================
  // UI HELPERS
  // =============================
  getRoleLabel(role: string): string {
    const labels: { [key: string]: string } = {
      'admin': 'Administrateur',
      'manager': 'Manager',
      'operator': 'Opérateur'
    };
    return labels[role] || role;
  }

  getRoleBadgeClass(role: string): string {
    return `badge badge-${role}`;
  }

  isFieldInvalid(fieldName: string): boolean {
    const field = this.editForm.get(fieldName);
    return !!(field && field.invalid && (field.dirty || field.touched));
  }

  private showSuccessMessage(message: string): void {
    // Implémenter avec un service de notification (Toastr, etc.)
    alert(message);
  }

  private showErrorMessage(message: string): void {
    // Implémenter avec un service de notification
    alert(message);
  }

  // =============================
  // GETTERS FOR TEMPLATE
  // =============================
  get hasUsers(): boolean {
    return this.filteredUsers.length > 0;
  }

  get currentUser() {
    return this.authService.currentUserValue;
  }
}