import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

interface Translations {
  [key: string]: {
    [lang: string]: string;
  };
}

@Injectable({
  providedIn: 'root'
})
export class TranslationService {
  private currentLanguage: 'fr' | 'en' | 'ar' = 'fr';
  private languageChange$ = new BehaviorSubject<'fr' | 'en' | 'ar'>('fr');

  private translations: Translations = {
    // Common
    'common.back': { fr: 'Retour', en: 'Back', ar: 'رجوع' },
    'common.error': { fr: 'Erreur', en: 'Error', ar: 'خطأ' },
    'common.success': { fr: 'Succès', en: 'Success', ar: 'نجح' },
    'common.loading': { fr: 'Chargement...', en: 'Loading...', ar: 'جاري التحميل...' },
    'common.save': { fr: 'Enregistrer', en: 'Save', ar: 'حفظ' },
    'common.cancel': { fr: 'Annuler', en: 'Cancel', ar: 'إلغاء' },
    'common.delete': { fr: 'Supprimer', en: 'Delete', ar: 'حذف' },
    'common.edit': { fr: 'Modifier', en: 'Edit', ar: 'تعديل' },
    'common.view': { fr: 'Voir', en: 'View', ar: 'عرض' },
    'common.search': { fr: 'Rechercher', en: 'Search', ar: 'بحث' },
    'common.filter': { fr: 'Filtrer', en: 'Filter', ar: 'تصفية' },
    'common.export': { fr: 'Exporter', en: 'Export', ar: 'تصدير' },
    'common.download': { fr: 'Télécharger', en: 'Download', ar: 'تحميل' },
    'common.refresh': { fr: 'Actualiser', en: 'Refresh', ar: 'تحديث' },
    'common.close': { fr: 'Fermer', en: 'Close', ar: 'إغلاق' },

    // Navbar
    'nav.dashboard': { fr: 'Tableau de bord', en: 'Dashboard', ar: 'لوحة القيادة' },
    'nav.videos': { fr: 'Vidéos', en: 'Videos', ar: 'مقاطع الفيديو' },
    'nav.kpi': { fr: 'Indicateurs', en: 'KPI', ar: 'المؤشرات' },
    'nav.employees': { fr: 'Employés', en: 'Employees', ar: 'الموظفون' },
    'nav.notifications': { fr: 'Notifications', en: 'Notifications', ar: 'الإخطارات' },
    'nav.settings': { fr: 'Paramètres', en: 'Settings', ar: 'الإعدادات' },
    'nav.logout': { fr: 'Déconnexion', en: 'Logout', ar: 'تسجيل الخروج' },

    // Dashboard
    'dashboard.welcome': { fr: 'Bienvenue sur CAMIA Factory', en: 'Welcome to CAMIA Factory', ar: 'مرحبًا بك في مصنع CAMIA' },
    'dashboard.total_videos': { fr: 'Vidéos totales', en: 'Total Videos', ar: 'إجمالي مقاطع الفيديو' },
    'dashboard.total_detections': { fr: 'Détections totales', en: 'Total Detections', ar: 'إجمالي الاكتشافات' },
    'dashboard.active_classes': { fr: 'Classes actives', en: 'Active Classes', ar: 'الفئات النشطة' },
    'dashboard.avg_time': { fr: 'Temps moyen', en: 'Avg Time', ar: 'متوسط الوقت' },
    'dashboard.recent_analyses': { fr: 'Analyses récentes', en: 'Recent Analyses', ar: 'التحليلات الأخيرة' },
    'dashboard.view_all': { fr: 'Voir tout', en: 'View All', ar: 'عرض الكل' },
    'dashboard.upload_video': { fr: 'Télécharger une vidéo', en: 'Upload Video', ar: 'رفع فيديو' },
    'dashboard.products': { fr: 'Produits', en: 'Products', ar: 'منتجات' },
    'dashboard.employees': { fr: 'Employés', en: 'Employees', ar: 'موظفون' },
    'dashboard.machines': { fr: 'Machines', en: 'Machines', ar: 'آلات' },
    'dashboard.detections': { fr: 'Détections', en: 'Detections', ar: 'الاكتشافات' },
    'dashboard.video_analyzed': { fr: 'Vidéo analysée', en: 'Analyzed Video', ar: 'فيديو محلل' },
    'dashboard.uploaded_on': { fr: 'Uploadée le', en: 'Uploaded on', ar: 'تم الرفع في' },
    'dashboard.view_video': { fr: 'Voir la vidéo', en: 'View Video', ar: 'عرض الفيديو' },
    'dashboard.no_video': { fr: 'Aucune vidéo analysée', en: 'No analyzed video', ar: 'لا يوجد فيديو محلل' },
    'dashboard.upload_first': { fr: 'Uploadez votre première vidéo pour commencer l\'analyse', en: 'Upload your first video to start analysis', ar: 'قم برفع أول فيديو لبدء التحليل' },
    'dashboard.uploading': { fr: 'Upload en cours', en: 'Uploading', ar: 'جاري الرفع' },
    'dashboard.upload_success': { fr: 'Vidéo uploadée avec succès ! Analyse en cours...', en: 'Video uploaded successfully!', ar: 'تم رفع الفيديو بنجاح!' },
    'dashboard.videos_7d': { fr: 'Vidéos (7j)', en: 'Videos (7d)', ar: 'مقاطع الفيديو (7 أيام)' },
    'dashboard.detections_7d': { fr: 'Détections (7j)', en: 'Detections (7d)', ar: 'الاكتشافات (7 أيام)' },
    'dashboard.detected_classes': { fr: 'Classes détectées', en: 'Detected Classes', ar: 'الفئات المكتشفة' },
    'dashboard.detected_classes_video': { fr: 'Classes Détectées dans la Vidéo', en: 'Detected Classes in Video', ar: 'الفئات المكتشفة في الفيديو' },
    'dashboard.total': { fr: 'Total', en: 'Total', ar: 'المجموع' },
    'dashboard.no_detections': { fr: 'Aucune détection', en: 'No detections', ar: 'لا توجد اكتشافات' },
    'dashboard.distribution': { fr: 'Répartition des Détections', en: 'Detection Distribution', ar: 'توزيع الاكتشافات' },
    'dashboard.class_distribution': { fr: 'Distribution par classe', en: 'Distribution by class', ar: 'التوزيع حسب الفئة' },
    'dashboard.analysis_history': { fr: 'Historique des Analyses', en: 'Analysis History', ar: 'تاريخ التحليلات' },
    'dashboard.last_7_days': { fr: '7 derniers jours', en: 'Last 7 days', ar: 'آخر 7 أيام' },
    'dashboard.total_videos_7d': { fr: 'Total vidéos (7j)', en: 'Total videos (7d)', ar: 'إجمالي مقاطع الفيديو' },
    'dashboard.total_detections_7d': { fr: 'Total détections (7j)', en: 'Total detections (7d)', ar: 'إجمالي الاكتشافات' },
    'dashboard.view_all_videos': { fr: 'Voir toutes les vidéos', en: 'View all videos', ar: 'عرض جميع مقاطع الفيديو' },
    'dashboard.no_recent': { fr: 'Aucune analyse récente', en: 'No recent analysis', ar: 'لا توجد تحليلات حديثة' },
    'dashboard.time_info': { fr: 'Informations Temporelles', en: 'Time Information', ar: 'معلومات الوقت' },
    'dashboard.video_upload': { fr: 'Upload Vidéo', en: 'Video Upload', ar: 'رفع الفيديو' },
    'dashboard.analysis_completed': { fr: 'Analyse Terminée', en: 'Analysis Completed', ar: 'اكتمل التحليل' },
    'dashboard.analysis_time': { fr: 'Temps d\'analyse', en: 'Analysis Time', ar: 'وقت التحليل' },
    'dashboard.frames_analyzed': { fr: 'Frames Analysées', en: 'Frames Analyzed', ar: 'الإطارات المحللة' },
    'dashboard.all_videos': { fr: 'Toutes les vidéos', en: 'All videos', ar: 'جميع مقاطع الفيديو' },
    'dashboard.view_kpi': { fr: 'Voir les KPI', en: 'View KPI', ar: 'عرض المؤشرات' },

    // Settings
    'settings.title': { fr: 'Paramètres', en: 'Settings', ar: 'الإعدادات' },
    'settings.subtitle': { fr: 'Configurez votre application', en: 'Configure your application', ar: 'قم بتكوين تطبيقك' },
    'settings.unsaved': { fr: 'Modifications non enregistrées', en: 'Unsaved changes', ar: 'تغييرات غير محفوظة' },
    'settings.notifications': { fr: 'Notifications', en: 'Notifications', ar: 'الإخطارات' },
    'settings.notif_subtitle': { fr: 'Gérez vos alertes', en: 'Manage your alerts', ar: 'إدارة التنبيهات' },
    'settings.machine_stop': { fr: 'Arrêt Machine', en: 'Machine Stop', ar: 'توقف الآلة' },
    'settings.machine_stop_desc': { fr: 'Alerte arrêt machine', en: 'Machine stop alert', ar: 'تنبيه توقف الآلة' },
    'settings.employee_inactive': { fr: 'Employé Inactif', en: 'Inactive Employee', ar: 'موظف غير نشط' },
    'settings.employee_inactive_desc': { fr: 'Détecter inactivité', en: 'Detect inactivity', ar: 'الكشف عن عدم النشاط' },
    'settings.analysis_complete': { fr: 'Analyse Terminée', en: 'Analysis Complete', ar: 'اكتمل التحليل' },
    'settings.analysis_complete_desc': { fr: 'Notif fin analyse', en: 'Analysis complete notification', ar: 'إشعار اكتمال التحليل' },
    'settings.analysis_error': { fr: 'Erreur d\'Analyse', en: 'Analysis Error', ar: 'خطأ في التحليل' },
    'settings.analysis_error_desc': { fr: 'Alerte erreur', en: 'Error alert', ar: 'تنبيه خطأ' },
    'settings.sound_enabled': { fr: 'Sons Activés', en: 'Sounds Enabled', ar: 'تمكين الأصوات' },
    'settings.sound_desc': { fr: 'Jouer un son', en: 'Play sound', ar: 'تشغيل الصوت' },
    'settings.test_notif': { fr: 'Tester', en: 'Test', ar: 'اختبار' },
    'settings.user_preferences': { fr: 'Préférences Utilisateur', en: 'User Preferences', ar: 'تفضيلات المستخدم' },
    'settings.user_subtitle': { fr: 'Personnalisez', en: 'Customize', ar: 'قم بتخصيص' },
    'settings.theme': { fr: 'Thème', en: 'Theme', ar: 'السمة' },
    'settings.theme_desc': { fr: 'Choisir le thème', en: 'Choose theme', ar: 'اختر السمة' },
    'settings.light': { fr: 'Clair', en: 'Light', ar: 'فاتح' },
    'settings.dark': { fr: 'Sombre', en: 'Dark', ar: 'داكن' },
    'settings.auto': { fr: 'Automatique', en: 'Auto', ar: 'تلقائي' },
    'settings.language': { fr: 'Langue', en: 'Language', ar: 'اللغة' },
    'settings.language_desc': { fr: 'Langue interface', en: 'Interface language', ar: 'لغة الواجهة' },
    'settings.email_alerts': { fr: 'Alertes Email', en: 'Email Alerts', ar: 'تنبيهات البريد' },
    'settings.email_alerts_desc': { fr: 'Notifications email', en: 'Email notifications', ar: 'إشعارات البريد' },
    'settings.system': { fr: 'Système', en: 'System', ar: 'النظام' },
    'settings.system_subtitle': { fr: 'Configuration avancée', en: 'Advanced config', ar: 'التكوين المتقدم' },
    'settings.auto_analysis': { fr: 'Analyse Auto', en: 'Auto Analysis', ar: 'تحليل تلقائي' },
    'settings.auto_analysis_desc': { fr: 'Lancer auto', en: 'Auto start', ar: 'بدء تلقائي' },
    'settings.confidence': { fr: 'Seuil Confiance', en: 'Confidence Threshold', ar: 'عتبة الثقة' },
    'settings.confidence_desc': { fr: 'Niveau minimum', en: 'Minimum level', ar: 'الحد الأدنى' },
    'settings.max_size': { fr: 'Taille Max', en: 'Max Size', ar: 'الحجم الأقصى' },
    'settings.max_size_desc': { fr: 'Taille max MB', en: 'Max size MB', ar: 'الحجم بالميجابايت' },
    'settings.default_model': { fr: 'Modèle Défaut', en: 'Default Model', ar: 'النموذج الافتراضي' },
    'settings.default_model_desc': { fr: 'Modèle à utiliser', en: 'Model to use', ar: 'النموذج المراد استخدامه' },
    'settings.objects_only': { fr: 'Objets uniquement', en: 'Objects only', ar: 'الأشياء فقط' },
    'settings.employees_only': { fr: 'Employés uniquement', en: 'Employees only', ar: 'الموظفون فقط' },
    'settings.both_models': { fr: 'Les deux', en: 'Both', ar: 'كلاهما' },
    'settings.save': { fr: 'Enregistrer', en: 'Save', ar: 'حفظ' },
    'settings.reset': { fr: 'Réinitialiser', en: 'Reset', ar: 'إعادة تعيين' },
    'settings.saved_success': { fr: 'Enregistré', en: 'Saved', ar: 'تم الحفظ' },
    'settings.language_changed': { fr: 'Langue modifiée', en: 'Language changed', ar: 'تم تغيير اللغة' },

    // KPI
    'kpi.title': { fr: 'Indicateurs', en: 'KPI', ar: 'المؤشرات' },
    'kpi.export_pdf': { fr: 'Export PDF', en: 'Export PDF', ar: 'تصدير PDF' },
    'kpi.export_excel': { fr: 'Export Excel', en: 'Export Excel', ar: 'تصدير Excel' },

    // Employees
    'employees.title': { fr: 'Employés', en: 'Employees', ar: 'الموظفون' },
    'employees.total': { fr: 'Total', en: 'Total', ar: 'المجموع' },
    'employees.active': { fr: 'Actifs', en: 'Active', ar: 'نشط' },
    'employees.inactive': { fr: 'Inactifs', en: 'Inactive', ar: 'غير نشط' },

    // Notifications
    'notifications.title': { fr: 'Notifications', en: 'Notifications', ar: 'الإخطارات' },
    'notifications.mark_read': { fr: 'Marquer lu', en: 'Mark read', ar: 'وضع علامة' },
    'notifications.clear_all': { fr: 'Tout effacer', en: 'Clear all', ar: 'مسح الكل' },
  };

  constructor() {
    const saved = localStorage.getItem('app_language');
    if (saved && (saved === 'fr' || saved === 'en' || saved === 'ar')) {
      this.currentLanguage = saved as 'fr' | 'en' | 'ar';
      this.languageChange$.next(this.currentLanguage);
    }
  }

  onLanguageChange(): Observable<'fr' | 'en' | 'ar'> {
    return this.languageChange$.asObservable();
  }

  getCurrentLanguage(): 'fr' | 'en' | 'ar' {
    return this.currentLanguage;
  }

  setLanguage(lang: 'fr' | 'en' | 'ar'): void {
    this.currentLanguage = lang;
    localStorage.setItem('app_language', lang);
    this.languageChange$.next(lang);
    
    document.documentElement.lang = lang;
    document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr';
    
    console.log('🌍 Language changed to:', lang);
  }

  translate(key: string): string {
    const translation = this.translations[key];
    if (!translation) {
      console.warn(`⚠️ Missing translation: ${key}`);
      return key;
    }
    return translation[this.currentLanguage] || translation['fr'] || key;
  }

  addTranslations(newTranslations: Translations): void {
    this.translations = { ...this.translations, ...newTranslations };
  }
}