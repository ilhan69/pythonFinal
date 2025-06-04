from django.contrib import admin
from .models import Category, Article, Tag

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'couleur', 'get_articles_count', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'couleur', 'get_articles_count', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'get_tags_display', 'status', 'likes_count', 'shares_count', 'views_count', 'created_at', 'updated_at')
    list_filter = ('category', 'tags', 'status', 'created_at', 'author')
    search_fields = ('title', 'content')
    filter_horizontal = ('tags',)
    prepopulated_fields = {'slug': ('title',)}
    
    def get_tags_display(self, obj):
        """Affiche les tags de l'article dans la liste d'administration"""
        return ", ".join([tag.name for tag in obj.tags.all()[:3]])
    get_tags_display.short_description = 'Tags'
