from django import template
from myapp.models import Follow, CustomUser

register = template.Library()

@register.filter
def is_following(user, target_user):
    """Check if user is following target_user."""
    if not user.is_authenticated:
        return False
    return Follow.objects.filter(follower=user, following=target_user).exists()
