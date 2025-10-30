# tracker/urls.py
from django.urls import path, include
from . import views

urlpatterns = [
    # Main auth (login, logout, password change, etc.)
    path('', include('django.contrib.auth.urls')),
    
    # Our new registration page
    path('register/', views.register, name='register'),
    
    # Our new dashboard page
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Page to update a category
    path('update_category/', views.update_category, name='update_category'),
    
    # Data endpoints for charts
    path('chart_data/', views.spending_chart_data, name='spending_chart_data'),
    path('bar_chart_data/', views.spending_bar_chart_data, name='spending_bar_chart_data'),
    
    # Page to manage categories
    path('categories/', views.manage_categories, name='manage_categories'),
    
    # --- THIS IS THE NEW URL ---
    path('delete_transaction/<int:pk>/', views.delete_transaction, name='delete_transaction'),
    path('edit_transaction/<int:pk>/', views.edit_transaction, name='edit_transaction'),
]