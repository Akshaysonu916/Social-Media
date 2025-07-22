import json
import pickle
import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import joblib
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from .models import ChatbotMessage
from django.shortcuts import render

# Load the trained model
model_path = os.path.join(settings.BASE_DIR, 'chatbot', 'chatbot_model.pkl')
with open(model_path, 'rb') as f:
    vectorizer, X, df = pickle.load(f)

# Load vectorizer and data only once at the module level
vectorizer = joblib.load("chatbot/vectorizer.pkl")
X = joblib.load("chatbot/questions.pkl")
df = pd.read_csv("chatbot/chatbot_data.csv")


@csrf_exempt  # Note: You should use @login_required + AJAX token in production
def chatbot_response(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get("message", "").strip()

            if not user_message:
                return JsonResponse({"reply": "Please enter a message."})

            query_vec = vectorizer.transform([user_message])
            similarity = cosine_similarity(query_vec, X)
            best_idx = similarity.argmax()
            score = similarity[0, best_idx]

            if score > 0.3:
                reply = df.iloc[best_idx]['answer']
            else:
                reply = "Sorry, I didn't quite understand that."

            # Optional: Save to DB
            if request.user.is_authenticated:
                ChatbotMessage.objects.create(
                    user=request.user,
                    question=user_message,
                    response=reply
                )

            return JsonResponse({"reply": reply})

        except Exception as e:
            return JsonResponse({"reply": "An error occurred: " + str(e)})

    return JsonResponse({"reply": "Only POST requests are accepted."})


def chatbot_ui(request):
    previous_messages = ChatbotMessage.objects.filter(user=request.user).order_by('timestamp')
    return render(request, 'messages.html', {'previous_messages': previous_messages})