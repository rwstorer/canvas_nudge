from datetime import datetime
from django import template

register = template.Library()

@register.filter
def dict_get(d, key):
    try:
        return d.get(key)
    except Exception:
        return None

@register.filter
def pretty_date(value):
    """Convert Canvas ISO8601 date to 'Feb 7, 2026'."""
    if not value:
        return "Unknown"
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.strftime("%b %d, %Y")
    except Exception:
        return value  # fallback
    
@register.filter(name="add_class")
def add_class(field, css_class):
    """
    Safely add a CSS class to a Django form field widget.
    """
    existing = field.field.widget.attrs.get("class", "")
    classes = f"{existing} {css_class}".strip()
    return field.as_widget(attrs={"class": classes})
