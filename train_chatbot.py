# train_chatbot.py
import pandas as pd
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Load dataset
df = pd.read_csv("chatbot/chatbot_data.csv")

# Train vectorizer
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(df['question'])

# Save vectorizer, transformed data, and original DataFrame
with open("chatbot/chatbot_model.pkl", "wb") as f:
    pickle.dump((vectorizer, X, df), f)

print("Model trained and saved!")
