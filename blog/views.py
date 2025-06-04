from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, F, Sum
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.utils.translation import gettext as _
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
import json
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
