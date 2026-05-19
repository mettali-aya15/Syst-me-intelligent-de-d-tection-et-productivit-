import { Routes } from '@angular/router';
import { authGuard, adminGuard } from './core/auth/auth.guard';

export const routes: Routes = [
  {
    path: '',
    redirectTo: 'login',
    pathMatch: 'full'
  },

  {
    path: 'login',
    loadComponent: () => import('./features/login/login').then(m => m.Login)
  },

  {
    path: 'admin',
    canActivate: [authGuard, adminGuard],
    children: [
      {
        path: '',
        redirectTo: 'dashboard',
        pathMatch: 'full'
      },
      {
        path: 'dashboard',
        loadComponent: () => import('./features/admin/admin-dashboard/admin-dashboard').then(m => m.AdminDashboardComponent)
      },
      {
        path: 'kpi',
        loadComponent: () => import('./features/admin/kpi-dashboard/kpi-dashboard.component').then(m => m.KpiDashboardComponent)
      },
      {
        path: 'videos',
        loadComponent: () => import('./features/videos/video-list/video-list').then(m => m.VideoListComponent)
      },
      // ✅ ROUTE UPLOAD VIDEO
      {
        path: 'videos/upload',
        loadComponent: () => import('./features/videos/video-upload/video-upload').then(m => m.VideoUploadComponent)
      },
      // ✅ ROUTE DÉTAILS VIDEO (doit être APRÈS upload)
      {
        path: 'videos/:id',
        loadComponent: () => import('./features/videos/video-detail/video-detail').then(m => m.VideoDetailComponent)
      },
      {
        path: 'employees',
        loadComponent: () => import('./features/employees/emp-list/emp-list').then(m => m.EmpListComponent)
      },
      {
        path: 'notifications',
        loadComponent: () => import('./features/admin/notifications/notifications.component').then(m => m.NotificationsComponent)
      },
      {
        path: 'settings',
        loadComponent: () => import('./features/admin/settings/settings.component').then(m => m.SettingsComponent)
      }
    ]
  },

  {
    path: '**',
    redirectTo: 'login'
  }
];