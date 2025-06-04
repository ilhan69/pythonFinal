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

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, _('Votre compte a été créé avec succès !'))
            return redirect('blog:home')
        else:
            messages.error(request, _('Veuillez corriger les erreurs dans le formulaire.'))
    else:
        form = UserRegistrationForm()
    return render(request, 'users/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = UserLoginForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, _('Vous êtes maintenant connecté !'))
                return redirect('blog:home')
            else:
                messages.error(request, _('Nom d\'utilisateur ou mot de passe incorrect.'))
        else:
            messages.error(request, _('Veuillez corriger les erreurs dans le formulaire.'))
    else:
        form = UserLoginForm()
    return render(request, 'users/login.html', {'form': form})

@login_required
def user_logout(request):
    logout(request)
    messages.success(request, _('Vous avez été déconnecté avec succès !'))
    return redirect('blog:home')

@login_required
def profile(request):
    """Vue pour afficher et modifier le profil utilisateur"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _('Votre profil a été mis à jour avec succès !'))
            return redirect('users:profile')
        else:
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
def manage_users(request):
    """Vue pour que les administrateurs gèrent les utilisateurs"""
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
def edit_user(request, user_id):
    """Vue pour modifier un utilisateur"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        form = AdminUserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, _('Utilisateur modifié avec succès !'))
            return redirect('users:manage_users')
        else:
            messages.error(request, _('Veuillez corriger les erreurs dans le formulaire.'))
    else:
        form = AdminUserForm(instance=user)
    
    return render(request, 'users/edit_user.html', {
        'form': form,
        'user_to_edit': user,
    })

@admin_required
def toggle_user_status(request, user_id):
    """Vue pour activer/désactiver un utilisateur"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        user.is_active = not user.is_active
        user.save()
        
        status = _('activé') if user.is_active else _('désactivé')
        messages.success(request, _('Utilisateur %(username)s %(status)s avec succès !') % {
            'username': user.username,
            'status': status
        })
    
    return redirect('users:manage_users')

@admin_required
def delete_user(request, user_id):
    """Vue pour supprimer un utilisateur"""
    user = get_object_or_404(User, id=user_id)
    
    # Empêcher la suppression de son propre compte
    if user == request.user:
        messages.error(request, _('Vous ne pouvez pas supprimer votre propre compte.'))
        return redirect('users:manage_users')
    
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, _('Utilisateur %(username)s supprimé avec succès !') % {
            'username': username
        })
        return redirect('users:manage_users')
    
    return render(request, 'users/delete_user.html', {'user_to_delete': user})

@login_required
def change_password(request):
    """Vue pour changer le mot de passe de l'utilisateur connecté"""
    if request.method == 'POST':
        form = UserPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            # Important: maintenir la session après changement de mot de passe
            update_session_auth_hash(request, user)
            messages.success(request, _('Votre mot de passe a été modifié avec succès !'))
            return redirect('users:profile')
        else:
            messages.error(request, _('Veuillez corriger les erreurs ci-dessous.'))
    else:
        form = UserPasswordChangeForm(user=request.user)
    
    return render(request, 'users/change_password.html', {'form': form})

@admin_required
def add_user(request):
    """Vue pour ajouter un nouvel utilisateur"""
    if request.method == 'POST':
        form = AdminUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, _('Utilisateur %(username)s créé avec succès !') % {
                'username': user.username
            })
            return redirect('users:manage_users')
        else:
            messages.error(request, _('Veuillez corriger les erreurs dans le formulaire.'))
    else:
        form = AdminUserCreationForm()
    
    return render(request, 'users/add_user.html', {'form': form})

@admin_required
def admin_change_password(request, user_id):
    """Vue pour qu'un administrateur change le mot de passe d'un utilisateur"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        form = AdminPasswordResetForm(user=user, data=request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _('Mot de passe de %(username)s modifié avec succès !') % {
                'username': user.username
            })
            return redirect('users:manage_users')
        else:
            messages.error(request, _('Veuillez corriger les erreurs ci-dessous.'))
    else:
        form = AdminPasswordResetForm(user=user)
    
    return render(request, 'users/admin_change_password.html', {
        'form': form,
        'user_to_edit': user
    })
