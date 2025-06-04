from django.urls import path
from . import views

app_name = 'stats'

urlpatterns = [
    path('like/', views.like_object, name='like_object'),
    path('share/', views.share_object, name='share_object'),
    path('view/', views.record_view, name='record_view'),
]