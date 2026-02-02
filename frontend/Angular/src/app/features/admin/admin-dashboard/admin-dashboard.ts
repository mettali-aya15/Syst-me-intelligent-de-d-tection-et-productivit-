import { Component } from '@angular/core';
import { Auth } from '../../../core/auth/auth';
import { Router, RouterLink } from '@angular/router';
import { RapportsComponent } from "../../repots/rapports/rapports";


@Component({
  standalone:true,
  selector: 'app-admin-dashboard',
  imports: [RouterLink],
  templateUrl: './admin-dashboard.html',
  styleUrl: './admin-dashboard.css',
})
export class AdminDashboard {
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
