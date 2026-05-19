import { Injectable } from '@angular/core';

export interface NotificationSettings {
  machineStop: boolean;
  employeeInactive: boolean;
  analysisComplete: boolean;
  analysisError: boolean;
  soundEnabled: boolean;
}

export interface UserSettings {
  theme: 'light' | 'dark' | 'auto';
  language: 'fr' | 'en' | 'ar';
  emailAlerts: boolean;
}

export interface SystemSettings {
  autoAnalysis: boolean;
  confidenceThreshold: number;
  maxVideoSize: number;
  defaultModel: 'objects' | 'employees' | 'both';
}

export interface AppSettings {
  notifications: NotificationSettings;
  user: UserSettings;
  system: SystemSettings;
}

@Injectable({
  providedIn: 'root'
})
export class SettingsService {
  private readonly STORAGE_KEY = 'camia_settings';
  private styleElement: HTMLStyleElement | null = null;

  private defaultSettings: AppSettings = {
    notifications: {
      machineStop: true,
      employeeInactive: true,
      analysisComplete: true,
      analysisError: true,
      soundEnabled: true
    },
    user: {
      theme: 'light',
      language: 'fr',
      emailAlerts: false
    },
    system: {
      autoAnalysis: false,
      confidenceThreshold: 0.5,
      maxVideoSize: 500,
      defaultModel: 'both'
    }
  };

  constructor() {
    const settings = this.getCurrentSettings();
    this.applyTheme(settings.user.theme);
  }

  getCurrentSettings(): AppSettings {
    const stored = localStorage.getItem(this.STORAGE_KEY);
    if (stored) {
      try {
        return JSON.parse(stored);
      } catch (e) {
        console.error('Error parsing settings:', e);
        return this.defaultSettings;
      }
    }
    return this.defaultSettings;
  }

  saveSettings(settings: AppSettings): void {
    localStorage.setItem(this.STORAGE_KEY, JSON.stringify(settings));
    console.log('✅ Settings saved');
    this.applyTheme(settings.user.theme);
  }

  resetSettings(): void {
    localStorage.removeItem(this.STORAGE_KEY);
    this.applyTheme(this.defaultSettings.user.theme);
    console.log('🔄 Settings reset');
  }

  applyTheme(theme: 'light' | 'dark' | 'auto'): void {
    console.log('🎨 Applying theme:', theme);

    // Déterminer le thème effectif
    let effectiveTheme: 'light' | 'dark'; // ✅ TYPAGE EXPLICITE
    if (theme === 'auto') {
      effectiveTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    } else {
      effectiveTheme = theme;
    }

    console.log('  → Effective theme:', effectiveTheme);

    // Supprimer l'ancien style si existe
    if (this.styleElement) {
      this.styleElement.remove();
    }

    // Créer un nouveau style element
    this.styleElement = document.createElement('style');
    this.styleElement.id = 'dynamic-theme';
    
    // Injecter le CSS directement
    this.styleElement.textContent = this.getThemeCSS(effectiveTheme);
    
    // Ajouter au head
    document.head.appendChild(this.styleElement);

    // Mettre à jour les attributs
    document.documentElement.setAttribute('data-theme', effectiveTheme);
    document.body.className = `${effectiveTheme}-theme`;

    console.log('  ✅ Theme CSS injected');
    console.log('  ✅ HTML data-theme:', document.documentElement.getAttribute('data-theme'));
    console.log('  ✅ Body class:', document.body.className);
  }

