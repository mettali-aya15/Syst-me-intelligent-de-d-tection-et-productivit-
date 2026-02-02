/**
 * Modèle utilisateur pour SmartFactory
 */
export interface User {
  password: string;
  id: string;
  email: string;
  
  firstName: string;
  lastName: string;
  role:UserRole;
  company?: string;
  avatar?: string;
  loginDate?: string;
  phone?: string;
  department?: string;
}

/**
 * Rôles disponibles dans le système
 */
export type UserRole ='admin' | 'manager' | 'operator' ;

/**
 * Permissions par rôle
 */
export const RolePermissions: Record<UserRole, string[]> = {
  admin: [
    'view_dashboard',
    'manage_users',
    'manage_employees',
    'manage_machines',
    'view_production',
    'manage_production',
    'view_rapports',
    'view_notifications',
    'manage_settings'
  ],
  manager: [
    'view_dashboard',
    'view_employees',
    'view_machines',
    'manage_machines',
    'view_production',
    'manage_production',
    'view_reports',
    'view_notifications'
  ],
  operator: [
    'view_dashboard',
    'view_machines',
    'view_production',
    'view_notifications'
  ]
};

/**
 * Vérifie si un rôle a une permission spécifique
 */
export function hasPermission(role: UserRole, permission: string): boolean {
  return RolePermissions[role]?.includes(permission) || false;
}

/**
 * Retourne le nom d'affichage d'un rôle
 */
export function getRoleDisplayName(role: UserRole): string {
  const roleNames: Record<UserRole, string> = {
    admin: 'Administrateur',
    manager: 'Manager',
    operator: 'Opérateur'
  };
  return roleNames[role] || role;
}