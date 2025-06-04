from django.contrib import admin
from .models import Comment

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'content_object', 'content', 'created_at', 'is_active')
    list_filter = ('is_active', 'created_at', 'content_type')
    search_fields = ('content', 'author__username')
    readonly_fields = ('created_at', 'updated_at')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('author', 'content_type')
