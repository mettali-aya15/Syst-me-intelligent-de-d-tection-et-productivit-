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
  private readonly API_URL = 'http://localhost:3000'; // Mock API
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
  }

  get currentUserValue(): User | null {
    return this.currentUserSubject.value;
  }

  /**
   * Connexion avec email et mot de passe (AVEC API)
   */
  login(email: string, password: string): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${this.API_URL}/login`, { email, password })
      .pipe(
        tap(response => this.handleAuthResponse(response)),
        catchError(this.handleError)
      );
  }

 
 register(userData: any): Observable<AuthResponse> {
  console.log('Étape 1 : Création de l\'utilisateur dans /users...');
  
  return this.http.post<any>(`${this.API_URL}/api/users`, userData).pipe(
    switchMap((userCreated) => {
      console.log('Étape 1 RÉUSSIE. Utilisateur créé :', userCreated);

      // Préparation de l'objet employé
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

      console.log('Étape 2 : Création de l\'employé dans /employees...', newEmployee);

      // DEUXIÈME APPEL : Vers /employees
      return this.http.post(`${this.API_URL}/api/employees`, newEmployee).pipe(
        tap(() => console.log('Étape 2 RÉUSSIE. Employé ajouté dans employees')),
        map(() => {
          // On retourne l'objet attendu par le composant
          return {
            token: 'fake-jwt-' + Math.random(),
            user: userCreated,
            expiresIn: 3600
          } as AuthResponse;
        }),
        // Si la création de l'employé échoue, on veut quand même savoir pourquoi
        catchError(err => {
          console.error('ERREUR à l\'étape 2 (création employé) :', err);
          return throwError(() => new Error('Erreur lors de la création de la fiche employé'));
        })
      );
    }),
    tap(response => {
      console.log('Traitement final de l\'authentification...');
      this.handleAuthResponse(response);
    }),
    catchError(err => {
      console.error('ERREUR GLOBALE Register :', err);
      return this.handleError(err);
    })
  );
}
  /**
   * Fonction utilitaire pour définir un titre de poste selon le rôle choisi
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
 * Déconnexion de l'utilisateur
 * Nettoie les données locales et redirige vers /login
 */
logout(): void {
  this.clearAuthData();
  this.currentUserSubject.next(null);
  this.isAuthenticatedSubject.next(false);
  this.router.navigate(['/login']);
}

 private isTokenExpired(token: string): boolean {
  try {
    console.log('🔍 isTokenExpired() - Analyse détaillée');
    
    // Décoder le token (base64 simple dans notre cas)
    const payloadBase64 = token.split('.')[1] || token;
    const decodedJson = atob(payloadBase64);
    const decoded = JSON.parse(decodedJson);
    
    console.log('  Token décodé:', decoded);
    console.log('  exp brut:', decoded.exp);
    console.log('  Type exp:', typeof decoded.exp);
    
    if (!decoded.exp) {
      console.log('  → Pas de exp, token considéré valide');
      return false;
    }
    
    // Conversion en millisecondes
    const expirationMs = decoded.exp * 1000;
    const now = Date.now();
    
    console.log('  exp * 1000:', expirationMs);
    console.log('  Date.now():', now);
    console.log('  Différence (ms):', expirationMs - now);
    
    const isExpired = expirationMs < now;
    console.log('  → Expiré?', isExpired);
    
    return isExpired;
    
  } catch (e) {
    console.error('  ❌ Erreur parsing:', e);
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
        console.error('Erreur lors du parsing de l\'utilisateur:', e);
        return null;
      }
    }
    return null;
  }


  /**
   * Nettoie les données d'authentification
   */
  private clearAuthData(): void {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
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
      // Erreur côté client
      errorMessage = error.error.message;
    } else {
      // Erreur côté serveur
      errorMessage = error.error?.error || error.error?.message || `Erreur ${error.status}`;
    }

    console.error('❌ Erreur API:', errorMessage);
    return throwError(() => new Error(errorMessage));
  }

/**
 * Vérifie si l'utilisateur est authentifié
 */
isAuthenticated(): boolean {
  console.log('🔐 isAuthenticated() appelée');
  
  const token = this.getToken();
  console.log('  Token existe:', !!token);
  
  if (!token) {
    console.log('  → false (pas de token)');
    return false;
  }
  
  const expired = this.isTokenExpired(token);
  console.log('  Token expiré:', expired);
  console.log('  → Résultat:', !expired);
  
  return !expired;
}

/**
 * Vérifie si l'utilisateur a un rôle spécifique
 */
hasRole(role: string): boolean {
  console.log('🎭 hasRole() appelée');
  console.log('  Rôle recherché:', role);
  
  const user = this.currentUserValue;
  console.log('  currentUserValue:', user);
  console.log('  Role user:', user?.role);
  console.log('  Comparaison:', user?.role === role);
  
  return user?.role === role;
}

/**
 * Vérifie si l'utilisateur a l'un des rôles spécifiés
 */
hasAnyRole(roles: string[]): boolean {
  console.log('🎭 hasAnyRole() appelée');
  console.log('  Rôles autorisés:', roles);
  
  const user = this.currentUserValue;
  console.log('  User:', user);
  console.log('  Role user:', user?.role);
  
  const result = user ? roles.includes(user.role) : false;
  console.log('  Résultat:', result);
  
  return result;
}
}
