from django import forms
from .models import Category, Transaction

TRANSACTION_TYPE_CHOICES = (
    ('Expense', 'Expense'),
    ('Income', 'Income'),
)

class CSVUploadForm(forms.Form):
    csv_file = forms.FileField()

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'budget_limit']

class TransactionForm(forms.ModelForm):
    transaction_type = forms.ChoiceField(choices=TRANSACTION_TYPE_CHOICES)

    class Meta:
        model = Transaction
        fields = ['date', 'description', 'amount', 'category', 'transaction_type']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'})
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None) 
        
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
        
        super().__init__(*args, **kwargs)
        
        if user:
            self.fields['category'].queryset = Category.objects.filter(user=user)
            
        self.fields['category'].required = False

# --- NEW CALCULATOR FORMS ---
class SavingsCalculatorForm(forms.Form):
    goal_amount = forms.DecimalField(label="Savings Goal ($)", max_digits=12, decimal_places=2)
    current_savings = forms.DecimalField(label="Current Savings ($)", max_digits=12, decimal_places=2, required=False, initial=0)
    target_date = forms.DateField(label="Target Date", widget=forms.DateInput(attrs={'type': 'date'}))

class LoanCalculatorForm(forms.Form):
    loan_amount = forms.DecimalField(label="Loan Amount ($)", max_digits=12, decimal_places=2)
    interest_rate = forms.DecimalField(label="Annual Interest Rate (%)", max_digits=5, decimal_places=2)
    term_years = forms.IntegerField(label="Loan Term (Years)")