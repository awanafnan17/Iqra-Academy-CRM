from django import template
from django.urls import reverse, NoReverseMatch

register = template.Library()

@register.simple_tag(takes_context=True)
def lead_url(context, view_name, *args, **kwargs):
    """Dynamically resolve lead URLs to registrar_panel or admin_panel:students."""
    request = context.get('request')
    if request and request.resolver_match:
        namespaces = request.resolver_match.namespaces
        if 'registrar_panel' in namespaces:
            try:
                return reverse(f"registrar_panel:{view_name}", args=args, kwargs=kwargs)
            except NoReverseMatch:
                pass
    try:
        return reverse(f"admin_panel:students:{view_name}", args=args, kwargs=kwargs)
    except NoReverseMatch:
        pass
    return ""


@register.simple_tag(takes_context=True)
def student_url(context, view_name, *args, **kwargs):
    """Dynamically resolve student URLs to registrar_panel or admin_panel:students.

    Supports both flat names (like manage_students, add_student) and nested names (like student_list).
    """
    request = context.get('request')
    if request and request.resolver_match:
        namespaces = request.resolver_match.namespaces
        if 'registrar_panel' in namespaces:
            mapped_name = view_name
            if view_name == "add_student":
                mapped_name = "student_create"
            elif view_name == "manage_students":
                mapped_name = "student_list"
            try:
                return reverse(f"registrar_panel:{mapped_name}", args=args, kwargs=kwargs)
            except NoReverseMatch:
                pass

    try:
        return reverse(f"admin_panel:{view_name}", args=args, kwargs=kwargs)
    except NoReverseMatch:
        pass

    try:
        mapped_name = view_name
        if view_name == "manage_students":
            mapped_name = "student_list"
        elif view_name == "add_student":
            mapped_name = "student_create"
        return reverse(f"admin_panel:students:{mapped_name}", args=args, kwargs=kwargs)
    except NoReverseMatch:
        pass
    return ""


@register.simple_tag(takes_context=True)
def admission_url(context, view_name, *args, **kwargs):
    """Dynamically resolve admission URLs to registrar_panel or admin_panel:admissions.

    Fixes cross-panel URL namespace leaks for Registrar role in admissions workflow.
    """
    request = context.get('request')
    if request and request.resolver_match:
        namespaces = request.resolver_match.namespaces
        if 'registrar_panel' in namespaces:
            try:
                return reverse(f"registrar_panel:admissions:{view_name}", args=args, kwargs=kwargs)
            except NoReverseMatch:
                pass
    try:
        return reverse(f"admin_panel:admissions:{view_name}", args=args, kwargs=kwargs)
    except NoReverseMatch:
        pass
    return ""

