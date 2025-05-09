# core/templatetags/form_filters.py

from django import template
from django.forms.boundfield import BoundField

register = template.Library()

@register.filter(name='add_class')
def add_class(value, css_class):
    if isinstance(value, BoundField):
        return value.as_widget(attrs={'class': css_class})
    return value  # return as-is if it's not a form field
