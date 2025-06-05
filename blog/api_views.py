import json
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models import Q, Count, F
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404

from .models import Article, Category, Tag
from .serializers import ArticleSerializer, CategorySerializer, TagSerializer, CommentSerializer, LikeSerializer
from comments.models import Comment
from stats.models import Like, View as ViewStats, Share


class APIBaseView(View):
    """Vue de base pour l'API avec méthodes communes"""
    
    def dispatch(self, request, *args, **kwargs):
        """Override pour gérer les headers CORS et le content-type"""
        response = super().dispatch(request, *args, **kwargs)
        
        # Headers CORS
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
        
        return response
    
    def options(self, request, *args, **kwargs):
        """Gérer les requêtes OPTIONS pour CORS"""
        return JsonResponse({}, status=200)
    
    def get_json_data(self, request):
        """Récupère et parse les données JSON de la requête"""
        try:
            if request.content_type == 'application/json':
                return json.loads(request.body.decode('utf-8'))
            return {}
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {}
    
    def success_response(self, data=None, message=None, status=200):
        """Retourne une réponse de succès standardisée"""
        response_data = {
            'success': True,
            'message': message or _('Opération réussie'),
        }
        if data is not None:
            response_data['data'] = data
        return JsonResponse(response_data, status=status)
    
    def error_response(self, message, errors=None, status=400):
        """Retourne une réponse d'erreur standardisée"""
        response_data = {
            'success': False,
            'message': message,
        }
        if errors:
            response_data['errors'] = errors
        return JsonResponse(response_data, status=status)
    
    def paginate_queryset(self, queryset, request, per_page=10):
        """Pagine un queryset et retourne les métadonnées de pagination"""
        page = request.GET.get('page', 1)
        try:
            page = int(page)
        except (ValueError, TypeError):
            page = 1
        
        paginator = Paginator(queryset, per_page)
        page_obj = paginator.get_page(page)
        
        return page_obj, {
            'current_page': page_obj.number,
            'total_pages': paginator.num_pages,
            'total_items': paginator.count,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
            'previous_page': page_obj.previous_page_number() if page_obj.has_previous() else None,
        }


@method_decorator(csrf_exempt, name='dispatch')
class ArticleListAPIView(APIBaseView):
    """API pour lister et créer des articles"""
    
    def get(self, request):
        """Liste tous les articles avec filtres et pagination"""
        queryset = Article.objects.filter(status='published').select_related('author', 'category').prefetch_related('tags')
        
        # Filtres
        category_id = request.GET.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        tag_slug = request.GET.get('tag')
        if tag_slug:
            queryset = queryset.filter(tags__slug=tag_slug)
        
        search = request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | 
                Q(content__icontains=search) |
                Q(excerpt__icontains=search)
            )
        
        author_id = request.GET.get('author')
        if author_id:
            queryset = queryset.filter(author_id=author_id)
        
        # Tri
        ordering = request.GET.get('ordering', '-created_at')
        valid_orderings = ['created_at', '-created_at', 'title', '-title', 'views_count', '-views_count', 'likes_count', '-likes_count']
        if ordering in valid_orderings:
            queryset = queryset.order_by(ordering)
        
        # Pagination
        per_page = min(int(request.GET.get('per_page', 10)), 50)  # Max 50 par page
        page_obj, pagination_meta = self.paginate_queryset(queryset, request, per_page)
        
        # Sérialisation
        articles_data = [
            ArticleSerializer.serialize(article, include_content=False, user=request.user)
            for article in page_obj
        ]
        
        return self.success_response({
            'articles': articles_data,
            'pagination': pagination_meta
        })
    
    def post(self, request):
        """Créer un nouvel article (authentification requise)"""
        if not request.user.is_authenticated:
            return self.error_response(_('Authentification requise'), status=401)
        
        data = self.get_json_data(request)
        
        # Validation des données requises
        required_fields = ['title', 'content']
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return self.error_response(
                _('Champs manquants'),
                {'missing_fields': missing_fields}
            )
        
        try:
            article = Article.objects.create(
                title=data['title'],
                content=data['content'],
                excerpt=data.get('excerpt', ''),
                author=request.user,
                status=data.get('status', 'draft'),
                meta_title=data.get('meta_title', ''),
                meta_description=data.get('meta_description', ''),
            )
            
            # Ajouter la catégorie si fournie
            if data.get('category_id'):
                try:
                    category = Category.objects.get(id=data['category_id'])
                    article.category = category
                    article.save()
                except Category.DoesNotExist:
                    pass
            
            # Ajouter les tags si fournis
            if data.get('tag_ids'):
                tag_ids = data['tag_ids'] if isinstance(data['tag_ids'], list) else [data['tag_ids']]
                tags = Tag.objects.filter(id__in=tag_ids)
                article.tags.set(tags)
            
            article_data = ArticleSerializer.serialize(article, user=request.user)
            return self.success_response(article_data, _('Article créé avec succès'), status=201)
            
        except Exception as e:
            return self.error_response(_('Erreur lors de la création de l\'article'), status=500)


