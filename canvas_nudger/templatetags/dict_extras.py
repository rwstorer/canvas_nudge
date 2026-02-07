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