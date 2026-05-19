import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';  // ✅ RouterLink retiré
import { VideoService } from '../services/video.service';
import { interval, Subscription } from 'rxjs';
import { switchMap } from 'rxjs/operators';

@Component({
  selector: 'app-video-detail',
  standalone: true,
  imports: [CommonModule],  // ✅ RouterLink retiré
  templateUrl: './video-detail.html',
  styleUrls: ['./video-detail.scss']
})
export class VideoDetailComponent implements OnInit, OnDestroy {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private videoService = inject(VideoService);

  video: any = null;
  attendanceReport: any = null;
  loading = true;
  error = '';
  
  videoUrl = '';
  
  private pollingSubscription?: Subscription;

  ngOnInit(): void {
    const videoId = this.route.snapshot.paramMap.get('id');
    if (videoId) {
      this.loadVideo(videoId);
    }
  }

  ngOnDestroy(): void {
    if (this.pollingSubscription) {
      this.pollingSubscription.unsubscribe();
    }
  }

  loadVideo(videoId: string): void {
    this.loading = true;
    
    this.videoService.getVideo(videoId).subscribe({
      next: (data: any) => {
        this.video = data;
        this.loading = false;
        
        console.log('📹 VIDEO COMPLETE:', data);
        console.log('🎯 model_type =', data.model_type);
        console.log('🔢 total_detections =', data.total_detections);
        console.log('📦 unique_objects =', data.unique_objects);
        console.log('📁 annotated_path =', data.annotated_path);
        
        if (data.annotated_path) {
          this.videoUrl = `http://localhost:8000/api/v1/videos/${videoId}/stream`;
          console.log('🎥 URL vidéo streaming:', this.videoUrl);
        }
        
        if (data.model_type === 'employees' || data.model_type === 'both') {
          console.log('✅ Chargement du rapport de présence (model_type = ' + data.model_type + ')');
          this.loadAttendance(videoId);
        } else {
          console.log('⏭️ Pas de rapport de présence (model_type = ' + data.model_type + ')');
          this.attendanceReport = null;
        }
        
        if (data.status === 'processing' || data.status === 'analyzing') {
          this.startPolling(videoId);
        } else {
          this.stopPolling();
        }
      },
      error: (err: any) => {
        this.error = 'Erreur lors du chargement de la vidéo';
        this.loading = false;
        console.error('❌ Erreur chargement vidéo:', err);
      }
    });
  }

  loadAttendance(videoId: string): void {
    this.videoService.getAttendance(videoId).subscribe({
      next: (data: any) => {
        this.attendanceReport = data;
        console.log('📊 Rapport de présence chargé:', data);
      },
      error: (err: any) => {
        console.error('❌ Erreur chargement présence:', err);
        this.attendanceReport = null;
      }
    });
  }

  private startPolling(videoId: string): void {
    console.log('🔄 Démarrage du polling automatique...');
    this.stopPolling();
    
    this.pollingSubscription = interval(3000)
      .pipe(switchMap(() => this.videoService.getVideo(videoId)))
      .subscribe({
        next: (data: any) => {
          console.log('🔄 Mise à jour automatique - Status:', data.status);
          this.video = data;
          
          if (data.annotated_path && !this.videoUrl) {
            this.videoUrl = `http://localhost:8000/api/v1/videos/${videoId}/stream`;
          }
          
          if (data.model_type === 'employees' || data.model_type === 'both') {
            this.loadAttendance(videoId);
          } else {
            this.attendanceReport = null;
          }
          
          if (data.status === 'completed' || data.status === 'failed') {
            console.log('✅ Analyse terminée, arrêt du polling');
            this.stopPolling();
          }
        },
        error: (err: any) => {
          console.error('❌ Erreur polling:', err);
          this.stopPolling();
        }
      });
  }

  private stopPolling(): void {
    if (this.pollingSubscription) {
      this.pollingSubscription.unsubscribe();
      this.pollingSubscription = undefined;
      console.log('⏹️ Polling arrêté');
    }
  }

  getStatusClass(status: string): string {
    const statusMap: { [key: string]: string } = {
      'completed': 'status-success',
      'processing': 'status-warning',
      'analyzing': 'status-warning',
      'uploaded': 'status-info',
      'failed': 'status-error',
      'error': 'status-error'
    };
    
    return statusMap[status?.toLowerCase()] || 'status-default';
  }

  getStatusLabel(status: string): string {
    const labelMap: { [key: string]: string } = {
      'completed': '✅ Terminé',
      'processing': '⏳ En cours',
      'analyzing': '🔍 Analyse...',
      'uploaded': '📤 Uploadé',
      'failed': '❌ Erreur',
      'error': '❌ Erreur'
    };
    
    return labelMap[status?.toLowerCase()] || status;
  }

  getModelLabel(modelType: string): string {
    if (!modelType || modelType === 'undefined') {
      return '🎯 Non défini';
    }
    
    const modelMap: { [key: string]: string } = {
      'objects': '📦 Objets',
      'employees': '👥 Employés',
      'both': '🎯 Les deux'
    };
    
    return modelMap[modelType.toLowerCase()] || modelType;
  }

  formatDuration(seconds: number): string {
    if (!seconds || seconds === 0) return '0:00';
    
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  }

  getAttendanceColor(): string {
    if (!this.attendanceReport) return '#6b7280';
    const rate = this.attendanceReport.attendance_rate || 0;
    if (rate >= 80) return '#10b981';
    if (rate >= 50) return '#f59e0b';
    return '#ef4444';
  }

  deleteVideo(): void {
    if (!this.video) return;

    const confirmMessage = `⚠️ ATTENTION ⚠️\n\nÊtes-vous sûr de vouloir supprimer cette vidéo ?\n\n📹 ${this.video.filename}\n\n❌ Action IRRÉVERSIBLE !`;

    if (confirm(confirmMessage)) {
      this.videoService.deleteVideo(this.video._id).subscribe({
        next: () => {
          console.log('✅ Vidéo supprimée');
          alert(`✅ Vidéo "${this.video.filename}" supprimée avec succès !`);
          this.router.navigate(['/admin/videos']);
        },
        error: (err: any) => {
          console.error('❌ Erreur suppression:', err);
          alert('❌ Erreur lors de la suppression');
        }
      });
    }
  }

  goBack(): void {
    this.router.navigate(['/admin/videos']);
  }

  objectKeys = Object.keys;
}