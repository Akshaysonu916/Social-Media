from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

# Create your models here.


class CustomUser(AbstractUser):
    email = models.EmailField(_('email address'), unique=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', default='default.jpg')
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=100, blank=True)
    birth_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.username
    

User = get_user_model()

class Story(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stories')
    image = models.ImageField(upload_to='stories/images/', blank=True, null=True)
    video = models.FileField(upload_to='stories/videos/', blank=True, null=True)
    caption = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        from django.utils import timezone
        return self.created_at < timezone.now() - timezone.timedelta(hours=24)

    def __str__(self):
        return f"{self.user.username}'s Story at {self.created_at}"