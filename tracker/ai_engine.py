import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
import re
from .models import Transaction, Category
import os
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

TRAINING_FILE = 'financial_dataset_24000_realistic.csv'

# --- BUG #1 (FIXED): The clean_text function was missing---
def clean_text(text):
    """
    Cleans description text by:
    1. Converting to string (to handle floats/NaNs)
    2. Making it lowercase
    3. Removing all punctuation
    4. Removing all numbers
    5. Stripping extra whitespace   
    """
    text = str(text) 
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
    
    df['clean_description'] = df['Transaction Description'].apply(clean_text)
    
    # --- Model 1: Type Classifier (Income vs. Expense) ---
    type_vectorizer = TfidfVectorizer(ngram_range=(1, 2))
    type_model = LinearSVC()
    
    X_type = type_vectorizer.fit_transform(df['clean_description'])
    y_type = df['Type']
    type_model.fit(X_type, y_type)
    
    # --- Model 2: Category Classifier (Income AND Expenses) ---
    df_cat = df.copy()
    
    cat_vectorizer = TfidfVectorizer(ngram_range=(1, 2))
    cat_model = LinearSVC()
    
    X_cat = cat_vectorizer.fit_transform(df_cat['clean_description'])
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
    
    # --- BUG #2 (FIXED): Must return (None, None) for accuracies ---
    if all_transactions.count() < 5:
        return None, None
    
    df_type = pd.DataFrame(list(all_transactions.values('description', 'amount')))
    df_type['type'] = df_type['amount'].apply(lambda x: 'Income' if x > 0 else 'Expense')
    df_type['clean_description'] = df_type['description'].apply(clean_text)
    
    X_type_train, X_type_test, y_type_train, y_type_test = train_test_split(
        df_type['clean_description'], df_type['type'], test_size=0.2, random_state=42
    )
    
    type_vectorizer = TfidfVectorizer(ngram_range=(1, 2))
    type_model = LinearSVC()
    
    X_type_train_vec = type_vectorizer.fit_transform(X_type_train)
    type_model.fit(X_type_train_vec, y_type_train)
    
    X_type_test_vec = type_vectorizer.transform(X_type_test)
    type_preds = type_model.predict(X_type_test_vec)
    type_accuracy = accuracy_score(y_type_test, type_preds)
    
    
    # --- Model 2: Category Classifier (Income AND Expenses) ---
    categorized_transactions = all_transactions.exclude(category__isnull=True)
    
    cat_accuracy = 0.0
    
    if categorized_transactions.count() < 5:
        models = {
            'type_model': type_model, 'type_vectorizer': type_vectorizer,
            'cat_model': None, 'cat_vectorizer': None
        }
        accuracies = {'type_accuracy': type_accuracy, 'cat_accuracy': cat_accuracy}
        return models, accuracies

    df_cat = pd.DataFrame(list(categorized_transactions.values('description', 'category__name')))
    df_cat.rename(columns={'category__name': 'category'}, inplace=True)
    df_cat['clean_description'] = df_cat['description'].apply(clean_text)
    
    X_cat_train, X_cat_test, y_cat_train, y_cat_test = train_test_split(
        df_cat['clean_description'], df_cat['category'], test_size=0.2, random_state=42
    )
    
    cat_vectorizer = TfidfVectorizer(ngram_range=(1, 2))
    cat_model = LinearSVC()
    
    X_cat_train_vec = cat_vectorizer.fit_transform(X_cat_train)
    cat_model.fit(X_cat_train_vec, y_cat_train)

    X_cat_test_vec = cat_vectorizer.transform(X_cat_test)
    cat_preds = cat_model.predict(X_cat_test_vec)
    cat_accuracy = accuracy_score(y_cat_test, cat_preds)

    models = {
        'type_model': type_model, 'type_vectorizer': type_vectorizer,
        'cat_model': cat_model, 'cat_vectorizer': cat_vectorizer
    }
    accuracies = {'type_accuracy': type_accuracy, 'cat_accuracy': cat_accuracy}
    
    return models, accuracies


def predict_transaction(models, description_text):
    """
    Predicts the type (Income/Expense) AND category.
    """
    clean_desc = clean_text(description_text)
    
    # --- Prediction 1: Type ---
    X_type_new = models['type_vectorizer'].transform([clean_desc])
    predicted_type = models['type_model'].predict(X_type_new)[0]
    
    predicted_category_name = None
    
    # --- Prediction 2: Category (ALWAYS) ---
    if models['cat_model']:
        try:
            X_cat_new = models['cat_vectorizer'].transform([clean_desc])
            predicted_category_name = models['cat_model'].predict(X_cat_new)[0]
        except:
            predicted_category_name = None 
            
    return predicted_type, predicted_category_name