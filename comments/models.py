from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class Comment(models.Model):
    content = models.TextField(_('contenu'))
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments', verbose_name=_('auteur'))
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('modifié le'), auto_now=True)
    is_active = models.BooleanField(_('actif'), default=True)

    # Champs génériques pour permettre les commentaires sur différents modèles
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        verbose_name = _('commentaire')
        verbose_name_plural = _('commentaires')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f'Commentaire de {self.author.username} sur {self.content_object}'
