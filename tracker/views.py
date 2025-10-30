from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Sum
from django.contrib import messages
import pandas as pd
import io
from datetime import datetime

from .models import Transaction, Category
from .forms import CSVUploadForm, CategoryForm
from .ai_engine import train_model, predict_category

# --- User Account Views ---

def register(request):
    """Register a new user."""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserCreationForm()
        
    context = {'form': form}
    return render(request, 'tracker/register.html', context)

# --- Main Dashboard View ---

@login_required
def dashboard(request):
    """The main dashboard page, with file upload, AI, and anomaly detection."""
    
    # --- ANOMALY DETECTION LOGIC ---
    alerts = []
    try:
        transactions = Transaction.objects.filter(user=request.user)
        
        if transactions.count() > 0:
            # We must get the category *name* using the ForeignKey relationship
            df = pd.DataFrame(list(transactions.values('date', 'category__name', 'amount')))
            df['date'] = pd.to_datetime(df['date'])
            df['amount'] = pd.to_numeric(df['amount'])
            # Rename 'category__name' to 'category' for pandas processing
            df.rename(columns={'category__name': 'category'}, inplace=True)
            
            now = datetime.now()
            current_month = now.month
            current_year = now.year
            
            current_month_df = df[
                (df['date'].dt.month == current_month) & (df['date'].dt.year == current_year)
            ]
            current_spending = current_month_df.groupby('category')['amount'].sum()

            past_months_df = df[
                (df['date'].dt.month != current_month) | (df['date'].dt.year != current_year)
            ]
            
            if not past_months_df.empty:
                monthly_spending = past_months_df.groupby(
                    [past_months_df['date'].dt.to_period('M'), 'category']
                )['amount'].sum().reset_index()
                
                average_spending = monthly_spending.groupby('category')['amount'].mean()

                for category, current_total in current_spending.items():
                    if category in average_spending:
                        average = average_spending[category]
                        if average > 0 and current_total > (average * 2):
                            alerts.append(
                                f"Unusual spending in {category}! You've spent ${current_total:,.2f} this month, "
                                f"which is more than 2x your average of ${average:,.2f}."
                            )
    except Exception as e:
        alerts.append(f"Could not check for anomalies: {e}")
    # --- END ANOMALY DETECTION ---


    # --- File Upload Logic (starts here) ---
    form = CSVUploadForm()
    if request.method == 'POST':
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
                        
                        # --- AI PREDICTION STEP (Updated for new model) ---
                        predicted_category_obj = None 
                        if model and vectorizer:
                            try:
                                # 1. AI predicts the *name*
                                predicted_name = predict_category(model, vectorizer, row['Description'])
                                # 2. We find the matching *Category object* for this user
                                predicted_category_obj = Category.objects.get(user=request.user, name=predicted_name)
                            except:
                                predicted_category_obj = None # AI failed or category doesn't exist
                        
                        Transaction.objects.create(
                            user=request.user,
                            date=row['Date'],
                            description=row['Description'],
                            amount=row['Amount'],
                            category=predicted_category_obj # Save the object (or None)
                        )
                        transactions_saved += 1
                    
                    messages.success(request, f'File uploaded! {transactions_saved} new transactions saved.')
                    return redirect('dashboard') 
                
                except Exception as e:
                    messages.error(request, f'Error processing file: {e}')
    # --- END FILE UPLOAD ---


    # --- Context (to send data to template) ---
    all_transactions = Transaction.objects.filter(user=request.user).order_by('-date')
    user_categories = Category.objects.filter(user=request.user)
    
    context = {
        'transactions': all_transactions,
        'form': form,
        'categories': user_categories,
        'alerts': alerts,
    }
    return render(request, 'tracker/dashboard.html', context)

# --- Category Management Views ---

@login_required
def manage_categories(request):
    """Page to add and view custom categories."""
    
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.user = request.user
            try:
                category.save()
                messages.success(request, 'New category added!')
            except Exception:
                messages.error(request, 'That category name already exists.')
            return redirect('manage_categories')
    else:
        form = CategoryForm()

    categories = Category.objects.filter(user=request.user).order_by('name')
    
    context = {
        'form': form,
        'categories': categories
    }
    return render(request, 'tracker/manage_categories.html', context)

@login_required
def update_category(request):
    """View to handle updating a transaction's category."""
    
    if request.method == 'POST':
        try:
            transaction_id = request.POST.get('transaction_id')
            new_category_id = request.POST.get('category')

            transaction = get_object_or_404(Transaction, id=transaction_id)

            if transaction.user == request.user:
                if new_category_id:
                    new_category = get_object_or_404(Category, id=new_category_id, user=request.user)
                    transaction.category = new_category
                else:
                    transaction.category = None # Set to Uncategorized
                
                transaction.save()
                messages.success(request, 'Category updated!')
            else:
                messages.error(request, 'You do not have permission to edit this.')
        
        except Exception as e:
            messages.error(request, f'An error occurred: {e}')
            
    return redirect('dashboard')

# --- Chart Data Views (JSON) ---

@login_required
def spending_chart_data(request):
    """View to provide data for the spending pie chart."""
    
    user_transactions = Transaction.objects.filter(user=request.user)
    
    # We must group by the category's *name*
    category_spending = user_transactions.values('category__name').annotate(
        total_amount=Sum('amount')
    ).order_by('-total_amount')
    
    labels = []
    data = []
    
    for item in category_spending:
        # 'category__name' is the field we get
        category_name = item['category__name'] if item['category__name'] else 'Uncategorized'
        labels.append(category_name)
        data.append(float(item['total_amount']))
        
    return JsonResponse({
        'labels': labels,
        'data': data,
    })

@login_required
def spending_bar_chart_data(request):
    """View to provide data for the spending bar chart."""
    
    user_transactions = Transaction.objects.filter(user=request.user).order_by('date')
    
    date_spending = user_transactions.values('date').annotate(
        total_amount=Sum('amount')
    ).order_by('date')
    
    labels = []
    data = []
    
    for item in date_spending:
        labels.append(item['date'].strftime('%b %d'))
        data.append(float(item['total_amount']))
        
    return JsonResponse({
        'labels': labels,
        'data': data,
    })