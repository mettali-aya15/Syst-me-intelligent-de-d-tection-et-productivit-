import { inject } from '@angular/core';
import { Router, CanActivateFn } from '@angular/router';
import { Auth } from './auth';

/**
 * Guard pour protéger les routes nécessitant une authentification
 */
export const authGuard: CanActivateFn = (route, state) => {
  console.log('🛡️ ========== AUTH GUARD ==========');
  const authService = inject(Auth);
  const router = inject(Router);
     data: { roles: ['admin', 'manager'] }

  const isAuth = authService.isAuthenticated();
  console.log('isAuthenticated():', isAuth);

  if (isAuth) {
    console.log('Accès autorisé');
    return true;
  }

  console.log('Redirection vers /login');
  authService.setRedirectUrl(state.url);
  return router.createUrlTree(['/login']);
};

/**
 * Guard pour protéger les routes basées sur les rôles
 */
export const roleGuard: CanActivateFn = (route, state) => {
  console.log('🛡️ ========== ROLE GUARD ==========');
  const authService = inject(Auth);
  const router = inject(Router);

  // Vérifier d'abord si l'utilisateur est authentifié
  const isAuth = authService.isAuthenticated();
  console.log('1. isAuthenticated():', isAuth);
  
  if (!isAuth) {
    console.log('Non authentifié → /login');
    authService.setRedirectUrl(state.url);
    return router.createUrlTree(['/login']);
  }

  // Récupérer les rôles autorisés
  const allowedRoles = route.data['roles'] as string[];
  console.log('2. Rôles autorisés:', allowedRoles);

  if (!allowedRoles || allowedRoles.length === 0) {
    console.log('Aucun rôle spécifié → Accès autorisé');
    return true;
  }

  const user = authService.currentUserValue;
  console.log('3. User actuel:', user);
  console.log('4. Role user:', user?.role);

  const hasRole = authService.hasAnyRole(allowedRoles);
  console.log('5. hasAnyRole():', hasRole);

  if (hasRole) {
    console.log(' Rôle valide → Accès autorisé');
    return true;
  }

  console.warn(' Rôle insuffisant → /access-denied');
  return router.createUrlTree(['/access-denied']);
};

/**
 * Guard spécifique pour les routes admin
 */
export const adminGuard: CanActivateFn = (route, state) => {
  console.log('🛡️  ========== ADMIN GUARD ==========');
  console.log('URL demandée:', state.url);
  
  const authService = inject(Auth);
  const router = inject(Router);

  // ÉTAPE 1: Vérifier l'authentification
  const isAuth = authService.isAuthenticated();
  console.log('1. isAuthenticated():', isAuth);
  
  if (!isAuth) {
    console.log(' Non authentifié → /login');
    authService.setRedirectUrl(state.url);
    return router.createUrlTree(['/login']);
  }

  // ÉTAPE 2: Vérifier le rôle
  const user = authService.currentUserValue;
  console.log('2. currentUserValue:', user);
  console.log('3. Role:', user?.role);
  console.log('4. Type du role:', typeof user?.role);

  const hasAdminRole = authService.hasRole('admin');
  console.log('5. hasRole("admin"):', hasAdminRole);

  // Test de comparaison directe
  const directCheck = user?.role === 'admin';
  console.log('6. Comparaison directe (role === "admin"):', directCheck);

  if (hasAdminRole) {
    console.log('✅ ACCÈS AUTORISÉ - Retour true');
    console.log('=====================================');
    return true;
  }

  console.warn('❌ Accès refusé: droits administrateur requis');
  console.log('Redirection vers /access-denied');
  console.log('=====================================');
  return router.createUrlTree(['/access-denied']);
};

/**
 * Guard spécifique pour les routes manager
 */
export const managerGuard: CanActivateFn = (route, state) => {
  console.log('🛡️ ========== MANAGER GUARD ==========');
  const authService = inject(Auth);
  const router = inject(Router);

  const isAuth = authService.isAuthenticated();
  console.log('1. isAuthenticated():', isAuth);

  if (!isAuth) {
    console.log('❌ Non authentifié → /login');
    authService.setRedirectUrl(state.url);
    return router.createUrlTree(['/login']);
  }

  const user = authService.currentUserValue;
  console.log('2. User:', user);
  console.log('3. Role:', user?.role);

  const hasManagerRole = authService.hasAnyRole(['admin', 'manager']);
  console.log('4. hasAnyRole(["admin", "manager"]):', hasManagerRole);

  if (hasManagerRole) {
    console.log('✅ Accès autorisé');
    return true;
  }

  console.warn('❌ Accès refusé: droits manager requis');
  return router.createUrlTree(['/access-denied']);
};