from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('change-password/', views.change_password, name='change_password'),
    
    # URLs d'administration
    path('admin/users/', views.manage_users, name='manage_users'),
    path('admin/users/add/', views.add_user, name='add_user'),
    path('admin/users/<int:user_id>/edit/', views.edit_user, name='edit_user'),
    path('admin/users/<int:user_id>/change-password/', views.admin_change_password, name='admin_change_password'),
    path('admin/users/<int:user_id>/toggle/', views.toggle_user_status, name='toggle_user_status'),
    path('admin/users/<int:user_id>/delete/', views.delete_user, name='delete_user'),
]