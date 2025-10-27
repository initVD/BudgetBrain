# tracker/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from .models import Transaction, CATEGORY_CHOICES
import pandas as pd  # This is the library for reading CSVs
import io            # To handle the file in memory
from .forms import CSVUploadForm
from django.contrib import messages # To show success/error messages
from django.shortcuts import get_object_or_404

def register(request):
    """Register a new user."""
    if request.method == 'POST':
        # The user submitted the form
        form = UserCreationForm(request.POST)
        if form.is_valid():
            # Form is valid, save the new user
            user = form.save()
            # Log the user in automatically
            login(request, user)
            # Send them to the dashboard (which we'll build next)
            return redirect('dashboard') 
    else:
        # The user is just visiting the page, show a blank form
        form = UserCreationForm()
        
    # Send the form to the HTML template
    context = {'form': form}
    return render(request, 'tracker/register.html', context)


@login_required
def dashboard(request):
    """The main dashboard page, now with file upload."""
    
    # Initialize the form
    form = CSVUploadForm()
    
    if request.method == 'POST':
        # This block handles the file upload
        form = CSVUploadForm(request.POST, request.FILES)
        
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            
            # Check if it's a CSV file
            if not csv_file.name.endswith('.csv'):
                messages.error(request, 'This is not a CSV file.')
            else:
                try:
                    # Read the CSV file in memory
                    file_data = csv_file.read().decode('utf-8')
                    csv_data = io.StringIO(file_data)
                    
                    # Use pandas to read the CSV
                    df = pd.read_csv(csv_data)
                    
                    # IMPORTANT: Adjust these column names if your CSV is different
                    # This assumes your CSV has columns named 'Date', 'Description', 'Amount'
                    for index, row in df.iterrows():
                        Transaction.objects.create(
                            user=request.user,
                            date=row['Date'],
                            description=row['Description'],
                            amount=row['Amount']
                        )
                    
                    messages.success(request, 'File uploaded and transactions saved.')
                    return redirect('dashboard') # Redirect to clear the form
                
                except Exception as e:
                    messages.error(request, f'Error processing file: {e}')

    # This part runs for both GET requests and if the POST form was invalid
    transactions = Transaction.objects.filter(user=request.user).order_by('-date')
    
    context = {
        'transactions': transactions,
        'form': form, # Add the form to the context
        'categories': CATEGORY_CHOICES,
    }
    return render(request, 'tracker/dashboard.html', context)

# tracker/views.py

@login_required
def update_category(request):
    """View to handle updating a transaction's category."""

    if request.method == 'POST':
        try:
            # Get the transaction ID and new category from the form
            transaction_id = request.POST.get('transaction_id')
            new_category = request.POST.get('category')

            # Find the transaction
            transaction = get_object_or_404(Transaction, id=transaction_id)

            # --- SECURITY CHECK ---
            # Make sure the transaction belongs to the logged-in user
            if transaction.user == request.user:
                transaction.category = new_category
                transaction.save()
                messages.success(request, 'Category updated!')
            else:
                messages.error(request, 'You do not have permission to edit this.')

        except Exception as e:
            messages.error(request, f'An error occurred: {e}')

    # Redirect back to the dashboard
    return redirect('dashboard')