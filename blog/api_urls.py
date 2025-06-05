from django.urls import path, include
from . import api_views

app_name = 'blog_api'

urlpatterns = [
    # Articles
    path('articles/', api_views.ArticleListAPIView.as_view(), name='article-list'),
    path('articles/<slug:slug>/', api_views.ArticleDetailAPIView.as_view(), name='article-detail'),
    
    # Commentaires
    path('articles/<slug:article_slug>/comments/', api_views.CommentListAPIView.as_view(), name='comment-list'),
    path('comments/<int:comment_id>/', api_views.CommentDetailAPIView.as_view(), name='comment-detail'),
    
    # Likes
    path('articles/<slug:article_slug>/like/', api_views.LikeAPIView.as_view(), name='article-like'),
    
    # Catégories et Tags
    path('categories/', api_views.CategoryListAPIView.as_view(), name='category-list'),
    path('tags/', api_views.TagListAPIView.as_view(), name='tag-list'),
    
    # Statistiques
    path('stats/', api_views.StatsAPIView.as_view(), name='stats'),
]