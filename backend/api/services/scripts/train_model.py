import pandas as pd
from sklearn.linear_model import LogisticRegression
import joblib
import os

# Load real or semi-real training data
csv_path = os.path.join(os.path.dirname(__file__), "train.csv")
df = pd.read_csv(csv_path)

X = df[["price", "market_cap", "eps", "sentiment"]]
y = df["will_go_up"]

model = LogisticRegression()
model.fit(X, y)

# Save model
model_dir = os.path.join(os.path.dirname(__file__), "..", "models")
os.makedirs(model_dir, exist_ok=True)
joblib.dump(model, os.path.join(model_dir, "model.pkl"))

print("✅ Model trained and saved.")