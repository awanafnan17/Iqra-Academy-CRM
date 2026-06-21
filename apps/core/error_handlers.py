"""
Custom error handlers for the Academy CRM.

All handlers render standardized error pages. The 403 handler
intentionally renders the 404 template to hide route existence
from unauthorized users.
"""

import logging

from django.http import HttpResponseNotFound, HttpResponseServerError
from django.template import loader

logger = logging.getLogger("crm.security")


def custom_403(request, exception=None):
    """Handle 403 Forbidden by rendering a 404 page.

    This intentionally hides the existence of protected routes
    from users who lack permission to access them.
    """
    logger.warning(
        "403 converted to 404: user=%s path=%s",
        getattr(request.user, "pk", "anonymous"),
        request.path,
    )
    template = loader.get_template("errors/404.html")
    context = {"request_path": request.path}
    return HttpResponseNotFound(template.render(context, request))


def custom_404(request, exception=None):
    """Handle 404 Not Found."""
    template = loader.get_template("errors/404.html")
    context = {"request_path": request.path}
    return HttpResponseNotFound(template.render(context, request))


def custom_500(request):
    """Handle 500 Internal Server Error.

    Logs the error at CRITICAL level. No traceback is shown
    to the user in production.
    """
    logger.critical(
        "500 Internal Server Error: path=%s user=%s",
        request.path,
        getattr(request.user, "pk", "anonymous"),
    )
    template = loader.get_template("errors/500.html")
    return HttpResponseServerError(template.render({}, request))
