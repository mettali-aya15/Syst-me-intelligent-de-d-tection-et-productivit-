import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { NotificationService, Notification } from '../../../core/services/notification.service';

@Component({
  selector: 'app-notifications',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './notifications.component.html',
  styleUrls: ['./notifications.component.scss']
})
export class NotificationsComponent implements OnInit, OnDestroy {
  private notificationService = inject(NotificationService);
  private router = inject(Router);

  notifications: Notification[] = [];
  filteredNotifications: Notification[] = [];
  currentFilter: 'all' | 'unread' | 'priority' | 'today' = 'all';

  totalCount = 0;
  unreadCount = 0;
  priorityCount = 0;
  todayCount = 0;

  private updateListener = this.onNotificationsUpdated.bind(this);

  ngOnInit(): void {
    // ✅ Marquer toutes comme "anciennes" (pas nouvelles) à l'ouverture de la page
    this.notificationService.markAllAsOld();
    
    this.loadNotifications();
    window.addEventListener('notifications-updated', this.updateListener);
  }

  ngOnDestroy(): void {
    window.removeEventListener('notifications-updated', this.updateListener);
  }

  private onNotificationsUpdated(): void {
    console.log('🔄 Notifications mises à jour');
    this.loadNotifications();
  }

  loadNotifications(): void {
    this.notifications = this.notificationService.getAllNotifications();
    this.updateStats();
    this.applyFilter(this.currentFilter);
    console.log('📋 Notifications chargées:', this.notifications.length);
  }

  updateStats(): void {
    this.totalCount = this.notifications.length;
    this.unreadCount = this.notificationService.getUnreadCount();
    this.priorityCount = this.notificationService.getHighPriorityCount();
    this.todayCount = this.notificationService.getTodayCount();
  }

  applyFilter(filter: 'all' | 'unread' | 'priority' | 'today'): void {
    this.currentFilter = filter;

    switch (filter) {
      case 'all':
        this.filteredNotifications = [...this.notifications];
        break;
      case 'unread':
        this.filteredNotifications = this.notifications.filter(n => !n.read);
        break;
      case 'priority':
        this.filteredNotifications = this.notifications.filter(n => n.priority === 'high');
        break;
      case 'today':
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        this.filteredNotifications = this.notifications.filter(n => {
          const notifDate = new Date(n.timestamp);
          notifDate.setHours(0, 0, 0, 0);
          return notifDate.getTime() === today.getTime();
        });
        break;
    }

    console.log(`🔍 Filtre "${filter}": ${this.filteredNotifications.length} notifications`);
  }

  markAsRead(notification: Notification): void {
    this.notificationService.markAsRead(notification.id);
  }

  markAllAsRead(): void {
    if (confirm('Marquer toutes les notifications comme lues ?')) {
      this.notificationService.markAllAsRead();
    }
  }

  deleteNotification(notification: Notification, event: Event): void {
    event.stopPropagation();
    this.notificationService.deleteNotification(notification.id);
  }

  deleteAll(): void {
    if (confirm('⚠️ Supprimer TOUTES les notifications ?\n\nCette action est irréversible !')) {
      this.notificationService.deleteAllNotifications();
    }
  }

  navigateToLink(notification: Notification): void {
    if (notification.link) {
      this.markAsRead(notification);
      this.router.navigate([notification.link]);
    }
  }

  getTimeAgo(date: Date): string {
    const now = new Date().getTime();
    const timestamp = new Date(date).getTime();
    const diff = now - timestamp;

    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (seconds < 60) return `Il y a ${seconds}s`;
    if (minutes < 60) return `Il y a ${minutes} min`;
    if (hours < 24) return `Il y a ${hours}h`;
    return `Il y a ${days}j`;
  }

  getIconClass(type: string): string {
    const iconMap: { [key: string]: string } = {
      'success': 'fas fa-check-circle',
      'warning': 'fas fa-exclamation-triangle',
      'error': 'fas fa-exclamation-circle',
      'info': 'fas fa-info-circle'
    };
    
    return iconMap[type] || 'fas fa-bell';
  }

  getPriorityLabel(type: string): string {
    const labelMap: { [key: string]: string } = {
      'error': 'IMPORTANT',
      'warning': 'IMPORTANT',
      'success': 'INFO',
      'info': 'INFO'
    };
    
    return labelMap[type] || 'INFO';
  }

  goBack(): void {
    this.router.navigate(['/admin/dashboard']);
  }
}