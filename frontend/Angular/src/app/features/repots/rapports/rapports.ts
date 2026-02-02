import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

import { Auth } from '../../../core/auth/auth';
import { RapportsService } from '../rapports-service';
import { exportRapportPDF } from '../exp-pdf';
import { exportRapportExcel } from '../exp-excel';
import { AdminDashboard } from "../../admin/admin-dashboard/admin-dashboard";
import { RouterLink } from '@angular/router';


@Component({
  selector: 'app-rapports',
  standalone: true,
  imports: [CommonModule, AdminDashboard , RouterLink],
  templateUrl: './rapports.html',
  styleUrls: ['./rapports.css']
})
export class RapportsComponent {

  loading = false;

  constructor(
    private rapportsService: RapportsService,
    private auth: Auth
  ) {}

 

  exportPDF() {
    this.loading = true;
    this.rapportsService.getAllRapportData().subscribe(data => {
      exportRapportPDF(data);
      this.loading = false;
    });
  }

  exportExcel() {
    this.loading = true;
    this.rapportsService.getAllRapportData().subscribe(data => {
      exportRapportExcel(data);
      this.loading = false;
    });
  }
}
