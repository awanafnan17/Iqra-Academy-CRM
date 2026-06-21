"""
URL Configuration for IICE.
Each app provides its own urlpatterns via include().
"""

from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from apps.achievements.views import PublicSuccessStoriesView

urlpatterns = [
    # Root redirect to login
    path("", RedirectView.as_view(url="/accounts/login/", permanent=False), name="home"),

    # Django admin
    path("admin/", admin.site.urls),

    # Authentication
    path("accounts/", include("apps.accounts.urls")),

    # Staff panels
    path("panel/admin/reports/", include("apps.reports.urls")),
    path("panel/admin/", include("apps.dashboard.urls_admin")),
    path("panel/principal/", include("apps.dashboard.urls_principal")),
    path("panel/teacher/", include("apps.dashboard.urls_teacher")),
    path("panel/accounts/", include("apps.dashboard.urls_accounts")),
    path("panel/registrar/", include("apps.dashboard.urls_registrar")),

    # Student and Guardian portals
    path(
        "portal/student/",
        include(("apps.portals.urls_student", "student_portal"), namespace="student_portal"),
    ),
    path(
        "portal/guardian/",
        include(("apps.portals.urls_parent", "guardian_portal"), namespace="guardian_portal"),
    ),

    # Internal API (AJAX)
    path("api/", include("apps.core.urls_api")),
    path("api/analytics/", include("apps.analytics.urls")),

    # Public Admission
    path("apply/", include(("apps.admissions.urls_public", "admissions_public"), namespace="admissions_public")),

    # Public Success Stories page
    path("success/", PublicSuccessStoriesView.as_view(), name="public_success"),
]

# Custom error handlers
handler403 = "apps.core.error_handlers.custom_403"
handler404 = "apps.core.error_handlers.custom_404"
handler500 = "apps.core.error_handlers.custom_500"

from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
