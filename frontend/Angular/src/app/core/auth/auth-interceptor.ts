import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Auth } from './auth';
import { catchError, throwError } from 'rxjs';
import { Router } from '@angular/router';

/**
 * Intercepteur HTTP pour ajouter le token JWT aux requêtes
 */
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(Auth);
  const router = inject(Router);
  
  const token = authService.getToken();

  // Cloner la requête et ajouter le header Authorization si le token existe
  if (token) {
    req = req.clone({
      setHeaders: {
        Authorization: `Bearer ${token}`
      }
    });
  }

  // Gérer les erreurs HTTP
  return next(req).pipe(
    catchError((error) => {
      // Si erreur 401 (Unauthorized), rediriger vers login
      if (error.status === 401) {
        authService.logout();
        router.navigate(['/login']);
      }

      // Si erreur 403 (Forbidden), rediriger vers access-denied
      if (error.status === 403) {
        router.navigate(['/access-denied']);
      }

      return throwError(() => error);
    })
  );
};