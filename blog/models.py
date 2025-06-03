from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils.text import slugify

# Create your models here.
class User(AbstractUser):
    bio = models.TextField(_('biography'), blank=True)
    avatar = models.ImageField(_('avatar'), upload_to='avatars/', null=True, blank=True)

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

class Category(models.Model):
    name = models.CharField(_('nom'), max_length=100, unique=True)
    description = models.TextField(_('description'), blank=True)
    slug = models.SlugField(_('slug'), max_length=100, unique=True, blank=True)
    couleur = models.CharField(_('couleur'), max_length=7, default='#007bff', help_text=_('Code couleur hexadécimal (ex: #007bff)'))
    icone = models.CharField(_('icône'), max_length=50, blank=True, help_text=_('Nom de l\'icône (ex: fas fa-tag)'))
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        """Génère automatiquement le slug à partir du nom si non fourni"""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """Retourne l'URL absolue de la catégorie"""
        return reverse('category_posts', kwargs={'category_id': self.pk})

    def get_articles_count(self):
        """Retourne le nombre d'articles dans cette catégorie"""
        return self.articles.count()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('catégorie')
        verbose_name_plural = _('catégories')
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(fields=['name'], name='unique_category_name'),
            models.UniqueConstraint(fields=['slug'], name='unique_category_slug'),
        ]

class Tag(models.Model):
    name = models.CharField(_('nom'), max_length=50, unique=True)
    slug = models.SlugField(_('slug'), max_length=50, unique=True, blank=True)
    couleur = models.CharField(_('couleur'), max_length=7, default='#6c757d', help_text=_('Code couleur hexadécimal (ex: #6c757d)'))
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        """Génère automatiquement le slug à partir du nom si non fourni"""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """Retourne l'URL absolue du tag"""
        return reverse('tag_posts', kwargs={'tag_slug': self.slug})

    def get_articles_count(self):
        """Retourne le nombre d'articles avec ce tag"""
        return self.articles.count()

    @classmethod
    def get_popular_tags(cls, limit=10):
        """Retourne les tags les plus populaires (avec le plus d'articles)"""
        from django.db.models import Count
        return cls.objects.annotate(
            articles_count=Count('articles')
        ).filter(articles_count__gt=0).order_by('-articles_count')[:limit]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('tag')
        verbose_name_plural = _('tags')
        ordering = ['name']

class Article(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    cover_image = models.ImageField(_('image de couverture'), upload_to='articles/covers/', null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='articles')
    tags = models.ManyToManyField(Tag, related_name='articles', blank=True, verbose_name=_('tags'))
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='articles')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def has_cover_image(self):
        """Retourne True si l'article a une image de couverture"""
        return bool(self.cover_image)

    def get_cover_image_url(self):
        """Retourne l'URL de l'image de couverture ou None"""
        if self.cover_image:
            return self.cover_image.url
        return None

    class Meta:
        ordering = ['-created_at']  # Order articles by creation date, newest first

class ArticleComment(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Comment by {self.author.username} on {self.article.title}'

    class Meta:
        ordering = ['-created_at']
