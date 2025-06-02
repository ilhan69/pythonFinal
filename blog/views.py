from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from .forms import PostForm, CommentForm, CategoryForm, UserRegistrationForm, UserLoginForm
from .models import Article, Category, User

# Create your views here.
def home(request):
    posts = Article.objects.all().order_by('-created_at')
    categories = Category.objects.all()
    return render(request, 'blog/home.html', {
        'posts': posts,
        'categories': categories
    })

def home_template(request):
    articles = Article.objects.all()
    categories = Category.objects.all()
    return render(request, 'blog/home.html', {
        'articles': articles,
        'categories': categories
    })

@login_required
def ajouter_article(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            article = form.save(commit=False)
            article.author = request.user
            article.save()
            messages.success(request, "L'article a été créé avec succès !")
            return redirect('home')
    else:
        form = PostForm()
    return render(request, 'blog/ajouter_article.html', {'form': form})

def modifier_article(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    if request.method == 'POST':
        form = PostForm(request.POST, instance=article)
        if form.is_valid():
            form.save()
            messages.success(request, "L'article a été modifié avec succès !")
            return redirect('article_detail', article_id=article.id)
    else:
        form = PostForm(instance=article)
    return render(request, 'blog/modifier_article.html', {'form': form, 'article': article})

def supprimer_article(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    if request.method == 'POST':
        article.delete()
        messages.success(request, "L'article a été supprimé avec succès !")
        return redirect('home')
    return render(request, 'blog/supprimer_article.html', {'article': article})

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

def supprimer_categorie(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        category.delete()
        messages.success(request, "La catégorie a été supprimée avec succès !")
        return redirect('home')
    return render(request, 'blog/supprimer_categorie.html', {'category': category})

def article_detail(request, article_id):
    article = get_object_or_404(Article, id=article_id)
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
        form = PostForm(request.POST)
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
    posts = Article.objects.filter(category=category).order_by('-created_at')
    return render(request, 'blog/home.html', {
        'category': category,
        'posts': posts
    })

@login_required
def user_logout(request):
    logout(request)
    messages.success(request, 'Vous avez été déconnecté avec succès !')
    return redirect('home')
