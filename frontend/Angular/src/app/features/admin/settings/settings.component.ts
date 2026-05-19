import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { SettingsService, AppSettings, NotificationSettings, UserSettings, SystemSettings } from '../../../core/services/settings.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { TranslationService } from '../../../core/services/translation.service';

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [CommonModule, FormsModule, TranslatePipe],
  templateUrl: './settings.component.html',
  styleUrls: ['./settings.component.scss']
})
export class SettingsComponent implements OnInit {
  private router = inject(Router);
  private settingsService = inject(SettingsService);
  private translationService = inject(TranslationService);

  notificationSettings!: NotificationSettings;
  userSettings!: UserSettings;
  systemSettings!: SystemSettings;
  private initialSettings!: AppSettings;

  // ✅ Audio pour le son de notification
  private notificationAudio: HTMLAudioElement | null = null;

  ngOnInit(): void {
    const current = this.settingsService.getCurrentSettings();
    this.notificationSettings = { ...current.notifications };
    this.userSettings = { ...current.user };
    this.systemSettings = { ...current.system };
    this.initialSettings = JSON.parse(JSON.stringify(current));

    // ✅ Précharger le son de notification
    this.loadNotificationSound();

    // ✅ Appliquer le thème au démarrage
    this.applyThemeToDocument(this.userSettings.theme);
  }

  goBack(): void {
    this.router.navigate(['/admin/dashboard']);
  }

  // ✅ GESTION DU THÈME FONCTIONNELLE
  onThemeChange(theme: 'light' | 'dark' | 'auto'): void {
    console.log('🎨 Theme changed to:', theme);
    
    // Appliquer le thème immédiatement
    this.applyThemeToDocument(theme);
    
    this.showToast(this.translationService.translate('settings.theme_applied') + `: ${theme}`, 'success');
  }

  private applyThemeToDocument(theme: 'light' | 'dark' | 'auto'): void {
    const htmlElement = document.documentElement;
    
    if (theme === 'auto') {
      // Détecter le thème système
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      htmlElement.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
    } else {
      htmlElement.setAttribute('data-theme', theme);
    }

    // Ajouter/retirer la classe dark sur le body
    if (theme === 'dark' || (theme === 'auto' && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
      document.body.classList.add('dark-theme');
      document.body.classList.remove('light-theme');
    } else {
      document.body.classList.add('light-theme');
      document.body.classList.remove('dark-theme');
    }

    console.log('✅ Theme applied:', theme);
  }

  onLanguageChange(lang: 'fr' | 'en' | 'ar'): void {
  console.log('🌍 Language changed to:', lang);
  
  // Changer la langue
  this.translationService.setLanguage(lang);
  this.userSettings.language = lang;
  
  // Appliquer immédiatement dans le service des settings
  this.settingsService.applyLanguage(lang);
  
  // Afficher le message de succès
  this.showToast(this.translationService.translate('settings.language_changed'), 'success');
}

  // ✅ CHARGER LE SON DE NOTIFICATION
  private loadNotificationSound(): void {
    try {
      this.notificationAudio = new Audio('assets/sounds/notification.mp3');
      this.notificationAudio.load();
      console.log('✅ Notification sound loaded');
    } catch (error) {
      console.error('❌ Error loading notification sound:', error);
    }
  }

  // ✅ JOUER LE SON DE NOTIFICATION
  private playNotificationSound(): void {
    if (!this.notificationSettings.soundEnabled) {
      console.log('🔇 Sound is disabled');
      return;
    }

    if (!this.notificationAudio) {
      console.warn('⚠️ Notification audio not loaded');
      this.loadNotificationSound();
    }

    try {
      // Reset et jouer
      this.notificationAudio!.currentTime = 0;
      this.notificationAudio!.play()
        .then(() => console.log('🔊 Notification sound played'))
        .catch(err => console.error('❌ Error playing sound:', err));
    } catch (error) {
      console.error('❌ Error playing notification sound:', error);
    }
  }

  // ✅ TEST DE NOTIFICATION (SON UNIQUEMENT)
  async testNotification(): Promise<void> {
    console.log('🔔 Testing notification...');
    
    // Jouer le son si activé
    if (this.notificationSettings.soundEnabled) {
      this.playNotificationSound();
    } else {
      console.log('🔇 Sound notifications are disabled');
    }
    
    this.showToast(this.translationService.translate('settings.test_notif'), 'success');
  }

  async saveSettings(): Promise<void> {
    console.log('💾 Saving settings...');
    
    try {
      const settings: AppSettings = {
        notifications: { ...this.notificationSettings },
        user: { ...this.userSettings },
        system: { ...this.systemSettings }
      };

      this.settingsService.saveSettings(settings);
      this.initialSettings = JSON.parse(JSON.stringify(settings));
      
      // Appliquer le thème sauvegardé
      this.applyThemeToDocument(settings.user.theme);
      
      console.log('✅ Settings saved:', settings);
      this.showToast(this.translationService.translate('settings.saved_success'), 'success');
    } catch (error) {
      console.error('❌ Error saving settings:', error);
      this.showToast(this.translationService.translate('common.error'), 'error');
    }
  }

  resetSettings(): void {
    const confirmMsg = this.translationService.translate('settings.reset_confirm');
    if (confirm(confirmMsg)) {
      console.log('🔄 Resetting settings...');
      this.settingsService.resetSettings();
      
      const defaults = this.settingsService.getCurrentSettings();
      this.notificationSettings = { ...defaults.notifications };
      this.userSettings = { ...defaults.user };
      this.systemSettings = { ...defaults.system };
      this.initialSettings = JSON.parse(JSON.stringify(defaults));
      
      // Appliquer le thème par défaut
      this.applyThemeToDocument(defaults.user.theme);
      
      this.showToast(this.translationService.translate('settings.reset_success'), 'info');
    }
  }

  hasUnsavedChanges(): boolean {
    const current: AppSettings = {
      notifications: { ...this.notificationSettings },
      user: { ...this.userSettings },
      system: { ...this.systemSettings }
    };
    return JSON.stringify(current) !== JSON.stringify(this.initialSettings);
  }

  getConfidenceLabel(val: number): string {
    if (val < 0.3) return this.translationService.translate('settings.very_low');
    if (val < 0.5) return this.translationService.translate('settings.low');
    if (val < 0.7) return this.translationService.translate('settings.medium');
    if (val < 0.9) return this.translationService.translate('settings.high');
    return this.translationService.translate('settings.very_high');
  }

  private showToast(msg: string, type: 'success' | 'error' | 'info' = 'info'): void {
    const toast = document.createElement('div');
    const colors = {
      success: '#10b981',
      error: '#ef4444',
      info: '#3b82f6'
    };
    
    toast.style.cssText = `
      position: fixed;
      top: 100px;
      right: 20px;
      padding: 14px 24px;
      background: ${colors[type]};
      color: white;
      border-radius: 10px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.2);
      font-weight: 600;
      z-index: 10000;
      animation: slideIn 0.3s ease;
    `;
    toast.textContent = msg;
    document.body.appendChild(toast);
    
    setTimeout(() => {
      toast.style.animation = 'slideOut 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 3000);
  }
}