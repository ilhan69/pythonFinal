from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.home, name='home'),
    path('articles/', views.liste_articles, name='liste_articles'),
    path('auteurs-actifs/', views.auteurs_actifs, name='auteurs_actifs'),
    path('category/<int:category_id>/', views.category_posts, name='category_posts'),
    path('ajouter/', views.ajouter_article, name='ajouter_article'),
    path('ajouter-categorie/', views.ajouter_categorie, name='ajouter_categorie'),
    path('ajouter-tag/', views.ajouter_tag, name='ajouter_tag'),
    path('article/<int:article_id>/', views.article_detail, name='article_detail'),
    path('article/<int:article_id>/modifier/', views.modifier_article, name='modifier_article'),
    path('article/<int:article_id>/supprimer/', views.supprimer_article, name='supprimer_article'),
    path('categorie/<int:category_id>/modifier/', views.modifier_categorie, name='modifier_categorie'),
    path('categorie/<int:category_id>/supprimer/', views.supprimer_categorie, name='supprimer_categorie'),
    path('tag/<int:tag_id>/modifier/', views.modifier_tag, name='modifier_tag'),
    path('tag/<int:tag_id>/supprimer/', views.supprimer_tag, name='supprimer_tag'),
    path('tag/<slug:tag_slug>/', views.tag_posts, name='tag_posts'),
    path('administration/statistiques-tags/', views.statistiques_tags, name='statistiques_tags'),
]
