from django import template
from myapp.models import Follow

register = template.Library()

@register.filter
def dict_key(d, key):
    return d.get(key) if isinstance(d, dict) else None


# following code is for custom template filters

@register.filter
def is_following(user, current_user):
    return Follow.objects.filter(follower=current_user, following=user).exists()

@register.filter
def is_followed_by(user, current_user):
    return Follow.objects.filter(follower=user, following=current_user).exists()