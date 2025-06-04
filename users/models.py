from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', _('Administrateur')),
        ('auteur', _('Auteur')),
        ('visiteur', _('Visiteur')),
    ]
    
    bio = models.TextField(_('biography'), blank=True)
    avatar = models.ImageField(_('avatar'), upload_to='avatars/', null=True, blank=True)
    role = models.CharField(_('rôle'), max_length=20, choices=ROLE_CHOICES, default='visiteur')

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
    
    def is_admin(self):
        """Vérifie si l'utilisateur est un administrateur"""
        return self.role == 'admin' or self.is_superuser
    
    def is_auteur(self):
        """Vérifie si l'utilisateur est un auteur"""
        return self.role == 'auteur' or self.is_admin()
    
    def is_visiteur(self):
        """Vérifie si l'utilisateur est un visiteur"""
        return self.role == 'visiteur'
    
    def can_create_article(self):
        """Vérifie si l'utilisateur peut créer des articles"""
        return self.is_auteur() or self.is_admin()
    
    def can_edit_article(self, article):
        """Vérifie si l'utilisateur peut modifier un article"""
        if self.is_admin():
            return True
        if self.is_auteur() and article.author == self:
            return True
        return False
    
    def can_delete_article(self, article):
        """Vérifie si l'utilisateur peut supprimer un article"""
        return self.can_edit_article(article)
    
    def can_manage_categories(self):
        """Vérifie si l'utilisateur peut gérer les catégories"""
        return self.is_admin()
    
    def can_manage_tags(self):
        """Vérifie si l'utilisateur peut gérer les tags"""
        return self.is_admin()
    
    def can_moderate_comments(self):
        """Vérifie si l'utilisateur peut modérer les commentaires"""
        return self.is_admin()
    
    def can_edit_comment(self, comment):
        """Vérifie si l'utilisateur peut modifier un commentaire"""
        if self.is_admin():
            return True
        if comment.author == self:
            return True
        return False
    
    def can_delete_comment(self, comment):
        """Vérifie si l'utilisateur peut supprimer un commentaire"""
        return self.can_edit_comment(comment)