  private getThemeCSS(theme: 'light' | 'dark'): string {
  if (theme === 'dark') {
    return `
      /* ========================================
         THÈME SOMBRE UNIQUEMENT
         ======================================== */
      
      /* Fond principal */
      body {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%) !important;
        color: #F1F5F9 !important;
      }

      /* Cards et conteneurs */
      .video-banner,
      .upload-banner,
      .stat-card,
      .detections-summary,
      .chart-box,
      .recent-analyses,
      .metadata-section,
      .detection-card,
      .analysis-item,
      .time-card,
      .kpi-card,
      .gauge-card,
      .projection-banner,
      .notification-card,
      .employee-card,
      .settings-section,
      .page-header,
      .risk-card,
      .chart-container {
        background: rgba(30, 41, 59, 0.8) !important;
        border: 1px solid rgba(148, 163, 184, 0.2) !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5) !important;
      }

      /* Textes principaux */
      h1, h2, h3, h4, h5, h6,
      .stat-value,
      .detection-value,
      .time-value,
      .projection-value,
      .card-value,
      .analysis-name,
      .total-value,
      .notif-title,
      .banner-title,
      .section-title,
      strong, b {
        color: #F1F5F9 !important;
        text-shadow: none !important;
      }

      /* Textes secondaires */
      p, span:not(.badge):not(.btn),
      label,
      .stat-label,
      .detection-label,
      .time-label,
      .projection-label,
      .card-label,
      .analysis-date,
      .meta-item,
      .notif-message,
      .banner-label,
      .setting-info p {
        color: #CBD5E1 !important;
      }

      /* Textes mutés */
      .total-unit,
      small,
      .chart-info,
      .projection-period,
      .confidence-label,
      .brand-tagline,
      .user-role {
        color: #94A3B8 !important;
      }

      /* Navbar */
      .admin-navbar {
        background: rgba(15, 23, 42, 0.95) !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4) !important;
        border-bottom: 1px solid rgba(148, 163, 184, 0.2) !important;
      }

      .nav-link {
        color: #94A3B8 !important;
      }

      .nav-link:hover {
        color: #F1F5F9 !important;
        background: rgba(30, 41, 59, 0.8) !important;
      }

      .nav-link.active {
        background: #60A5FA !important;
        color: white !important;
      }

      .brand-name {
        color: #F1F5F9 !important;
      }

      .user-name {
        color: #F1F5F9 !important;
      }

      .user-profile {
        background: #1e293b !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
      }

      .user-profile:hover {
        background: rgba(30, 41, 59, 0.8) !important;
        border-color: #60A5FA !important;
      }

      .btn-logout {
        background: #1e293b !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: #94A3B8 !important;
      }

      /* Formulaires */
      input[type="text"],
      input[type="email"],
      input[type="password"],
      input[type="number"],
      input[type="date"],
      select,
      textarea,
      .setting-select,
      .setting-input {
        background: rgba(30, 41, 59, 0.8) !important;
        color: #F1F5F9 !important;
        border: 1px solid rgba(148, 163, 184, 0.2) !important;
      }

      input::placeholder,
      textarea::placeholder {
        color: #94A3B8 !important;
      }

      select option {
        background: #0f172a !important;
        color: #F1F5F9 !important;
      }

      /* Boutons secondaires */
      .btn-secondary,
      .action-btn,
      .btn-view-all {
        background: rgba(30, 41, 59, 0.8) !important;
        color: #F1F5F9 !important;
        border: 1px solid rgba(148, 163, 184, 0.2) !important;
      }

      .btn-secondary:hover,
      .action-btn:hover {
        background: rgba(96, 165, 250, 0.15) !important;
        color: #60A5FA !important;
        border-color: #60A5FA !important;
      }

      /* Settings */
      .setting-item {
        background: rgba(30, 41, 59, 0.8) !important;
        border: 1px solid rgba(148, 163, 184, 0.2) !important;
      }

      .setting-item:hover {
        background: #1e293b !important;
        border-color: #60A5FA !important;
      }

      .toggle-slider {
        background: rgba(255, 255, 255, 0.1) !important;
      }

      .header-subtitle {
        color: #CBD5E1 !important;
      }

      .unsaved-changes {
        background: rgba(245, 158, 11, 0.2) !important;
        color: #FBBF24 !important;
      }

      /* Loading */
      .loading-overlay {
        background: rgba(15, 23, 42, 0.95) !important;
      }

      .spinner {
        border-color: rgba(255, 255, 255, 0.1) !important;
        border-top-color: #60A5FA !important;
      }

      /* Scrollbar */
      ::-webkit-scrollbar-track {
        background: #0f172a !important;
      }

      ::-webkit-scrollbar-thumb {
        background: rgba(148, 163, 184, 0.2) !important;
      }

      ::-webkit-scrollbar-thumb:hover {
        background: #94A3B8 !important;
      }
    `;
  } else {
    // ✅ MODE CLAIR = AUCUN CSS = GARDE VOS STYLES EXISTANTS
    return `
      /* MODE CLAIR - Aucune modification, garde vos styles existants */
    `;
  }
}

  applyLanguage(lang: 'fr' | 'en' | 'ar'): void {
  document.documentElement.lang = lang;
  if (lang === 'ar') {
    document.documentElement.dir = 'rtl';
  } else {
    document.documentElement.dir = 'ltr';
  }
  console.log('🌍 Language applied:', lang);
}
}