import { Routes } from '@angular/router';
import { Home } from './home/home';
import { Contact } from './contact/contact';
import { About } from './about/about';
import { Login } from './features/login/login';
import { Register } from './features/register/register';
import { Admin } from './features/admin/admin';
import { AccessDenied } from './shared/components/access-denied/access-denied';

import { adminGuard, authGuard, managerGuard } from './core/auth/auth.guard';
import { EmpList } from './features/employees/emp-list/emp-list';
import { MachineList } from './features/machines/machines-list/machines-list';
import { ProductionList } from './features/production/production-list/production-list';
import { RapportsComponent } from './features/repots/rapports/rapports';
import { NotificationListComponent } from './shared/components/notifications/notif-list/notif-list';
import { AdminDashboard } from './features/admin/admin-dashboard/admin-dashboard';
import { OperatorDashboard } from './features/operator/operator-dashboard/operator-dashboard';
import { Manager } from './features/manager/manager-dashboard/manager-dashboard';
import { UserManagementComponent } from './features/admin/user-management/user-management/user-management';



export const routes: Routes = [
    {path:'',component:Home},
    {path:'contact',component:Contact},
    {path:'about',component:About},
    {path:'login',component:Login},
    {path:'register',component:Register},
    {path:'access-denied',component:AccessDenied},
    {path:'admin',component:Admin  ,canActivate:[adminGuard]},
    {path:'manager',component:Manager , canActivate:[managerGuard]},
     {path:'app-admin-dashboard',component:AdminDashboard },
    
{ path: 'machines', component: MachineList  , canActivate: [authGuard]},
{ path: 'machines/:id', component: MachineList ,canActivate: [authGuard]},


    {path:'production',component:ProductionList,canActivate: [authGuard]},
    {path:'emp-list',component:EmpList,canActivate: [authGuard]},
  
{path:'rapport',component:RapportsComponent,canActivate: [authGuard]},
  {path:'notifications',component:NotificationListComponent,canActivate: [authGuard]},

 {path:'operator',component:OperatorDashboard},
 {path:'kpi',component:Admin,  canActivate: [adminGuard]},
 {path:'users',component:UserManagementComponent,  canActivate: [adminGuard]},
];

