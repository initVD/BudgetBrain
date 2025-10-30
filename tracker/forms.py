from django import forms
from .models import Category, Transaction  # <-- You need this line

class CSVUploadForm(forms.Form):
    csv_file = forms.FileField()

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['date', 'description', 'amount', 'category']
        # This will use the HTML5 date picker
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'})
        }

    def __init__(self, *args, **kwargs):
        # Get the 'user' we'll pass in from the view
        user = kwargs.pop('user', None) 
        super().__init__(*args, **kwargs)
        
        # If a user was passed in, filter the category dropdown
        if user:
            self.fields['category'].queryset = Category.objects.filter(user=user)