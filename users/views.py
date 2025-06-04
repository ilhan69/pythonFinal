from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext as _
from django.core.paginator import Paginator
from django.db.models import Q
from .forms import UserRegistrationForm, UserLoginForm, UserProfileForm, AdminUserForm, UserPasswordChangeForm, AdminUserCreationForm, AdminPasswordResetForm
from .models import User
from .decorators import admin_required
from pythonFinal.logging_utils import (
    log_auth_event, log_admin_action, log_security_event, 
    log_error, log_view_access
)

@log_view_access('users')
def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                user = form.save()
                login(request, user)
                
                # Log de l'inscription réussie
                log_auth_event(request, 'INSCRIPTION', user.username, success=True, 
                              extra_info=f"Nouveau compte créé avec le rôle {user.role}")
                
                messages.success(request, _('Votre compte a été créé avec succès !'))
                return redirect('blog:home')
            except Exception as e:
                log_error(request, e, "Erreur lors de l'inscription")
                messages.error(request, _('Une erreur est survenue lors de la création du compte.'))
        else:
            # Log des tentatives d'inscription échouées
            username = form.data.get('username', 'N/A')
            log_auth_event(request, 'INSCRIPTION', username, success=False, 
                          extra_info="Erreurs de validation du formulaire")
            messages.error(request, _('Veuillez corriger les erreurs dans le formulaire.'))
    else:
        form = UserRegistrationForm()
    return render(request, 'users/register.html', {'form': form})

@log_view_access('users')
def user_login(request):
    if request.method == 'POST':
        form = UserLoginForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    
                    # Log de la connexion réussie
                    log_auth_event(request, 'CONNEXION', username, success=True,
                                  extra_info=f"Rôle: {user.role}")
                    
                    messages.success(request, _('Vous êtes maintenant connecté !'))
                    return redirect('blog:home')
                else:
                    # Log de tentative de connexion avec compte désactivé
                    log_security_event(request, 'TENTATIVE_CONNEXION_COMPTE_DESACTIVE', 'WARNING',
                                     f"Utilisateur: {username}")
                    messages.error(request, _('Votre compte est désactivé.'))
            else:
                # Log de tentative de connexion échouée
                log_auth_event(request, 'CONNEXION', username, success=False,
                              extra_info="Identifiants incorrects")
                log_security_event(request, 'TENTATIVE_CONNEXION_ECHOUEE', 'WARNING',
                                 f"Utilisateur: {username}")
                messages.error(request, _('Nom d\'utilisateur ou mot de passe incorrect.'))
        else:
            # Log des erreurs de formulaire de connexion
            username = form.data.get('username', 'N/A')
            log_auth_event(request, 'CONNEXION', username, success=False,
                          extra_info="Erreurs de validation du formulaire")
            messages.error(request, _('Veuillez corriger les erreurs dans le formulaire.'))
    else:
        form = UserLoginForm()
    return render(request, 'users/login.html', {'form': form})

@login_required
@log_view_access('users')
def user_logout(request):
    username = request.user.username
    
    # Log de la déconnexion
    log_auth_event(request, 'DECONNEXION', username, success=True)
    
    logout(request)
    messages.success(request, _('Vous avez été déconnecté avec succès !'))
    return redirect('blog:home')

