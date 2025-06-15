from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.conf import settings

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
    





class StoryLike(models.Model):
    story = models.ForeignKey(Story, related_name='likes', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('story', 'user')  # One like per user per story

class StoryComment(models.Model):
    story = models.ForeignKey(Story, related_name='comments', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class StoryShare(models.Model):
    story = models.ForeignKey(Story, related_name='shares', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    shared_at = models.DateTimeField(auto_now_add=True)


# post model
class Post(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField(max_length=500)
    image = models.ImageField(upload_to='post_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='liked_posts', blank=True)

    def total_likes(self):
        return self.likes.count()

    def total_comments(self):
        return self.comments.count()

    def __str__(self):
        return f"{self.user.username}'s post at {self.created_at.strftime('%Y-%m-%d %H:%M')}"

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField(max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user.username} on Post {self.post.id} at {self.created_at.strftime('%Y-%m-%d %H:%M')}"


# chat model
User = get_user_model()

class Conversation(models.Model):
    participants = models.ManyToManyField(User, related_name='conversations')
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        # Show usernames in alphabetical order for consistency
        usernames = sorted([user.username for user in self.participants.all()])
        return " & ".join(usernames)

    @property
    def last_message(self):
        return self.messages.order_by('-timestamp').first()

    def get_other_participant(self, current_user):
        """
        Returns the other participant in a 2-user conversation.
        If more than 2 users, returns the first one that isn't the current user.
        """
        return self.participants.exclude(id=current_user.id).first()

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sender.username}: {self.content[:20]}"
    


# follow model
class Follow(models.Model):
    follower = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='following_set', on_delete=models.CASCADE)
    following = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='followers_set', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')



# event model
class Event(models.Model):
    EVENT_TYPES = [
        ('Conference', 'Conference'),
        ('Workshop', 'Workshop'),
        ('Networking', 'Networking'),
        ('Social', 'Social Gathering'),
        ('Other', 'Other'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    date = models.DateTimeField()
    location = models.CharField(max_length=200)
    image = models.ImageField(upload_to='event_images/', blank=True, null=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    featured = models.BooleanField(default=False)

    def _str_(self):
        return self.title

    @property
    def image_url(self):
        if self.image and hasattr(self.image, 'url'):
            return self.image.url
        return 'https://via.placeholder.com/400x250?text=Event'