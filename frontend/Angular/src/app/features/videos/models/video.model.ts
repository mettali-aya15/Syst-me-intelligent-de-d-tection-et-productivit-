/**
 * Modèles de données pour les vidéos
 */

export type VideoStatus = 'uploaded' | 'processing' | 'completed' | 'failed';

export interface Video {
  _id: string;
  id?: string;
  filename: string;
  file_path?: string;
  filepath?: string;
  annotated_path?: string;
  duration: number;
  fps: number;
  width?: number;
  height?: number;
  total_frames: number;
  status: VideoStatus;
  model_type: 'objects' | 'employees' | 'both';
  confidence?: number;
  total_detections?: number;
  summary?: { [key: string]: number };
  classes_detectees?: { [key: string]: number };
  uploaded_at?: string;
  processed_at?: string;
  created_at: string;
  updated_at?: string;
}

export interface Detection {
  id?: string;
  video_id?: string;
  frame_number: number;
  timestamp: number;
  class_name: string;
  confidence: number;
  bbox: BoundingBox;
  track_id?: number;
  source?: string;
  created_at?: string;
}

export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface VideoStats {
  video_id?: string;
  total_detections: number;
  avg_confidence?: number;
  average_confidence?: number;
  max_confidence?: number;
  min_confidence?: number;
  unique_classes?: string[];
  unique_objects?: { [key: string]: number };
  class_distribution?: { [key: string]: number };
  detections_by_frame?: { [key: number]: number };
}

export interface VideoUploadParams {
  file: File;
  model_type: 'objects' | 'employees' | 'both';
  confidence: number;
}

export interface VideoUploadResponse {
  video_id: string;
  filename: string;
  duration?: number;
  fps?: number;
  resolution?: string;
  total_frames?: number;
  status: VideoStatus;
  message?: string;
}