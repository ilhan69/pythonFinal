from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class Like(models.Model):
    """Modèle pour gérer les likes sur différents objets"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Champs génériques pour permettre les likes sur différents modèles
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        unique_together = ('user', 'content_type', 'object_id')
        verbose_name = _('like')
        verbose_name_plural = _('likes')
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f'{self.user.username} likes {self.content_object}'

class Share(models.Model):
    """Modèle pour suivre les partages d'objets"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shares', null=True, blank=True)
    shared_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Champs génériques pour permettre les partages sur différents modèles
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        verbose_name = _('partage')
        verbose_name_plural = _('partages')
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['-shared_at']),
        ]

    def __str__(self):
        if self.user:
            return f'{self.user.username} shared {self.content_object}'
        return f'Anonymous shared {self.content_object}'

class View(models.Model):
    """Modèle pour suivre les vues d'objets"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='views', null=True, blank=True)
    viewed_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Champs génériques pour permettre les vues sur différents modèles
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        verbose_name = _('vue')
        verbose_name_plural = _('vues')
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['-viewed_at']),
        ]

    def __str__(self):
        if self.user:
            return f'{self.user.username} viewed {self.content_object}'
        return f'Anonymous viewed {self.content_object}'
