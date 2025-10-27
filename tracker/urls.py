# tracker/urls.py
from django.urls import path, include
from . import views

urlpatterns = [
    # Main auth (login, logout, password change, etc.)
    # This gives us the login page at /login/
    path('', include('django.contrib.auth.urls')),
    
    # Our new registration page
    path('register/', views.register, name='register'),
    
    # Our new dashboard page
    path('dashboard/', views.dashboard, name='dashboard'),
]