# train_chatbot.py

import os
import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer

# === CONFIGURATION ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "chatbot")
CSV_FILE = os.path.join(DATA_DIR, "chatbot_data.csv")
VECTORIZER_FILE = os.path.join(DATA_DIR, "vectorizer.pkl")
TFIDF_MATRIX_FILE = os.path.join(DATA_DIR, "questions.pkl")
DATAFRAME_FILE = os.path.join(DATA_DIR, "data.pkl")

# === Ensure chatbot directory exists ===
os.makedirs(DATA_DIR, exist_ok=True)

# === Load CSV Data ===
if not os.path.exists(CSV_FILE):
    raise FileNotFoundError(f"❌ CSV file not found: {CSV_FILE}")

df = pd.read_csv(CSV_FILE)

# === Check required columns ===
required_columns = {'question', 'answer'}
if not required_columns.issubset(df.columns):
    raise ValueError(f"❌ CSV must contain columns: {required_columns}. Found: {set(df.columns)}")

# === Train TF-IDF Vectorizer ===
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(df['question'])

# === Save all model files ===
joblib.dump(vectorizer, VECTORIZER_FILE)
joblib.dump(X, TFIDF_MATRIX_FILE)
joblib.dump(df, DATAFRAME_FILE)

print("✅ Chatbot model trained and saved successfully!")
print(f"📁 Saved vectorizer to: {VECTORIZER_FILE}")
print(f"📁 Saved TF-IDF matrix to: {TFIDF_MATRIX_FILE}")
print(f"📁 Saved DataFrame to: {DATAFRAME_FILE}")
