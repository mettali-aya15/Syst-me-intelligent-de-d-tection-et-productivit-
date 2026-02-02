import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators, AbstractControl, ValidationErrors } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { Auth } from '../../core/auth/auth';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    RouterLink
  ],
  templateUrl: './register.html',
  styleUrls: ['./register.css']
})
export class Register implements OnInit, OnDestroy {
  registerForm!: FormGroup;
  isSubmitting = false;
  registerSuccess = false;
  registerError = false;
  errorMessage = '';
  showPassword = false;
  showConfirmPassword = false;
  
  // Force de mot de passe
  passwordStrength: 'weak' | 'medium' | 'strong' | '' = '';
  passwordStrengthText = 'Entrez un mot de passe';
  showPasswordStrength = false;

  private destroy$ = new Subject<void>();

  // Options pour le secteur d'activité
  industryOptions = [
    { value: '', label: 'Sélectionnez votre secteur' },
    { value: 'textile', label: 'Textile' },
    { value: 'agroalimentaire', label: 'Agroalimentaire' },
    { value: 'plastique', label: 'Plastique & Emballage' },
    { value: 'electronique', label: 'Électronique' },
    { value: 'mecanique', label: 'Mécanique' },
    { value: 'pharmaceutique', label: 'Pharmaceutique' },
    { value: 'autre', label: 'Autre' }
  ];
 
roleOptions = [
  { value: '', label: 'Sélectionnez votre rôle' },
  { value: 'operator', label: 'Opérateur - Accès basique' },
  { value: 'manager', label: 'Manager - Gestion de production' },
  { value: 'admin', label: 'Administrateur - Accès complet' }
];
  constructor(
    private formBuilder: FormBuilder,
    private authService: Auth,
    private router: Router
  ) {}
  // Options pour le rôle


