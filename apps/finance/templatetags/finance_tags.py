from django import template
from django.urls import reverse, NoReverseMatch
from apps.finance.utils import format_currency as utils_format_currency

register = template.Library()

@register.filter
def format_currency(value):
    """Formats an amount into Pakistani Rupees (PKR) representation.
    Example: 120000 -> "PKR 120,000"
    """
    return utils_format_currency(value)


@register.filter
def dict_item(dictionary, key):
    """Retrieve an item from a dictionary dynamically inside templates."""
    if not isinstance(dictionary, dict):
        return None
    return dictionary.get(key)


@register.simple_tag(takes_context=True)
def finance_url(context, view_name, *args, **kwargs):
    """Dynamically resolve finance URLs to either accounts_panel or admin_panel:finance.

    This fixes DEF-TEMPLATE-01 by routing Accountant panel requests to accounts_panel:<view_name>
    and Admin/Principal panel requests to admin_panel:finance:<view_name>.
    """
    request = context.get('request')
    if request and request.resolver_match:
        namespaces = request.resolver_match.namespaces
        if 'accounts_panel' in namespaces:
            # Try flat name under accounts_panel first
            try:
                return reverse(f"accounts_panel:{view_name}", args=args, kwargs=kwargs)
            except NoReverseMatch:
                pass

    # Default to admin_panel:finance
    try:
        return reverse(f"admin_panel:finance:{view_name}", args=args, kwargs=kwargs)
    except NoReverseMatch:
        # Fallback to admin_panel direct (e.g. installment_pay which is defined directly in urls_admin.py)
        try:
            return reverse(f"admin_panel:{view_name}", args=args, kwargs=kwargs)
        except NoReverseMatch:
            pass
    return ""


