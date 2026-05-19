import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { Auth } from '../../core/auth/auth';

@Component({
  selector: 'app-admin',
  standalone: true,
  imports: [CommonModule, RouterOutlet, RouterLink, RouterLinkActive],
  templateUrl: './admin.html',
  styleUrls: ['./admin.css']
})
export class Admin {
  private authService = inject(Auth);
  private router = inject(Router);

  /**
   * Déconnexion
   */
  logout(): void {
    if (confirm('Voulez-vous vraiment vous déconnecter ?')) {
      this.authService.logout();
      this.router.navigate(['/login']);
    }
  }
}