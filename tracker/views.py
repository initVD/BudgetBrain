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
from .forms import CSVUploadForm, CategoryForm, TransactionForm
from .ai_engine import train_models, predict_transaction, create_pretrained_models 

# --- Load the Pre-Trained AI "Brain" when the server starts! ---
print("Training pre-trained AI model from CSV... this may take a moment.")
PRE_TRAINED_MODELS = create_pretrained_models()
if PRE_TRAINED_MODELS:
    print("Pre-trained AI model loaded successfully!")
else:
    print("WARNING: 'financial_dataset_24000_realistic.csv' not found. AI will not be pre-trained.")
# --- END NEW ---

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
            df = pd.DataFrame(list(transactions.values('date', 'category__name', 'amount')))
            df['date'] = pd.to_datetime(df['date'])
            df['amount'] = pd.to_numeric(df['amount'])
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
                    current_expense = abs(current_total) if current_total < 0 else 0
                    average_expense = abs(average_spending.get(category, 0)) if average_spending.get(category, 0) < 0 else 0
                    
                    if average_expense > 0 and current_expense > (average_expense * 2):
                        alerts.append(
                            f"Unusual spending in {category}! You've spent ${current_expense:,.2f} this month, "
                            f"which is more than 2x your average of ${average_expense:,.2f}."
                        )
    except Exception as e:
        alerts.append(f"Could not check for anomalies: {e}")
    # --- END ANOMALY DETECTION ---

    # --- DUAL-FORM HANDLING ---
    if request.method == 'POST':
        
        if 'csv_submit' in request.POST:
            upload_form = CSVUploadForm(request.POST, request.FILES)
            manual_form = TransactionForm(user=request.user) 
            
            if upload_form.is_valid():
                csv_file = request.FILES['csv_file']
                if not csv_file.name.endswith('.csv'):
                    messages.error(request, 'This is not a CSV file.')
                else:
                    
                    models = train_models(request.user) 
                    if not models:
                        models = PRE_TRAINED_MODELS
                    
                    if models:
                        messages.info(request, 'AI "Brain" is active.')
                    else:
                        messages.info(request, 'No AI model found. Uploading as uncategorized.')
                    
                    try:
                        file_data = csv_file.read().decode('utf-8')
                        csv_data = io.StringIO(file_data)
                        df = pd.read_csv(csv_data)
                        
                        transactions_saved = 0
                        for index, row in df.iterrows():
                            
                            description = row['Transaction Description']
                            amount = abs(pd.to_numeric(row['Amount ($)'])) 
                            
                            predicted_type = 'Expense' 
                            predicted_category_obj = None
                            
                            if models:
                                try:
                                    predicted_type, predicted_cat_name = predict_transaction(models, description)
                                    if predicted_cat_name:
                                        predicted_category_obj = Category.objects.get(user=request.user, name=predicted_cat_name)
                                except Category.DoesNotExist:
                                    predicted_category_obj = Category.objects.create(user=request.user, name=predicted_cat_name)
                                except:
                                    pass 
                            
                            if predicted_type == 'Expense':
                                amount = -amount
                            
                            # --- THIS IS THE FIX ---
                            try:
                                # Try to find a 'Date' column
                                transaction_date = pd.to_datetime(row['Date'])
                            except KeyError:
                                # If 'Date' column doesn't exist, use today's date
                                transaction_date = datetime.now().date()
                            # --- END OF FIX ---
                            
                            Transaction.objects.create(
                                user=request.user,
                                date=transaction_date, # <-- Use our new, safe variable
                                description=description,
                                amount=amount,
                                category=predicted_category_obj
                            )
                            transactions_saved += 1
                        
                        messages.success(request, f'File uploaded! {transactions_saved} new transactions saved.')
                    
                    except KeyError:
                        # --- THIS IS THE SECOND FIX ---
                        # Updated the error message
                        messages.error(request, "Error: The CSV file must have columns named 'Transaction Description' and 'Amount ($)'.")
                    except Exception as e:
                        messages.error(request, f'Error processing file: {e}')
                return redirect('dashboard') 

        elif 'manual_submit' in request.POST:
            manual_form = TransactionForm(request.POST, user=request.user)
            upload_form = CSVUploadForm() 
            
            if manual_form.is_valid():
                transaction_type = manual_form.cleaned_data['transaction_type']
                amount = manual_form.cleaned_data['amount']
                transaction = manual_form.save(commit=False)
                transaction.user = request.user
                
                if transaction_type == 'Expense':
                    transaction.amount = -abs(amount)
                else:
                    transaction.amount = abs(amount)
                
                transaction.save()
                messages.success(request, 'Transaction added!')
                return redirect('dashboard')
    
    else:
        upload_form = CSVUploadForm()
        manual_form = TransactionForm(user=request.user)
    # --- END DUAL-FORM HANDLING ---

    # --- Context (to send data to template) ---
    all_transactions = Transaction.objects.filter(user=request.user).order_by('-date')
    
    total_income = all_transactions.filter(amount__gt=0).aggregate(Sum('amount'))['amount__sum'] or 0
    total_expenses = all_transactions.filter(amount__lt=0).aggregate(Sum('amount'))['amount__sum'] or 0
    net_balance = total_income + total_expenses
    
    user_categories = Category.objects.filter(user=request.user)
    
    context = {
        'transactions': all_transactions,
        'upload_form': upload_form,
        'manual_form': manual_form,
        'categories': user_categories,
        'alerts': alerts,
        'total_income': total_income,
        'total_expenses': abs(total_expenses),
        'net_balance': net_balance,
    }
    return render(request, 'tracker/dashboard.html', context)

