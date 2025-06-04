/**
 * Script JavaScript principal pour le projet Django Blog
 * Contient les fonctionnalités communes et utilitaires
 */

// Attendre que le DOM soit complètement chargé
document.addEventListener('DOMContentLoaded', function() {
    
    // Initialisation des fonctionnalités
    initializeAlerts();
    initializeConfirmButtons();
    initializeForms();
    initializeNavigation();
    initializeImagePreview();
    initializeTooltips();
    
});

/**
 * Gestion des messages d'alerte avec auto-fermeture
 */
function initializeAlerts() {
    const alerts = document.querySelectorAll('.alert');
    
    alerts.forEach(function(alert) {
        // Ajouter un bouton de fermeture si pas déjà présent
        if (!alert.querySelector('.alert-close')) {
            const closeButton = document.createElement('button');
            closeButton.innerHTML = '&times;';
            closeButton.className = 'alert-close';
            closeButton.style.cssText = `
                position: absolute;
                top: 0.5rem;
                right: 1rem;
                background: none;
                border: none;
                font-size: 1.5rem;
                cursor: pointer;
                color: inherit;
                opacity: 0.7;
            `;
            
            alert.style.position = 'relative';
            alert.appendChild(closeButton);
            
            closeButton.addEventListener('click', function() {
                alert.style.transition = 'opacity 0.3s ease';
                alert.style.opacity = '0';
                setTimeout(() => alert.remove(), 300);
            });
        }
        
        // Auto-fermeture après 5 secondes pour les messages de succès
        if (alert.classList.contains('alert-success')) {
            setTimeout(function() {
                if (alert.parentNode) {
                    alert.style.transition = 'opacity 0.3s ease';
                    alert.style.opacity = '0';
                    setTimeout(() => alert.remove(), 300);
                }
            }, 5000);
        }
    });
}

/**
 * Confirmation pour les actions de suppression
 */
function initializeConfirmButtons() {
    const deleteButtons = document.querySelectorAll('.btn-danger, [data-confirm]');
    
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            const message = this.getAttribute('data-confirm') || 
                          'Êtes-vous sûr de vouloir effectuer cette action ?';
            
            if (!confirm(message)) {
                e.preventDefault();
                return false;
            }
        });
    });
}

/**
 * Amélioration des formulaires
 */
function initializeForms() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(function(form) {
        // Validation en temps réel
        const inputs = form.querySelectorAll('input, textarea, select');
        inputs.forEach(function(input) {
            input.addEventListener('blur', function() {
                validateField(this);
            });
            
            input.addEventListener('input', function() {
                if (this.classList.contains('is-invalid')) {
                    validateField(this);
                }
            });
        });
        
        // Soumission du formulaire
        form.addEventListener('submit', function(e) {
            let isValid = true;
            
            inputs.forEach(function(input) {
                if (!validateField(input)) {
                    isValid = false;
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                const firstInvalid = form.querySelector('.is-invalid');
                if (firstInvalid) {
                    firstInvalid.focus();
                    firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }
        });
    });
}

/**
 * Validation d'un champ de formulaire
 */
function validateField(field) {
    const value = field.value.trim();
    let isValid = true;
    let errorMessage = '';
    
    // Vérification des champs requis
    if (field.hasAttribute('required') && !value) {
        isValid = false;
        errorMessage = 'Ce champ est requis.';
    }
    
    // Validation de l'email
    if (field.type === 'email' && value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
            isValid = false;
            errorMessage = 'Veuillez entrer une adresse email valide.';
        }
    }
    
    // Validation de la longueur minimale
    const minLength = field.getAttribute('minlength');
    if (minLength && value.length < parseInt(minLength)) {
        isValid = false;
        errorMessage = `Ce champ doit contenir au moins ${minLength} caractères.`;
    }
    
    // Appliquer les styles de validation
    field.classList.remove('is-valid', 'is-invalid');
    const feedback = field.parentNode.querySelector('.invalid-feedback');
    
    if (isValid) {
        field.classList.add('is-valid');
        if (feedback) feedback.remove();
    } else {
        field.classList.add('is-invalid');
        
        if (!feedback) {
            const feedbackElement = document.createElement('div');
            feedbackElement.className = 'invalid-feedback';
            feedbackElement.style.cssText = `
                color: #dc3545;
                font-size: 0.875rem;
                margin-top: 0.25rem;
                display: block;
            `;
            field.parentNode.appendChild(feedbackElement);
        }
        
        const feedbackElement = field.parentNode.querySelector('.invalid-feedback');
        feedbackElement.textContent = errorMessage;
    }
    
    return isValid;
}

/**
 * Navigation mobile responsive
 */
function initializeNavigation() {
    // Créer un bouton de menu hamburger si nécessaire
    const navbar = document.querySelector('.navbar');
    const navbarNav = document.querySelector('.navbar-nav');
    
    if (navbar && navbarNav) {
        // Créer le bouton hamburger
        const toggleButton = document.createElement('button');
        toggleButton.className = 'navbar-toggle';
        toggleButton.innerHTML = '☰';
        toggleButton.style.cssText = `
            display: none;
            background: none;
            border: none;
            font-size: 1.5rem;
            color: white;
            cursor: pointer;
        `;
        
        navbar.insertBefore(toggleButton, navbarNav);
        
        // Gérer le clic sur le bouton
        toggleButton.addEventListener('click', function() {
            navbarNav.classList.toggle('active');
        });
        
        // Responsive: afficher/masquer le bouton selon la taille d'écran
        function checkScreenSize() {
            if (window.innerWidth <= 768) {
                toggleButton.style.display = 'block';
                navbarNav.style.display = navbarNav.classList.contains('active') ? 'flex' : 'none';
            } else {
                toggleButton.style.display = 'none';
                navbarNav.style.display = 'flex';
                navbarNav.classList.remove('active');
            }
        }
        
        window.addEventListener('resize', checkScreenSize);
        checkScreenSize();
    }
}

/**
 * Prévisualisation des images uploadées
 */
function initializeImagePreview() {
    const imageInputs = document.querySelectorAll('input[type="file"][accept*="image"]');
    
    imageInputs.forEach(function(input) {
        input.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    let preview = input.parentNode.querySelector('.image-preview');
                    
                    if (!preview) {
                        preview = document.createElement('img');
                        preview.className = 'image-preview';
                        preview.style.cssText = `
                            max-width: 200px;
                            max-height: 200px;
                            margin-top: 1rem;
                            border-radius: 4px;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                        `;
                        input.parentNode.appendChild(preview);
                    }
                    
                    preview.src = e.target.result;
                };
                reader.readAsDataURL(file);
            }
        });
    });
}