@login_required
@log_view_access('users')
def profile(request):
    """Vue pour afficher et modifier le profil utilisateur"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            try:
                form.save()
                
                # Log de la modification de profil
                log_auth_event(request, 'MODIFICATION_PROFIL', request.user.username, 
                              success=True, extra_info="Profil mis à jour")
                
                messages.success(request, _('Votre profil a été mis à jour avec succès !'))
                return redirect('users:profile')
            except Exception as e:
                log_error(request, e, "Erreur lors de la modification du profil")
                messages.error(request, _('Une erreur est survenue lors de la modification.'))
        else:
            # Log des erreurs de modification de profil
            log_auth_event(request, 'MODIFICATION_PROFIL', request.user.username, 
                          success=False, extra_info="Erreurs de validation")
            messages.error(request, _('Veuillez corriger les erreurs ci-dessous.'))
    else:
        form = UserProfileForm(instance=request.user)
    
    # Récupérer les articles de l'utilisateur avec statistiques
    user_posts = request.user.articles.all().order_by('-created_at')

    # Articles favoris (likés)
    from stats.models import Like
    from django.contrib.contenttypes.models import ContentType
    from blog.models import Article
    
    article_ct = ContentType.objects.get_for_model(Article)
    liked_article_ids = Like.objects.filter(
        user=request.user,
        content_type=article_ct
    ).values_list('object_id', flat=True)
    favoris = Article.objects.filter(id__in=liked_article_ids).distinct().order_by('-created_at')

    # Statistiques utilisateur
    total_articles = user_posts.count()
    published_articles = user_posts.filter(status='published').count()
    draft_articles = user_posts.filter(status='draft').count()
    total_views = sum(post.views_count for post in user_posts)
    total_likes = sum(post.likes_count for post in user_posts)
    
    return render(request, 'users/profile.html', {
        'user': request.user,
        'posts': user_posts,
        'favoris': favoris,
        'form': form,
        'stats': {
            'total_articles': total_articles,
            'published_articles': published_articles,
            'draft_articles': draft_articles,
            'total_views': total_views,
            'total_likes': total_likes,
        }
    })

@admin_required
@log_view_access('users')
def manage_users(request):
    """Vue pour que les administrateurs gèrent les utilisateurs"""
    # Log de l'accès à la gestion des utilisateurs
    log_admin_action(request, "ACCES_GESTION_UTILISATEURS")
    
    search_query = request.GET.get('search', '').strip()
    role_filter = request.GET.get('role', '')
    
    users = User.objects.all().order_by('-date_joined')
    
    # Filtrage par recherche
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    # Filtrage par rôle
    if role_filter and role_filter in ['admin', 'auteur', 'visiteur']:
        users = users.filter(role=role_filter)
    
    # Pagination
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques
    stats = {
        'total_users': User.objects.count(),
        'admin_count': User.objects.filter(role='admin').count(),
        'auteur_count': User.objects.filter(role='auteur').count(),
        'visiteur_count': User.objects.filter(role='visiteur').count(),
        'active_users': User.objects.filter(is_active=True).count(),
    }
    
    return render(request, 'users/manage_users.html', {
        'page_obj': page_obj,
        'users': page_obj.object_list,
        'search_query': search_query,
        'role_filter': role_filter,
        'stats': stats,
        'role_choices': User.ROLE_CHOICES,
    })

@admin_required
@log_view_access('users')
def edit_user(request, user_id):
    """Vue pour modifier un utilisateur"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        form = AdminUserForm(request.POST, instance=user)
        if form.is_valid():
            try:
                # Sauvegarder les changements précédents pour le log
                old_role = user.role
                old_active = user.is_active
                
                form.save()
                
                # Log de la modification utilisateur
                changes = []
                if user.role != old_role:
                    changes.append(f"Rôle: {old_role} -> {user.role}")
                if user.is_active != old_active:
                    changes.append(f"Statut: {'actif' if old_active else 'inactif'} -> {'actif' if user.is_active else 'inactif'}")
                
                log_admin_action(request, "MODIFICATION_UTILISATEUR", f"Utilisateur {user.username}",
                               f"Changements: {', '.join(changes) if changes else 'Informations générales'}")
                
                messages.success(request, _('Utilisateur modifié avec succès !'))
                return redirect('users:manage_users')
            except Exception as e:
                log_error(request, e, f"Erreur lors de la modification de l'utilisateur {user.username}")
                messages.error(request, _('Une erreur est survenue lors de la modification.'))
        else:
            log_admin_action(request, "ECHEC_MODIFICATION_UTILISATEUR", f"Utilisateur {user.username}",
                           "Erreurs de validation du formulaire")
            messages.error(request, _('Veuillez corriger les erreurs dans le formulaire.'))
    else:
        form = AdminUserForm(instance=user)
    
    return render(request, 'users/edit_user.html', {
        'form': form,
        'user_to_edit': user,
    })

