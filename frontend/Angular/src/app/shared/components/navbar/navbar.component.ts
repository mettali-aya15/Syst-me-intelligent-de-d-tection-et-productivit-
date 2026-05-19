import { Component, inject, HostListener, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterLink, RouterLinkActive } from '@angular/router';
import { NotificationService } from '../../../core/services/notification.service';
import { Auth } from '../../../core/auth/auth';
import { TranslatePipe } from '../../pipes/translate.pipe'; // ✅ IMPORTER

@Component({
  selector: 'app-navbar',
  standalone: true,
  imports: [CommonModule, RouterLink, RouterLinkActive, TranslatePipe], // ✅ AJOUTER TranslatePipe
  templateUrl: './navbar.component.html',
  styleUrls: ['./navbar.component.scss']
})
export class NavbarComponent implements OnInit, OnDestroy {
  private router = inject(Router);
  private notificationService = inject(NotificationService);
  private authService = inject(Auth);

  dropdownOpen = false;
  unreadCount = 0;

  // Info utilisateur
  userName = 'Administrateur';
  userEmail = 'admin@camia.com';
  userInitials = 'AU';

  private updateListener = this.updateUnreadCount.bind(this);

  ngOnInit(): void {
    this.updateUnreadCount();
    window.addEventListener('notifications-updated', this.updateListener);
    this.loadUserInfo();
  }

  ngOnDestroy(): void {
    window.removeEventListener('notifications-updated', this.updateListener);
  }

  /**
   * Charger les infos utilisateur
   */
  private loadUserInfo(): void {
    const user = this.authService.currentUserValue;
    if (user) {
      this.userName = `${user.firstName || ''} ${user.lastName || ''}`.trim() || 'Administrateur';
      this.userEmail = user.email || 'admin@camia.com';
      this.userInitials = this.getInitials(this.userName);
    }
  }

  /**
   * Obtenir initiales
   */
  private getInitials(name: string): string {
    const parts = name.trim().split(' ');
    if (parts.length >= 2) {
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return name.substring(0, 2).toUpperCase();
  }

  private updateUnreadCount(): void {
    this.unreadCount = this.notificationService.getUnreadCount();
  }

  toggleDropdown(): void {
    this.dropdownOpen = !this.dropdownOpen;
  }

  closeDropdown(): void {
    this.dropdownOpen = false;
  }

  @HostListener('document:click', ['$event'])
  onDocumentClick(event: MouseEvent): void {
    const target = event.target as HTMLElement;
    const clickedInside = target.closest('.user-dropdown');
    
    if (!clickedInside && this.dropdownOpen) {
      this.closeDropdown();
    }
  }

  @HostListener('document:keydown.escape')
  onEscapeKey(): void {
    if (this.dropdownOpen) {
      this.closeDropdown();
    }
  }

  /**
   * 🚪 DÉCONNEXION - UTILISE AUTH SERVICE
   */
  logout(): void {
    console.log('🚪 Déconnexion demandée');
    this.closeDropdown();
    this.authService.logout();
  }
}