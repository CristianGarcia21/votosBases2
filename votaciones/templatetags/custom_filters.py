from django import template
register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Obtener un elemento de un diccionario por su clave"""
    if dictionary is None:
        return None
    return dictionary.get(key)

@register.filter
def attr(obj, attr_name):
    """Acceder a un atributo de un objeto"""
    if obj is None:
        return None
    try:
        return getattr(obj, attr_name)
    except (AttributeError, TypeError):
        return None