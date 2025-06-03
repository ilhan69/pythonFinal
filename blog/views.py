from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count, Q, F
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.utils.translation import gettext as _, gettext_lazy
from django.utils import translation
import json
from .forms import PostForm, CommentForm, CategoryForm, TagForm, UserRegistrationForm, UserLoginForm, UserProfileForm
from .models import Article, Category, Tag, User, ArticleLike, ArticleShare

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

def home_template(request):
    # Afficher seulement les articles publiés
    articles = Article.objects.filter(status='published').order_by('-created_at')
    categories = Category.objects.all()
    tags = Tag.objects.all().order_by('name')
    return render(request, 'blog/home.html', {
        'articles': articles,
        'categories': categories,
        'tags': tags
    })

@login_required
def ajouter_article(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                article = form.save(commit=False)
                article.author = request.user
                article.save()
                form.save_m2m()  # Important pour sauvegarder les relations many-to-many
                messages.success(request, _("L'article a été créé avec succès !"))
                return redirect('home')
            except Exception as e:
                messages.error(request, _("Erreur lors de l'enregistrement : %(error)s") % {'error': str(e)})
                print(f"Erreur détaillée : {e}")  # Pour le debug
        else:
            # Afficher les erreurs du formulaire
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, _("Erreur dans le champ '%(field)s': %(error)s") % {'field': field, 'error': error})
            print(f"Erreurs du formulaire : {form.errors}")  # Pour le debug
    else:
        form = PostForm()
    return render(request, 'blog/ajouter_article.html', {'form': form})

@login_required
def modifier_article(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=article)
        if form.is_valid():
            form.save()
            messages.success(request, _("L'article a été modifié avec succès !"))
            return redirect('article_detail', article_id=article.id)
    else:
        form = PostForm(instance=article)
    return render(request, 'blog/modifier_article.html', {'form': form, 'article': article})

@login_required
def supprimer_article(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    if request.method == 'POST':
        article.delete()
        messages.success(request, _("L'article a été supprimé avec succès !"))
        return redirect('home')
    return render(request, 'blog/supprimer_article.html', {'article': article})

@login_required
def ajouter_categorie(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _("La catégorie a été créée avec succès !"))
            return redirect('home')
    else:
        form = CategoryForm()
    return render(request, 'blog/ajouter_categorie.html', {'form': form})

@login_required
def modifier_categorie(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, _("La catégorie a été modifiée avec succès !"))
            return redirect('home')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'blog/modifier_categorie.html', {'form': form, 'category': category})

@login_required
def supprimer_categorie(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        category.delete()
        messages.success(request, _("La catégorie a été supprimée avec succès !"))
        return redirect('home')
    return render(request, 'blog/supprimer_categorie.html', {'category': category})

@login_required
def ajouter_tag(request):
    if request.method == 'POST':
        form = TagForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _("Le tag a été créé avec succès !"))
            return redirect('home')
    else:
        form = TagForm()
    return render(request, 'blog/ajouter_tag.html', {'form': form})

@login_required
def modifier_tag(request, tag_id):
    tag = get_object_or_404(Tag, id=tag_id)
    if request.method == 'POST':
        form = TagForm(request.POST, instance=tag)
        if form.is_valid():
            form.save()
            messages.success(request, _("Le tag a été modifié avec succès !"))
            return redirect('home')
    else:
        form = TagForm(instance=tag)
    return render(request, 'blog/modifier_tag.html', {'form': form, 'tag': tag})

@login_required
def supprimer_tag(request, tag_id):
    tag = get_object_or_404(Tag, id=tag_id)
    if request.method == 'POST':
        tag.delete()
        messages.success(request, _("Le tag a été supprimé avec succès !"))
        return redirect('home')
    return render(request, 'blog/supprimer_tag.html', {'tag': tag})

