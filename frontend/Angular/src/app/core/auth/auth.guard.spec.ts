import { TestBed } from '@angular/core/testing';
import { Router, UrlTree } from '@angular/router';
import { authGuard } from './auth.guard';
import { Auth } from './auth';
import { ActivatedRouteSnapshot, RouterStateSnapshot } from '@angular/router';

describe('AuthGuard', () => {

  // ❌ ERREUR : authGuard est une fonction, pas une classe
  // let guard: authGuard;
  
  // ✅ CORRECTION : On déclare les dépendances directement
  let authService: jasmine.SpyObj<Auth>;
  let router: jasmine.SpyObj<Router>;
  let routeSnapshot: ActivatedRouteSnapshot;
  let stateSnapshot: jasmine.SpyObj<RouterStateSnapshot>;

  beforeEach(() => {
    // Créer des mocks pour AuthService et Router
    const authServiceSpy = jasmine.createSpyObj('Auth', [
      'isAuthenticated',
      'setRedirectUrl'
    ]);
    const routerSpy = jasmine.createSpyObj('Router', ['createUrlTree']);

    TestBed.configureTestingModule({
      providers: [
        // ❌ RETIRER : authGuard n'est pas un provider injectable
        // authGuard,
        { provide: Auth, useValue: authServiceSpy },
        { provide: Router, useValue: routerSpy }
      ]
    });

    // ❌ RETIRER : on ne peut pas inject une fonction guard
    // guard = TestBed.inject(authGuard);
    
    authService = TestBed.inject(Auth) as jasmine.SpyObj<Auth>;
    router = TestBed.inject(Router) as jasmine.SpyObj<Router>;

    // Créer des mocks pour les snapshots
    routeSnapshot = {} as ActivatedRouteSnapshot;
    stateSnapshot = { url: '/dashboard' } as jasmine.SpyObj<RouterStateSnapshot>;
  });

  // ❌ RETIRER : le guard n'est pas une instance
  // it('devrait être créé', () => {
  //   expect(guard).toBeTruthy();
  // });

  describe('canActivate', () => {
    it('devrait retourner true si l\'utilisateur est authentifié', () => {
      // Arrange
      authService.isAuthenticated.and.returnValue(true);

      // Act - ✅ On appelle directement la fonction guard
      const result = authGuard(routeSnapshot, stateSnapshot);

      // Assert
      expect(result).toBe(true);
      expect(authService.isAuthenticated).toHaveBeenCalled();
      expect(authService.setRedirectUrl).not.toHaveBeenCalled();
      expect(router.createUrlTree).not.toHaveBeenCalled();
    });

    it('devrait rediriger vers /login si l\'utilisateur n\'est pas authentifié', () => {
      // Arrange
      authService.isAuthenticated.and.returnValue(false);
      const mockUrlTree = {} as UrlTree;
      router.createUrlTree.and.returnValue(mockUrlTree);

      // Act
      const result = authGuard(routeSnapshot, stateSnapshot);

      // Assert
      expect(result).toBe(mockUrlTree);
      expect(authService.isAuthenticated).toHaveBeenCalled();
      expect(authService.setRedirectUrl).toHaveBeenCalledWith('/dashboard');
      expect(router.createUrlTree).toHaveBeenCalledWith(['/login']);
    });

    it('devrait sauvegarder l\'URL demandée avant de rediriger', () => {
      // Arrange
      authService.isAuthenticated.and.returnValue(false);
      stateSnapshot.url = '/admin/users';
      router.createUrlTree.and.returnValue({} as UrlTree);

      // Act
      authGuard(routeSnapshot, stateSnapshot);

      // Assert
      expect(authService.setRedirectUrl).toHaveBeenCalledWith('/admin/users');
    });

    it('devrait gérer les URLs avec paramètres de requête', () => {
      // Arrange
      authService.isAuthenticated.and.returnValue(false);
      stateSnapshot.url = '/dashboard?tab=analytics';
      router.createUrlTree.and.returnValue({} as UrlTree);

      // Act
      authGuard(routeSnapshot, stateSnapshot);

      // Assert
      expect(authService.setRedirectUrl).toHaveBeenCalledWith('/dashboard?tab=analytics');
    });
  });

  describe('Scénarios d\'intégration', () => {
    it('devrait permettre l\'accès à un utilisateur authentifié avec token valide', () => {
      // Arrange
      authService.isAuthenticated.and.returnValue(true);

      // Act
      const result = authGuard(routeSnapshot, stateSnapshot);

      // Assert
      expect(result).toBe(true);
    });

    it('devrait bloquer l\'accès à un utilisateur avec token expiré', () => {
      // Arrange
      authService.isAuthenticated.and.returnValue(false);
      router.createUrlTree.and.returnValue({} as UrlTree);

      // Act
      const result = authGuard(routeSnapshot, stateSnapshot);

      // Assert
      expect(result).toBeInstanceOf(Object); // UrlTree
      expect(router.createUrlTree).toHaveBeenCalledWith(['/login']);
    });

    it('devrait bloquer l\'accès à un utilisateur non connecté', () => {
      // Arrange
      authService.isAuthenticated.and.returnValue(false);
      router.createUrlTree.and.returnValue({} as UrlTree);

      // Act
      const result = authGuard(routeSnapshot, stateSnapshot);

      // Assert
      expect(result).not.toBe(true);
      expect(authService.setRedirectUrl).toHaveBeenCalled();
    });
  });

  describe('Cas limites', () => {
    it('devrait gérer une URL vide', () => {
      // Arrange
      authService.isAuthenticated.and.returnValue(false);
      stateSnapshot.url = '';
      router.createUrlTree.and.returnValue({} as UrlTree);

      // Act
      authGuard(routeSnapshot, stateSnapshot);

      // Assert
      expect(authService.setRedirectUrl).toHaveBeenCalledWith('');
    });

    it('devrait gérer une URL avec fragment', () => {
      // Arrange
      authService.isAuthenticated.and.returnValue(false);
      stateSnapshot.url = '/dashboard#section1';
      router.createUrlTree.and.returnValue({} as UrlTree);

      // Act
      authGuard(routeSnapshot, stateSnapshot);

      // Assert
      expect(authService.setRedirectUrl).toHaveBeenCalledWith('/dashboard#section1');
    });

    it('ne devrait pas appeler setRedirectUrl si l\'utilisateur est authentifié', () => {
      // Arrange
      authService.isAuthenticated.and.returnValue(true);

      // Act
      authGuard(routeSnapshot, stateSnapshot);

      // Assert
      expect(authService.setRedirectUrl).not.toHaveBeenCalled();
    });
  });

  describe('Performance', () => {
    it('devrait appeler isAuthenticated une seule fois par vérification', () => {
      // Arrange
      authService.isAuthenticated.and.returnValue(true);

      // Act
      authGuard(routeSnapshot, stateSnapshot);

      // Assert
      expect(authService.isAuthenticated).toHaveBeenCalledTimes(1);
    });

    it('devrait créer l\'UrlTree une seule fois en cas de redirection', () => {
      // Arrange
      authService.isAuthenticated.and.returnValue(false);
      router.createUrlTree.and.returnValue({} as UrlTree);

      // Act
      authGuard(routeSnapshot, stateSnapshot);

      // Assert
      expect(router.createUrlTree).toHaveBeenCalledTimes(1);
    });
  });
});