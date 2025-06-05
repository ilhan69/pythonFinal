from django.contrib.syndication.views import Feed
from django.urls import reverse
from django.utils.feedgenerator import Rss201rev2Feed
from django.utils.translation import gettext_lazy as _, get_language
from django.conf import settings
from django.utils import translation
from .models import Article, Category, Tag


class MultilingualFeed(Feed):
    """Classe de base pour les flux RSS multilingues"""
    
    def __call__(self, request, *args, **kwargs):
        """Override pour activer la langue courante dans le flux"""
        # Récupérer la langue depuis l'URL ou utiliser la langue par défaut
        language = getattr(request, 'LANGUAGE_CODE', settings.LANGUAGE_CODE)
        
        # Activer la langue pour ce flux
        translation.activate(language)
        
        try:
            return super().__call__(request, *args, **kwargs)
        finally:
            # Revenir à la langue par défaut après génération du flux
            translation.deactivate()


class LatestArticlesFeed(MultilingualFeed):
    """Flux RSS pour les derniers articles publiés - Multilingue"""
    
    def title(self):
        return _("Derniers articles - Mon Blog")
    
    def link(self):
        return f"/{get_language()}/"
    
    def description(self):
        return _("Les derniers articles publiés sur notre blog")
    
    feed_type = Rss201rev2Feed
    
    def items(self):
        """Retourne les 20 derniers articles publiés"""
        return Article.objects.filter(status='published').order_by('-created_at')[:20]
    
    def item_title(self, item):
        """Titre de l'article"""
        return item.title
    
    def item_description(self, item):
        """Description de l'article (extrait ou début du contenu)"""
        if item.excerpt:
            return item.excerpt
        # Si pas d'extrait, prendre les 200 premiers caractères du contenu
        import re
        clean_content = re.sub('<[^<]+?>', '', item.content)
        return clean_content[:200] + '...' if len(clean_content) > 200 else clean_content
    
    def item_link(self, item):
        """Lien vers l'article avec préfixe de langue"""
        return f"/{get_language()}/article/{item.id}/"
    
    def item_pubdate(self, item):
        """Date de publication"""
        return item.created_at
    
    def item_updateddate(self, item):
        """Date de mise à jour"""
        return item.updated_at
    
    def item_author_name(self, item):
        """Nom de l'auteur"""
        return item.author.get_full_name() or item.author.username
    
    def item_author_email(self, item):
        """Email de l'auteur (optionnel)"""
        return item.author.email if hasattr(item.author, 'email') else None
    
    def item_categories(self, item):
        """Catégories de l'article"""
        categories = []
        if item.category:
            categories.append(item.category.name)
        categories.extend([tag.name for tag in item.tags.all()])
        return categories
    
    def item_guid(self, item):
        """GUID unique pour l'article"""
        return f"article-{item.id}-{item.slug}-{get_language()}"
    
    def item_guid_is_permalink(self, item):
        """Le GUID n'est pas un permalien"""
        return False


class CategoryArticlesFeed(MultilingualFeed):
    """Flux RSS pour les articles d'une catégorie spécifique - Multilingue"""
    
    def get_object(self, request, category_id):
        """Récupère la catégorie à partir de l'ID"""
        return Category.objects.get(pk=category_id)
    
    def title(self, obj):
        return _("Articles de la catégorie: {}").format(obj.name)
    
    def link(self, obj):
        return f"/{get_language()}/category/{obj.id}/"
    
    def description(self, obj):
        return _("Les derniers articles de la catégorie {}").format(obj.name)
    
    def items(self, obj):
        """Retourne les 20 derniers articles de la catégorie"""
        return Article.objects.filter(
            category=obj, 
            status='published'
        ).order_by('-created_at')[:20]
    
    def item_title(self, item):
        return item.title
    
    def item_description(self, item):
        if item.excerpt:
            return item.excerpt
        import re
        clean_content = re.sub('<[^<]+?>', '', item.content)
        return clean_content[:200] + '...' if len(clean_content) > 200 else clean_content
    
    def item_link(self, item):
        return f"/{get_language()}/article/{item.id}/"
    
    def item_pubdate(self, item):
        return item.created_at
    
    def item_updateddate(self, item):
        return item.updated_at
    
    def item_author_name(self, item):
        return item.author.get_full_name() or item.author.username
    
    def item_categories(self, item):
        categories = []
        if item.category:
            categories.append(item.category.name)
        categories.extend([tag.name for tag in item.tags.all()])
        return categories
    
    def item_guid(self, item):
        return f"article-{item.id}-{item.slug}-{get_language()}"


class TagArticlesFeed(MultilingualFeed):
    """Flux RSS pour les articles d'un tag spécifique - Multilingue"""
    
    def get_object(self, request, tag_slug):
        """Récupère le tag à partir du slug"""
        return Tag.objects.get(slug=tag_slug)
    
    def title(self, obj):
        return _("Articles avec le tag: {}").format(obj.name)
    
    def link(self, obj):
        return f"/{get_language()}/tag/{obj.slug}/"
    
    def description(self, obj):
        return _("Les derniers articles avec le tag {}").format(obj.name)
    
    def items(self, obj):
        """Retourne les 20 derniers articles avec ce tag"""
        return Article.objects.filter(
            tags=obj, 
            status='published'
        ).order_by('-created_at')[:20]
    
    def item_title(self, item):
        return item.title
    
    def item_description(self, item):
        if item.excerpt:
            return item.excerpt
        import re
        clean_content = re.sub('<[^<]+?>', '', item.content)
        return clean_content[:200] + '...' if len(clean_content) > 200 else clean_content
    
    def item_link(self, item):
        return f"/{get_language()}/article/{item.id}/"
    
    def item_pubdate(self, item):
        return item.created_at
    
    def item_updateddate(self, item):
        return item.updated_at
    
    def item_author_name(self, item):
        return item.author.get_full_name() or item.author.username
    
    def item_categories(self, item):
        categories = []
        if item.category:
            categories.append(item.category.name)
        categories.extend([tag.name for tag in item.tags.all()])
        return categories
    
    def item_guid(self, item):
        return f"article-{item.id}-{item.slug}-{get_language()}"