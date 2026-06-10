import { Component, OnInit, AfterViewInit, OnDestroy, inject, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { HttpClient, HttpEventType } from '@angular/common/http';
import { Chart, registerables } from 'chart.js';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { VideoService } from '../../../features/videos/services/video.service';


Chart.register(...registerables);

interface DetectionItem {
  key: string;
  label: string;
  value: number;
  icon: string;
  color: string;
  percentage: string;
}

interface VideoMetadata {
  uploadedAt: string;
  analyzedAt: string;
  duration: string;
  frameCount: number;
  analysisTime: string;
}

interface AnalysisTimeline {
  date: string;
  videosAnalyzed: number;
  totalDetections: number;
}

@Component({
  selector: 'app-admin-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule,TranslatePipe],
  templateUrl: './admin-dashboard.html',
  styleUrls: ['./admin-dashboard.scss']
})
export class AdminDashboardComponent implements OnInit, AfterViewInit, OnDestroy {
  router = inject(Router);
  private http = inject(HttpClient);
  private apiUrl = 'http://localhost:8000/api/v1';
  private videoService = inject(VideoService);
  
  @ViewChild('fileInput') fileInput!: ElementRef<HTMLInputElement>;
  
  private charts: { [key: string]: Chart } = {};
  
  // VIDÉO ACTUELLE
  currentVideo: any = null;
  videoMetadata: VideoMetadata = {
    uploadedAt: '',
    analyzedAt: '',
    duration: '',
    frameCount: 0,
    analysisTime: ''
  };
  
  // DÉTECTIONS BRUTES
  detections: DetectionItem[] = [];
  totalDetections = 0;
  
  // TIMELINE & HISTORIQUE
  analysisTimeline: AnalysisTimeline[] = [];
  recentAnalyses: any[] = [];
  
  // ✅ UPLOAD
  uploadProgress = 0;
  uploadSuccess = false;
  selectedFileName = '';
  
  loading = true;

  ngOnInit(): void {
    this.loadData();
  }

  ngAfterViewInit(): void {
    setTimeout(() => this.initCharts(), 500);
  }

  ngOnDestroy(): void {
    Object.values(this.charts).forEach(chart => chart?.destroy());
  }

  // ==========================================
  // 📤 UPLOAD VIDEO
  // ==========================================
  public triggerFileUpload(): void {
    this.fileInput.nativeElement.click();
  }

  public onFileSelected(event: any): void {
    const file = event.target.files[0];
    
    if (!file) {
      return;
    }

    // Vérifier le type de fichier
    if (!file.type.startsWith('video/')) {
      alert('⚠️ Veuillez sélectionner un fichier vidéo valide');
      return;
    }

    // Vérifier la taille (max 500MB)
    const maxSize = 500 * 1024 * 1024; // 500MB
    if (file.size > maxSize) {
      alert('⚠️ La vidéo est trop grande (max 500MB)');
      return;
    }

    this.selectedFileName = file.name;
    this.uploadVideo(file);
  }

  private uploadVideo(file: File): void {
    const formData = new FormData();
    formData.append('file', file);

    this.uploadProgress = 0;
    this.uploadSuccess = false;

    console.log('📤 Upload démarré:', file.name);

    this.http.post(`${this.apiUrl}/videos/upload`, formData, {
      reportProgress: true,
      observe: 'events'
    }).subscribe({
      next: (event: any) => {
        if (event.type === HttpEventType.UploadProgress) {
          const percentDone = event.total 
            ? Math.round((100 * event.loaded) / event.total) 
            : 0;
          this.uploadProgress = percentDone;
          console.log(`📊 Upload progress: ${percentDone}%`);
        } else if (event.type === HttpEventType.Response) {
          console.log('✅ Upload terminé:', event.body);
          this.uploadProgress = 100;
          
          setTimeout(() => {
            this.uploadSuccess = true;
            this.uploadProgress = 0;
            
            setTimeout(() => {
              this.loadData();
            }, 2000);
          }, 500);
        }
      },
      error: (error) => {
        console.error('❌ Erreur upload:', error);
        this.uploadProgress = 0;
        
        let errorMessage = 'Erreur lors de l\'upload de la vidéo';
        
        if (error.status === 0) {
          errorMessage = 'Impossible de contacter le serveur. Vérifiez que le backend est démarré.';
        } else if (error.error?.detail) {
          errorMessage = error.error.detail;
        }
        
        alert(`❌ ${errorMessage}`);
      }
    });
  }

  // ==========================================
  // 📥 CHARGEMENT DES DONNÉES
  // ==========================================
async loadData(): Promise<void> {
  try {
    this.loading = true;
    
    const videos = await this.http.get<any[]>(`${this.apiUrl}/videos/`).toPromise();
    const completed = videos?.filter(v => v.status === 'completed') || [];
    
    console.log('🎥 Admin Dashboard - Vidéos terminées:', completed.length);
    
    if (completed.length === 0) {
      this.loading = false;
      return;
    }

    // ✅ CHARGER classes_detectees pour toutes les vidéos depuis video_detections
    for (const v of completed) {
      try {
        const det = await this.http.get<any>(
          `http://localhost:8000/api/v1/detections/video/${v._id}`
        ).toPromise();
        v.classes_detectees = det?.classes_detectees || {};
      } catch {
        v.classes_detectees = {};
      }
    }

    this.currentVideo = completed[0];
    const uniqueObjects = completed[0].classes_detectees || {};
    console.log('📊 Détections brutes:', uniqueObjects);

    // 2. MÉTADONNÉES
    this.videoMetadata = {
      uploadedAt: this.formatDateTime(new Date(this.currentVideo.uploaded_at || this.currentVideo.created_at)),
      analyzedAt: this.formatDateTime(new Date(this.currentVideo.created_at)),
      duration: '2min 34s',
      frameCount: this.currentVideo.total_detections || 0,
      analysisTime: '45s'
    };

    // 3. EXTRACTION DES CLASSES
    this.detections = [];
    this.totalDetections = 0;

    const EXCLUDED_NAMES = [
      'seline', 'adem', 'mohamed', 'ali', 'alena', 'amir', 'insaf',
      'ibtihel', 'amelie', 'sami', 'employe', 'porte verte', 'temps',
      'porte_verte', 'temp'
    ];

    Object.keys(uniqueObjects).forEach(key => {
      const value = Number(uniqueObjects[key]) || 0;
      const keyLower = key.toLowerCase();
      const isExcluded = EXCLUDED_NAMES.some(name => keyLower.includes(name));

      if (value > 0 && !isExcluded) {
        this.detections.push({
          key: key,
          label: this.formatLabel(key),
          value: value,
          icon: this.getIcon(key),
          color: this.getColor(key),
          percentage: '0'
        });
        this.totalDetections += value;
      }
    });

    this.detections.forEach(d => {
      d.percentage = this.totalDetections > 0
        ? ((d.value / this.totalDetections) * 100).toFixed(1)
        : '0';
    });

    console.log('📊 Classes extraites (filtrées):', this.detections.map(d => `${d.label}: ${d.value}`));

    // 4. TIMELINE
    this.generateAnalysisTimeline(completed);

    // 5. ANALYSES RÉCENTES
    this.recentAnalyses = completed.slice(0, 5).map(v => ({
      id: v._id,
      filename: v.filename,
      date: this.formatDateTime(new Date(v.created_at)),
      detectionCount: Object.values(v.classes_detectees || {})
        .reduce((sum: number, val: any) => sum + Number(val), 0),
      status: v.status
    }));

    // 6. GRAPHIQUES
    setTimeout(() => this.initCharts(), 200);

    this.loading = false;

  } catch (error) {
    console.error('❌ Erreur loadData:', error);
    this.loading = false;
  }
}
  private generateAnalysisTimeline(videos: any[]): void {
    const last7Days: AnalysisTimeline[] = [];
    
    for (let i = 6; i >= 0; i--) {
      const date = new Date();
      date.setDate(date.getDate() - i);
      const dateStr = date.toISOString().split('T')[0];
      
      const dayVideos = videos.filter(v => {
        const vDate = new Date(v.created_at).toISOString().split('T')[0];
        return vDate === dateStr;
      });
      
      const totalDet = dayVideos.reduce((sum, v) => {
        return sum + Object.values(v.classes_detectees || {}).reduce((a: number, b: any) => a + Number(b), 0);

      }, 0);
      
      last7Days.push({
        date: this.formatShortDate(date),
        videosAnalyzed: dayVideos.length,
        totalDetections: totalDet
      });
    }
    
    this.analysisTimeline = last7Days;
  }

  // ==========================================
  // 📊 GRAPHIQUES
  // ==========================================
  private initCharts(): void {
    this.createDistributionChart();
    this.createTimelineChart();
  }

  private createDistributionChart(): void {
    const canvas = document.getElementById('distributionChart') as HTMLCanvasElement;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    if (this.charts['distribution']) {
      this.charts['distribution'].destroy();
    }
    
    this.charts['distribution'] = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: this.detections.map(d => d.label),
        datasets: [{
          data: this.detections.map(d => d.value),
          backgroundColor: this.detections.map(d => d.color),
          borderWidth: 3,
          borderColor: '#fff',
          hoverOffset: 15
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '70%',
        plugins: {
          legend: { 
            position: 'bottom',
            labels: { 
              padding: 15,
              font: { size: 12, weight: 'bold' },
              usePointStyle: true
            }
          },
          tooltip: {
            backgroundColor: '#fff',
            titleColor: '#0f172a',
            bodyColor: '#64748b',
            borderColor: '#e2e8f0',
            borderWidth: 2,
            padding: 12,
            cornerRadius: 8,
            callbacks: {
              label: (context: any) => {
                const label = context.label || '';
                const value = context.parsed || 0;
                return `${label}: ${value} détections`;
              }
            }
          }
        }
      }
    });
  }

  private createTimelineChart(): void {
    const canvas = document.getElementById('timelineChart') as HTMLCanvasElement;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    if (this.charts['timeline']) {
      this.charts['timeline'].destroy();
    }
    
    this.charts['timeline'] = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: this.analysisTimeline.map(t => t.date),
        datasets: [
          {
            label: 'Vidéos analysées',
            data: this.analysisTimeline.map(t => t.videosAnalyzed),
            backgroundColor: '#6366f1',
            borderRadius: 8,
            barThickness: 30
          },
          {
            label: 'Total détections',
            data: this.analysisTimeline.map(t => t.totalDetections),
            backgroundColor: '#10b981',
            borderRadius: 8,
            barThickness: 30
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'top',
            labels: { 
              padding: 15,
              font: { size: 11, weight: 'bold' },
              usePointStyle: true
            }
          },
          tooltip: {
            backgroundColor: '#fff',
            titleColor: '#0f172a',
            bodyColor: '#64748b',
            borderColor: '#e2e8f0',
            borderWidth: 2,
            padding: 12,
            cornerRadius: 8
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            grid: { color: '#f1f5f9' },
            ticks: { 
              font: { size: 11 },
              stepSize: 1
            }
          },
          x: { 
            grid: { display: false },
            ticks: { font: { size: 11 } }
          }
        }
      }
    });
  }

  // ==========================================
  // 🛠 UTILITAIRES
  // ==========================================
  private formatDateTime(date: Date): string {
    return date.toLocaleString('fr-FR', {
      day: '2-digit', 
      month: '2-digit', 
      year: 'numeric',
      hour: '2-digit', 
      minute: '2-digit'
    });
  }

  private formatShortDate(date: Date): string {
    return date.toLocaleDateString('fr-FR', { 
      day: '2-digit', 
      month: 'short' 
    });
  }

  public formatLabel(key: string): string {
    const labels: { [key: string]: string } = {
      'machine': 'Machines',
      'machine arrêtée': 'Machines Arrêtées',
      'employé': 'Employés',
      'employé actif': 'Employés Actifs',
      'employé inactif': 'Employés Inactifs',
      'client': 'Clients',
      'produit': 'Produits',
      'tables': 'Tables',
      'tables_vides': 'Tables Vides'
    };
    return labels[key] || key.replace('_', ' ').replace(/^\w/, c => c.toUpperCase());
  }

  public getIcon(key: string): string {
    const icons: { [key: string]: string } = {
      'machine': 'fas fa-cog',
      'machine arrêtée': 'fas fa-stop-circle',
      'employé': 'fas fa-user',
      'employé actif': 'fas fa-user-check',
      'employé inactif': 'fas fa-user-times',
      'client': 'fas fa-user-tie',
      'produit': 'fas fa-box',
      'tables': 'fas fa-table',
      'tables_vides': 'fas fa-inbox'
    };
    return icons[key] || 'fas fa-circle';
  }

  public getColor(key: string): string {
    const colors: { [key: string]: string } = {
      'machine': '#6366f1',
      'machine arrêtée': '#64748b',
      'employé': '#3b82f6',
      'employé actif': '#10b981',
      'employé inactif': '#f59e0b',
      'client': '#f59e0b',
      'produit': '#10b981',
      'tables': '#8b5cf6',
      'tables_vides': '#ef4444'
    };
    return colors[key] || '#94a3b8';
  }

  public refreshData(): void {
    console.log('🔄 Actualisation...');
    this.loadData();
  }

  public navigateToVideo(id: string): void {
    this.router.navigate(['/admin/videos', id]);
  }

  public navigateToVideos(): void {
    this.router.navigate(['/admin/videos']);
  }

  get totalVideos7Days(): number {
    return this.analysisTimeline.reduce((sum, t) => sum + t.videosAnalyzed, 0);
  }

  get totalDetections7Days(): number {
    return this.analysisTimeline.reduce((sum, t) => sum + t.totalDetections, 0);
  }
}