import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { BehaviorSubject, Observable, throwError } from 'rxjs';
import { map, catchError, tap, switchMap } from 'rxjs/operators';
import { Router } from '@angular/router';
import { User } from '../models/user';

export interface AuthResponse {
  token: string;
  user: User;
  expiresIn: number;
}

@Injectable({
  providedIn: 'root'
})
export class Auth {
  private readonly API_URL = 'http://localhost:3000';
  private readonly TOKEN_KEY = 'auth_token';
  private readonly USER_KEY = 'current_user';
  private readonly REDIRECT_URL_KEY = 'redirect_url';

  private http = inject(HttpClient);
  private router = inject(Router); 

  private currentUserSubject: BehaviorSubject<User | null>;
  public currentUser$: Observable<User | null>;

  private isAuthenticatedSubject: BehaviorSubject<boolean>;
  public isAuthenticated$: Observable<boolean>;

  constructor() {
    const storedUser = this.getUserFromStorage();
    this.currentUserSubject = new BehaviorSubject<User | null>(storedUser);
    this.currentUser$ = this.currentUserSubject.asObservable();

    this.isAuthenticatedSubject = new BehaviorSubject<boolean>(!!storedUser && !!this.getToken());
    this.isAuthenticated$ = this.isAuthenticatedSubject.asObservable();
    
    console.log('🔐 Auth Service initialisé');
  }

  get currentUserValue(): User | null {
    return this.currentUserSubject.value;
  }

  /**
   * Connexion avec email et mot de passe
   */
  login(email: string, password: string): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${this.API_URL}/login`, { email, password })
      .pipe(
        tap(response => this.handleAuthResponse(response)),
        catchError(this.handleError)
      );
  }

  /**
   * Inscription
   */
  register(userData: any): Observable<AuthResponse> {
    console.log('📝 Création utilisateur...');
    
    return this.http.post<any>(`${this.API_URL}/api/users`, userData).pipe(
      switchMap((userCreated) => {
        const newEmployee = {
          firstName: userData.firstName || 'Sans prénom',
          lastName: userData.lastName || 'Sans nom',
          email: userData.email,
          role: userData.role || 'operator',
          phone: userData.phone || '-',
          department: userData.company || 'Non assigné',
          position: this.getPositionFromRole(userData.role),
          status: 'active',
          performance: 0,
          avatar: `https://i.pravatar.cc/150?u=${userData.email}`,
          shift: 'Matin'
        };

        return this.http.post(`${this.API_URL}/api/employees`, newEmployee).pipe(
          map(() => ({
            token: 'fake-jwt-' + Math.random(),
            user: userCreated,
            expiresIn: 3600
          } as AuthResponse)),
          catchError(err => {
            console.error('❌ Erreur création employé:', err);
            return throwError(() => new Error('Erreur lors de la création de la fiche employé'));
          })
        );
      }),
      tap(response => this.handleAuthResponse(response)),
      catchError(this.handleError)
    );
  }

  /**
   * Fonction utilitaire pour définir un titre de poste
   */
  private getPositionFromRole(role: string): string {
    switch (role) {
      case 'admin': return 'Administrateur Système';
      case 'manager': return 'Responsable de Production';
      case 'operator': return 'Opérateur de Ligne';
      default: return 'Employé';
    }
  }

  /**
   * 🚪 DÉCONNEXION - MÉTHODE PRINCIPALE
   */
  /**
 * 🚪 DÉCONNEXION - AVEC RECHARGEMENT FORCÉ
 */
