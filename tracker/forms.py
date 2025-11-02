from django import forms
from .models import Category, Transaction

# --- THIS IS NEW ---
# We define the choices for our new dropdown
TRANSACTION_TYPE_CHOICES = (
    ('Expense', 'Expense'),
    ('Income', 'Income'),
)

class CSVUploadForm(forms.Form):
    csv_file = forms.FileField()

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']

class TransactionForm(forms.ModelForm):
    # --- THIS IS NEW ---
    # A new field that is *not* in our database model
    # This will be the "Income" or "Expense" dropdown
    transaction_type = forms.ChoiceField(choices=TRANSACTION_TYPE_CHOICES)

    class Meta:
        model = Transaction
        # These are the fields the user is allowed to edit
        fields = ['date', 'description', 'amount', 'category', 'transaction_type']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'})
        }

    def __init__(self, *args, **kwargs):
        # Get the 'user' we'll pass in from the view
        user = kwargs.pop('user', None) 
        
        # --- NEW: Get initial data for edit form ---
        initial = kwargs.get('initial', {})
        instance = kwargs.get('instance')
        if instance:
            if instance.amount > 0:
                initial['transaction_type'] = 'Income'
                initial['amount'] = abs(instance.amount)
            else:
                initial['transaction_type'] = 'Expense'
                initial['amount'] = abs(instance.amount)
        kwargs['initial'] = initial
        # --- END NEW ---
        
        super().__init__(*args, **kwargs)
        
        # If a user was passed in, filter the category dropdown
        if user:
            self.fields['category'].queryset = Category.objects.filter(user=user)
            
        # Make the 'category' field NOT required, since income might not have one
        self.fields['category'].required = False