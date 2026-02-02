import { Component } from '@angular/core';

import { Auth } from '../../../core/auth/auth';
import { Router, RouterLink } from '@angular/router';

@Component({
  selector: 'app-manager-dashboard',
 standalone:true,
    imports: [RouterLink],
  templateUrl: './manager-dashboard.html',
  styleUrl: './manager-dashboard.css',
})
export class Manager {
    constructor(
      private authService: Auth,
      private router: Router
    ) {}
    hasUnreadNotifications = false; // Mettre à jour selon votre logique
    logout(): void {
      this.authService.logout();
      this.router.navigate(['/login']);
    }
    get isAdmin(): boolean {
      return this.authService.hasRole('admin');
    }
  
    get isManager(): boolean {
      return this.authService.hasAnyRole(['admin', 'manager']);
    }

}
