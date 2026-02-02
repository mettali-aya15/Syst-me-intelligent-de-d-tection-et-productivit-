import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, FormsModule, ReactiveFormsModule, Validators } from '@angular/forms';
import { Navbar } from "../shared/components/navbar/navbar";
import { CommonModule } from '@angular/common';

interface ContactFormData {
  firstName: string;
  lastName: string;
  email: string;
  phone?: string;
  company?: string;
  subject: string;
  message: string;
}

@Component({
  selector: 'app-contact',
  templateUrl: './contact.html',
  styleUrls: ['./contact.css'],
  imports: [Navbar,CommonModule,ReactiveFormsModule]
})
export class Contact implements OnInit {
  contactForm!: FormGroup;
  isSubmitting = false;
  submitSuccess = false;
  submitError = false;
  errorMessage = '';

  // Options pour le menu déroulant "Sujet"
  subjectOptions = [
    { value: '', label: 'Sélectionnez un sujet' },
    { value: 'demo', label: 'Demande de démonstration' },
    { value: 'info', label: 'Demande d\'information' },
    { value: 'quote', label: 'Demande de devis' },
    { value: 'support', label: 'Support technique' },
    { value: 'partnership', label: 'Partenariat' },
    { value: 'other', label: 'Autre' }
  ];

  // Informations de contact de l'entreprise
  contactInfo = {
    emails: [
      { address: 'info@smartfactory.tn', icon: 'fas fa-envelope' },
      { address: 'contact@smartfactory.tn', icon: 'fas fa-envelope' }
    ]
  };

  constructor(private formBuilder: FormBuilder) {}

  ngOnInit(): void {
    this.initializeForm();
  }

  /**
   * Initialise le formulaire de contact avec les validations
   */
  private initializeForm(): void {
    this.contactForm = this.formBuilder.group({
      firstName: ['', [Validators.required, Validators.minLength(2), Validators.maxLength(50)]],
      lastName: ['', [Validators.required, Validators.minLength(2), Validators.maxLength(50)]],
      email: ['', [Validators.required, Validators.email, Validators.maxLength(100)]],
      phone: ['', [Validators.pattern(/^[+]?[(]?[0-9]{1,4}[)]?[-\s.]?[(]?[0-9]{1,4}[)]?[-\s.]?[0-9]{1,9}$/)]],
      company: ['', [Validators.maxLength(100)]],
      subject: ['', Validators.required],
      message: ['', [Validators.required, Validators.minLength(10), Validators.maxLength(1000)]]
    });
  }

  /**
   * Vérifie si un champ est invalide et a été touché
   */
  isFieldInvalid(fieldName: string): boolean {
    const field = this.contactForm.get(fieldName);
    return !!(field && field.invalid && (field.dirty || field.touched));
  }

  /**
   * Retourne le message d'erreur pour un champ spécifique
   */
  getFieldError(fieldName: string): string {
    const field = this.contactForm.get(fieldName);
    
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
   * Marque tous les champs du formulaire comme touchés
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
   * Soumet le formulaire de contact
   */
  onSubmit(): void {
    // Marquer tous les champs comme touchés pour afficher les erreurs
    this.markFormGroupTouched(this.contactForm);

    // Vérifier si le formulaire est valide
    if (this.contactForm.invalid) {
      this.submitError = true;
      this.errorMessage = 'Veuillez corriger les erreurs dans le formulaire';
      this.scrollToError();
      return;
    }

    // Réinitialiser les états
    this.isSubmitting = true;
    this.submitError = false;
    this.submitSuccess = false;

    const formData: ContactFormData = this.contactForm.value;

    // Appel à l'API ou service
    this.submitContactForm(formData);
  }

  /**
   * Soumet le formulaire à l'API
   * Remplacer cette méthode par un vrai appel HTTP dans un service
   */
  private submitContactForm(data: ContactFormData): void {
    console.log('Données du formulaire:', data);

    // Simulation d'un appel API avec setTimeout
    setTimeout(() => {
      // Simuler un succès (vous pouvez ajouter une logique d'erreur ici)
      const success = Math.random() > 0.1; // 90% de succès

      if (success) {
        this.isSubmitting = false;
        this.submitSuccess = true;
        this.contactForm.reset();
        
        // Réinitialiser l'état du formulaire
        Object.keys(this.contactForm.controls).forEach(key => {
          this.contactForm.get(key)?.setErrors(null);
        });
        
        // Masquer le message de succès après 5 secondes
        setTimeout(() => {
          this.submitSuccess = false;
        }, 5000);

        // Scroll vers le haut pour voir le message de succès
        window.scrollTo({ top: 0, behavior: 'smooth' });
      } else {
        this.isSubmitting = false;
        this.submitError = true;
        this.errorMessage = 'Une erreur est survenue lors de l\'envoi du message. Veuillez réessayer.';
      }
    }, 1500);

    
  }

  /**
   * Scroll vers le premier champ en erreur
   */
  private scrollToError(): void {
    const firstInvalidControl = document.querySelector('.form-group input.ng-invalid, .form-group select.ng-invalid, .form-group textarea.ng-invalid');
    if (firstInvalidControl) {
      firstInvalidControl.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }

  /**
   * Réinitialise le formulaire
   */
  resetForm(): void {
    this.contactForm.reset();
    this.submitError = false;
    this.submitSuccess = false;
    this.errorMessage = '';
  }

  /**
   * Retourne le nombre de caractères restants pour le message
   */
  getMessageCharacterCount(): string {
    const messageControl = this.contactForm.get('message');
    if (messageControl) {
      const currentLength = messageControl.value?.length || 0;
      const maxLength = 1000;
      return `${currentLength}/${maxLength}`;
    }
    return '0/1000';
  }

  /**
   * Vérifie si le message approche de la limite
   */
  isMessageNearLimit(): boolean {
    const messageControl = this.contactForm.get('message');
    if (messageControl) {
      const currentLength = messageControl.value?.length || 0;
      return currentLength > 900;
    }
    return false;
  }
}