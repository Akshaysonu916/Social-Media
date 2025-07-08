import json
import pickle
import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

# Load the trained model
model_path = os.path.join(settings.BASE_DIR, 'chatbot', 'chatbot_model.pkl')
with open(model_path, 'rb') as f:
    vectorizer, X, df = pickle.load(f)

@csrf_exempt
def chatbot_response(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_message = data.get("message", "")

        if not user_message:
            return JsonResponse({"reply": "Please enter a message."})

        query_vec = vectorizer.transform([user_message])
        from sklearn.metrics.pairwise import cosine_similarity
        similarity = cosine_similarity(query_vec, X)
        best_idx = similarity.argmax()
        score = similarity[0, best_idx]

        if score > 0.3:
            reply = df.iloc[best_idx]['answer']
        else:
            reply = "Sorry, I didn't quite understand that."

        return JsonResponse({"reply": reply})
