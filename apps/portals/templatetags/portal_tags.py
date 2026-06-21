from django import template
from django.db.models import Q
from apps.students.models import Student, Guardian

register = template.Library()

@register.simple_tag(takes_context=True)
def get_guardian_children(context):
    request = context.get('request')
    if not request or not request.user.is_authenticated:
        return []

    guardians = Guardian.objects.filter(
        Q(portal_user=request.user) | Q(email=request.user.email)
    )
    return Student.objects.filter(guardians__in=guardians).distinct()


@register.simple_tag(takes_context=True)
def get_unread_notifications_count(context):
    request = context.get('request')
    if not request or not request.user.is_authenticated:
        return 0
    from apps.notifications.models import Notification
    return Notification.objects.filter(recipient=request.user, is_read=False).count()
