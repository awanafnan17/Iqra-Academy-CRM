import json
from django.http import HttpResponse, JsonResponse, Http404
from django.shortcuts import render, get_object_or_404
from django.views import View
from django.core.paginator import Paginator
from django.utils.decorators import method_decorator
from django.db.models import Q

from apps.core.decorators import role_required
from apps.core.models import AuditLog


def _stub(name):
    """Create a placeholder view function."""
    def view(request, *args, **kwargs):
        return HttpResponse(
            f"{name} - Coming soon",
            content_type="text/plain",
        )
    view.__name__ = name
    view.__qualname__ = name
    return view


def _json_stub(name):
    """Create a placeholder view that returns JSON."""
    def view(request, *args, **kwargs):
        return JsonResponse({"status": "stub", "view": name})
    view.__name__ = name
    view.__qualname__ = name
    return view


# -------------------------------------------------------------------
#  API endpoints (AJAX)
# -------------------------------------------------------------------

api_student_search = _json_stub("api_student_search")
api_session_search = _json_stub("api_session_search")
api_unread_count = _json_stub("api_unread_count")
api_attendance_bulk_mark = _json_stub("api_attendance_bulk_mark")
api_dashboard_stats = _json_stub("api_dashboard_stats")

# -------------------------------------------------------------------
#  Audit log views
# -------------------------------------------------------------------

@method_decorator(role_required("Admin"), name="dispatch")
class AuditLogListView(View):
    """Admin-only list view for central compliance AuditLogs."""
    template_name = "core/audit_log_list.html"

    def get(self, request, *args, **kwargs):
        # Read-only query: order newest-first
        queryset = AuditLog.objects.select_related("user").all().order_by("-timestamp")

        # Extract filters
        action = request.GET.get("action", "").strip()
        user_query = request.GET.get("user", "").strip()
        model_name = request.GET.get("model_name", "").strip()
        date_from = request.GET.get("date_from", "").strip()
        date_to = request.GET.get("date_to", "").strip()
        search_text = request.GET.get("search_text", "").strip()

        # Apply action filter
        if action:
            queryset = queryset.filter(action=action)
        # Apply user search filter
        if user_query:
            queryset = queryset.filter(
                Q(user__username__icontains=user_query) |
                Q(user__email__icontains=user_query)
            )
        # Apply model_name filter
        if model_name:
            queryset = queryset.filter(model_name__icontains=model_name)
        # Apply date range filters
        if date_from:
            try:
                queryset = queryset.filter(timestamp__date__gte=date_from)
            except (ValueError, TypeError):
                pass
        if date_to:
            try:
                queryset = queryset.filter(timestamp__date__lte=date_to)
            except (ValueError, TypeError):
                pass
        # Apply general search
        if search_text:
            queryset = queryset.filter(
                Q(changes__icontains=search_text) |
                Q(object_id__icontains=search_text) |
                Q(ip_address__icontains=search_text) |
                Q(user_agent__icontains=search_text)
            )

        # Pagination (25 items per page)
        paginator = Paginator(queryset, 25)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        context = {
            "page_obj": page_obj,
            "action_choices": AuditLog.ACTION_CHOICES,
            "filters": {
                "action": action,
                "user": user_query,
                "model_name": model_name,
                "date_from": date_from,
                "date_to": date_to,
                "search_text": search_text,
            }
        }
        return render(request, self.template_name, context)


@method_decorator(role_required("Admin"), name="dispatch")
class AuditLogDetailView(View):
    """Admin-only detailed read-only view of a single compliance AuditLog record."""
    template_name = "core/audit_log_detail.html"

    def get(self, request, pk, *args, **kwargs):
        # 404 on missing log entries
        log_entry = get_object_or_404(AuditLog.objects.select_related("user"), pk=pk)

        # Safely parse JSON changes diff
        parsed_changes = None
        if log_entry.changes:
            try:
                parsed_changes = json.loads(log_entry.changes)
            except Exception:
                parsed_changes = log_entry.changes

        context = {
            "log": log_entry,
            "parsed_changes": parsed_changes,
        }
        return render(request, self.template_name, context)


audit_log_list = AuditLogListView.as_view()
audit_log_detail = AuditLogDetailView.as_view()

