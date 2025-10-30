# tracker/ai_engine.py

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import KNeighborsClassifier
from .models import Transaction

def train_model(user):
    """
    Trains a new categorization model based on a user's existing
    manually-categorized transactions.
    """
    
    # 1. Get all of the user's transactions that HAVE a category
    training_data = Transaction.objects.filter(user=user).exclude(category__isnull=True)
    
    # Check if we have enough data to train (we need at least 2 samples)
    if training_data.count() < 2:
        return None, None # Not enough data, can't train

    # 2. Convert the training data into a pandas DataFrame
    df = pd.DataFrame(list(training_data.values('description', 'category')))
    
    # 3. Setup the AI components
    # The Vectorizer (turns "TRADER JOE'S" into numbers)
    vectorizer = TfidfVectorizer()
    
    # The Classifier (learns the patterns)
    # n_neighbors=1 means "just find the single most similar transaction and copy its category"
    model = KNeighborsClassifier(n_neighbors=1)

    # 4. Prepare the data for training
    # X is the "features" (the text descriptions)
    X = vectorizer.fit_transform(df['description'])
    
    # y is the "labels" (the categories we want to predict)
    y = df['category']
    
    # 5. Train the model!
    model.fit(X, y)
    
    # 6. Return the trained "brain" (model) and "translator" (vectorizer)
    return model, vectorizer


def predict_category(model, vectorizer, description_text):
    """
    Predicts a category for a new, unseen transaction description.
    """
    
    # Use the vectorizer to turn the new text into the same number format
    X_new = vectorizer.transform([description_text])
    
    # Use the model to predict the category
    prediction = model.predict(X_new)
    
    # Return the predicted category name
    return prediction[0]