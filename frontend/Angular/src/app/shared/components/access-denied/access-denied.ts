import { Component, OnInit } from '@angular/core';
import { CommonModule, Location } from '@angular/common';
import { Auth } from '../../../core/auth/auth';
import { User } from '../../../core/models/user';
import { RouterLink } from '@angular/router';


@Component({
  selector: 'app-access-denied',
   standalone: true, // <== INDISPENSABLE
  imports: [CommonModule, RouterLink],
  templateUrl: './access-denied.html',
  styleUrls: ['./access-denied.css']
})
export class AccessDenied implements OnInit {
  currentUser: User | null = null;

  constructor(
    private authService: Auth,
    private location: Location
  ) {}

  ngOnInit(): void {
    // Récupérer l'utilisateur actuel
    this.currentUser = this.authService.currentUserValue;
  }

  /**
   * Retourne à la page précédente
   */
  goBack(): void {
    this.location.back();
  }
}