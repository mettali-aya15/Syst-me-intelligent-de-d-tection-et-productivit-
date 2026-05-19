import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { VideoService } from '../services/video.service';
import { VideoUploadResponse } from '../models/video.model';
import { SettingsService } from '../../../core/services/settings.service';
import { NotificationService } from '../../../core/services/notification.service';

@Component({
  selector: 'app-video-upload',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './video-upload.html',
  styleUrls: ['./video-upload.scss']
})
export class VideoUploadComponent {
  private videoService = inject(VideoService);
  private router = inject(Router);
  private settingsService = inject(SettingsService);
  private notificationService = inject(NotificationService);

  selectedFile: File | null = null;
  modelType: 'objects' | 'employees' | 'both' = 'both';
  confidence: number = 0.3;
  isUploading = false;
  uploadProgress = 0;
  errorMessage = '';
  successMessage = '';
  
  uploadedVideoId: string | null = null;
  isAnalyzing = false;

  constructor() {
    // ✅ Charger les paramètres par défaut au démarrage
    const settings = this.settingsService.getCurrentSettings();
    this.modelType = settings.system.defaultModel;
    this.confidence = settings.system.confidenceThreshold;
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      const file = input.files[0];
      
      const validTypes = ['video/mp4', 'video/avi', 'video/mov', 'video/x-matroska'];
      if (!validTypes.includes(file.type)) {
        this.errorMessage = 'Format de fichier non supporté. Utilisez MP4, AVI, MOV ou MKV.';
        this.selectedFile = null;
        return;
      }

      // ✅ Utiliser la taille max depuis les paramètres
      const settings = this.settingsService.getCurrentSettings();
      const maxSizeMB = settings.system.maxVideoSize;
      const maxSize = maxSizeMB * 1024 * 1024;
      
      if (file.size > maxSize) {
        this.errorMessage = `Fichier trop volumineux. Taille maximale : ${maxSizeMB} MB.`;
        this.selectedFile = null;
        return;
      }

      this.selectedFile = file;
      this.errorMessage = '';
      console.log('✅ Fichier sélectionné:', file.name, `(${(file.size / 1024 / 1024).toFixed(2)} MB)`);
    }
  }

  uploadVideo(): void {
    if (!this.selectedFile) {
      this.errorMessage = 'Veuillez sélectionner un fichier vidéo.';
      return;
    }

    this.isUploading = true;
    this.uploadProgress = 0;
    this.errorMessage = '';
    this.successMessage = '';
    this.uploadedVideoId = null;

    this.videoService.uploadVideo({
      file: this.selectedFile,
      model_type: this.modelType,
      confidence: this.confidence
    }).subscribe({
      next: (response) => {
        if (typeof response === 'number') {
          this.uploadProgress = response;
          console.log(`📊 Progression: ${response}%`);
        } else {
          console.log('✅ Upload réussi:', response);
          this.successMessage = `Vidéo "${response.filename}" uploadée avec succès !`;
          this.isUploading = false;
          
          this.uploadedVideoId = response.video_id;

          // ✅ NOUVEAU : Analyse automatique si activée
          const settings = this.settingsService.getCurrentSettings();
          if (settings.system.autoAnalysis) {
            console.log('🤖 Analyse automatique activée - Démarrage...');
            this.analyzeVideo();
          }
        }
      },
      error: (error) => {
        console.error('❌ Erreur upload:', error);
        this.errorMessage = error.error?.detail || 'Erreur lors de l\'upload de la vidéo.';
        this.isUploading = false;
        this.uploadProgress = 0;
        
        // ✅ Notification d'erreur
        this.notificationService.notifyAnalysisError(
          this.selectedFile?.name || 'Fichier inconnu',
          this.errorMessage
        );
      }
    });
  }

  analyzeVideo(): void {
    if (!this.uploadedVideoId) {
      this.errorMessage = 'Aucune vidéo à analyser.';
      return;
    }

    console.log('🎬 Démarrage analyse pour:', this.uploadedVideoId);
    this.isAnalyzing = true;
    this.errorMessage = '';

    this.videoService.analyzeVideo(this.uploadedVideoId).subscribe({
      next: (response: any) => {
        console.log('✅ Analyse démarrée:', response);
        this.isAnalyzing = false;
        
        // Rediriger vers la page de détail
        this.router.navigate(['/admin/videos', this.uploadedVideoId]);
      },
      error: (err: any) => {
        console.error('❌ Erreur analyse:', err);
        this.errorMessage = 'Erreur lors du démarrage de l\'analyse';
        this.isAnalyzing = false;
        
        // ✅ Notification d'erreur
        this.notificationService.notifyAnalysisError(
          this.selectedFile?.name || 'Fichier inconnu',
          err.error?.detail || 'Erreur inconnue'
        );
      }
    });
  }

  resetForm(): void {
    this.selectedFile = null;
    
    // ✅ Recharger les paramètres par défaut
    const settings = this.settingsService.getCurrentSettings();
    this.modelType = settings.system.defaultModel;
    this.confidence = settings.system.confidenceThreshold;
    
    this.uploadProgress = 0;
    this.errorMessage = '';
    this.successMessage = '';
    this.uploadedVideoId = null;
    this.isAnalyzing = false;
    
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    if (fileInput) {
      fileInput.value = '';
    }
  }
}