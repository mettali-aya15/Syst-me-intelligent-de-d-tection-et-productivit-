import { Injectable } from '@angular/core';

export interface Notification {
  id: string;
  type: 'success' | 'warning' | 'error' | 'info';
  priority: 'normal' | 'high';
  title: string;
  message: string;
  timestamp: Date;
  read: boolean;
  isNew: boolean; // ✅ NOUVEAU : Pour identifier les nouvelles notifications
  videoId?: string;
  link?: string;
}

@Injectable({
  providedIn: 'root'
})
export class NotificationService {
  private readonly STORAGE_KEY = 'camia_notifications';
  private readonly MAX_NOTIFICATIONS = 100;

  constructor() {
    console.log('🔔 NotificationService initialisé');
    this.initializeTestNotifications();
  }

  // ========================================
  // 🧪 INITIALISATION NOTIFICATIONS TEST
  // ========================================
  
  private initializeTestNotifications(): void {
    const existing = this.getAllNotifications();
    
    if (existing.length === 0) {
      console.log('📝 Création de notifications de test...');
      
      const testNotifications: Notification[] = [
        {
          id: `test-success-${Date.now()}`,
          type: 'success',
          priority: 'normal',
          title: '✅ Analyse terminée',
          message: 'La vidéo factory_20260515.mp4 a été analysée avec succès - 285 détections trouvées',
          timestamp: new Date(Date.now() - 5 * 60 * 1000),
          read: false,
          isNew: false,
          link: '/admin/videos'
        },
        {
          id: `test-warning-trs-${Date.now()}`,
          type: 'warning',
          priority: 'high',
          title: '⚠️ TRS Critique',
          message: 'Le TRS de la ligne Assembly A est tombé à 68% (objectif: 85%)',
          timestamp: new Date(Date.now() - 10 * 60 * 1000),
          read: false,
          isNew: false,
          link: '/admin/kpi'
        },
        {
          id: `test-error-machine-${Date.now()}`,
          type: 'error',
          priority: 'high',
          title: '❌ Machine arrêtée',
          message: 'Machine #3 en arrêt depuis 15 minutes',
          timestamp: new Date(Date.now() - 15 * 60 * 1000),
          read: false,
          isNew: false,
          link: '/admin/dashboard'
        },
        {
          id: `test-info-rapport-${Date.now()}`,
          type: 'info',
          priority: 'normal',
          title: '📊 Rapport hebdomadaire disponible',
          message: 'Votre rapport de performance hebdomadaire est prêt',
          timestamp: new Date(Date.now() - 30 * 60 * 1000),
          read: false,
          isNew: false,
          link: '/admin/reports'
        },
        {
          id: `test-success-upload-${Date.now()}`,
          type: 'success',
          priority: 'normal',
          title: '📤 Upload réussi',
          message: 'La vidéo temp_pause_20260515.mp4 a été uploadée',
          timestamp: new Date(Date.now() - 45 * 60 * 1000),
          read: true,
          isNew: false,
          link: '/admin/videos'
        }
      ];

      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(testNotifications));
      console.log(`✅ ${testNotifications.length} notifications de test créées`);
      window.dispatchEvent(new CustomEvent('notifications-updated'));
    } else {
      console.log(`📋 ${existing.length} notifications existantes trouvées`);
    }
  }

  // ========================================
  // GETTERS
  // ========================================

  getAllNotifications(): Notification[] {
    const stored = localStorage.getItem(this.STORAGE_KEY);
    if (!stored) return [];
    
    try {
      const notifications = JSON.parse(stored);
      return notifications.map((n: any) => ({
        ...n,
        timestamp: new Date(n.timestamp),
        isNew: n.isNew !== undefined ? n.isNew : false // ✅ Compatibilité anciennes notifications
      }));
    } catch (error) {
      console.error('❌ Erreur lecture notifications:', error);
      return [];
    }
  }

  getUnreadCount(): number {
    return this.getAllNotifications().filter(n => !n.read).length;
  }

  getHighPriorityCount(): number {
    return this.getAllNotifications().filter(n => n.priority === 'high' && !n.read).length;
  }

  getTodayCount(): number {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    return this.getAllNotifications().filter(n => {
      const notifDate = new Date(n.timestamp);
      notifDate.setHours(0, 0, 0, 0);
      return notifDate.getTime() === today.getTime();
    }).length;
  }

  // ========================================
  // CRÉATION DE NOTIFICATIONS
  // ========================================

  private addNotification(notification: Notification): void {
    const notifications = this.getAllNotifications();
    
    const exists = notifications.some(n => n.id === notification.id);
    if (exists) {
      console.log('⏭️ Notification déjà existante, ignorée:', notification.id);
      return;
    }

    notifications.unshift(notification);

    if (notifications.length > this.MAX_NOTIFICATIONS) {
      notifications.splice(this.MAX_NOTIFICATIONS);
    }

    localStorage.setItem(this.STORAGE_KEY, JSON.stringify(notifications));
    console.log('✅ Notification ajoutée:', notification.title);

    window.dispatchEvent(new CustomEvent('notifications-updated'));
  }

  public createNotification(
    type: 'success' | 'warning' | 'error' | 'info',
    title: string,
    message: string,
    priority: 'normal' | 'high' = 'normal',
    link?: string
  ): void {
    this.addNotification({
      id: `manual-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      type,
      priority,
      title,
      message,
      timestamp: new Date(),
      read: false,
      isNew: true, // ✅ Nouvelle notification = isNew true
      link
    });
  }

  // ========================================
  // NOTIFICATIONS SPÉCIFIQUES
  // ========================================

  notifyAnalysisComplete(videoId: string, filename: string, detections: number): void {
    const id = `analysis-complete-${videoId}`;
    
    this.addNotification({
      id,
      type: 'success',
      priority: 'normal',
      title: '✅ Analyse terminée',
      message: `${filename} : ${detections} détection(s) trouvée(s)`,
      timestamp: new Date(),
      read: false,
      isNew: true, // ✅ Nouvelle
      videoId,
      link: `/admin/videos/${videoId}`
    });
  }

  notifyVideoAnalyzed(videoId: string, filename: string): void {
    const id = `analysis-complete-${videoId}`;
    
    this.addNotification({
      id,
      type: 'success',
      priority: 'normal',
      title: '✅ Analyse terminée',
      message: `${filename} a été analysée avec succès`,
      timestamp: new Date(),
      read: false,
      isNew: true, // ✅ Nouvelle
      videoId,
      link: `/admin/videos/${videoId}`
    });
  }

  notifyAnalysisError(filename: string, error: string): void {
    const id = `analysis-error-${filename}-${Date.now()}`;
    
    this.addNotification({
      id,
      type: 'error',
      priority: 'high',
      title: '❌ Erreur d\'analyse',
      message: `${filename} : ${error}`,
      timestamp: new Date(),
      read: false,
      isNew: true,
    });
  }

  notifyEmployeeAbsent(videoId: string, count: number): void {
    const id = `employee-absent-${videoId}`;
    
    this.addNotification({
      id,
      type: 'warning',
      priority: 'high',
      title: '⚠️ Employés absents détectés',
      message: `${count} employé(s) absent(s) détecté(s)`,
      timestamp: new Date(),
      read: false,
      isNew: true,
      videoId,
      link: `/admin/videos/${videoId}`
    });
  }

  notifyEmployeeAbsence(videoId: string, count: number): void {
    this.notifyEmployeeAbsent(videoId, count);
  }

  notifyEmployeeInactive(videoId: string, count: number): void {
    const id = `employee-inactive-${videoId}`;
    
    this.addNotification({
      id,
      type: 'warning',
      priority: 'high',
      title: '⚠️ Employés inactifs',
      message: `${count} employé(s) inactif(s) détecté(s)`,
      timestamp: new Date(),
      read: false,
      isNew: true,
      videoId,
      link: `/admin/videos/${videoId}`
    });
  }

  notifyMachineStopped(videoId: string, count: number): void {
    const id = `machine-stopped-${videoId}`;
    
    this.addNotification({
      id,
      type: 'error',
      priority: 'high',
      title: '❌ Machine arrêtée',
      message: `${count} machine(s) arrêtée(s) détectée(s)`,
      timestamp: new Date(),
      read: false,
      isNew: true,
      videoId,
      link: `/admin/videos/${videoId}`
    });
  }

  notifyEmptyTable(videoId: string, count: number): void {
    const id = `empty-table-${videoId}`;
    
    this.addNotification({
      id,
      type: 'info',
      priority: 'normal',
      title: '📦 Tables vides',
      message: `${count} table(s) vide(s) détectée(s)`,
      timestamp: new Date(),
      read: false,
      isNew: true,
      videoId,
      link: `/admin/videos/${videoId}`
    });
  }

  notifyLowProduction(videoId: string, productCount: number): void {
    const id = `low-production-${videoId}`;
    
    this.addNotification({
      id,
      type: 'warning',
      priority: 'normal',
      title: '⚠️ Production faible',
      message: `Seulement ${productCount} produit(s) détecté(s)`,
      timestamp: new Date(),
      read: false,
      isNew: true,
      videoId,
      link: `/admin/videos/${videoId}`
    });
  }

  // ========================================
  // ACTIONS SUR NOTIFICATIONS
  // ========================================

  markAsRead(notificationId: string): void {
    const notifications = this.getAllNotifications();
    const notification = notifications.find(n => n.id === notificationId);
    
    if (notification) {
      notification.read = true;
      notification.isNew = false; // ✅ Plus nouvelle quand lue
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(notifications));
      window.dispatchEvent(new CustomEvent('notifications-updated'));
      console.log('✅ Notification marquée comme lue:', notificationId);
    }
  }

  markAllAsRead(): void {
    const notifications = this.getAllNotifications();
    notifications.forEach(n => {
      n.read = true;
      n.isNew = false; // ✅ Plus nouvelles
    });
    localStorage.setItem(this.STORAGE_KEY, JSON.stringify(notifications));
    window.dispatchEvent(new CustomEvent('notifications-updated'));
    console.log('✅ Toutes les notifications marquées comme lues');
  }

  // ✅ NOUVELLE MÉTHODE : Marquer toutes comme "pas nouvelles" (sans les marquer lues)
  markAllAsOld(): void {
    const notifications = this.getAllNotifications();
    let updated = false;

    notifications.forEach(n => {
      if (n.isNew) {
        n.isNew = false;
        updated = true;
      }
    });

    if (updated) {
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(notifications));
      window.dispatchEvent(new CustomEvent('notifications-updated'));
      console.log('✅ Toutes les notifications marquées comme anciennes');
    }
  }

  deleteNotification(notificationId: string): void {
    let notifications = this.getAllNotifications();
    notifications = notifications.filter(n => n.id !== notificationId);
    localStorage.setItem(this.STORAGE_KEY, JSON.stringify(notifications));
    window.dispatchEvent(new CustomEvent('notifications-updated'));
    console.log('✅ Notification supprimée:', notificationId);
  }

  deleteAllNotifications(): void {
    localStorage.removeItem(this.STORAGE_KEY);
    window.dispatchEvent(new CustomEvent('notifications-updated'));
    console.log('✅ Toutes les notifications supprimées');
  }

  async showBrowserNotification(title: string, body: string): Promise<void> {
    if (!('Notification' in window)) {
      console.warn('⚠️ Notifications navigateur non supportées');
      return;
    }

    if (Notification.permission === 'granted') {
      new Notification(title, {
        body,
        icon: '/favicon.ico',
        badge: '/favicon.ico'
      });
    } else if (Notification.permission !== 'denied') {
      const permission = await Notification.requestPermission();
      if (permission === 'granted') {
        new Notification(title, {
          body,
          icon: '/favicon.ico',
          badge: '/favicon.ico'
        });
      }
    }
  }
}