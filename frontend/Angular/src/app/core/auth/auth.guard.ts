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

  const isAuth = authService.isAuthenticated();
  console.log('  isAuthenticated():', isAuth);

  if (isAuth) {
    console.log('  ✅ Accès autorisé');
    return true;
  }

  console.log('  ❌ Redirection vers /login');
  authService.setRedirectUrl(state.url);
  return router.createUrlTree(['/login']);
};

/**
 * Guard spécifique pour les routes admin
 */
export const adminGuard: CanActivateFn = (route, state) => {
  console.log('🛡️ ========== ADMIN GUARD ==========');
  console.log('  URL demandée:', state.url);
  
  const authService = inject(Auth);
  const router = inject(Router);

  // ÉTAPE 1: Vérifier l'authentification
  const isAuth = authService.isAuthenticated();
  console.log('  1. isAuthenticated():', isAuth);
  
  if (!isAuth) {
    console.log('  ❌ Non authentifié → /login');
    authService.setRedirectUrl(state.url);
    return router.createUrlTree(['/login']);
  }

  // ÉTAPE 2: Vérifier le rôle admin
  const user = authService.currentUserValue;
  console.log('  2. currentUserValue:', user?.email);
  console.log('  3. Role:', user?.role);

  const hasAdminRole = user?.role === 'admin';
  console.log('  4. Role === "admin":', hasAdminRole);

  if (hasAdminRole) {
    console.log('  ✅ ACCÈS AUTORISÉ');
    return true;
  }

  console.warn('  ❌ Accès refusé: droits administrateur requis');
  return router.createUrlTree(['/access-denied']);
};