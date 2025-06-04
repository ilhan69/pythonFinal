from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.translation import gettext as _
from django.http import Http404


def admin_required(view_func):
    """Décorateur pour les vues nécessitant un rôle admin"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, _('Vous devez être connecté pour accéder à cette page.'))
            return redirect('users:login')
        
        if not request.user.is_admin():
            messages.error(request, _('Vous n\'avez pas les permissions nécessaires pour accéder à cette page.'))
            return redirect('blog:home')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def auteur_required(view_func):
    """Décorateur pour les vues nécessitant un rôle auteur ou admin"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, _('Vous devez être connecté pour accéder à cette page.'))
            return redirect('users:login')
        
        if not request.user.can_create_article():
            messages.error(request, _('Vous devez être auteur ou administrateur pour accéder à cette page.'))
            return redirect('blog:home')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def article_owner_required(view_func):
    """Décorateur pour les vues nécessitant d'être propriétaire de l'article ou admin"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, _('Vous devez être connecté pour accéder à cette page.'))
            return redirect('users:login')
        
        # Récupérer l'article pour vérifier les permissions
        from blog.models import Article
        from django.shortcuts import get_object_or_404
        
        article_id = kwargs.get('article_id')
        if article_id:
            article = get_object_or_404(Article, id=article_id)
            if not request.user.can_edit_article(article):
                messages.error(request, _('Vous n\'avez pas les permissions pour modifier cet article.'))
                return redirect('blog:home')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def comment_owner_required(view_func):
    """Décorateur pour les vues nécessitant d'être propriétaire du commentaire ou admin"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, _('Vous devez être connecté pour accéder à cette page.'))
            return redirect('users:login')
        
        # Récupérer le commentaire pour vérifier les permissions
        from comments.models import Comment
        from django.shortcuts import get_object_or_404
        
        comment_id = kwargs.get('comment_id')
        if comment_id:
            comment = get_object_or_404(Comment, id=comment_id)
            if not request.user.can_edit_comment(comment):
                messages.error(request, _('Vous n\'avez pas les permissions pour modifier ce commentaire.'))
                return redirect('blog:home')
        
        return view_func(request, *args, **kwargs)
    return wrapper