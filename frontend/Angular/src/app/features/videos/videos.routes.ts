import { Routes } from '@angular/router';
import { VideoUploadComponent } from './video-upload/video-upload';
import { VideoListComponent } from './video-list/video-list';
import { VideoDetailComponent } from './video-detail/video-detail';

export const VIDEOS_ROUTES: Routes = [
  { 
    path: '', 
    component: VideoListComponent 
  },
  { 
    path: 'upload', 
    component: VideoUploadComponent 
  },
  { 
    path: ':id', 
    component: VideoDetailComponent 
  }
];