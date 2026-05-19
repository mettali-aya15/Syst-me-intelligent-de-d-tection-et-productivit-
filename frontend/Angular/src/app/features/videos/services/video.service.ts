import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, tap } from 'rxjs';
import { NotificationService } from '../../../core/services/notification.service';
import { Video, VideoUploadParams, VideoUploadResponse } from '../models/video.model';

export interface AttendanceReport {
  total_employees: number;
  present: Array<{
    id: string;
    name: string;
    full_name: string;
    department: string;
    email: string;
  }>;
  present_count: number;
  absent: Array<{
    id: string;
    name: string;
    full_name: string;
    department: string;
    email: string;
  }>;
  absent_count: number;
  attendance_rate: number;
}

@Injectable({
  providedIn: 'root'
})
export class VideoService {
  private apiUrl = 'http://localhost:8000/api/v1/videos';

  constructor(
    private http: HttpClient,
    private notificationService: NotificationService
  ) {}

  uploadVideo(params: VideoUploadParams): Observable<VideoUploadResponse> {
    const formData = new FormData();
    formData.append('file', params.file);

    const httpParams = new HttpParams()
      .set('model_type', params.model_type || 'objects')
      .set('confidence', (params.confidence || 0.3).toString());

    return this.http.post<VideoUploadResponse>(`${this.apiUrl}/upload`, formData, { params: httpParams });
  }

  getVideos(): Observable<Video[]> {
    return this.http.get<Video[]>(this.apiUrl).pipe(
      tap(videos => {
        console.log('✅ Vidéos chargées:', videos.length);
        
        videos.forEach(video => {
          if (video.status === 'completed') {
            this.checkForAlerts(video);
          }
        });
      })
    );
  }

  listVideos(): Observable<Video[]> {
    return this.getVideos();
  }

  getVideo(id: string): Observable<Video> {
    return this.http.get<Video>(`${this.apiUrl}/${id}`);
  }

  analyzeVideo(videoId: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/${videoId}/analyze`, {});
  }

  deleteVideo(id: string): Observable<any> {
    return this.http.delete(`${this.apiUrl}/${id}`);
  }

  getAttendance(videoId: string): Observable<AttendanceReport> {
    return this.http.get<AttendanceReport>(`${this.apiUrl}/${videoId}/attendance`);
  }

  private checkForAlerts(video: Video): void {
    // ✅ VÉRIFIER SI DÉJÀ NOTIFIÉ POUR CETTE VIDÉO
    const notifiedKey = `notified_${video._id}`;
    const hasNotified = sessionStorage.getItem(notifiedKey);
    
    if (hasNotified) {
      console.log(`⏭️ Vidéo ${video._id} déjà notifiée, ignorée`);
      return;
    }

    const uniqueObjects = video.unique_objects || {};
    
    console.log('🔍 Vérification des alertes pour:', video.filename);
    console.log('🎯 model_type:', video.model_type);
    console.log('📦 unique_objects:', uniqueObjects);

    let hasCreatedNotification = false;

    const isEmployeeModel = video.model_type === 'employees' || video.model_type === 'both';

    // MACHINES ARRÊTÉES
    const machinesStopped = 
      uniqueObjects['machine arrêtée'] || 
      uniqueObjects['machine arretee'] || 
      uniqueObjects['Machine Arrêtée'] || 
      uniqueObjects['Machine Arretee'] || 
      uniqueObjects['MACHINE_ARRETEE'] ||
      uniqueObjects['machine_arretee'] || 0;
    
    if (machinesStopped > 0) {
      console.log('🚨 → NOTIFICATION: Machine arrêtée');
      this.notificationService.notifyMachineStopped(video._id, machinesStopped);
      hasCreatedNotification = true;
    }

    // EMPLOYÉS INACTIFS
    const employeesInactive = 
      uniqueObjects['employé inactif'] || 
      uniqueObjects['employe inactif'] || 
      uniqueObjects['Employé Inactif'] || 
      uniqueObjects['Employe Inactif'] ||
      uniqueObjects['EMPLOYE_INACTIF'] ||
      uniqueObjects['employe_inactif'] || 0;
    
    if (employeesInactive > 0) {
      console.log('⚠️ → NOTIFICATION: Employé inactif');
      this.notificationService.notifyEmployeeInactive(video._id, employeesInactive);
      hasCreatedNotification = true;
    }

    // TABLES VIDES
    const emptyTables = 
      uniqueObjects['tables_vides'] ||
      uniqueObjects['tables vides'] || 
      uniqueObjects['table_vide'] || 
      uniqueObjects['table vide'] || 
      uniqueObjects['Table vide'] || 
      uniqueObjects['TABLE_VIDE'] || 0;

    if (emptyTables > 0) {
      console.log('📋 → NOTIFICATION: Table vide détectée');
      this.notificationService.notifyEmptyTable(video._id, emptyTables);
      hasCreatedNotification = true;
    }

    // ABSENCES (SEULEMENT POUR EMPLOYEES/BOTH)
    if (isEmployeeModel) {
      console.log('👥 Vérification des absences (model_type = ' + video.model_type + ')');
      this.checkEmployeeAbsence(video);
      hasCreatedNotification = true;
    } else {
      console.log('⏭️ Pas de vérification d\'absence (model_type = ' + video.model_type + ')');
    }

    // ANALYSE TERMINÉE (UNE SEULE FOIS)
    if (hasCreatedNotification) {
      console.log('✅ → NOTIFICATION: Analyse terminée');
      this.notificationService.notifyVideoAnalyzed(video._id, video.filename);
    }

    // ✅ MARQUER COMME NOTIFIÉ
    sessionStorage.setItem(notifiedKey, 'true');
    console.log(`✅ Vidéo ${video._id} marquée comme notifiée`);
  }

  private checkEmployeeAbsence(video: Video): void {
    // ✅ VÉRIFIER SI DÉJÀ NOTIFIÉ POUR LES ABSENCES
    const absenceKey = `absence_notified_${video._id}`;
    const hasNotifiedAbsence = sessionStorage.getItem(absenceKey);
    
    if (hasNotifiedAbsence) {
      console.log(`⏭️ Absence pour vidéo ${video._id} déjà notifiée, ignorée`);
      return;
    }

    this.getAttendance(video._id).subscribe({
      next: (report) => {
        if (report.absent_count > 0) {
          console.log(`👥 → NOTIFICATION: ${report.absent_count} employé(s) absent(s)`);
          this.notificationService.notifyEmployeeAbsence(video._id, report.absent_count);
          
          // ✅ MARQUER COMME NOTIFIÉ
          sessionStorage.setItem(absenceKey, 'true');
        }
      },
      error: (err) => {
        console.error('❌ Erreur lors de la vérification des absences:', err);
      }
    });
  }
}