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
    STATUS_CHOICES = [
        ('draft', _('Brouillon')),
        ('published', _('Publié')),
        ('archived', _('Archivé')),
    ]
    
    title = models.CharField(_('titre'), max_length=200)
    slug = models.SlugField(_('slug'), max_length=200, unique=True, blank=True)
    content = models.TextField(_('contenu'))
    excerpt = models.TextField(_('extrait'), max_length=300, blank=True, help_text=_('Résumé de l\'article (max 300 caractères)'))
    
    # Relations
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='articles', verbose_name=_('auteur'))
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='articles', verbose_name=_('catégorie'))
    tags = models.ManyToManyField(Tag, related_name='articles', blank=True, verbose_name=_('tags'))
    
    # Statut et publication
    status = models.CharField(_('statut'), max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Médias
    cover_image = models.ImageField(_('image de couverture'), upload_to='articles/covers/', null=True, blank=True)
    
    # Dates
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('modifié le'), auto_now=True)
    
    # Compteurs
    views_count = models.PositiveIntegerField(_('nombre de vues'), default=0)
    likes_count = models.PositiveIntegerField(_('nombre de likes'), default=0)
    shares_count = models.PositiveIntegerField(_('nombre de partages'), default=0)
    
    # Meta SEO
    meta_title = models.CharField(_('titre SEO'), max_length=60, blank=True, help_text=_('Titre pour le référencement (max 60 caractères)'))
    meta_description = models.CharField(_('description SEO'), max_length=160, blank=True, help_text=_('Description pour le référencement (max 160 caractères)'))

    def save(self, *args, **kwargs):
        """Génère automatiquement le slug à partir du titre si non fourni"""
        if not self.slug:
            self.slug = slugify(self.title)
        
        # Génère l'extrait automatiquement s'il est vide
        if not self.excerpt and self.content:
            # Prendre les 250 premiers caractères du contenu (sans HTML)
            import re
            clean_content = re.sub('<[^<]+?>', '', self.content)
            self.excerpt = clean_content[:250] + '...' if len(clean_content) > 250 else clean_content
        
        # Génère le meta_title s'il est vide
        if not self.meta_title:
            self.meta_title = self.title[:60]
        
        # Génère la meta_description s'elle est vide
        if not self.meta_description:
            self.meta_description = self.excerpt[:160] if self.excerpt else self.title
        
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """Retourne l'URL absolue de l'article"""
        return reverse('article_detail', kwargs={'slug': self.slug})

    def increment_views(self):
        """Incrémente le compteur de vues"""
        self.views_count += 1
        self.save(update_fields=['views_count'])

    def increment_likes(self):
        """Incrémente le compteur de likes"""
        self.likes_count += 1
        self.save(update_fields=['likes_count'])

    def increment_shares(self):
        """Incrémente le compteur de partages"""
        self.shares_count += 1
        self.save(update_fields=['shares_count'])

    def is_published(self):
        """Retourne True si l'article est publié"""
        return self.status == 'published'

    def get_reading_time(self):
        """Estime le temps de lecture en minutes"""
        word_count = len(self.content.split())
        return max(1, round(word_count / 200))  # Environ 200 mots par minute

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
        ordering = ['-created_at']
        verbose_name = _('article')
        verbose_name_plural = _('articles')
        constraints = [
            models.UniqueConstraint(fields=['slug'], name='unique_article_slug'),
        ]

class ArticleComment(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Comment by {self.author.username} on {self.article.title}'

    class Meta:
        ordering = ['-created_at']

class ArticleLike(models.Model):
    """Modèle pour gérer les likes individuels des utilisateurs"""
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='user_likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='liked_articles')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('article', 'user')  # Un utilisateur ne peut liker qu'une fois un article
        verbose_name = 'Like'
        verbose_name_plural = 'Likes'

    def __str__(self):
        return f'{self.user.username} likes {self.article.title}'

class ArticleShare(models.Model):
    """Modèle pour suivre les partages d'articles"""
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='user_shares')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shared_articles', null=True, blank=True)
    shared_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Partage'
        verbose_name_plural = 'Partages'

    def __str__(self):
        if self.user:
            return f'{self.user.username} shared {self.article.title}'
        return f'Anonymous shared {self.article.title}'