@admin_required
@log_view_access('users')
def toggle_user_status(request, user_id):
    """Vue pour activer/désactiver un utilisateur"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        old_status = user.is_active
        user.is_active = not user.is_active
        user.save()
        
        # Log de l'action de changement de statut
        action = "ACTIVATION_UTILISATEUR" if user.is_active else "DESACTIVATION_UTILISATEUR"
        log_admin_action(request, action, f"Utilisateur {user.username}",
                        f"Statut changé: {'inactif' if old_status else 'actif'} -> {'actif' if user.is_active else 'inactif'}")
        
        # Log de sécurité pour les désactivations
        if not user.is_active:
            log_security_event(request, 'DESACTIVATION_COMPTE', 'WARNING',
                             f"Compte {user.username} désactivé par admin")
        
        status = _('activé') if user.is_active else _('désactivé')
        messages.success(request, _('Utilisateur %(username)s %(status)s avec succès !') % {
            'username': user.username,
            'status': status
        })
    
    return redirect('users:manage_users')

@admin_required
@log_view_access('users')
def delete_user(request, user_id):
    """Vue pour supprimer un utilisateur"""
    user = get_object_or_404(User, id=user_id)
    
    # Empêcher la suppression de son propre compte
    if user == request.user:
        log_security_event(request, 'TENTATIVE_SUPPRESSION_PROPRE_COMPTE', 'WARNING',
                         f"Admin {request.user.username} a tenté de supprimer son propre compte")
        messages.error(request, _('Vous ne pouvez pas supprimer votre propre compte.'))
        return redirect('users:manage_users')
    
    if request.method == 'POST':
        username = user.username
        user_role = user.role
        
        try:
            user.delete()
            
            # Log de la suppression d'utilisateur
            log_admin_action(request, "SUPPRESSION_UTILISATEUR", f"Utilisateur {username}",
                           f"Rôle supprimé: {user_role}")
            log_security_event(request, 'SUPPRESSION_COMPTE', 'ERROR',
                             f"Compte {username} (rôle: {user_role}) supprimé par admin")
            
            messages.success(request, _('Utilisateur %(username)s supprimé avec succès !') % {
                'username': username
            })
            return redirect('users:manage_users')
        except Exception as e:
            log_error(request, e, f"Erreur lors de la suppression de l'utilisateur {username}")
            messages.error(request, _('Une erreur est survenue lors de la suppression.'))
    
    return render(request, 'users/delete_user.html', {'user_to_delete': user})

@login_required
@log_view_access('users')
def change_password(request):
    """Vue pour changer le mot de passe de l'utilisateur connecté"""
    if request.method == 'POST':
        form = UserPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            try:
                user = form.save()
                # Important: maintenir la session après changement de mot de passe
                update_session_auth_hash(request, user)
                
                # Log du changement de mot de passe
                log_auth_event(request, 'CHANGEMENT_MOT_DE_PASSE', user.username, success=True)
                log_security_event(request, 'CHANGEMENT_MOT_DE_PASSE_UTILISATEUR', 'INFO',
                                 f"Utilisateur {user.username} a changé son mot de passe")
                
                messages.success(request, _('Votre mot de passe a été modifié avec succès !'))
                return redirect('users:profile')
            except Exception as e:
                log_error(request, e, f"Erreur lors du changement de mot de passe pour {request.user.username}")
                messages.error(request, _('Une erreur est survenue lors du changement de mot de passe.'))
        else:
            log_auth_event(request, 'CHANGEMENT_MOT_DE_PASSE', request.user.username, success=False,
                          extra_info="Erreurs de validation")
            messages.error(request, _('Veuillez corriger les erreurs ci-dessous.'))
    else:
        form = UserPasswordChangeForm(user=request.user)
    
    return render(request, 'users/change_password.html', {'form': form})

@admin_required
@log_view_access('users')
def add_user(request):
    """Vue pour ajouter un nouvel utilisateur"""
    if request.method == 'POST':
        form = AdminUserCreationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                
                # Log de la création d'utilisateur par admin
                log_admin_action(request, "CREATION_UTILISATEUR", f"Utilisateur {user.username}",
                               f"Nouveau compte créé avec le rôle {user.role}")
                
                messages.success(request, _('Utilisateur %(username)s créé avec succès !') % {
                    'username': user.username
                })
                return redirect('users:manage_users')
            except Exception as e:
                log_error(request, e, "Erreur lors de la création d'utilisateur par admin")
                messages.error(request, _('Une erreur est survenue lors de la création.'))
        else:
            username = form.data.get('username', 'N/A')
            log_admin_action(request, "ECHEC_CREATION_UTILISATEUR", f"Tentative pour {username}",
                           "Erreurs de validation du formulaire")
            messages.error(request, _('Veuillez corriger les erreurs dans le formulaire.'))
    else:
        form = AdminUserCreationForm()
    
    return render(request, 'users/add_user.html', {'form': form})

@admin_required
@log_view_access('users')
def admin_change_password(request, user_id):
    """Vue pour qu'un administrateur change le mot de passe d'un utilisateur"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        form = AdminPasswordResetForm(user=user, data=request.POST)
        if form.is_valid():
            try:
                form.save()
                
                # Log du changement de mot de passe par admin
                log_admin_action(request, "RESET_MOT_DE_PASSE", f"Utilisateur {user.username}",
                               "Mot de passe réinitialisé par administrateur")
                log_security_event(request, 'RESET_MOT_DE_PASSE_PAR_ADMIN', 'WARNING',
                                 f"Mot de passe de {user.username} réinitialisé par admin")
                
                messages.success(request, _('Mot de passe de %(username)s modifié avec succès !') % {
                    'username': user.username
                })
                return redirect('users:manage_users')
            except Exception as e:
                log_error(request, e, f"Erreur lors du reset de mot de passe pour {user.username}")
                messages.error(request, _('Une erreur est survenue lors de la modification.'))
        else:
            log_admin_action(request, "ECHEC_RESET_MOT_DE_PASSE", f"Utilisateur {user.username}",
                           "Erreurs de validation du formulaire")
            messages.error(request, _('Veuillez corriger les erreurs ci-dessous.'))
    else:
        form = AdminPasswordResetForm(user=user)
    
    return render(request, 'users/admin_change_password.html', {
        'form': form,
        'user_to_edit': user
    })