  ngOnInit(): void {
    // Vérifier si l'utilisateur est déjà connecté
    if (this.authService.isAuthenticated()) {
      this.router.navigate(['/admin']);
      return;
    }

    this.initializeForm();
    this.setupPasswordStrengthListener();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * Initialise le formulaire d'inscription
   */
private initializeForm(): void {
  this.registerForm = this.formBuilder.group({
    firstName: ['', [Validators.required, Validators.minLength(2), Validators.maxLength(50)]],
    lastName: ['', [Validators.required, Validators.minLength(2), Validators.maxLength(50)]],
    email: ['', [Validators.required, Validators.email]],
    company: ['', [Validators.required, Validators.minLength(2), Validators.maxLength(100)]],
    phone: ['', [Validators.pattern(/^[+]?[(]?[0-9]{1,4}[)]?[-\s.]?[(]?[0-9]{1,4}[)]?[-\s.]?[0-9]{1,9}$/)]],
    industry: ['', [Validators.required]],
    role: ['', [Validators.required]], 
    password: ['', [Validators.required, Validators.minLength(8)]],
    confirmPassword: ['', [Validators.required]],
    terms: [false, [Validators.requiredTrue]]
  }, {
    validators: this.passwordMatchValidator
  });
}
  /**
   * Validateur personnalisé pour vérifier que les mots de passe correspondent
   */
  private passwordMatchValidator(control: AbstractControl): ValidationErrors | null {
    const password = control.get('password');
    const confirmPassword = control.get('confirmPassword');

    if (!password || !confirmPassword) {
      return null;
    }

    return password.value === confirmPassword.value ? null : { passwordMismatch: true };
  }

  /**
   * Configure l'écoute des changements de mot de passe pour la force
   */
  private setupPasswordStrengthListener(): void {
    const passwordControl = this.registerForm.get('password');
    
    if (passwordControl) {
      passwordControl.valueChanges
        .pipe(takeUntil(this.destroy$))
        .subscribe(password => {
          this.calculatePasswordStrength(password);
        });
    }
  }

  /**
   * Calcule la force du mot de passe
   */
  private calculatePasswordStrength(password: string): void {
    if (!password || password.length === 0) {
      this.showPasswordStrength = false;
      this.passwordStrength = '';
      this.passwordStrengthText = 'Entrez un mot de passe';
      return;
    }

    this.showPasswordStrength = true;
    let strength = 0;

    // Critères de force
    if (password.length >= 8) strength++;
    if (/[a-z]/.test(password) && /[A-Z]/.test(password)) strength++;
    if (/[0-9]/.test(password)) strength++;
    if (/[^a-zA-Z0-9]/.test(password)) strength++;

    // Définir la force
    if (strength <= 1) {
      this.passwordStrength = 'weak';
      this.passwordStrengthText = 'Mot de passe faible';
    } else if (strength <= 3) {
      this.passwordStrength = 'medium';
      this.passwordStrengthText = 'Mot de passe moyen';
    } else {
      this.passwordStrength = 'strong';
      this.passwordStrengthText = 'Mot de passe fort';
    }
  }

  /**
   * Bascule la visibilité du mot de passe
   */
  togglePasswordVisibility(): void {
    this.showPassword = !this.showPassword;
  }

  /**
   * Bascule la visibilité de la confirmation du mot de passe
   */
  toggleConfirmPasswordVisibility(): void {
    this.showConfirmPassword = !this.showConfirmPassword;
  }

  /**
   * Vérifie si un champ est invalide
   */
  isFieldInvalid(fieldName: string): boolean {
    const field = this.registerForm.get(fieldName);
    return !!(field && field.invalid && (field.dirty || field.touched));
  }

  /**
   * Vérifie si les mots de passe ne correspondent pas
   */
  hasPasswordMismatch(): boolean {
    const confirmPasswordControl = this.registerForm.get('confirmPassword');
    return !!(
      this.registerForm.hasError('passwordMismatch') &&
      confirmPasswordControl &&
      confirmPasswordControl.touched
    );
  }

  /**
   * Retourne le message d'erreur pour un champ
   */
  getFieldError(fieldName: string): string {
    const field = this.registerForm.get(fieldName);
    
    if (!field || !field.errors) {
      return '';
    }

    if (field.errors['required']) {
      return 'Ce champ est requis';
    }

    if (field.errors['email']) {
      return 'Veuillez entrer une adresse email valide';
    }

    if (field.errors['minlength']) {
      const minLength = field.errors['minlength'].requiredLength;
      return `Minimum ${minLength} caractères requis`;
    }

    if (field.errors['maxlength']) {
      const maxLength = field.errors['maxlength'].requiredLength;
      return `Maximum ${maxLength} caractères autorisés`;
    }

    if (field.errors['pattern']) {
      return 'Format de numéro de téléphone invalide';
    }

    return 'Erreur de validation';
  }

  /**
   * Marque tous les champs comme touchés
   */
  private markFormGroupTouched(formGroup: FormGroup): void {
    Object.keys(formGroup.controls).forEach(key => {
      const control = formGroup.get(key);
      control?.markAsTouched();

      if (control instanceof FormGroup) {
        this.markFormGroupTouched(control);
      }
    });
  }

  /**
   * Soumet le formulaire d'inscription
   */
  onSubmit(): void {
    this.markFormGroupTouched(this.registerForm);

    if (this.registerForm.invalid) {
      this.registerError = true;
      
      // Messages d'erreur spécifiques
      if (this.registerForm.hasError('passwordMismatch')) {
        this.errorMessage = 'Les mots de passe ne correspondent pas';
      } else if (this.registerForm.get('terms')?.invalid) {
        this.errorMessage = 'Veuillez accepter les conditions d\'utilisation';
      } else {
        this.errorMessage = 'Veuillez corriger les erreurs dans le formulaire';
      }
      return;
    }

    this.isSubmitting = true;
    this.registerError = false;
    this.registerSuccess = false;

    const formData = this.registerForm.value;

    // Appel au service d'inscription
    this.authService.register(formData)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response) => {
          this.isSubmitting = false;
          this.registerSuccess = true;

          console.log('✅ Inscription réussie:', response.user);

          // Rediriger après 1 seconde
          setTimeout(() => {
            const user = response.user;
            switch (user.role) {
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
                this.router.navigate(['/']);
            }
          }, 1000);
        },
        error: (error) => {
          this.isSubmitting = false;
          this.registerError = true;
          this.errorMessage = error.message || 'Une erreur est survenue lors de l\'inscription';
          
          console.error(' Erreur d\'inscription:', error);
        }
      });
  }
}