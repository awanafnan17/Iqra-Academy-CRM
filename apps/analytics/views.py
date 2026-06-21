from django.http import JsonResponse
from apps.core.decorators import role_required
from apps.analytics import services

@role_required("Admin", "Accountant")
def api_revenue_trend(request):
    """Serve monthly confirmed revenue trend data.

    Restricted to Admin and Accountant roles.
    """
    year_str = request.GET.get("year")
    try:
        year = int(year_str) if year_str else None
    except ValueError:
        year = None
    data = services.get_revenue_trend(year)
    return JsonResponse({"status": "success", "data": data})

@role_required("Admin", "Principal")
def api_attendance_trend(request):
    """Serve daily attendance trend metrics.

    Restricted to Admin and Principal roles.
    """
    session_id_str = request.GET.get("session_id")
    try:
        session_id = int(session_id_str) if session_id_str else None
    except ValueError:
        session_id = None
    data = services.get_attendance_trend(session_id)
    return JsonResponse({"status": "success", "data": data})

@role_required("Admin", "Principal")
def api_enrollment_growth(request):
    """Serve monthly enrollment growth metrics for the current year.

    Restricted to Admin and Principal roles.
    """
    data = services.get_enrollment_growth()
    return JsonResponse({"status": "success", "data": data})

@role_required("Admin", "Principal")
def api_lead_funnel(request):
    """Serve lead conversion funnel counts and conversion rates.

    Restricted to Admin and Principal roles.
    """
    data = services.get_lead_conversion_funnel()
    return JsonResponse({"status": "success", "data": data})

@role_required("Admin", "Accountant")
def api_aging_report(request):
    """Serve outstanding installment payment aging stats.

    Restricted to Admin and Accountant roles.
    """
    data = services.get_payment_aging_report()
    return JsonResponse({"status": "success", "data": data})
