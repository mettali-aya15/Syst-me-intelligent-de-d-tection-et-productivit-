import { Component, Input } from '@angular/core';
import { CommonModule, Location } from '@angular/common';

@Component({
  selector: 'app-back-button',
  standalone: true,
  imports: [CommonModule],
  template: `
    <button class="btn-back" (click)="goBack()">
      <i class="fas fa-arrow-left"></i>
      <span>{{ label }}</span>
    </button>
  `,
  styles: [`
    .btn-back {
      display: inline-flex;
      align-items: center;
      gap: 10px;
      padding: 12px 20px;
      background: white;
      color: #4b5563;
      border: 2px solid #e5e7eb;
      border-radius: 10px;
      font-size: 15px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.3s ease;
      margin-bottom: 24px;

      i {
        font-size: 16px;
      }

      &:hover {
        background: #f9fafb;
        border-color: #dc143c;
        color: #dc143c;
        transform: translateX(-4px);
      }
    }
  `]
})
export class BackButtonComponent {
  @Input() label: string = 'Retour';
  
  constructor(private location: Location) {}
  
  goBack(): void {
    this.location.back();
  }
}