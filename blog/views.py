from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count, Q
import json
from .forms import PostForm, CommentForm, CategoryForm, TagForm, UserRegistrationForm, UserLoginForm
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
                messages.success(request, "L'article a été créé avec succès !")
                return redirect('home')
            except Exception as e:
                messages.error(request, f"Erreur lors de l'enregistrement : {str(e)}")
                print(f"Erreur détaillée : {e}")  # Pour le debug
        else:
            # Afficher les erreurs du formulaire
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Erreur dans le champ '{field}': {error}")
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
            messages.success(request, "L'article a été modifié avec succès !")
            return redirect('article_detail', article_id=article.id)
    else:
        form = PostForm(instance=article)
    return render(request, 'blog/modifier_article.html', {'form': form, 'article': article})

@login_required
def supprimer_article(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    if request.method == 'POST':
        article.delete()
        messages.success(request, "L'article a été supprimé avec succès !")
        return redirect('home')
    return render(request, 'blog/supprimer_article.html', {'article': article})

@login_required
def ajouter_categorie(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "La catégorie a été créée avec succès !")
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
            messages.success(request, "La catégorie a été modifiée avec succès !")
            return redirect('home')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'blog/modifier_categorie.html', {'form': form, 'category': category})

@login_required
def supprimer_categorie(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        category.delete()
        messages.success(request, "La catégorie a été supprimée avec succès !")
        return redirect('home')
    return render(request, 'blog/supprimer_categorie.html', {'category': category})

@login_required
def ajouter_tag(request):
    if request.method == 'POST':
        form = TagForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Le tag a été créé avec succès !")
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
            messages.success(request, "Le tag a été modifié avec succès !")
            return redirect('home')
    else:
        form = TagForm(instance=tag)
    return render(request, 'blog/modifier_tag.html', {'form': form, 'tag': tag})

@login_required
def supprimer_tag(request, tag_id):
    tag = get_object_or_404(Tag, id=tag_id)
    if request.method == 'POST':
        tag.delete()
        messages.success(request, "Le tag a été supprimé avec succès !")
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
            messages.success(request, "Votre commentaire a été ajouté avec succès !")
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
            messages.success(request, 'Votre compte a été créé avec succès !')
            return redirect('home')
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
                messages.success(request, 'Vous êtes maintenant connecté !')
                return redirect('home')
    else:
        form = UserLoginForm()
    return render(request, 'blog/login.html', {'form': form})

@login_required
def profile(request):
    user_posts = Article.objects.filter(author=request.user)
    return render(request, 'blog/profile.html', {
        'user': request.user,
        'posts': user_posts
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
            return redirect('post_detail', post_id=post.id)
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
            return redirect('post_detail', post_id=post.id)
    else:
        form = PostForm()
    return render(request, 'blog/ajouter_article.html', {'form': form})

@login_required
def create_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')
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
    messages.success(request, 'Vous avez été déconnecté avec succès !')
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
        message = 'Article liké avec succès!'
    else:
        # Unlike - supprimer le like existant
        like.delete()
        article.likes_count = max(0, article.likes_count - 1)
        article.save(update_fields=['likes_count'])
        liked = False
        message = 'Like retiré avec succès!'
    
    return JsonResponse({
        'success': True,
        'liked': liked,
        'likes_count': article.likes_count,
        'message': message
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
        'message': 'Article partagé avec succès!'
    })