# --- Category & Transaction Management Views ---
@login_required
def manage_categories(request):
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
    context = {'form': form, 'categories': categories}
    return render(request, 'tracker/manage_categories.html', context)

@login_required
def update_all_categories(request):
    if request.method == 'POST':
        for key, value in request.POST.items():
            if key.startswith('category_'):
                transaction_id = key.split('_')[1]
                try:
                    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)
                    new_category_id = value
                    if (new_category_id == "" and transaction.category is not None) or \
                       (new_category_id != "" and str(transaction.category_id) != new_category_id):
                        
                        if new_category_id:
                            new_category = get_object_or_404(Category, id=new_category_id, user=request.user)
                            transaction.category = new_category
                        else:
                            transaction.category = None
                        transaction.save()
                except Exception as e:
                    messages.error(request, f"Could not update transaction {transaction_id}: {e}")
        messages.success(request, 'All changes saved!')
        try:
            train_models(request.user) 
            messages.info(request, 'AI "Brain" has been retrained with your changes.')
        except:
            messages.warning(request, 'AI could not be retrained.')
    return redirect('dashboard')

@login_required
def delete_transaction(request, pk):
    transaction = get_object_or_404(Transaction, id=pk, user=request.user)
    if request.method == 'POST':
        transaction.delete()
        messages.success(request, 'Transaction deleted.')
        return redirect('dashboard')
    context = {'transaction': transaction}
    return render(request, 'tracker/delete_transaction.html', context)

@login_required
def delete_all_transactions(request):
    if request.method == 'POST':
        Transaction.objects.filter(user=request.user).delete()
        messages.success(request, 'All transactions have been deleted.')
        return redirect('dashboard')
    return render(request, 'tracker/delete_all_confirm.html')

@login_required
def edit_transaction(request, pk):
    transaction = get_object_or_404(Transaction, id=pk, user=request.user)
    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction, user=request.user)
        if form.is_valid():
            transaction_type = form.cleaned_data['transaction_type']
            amount = form.cleaned_data['amount']
            edited_transaction = form.save(commit=False)
            if transaction_type == 'Expense':
                edited_transaction.amount = -abs(amount)
            else:
                edited_transaction.amount = abs(amount)
            edited_transaction.save()
            messages.success(request, 'Transaction updated!')
            return redirect('dashboard')
    else:
        form = TransactionForm(instance=transaction, user=request.user)
    context = {'form': form, 'transaction': transaction}
    return render(request, 'tracker/edit_transaction.html', context)

@login_required
def retrain_ai(request):
    if request.method == 'POST':
        try:
            models = train_models(request.user) 
            if models: 
                messages.success(request, 'AI "Brain" has been retrained on all your data!')
            else:
                messages.warning(request, 'Not enough data to train the AI. Categorize more transactions first.')
        except Exception as e:
            messages.error(request, f'An error occurred during retraining: {e}')
    return redirect('manage_categories')

# --- Chart Data Views (JSON) ---
@login_required
def spending_chart_data(request):
    user_transactions = Transaction.objects.filter(user=request.user, amount__lt=0)
    category_spending = user_transactions.values('category__name').annotate(
        total_amount=Sum('amount')
    ).order_by('-total_amount')
    labels = []
    data = []
    for item in category_spending:
        category_name = item['category__name'] if item['category__name'] else 'Uncategorized'
        labels.append(category_name)
        data.append(float(abs(item['total_amount'])))
    return JsonResponse({'labels': labels, 'data': data})

@login_required
def spending_bar_chart_data(request):
    user_transactions = Transaction.objects.filter(user=request.user, amount__lt=0).order_by('date')
    date_spending = user_transactions.values('date').annotate(
        total_amount=Sum('amount')
    ).order_by('date')
    labels = []
    data = []
    for item in date_spending:
        labels.append(item['date'].strftime('%b %d'))
        data.append(float(abs(item['total_amount'])))
    return JsonResponse({'labels': labels, 'data': data})