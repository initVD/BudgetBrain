# tracker/forms.py
from django import forms
from .models import Category # <-- Make sure this is here too

class CSVUploadForm(forms.Form):
    # This field will be rendered as an <input type="file">
    csv_file = forms.FileField()

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']