@method_decorator(csrf_exempt, name='dispatch')
class ArticleDetailAPIView(APIBaseView):
    """API pour récupérer, modifier et supprimer un article"""
    
    def get(self, request, slug):
        """Récupère un article par son slug"""
        try:
            article = Article.objects.select_related('author', 'category').prefetch_related('tags').get(slug=slug)
            
            # Vérifier si l'article est publié ou si l'utilisateur a les permissions
            if article.status != 'published' and (not request.user.is_authenticated or 
                                                 (request.user != article.author and not request.user.is_staff)):
                return self.error_response(_('Article non trouvé'), status=404)
            
            # Enregistrer la vue si l'utilisateur n'est pas l'auteur
            if request.user != article.author:
                self.record_view(article, request)
            
            article_data = ArticleSerializer.serialize(article, user=request.user)
            return self.success_response(article_data)
            
        except Article.DoesNotExist:
            return self.error_response(_('Article non trouvé'), status=404)
    
    def put(self, request, slug):
        """Modifie un article (auteur ou admin seulement)"""
        if not request.user.is_authenticated:
            return self.error_response(_('Authentification requise'), status=401)
        
        try:
            article = Article.objects.get(slug=slug)
            
            # Vérifier les permissions
            if request.user != article.author and not request.user.is_staff:
                return self.error_response(_('Permission refusée'), status=403)
            
            data = self.get_json_data(request)
            
            # Mettre à jour les champs
            if 'title' in data:
                article.title = data['title']
            if 'content' in data:
                article.content = data['content']
            if 'excerpt' in data:
                article.excerpt = data['excerpt']
            if 'status' in data:
                article.status = data['status']
            if 'meta_title' in data:
                article.meta_title = data['meta_title']
            if 'meta_description' in data:
                article.meta_description = data['meta_description']
            
            # Mettre à jour la catégorie
            if 'category_id' in data:
                if data['category_id']:
                    try:
                        category = Category.objects.get(id=data['category_id'])
                        article.category = category
                    except Category.DoesNotExist:
                        pass
                else:
                    article.category = None
            
            article.save()
            
            # Mettre à jour les tags
            if 'tag_ids' in data:
                tag_ids = data['tag_ids'] if isinstance(data['tag_ids'], list) else [data['tag_ids']]
                tags = Tag.objects.filter(id__in=tag_ids)
                article.tags.set(tags)
            
            article_data = ArticleSerializer.serialize(article, user=request.user)
            return self.success_response(article_data, _('Article modifié avec succès'))
            
        except Article.DoesNotExist:
            return self.error_response(_('Article non trouvé'), status=404)
        except Exception as e:
            return self.error_response(_('Erreur lors de la modification'), status=500)
    
    def delete(self, request, slug):
        """Supprime un article (auteur ou admin seulement)"""
        if not request.user.is_authenticated:
            return self.error_response(_('Authentification requise'), status=401)
        
        try:
            article = Article.objects.get(slug=slug)
            
            # Vérifier les permissions
            if request.user != article.author and not request.user.is_staff:
                return self.error_response(_('Permission refusée'), status=403)
            
            article.delete()
            return self.success_response(message=_('Article supprimé avec succès'))
            
        except Article.DoesNotExist:
            return self.error_response(_('Article non trouvé'), status=404)
    
    def record_view(self, article, request):
        """Enregistre une vue pour l'article"""
        try:
            content_type = ContentType.objects.get_for_model(Article)
            ViewStats.objects.create(
                content_type=content_type,
                object_id=article.id,
                user=request.user if request.user.is_authenticated else None,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
            )
            # Mettre à jour le compteur
            article.increment_views()
        except Exception:
            pass  # Ignore les erreurs de vue
    
    def get_client_ip(self, request):
        """Récupère l'IP du client"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


@method_decorator(csrf_exempt, name='dispatch')
class CommentListAPIView(APIBaseView):
    """API pour lister et créer des commentaires"""
    
    def get(self, request, article_slug):
        """Liste tous les commentaires d'un article"""
        try:
            article = Article.objects.get(slug=article_slug)
            
            # Vérifier si l'article est accessible
            if article.status != 'published' and (not request.user.is_authenticated or 
                                                 (request.user != article.author and not request.user.is_staff)):
                return self.error_response(_('Article non trouvé'), status=404)
            
            content_type = ContentType.objects.get_for_model(Article)
            queryset = Comment.objects.filter(
                content_type=content_type,
                object_id=article.id,
                is_active=True
            ).select_related('author').order_by('-created_at')
            
            # Pagination
            per_page = min(int(request.GET.get('per_page', 20)), 100)
            page_obj, pagination_meta = self.paginate_queryset(queryset, request, per_page)
            
            # Sérialisation
            comments_data = [
                CommentSerializer.serialize(comment, user=request.user)
                for comment in page_obj
            ]
            
            return self.success_response({
                'comments': comments_data,
                'pagination': pagination_meta,
                'article': {
                    'id': article.id,
                    'title': article.title,
                    'slug': article.slug
                }
            })
            
        except Article.DoesNotExist:
            return self.error_response(_('Article non trouvé'), status=404)
    
    def post(self, request, article_slug):
        """Créer un nouveau commentaire (authentification requise)"""
        if not request.user.is_authenticated:
            return self.error_response(_('Authentification requise'), status=401)
        
        try:
            article = Article.objects.get(slug=article_slug)
            
            # Vérifier si l'article est accessible
            if article.status != 'published':
                return self.error_response(_('Impossible de commenter cet article'), status=403)
            
            data = self.get_json_data(request)
            
            # Validation
            content = data.get('content', '').strip()
            if not content:
                return self.error_response(_('Le contenu du commentaire est requis'))
            
            if len(content) > 1000:
                return self.error_response(_('Le commentaire est trop long (max 1000 caractères)'))
            
            # Créer le commentaire
            content_type = ContentType.objects.get_for_model(Article)
            comment = Comment.objects.create(
                content=content,
                author=request.user,
                content_type=content_type,
                object_id=article.id
            )
            
            comment_data = CommentSerializer.serialize(comment, user=request.user)
            return self.success_response(comment_data, _('Commentaire ajouté avec succès'), status=201)
            
        except Article.DoesNotExist:
            return self.error_response(_('Article non trouvé'), status=404)
        except Exception as e:
            return self.error_response(_('Erreur lors de la création du commentaire'), status=500)


