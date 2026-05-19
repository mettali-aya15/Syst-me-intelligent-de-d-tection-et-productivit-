import { Injectable, inject } from '@angular/core';
import { BehaviorSubject } from 'rxjs';
import { NotificationService } from './notification.service';

@Injectable({
  providedIn: 'root'
})
export class WebSocketService {
  private notificationService = inject(NotificationService);
  
  private socket: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 3000;
  private reconnectTimeout: any = null;

  private connectedSubject = new BehaviorSubject<boolean>(false);
  public connected$ = this.connectedSubject.asObservable();

  private readonly WS_URL = 'ws://localhost:8000/api/v1/ws';

  connect(): void {
    if (this.socket?.readyState === WebSocket.OPEN) {
      console.log('⚠️ WebSocket déjà connecté');
      return;
    }

    console.log('🔌 Connexion WebSocket...', this.WS_URL);

    try {
      this.socket = new WebSocket(this.WS_URL);

      this.socket.onopen = () => {
        console.log('✅ WebSocket connecté');
        this.connectedSubject.next(true);
        this.reconnectAttempts = 0;
        
        // Test de connexion
        this.send({ type: 'ping', data: 'Connection test' });
      };

      this.socket.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          console.log('📨 Message WebSocket reçu:', message);
          this.handleMessage(message);
        } catch (error) {
          console.error('❌ Erreur parsing message WebSocket:', error);
        }
      };

      this.socket.onerror = (error) => {
        console.error('❌ Erreur WebSocket:', error);
        this.connectedSubject.next(false);
      };

      this.socket.onclose = (event) => {
        console.log('🔌 WebSocket déconnecté', event.code, event.reason);
        this.connectedSubject.next(false);
        this.socket = null;
        
        // Tentative de reconnexion
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts++;
          console.log(`🔄 Tentative de reconnexion ${this.reconnectAttempts}/${this.maxReconnectAttempts} dans ${this.reconnectDelay}ms...`);
          
          this.reconnectTimeout = setTimeout(() => {
            this.connect();
          }, this.reconnectDelay);
        } else {
          console.error('❌ Nombre maximum de tentatives de reconnexion atteint');
        }
      };

    } catch (error) {
      console.error('❌ Erreur création WebSocket:', error);
      this.connectedSubject.next(false);
    }
  }

  private handleMessage(message: any): void {
    const { type, data } = message;

    switch (type) {
      case 'analysis_complete':
        this.handleAnalysisComplete(data);
        break;

      case 'analysis_error':
        this.handleAnalysisError(data);
        break;

      case 'alert':
        this.handleAlert(data);
        break;

      case 'echo':
        console.log('🔔 Echo reçu:', data);
        break;

      default:
        console.log('ℹ️ Type de message non géré:', type);
    }
  }

  private handleAnalysisComplete(data: any): void {
    console.log('✅ Analyse terminée - Traitement des notifications...');
    
    const { video_id, filename, alerts } = data;

    // ✅ Notification principale : analyse terminée
    this.notificationService.notifyVideoAnalyzed(video_id, filename);

    // ✅ Traiter les alertes SI ELLES EXISTENT
    if (alerts) {
      this.processAlerts(video_id, alerts);
    }

    // ✅ Émettre un événement pour rafraîchir l'UI
    window.dispatchEvent(new CustomEvent('video-analyzed', { 
      detail: { videoId: video_id, filename, alerts } 
    }));
  }

  private handleAnalysisError(data: any): void {
    console.error('❌ Erreur d\'analyse:', data);
    
    const { filename, error } = data;
    this.notificationService.notifyAnalysisError(filename, error);

    // ✅ Émettre un événement pour rafraîchir l'UI
    window.dispatchEvent(new CustomEvent('video-error', { 
      detail: { filename, error } 
    }));
  }

  private handleAlert(data: any): void {
    console.log('⚠️ Alerte reçue:', data);
    
    const { video_id, alerts } = data;
    if (alerts) {
      this.processAlerts(video_id, alerts);
    }
  }

  private processAlerts(videoId: string, alerts: any): void {
    console.log('🔍 Traitement des alertes:', alerts);

    // ✅ MACHINE ARRÊTÉE
    if (alerts.machines_stopped && alerts.machines_stopped > 0) {
      this.notificationService.notifyMachineStopped(videoId, alerts.machines_stopped);
    }

    // ✅ EMPLOYÉS INACTIFS
    if (alerts.employees_inactive && alerts.employees_inactive > 0) {
      this.notificationService.notifyEmployeeInactive(videoId, alerts.employees_inactive);
    }

    // ✅ TABLES VIDES
    if (alerts.tables_empty && alerts.tables_empty > 0) {
      this.notificationService.notifyEmptyTable(videoId, alerts.tables_empty);
    }

    // ✅ EMPLOYÉS ABSENTS
    if (alerts.employees_absent && alerts.employees_absent > 0) {
      this.notificationService.notifyEmployeeAbsence(videoId, alerts.employees_absent);
    }
  }

  send(message: any): void {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(message));
      console.log('📤 Message envoyé:', message);
    } else {
      console.warn('⚠️ WebSocket non connecté, impossible d\'envoyer le message');
    }
  }

  disconnect(): void {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    if (this.socket) {
      console.log('🔌 Déconnexion WebSocket...');
      this.socket.close();
      this.socket = null;
    }

    this.connectedSubject.next(false);
    this.reconnectAttempts = 0;
  }

  isConnected(): boolean {
    return this.socket?.readyState === WebSocket.OPEN;
  }
}