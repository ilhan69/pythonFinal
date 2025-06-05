from django.urls import path
from .feeds import LatestArticlesFeed, CategoryArticlesFeed, TagArticlesFeed

urlpatterns = [
    # Flux RSS principal
    path('', LatestArticlesFeed(), name='articles_feed'),
    
    # Flux RSS par catégorie
    path('category/<int:category_id>/', CategoryArticlesFeed(), name='category_feed'),
    
    # Flux RSS par tag
    path('tag/<slug:tag_slug>/', TagArticlesFeed(), name='tag_feed'),
]