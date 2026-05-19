import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { VideoService } from '../services/video.service';
import { Video } from '../models/video.model';

@Component({
  selector: 'app-video-list',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './video-list.html',
  styleUrls: ['./video-list.scss']
})
export class VideoListComponent implements OnInit {
  private videoService = inject(VideoService);

  videos: Video[] = [];
  filteredVideos: Video[] = [];
  isLoading = true;
  errorMessage = '';

  filterStatus = 'all';
  filterModel = 'all';  // ✅ REMIS
  searchQuery = '';

  ngOnInit(): void {
    this.loadVideos();
  }

  loadVideos(): void {
    this.isLoading = true;
    this.errorMessage = '';

    this.videoService.getVideos().subscribe({
      next: (videos) => {
        this.videos = videos.map(v => ({
          ...v,
          model_type: v.model_type || 'both'
        }));
        
        this.filteredVideos = [...this.videos];
        this.isLoading = false;
        
        console.log('✅ Vidéos chargées:', this.videos.length);
      },
      error: (error) => {
        console.error('❌ Erreur:', error);
        this.errorMessage = 'Impossible de charger les vidéos.';
        this.isLoading = false;
      }
    });
  }

  applyFilters(): void {
    this.filteredVideos = this.videos.filter(video => {
      // Filtre par statut
      if (this.filterStatus !== 'all' && video.status !== this.filterStatus) {
        return false;
      }

      // Filtre par modèle - ✅ REMIS
      if (this.filterModel !== 'all' && video.model_type !== this.filterModel) {
        return false;
      }

      // Filtre par recherche
      if (this.searchQuery && this.searchQuery.trim()) {
        if (!video.filename.toLowerCase().includes(this.searchQuery.toLowerCase())) {
          return false;
        }
      }

      return true;
    });

    console.log(`✅ Filtrage: ${this.filteredVideos.length} / ${this.videos.length} vidéos`);
  }

  deleteVideo(video: Video, event: Event): void {
    event.stopPropagation();
    event.preventDefault();

    const confirmMessage = `⚠️ ATTENTION ⚠️\n\nÊtes-vous sûr de vouloir supprimer ?\n\n📹 ${video.filename}\n📊 ${this.getStatusLabel(video.status)}\n\n❌ Action IRRÉVERSIBLE !`;

    if (!confirm(confirmMessage)) {
      return;
    }

    this.videoService.deleteVideo(video._id).subscribe({
      next: () => {
        console.log('✅ Suppression réussie:', video._id);
        alert(`✅ Vidéo "${video.filename}" supprimée avec succès !`);
        this.loadVideos();
      },
      error: (error: any) => {
        console.error('❌ Erreur suppression:', error);
        alert(`❌ Erreur: ${error.message || 'Suppression impossible'}`);
      }
    });
  }

  resetFilters(): void {
    this.filterStatus = 'all';
    this.filterModel = 'all';  // ✅ REMIS
    this.searchQuery = '';
    this.filteredVideos = [...this.videos];
    console.log(`✅ Filtres réinitialisés`);
  }

  // ========================================
  // HELPER FUNCTIONS
  // ========================================

  getStatusClass(status: string): string {
    const statusMap: { [key: string]: string } = {
      'completed': 'status-success',
      'processing': 'status-warning',
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

  hasDetections(video: Video): boolean {
    if (!video.unique_objects) return false;
    
    const total = Object.values(video.unique_objects)
      .reduce((sum, count) => sum + (Number(count) || 0), 0);
    
    return total > 0;
  }

  getTotalUniqueObjects(video: Video): number {
    if (!video.unique_objects) return 0;
    
    return Object.values(video.unique_objects)
      .reduce((sum, count) => sum + (Number(count) || 0), 0);
  }

  getTopClasses(video: Video): string[] {
    if (!video.unique_objects) return [];
    
    return Object.entries(video.unique_objects)
      .filter(([_, count]) => Number(count) > 0)
      .sort((a, b) => Number(b[1]) - Number(a[1]))
      .slice(0, 3)
      .map(([className, count]) => `${className}: ${count}`);
  }

  getVideoStats(): { [key: string]: number } {
    const stats: { [key: string]: number } = {
      total: this.videos.length,
      completed: 0,
      processing: 0,
      uploaded: 0,
      failed: 0
    };

    this.videos.forEach(video => {
      const status = video.status?.toLowerCase();
      if (status && status in stats) {
        stats[status]++;
      }
    });

    return stats;
  }

  getModelStats(): { [key: string]: number } {
    const stats: { [key: string]: number } = {
      objects: 0,
      employees: 0,
      both: 0
    };

    this.videos.forEach(video => {
      const model = (video.model_type || 'both').toLowerCase();
      if (model in stats) {
        stats[model]++;
      }
    });

    return stats;
  }
}