# training_pipeline/train/train_model.py

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from sklearn.ensemble import RandomForestClassifier
from pathlib import Path
import joblib

DATA_PATH = Path("training_pipeline/data/training_data.csv")
MODEL_PATH = Path("training_pipeline/models/price_direction_model.pkl")

def load_data():
    df = pd.read_csv(DATA_PATH)

    # Drop missing or bad data
    df = df.dropna()

    # Features and label
    X = df[["close_price", "pe_ratio", "eps", "revenue_growth"]]
    y = df["label_next_7d"]

    return train_test_split(X, y, test_size=0.2, random_state=42)

def train_model():
    X_train, X_test, y_train, y_test = load_data()

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"Accuracy: {acc:.2%}")
    print("\nClassification Report:\n", classification_report(y_test, y_pred))

    # Save model
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")

if __name__ == "__main__":
    train_model()