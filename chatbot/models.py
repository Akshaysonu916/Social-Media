from django.db import models
from django.conf import settings

# Create your models here.



class ChatbotMessage(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    question = models.TextField()
    response = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Chat by {self.user.username} on {self.timestamp.strftime('%Y-%m-%d %H:%M')}"