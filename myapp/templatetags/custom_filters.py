from django import template

register = template.Library()

@register.filter
def dict_key(d, key):
    return d.get(key) if isinstance(d, dict) else None