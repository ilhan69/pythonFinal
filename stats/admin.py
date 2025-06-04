from django.contrib import admin
from .models import Like, Share, View

@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'content_object', 'created_at')
    list_filter = ('created_at', 'content_type')
    search_fields = ('user__username',)
    readonly_fields = ('created_at',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'content_type')

@admin.register(Share)
class ShareAdmin(admin.ModelAdmin):
    list_display = ('user', 'content_object', 'shared_at', 'ip_address')
    list_filter = ('shared_at', 'content_type')
    search_fields = ('user__username', 'ip_address')
    readonly_fields = ('shared_at',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'content_type')

@admin.register(View)
class ViewAdmin(admin.ModelAdmin):
    list_display = ('user', 'content_object', 'viewed_at', 'ip_address')
    list_filter = ('viewed_at', 'content_type')
    search_fields = ('user__username', 'ip_address')
    readonly_fields = ('viewed_at',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'content_type')
