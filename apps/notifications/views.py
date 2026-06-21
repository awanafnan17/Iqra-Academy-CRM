import json
import logging
from functools import wraps
from django.http import HttpResponse, JsonResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View
from django.core.exceptions import ValidationError
from django.core.cache import cache
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from apps.core.decorators import role_required
from apps.notifications.models import Notification
from apps.notifications import services

logger = logging.getLogger("crm.notifications")


def throttle_admin_bulk_send(view_func):
    """Throttle admin bulk send requests (max 3 calls per minute per admin)."""
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            key = f"throttle_bulk_send_{request.user.id}"
            requests = cache.get(key, [])
            now = timezone.now().timestamp()
            requests = [r for r in requests if now - r < 60]
            if len(requests) >= 3:
                logger.warning(f"Rate limit exceeded for admin bulk send: user {request.user.id}")
                return JsonResponse({"status": "error", "message": "Rate limit exceeded. Max 3 calls per minute."}, status=429)
            requests.append(now)
            cache.set(key, requests, 60)
        return view_func(request, *args, **kwargs)
    return wrapped_view


def _placeholder(name):
    """Create a placeholder view that raises Http404."""
    def view(request, *args, **kwargs):
        from django.http import Http404
        raise Http404(f"View {name} is not implemented yet.")
    view.__name__ = name
    view.__qualname__ = name
    return view


# Template and Email Log Placeholders
@login_required
@role_required("Admin", "Principal")
def template_list(request):
    from apps.notifications.models import NotificationTemplate
    from django.template import TemplateDoesNotExist
    from django.http import Http404
    templates = NotificationTemplate.objects.all().order_by('name')
    try:
        return render(request, "notifications/template_list.html", {
            "templates": templates,
            "page_title": "Notification Templates"
        })
    except TemplateDoesNotExist:
        raise Http404("Template not implemented yet")

@login_required
@role_required("Admin", "Principal")
def template_create(request):
    from apps.notifications.forms import NotificationTemplateForm
    from django.template import TemplateDoesNotExist
    from django.http import Http404
    if request.method == "POST":
        form = NotificationTemplateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Template created successfully.")
            return redirect("admin_panel:notifications:template_list")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = NotificationTemplateForm()
    try:
        return render(request, "notifications/template_form.html", {
            "form": form,
            "page_title": "Create Template"
        })
    except TemplateDoesNotExist:
        raise Http404("Template not implemented yet")

@login_required
@role_required("Admin", "Principal")
def template_edit(request, pk):
    from apps.notifications.models import NotificationTemplate
    from apps.notifications.forms import NotificationTemplateForm
    from django.template import TemplateDoesNotExist
    from django.http import Http404
    template = get_object_or_404(NotificationTemplate, pk=pk)
    if request.method == "POST":
        form = NotificationTemplateForm(request.POST, instance=template)
        if form.is_valid():
            form.save()
            messages.success(request, "Template updated successfully.")
            return redirect("admin_panel:notifications:template_list")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = NotificationTemplateForm(instance=template)
    try:
        return render(request, "notifications/template_form.html", {
            "form": form,
            "template": template,
            "page_title": f"Edit Template: {template.name}"
        })
    except TemplateDoesNotExist:
        raise Http404("Template not implemented yet")

@login_required
@role_required("Admin", "Principal")
def email_log_list(request):
    from apps.notifications.models import EmailLog
    logs = EmailLog.objects.all().order_by('-sent_at')
    return render(request, "notifications/email_log_list.html", {
        "logs": logs,
        "page_title": "Email Logs"
    })



@method_decorator(role_required("Admin", "Principal", "Teacher", "Student", "Guardian", "Accountant", "Registrar"), name="dispatch")
class NotificationListView(View):
    """List notifications for the logged in user."""
    def get(self, request, *args, **kwargs):
        # Always scope to request.user, ignoring any recipient query parameter
        notifications = services.get_user_notifications(request.user)
        if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.GET.get("format") == "json":
            data = list(notifications.values("id", "title", "content", "category", "is_read", "created_at"))
            return JsonResponse({"notifications": data})
        return render(request, "notifications/notification_list.html", {"notifications": notifications})


