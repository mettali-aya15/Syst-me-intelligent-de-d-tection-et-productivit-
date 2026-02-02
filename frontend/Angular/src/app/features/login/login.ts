import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { Auth } from '../../core/auth/auth';
import { User } from '../../core/models/user'; // Assurez-vous que l'import est correct

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './login.html',
  styleUrls: ['./login.css']
})
export class Login implements OnInit, OnDestroy {
  loginForm!: FormGroup;
  isSubmitting = false;
  loginSuccess = false;
  loginError = false;
  errorMessage = '';
  showPassword = false;

  private destroy$ = new Subject<void>();

  constructor(
    private formBuilder: FormBuilder,
    private authService: Auth,
    private router: Router
  ) {}

  ngOnInit(): void {
    // Si déjà connecté, on redirige immédiatement
    if (this.authService.isAuthenticated()) {
      this.redirectToDashboard(this.authService.currentUserValue);
      return;
    }
    this.initializeForm();
    this.loadRememberedEmail();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private initializeForm(): void {
    this.loginForm = this.formBuilder.group({
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(6)]],
      rememberMe: [false]
    });
  }

  private loadRememberedEmail(): void {
    const rememberedEmail = localStorage.getItem('rememberedEmail');
    if (rememberedEmail) {
      this.loginForm.patchValue({ email: rememberedEmail, rememberMe: true });
    }
  }

  togglePasswordVisibility(): void {
    this.showPassword = !this.showPassword;
  }

  isFieldInvalid(fieldName: string): boolean {
    const field = this.loginForm.get(fieldName);
    return !!(field && field.invalid && (field.dirty || field.touched));
  }

  getFieldError(fieldName: string): string {
    const field = this.loginForm.get(fieldName);
    if (!field || !field.errors) return '';
    if (field.errors['required']) return 'Ce champ est requis';
    if (field.errors['email']) return 'Email invalide';
    if (field.errors['minlength']) return 'Minimum 6 caractères';
    return 'Erreur';
  }

  private markFormGroupTouched(formGroup: FormGroup): void {
    Object.values(formGroup.controls).forEach(control => {
      control.markAsTouched();
      if (control instanceof FormGroup) this.markFormGroupTouched(control);
    });
  }

  onSubmit(): void {
    this.markFormGroupTouched(this.loginForm);
    if (this.loginForm.invalid) {
      this.loginError = true;
      this.errorMessage = 'Veuillez remplir correctement tous les champs';
      return;
    }

    this.isSubmitting = true;
    this.loginError = false;
    this.loginSuccess = false;

    const { email, password, rememberMe } = this.loginForm.value;

    this.authService.login(email, password)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response) => {
          this.isSubmitting = false;
          this.loginSuccess = true;

          // Gérer "Se souvenir de moi"
          if (rememberMe) localStorage.setItem('rememberedEmail', email);
          else localStorage.removeItem('rememberedEmail');

          console.log('✅ Connexion réussie, utilisateur:', response.user);

          // REDIRECTION : On passe directement l'utilisateur de la réponse
          setTimeout(() => {
            this.redirectToDashboard(response.user);
          }, 1000);
        },
        error: (error) => {
          this.isSubmitting = false;
          this.loginError = true;
          this.errorMessage = error.message || 'Identifiants incorrects';
          this.loginForm.patchValue({ password: '' });
          console.error('❌ Erreur:', error);
        }
      });
  }

  /**
   * Redirige l'utilisateur selon son rôle
   * @param user L'objet utilisateur à tester
   */
  private redirectToDashboard(user: User | null): void {
    const redirectUrl = this.authService.getRedirectUrl();

    // 1. Si une URL de redirection forcée existe (ex: via un Guard)
    if (redirectUrl) {
      this.router.navigate([redirectUrl]);
      return;
    }

    // 2. Sinon, redirection par rôle
    if (user && user.role) {
      // On convertit en minuscules pour éviter les erreurs "Admin" vs "admin"
      const role = user.role.toLowerCase();
      console.log('🚀 Tentative de redirection pour le rôle:', role);

      switch (role) {
        case 'admin':
          this.router.navigate(['/admin']);
          break;
        case 'manager':
          this.router.navigate(['/manager']);
          break;
        case 'operator':
          this.router.navigate(['/operator']);
          break;
        default:
          console.warn('⚠️ Rôle inconnu, retour à l\'accueil');
          this.router.navigate(['/']);
          break;
      }
    } else {
      console.error('❌ Aucun utilisateur ou rôle trouvé pour la redirection');
      this.router.navigate(['/']);
    }
  }
}