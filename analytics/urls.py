from django.urls import path
from . import views

urlpatterns = [
    path('admin_dashboard/', views.analytics_dashboard, name='analytics_dashboard'),
]
