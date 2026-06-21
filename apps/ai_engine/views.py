"""
AI engine views for the Academy CRM.

Covers prediction logs, model versions, and dropout risk dashboard.
All views are stubs for Phase 1 (RBAC + Routing).
"""

from django.http import HttpResponse


import json
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.core.paginator import Paginator
from django.http import Http404
from apps.core.decorators import role_required, post_required
from apps.ai_engine.models import PredictionLog, ModelVersion
from apps.students.models import Student


# -------------------------------------------------------------------
#  Prediction views (Admin only)
# -------------------------------------------------------------------

@role_required("Admin")
def prediction_list(request):
    """List all AI predictions in the database, newest-first, with filters."""
    prediction_qs = PredictionLog.objects.all().order_by("-created_at")

    # Get filter params
    pred_type = request.GET.get("prediction_type", "").strip()
    risk = request.GET.get("risk_level", "").strip()
    ack = request.GET.get("is_acknowledged", "").strip()
    q = request.GET.get("q", "").strip()

    # Apply filters
    if pred_type:
        prediction_qs = prediction_qs.filter(prediction_type=pred_type)
    if risk:
        prediction_qs = prediction_qs.filter(risk_level=risk)
    if ack == "true":
        prediction_qs = prediction_qs.filter(is_acknowledged=True)
    elif ack == "false":
        prediction_qs = prediction_qs.filter(is_acknowledged=False)

    if q:
        # Search by student name/roll number if target model is Student
        matching_student_ids = Student.objects.filter(
            full_name__icontains=q
        ).values_list("id", flat=True)
        
        # Or search if target_object_id matches a numerical ID
        if q.isdigit():
            prediction_qs = prediction_qs.filter(
                target_object_id=int(q)
            ) | prediction_qs.filter(
                target_model="students.Student",
                target_object_id__in=matching_student_ids
            )
        else:
            prediction_qs = prediction_qs.filter(
                target_model="students.Student",
                target_object_id__in=matching_student_ids
            )

    # Pagination
    paginator = Paginator(prediction_qs, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Prefetch/resolve student targets to avoid N+1 queries
    student_ids = [p.target_object_id for p in page_obj if p.target_model == "students.Student"]
    students_map = {}
    if student_ids:
        students_map = {s.id: s for s in Student.objects.filter(id__in=student_ids)}

    for p in page_obj:
        if p.target_model == "students.Student":
            p.student_target = students_map.get(p.target_object_id)
        else:
            p.student_target = None

    context = {
        "page_obj": page_obj,
        "prediction_types": PredictionLog.PREDICTION_TYPE_CHOICES,
        "risk_levels": PredictionLog.RISK_LEVEL_CHOICES,
        "selected_prediction_type": pred_type,
        "selected_risk_level": risk,
        "selected_is_acknowledged": ack,
        "q": q,
    }
    return render(request, "ai_engine/prediction_list.html", context)


@role_required("Admin")
def prediction_detail(request, pk):
    """View details of a single prediction."""
    prediction = get_object_or_404(PredictionLog, pk=pk)

    student_target = None
    if prediction.target_model == "students.Student":
        student_target = Student.objects.filter(id=prediction.target_object_id).first()

    # Safely parse JSON strings for display
    input_features_json = None
    if prediction.input_features:
        try:
            input_features_json = json.loads(prediction.input_features)
        except Exception:
            input_features_json = prediction.input_features

    prediction_value_json = None
    if prediction.prediction_value:
        try:
            prediction_value_json = json.loads(prediction.prediction_value)
        except Exception:
            prediction_value_json = prediction.prediction_value

    context = {
        "prediction": prediction,
        "student_target": student_target,
        "input_features_json": input_features_json,
        "prediction_value_json": prediction_value_json,
    }
    return render(request, "ai_engine/prediction_detail.html", context)


@role_required("Admin")
@post_required
def prediction_acknowledge(request, pk):
    """Acknowledge a prediction log entry (POST only)."""
    prediction = get_object_or_404(PredictionLog, pk=pk)

    if not prediction.is_acknowledged:
        prediction.is_acknowledged = True
        prediction.acknowledged_by = request.user
        prediction.acknowledged_at = timezone.now()
        prediction.save(update_fields=["is_acknowledged", "acknowledged_by", "acknowledged_at"])

    return redirect("admin_panel:ai_engine:prediction_detail", pk=pk)


# -------------------------------------------------------------------
#  Model version views (Admin only)
# -------------------------------------------------------------------

@role_required("Admin")
def model_version_list(request):
    """List all ML models and versions, newest-first, with filters."""
    model_qs = ModelVersion.objects.all().order_by("-trained_at")

    model_type = request.GET.get("model_type", "").strip()
    is_active = request.GET.get("is_active", "").strip()

    if model_type:
        model_qs = model_qs.filter(model_type=model_type)
    if is_active == "true":
        model_qs = model_qs.filter(is_active=True)
    elif is_active == "false":
        model_qs = model_qs.filter(is_active=False)

    paginator = Paginator(model_qs, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "model_types": ModelVersion.MODEL_TYPE_CHOICES,
        "selected_model_type": model_type,
        "selected_is_active": is_active,
    }
    return render(request, "ai_engine/model_version_list.html", context)


# -------------------------------------------------------------------
#  Dropout risk dashboard (Admin + Principal)
# -------------------------------------------------------------------

@role_required("Admin", "Principal")
def dropout_risk_dashboard(request):
    """Dropout risk dashboard based strictly on database predictions."""
    dropout_predictions = PredictionLog.objects.filter(prediction_type="dropout")

    total_predictions = dropout_predictions.count()
    high_critical_count = dropout_predictions.filter(
        risk_level__in=["high", "critical"]
    ).count()
    unacknowledged_count = dropout_predictions.filter(
        is_acknowledged=False
    ).count()

    latest_pred = dropout_predictions.order_by("-created_at").first()
    latest_prediction_date = latest_pred.created_at if latest_pred else None

    # Get active dropout model version
    active_model = ModelVersion.objects.filter(
        model_type="dropout",
        is_active=True
    ).first()

    # Get top high-risk unacknowledged predictions
    top_risks_qs = dropout_predictions.filter(
        risk_level__in=["high", "critical"],
        is_acknowledged=False
    ).order_by("-confidence_score", "-created_at")[:10]

    # Resolve student targets
    top_risks = list(top_risks_qs)
    student_ids = [p.target_object_id for p in top_risks if p.target_model == "students.Student"]
    students_map = {}
    if student_ids:
        students_map = {s.id: s for s in Student.objects.filter(id__in=student_ids)}

    for p in top_risks:
        if p.target_model == "students.Student":
            p.student_target = students_map.get(p.target_object_id)
        else:
            p.student_target = None

    context = {
        "total_predictions": total_predictions,
        "high_critical_count": high_critical_count,
        "unacknowledged_count": unacknowledged_count,
        "latest_prediction_date": latest_prediction_date,
        "active_model": active_model,
        "top_risks": top_risks,
    }
    return render(request, "ai_engine/dropout_risk_dashboard.html", context)

