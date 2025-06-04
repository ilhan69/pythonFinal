from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm, SetPasswordForm
from django.utils.translation import gettext_lazy as _
from .models import User

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    bio = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    avatar = forms.ImageField(required=False)
    role = forms.ChoiceField(
        choices=[('visiteur', _('Visiteur')), ('auteur', _('Auteur'))],
        initial='visiteur',
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text=_('Les visiteurs peuvent uniquement lire le contenu. Les auteurs peuvent créer des articles.')
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'role', 'bio', 'avatar']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})

class UserLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

class UserProfileForm(forms.ModelForm):
    """Formulaire pour modifier le profil utilisateur"""
    class Meta:
        model = User
        fields = ['username', 'email', 'bio', 'avatar', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom d\'utilisateur'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Adresse email'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Prénom'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom de famille'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Parlez-nous de vous...'
            }),
            'avatar': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['bio'].required = False
        self.fields['avatar'].required = False
        self.fields['first_name'].required = False
        self.fields['last_name'].required = False

class AdminUserForm(forms.ModelForm):
    """Formulaire pour que les administrateurs puissent modifier les rôles des utilisateurs"""
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'bio']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['bio'].required = False
        self.fields['first_name'].required = False
        self.fields['last_name'].required = False

class UserPasswordChangeForm(PasswordChangeForm):
    """Formulaire personnalisé pour changer le mot de passe"""
    old_password = forms.CharField(
        label=_('Mot de passe actuel'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Votre mot de passe actuel'
        })
    )
    new_password1 = forms.CharField(
        label=_('Nouveau mot de passe'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nouveau mot de passe'
        }),
        help_text=_('Votre mot de passe doit contenir au moins 8 caractères.')
    )
    new_password2 = forms.CharField(
        label=_('Confirmation du nouveau mot de passe'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirmez votre nouveau mot de passe'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personnalisation des messages d'erreur
        self.fields['old_password'].error_messages = {
            'required': _('Veuillez saisir votre mot de passe actuel.'),
        }
        self.fields['new_password1'].error_messages = {
            'required': _('Veuillez saisir un nouveau mot de passe.'),
        }
        self.fields['new_password2'].error_messages = {
            'required': _('Veuillez confirmer votre nouveau mot de passe.'),
        }

class AdminUserCreationForm(UserCreationForm):
    """Formulaire pour que les administrateurs créent de nouveaux utilisateurs"""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    first_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    role = forms.ChoiceField(
        choices=User.ROLE_CHOICES,
        initial='visiteur',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    bio = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'role', 'bio']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})

class AdminPasswordResetForm(SetPasswordForm):
    """Formulaire pour que les administrateurs changent le mot de passe d'un utilisateur"""
    new_password1 = forms.CharField(
        label=_('Nouveau mot de passe'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nouveau mot de passe'
        }),
        help_text=_('Le mot de passe doit contenir au moins 8 caractères.')
    )
    new_password2 = forms.CharField(
        label=_('Confirmation du nouveau mot de passe'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirmez le nouveau mot de passe'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personnalisation des messages d'erreur
        self.fields['new_password1'].error_messages = {
            'required': _('Veuillez saisir un nouveau mot de passe.'),
        }
        self.fields['new_password2'].error_messages = {
            'required': _('Veuillez confirmer le nouveau mot de passe.'),
        }