logout(): void {
  console.log('🚪 ========== DÉCONNEXION ==========');
  
  // 1. Nettoyer localStorage
  console.log('  Étape 1: Nettoyage localStorage...');
  localStorage.removeItem(this.TOKEN_KEY);
  localStorage.removeItem(this.USER_KEY);
  localStorage.removeItem(this.REDIRECT_URL_KEY);
  localStorage.removeItem('camia_auth_token');
  localStorage.removeItem('camia_user');
  
  console.log('  ✅ localStorage nettoyé');
  
  // 2. Réinitialiser les observables
  console.log('  Étape 2: Réinitialisation observables...');
  this.currentUserSubject.next(null);
  this.isAuthenticatedSubject.next(false);
  console.log('  ✅ Observables réinitialisés');
  
  // 3. Redirection FORCÉE avec rechargement
  console.log('  Étape 3: Redirection FORCÉE vers /login...');
  
  // ✅ UTILISE window.location.href au lieu de router.navigate
  window.location.href = '/login';
  
  console.log('========== FIN DÉCONNEXION ==========');
}

  /**
   * Vérifier si le token est expiré
   */
  private isTokenExpired(token: string): boolean {
    try {
      const payloadBase64 = token.split('.')[1] || token;
      const decodedJson = atob(payloadBase64);
      const decoded = JSON.parse(decodedJson);
      
      if (!decoded.exp) {
        return false;
      }
      
      const expirationMs = decoded.exp * 1000;
      const now = Date.now();
      
      return expirationMs < now;
      
    } catch (e) {
      console.error('❌ Erreur parsing token:', e);
      return true;
    }
  }

  /**
   * Obtenir l'utilisateur courant depuis l'API
   */
  getCurrentUser(): Observable<User> {
    return this.http.get<User>(`${this.API_URL}/api/me`)
      .pipe(
        tap(user => {
          this.currentUserSubject.next(user);
          localStorage.setItem(this.USER_KEY, JSON.stringify(user));
        }),
        catchError(this.handleError)
      );
  }

  /**
   * Récupère le token JWT
   */
  getToken(): string | null {
    return localStorage.getItem(this.TOKEN_KEY);
  }

  /**
   * Stocke l'URL de redirection
   */
  setRedirectUrl(url: string): void {
    localStorage.setItem(this.REDIRECT_URL_KEY, url);
  }

  /**
   * Récupère l'URL de redirection
   */
  getRedirectUrl(): string | null {
    const url = localStorage.getItem(this.REDIRECT_URL_KEY);
    localStorage.removeItem(this.REDIRECT_URL_KEY);
    return url;
  }

  /**
   * Gère la réponse d'authentification
   */
  private handleAuthResponse(response: AuthResponse): void {
    localStorage.setItem(this.TOKEN_KEY, response.token);
    localStorage.setItem(this.USER_KEY, JSON.stringify(response.user));
    this.currentUserSubject.next(response.user);
    this.isAuthenticatedSubject.next(true);
  }

  /**
   * Récupère l'utilisateur du localStorage
   */
  private getUserFromStorage(): User | null {
    const userJson = localStorage.getItem(this.USER_KEY);
    if (userJson) {
      try {
        return JSON.parse(userJson);
      } catch (e) {
        console.error('❌ Erreur parsing user:', e);
        return null;
      }
    }
    return null;
  }

  /**
   * Met à jour l'utilisateur
   */
  updateUser(user: User): void {
    localStorage.setItem(this.USER_KEY, JSON.stringify(user));
    this.currentUserSubject.next(user);
  }

  /**
   * Gère les erreurs HTTP
   */
  private handleError(error: HttpErrorResponse): Observable<never> {
    let errorMessage = 'Une erreur est survenue';

    if (error.error instanceof ErrorEvent) {
      errorMessage = error.error.message;
    } else {
      errorMessage = error.error?.error || error.error?.message || `Erreur ${error.status}`;
    }

    console.error('❌ Erreur API:', errorMessage);
    return throwError(() => new Error(errorMessage));
  }

  /**
   * Vérifie si l'utilisateur est authentifié
   */
  isAuthenticated(): boolean {
    const token = this.getToken();
    
    if (!token) {
      return false;
    }
    
    return !this.isTokenExpired(token);
  }

  /**
   * Vérifie si l'utilisateur a un rôle spécifique
   */
  hasRole(role: string): boolean {
    const user = this.currentUserValue;
    return user?.role === role;
  }

  /**
   * Vérifie si l'utilisateur a l'un des rôles spécifiés
   */
  hasAnyRole(roles: string[]): boolean {
    const user = this.currentUserValue;
    return user ? roles.includes(user.role) : false;
  }
}