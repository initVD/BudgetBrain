from django.urls import path, include
from . import views

urlpatterns = [
    # Main auth (login, logout, password change, etc.)
    path('', include('django.contrib.auth.urls')),
    
    # Registration page
    path('register/', views.register, name='register'),
    
    # Main dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Data endpoints for charts
    path('chart_data/', views.spending_chart_data, name='spending_chart_data'),
    path('bar_chart_data/', views.spending_bar_chart_data, name='spending_bar_chart_data'),
    
    # Page to manage categories
    path('categories/', views.manage_categories, name='manage_categories'),
    
    # CRUD for Transactions
    path('delete_transaction/<int:pk>/', views.delete_transaction, name='delete_transaction'),
    path('edit_transaction/<int:pk>/', views.edit_transaction, name='edit_transaction'),
    path('delete_all/', views.delete_all_transactions, name='delete_all_transactions'),
    
    # AI Triggers
    path('retrain_ai/', views.retrain_ai, name='retrain_ai'),
    path('update_all/', views.update_all_categories, name='update_all_categories'),

    # Export Features
    path('export/', views.export_transactions_csv, name='export_transactions_csv'),
    path('export_pdf/', views.export_transactions_pdf, name='export_transactions_pdf'),
    
    # Tools
    # Codes
    path('tools/', views.calculators, name='calculators'),
]