def article_detail(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    # Incrémenter le compteur de vues
    article.increment_views()
    
    comments = article.comments.all()
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.article = article
            comment.author = request.user
            comment.save()
            messages.success(request, _("Votre commentaire a été ajouté avec succès !"))
            return redirect('article_detail', article_id=article.id)
    else:
        form = CommentForm()
    return render(request, 'blog/article_detail.html', {
        'article': article,
        'comments': comments,
        'form': form
    })

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, _('Votre compte a été créé avec succès !'))
            return redirect('home')
        else:
            messages.error(request, _('Veuillez corriger les erreurs dans le formulaire.'))
    else:
        form = UserRegistrationForm()
    return render(request, 'blog/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = UserLoginForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, _('Vous êtes maintenant connecté !'))
                return redirect('home')
            else:
                messages.error(request, _('Nom d\'utilisateur ou mot de passe incorrect.'))
        else:
            messages.error(request, _('Veuillez corriger les erreurs dans le formulaire.'))
    else:
        form = UserLoginForm()
    return render(request, 'blog/login.html', {'form': form})

@login_required
def profile(request):
    """Vue pour afficher et modifier le profil utilisateur"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _('Votre profil a été mis à jour avec succès !'))
            return redirect('profile')
        else:
            messages.error(request, _('Veuillez corriger les erreurs ci-dessous.'))
    else:
        form = UserProfileForm(instance=request.user)
    
    # Récupérer les articles de l'utilisateur avec statistiques
    user_posts = Article.objects.filter(author=request.user).order_by('-created_at')
    
    # Statistiques utilisateur
    total_articles = user_posts.count()
    published_articles = user_posts.filter(status='published').count()
    draft_articles = user_posts.filter(status='draft').count()
    total_views = sum(post.views_count for post in user_posts)
    total_likes = sum(post.likes_count for post in user_posts)
    
    return render(request, 'blog/profile.html', {
        'user': request.user,
        'posts': user_posts,
        'form': form,
        'stats': {
            'total_articles': total_articles,
            'published_articles': published_articles,
            'draft_articles': draft_articles,
            'total_views': total_views,
            'total_likes': total_likes,
        }
    })

def post_detail(request, post_id):
    post = get_object_or_404(Article, id=post_id)
    comments = post.comments.all().order_by('-created_at')
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            messages.success(request, _("Votre commentaire a été ajouté avec succès !"))
            return redirect('post_detail', post_id=post.id)
        else:
            messages.error(request, _('Veuillez corriger les erreurs dans le formulaire.'))
    else:
        form = CommentForm()
    
    return render(request, 'blog/post_detail.html', {
        'post': post,
        'comments': comments,
        'form': form
    })

@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            form.save_m2m()
            messages.success(request, _("L'article a été créé avec succès !"))
            return redirect('post_detail', post_id=post.id)
        else:
            messages.error(request, _('Veuillez corriger les erreurs dans le formulaire.'))
    else:
        form = PostForm()
    return render(request, 'blog/ajouter_article.html', {'form': form})

@login_required
def create_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _("La catégorie a été créée avec succès !"))
            return redirect('home')
        else:
            messages.error(request, _('Veuillez corriger les erreurs dans le formulaire.'))
    else:
        form = CategoryForm()
    return render(request, 'blog/ajouter_categorie.html', {'form': form})

def category_posts(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    # Afficher seulement les articles publiés de cette catégorie
    posts = Article.objects.filter(category=category, status='published').order_by('-created_at')
    return render(request, 'blog/home.html', {
        'category': category,
        'posts': posts
    })

def tag_posts(request, tag_slug):
    tag = get_object_or_404(Tag, slug=tag_slug)
    # Afficher seulement les articles publiés avec ce tag
    posts = Article.objects.filter(tags=tag, status='published').order_by('-created_at')
    return render(request, 'blog/home.html', {
        'tag': tag,
        'posts': posts
    })

@login_required
def user_logout(request):
    logout(request)
    messages.success(request, _('Vous avez été déconnecté avec succès !'))
    return redirect('home')

@require_POST
@login_required
def like_article(request, article_id):
    """Vue pour gérer les likes d'articles via AJAX"""
    article = get_object_or_404(Article, id=article_id)
    user = request.user
    
    # Vérifier si l'utilisateur a déjà liké cet article
    like, created = ArticleLike.objects.get_or_create(
        article=article,
        user=user
    )
    
    if created:
        # Nouveau like
        article.increment_likes()
        liked = True
        message = _('Article liké avec succès!')
    else:
        # Unlike - supprimer le like existant
        like.delete()
        article.likes_count = max(0, article.likes_count - 1)
        article.save(update_fields=['likes_count'])
        liked = False
        message = _('Like retiré avec succès!')
    
    return JsonResponse({
        'success': True,
        'liked': liked,
        'likes_count': article.likes_count,
        'message': str(message)
    })

@require_POST  
def share_article(request, article_id):
    """Vue pour gérer les partages d'articles via AJAX"""
    article = get_object_or_404(Article, id=article_id)
    
    # Récupérer l'adresse IP et le user agent
    ip_address = request.META.get('REMOTE_ADDR')
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    # Créer un enregistrement de partage
    share = ArticleShare.objects.create(
        article=article,
        user=request.user if request.user.is_authenticated else None,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    # Incrémenter le compteur de partages
    article.increment_shares()
    
    return JsonResponse({
        'success': True,
        'shares_count': article.shares_count,
        'message': str(_('Article partagé avec succès!'))
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
    sort_by = request.GET.get('sort', 'recent')  # recent, popular, alphabetic
    
    # Recherche full-text PostgreSQL optimisée
    if search_query:
        try:
            # Configuration avancée de la recherche PostgreSQL avec pondération
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
            # Fallback vers une recherche simple si PostgreSQL search échoue
            articles = articles.filter(
                Q(title__icontains=search_query) |
                Q(content__icontains=search_query) |
                Q(excerpt__icontains=search_query)
            ).order_by('-created_at')
    
    # Filtrage par catégorie
    if category_id:
        try:
            category_id = int(category_id)
            articles = articles.filter(category_id=category_id)
        except (ValueError, TypeError):
            pass
    
    # Filtrage par tag
    if tag_id:
        try:
            tag_id = int(tag_id)
            articles = articles.filter(tags__id=tag_id).distinct()  # distinct() pour éviter les doublons
        except (ValueError, TypeError):
            pass
    
    # Filtrage par auteur
    if author_id:
        try:
            author_id = int(author_id)
            articles = articles.filter(author_id=author_id)
        except (ValueError, TypeError):
            pass
    
    # Tri des résultats
    if not search_query:  # Si pas de recherche, appliquer le tri normal
        if sort_by == 'popular':
            # Tri par popularité optimisé avec annotation
            articles = articles.annotate(
                popularity_score=F('views_count') + F('likes_count') * 2 + F('shares_count') * 3
            ).order_by('-popularity_score', '-created_at')
        elif sort_by == 'alphabetic':
            articles = articles.order_by('title', '-created_at')
        elif sort_by == 'oldest':
            articles = articles.order_by('created_at')
        else:  # recent par défaut
            articles = articles.order_by('-created_at')
    
    # Pagination
    items_per_page = int(request.GET.get('per_page', 12))
    items_per_page = min(max(items_per_page, 6), 24)  # Entre 6 et 24 articles par page
    
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
    
    authors = User.objects.annotate(
        articles_count=Count('articles', filter=Q(articles__status='published'))
    ).filter(articles_count__gt=0).order_by('username')
    
    # Statistiques pour l'affichage
    total_articles = Article.objects.filter(status='published').count()
    filtered_count = paginator.count
    
    # Catégorie et tag sélectionnés pour l'affichage
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
