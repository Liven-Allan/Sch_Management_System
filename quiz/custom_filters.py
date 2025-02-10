from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Safely get the value of a dictionary key."""
    return dictionary.get(key)
