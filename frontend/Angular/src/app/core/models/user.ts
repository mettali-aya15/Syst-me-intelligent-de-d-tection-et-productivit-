// src/app/core/models/user.ts

/**
 * Rôle unique disponible dans le système
 */
export type UserRole = 'admin';

/**
 * Modèle utilisateur pour CAMIA-Factory
 */
export interface User {
  id: string;
  email: string;
  password?: string; // Optionnel (pas retourné par le backend)
  firstName: string;
  lastName: string;
  role: UserRole;
  company?: string;
  avatar?: string;
  loginDate?: string;
  phone?: string;
  department?: string;
}

/**
 * Réponse du backend lors de l'authentification
 */
export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

/**
 * Permissions administrateur
 */
export const AdminPermissions: string[] = [
  'view_dashboard',
  'manage_users',
  'manage_employees',
  'manage_machines',
  'view_production',
  'manage_production',
  'view_notifications',
  'manage_settings',
  'upload_videos',      // ✅ NOUVEAU
  'view_videos',        // ✅ NOUVEAU
  'manage_videos'       // ✅ NOUVEAU
];

/**
 * Vérifie si l'admin a une permission spécifique
 */
export function hasPermission(permission: string): boolean {
  return AdminPermissions.includes(permission);
}

/**
 * Retourne le nom d'affichage du rôle
 */
export function getRoleDisplayName(role: UserRole): string {
  return 'Administrateur';
}