from django import template

from enrichment.categories import label_for

register = template.Library()


@register.filter(name="category_label")
def category_label(value: str) -> str:
    """Render a stored category value as its Portuguese label."""
    return label_for(value or "")
