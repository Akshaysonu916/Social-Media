from django import template
from myapp.models import Follow, CustomUser

register = template.Library()

@register.filter
def is_following(user, target_user):
    """Check if user is following target_user."""
    if not user.is_authenticated:
        return False
    return Follow.objects.filter(follower=user, following=target_user).exists()


@register.filter
def is_liked(post, user):
    return post.like_entries.filter(user=user).exists()