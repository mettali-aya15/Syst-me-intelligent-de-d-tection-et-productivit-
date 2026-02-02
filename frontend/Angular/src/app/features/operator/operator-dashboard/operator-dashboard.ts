import { Component } from '@angular/core';
import { Auth } from '../../../core/auth/auth';
import { Router, RouterLink } from '@angular/router';

@Component({
  selector: 'app-operator-dashboard',
  standalone:true,
  imports: [RouterLink],
  templateUrl: './operator-dashboard.html',
  styleUrl: './operator-dashboard.css',
})
export class OperatorDashboard {
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