@method_decorator(role_required("Admin", "Principal", "Teacher", "Student", "Guardian", "Accountant", "Registrar"), name="dispatch")
class NotificationDetailView(View):
    """Retrieve detailed information of a notification."""
    def get(self, request, pk, *args, **kwargs):
        notif = Notification.objects.filter(pk=pk, recipient=request.user).first()
        if notif is None:
            logger.warning(f"Unauthorized access attempt by user {request.user.id} to notification {pk}")
            raise Http404("Notification not found.")

        if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.GET.get("format") == "json":
            return JsonResponse({
                "id": notif.id,
                "title": notif.title,
                "content": notif.content,
                "category": notif.category,
                "is_read": notif.is_read,
                "created_at": notif.created_at,
            })
        return render(request, "notifications/notification_detail.html", {"notification": notif})


@method_decorator(role_required("Admin", "Principal", "Teacher", "Student", "Guardian", "Accountant", "Registrar"), name="dispatch")
class NotificationMarkReadView(View):
    """Mark one or all notifications of the user as read."""
    def dispatch(self, request, *args, **kwargs):
        if request.method != "POST":
            raise Http404("POST required.")
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        notification_id = request.POST.get("notification_id")
        if not notification_id and request.content_type == "application/json":
            try:
                body = json.loads(request.body)
                notification_id = body.get("notification_id")
            except ValueError:
                pass

        if notification_id:
            try:
                services.mark_notification_read(notification_id, request.user)
                return JsonResponse({"status": "success", "message": "Notification marked as read."})
            except ValidationError as e:
                return JsonResponse({"status": "error", "message": str(e)}, status=400)
            except Http404 as e:
                raise Http404(str(e))
        else:
            services.mark_all_notifications_read(request.user)
            return JsonResponse({"status": "success", "message": "All notifications marked as read."})


@method_decorator(role_required("Admin"), name="dispatch")
@method_decorator(throttle_admin_bulk_send, name="post")
class NotificationBulkSendView(View):
    """Admin-only view to bulk notify a list of users."""
    def get(self, request, *args, **kwargs):
        """Render the bulk send notification form."""
        return render(request, "notifications/bulk_send_form.html")

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_superuser or request.user.groups.filter(name="Admin").exists()):
            username = request.user.username if request.user.is_authenticated else "Anonymous"
            logger.warning(f"Unauthorized bulk send access attempt by user {username}")
            raise Http404("Access denied.")
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if request.content_type == "application/json":
            try:
                body = json.loads(request.body)
                user_ids = body.get("user_ids", [])
                title = body.get("title")
                message = body.get("message")
                category = body.get("category")
            except ValueError:
                return JsonResponse({"status": "error", "message": "Invalid JSON."}, status=400)
        else:
            user_ids = request.POST.getlist("user_ids")
            title = request.POST.get("title")
            message = request.POST.get("message")
            category = request.POST.get("category")

        # Normalize string representation of list (if passed as comma-separated values)
        if isinstance(user_ids, str):
            try:
                user_ids = [int(x.strip()) for x in user_ids.split(",") if x.strip()]
            except ValueError:
                return JsonResponse({"status": "error", "message": "Invalid user_ids format."}, status=400)

        try:
            notifications = services.bulk_notify_users(
                user_ids=user_ids,
                title=title,
                message=message,
                category=category,
                created_by=request.user
            )
            return JsonResponse({"status": "success", "count": len(notifications)})
        except ValidationError as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)


@method_decorator(role_required("Admin", "Principal", "Teacher", "Student", "Guardian", "Accountant", "Registrar"), name="dispatch")
class UnreadCountAPIView(View):
    """API endpoint to get unread notification count for the user."""
    def get(self, request, *args, **kwargs):
        count = services.get_unread_count(request.user)
        return JsonResponse({"unread_count": count})


# Expose CBVs as function views for compatibility
notification_list = NotificationListView.as_view()
notification_detail = NotificationDetailView.as_view()
notification_mark_read = NotificationMarkReadView.as_view()
notification_bulk_send = NotificationBulkSendView.as_view()
unread_count_api = UnreadCountAPIView.as_view()

