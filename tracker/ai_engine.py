import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import KNeighborsClassifier
from .models import Transaction, Category
import os

# --- NEW: Define the training file ---
TRAINING_FILE = 'financial_dataset_24000_realistic.csv'

def create_pretrained_models():
    """
    Trains a powerful set of models on the 24,000-line CSV.
    This is our "Pre-Trained Brain".
    """
    if not os.path.exists(TRAINING_FILE):
        return None # Can't train if the file isn't there

    df = pd.read_csv(TRAINING_FILE)
    
    # --- Model 1: Type Classifier (Income vs. Expense) ---
    type_vectorizer = TfidfVectorizer()
    type_model = KNeighborsClassifier(n_neighbors=3)
    
    X_type = type_vectorizer.fit_transform(df['Transaction Description'])
    y_type = df['Type']
    type_model.fit(X_type, y_type)
    
    # --- Model 2: Category Classifier (For Expenses Only) ---
    df_cat = df[df['Type'] == 'Expense'].copy()
    
    cat_vectorizer = TfidfVectorizer()
    cat_model = KNeighborsClassifier(n_neighbors=3)
    
    X_cat = cat_vectorizer.fit_transform(df_cat['Transaction Description'])
    y_cat = df_cat['Category']
    cat_model.fit(X_cat, y_cat)

    models = {
        'type_model': type_model,
        'type_vectorizer': type_vectorizer,
        'cat_model': cat_model,
        'cat_vectorizer': cat_vectorizer
    }
    return models

# We keep this function for the user's *own* data
def train_models(user):
    """
    Trains models on the user's *own* manually-corrected data.
    This "fine-tunes" the pre-trained model.
    """
    all_transactions = Transaction.objects.filter(user=user)
    
    if all_transactions.count() < 2:
        return None 
    
    df_type = pd.DataFrame(list(all_transactions.values('description', 'amount')))
    df_type['type'] = df_type['amount'].apply(lambda x: 'Income' if x > 0 else 'Expense')
    
    type_vectorizer = TfidfVectorizer()
    type_model = KNeighborsClassifier(n_neighbors=1)
    X_type = type_vectorizer.fit_transform(df_type['description'])
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
    
    cat_vectorizer = TfidfVectorizer()
    cat_model = KNeighborsClassifier(n_neighbors=1)
    
    X_cat = cat_vectorizer.fit_transform(df_cat['description'])
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
    X_type_new = models['type_vectorizer'].transform([description_text])
    predicted_type = models['type_model'].predict(X_type_new)[0]
    
    predicted_category_name = None
    
    if predicted_type == 'Expense' and models['cat_model']:
        try:
            X_cat_new = models['cat_vectorizer'].transform([description_text])
            predicted_category_name = models['cat_model'].predict(X_cat_new)[0]
        except:
            predicted_category_name = None 
            
    return predicted_type, predicted_category_name