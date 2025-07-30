from django.db import models
from django.conf import settings
from django.utils.timezone import now

class UserActivity(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    last_active = models.DateTimeField(default=now)

    def __str__(self):
        return f"{self.user.username} - {self.last_active}"