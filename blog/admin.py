from django.contrib import admin
from .models import User, Category, Article, ArticleComment, Tag, ArticleLike, ArticleShare

# Register your models here.

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')

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
    list_display = ('title', 'author', 'category', 'get_tags_display', 'likes_count', 'shares_count', 'views_count', 'created_at', 'updated_at')
    list_filter = ('category', 'tags', 'status', 'created_at', 'author')
    search_fields = ('title', 'content')
    filter_horizontal = ('tags',)
    
    def get_tags_display(self, obj):
        """Affiche les tags de l'article dans la liste d'administration"""
        return ", ".join([tag.name for tag in obj.tags.all()[:3]])
    get_tags_display.short_description = 'Tags'

@admin.register(ArticleComment)
class ArticleCommentAdmin(admin.ModelAdmin):
    list_display = ('article', 'author', 'comment_preview', 'created_at')
    list_filter = ('created_at', 'article__category')
    search_fields = ('comment', 'article__title', 'author__username')
    
    def comment_preview(self, obj):
        """Affiche un aperçu du commentaire"""
        return obj.comment[:50] + "..." if len(obj.comment) > 50 else obj.comment
    comment_preview.short_description = 'Aperçu'

@admin.register(ArticleLike)
class ArticleLikeAdmin(admin.ModelAdmin):
    list_display = ('article', 'user', 'created_at')
    list_filter = ('created_at', 'article__category')
    search_fields = ('article__title', 'user__username')
    raw_id_fields = ('article', 'user')

@admin.register(ArticleShare)
class ArticleShareAdmin(admin.ModelAdmin):
    list_display = ('article', 'user', 'shared_at', 'ip_address')
    list_filter = ('shared_at', 'article__category')
    search_fields = ('article__title', 'user__username', 'ip_address')
    raw_id_fields = ('article', 'user')
    readonly_fields = ('ip_address', 'user_agent')