@method_decorator(csrf_exempt, name='dispatch')
class CommentDetailAPIView(APIBaseView):
    """API pour modifier et supprimer un commentaire"""
    
    def put(self, request, comment_id):
        """Modifie un commentaire (auteur ou admin seulement)"""
        if not request.user.is_authenticated:
            return self.error_response(_('Authentification requise'), status=401)
        
        try:
            comment = Comment.objects.get(id=comment_id, is_active=True)
            
            # Vérifier les permissions
            if request.user != comment.author and not request.user.is_staff:
                return self.error_response(_('Permission refusée'), status=403)
            
            data = self.get_json_data(request)
            
            # Validation
            content = data.get('content', '').strip()
            if not content:
                return self.error_response(_('Le contenu du commentaire est requis'))
            
            if len(content) > 1000:
                return self.error_response(_('Le commentaire est trop long (max 1000 caractères)'))
            
            comment.content = content
            comment.save()
            
            comment_data = CommentSerializer.serialize(comment, user=request.user)
            return self.success_response(comment_data, _('Commentaire modifié avec succès'))
            
        except Comment.DoesNotExist:
            return self.error_response(_('Commentaire non trouvé'), status=404)
        except Exception as e:
            return self.error_response(_('Erreur lors de la modification'), status=500)
    
    def delete(self, request, comment_id):
        """Supprime un commentaire (auteur ou admin seulement)"""
        if not request.user.is_authenticated:
            return self.error_response(_('Authentification requise'), status=401)
        
        try:
            comment = Comment.objects.get(id=comment_id, is_active=True)
            
            # Vérifier les permissions
            if request.user != comment.author and not request.user.is_staff:
                return self.error_response(_('Permission refusée'), status=403)
            
            comment.is_active = False
            comment.save()
            
            return self.success_response(message=_('Commentaire supprimé avec succès'))
            
        except Comment.DoesNotExist:
            return self.error_response(_('Commentaire non trouvé'), status=404)


