from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Informations supplémentaires', {'fields': ('bio', 'avatar', 'role')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Informations supplémentaires', {'fields': ('bio', 'avatar', 'role')}),
    )
    list_display = BaseUserAdmin.list_display + ('role', 'is_active')
    list_filter = BaseUserAdmin.list_filter + ('role',)
    search_fields = BaseUserAdmin.search_fields + ('bio',)
