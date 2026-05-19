/**
 * Modèles TypeScript pour les KPI
 * Correspondant aux modèles Pydantic du backend
 */

export interface KPIProduction {
  taux_productivite: number;
  objectif_production: number;
  taux_conformite: number;
  cadence_production: number;
  unites_produites: number;
  objectif_unites: number;
  produits_conformes: number;
  total_produits: number;
}

export interface KPIMachines {
  trs: number;
  disponibilite: number;
  performance: number;
  qualite: number;
  taux_panne: number;
  mtbf: number;
  mttr: number;
  total_machines: number;
  machines_actives: number;
  machines_arretees: number;
  temps_productif: number;
  temps_total: number;
}

export interface KPIEmployes {
  taux_presence: number;
  taux_activite: number;
  productivite_par_employe: number;
  taux_inactivite: number;
  total_employes: number;
  employes_presents: number;
  employes_actifs: number;
  employes_inactifs: number;
}

export interface KPITables {
  total_tables: number;
  tables_occupees: number;
  tables_vides: number;
  taux_occupation: number;
}

export interface KPIClients {
  total_clients: number;
  clients_en_attente: number;
  clients_servis: number;
  taux_service: number;
}

export interface KPIGlobal {
  date: string;
  periode: string;
  date_debut: string;
  date_fin: string;
  production?: KPIProduction;
  machines?: KPIMachines;
  employes?: KPIEmployes;
  tables?: KPITables;
  clients?: KPIClients;
  nombre_videos: number;
}

export interface KPIResponse {
  success: boolean;
  data: KPIGlobal;
}