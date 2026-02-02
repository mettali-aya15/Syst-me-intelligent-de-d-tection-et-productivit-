// src/app/features/notifications/notification-list.component.ts

import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NotificationService } from '../notifications';
import { RouterLink } from '@angular/router';
export interface Notification {
 id:string;
  type: 'alert' | 'maintenance' | 'info' | 'warning';
  title: string;
  message: string;
  userId: string;
  read: boolean;
  createdAt: string;
  priority: 'high' | 'medium' | 'low';
}

@Component({
  selector: 'app-notification-list',
  standalone: true,
  imports: [CommonModule,RouterLink],
templateUrl:"./notif-list.html",
styleUrl:"./notif-list.css"
})
export class NotificationListComponent implements OnInit {
  private notificationService = inject(NotificationService);

  notifications$ = this.notificationService.notifications$;
  unreadCount$ = this.notificationService.unreadCount$;

  ngOnInit(): void {
    this.notificationService.getNotifications().subscribe();
  }

  markAsRead(id: string): void {
    this.notificationService.markAsRead(id).subscribe();
  }

  markAllAsRead(): void {
    this.notificationService.markAllAsRead().subscribe({
      next: () => {
        console.log('✅ Toutes les notifications marquées comme lues');
      }
    });
  }

  deleteNotification(notif: Notification): void {
    if (confirm(`Supprimer la notification "${notif.title}" ?`)) {
      this.notificationService.deleteNotification(notif.id).subscribe({
        next: () => {
          console.log('✅ Notification supprimée');
        }
      });
    }
  }

  getHighPriorityCount(): number {
    const notifications = this.notificationService['notificationsSubject'].value;
    return notifications.filter(n => n.priority === 'high').length;
  }

  getTodayCount(): number {
    const notifications = this.notificationService['notificationsSubject'].value;
    const today = new Date().toISOString().split('T')[0];
    return notifications.filter(n => n.createdAt.startsWith(today)).length;
  }

  getPriorityLabel(priority: string): string {
    const labels = {
      high: 'URGENT',
      medium: 'MOYEN',
      low: 'BAS'
    };
    return labels[priority as keyof typeof labels] || priority;
  }

  getRelativeTime(dateString: string): string {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'À l\'instant';
    if (diffMins < 60) return `Il y a ${diffMins} min`;
    if (diffHours < 24) return `Il y a ${diffHours}h`;
    if (diffDays < 7) return `Il y a ${diffDays}j`;
    
    return date.toLocaleDateString('fr-FR');
  }
}