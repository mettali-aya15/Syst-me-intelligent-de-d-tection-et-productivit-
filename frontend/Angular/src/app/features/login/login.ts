import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router} from '@angular/router';
import { FormGroup, FormControl, ReactiveFormsModule, Validators } from '@angular/forms';
import { Auth } from '../../core/auth/auth';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './login.html',
  styleUrls: ['./login.css']
})
export class Login {
  private authService = inject(Auth);
  private router = inject(Router);

  // ✅ FormGroup
  loginForm = new FormGroup({
  email: new FormControl('', [Validators.required, Validators.email]),
  password: new FormControl('', [Validators.required, Validators.minLength(6)]),
  rememberMe: new FormControl(false) // ✅ AJOUTE CETTE LIGNE
});

  // ✅ Propriétés manquantes
  errorMessage = '';
  loginError = '';
  isLoading = false;
  isSubmitting = false;
  loginSuccess = false;
  showPassword = false;

  /**
   * ✅ Vérifier si un champ est invalide
   */
  isFieldInvalid(fieldName: string): boolean {
    const field = this.loginForm.get(fieldName);
    return !!(field && field.invalid && (field.dirty || field.touched));
  }

  /**
   * ✅ Obtenir le message d'erreur d'un champ
   */
  getFieldError(fieldName: string): string {
    const field = this.loginForm.get(fieldName);
    
    if (!field || !field.errors) {
      return '';
    }

    if (field.errors['required']) {
      return 'Ce champ est requis';
    }

    if (field.errors['email']) {
      return 'Email invalide';
    }

    if (field.errors['minlength']) {
      return `Minimum ${field.errors['minlength'].requiredLength} caractères`;
    }

    return '';
  }

  /**
   * ✅ Toggle visibilité du mot de passe
   */
  togglePasswordVisibility(): void {
    this.showPassword = !this.showPassword;
  }

  /**
   * ✅ Soumettre le formulaire
   */
  onSubmit(): void {
    // Marquer tous les champs comme touchés pour afficher les erreurs
    Object.keys(this.loginForm.controls).forEach(key => {
      this.loginForm.get(key)?.markAsTouched();
    });

    if (this.loginForm.invalid) {
      this.loginError = 'Veuillez remplir tous les champs correctement.';
      return;
    }

    this.isSubmitting = true;
    this.isLoading = true;
    this.loginError = '';
    this.errorMessage = '';

    const { email, password } = this.loginForm.value;

    this.authService.login(email!, password!).subscribe({
      next: (response: any) => {
        console.log('✅ Connexion réussie:', response);
        
        this.loginSuccess = true;
        this.isSubmitting = false;
        this.isLoading = false;

        // Redirection selon le rôle
        const user = response.user || response;
        if (user.role === 'admin') {
          this.router.navigate(['/admin/dashboard']);
        } else {
          this.router.navigate(['/']);
        }
      },
      error: (error) => {
        console.error('❌ Erreur login:', error);
        this.loginError = error.error?.message || 'Email ou mot de passe incorrect.';
        this.errorMessage = this.loginError;
        this.isSubmitting = false;
        this.isLoading = false;
        this.loginSuccess = false;
      }
    });
  }
}