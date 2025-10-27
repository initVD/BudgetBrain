# budgetbrain_project/urls.py
from django.contrib import admin
from django.urls import path, include  # <-- Make sure 'include' is imported

urlpatterns = [
    path('admin/', admin.site.urls),
    # Add this line:
    path('', include('tracker.urls')), # <-- Tells project to look at tracker/urls.py
]