/**
 * Tooltips pour les boutons et liens
 */
function initializeTooltips() {
    const elements = document.querySelectorAll('[data-tooltip]');
    
    elements.forEach(function(element) {
        element.addEventListener('mouseenter', function() {
            const tooltip = document.createElement('div');
            tooltip.className = 'tooltip';
            tooltip.textContent = this.getAttribute('data-tooltip');
            tooltip.style.cssText = `
                position: absolute;
                background: #333;
                color: white;
                padding: 0.5rem;
                border-radius: 4px;
                font-size: 0.875rem;
                z-index: 1000;
                pointer-events: none;
                white-space: nowrap;
            `;
            
            document.body.appendChild(tooltip);
            
            const rect = this.getBoundingClientRect();
            tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
            tooltip.style.top = rect.top - tooltip.offsetHeight - 5 + 'px';
            
            this._tooltip = tooltip;
        });
        
        element.addEventListener('mouseleave', function() {
            if (this._tooltip) {
                this._tooltip.remove();
                this._tooltip = null;
            }
        });
    });
}

/**
 * Utilitaires généraux
 */
const Utils = {
    // Formater une date
    formatDate: function(date) {
        return new Intl.DateTimeFormat('fr-FR', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        }).format(new Date(date));
    },
    
    // Tronquer un texte
    truncateText: function(text, maxLength) {
        if (text.length <= maxLength) return text;
        return text.substr(0, maxLength) + '...';
    },
    
    // Débounce pour les fonctions
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    // Scroll fluide vers un élément
    scrollTo: function(element) {
        if (typeof element === 'string') {
            element = document.querySelector(element);
        }
        if (element) {
            element.scrollIntoView({ behavior: 'smooth' });
        }
    }
};

// Fonctions AJAX pour les interactions dynamiques
const Ajax = {
    // Requête GET simple
    get: function(url, callback) {
        fetch(url, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            }
        })
        .then(response => response.json())
        .then(data => callback(null, data))
        .catch(error => callback(error, null));
    },
    
    // Requête POST avec CSRF
    post: function(url, data, callback) {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        
        fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken ? csrfToken.value : '',
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => callback(null, data))
        .catch(error => callback(error, null));
    }
};

// Exposer les utilitaires globalement
window.Utils = Utils;
window.Ajax = Ajax;