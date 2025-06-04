from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    bio = models.TextField(_('biography'), blank=True)
    avatar = models.ImageField(_('avatar'), upload_to='avatars/', null=True, blank=True)

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
