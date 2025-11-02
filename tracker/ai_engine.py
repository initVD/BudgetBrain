import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC  # <-- NEW
import re                          # <-- NEW
from .models import Transaction, Category
import os

TRAINING_FILE = 'financial_dataset_24000_realistic.csv'

def clean_text(text):
    """
    Cleans description text by:
    1. Making it lowercase
    2. Removing all punctuation
    3. Removing all numbers
    4. Stripping extra whitespace
    """
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\d+', '', text)
    return text.strip()


def create_pretrained_models():
    """
    Trains a powerful set of models on the 24,000-line CSV.
    This is our "Pre-Trained Brain".
    """
    if not os.path.exists(TRAINING_FILE):
        return None 

    df = pd.read_csv(TRAINING_FILE)
    
    # --- NEW: Clean the text first ---
    df['clean_description'] = df['Transaction Description'].apply(clean_text)
    
    # --- Model 1: Type Classifier (Income vs. Expense) ---
    type_vectorizer = TfidfVectorizer(ngram_range=(1, 2)) # <-- NEW: n-grams
    type_model = LinearSVC() # <-- NEW: better algorithm
    
    X_type = type_vectorizer.fit_transform(df['clean_description']) # <-- Use clean text
    y_type = df['Type']
    type_model.fit(X_type, y_type)
    
    # --- Model 2: Category Classifier (For Expenses Only) ---
    df_cat = df[df['Type'] == 'Expense'].copy()
    
    cat_vectorizer = TfidfVectorizer(ngram_range=(1, 2)) # <-- NEW: n-grams
    cat_model = LinearSVC() # <-- NEW: better algorithm
    
    X_cat = cat_vectorizer.fit_transform(df_cat['clean_description']) # <-- Use clean text
    y_cat = df_cat['Category']
    cat_model.fit(X_cat, y_cat)

    models = {
        'type_model': type_model,
        'type_vectorizer': type_vectorizer,
        'cat_model': cat_model,
        'cat_vectorizer': cat_vectorizer
    }
    return models

def train_models(user):
    """
    Trains models on the user's *own* manually-corrected data.
    """
    all_transactions = Transaction.objects.filter(user=user)
    
    if all_transactions.count() < 2:
        return None 
    
    df_type = pd.DataFrame(list(all_transactions.values('description', 'amount')))
    df_type['type'] = df_type['amount'].apply(lambda x: 'Income' if x > 0 else 'Expense')
    # --- NEW: Clean the text ---
    df_type['clean_description'] = df_type['description'].apply(clean_text)
    
    type_vectorizer = TfidfVectorizer(ngram_range=(1, 2)) # <-- NEW: n-grams
    type_model = LinearSVC() # <-- NEW: better algorithm
    
    X_type = type_vectorizer.fit_transform(df_type['clean_description']) # <-- Use clean text
    y_type = df_type['type']
    type_model.fit(X_type, y_type)
    
    expense_transactions = all_transactions.filter(amount__lt=0).exclude(category__isnull=True)
    
    if expense_transactions.count() < 2:
        models = {
            'type_model': type_model, 'type_vectorizer': type_vectorizer,
            'cat_model': None, 'cat_vectorizer': None
        }
        return models

    df_cat = pd.DataFrame(list(expense_transactions.values('description', 'category__name')))
    df_cat.rename(columns={'category__name': 'category'}, inplace=True)
    # --- NEW: Clean the text ---
    df_cat['clean_description'] = df_cat['description'].apply(clean_text)
    
    cat_vectorizer = TfidfVectorizer(ngram_range=(1, 2)) # <-- NEW: n-grams
    cat_model = LinearSVC() # <-- NEW: better algorithm
    
    X_cat = cat_vectorizer.fit_transform(df_cat['clean_description']) # <-- Use clean text
    y_cat = df_cat['category']
    cat_model.fit(X_cat, y_cat)

    models = {
        'type_model': type_model, 'type_vectorizer': type_vectorizer,
        'cat_model': cat_model, 'cat_vectorizer': cat_vectorizer
    }
    return models


def predict_transaction(models, description_text):
    """
    Predicts the type (Income/Expense) AND category.
    """
    
    # --- NEW: Clean the incoming text first! ---
    clean_desc = clean_text(description_text)
    
    # --- Prediction 1: Type ---
    X_type_new = models['type_vectorizer'].transform([clean_desc]) # <-- Use clean text
    predicted_type = models['type_model'].predict(X_type_new)[0]
    
    predicted_category_name = None
    
    # --- Prediction 2: Category (ONLY if it's an Expense) ---
    if predicted_type == 'Expense' and models['cat_model']:
        try:
            X_cat_new = models['cat_vectorizer'].transform([clean_desc]) # <-- Use clean text
            predicted_category_name = models['cat_model'].predict(X_cat_new)[0]
        except:
            predicted_category_name = None 
            
    return predicted_type, predicted_category_name