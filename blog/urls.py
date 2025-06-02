from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('post/<int:post_id>/', views.post_detail, name='post_detail'),
    path('create-post/', views.create_post, name='create_post'),
    path('create-category/', views.create_category, name='create_category'),
    path('category/<int:category_id>/', views.category_posts, name='category_posts'),
    path('ajouter/', views.ajouter_article, name='ajouter_article'),
    path('ajouter-categorie/', views.ajouter_categorie, name='ajouter_categorie'),
    path('article/<int:article_id>/', views.article_detail, name='article_detail'),
    path('article/<int:article_id>/modifier/', views.modifier_article, name='modifier_article'),
    path('article/<int:article_id>/supprimer/', views.supprimer_article, name='supprimer_article'),
    path('categorie/<int:category_id>/modifier/', views.modifier_categorie, name='modifier_categorie'),
    path('categorie/<int:category_id>/supprimer/', views.supprimer_categorie, name='supprimer_categorie'),
]
