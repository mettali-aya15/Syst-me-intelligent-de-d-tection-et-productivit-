// src/app/features/notifications/services/notification.service.ts

import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { tap, map } from 'rxjs/operators';
// src/app/features/notifications/models/notification.model.ts

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

@Injectable({
  providedIn: 'root'
})
export class NotificationService {
  private readonly API_URL = 'http://localhost:3000/api';
  private http = inject(HttpClient);

  private notificationsSubject = new BehaviorSubject<Notification[]>([]);
  public notifications$ = this.notificationsSubject.asObservable();

  // Compteur de notifications non lues
  public unreadCount$ = this.notifications$.pipe(
    map(notifs => notifs.filter(n => !n.read).length)
  );

  getNotifications(): Observable<Notification[]> {
    return this.http.get<Notification[]>(`${this.API_URL}/notifications`)
      .pipe(
        tap(notifications => {
          this.notificationsSubject.next(notifications);
          console.log('✅ Notifications chargées:', notifications.length);
        })
      );
  }

  markAsRead(id: string): Observable<Notification> {
    return this.http.patch<Notification>(`${this.API_URL}/notifications/${id}`, { read: true })
      .pipe(
        tap(() => this.getNotifications().subscribe())
      );
  }

  markAllAsRead(): Observable<void> {
    const unread = this.notificationsSubject.value.filter(n => !n.read);
    
    // Marquer toutes les non lues
    const requests = unread.map(n => 
      this.http.patch(`${this.API_URL}/notifications/${n.id}`, { read: true })
    );

    return new Observable(observer => {
      Promise.all(requests.map(req => req.toPromise()))
        .then(() => {
          this.getNotifications().subscribe();
          observer.next();
          observer.complete();
        })
        .catch(err => observer.error(err));
    });
  }

  deleteNotification(id: string): Observable<void> {
    return this.http.delete<void>(`${this.API_URL}/notifications/${id}`)
      .pipe(
        tap(() => this.getNotifications().subscribe())
      );
  }

  createNotification(notification: Omit<Notification, 'id'>): Observable<Notification> {
    return this.http.post<Notification>(`${this.API_URL}/notifications`, {
      ...notification,
      id: 'notif_' + Date.now(),
      createdAt: new Date().toISOString(),
      read: false
    }).pipe(
      tap(() => this.getNotifications().subscribe())
    );
  }
}