@method_decorator(csrf_exempt, name='dispatch')
class LikeAPIView(APIBaseView):
    """API pour gérer les likes"""
    
    def post(self, request, article_slug):
        """Ajouter ou retirer un like sur un article"""
        if not request.user.is_authenticated:
            return self.error_response(_('Authentification requise'), status=401)
        
        try:
            article = Article.objects.get(slug=article_slug)
            
            # Vérifier si l'article est accessible
            if article.status != 'published':
                return self.error_response(_('Article non trouvé'), status=404)
            
            content_type = ContentType.objects.get_for_model(Article)
            
            # Vérifier si l'utilisateur a déjà liké
            existing_like = Like.objects.filter(
                user=request.user,
                content_type=content_type,
                object_id=article.id
            ).first()
            
            if existing_like:
                # Retirer le like
                existing_like.delete()
                article.increment_likes()  # Recalculer le compteur
                return self.success_response({
                    'liked': False,
                    'likes_count': article.likes_count
                }, _('Like retiré'))
            else:
                # Ajouter le like
                Like.objects.create(
                    user=request.user,
                    content_type=content_type,
                    object_id=article.id
                )
                article.increment_likes()  # Recalculer le compteur
                return self.success_response({
                    'liked': True,
                    'likes_count': article.likes_count
                }, _('Article liké'))
                
        except Article.DoesNotExist:
            return self.error_response(_('Article non trouvé'), status=404)
        except Exception as e:
            return self.error_response(_('Erreur lors du traitement du like'), status=500)


class CategoryListAPIView(APIBaseView):
    """API pour lister les catégories"""
    
    def get(self, request):
        """Liste toutes les catégories avec le nombre d'articles"""
        queryset = Category.objects.annotate(
            articles_count=Count('articles', filter=Q(articles__status='published'))
        ).order_by('name')
        
        categories_data = [CategorySerializer.serialize(category) for category in queryset]
        
        return self.success_response({
            'categories': categories_data,
            'total': len(categories_data)
        })


class TagListAPIView(APIBaseView):
    """API pour lister les tags"""
    
    def get(self, request):
        """Liste tous les tags avec le nombre d'articles"""
        queryset = Tag.objects.annotate(
            articles_count=Count('articles', filter=Q(articles__status='published'))
        ).filter(articles_count__gt=0).order_by('-articles_count', 'name')
        
        # Limite optionnelle
        limit = request.GET.get('limit')
        if limit:
            try:
                limit = int(limit)
                queryset = queryset[:limit]
            except (ValueError, TypeError):
                pass
        
        tags_data = [TagSerializer.serialize(tag) for tag in queryset]
        
        return self.success_response({
            'tags': tags_data,
            'total': len(tags_data)
        })


class StatsAPIView(APIBaseView):
    """API pour les statistiques générales"""
    
    def get(self, request):
        """Retourne les statistiques générales du blog"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        stats = {
            'articles': {
                'total': Article.objects.filter(status='published').count(),
                'draft': Article.objects.filter(status='draft').count() if request.user.is_authenticated else 0,
                'total_views': Article.objects.filter(status='published').aggregate(
                    total=Count('views'))['total'] or 0,
                'total_likes': Article.objects.filter(status='published').aggregate(
                    total=Count('likes'))['total'] or 0,
            },
            'categories': Category.objects.count(),
            'tags': Tag.objects.count(),
            'comments': Comment.objects.filter(is_active=True).count(),
            'users': User.objects.filter(is_active=True).count(),
        }
        
        # Articles populaires (top 5)
        popular_articles = Article.objects.filter(status='published').order_by('-views_count')[:5]
        stats['popular_articles'] = [
            {
                'id': article.id,
                'title': article.title,
                'slug': article.slug,
                'views_count': article.views_count
            }
            for article in popular_articles
        ]
        
        # Articles récents (top 5)
        recent_articles = Article.objects.filter(status='published').order_by('-created_at')[:5]
        stats['recent_articles'] = [
            {
                'id': article.id,
                'title': article.title,
                'slug': article.slug,
                'created_at': article.created_at.isoformat()
            }
            for article in recent_articles
        ]
        
        return self.success_response(stats)