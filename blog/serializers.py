import json
from django.core.serializers.json import DjangoJSONEncoder
from django.forms.models import model_to_dict
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from .models import Article, Category, Tag
from comments.models import Comment
from stats.models import Like


class APISerializer:
    """Serializer de base pour l'API"""
    
    @staticmethod
    def serialize_model(instance, fields=None, exclude=None):
        """Sérialise un modèle Django en dictionnaire"""
        if not instance:
            return None
            
        data = model_to_dict(instance)
        
        # Gestion des champs spéciaux
        if hasattr(instance, 'created_at'):
            data['created_at'] = instance.created_at.isoformat() if instance.created_at else None
        if hasattr(instance, 'updated_at'):
            data['updated_at'] = instance.updated_at.isoformat() if instance.updated_at else None
        
        # Filtrer les champs si spécifié
        if fields:
            data = {k: v for k, v in data.items() if k in fields}
        if exclude:
            data = {k: v for k, v in data.items() if k not in exclude}
            
        return data
    
    @staticmethod
    def serialize_queryset(queryset, fields=None, exclude=None):
        """Sérialise un queryset en liste de dictionnaires"""
        return [APISerializer.serialize_model(item, fields, exclude) for item in queryset]


class ArticleSerializer(APISerializer):
    """Serializer pour les articles"""
    
    @classmethod
    def serialize(cls, article, include_content=True, user=None):
        """Sérialise un article avec ses relations"""
        if not article:
            return None
            
        data = {
            'id': article.id,
            'title': article.title,
            'slug': article.slug,
            'excerpt': article.excerpt,
            'status': article.status,
            'views_count': article.views_count,
            'likes_count': article.likes_count,
            'shares_count': article.shares_count,
            'created_at': article.created_at.isoformat(),
            'updated_at': article.updated_at.isoformat(),
            'meta_title': article.meta_title,
            'meta_description': article.meta_description,
            'reading_time': article.get_reading_time(),
            'has_cover_image': article.has_cover_image(),
            'cover_image_url': article.get_cover_image_url(),
        }
        
        # Inclure le contenu complet si demandé
        if include_content:
            data['content'] = article.content
        
        # Informations sur l'auteur
        if article.author:
            data['author'] = {
                'id': article.author.id,
                'username': article.author.username,
                'first_name': article.author.first_name,
                'last_name': article.author.last_name,
            }
        
        # Catégorie
        if article.category:
            data['category'] = CategorySerializer.serialize(article.category)
        
        # Tags
        data['tags'] = [TagSerializer.serialize(tag) for tag in article.tags.all()]
        
        # Informations utilisateur spécifiques
        if user and user.is_authenticated:
            data['user_has_liked'] = cls.user_has_liked(article, user)
        
        # Nombre de commentaires
        data['comments_count'] = article.comments.filter(is_active=True).count()
        
        return data
    
    @staticmethod
    def user_has_liked(article, user):
        """Vérifie si l'utilisateur a liké l'article"""
        content_type = ContentType.objects.get_for_model(Article)
        return Like.objects.filter(
            user=user,
            content_type=content_type,
            object_id=article.id
        ).exists()


class CategorySerializer(APISerializer):
    """Serializer pour les catégories"""
    
    @classmethod
    def serialize(cls, category):
        """Sérialise une catégorie"""
        if not category:
            return None
            
        return {
            'id': category.id,
            'name': category.name,
            'description': category.description,
            'slug': category.slug,
            'couleur': category.couleur,
            'icone': category.icone,
            'articles_count': category.get_articles_count(),
            'created_at': category.created_at.isoformat(),
        }


class TagSerializer(APISerializer):
    """Serializer pour les tags"""
    
    @classmethod
    def serialize(cls, tag):
        """Sérialise un tag"""
        if not tag:
            return None
            
        return {
            'id': tag.id,
            'name': tag.name,
            'slug': tag.slug,
            'couleur': tag.couleur,
            'articles_count': tag.get_articles_count(),
            'created_at': tag.created_at.isoformat(),
        }


class CommentSerializer(APISerializer):
    """Serializer pour les commentaires"""
    
    @classmethod
    def serialize(cls, comment, user=None):
        """Sérialise un commentaire"""
        if not comment:
            return None
            
        data = {
            'id': comment.id,
            'content': comment.content,
            'created_at': comment.created_at.isoformat(),
            'updated_at': comment.updated_at.isoformat(),
            'is_active': comment.is_active,
        }
        
        # Informations sur l'auteur
        if comment.author:
            data['author'] = {
                'id': comment.author.id,
                'username': comment.author.username,
                'first_name': comment.author.first_name,
                'last_name': comment.author.last_name,
            }
        
        # Permissions utilisateur
        if user and user.is_authenticated:
            data['can_edit'] = user == comment.author or user.is_staff
            data['can_delete'] = user == comment.author or user.is_staff
        
        return data


class LikeSerializer(APISerializer):
    """Serializer pour les likes"""
    
    @classmethod
    def serialize(cls, like):
        """Sérialise un like"""
        if not like:
            return None
            
        return {
            'id': like.id,
            'created_at': like.created_at.isoformat(),
            'user': {
                'id': like.user.id,
                'username': like.user.username,
            } if like.user else None,
        }