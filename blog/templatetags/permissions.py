from django import template
from django.contrib.auth import get_user_model

register = template.Library()

User = get_user_model()

@register.filter
def can_edit_article(user, article):
    """Vérifie si l'utilisateur peut modifier un article"""
    if not user.is_authenticated:
        return False
    return user.can_edit_article(article)

@register.filter
def can_delete_article(user, article):
    """Vérifie si l'utilisateur peut supprimer un article"""
    if not user.is_authenticated:
        return False
    return user.can_delete_article(article)

@register.filter
def can_edit_comment(user, comment):
    """Vérifie si l'utilisateur peut modifier un commentaire"""
    if not user.is_authenticated:
        return False
    return user.can_edit_comment(comment)

@register.filter
def can_delete_comment(user, comment):
    """Vérifie si l'utilisateur peut supprimer un commentaire"""
    if not user.is_authenticated:
        return False
    return user.can_delete_comment(comment)

@register.simple_tag
def user_can_create_article(user):
    """Vérifie si l'utilisateur peut créer des articles"""
    if not user.is_authenticated:
        return False
    return user.can_create_article()

@register.simple_tag
def user_can_manage_categories(user):
    """Vérifie si l'utilisateur peut gérer les catégories"""
    if not user.is_authenticated:
        return False
    return user.can_manage_categories()

@register.simple_tag
def user_can_manage_tags(user):
    """Vérifie si l'utilisateur peut gérer les tags"""
    if not user.is_authenticated:
        return False
    return user.can_manage_tags()

@register.simple_tag
def user_is_admin(user):
    """Vérifie si l'utilisateur est un administrateur"""
    if not user.is_authenticated:
        return False
    return user.is_admin()

@register.simple_tag
def user_is_auteur(user):
    """Vérifie si l'utilisateur est un auteur"""
    if not user.is_authenticated:
        return False
    return user.is_auteur()