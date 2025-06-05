from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, F, Sum, Avg, Max
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.utils.translation import gettext as _
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.files.base import ContentFile
import json
import requests
import base64
from io import BytesIO
from PIL import Image
from .forms import PostForm, CategoryForm, TagForm
from .models import Article, Category, Tag
from comments.models import Comment
from comments.forms import CommentForm
from stats.models import Like, Share, View
from users.decorators import admin_required, auteur_required, article_owner_required
from pythonFinal.logging_utils import (
    log_content_action, log_admin_action, log_error, 
    log_view_access, log_security_event
)

# Create your views here.
@log_view_access('blog')
def home(request):
    # Articles récents (5 derniers articles publiés)
    recent_articles = Article.objects.filter(status='published').order_by('-created_at')[:5]
    
    # Articles populaires (basés sur les vues, likes et partages)
    popular_articles = Article.objects.filter(status='published').extra(
        select={'popularity': 'views_count + likes_count * 2 + shares_count * 3'}
    ).order_by('-popularity')[:5]
    
    # Catégories avec statistiques
    categories_with_stats = Category.objects.annotate(
        articles_count=Count('articles', filter=Q(articles__status='published')),
        total_views=Count('articles__views_count', filter=Q(articles__status='published'))
    ).order_by('-articles_count')
    
    # Auteurs populaires (basés sur le nombre d'articles publiés et vues totales)
    from django.contrib.auth import get_user_model
    User = get_user_model()
    popular_authors = User.objects.annotate(
        published_articles_count=Count('articles', filter=Q(articles__status='published')),
        total_views=Count('articles__views_count', filter=Q(articles__status='published'))
    ).filter(published_articles_count__gt=0).order_by('-published_articles_count', '-total_views')[:5]
    
    # Tous les articles pour la section principale
    posts = Article.objects.filter(status='published').order_by('-created_at')
    
    # Tags populaires
    tags = Tag.objects.all().order_by('name')
    
    return render(request, 'blog/home.html', {
        'posts': posts,
        'recent_articles': recent_articles,
        'popular_articles': popular_articles,
        'categories': categories_with_stats,
        'popular_authors': popular_authors,
        'tags': tags
    })

@auteur_required
@log_view_access('blog')
def ajouter_article(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                article = form.save(commit=False)
                article.author = request.user
                article.save()
                form.save_m2m()
                
                # Log de la création d'article
                log_content_action(request, 'CREATION', 'Article', article.id, 
                                 f"Titre: {article.title}, Statut: {article.status}")
                
                messages.success(request, _("L'article a été créé avec succès !"))
                return redirect('blog:home')
            except Exception as e:
                log_error(request, e, "Erreur lors de la création d'article")
                messages.error(request, _("Erreur lors de l'enregistrement : %(error)s") % {'error': str(e)})
        else:
            # Log des erreurs de création d'article
            log_content_action(request, 'ECHEC_CREATION', 'Article', None, 
                             "Erreurs de validation du formulaire")
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, _("Erreur dans le champ '%(field)s': %(error)s") % {'field': field, 'error': error})
    else:
        form = PostForm()
    return render(request, 'blog/ajouter_article.html', {'form': form})

