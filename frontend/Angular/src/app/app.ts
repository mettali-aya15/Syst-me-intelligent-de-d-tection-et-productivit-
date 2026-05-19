import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterOutlet, NavigationEnd } from '@angular/router';
import { filter } from 'rxjs/operators';
import { WebSocketService } from './core/services/websocket.service';
import { NavbarComponent } from './shared/components/navbar/navbar.component';
import { Auth } from './core/auth/auth';
import { SettingsService } from './core/services/settings.service';
import { TranslationService } from './core/services/translation.service';


@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet, NavbarComponent],
  template: `
    <!-- ✅ Navbar conditionnelle - cachée sur login/register -->
    <app-navbar *ngIf="showNavbar"></app-navbar>
    
    <main [class]="showNavbar ? 'main-content' : 'main-content-full'">
      <router-outlet></router-outlet>
    </main>
  `,
  styles: [`
    .main-content {
      margin-top: 70px;
      padding: 20px;
      min-height: calc(100vh - 70px);
    }

    .main-content-full {
      padding: 0;
      min-height: 100vh;
    }
  `]
})
export class App implements OnInit, OnDestroy {
  private wsService = inject(WebSocketService);
  private router = inject(Router);
  private authService = inject(Auth);
  private settingsService = inject(SettingsService);
  private translationService = inject(TranslationService); // ✅ INJECTION
  
  title = 'CAMIA Factory';
  showNavbar = true;

  ngOnInit(): void {
    console.log('🚀 Application CAMIA Factory démarrée');
    
    // ✅ Appliquer le thème et la langue sauvegardés au démarrage
    const settings = this.settingsService.getCurrentSettings();
    this.settingsService.applyTheme(settings.user.theme);
    this.settingsService.applyLanguage(settings.user.language);
    
    // ✅ IMPORTANT : Synchroniser avec TranslationService
    this.translationService.setLanguage(settings.user.language);
    
    console.log('🎨 Theme appliqué au démarrage:', settings.user.theme);
    console.log('🌍 Langue appliquée au démarrage:', settings.user.language);
    
    // ✅ Écouter les changements de route
    this.router.events
      .pipe(filter(event => event instanceof NavigationEnd))
      .subscribe((event: any) => {
        this.updateNavbarVisibility(event.urlAfterRedirects);
      });

    // Vérifier la route initiale
    this.updateNavbarVisibility(this.router.url);
    
    try {
      console.log('🔌 Initialisation WebSocket...');
      this.wsService.connect();
    } catch (error) {
      console.error('❌ Erreur connexion WebSocket:', error);
    }
  }

  ngOnDestroy(): void {
    console.log('🛑 Application fermée');
    
    try {
      this.wsService.disconnect();
    } catch (error) {
      console.error('❌ Erreur déconnexion WebSocket:', error);
    }
  }

  /**
   * ✅ Mettre à jour la visibilité de la navbar
   */
  private updateNavbarVisibility(url: string): void {
    console.log('📍 Route actuelle:', url);
    
    const publicRoutes = ['/login', '/register', '/auth/login', '/auth/register'];
    const isPublicRoute = publicRoutes.some(route => url.startsWith(route));
    
    // ✅ Vérifier aussi l'authentification
    const isAuthenticated = this.authService.isAuthenticated();
    
    console.log('  Est route publique:', isPublicRoute);
    console.log('  Est authentifié:', isAuthenticated);
    
    // Cacher la navbar sur les routes publiques OU si non authentifié
    this.showNavbar = !isPublicRoute && isAuthenticated;
    
    console.log('  → Navbar visible:', this.showNavbar);
  }
}