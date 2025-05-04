from django import template

register = template.Library()

@register.filter
def subtract(value, arg):
    """Shablonda ikki sonni ayirish uchun filter"""
    try:
        return value - arg
    except (TypeError, ValueError):
        return 0
    
@register.filter
def kopaytir(value, arg):
    return value * arg
