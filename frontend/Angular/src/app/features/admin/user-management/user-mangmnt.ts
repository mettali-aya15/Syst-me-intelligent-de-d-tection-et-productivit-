import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';

export interface User {
  id: string;
  email: string;
  password: string;
  firstName: string;
  lastName: string;
  role: 'admin' | 'manager' | 'operator';
  company?: string;
  companyId?: string;
  phone?: string;
  department?: string;
  avatar?: string;
  createdAt?: string;
  loginDate?: string;
}

export interface UserUpdateDto {
  firstName?: string;
  lastName?: string;
  email?: string;
  phone?: string;
  role?: string;
  department?: string;
  company?: string;
}

@Injectable({
  providedIn: 'root'
})
export class UserManagementService {
  private readonly API_URL = 'http://localhost:3000/api';

  constructor(private http: HttpClient) {}

  /**
   * Récupérer tous les utilisateurs
   */
  getAllUsers(): Observable<User[]> {
    return this.http.get<User[]>(`${this.API_URL}/users`);
  }

  /**
   * Récupérer un utilisateur par ID
   */
  getUserById(id: string): Observable<User> {
    return this.http.get<User>(`${this.API_URL}/users/${id}`);
  }

  /**
   * Récupérer les utilisateurs par rôle
   */
  getUsersByRole(role: string): Observable<User[]> {
    return this.getAllUsers().pipe(
      map(users => users.filter(u => u.role === role))
    );
  }

  /**
   * Mettre à jour un utilisateur
   */
  updateUser(id: string, userData: UserUpdateDto): Observable<User> {
    return this.http.patch<User>(`${this.API_URL}/users/${id}`, userData);
  }

  /**
   * Supprimer un utilisateur
   * Supprime aussi l'employé correspondant dans /employees
   */
  deleteUser(id: string, email: string): Observable<any> {
    // D'abord supprimer l'utilisateur
    return this.http.delete(`${this.API_URL}/users/${id}`).pipe(
      map(() => {
        // Puis supprimer l'employé correspondant (si existe)
        this.deleteEmployeeByEmail(email).subscribe({
          next: () => console.log('✅ Employé supprimé'),
          error: (err) => console.log('⚠️ Pas d\'employé à supprimer ou erreur:', err)
        });
        return { success: true, message: 'Utilisateur supprimé' };
      })
    );
  }

  /**
   * Supprimer un employé par email
   */
  private deleteEmployeeByEmail(email: string): Observable<any> {
    // D'abord trouver l'employé
    return this.http.get<any[]>(`${this.API_URL}/employees?email=${email}`).pipe(
      map(employees => {
        if (employees && employees.length > 0) {
          const employeeId = employees[0].id;
          // Supprimer l'employé
          return this.http.delete(`${this.API_URL}/employees/${employeeId}`).subscribe();
        }
        return null;
      })
    );
  }

  /**
   * Mettre à jour le rôle d'un utilisateur
   */
  updateUserRole(id: string, newRole: 'admin' | 'manager' | 'operator'): Observable<User> {
    return this.http.patch<User>(`${this.API_URL}/users/${id}`, { role: newRole });
  }

  /**
   * Compter les utilisateurs par rôle
   */
  countUsersByRole(): Observable<{ admin: number; manager: number; operator: number }> {
    return this.getAllUsers().pipe(
      map(users => ({
        admin: users.filter(u => u.role === 'admin').length,
        manager: users.filter(u => u.role === 'manager').length,
        operator: users.filter(u => u.role === 'operator').length
      }))
    );
  }

  /**
   * Rechercher des utilisateurs
   */
  searchUsers(query: string): Observable<User[]> {
    return this.getAllUsers().pipe(
      map(users => users.filter(u => 
        u.firstName?.toLowerCase().includes(query.toLowerCase()) ||
        u.lastName?.toLowerCase().includes(query.toLowerCase()) ||
        u.email?.toLowerCase().includes(query.toLowerCase()) ||
        u.company?.toLowerCase().includes(query.toLowerCase())
      ))
    );
  }

  /**
   * Vérifier si un email existe déjà
   */
  emailExists(email: string, excludeId?: string): Observable<boolean> {
    return this.getAllUsers().pipe(
      map(users => {
        const exists = users.some(u => 
          u.email.toLowerCase() === email.toLowerCase() && u.id !== excludeId
        );
        return exists;
      })
    );
  }
}