@article_owner_required
@log_view_access('blog')
def modifier_article(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    # Vérification supplémentaire des permissions
    if not request.user.can_edit_article(article):
        log_security_event(request, 'TENTATIVE_MODIFICATION_ARTICLE_NON_AUTORISEE', 'WARNING',
                         f"Article ID: {article_id}, Titre: {article.title}")
        messages.error(request, _('Vous n\'avez pas les permissions pour modifier cet article.'))
        return redirect('blog:home')
    
    if request.method == 'POST':
        # Sauvegarder l'état précédent pour le log
        old_title = article.title
        old_status = article.status
        
        form = PostForm(request.POST, request.FILES, instance=article)
        if form.is_valid():
            try:
                form.save()
                
                # Log de la modification d'article
                changes = []
                if article.title != old_title:
                    changes.append(f"Titre: {old_title} -> {article.title}")
                if article.status != old_status:
                    changes.append(f"Statut: {old_status} -> {article.status}")
                
                log_content_action(request, 'MODIFICATION', 'Article', article.id,
                                 f"Changements: {', '.join(changes) if changes else 'Mise à jour générale'}")
                
                messages.success(request, _("L'article a été modifié avec succès !"))
                return redirect('blog:article_detail', article_id=article.id)
            except Exception as e:
                log_error(request, e, f"Erreur lors de la modification de l'article {article_id}")
                messages.error(request, _("Une erreur est survenue lors de la modification."))
        else:
            log_content_action(request, 'ECHEC_MODIFICATION', 'Article', article_id,
                             "Erreurs de validation du formulaire")
    else:
        form = PostForm(instance=article)
    return render(request, 'blog/modifier_article.html', {'form': form, 'article': article})

@article_owner_required
@log_view_access('blog')
def supprimer_article(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    # Vérification supplémentaire des permissions
    if not request.user.can_delete_article(article):
        log_security_event(request, 'TENTATIVE_SUPPRESSION_ARTICLE_NON_AUTORISEE', 'WARNING',
                         f"Article ID: {article_id}, Titre: {article.title}")
        messages.error(request, _('Vous n\'avez pas les permissions pour supprimer cet article.'))
        return redirect('blog:home')
    
    if request.method == 'POST':
        article_title = article.title
        article_status = article.status
        
        try:
            article.delete()
            
            # Log de la suppression d'article
            log_content_action(request, 'SUPPRESSION', 'Article', article_id,
                             f"Titre supprimé: {article_title}, Statut: {article_status}")
            log_security_event(request, 'SUPPRESSION_ARTICLE', 'INFO',
                             f"Article supprimé: {article_title} (ID: {article_id})")
            
            messages.success(request, _("L'article a été supprimé avec succès !"))
            return redirect('blog:home')
        except Exception as e:
            log_error(request, e, f"Erreur lors de la suppression de l'article {article_id}")
            messages.error(request, _("Une erreur est survenue lors de la suppression."))
            
    return render(request, 'blog/supprimer_article.html', {'article': article})

@admin_required
@log_view_access('blog')
def ajouter_categorie(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            try:
                category = form.save()
                
                # Log de la création de catégorie
                log_admin_action(request, "CREATION_CATEGORIE", f"Catégorie {category.name}",
                               f"Slug: {category.slug}")
                
                messages.success(request, _("La catégorie a été créée avec succès !"))
                return redirect('blog:home')
            except Exception as e:
                log_error(request, e, "Erreur lors de la création de catégorie")
                messages.error(request, _("Une erreur est survenue lors de la création."))
        else:
            log_admin_action(request, "ECHEC_CREATION_CATEGORIE", "Nouvelle catégorie",
                           "Erreurs de validation du formulaire")
    else:
        form = CategoryForm()
    return render(request, 'blog/ajouter_categorie.html', {'form': form})

@admin_required
@log_view_access('blog')
def modifier_categorie(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        old_name = category.name
        old_slug = category.slug
        
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            try:
                form.save()
                
                # Log de la modification de catégorie
                changes = []
                if category.name != old_name:
                    changes.append(f"Nom: {old_name} -> {category.name}")
                if category.slug != old_slug:
                    changes.append(f"Slug: {old_slug} -> {category.slug}")
                
                log_admin_action(request, "MODIFICATION_CATEGORIE", f"Catégorie {category.name}",
                               f"Changements: {', '.join(changes) if changes else 'Mise à jour générale'}")
                
                messages.success(request, _("La catégorie a été modifiée avec succès !"))
                return redirect('blog:home')
            except Exception as e:
                log_error(request, e, f"Erreur lors de la modification de la catégorie {category_id}")
                messages.error(request, _("Une erreur est survenue lors de la modification."))
        else:
            log_admin_action(request, "ECHEC_MODIFICATION_CATEGORIE", f"Catégorie {category.name}",
                           "Erreurs de validation du formulaire")
    else:
        form = CategoryForm(instance=category)
    return render(request, 'blog/modifier_categorie.html', {'form': form, 'category': category})

@admin_required
@log_view_access('blog')
def supprimer_categorie(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        category_name = category.name
        articles_count = category.articles.count()
        
        try:
            category.delete()
            
            # Log de la suppression de catégorie
            log_admin_action(request, "SUPPRESSION_CATEGORIE", f"Catégorie {category_name}",
                           f"Articles affectés: {articles_count}")
            log_security_event(request, 'SUPPRESSION_CATEGORIE', 'WARNING',
                             f"Catégorie supprimée: {category_name} (ID: {category_id})")
            
            messages.success(request, _("La catégorie a été supprimée avec succès !"))
            return redirect('blog:home')
        except Exception as e:
            log_error(request, e, f"Erreur lors de la suppression de la catégorie {category_id}")
            messages.error(request, _("Une erreur est survenue lors de la suppression."))
            
    return render(request, 'blog/supprimer_categorie.html', {'category': category})

@admin_required
@log_view_access('blog')
def ajouter_tag(request):
    if request.method == 'POST':
        form = TagForm(request.POST)
        if form.is_valid():
            try:
                tag = form.save()
                
                # Log de la création de tag
                log_admin_action(request, "CREATION_TAG", f"Tag {tag.name}",
                               f"Slug: {tag.slug}")
                
                messages.success(request, _("Le tag a été créé avec succès !"))
                return redirect('blog:home')
            except Exception as e:
                log_error(request, e, "Erreur lors de la création de tag")
                messages.error(request, _("Une erreur est survenue lors de la création."))
        else:
            log_admin_action(request, "ECHEC_CREATION_TAG", "Nouveau tag",
                           "Erreurs de validation du formulaire")
    else:
        form = TagForm()
    return render(request, 'blog/ajouter_tag.html', {'form': form})

@admin_required
@log_view_access('blog')
def modifier_tag(request, tag_id):
    tag = get_object_or_404(Tag, id=tag_id)
    if request.method == 'POST':
        old_name = tag.name
        old_slug = tag.slug
        
        form = TagForm(request.POST, instance=tag)
        if form.is_valid():
            try:
                form.save()
                
                # Log de la modification de tag
                changes = []
                if tag.name != old_name:
                    changes.append(f"Nom: {old_name} -> {tag.name}")
                if tag.slug != old_slug:
                    changes.append(f"Slug: {old_slug} -> {tag.slug}")
                
                log_admin_action(request, "MODIFICATION_TAG", f"Tag {tag.name}",
                               f"Changements: {', '.join(changes) if changes else 'Mise à jour générale'}")
                
                messages.success(request, _("Le tag a été modifié avec succès !"))
                return redirect('blog:home')
            except Exception as e:
                log_error(request, e, f"Erreur lors de la modification du tag {tag_id}")
                messages.error(request, _("Une erreur est survenue lors de la modification."))
        else:
            log_admin_action(request, "ECHEC_MODIFICATION_TAG", f"Tag {tag.name}",
                           "Erreurs de validation du formulaire")
    else:
        form = TagForm(instance=tag)
    return render(request, 'blog/modifier_tag.html', {'form': form, 'tag': tag})

@admin_required
@log_view_access('blog')
def supprimer_tag(request, tag_id):
    tag = get_object_or_404(Tag, id=tag_id)
    if request.method == 'POST':
        tag_name = tag.name
        articles_count = tag.articles.count()
        
        try:
            tag.delete()
            
            # Log de la suppression de tag
            log_admin_action(request, "SUPPRESSION_TAG", f"Tag {tag_name}",
                           f"Articles affectés: {articles_count}")
            log_security_event(request, 'SUPPRESSION_TAG', 'INFO',
                             f"Tag supprimé: {tag_name} (ID: {tag_id})")
            
            messages.success(request, _("Le tag a été supprimé avec succès !"))
            return redirect('blog:home')
        except Exception as e:
            log_error(request, e, f"Erreur lors de la suppression du tag {tag_id}")
            messages.error(request, _("Une erreur est survenue lors de la suppression."))
            
    return render(request, 'blog/supprimer_tag.html', {'tag': tag})

@log_view_access('blog')
def article_detail(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    
    # Enregistrer une vue
    if request.method == 'GET':
        content_type = ContentType.objects.get_for_model(Article)
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        try:
            View.objects.create(
                user=request.user if request.user.is_authenticated else None,
                content_type=content_type,
                object_id=article.id,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Mettre à jour le compteur de vues
            article.views_count = article.views.count()
            article.save(update_fields=['views_count'])
            
            # Log de la consultation d'article (niveau DEBUG pour éviter trop de logs)
            from pythonFinal.logging_utils import blog_logger
            blog_logger.debug(f"[CONSULTATION] Article '{article.title}' (ID: {article_id}) "
                            f"consulté par {request.user.username if request.user.is_authenticated else 'anonyme'}")
        except Exception as e:
            log_error(request, e, f"Erreur lors de l'enregistrement de vue pour l'article {article_id}")
    
    # Récupérer les commentaires via la relation générique
    comments = article.comments.filter(is_active=True).order_by('-created_at')
    
    if request.method == 'POST' and request.user.is_authenticated:
        form = CommentForm(request.POST)
        if form.is_valid():
            try:
                comment = form.save(commit=False)
                comment.author = request.user
                comment.content_type = ContentType.objects.get_for_model(Article)
                comment.object_id = article.id
                comment.save()
                
                # Log de l'ajout de commentaire
                log_content_action(request, 'CREATION', 'Commentaire', comment.id,
                                 f"Sur l'article: {article.title}")
                
                messages.success(request, _("Votre commentaire a été ajouté avec succès !"))
                return redirect('blog:article_detail', article_id=article.id)
            except Exception as e:
                log_error(request, e, f"Erreur lors de l'ajout de commentaire sur l'article {article_id}")
                messages.error(request, _("Une erreur est survenue lors de l'ajout du commentaire."))
        else:
            log_content_action(request, 'ECHEC_CREATION', 'Commentaire', None,
                             f"Erreurs de validation sur l'article: {article.title}")
    else:
        form = CommentForm()
    
    return render(request, 'blog/article_detail.html', {
        'article': article,
        'comments': comments,
        'form': form
    })

@log_view_access('blog')
def category_posts(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    posts = Article.objects.filter(category=category, status='published').order_by('-created_at')
    return render(request, 'blog/home.html', {
        'category': category,
        'posts': posts
    })

@log_view_access('blog')
def tag_posts(request, tag_slug):
    tag = get_object_or_404(Tag, slug=tag_slug)
    posts = Article.objects.filter(tags=tag, status='published').order_by('-created_at')
    return render(request, 'blog/home.html', {
        'tag': tag,
        'posts': posts
    })

@log_view_access('blog')
def liste_articles(request):
    """
    Vue pour afficher la liste des articles avec pagination, filtrage, tri et recherche PostgreSQL optimisée
    """
    # Commencer avec tous les articles publiés
    articles = Article.objects.filter(status='published').select_related('author', 'category').prefetch_related('tags')
    
    # Paramètres de recherche et filtrage
    search_query = request.GET.get('search', '').strip()
    category_id = request.GET.get('category', '')
    tag_id = request.GET.get('tag', '')
    author_id = request.GET.get('author', '')
    sort_by = request.GET.get('sort', 'recent')
    
    # Recherche full-text PostgreSQL optimisée
    if search_query:
        try:
            search_vector = (
                SearchVector('title', weight='A', config='french') + 
                SearchVector('content', weight='B', config='french') + 
                SearchVector('excerpt', weight='C', config='french') +
                SearchVector('meta_title', weight='A', config='french') +
                SearchVector('meta_description', weight='C', config='french')
            )
            search_query_obj = SearchQuery(search_query, config='french')
            
            articles = articles.annotate(
                search=search_vector,
                rank=SearchRank(search_vector, search_query_obj)
            ).filter(search=search_query_obj).order_by('-rank', '-created_at')
        except Exception as e:
            log_error(request, e, f"Erreur lors de la recherche PostgreSQL: {search_query}")
            articles = articles.filter(
                Q(title__icontains=search_query) |
                Q(content__icontains=search_query) |
                Q(excerpt__icontains=search_query)
            ).order_by('-created_at')
    
    # Filtrage par catégorie, tag et auteur
    if category_id:
        try:
            articles = articles.filter(category_id=int(category_id))
        except (ValueError, TypeError):
            pass
    
    if tag_id:
        try:
            articles = articles.filter(tags__id=int(tag_id)).distinct()
        except (ValueError, TypeError):
            pass
    
    if author_id:
        try:
            articles = articles.filter(author_id=int(author_id))
        except (ValueError, TypeError):
            pass
    
    # Tri des résultats
    if not search_query:
        if sort_by == 'popular':
            articles = articles.annotate(
                popularity_score=F('views_count') + F('likes_count') * 2 + F('shares_count') * 3
            ).order_by('-popularity_score', '-created_at')
        elif sort_by == 'alphabetic':
            articles = articles.order_by('title', '-created_at')
        elif sort_by == 'oldest':
            articles = articles.order_by('created_at')
        else:
            articles = articles.order_by('-created_at')
    
    # Pagination
    items_per_page = int(request.GET.get('per_page', 12))
    items_per_page = min(max(items_per_page, 6), 24)
    
    paginator = Paginator(articles, items_per_page)
    page_number = request.GET.get('page', 1)
    
    try:
        page_obj = paginator.get_page(page_number)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.get_page(1)
    
    # Données pour les filtres avec compteurs optimisés
    categories = Category.objects.annotate(
        articles_count=Count('articles', filter=Q(articles__status='published'))
    ).filter(articles_count__gt=0).order_by('name')
    
    tags = Tag.objects.annotate(
        articles_count=Count('articles', filter=Q(articles__status='published'))
    ).filter(articles_count__gt=0).order_by('name')
    
    from django.contrib.auth import get_user_model
    User = get_user_model()
    authors = User.objects.annotate(
        articles_count=Count('articles', filter=Q(articles__status='published'))
    ).filter(articles_count__gt=0).order_by('username')
    
    # Statistiques pour l'affichage
    total_articles = Article.objects.filter(status='published').count()
    filtered_count = paginator.count
    
    # Objets sélectionnés pour l'affichage
    selected_category_obj = None
    selected_tag_obj = None
    selected_author_obj = None
    
    if category_id:
        try:
            selected_category_obj = Category.objects.get(id=int(category_id))
        except (Category.DoesNotExist, ValueError):
            pass
    
    if tag_id:
        try:
            selected_tag_obj = Tag.objects.get(id=int(tag_id))
        except (Tag.DoesNotExist, ValueError):
            pass
    
    if author_id:
        try:
            selected_author_obj = User.objects.get(id=int(author_id))
        except (User.DoesNotExist, ValueError):
            pass
    
    context = {
        'page_obj': page_obj,
        'articles': page_obj.object_list,
        'categories': categories,
        'tags': tags,
        'authors': authors,
        'search_query': search_query,
        'selected_category': category_id,
        'selected_tag': tag_id,
        'selected_author': author_id,
        'selected_category_obj': selected_category_obj,
        'selected_tag_obj': selected_tag_obj,
        'selected_author_obj': selected_author_obj,
        'sort_by': sort_by,
        'items_per_page': items_per_page,
        'total_articles': total_articles,
        'filtered_count': filtered_count,
        'is_paginated': page_obj.has_other_pages(),
        'paginator': paginator,
        'sort_options': [
            ('recent', _('Plus récent')),
            ('oldest', _('Plus ancien')),
            ('popular', _('Plus populaire')),
            ('alphabetic', _('Alphabétique')),
        ],
        'per_page_options': [6, 12, 18, 24],
    }
    
    return render(request, 'blog/liste_articles.html', context)

@admin_required
@log_view_access('blog')
def statistiques_tags(request):
    """Affiche les statistiques des tags avec nuage de mots et suggestions"""
    
    # Statistiques générales des tags
    tags_stats = Tag.objects.annotate(
        articles_count=Count('articles', filter=Q(articles__status='published')),
        total_views=Sum('articles__views_count', filter=Q(articles__status='published')),
        total_likes=Sum('articles__likes_count', filter=Q(articles__status='published')),
        total_shares=Sum('articles__shares_count', filter=Q(articles__status='published'))
    ).filter(articles_count__gt=0).order_by('-articles_count')
    
    # Tags les plus populaires (pour le nuage de mots)
    popular_tags = tags_stats[:20]  # Top 20 pour le nuage
    
    # Données pour le nuage de mots (format JSON)
    wordcloud_data = []
    for tag in popular_tags:
        # Calcul d'un score de popularité basé sur articles, vues, likes
        popularity_score = (
            tag.articles_count * 10 +  # Poids fort pour le nombre d'articles
            (tag.total_views or 0) * 0.1 +  # Poids moyen pour les vues
            (tag.total_likes or 0) * 2   # Poids fort pour les likes
        )
        wordcloud_data.append({
            'text': tag.name,
            'size': max(10, min(50, int(popularity_score / 10))),  # Taille entre 10 et 50
            'color': tag.couleur,
            'articles_count': tag.articles_count,
            'url': reverse('blog:tag_posts', args=[tag.slug])
        })
    
    # Tags suggérés (combinaisons fréquentes)
    # Recherche des tags qui apparaissent souvent ensemble
    tag_combinations = {}
    articles_with_multiple_tags = Article.objects.filter(
        status='published',
        tags__isnull=False
    ).prefetch_related('tags').annotate(tag_count=Count('tags')).filter(tag_count__gte=2)
    
    for article in articles_with_multiple_tags:
        article_tags = list(article.tags.all())
        for i, tag1 in enumerate(article_tags):
            for tag2 in article_tags[i+1:]:
                combination = tuple(sorted([tag1.name, tag2.name]))
                tag_combinations[combination] = tag_combinations.get(combination, 0) + 1
    
    # Trier les combinaisons par fréquence
    suggested_combinations = sorted(
        tag_combinations.items(), 
        key=lambda x: x[1], 
        reverse=True
    )[:10]
    
    # Tags inutilisés ou peu utilisés
    unused_tags = Tag.objects.annotate(
        articles_count=Count('articles', filter=Q(articles__status='published'))
    ).filter(articles_count=0)
    
    low_usage_tags = Tag.objects.annotate(
        articles_count=Count('articles', filter=Q(articles__status='published'))
    ).filter(articles_count__lte=2, articles_count__gt=0).order_by('articles_count')
    
    # Statistiques globales
    total_tags = Tag.objects.count()
    used_tags = tags_stats.count()
    total_articles = Article.objects.filter(status='published').count()
    
    context = {
        'tags_stats': tags_stats,
        'popular_tags': popular_tags,
        'wordcloud_data': json.dumps(wordcloud_data),
        'suggested_combinations': suggested_combinations,
        'unused_tags': unused_tags,
        'low_usage_tags': low_usage_tags,
        'total_tags': total_tags,
        'used_tags': used_tags,
        'unused_tags_count': total_tags - used_tags,
        'total_articles': total_articles,
    }
    
    return render(request, 'blog/admin/statistiques_tags.html', context)

@log_view_access('blog')
def auteurs_actifs(request):
    """
    Vue pour afficher la liste des auteurs actifs avec leurs statistiques
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    # Paramètres de tri
    sort_by = request.GET.get('sort', 'articles')
    
    # Auteurs avec leurs statistiques
    auteurs = User.objects.annotate(
        articles_count=Count('articles', filter=Q(articles__status='published')),
        total_views=Sum('articles__views_count', filter=Q(articles__status='published')),
        total_likes=Sum('articles__likes_count', filter=Q(articles__status='published')),
        total_shares=Sum('articles__shares_count', filter=Q(articles__status='published')),
        avg_views=Avg('articles__views_count', filter=Q(articles__status='published')),
        recent_activity=Max('articles__created_at', filter=Q(articles__status='published'))
    ).filter(articles_count__gt=0)
    
    # Tri des auteurs
    if sort_by == 'views':
        auteurs = auteurs.order_by('-total_views', '-articles_count')
    elif sort_by == 'likes':
        auteurs = auteurs.order_by('-total_likes', '-articles_count')
    elif sort_by == 'activity':
        auteurs = auteurs.order_by('-recent_activity', '-articles_count')
    elif sort_by == 'alphabetic':
        auteurs = auteurs.order_by('username')
    else:  # articles par défaut
        auteurs = auteurs.order_by('-articles_count', '-total_views')
    
    # Statistiques générales
    total_auteurs = auteurs.count()
    total_articles_tous = sum(a.articles_count for a in auteurs)
    total_vues_toutes = sum(a.total_views or 0 for a in auteurs)
    
    context = {
        'auteurs': auteurs[:50],  # Limite à 50 auteurs pour la performance
        'sort_by': sort_by,
        'total_auteurs': total_auteurs,
        'total_articles_tous': total_articles_tous,
        'total_vues_toutes': total_vues_toutes,
        'sort_options': [
            ('articles', _('Nombre d\'articles')),
            ('views', _('Vues totales')),
            ('likes', _('Likes totaux')),
            ('activity', _('Activité récente')),
            ('alphabetic', _('Alphabétique')),
        ],
    }
    
    return render(request, 'blog/auteurs_actifs.html', context)

@login_required
@csrf_exempt
def generer_article_openai(request):
    """
    Vue pour générer du contenu d'article et une image de couverture via l'API OpenAI
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    if not request.user.can_create_article():
        return JsonResponse({'error': 'Permissions insuffisantes'}, status=403)
    
    try:
        data = json.loads(request.body)
        prompt = data.get('prompt', '').strip()
        generer_image = data.get('generer_image', False)
        
        if not prompt:
            return JsonResponse({'error': 'Le prompt ne peut pas être vide'}, status=400)
        
        # Configuration de l'API OpenAI
        OPENAI_API_KEY = getattr(settings, 'OPENAI_API_KEY', None)
        
        if not OPENAI_API_KEY:
            return JsonResponse({
                'error': 'Configuration API OpenAI manquante. Veuillez configurer OPENAI_API_KEY dans les settings.'
            }, status=500)
        
        # Génération du contenu textuel avec GPT-4
        headers = {
            'Authorization': f'Bearer {OPENAI_API_KEY}',
            'Content-Type': 'application/json',
        }
        
        # Prompt optimisé pour la génération de contenu
        content_prompt = f"""
        Écris un article de blog en français sur : {prompt}
        
        Réponds UNIQUEMENT avec un JSON valide dans ce format exact :
        {{
            "titre": "Titre accrocheur de l'article",
            "resume": "Résumé en une phrase (max 200 caractères)",
            "contenu": "Contenu HTML structuré avec <p>, <h2>, <strong>, <em>, <ul>, <li>"
        }}
        
        Contenu : 400-600 mots, style informatif et engageant.
        """
        
        # Paramètres optimisés pour réduire le temps de génération
        gpt_payload = {
            "model": "gpt-3.5-turbo",  # Plus rapide que GPT-4
            "messages": [
                {
                    "role": "system", 
                    "content": "Tu es un rédacteur expert. Réponds UNIQUEMENT avec du JSON valide, sans texte supplémentaire."
                },
                {
                    "role": "user", 
                    "content": content_prompt
                }
            ],
            "max_tokens": 1500,  # Réduit pour accélérer
            "temperature": 0.7,
            "top_p": 0.9,
            "frequency_penalty": 0.1,
            "presence_penalty": 0.1
        }
        
        # Augmenter le timeout et ajouter des tentatives
        max_retries = 2
        timeout_duration = 60  # Augmenté à 60 secondes
        
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    'https://api.openai.com/v1/chat/completions',
                    headers=headers,
                    json=gpt_payload,
                    timeout=timeout_duration
                )
                break  # Si succès, sortir de la boucle
                
            except requests.exceptions.Timeout:
                if attempt == max_retries - 1:  # Dernière tentative
                    log_error(request, Exception("Timeout API OpenAI après plusieurs tentatives"), 
                             "Timeout lors de la génération d'article")
                    return JsonResponse({
                        'error': 'La génération prend trop de temps. Essayez avec un prompt plus court ou réessayez plus tard.'
                    }, status=408)
                
                # Réduire les paramètres pour la tentative suivante
                gpt_payload["max_tokens"] = max(800, gpt_payload["max_tokens"] - 300)
                timeout_duration = 45  # Réduire le timeout pour la deuxième tentative
                continue
            
            except requests.exceptions.RequestException as e:
                log_error(request, e, f"Erreur de connexion à OpenAI (tentative {attempt + 1})")
                if attempt == max_retries - 1:
                    return JsonResponse({
                        'error': 'Erreur de connexion à l\'API OpenAI. Vérifiez votre connexion internet.'
                    }, status=500)
                continue
        
        if response.status_code != 200:
            error_message = f"Erreur API OpenAI: {response.status_code}"
            if response.text:
                try:
                    error_data = response.json()
                    if 'error' in error_data:
                        error_message = error_data['error'].get('message', error_message)
                except:
                    pass
            
            log_error(request, Exception(error_message), "Erreur lors de l'appel à l'API OpenAI")
            return JsonResponse({'error': error_message}, status=500)
        
        gpt_response = response.json()
        generated_text = gpt_response['choices'][0]['message']['content'].strip()
        
        # Parser le JSON généré avec gestion d'erreur améliorée
        try:
            # Nettoyer le texte pour extraire le JSON
            start_idx = generated_text.find('{')
            end_idx = generated_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_text = generated_text[start_idx:end_idx]
                article_data = json.loads(json_text)
            else:
                raise ValueError("Format JSON non trouvé dans la réponse")
            
            # Validation des champs requis
            if not article_data.get('titre') or not article_data.get('contenu'):
                raise ValueError("Champs titre ou contenu manquants")
                
        except (json.JSONDecodeError, ValueError) as e:
            # Fallback amélioré : parser manuellement le contenu
            log_error(request, e, "Erreur de parsing JSON, utilisation du fallback")
            
            lines = [line.strip() for line in generated_text.split('\n') if line.strip()]
            titre = "Article généré par IA"
            contenu = generated_text
            resume = ""
            
            # Essayer d'extraire un titre des premières lignes
            for line in lines[:3]:
                if len(line) > 10 and len(line) < 100 and not line.startswith('{'):
                    titre = line.replace('"', '').replace("'", "")
                    break
            
            article_data = {
                'titre': titre,
                'resume': resume,
                'contenu': f"<p>{contenu.replace(chr(10), '</p><p>')}</p>"
            }
        
        result_data = {
            'success': True,
            'titre': article_data.get('titre', ''),
            'resume': article_data.get('resume', ''),
            'contenu': article_data.get('contenu', ''),
            'message': 'Article généré avec succès !'
        }
        
        # Génération de l'image de couverture avec DALL-E si demandée
        if generer_image:
            try:
                # Prompt simplifié pour l'image
                image_prompt = f"Professional blog cover image about: {prompt}. Modern, clean, professional style, no text overlay."
                
                dalle_payload = {
                    "model": "dall-e-3",
                    "prompt": image_prompt[:400],  # Limiter la taille du prompt
                    "n": 1,
                    "size": "1024x1024",
                    "quality": "standard",
                    "response_format": "b64_json"
                }
                
                # Timeout plus long pour DALL-E
                dalle_response = requests.post(
                    'https://api.openai.com/v1/images/generations',
                    headers=headers,
                    json=dalle_payload,
                    timeout=90  # 90 secondes pour DALL-E
                )
                
                if dalle_response.status_code == 200:
                    dalle_data = dalle_response.json()
                    if 'data' in dalle_data and len(dalle_data['data']) > 0:
                        # Décoder l'image base64
                        image_b64 = dalle_data['data'][0]['b64_json']
                        
                        # Créer un nom de fichier unique
                        import uuid
                        filename = f"ai_generated_{uuid.uuid4().hex[:8]}.png"
                        
                        # Sauvegarder l'image temporairement en base64 pour l'affichage
                        result_data['image_generated'] = True
                        result_data['image_data'] = f"data:image/png;base64,{image_b64}"
                        result_data['image_filename'] = filename
                        result_data['message'] = 'Article et image générés avec succès !'
                    else:
                        result_data['image_error'] = 'Aucune image générée par DALL-E'
                else:
                    error_msg = f"Erreur DALL-E: {dalle_response.status_code}"
                    if dalle_response.text:
                        try:
                            error_data = dalle_response.json()
                            if 'error' in error_data:
                                error_msg = error_data['error'].get('message', error_msg)
                        except:
                            pass
                    result_data['image_error'] = error_msg
                    
            except requests.exceptions.Timeout:
                result_data['image_error'] = 'Timeout lors de la génération d\'image. L\'article a été créé sans image.'
                log_error(request, Exception("Timeout DALL-E"), "Timeout lors de la génération d'image")
                
            except Exception as e:
                log_error(request, e, "Erreur lors de la génération d'image avec DALL-E")
                result_data['image_error'] = f'Erreur lors de la génération d\'image: {str(e)}'
        
        # Log de l'action
        log_content_action(request, 'GENERATION_IA_OPENAI', 'Article', None,
                         f"Prompt: {prompt[:100]}..., Image: {generer_image}")
        
        return JsonResponse(result_data)
        
    except requests.exceptions.Timeout:
        log_error(request, Exception("Timeout général"), "Timeout lors de la génération d'article")
        return JsonResponse({
            'error': 'La génération prend trop de temps. Essayez avec un prompt plus court.'
        }, status=408)
        
    except requests.RequestException as e:
        log_error(request, e, "Erreur de connexion à l'API OpenAI")
        return JsonResponse({
            'error': 'Erreur de connexion à l\'API OpenAI. Veuillez réessayer.'
        }, status=500)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Format de données invalide'}, status=400)
        
    except Exception as e:
        log_error(request, e, "Erreur lors de la génération d'article avec OpenAI")
        return JsonResponse({
            'error': 'Une erreur inattendue est survenue lors de la génération.'
        }, status=500)

@login_required
@csrf_exempt
def sauvegarder_image_generee(request):
    """
    Vue pour sauvegarder une image générée par IA dans le système de fichiers
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    try:
        data = json.loads(request.body)
        image_data = data.get('image_data', '')
        filename = data.get('filename', 'generated_image.png')
        
        if not image_data.startswith('data:image/'):
            return JsonResponse({'error': 'Format d\'image invalide'}, status=400)
        
        # Extraire les données base64
        header, encoded = image_data.split(',', 1)
        image_bytes = base64.b64decode(encoded)
        
        # Créer un nom de fichier unique
        import uuid
        import os
        from django.utils import timezone
        
        name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{uuid.uuid4().hex[:8]}{ext}"
        
        # Sauvegarder dans le répertoire des images d'articles
        from django.core.files.storage import default_storage
        file_path = f"articles/covers/{unique_filename}"
        
        # Sauvegarder le fichier
        saved_path = default_storage.save(file_path, ContentFile(image_bytes))
        
        # Retourner l'URL pour utilisation dans le formulaire
        file_url = default_storage.url(saved_path)
        
        log_content_action(request, 'SAUVEGARDE_IMAGE_IA', 'Image', None,
                         f"Fichier: {unique_filename}")
        
        return JsonResponse({
            'success': True,
            'file_path': saved_path,
            'file_url': file_url,
            'filename': unique_filename
        })
        
    except Exception as e:
        log_error(request, e, "Erreur lors de la sauvegarde d'image générée")
        return JsonResponse({
            'error': 'Erreur lors de la sauvegarde de l\'image'
        }, status=500)
