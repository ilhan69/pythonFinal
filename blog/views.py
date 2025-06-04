from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, F
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.utils.translation import gettext as _
from django.contrib.contenttypes.models import ContentType
import json
from .forms import PostForm, CategoryForm, TagForm
from .models import Article, Category, Tag
from comments.models import Comment
from comments.forms import CommentForm
from stats.models import Like, Share, View
from users.decorators import admin_required, auteur_required, article_owner_required

# Create your views here.
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
def ajouter_article(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                article = form.save(commit=False)
                article.author = request.user
                article.save()
                form.save_m2m()
                messages.success(request, _("L'article a été créé avec succès !"))
                return redirect('blog:home')
            except Exception as e:
                messages.error(request, _("Erreur lors de l'enregistrement : %(error)s") % {'error': str(e)})
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, _("Erreur dans le champ '%(field)s': %(error)s") % {'field': field, 'error': error})
    else:
        form = PostForm()
    return render(request, 'blog/ajouter_article.html', {'form': form})

@article_owner_required
def modifier_article(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    # Vérification supplémentaire des permissions
    if not request.user.can_edit_article(article):
        messages.error(request, _('Vous n\'avez pas les permissions pour modifier cet article.'))
        return redirect('blog:home')
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=article)
        if form.is_valid():
            form.save()
            messages.success(request, _("L'article a été modifié avec succès !"))
            return redirect('blog:article_detail', article_id=article.id)
    else:
        form = PostForm(instance=article)
    return render(request, 'blog/modifier_article.html', {'form': form, 'article': article})

@article_owner_required
def supprimer_article(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    # Vérification supplémentaire des permissions
    if not request.user.can_delete_article(article):
        messages.error(request, _('Vous n\'avez pas les permissions pour supprimer cet article.'))
        return redirect('blog:home')
    
    if request.method == 'POST':
        article.delete()
        messages.success(request, _("L'article a été supprimé avec succès !"))
        return redirect('blog:home')
    return render(request, 'blog/supprimer_article.html', {'article': article})

@admin_required
def ajouter_categorie(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _("La catégorie a été créée avec succès !"))
            return redirect('blog:home')
    else:
        form = CategoryForm()
    return render(request, 'blog/ajouter_categorie.html', {'form': form})

@admin_required
def modifier_categorie(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, _("La catégorie a été modifiée avec succès !"))
            return redirect('blog:home')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'blog/modifier_categorie.html', {'form': form, 'category': category})

@admin_required
def supprimer_categorie(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        category.delete()
        messages.success(request, _("La catégorie a été supprimée avec succès !"))
        return redirect('blog:home')
    return render(request, 'blog/supprimer_categorie.html', {'category': category})

@admin_required
def ajouter_tag(request):
    if request.method == 'POST':
        form = TagForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _("Le tag a été créé avec succès !"))
            return redirect('blog:home')
    else:
        form = TagForm()
    return render(request, 'blog/ajouter_tag.html', {'form': form})

@admin_required
def modifier_tag(request, tag_id):
    tag = get_object_or_404(Tag, id=tag_id)
    if request.method == 'POST':
        form = TagForm(request.POST, instance=tag)
        if form.is_valid():
            form.save()
            messages.success(request, _("Le tag a été modifié avec succès !"))
            return redirect('blog:home')
    else:
        form = TagForm(instance=tag)
    return render(request, 'blog/modifier_tag.html', {'form': form, 'tag': tag})

@admin_required
def supprimer_tag(request, tag_id):
    tag = get_object_or_404(Tag, id=tag_id)
    if request.method == 'POST':
        tag.delete()
        messages.success(request, _("Le tag a été supprimé avec succès !"))
        return redirect('blog:home')
    return render(request, 'blog/supprimer_tag.html', {'tag': tag})

def article_detail(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    
    # Enregistrer une vue
    if request.method == 'GET':
        content_type = ContentType.objects.get_for_model(Article)
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
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
    
    # Récupérer les commentaires via la relation générique
    comments = article.comments.filter(is_active=True).order_by('-created_at')
    
    if request.method == 'POST' and request.user.is_authenticated:
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.content_type = ContentType.objects.get_for_model(Article)
            comment.object_id = article.id
            comment.save()
            messages.success(request, _("Votre commentaire a été ajouté avec succès !"))
            return redirect('blog:article_detail', article_id=article.id)
    else:
        form = CommentForm()
    
    return render(request, 'blog/article_detail.html', {
        'article': article,
        'comments': comments,
        'form': form
    })

def category_posts(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    posts = Article.objects.filter(category=category, status='published').order_by('-created_at')
    return render(request, 'blog/home.html', {
        'category': category,
        'posts': posts
    })

def tag_posts(request, tag_slug):
    tag = get_object_or_404(Tag, slug=tag_slug)
    posts = Article.objects.filter(tags=tag, status='published').order_by('-created_at')
    return render(request, 'blog/home.html', {
        'tag': tag,
        'posts': posts
    })

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
