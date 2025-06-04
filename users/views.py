from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext as _
from .forms import UserRegistrationForm, UserLoginForm, UserProfileForm
from .models import User

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
