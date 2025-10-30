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
from django.http import JsonResponse
from django.db.models import Sum
from .ai_engine import train_model, predict_category
from datetime import datetime

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


# tracker/views.py

# tracker/views.py

@login_required
def dashboard(request):
    """The main dashboard page, now with ANOMALY DETECTION."""
    
    # --- ANOMALY DETECTION LOGIC ---
    alerts = []
    try:
        # Get all transactions for the user
        transactions = Transaction.objects.filter(user=request.user)
        
        if transactions.count() > 0:
            # Convert to pandas DataFrame
            df = pd.DataFrame(list(transactions.values('date', 'category', 'amount')))
            df['date'] = pd.to_datetime(df['date'])
            df['amount'] = pd.to_numeric(df['amount'])
            
            # Get current month and year
            now = datetime.now()
            current_month = now.month
            current_year = now.year
            
            # --- 1. Calculate current month's spending ---
            current_month_df = df[
                (df['date'].dt.month == current_month) & (df['date'].dt.year == current_year)
            ]
            current_spending = current_month_df.groupby('category')['amount'].sum()

            # --- 2. Calculate average spending for past months ---
            past_months_df = df[
                (df['date'].dt.month != current_month) | (df['date'].dt.year != current_year)
            ]
            
            if not past_months_df.empty:
                # Group by month, year, and category
                monthly_spending = past_months_df.groupby(
                    [past_months_df['date'].dt.to_period('M'), 'category']
                )['amount'].sum().reset_index()
                
                # Now, find the average *per category* across all past months
                average_spending = monthly_spending.groupby('category')['amount'].mean()

                # --- 3. Compare and find anomalies ---
                for category, current_total in current_spending.items():
                    if category in average_spending:
                        average = average_spending[category]
                        # We'll define "unusual" as 200% (2x) the average
                        if average > 0 and current_total > (average * 2):
                            alerts.append(
                                f"Unusual spending in {category}! You've spent ${current_total:,.2f} this month, "
                                f"which is more than 2x your average of ${average:,.2f}."
                            )
    except Exception as e:
        # Don't crash the page if analytics fail
        alerts.append(f"Could not check for anomalies: {e}")
    # --- END ANOMALY DETECTION ---


    # --- File Upload Logic (starts here) ---
    form = CSVUploadForm()
    if request.method == 'POST':
        # ... (all your existing file upload and AI code stays here) ...
        # ... (no changes needed to the POST block) ...
        form = CSVUploadForm(request.POST, request.FILES)
        
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            
            if not csv_file.name.endswith('.csv'):
                messages.error(request, 'This is not a CSV file.')
            else:
                
                # --- AI TRAINING STEP ---
                model, vectorizer = train_model(request.user)
                if model:
                    messages.info(request, 'AI "Brain" trained on your existing data.')
                else:
                    messages.info(request, 'Not enough data to train AI. Categories will be blank.')
                
                try:
                    file_data = csv_file.read().decode('utf-8')
                    csv_data = io.StringIO(file_data)
                    df = pd.read_csv(csv_data)
                    
                    transactions_saved = 0
                    for index, row in df.iterrows():
                        
                        # --- AI PREDICTION STEP ---
                        predicted_category = None 
                        if model and vectorizer:
                            try:
                                predicted_category = predict_category(model, vectorizer, row['Description'])
                            except:
                                predicted_category = None
                        
                        Transaction.objects.create(
                            user=request.user,
                            date=row['Date'],
                            description=row['Description'],
                            amount=row['Amount'],
                            category=predicted_category 
                        )
                        transactions_saved += 1
                    
                    messages.success(request, f'File uploaded! {transactions_saved} new transactions saved.')
                    return redirect('dashboard') 
                
                except Exception as e:
                    messages.error(request, f'Error processing file: {e}')

    # --- Context (to send data to template) ---
    # We must re-fetch transactions here for the table
    all_transactions = Transaction.objects.filter(user=request.user).order_by('-date')
    
    context = {
        'transactions': all_transactions, # For the table
        'form': form,
        'categories': CATEGORY_CHOICES,
        'alerts': alerts, # <-- SEND OUR NEW ALERTS!
    }
    return render(request, 'tracker/dashboard.html', context)
# tracker/views.py

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
            
    # --- THIS IS THE FIX ---
    # This line MUST be outside the 'if' block.
    # It should be the very last line of the function.
    return redirect('dashboard')
# tracker/views.py

@login_required
def spending_chart_data(request):
    """View to provide data for the spending pie chart."""

    # Get all transactions for the user
    user_transactions = Transaction.objects.filter(user=request.user)

    # Group by category and sum the amounts
    # This creates a list of dictionaries, e.g.:
    # [{'category': 'Groceries', 'total_amount': 85.20}, ...]
    category_spending = user_transactions.values('category').annotate(
        total_amount=Sum('amount')
    ).order_by('-total_amount')

    # Format the data for Chart.js
    labels = []
    data = []

    for item in category_spending:
        # Use 'Uncategorized' if category is None or empty
        category_name = item['category'] if item['category'] else 'Uncategorized'
        labels.append(category_name)
        data.append(float(item['total_amount'])) # Convert Decimal to float for JSON

    return JsonResponse({
        'labels': labels,
        'data': data,
    })

    # Redirect back to the dashboard
    return redirect('dashboard')
# tracker/views.py

@login_required
def spending_bar_chart_data(request):
    """View to provide data for the spending bar chart."""

    # Get all transactions for the user, ordered by date
    user_transactions = Transaction.objects.filter(user=request.user).order_by('date')

    # Group by date and sum the amounts
    # This creates a list of dictionaries, e.g.:
    # [{'date': datetime.date(2025, 10, 23), 'total_amount': 15.49}, ...]
    date_spending = user_transactions.values('date').annotate(
        total_amount=Sum('amount')
    ).order_by('date')

    # Format the data for Chart.js
    labels = []
    data = []

    for item in date_spending:
        # Format the date as a simple string (e.g., "Oct 23")
        labels.append(item['date'].strftime('%b %d'))
        data.append(float(item['total_amount'])) # Convert Decimal to float for JSON

    return JsonResponse({
        'labels': labels,
        'data': data,
    })

    return redirect('dashboard')

