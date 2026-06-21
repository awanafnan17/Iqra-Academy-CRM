"""
Account views for the Academy CRM.

Handles authentication (login, logout, password change) and
profile management. Login and logout use Django built-in views
via URL configuration. This module provides the post-login
redirect and profile placeholders.
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from apps.accounts.utils import get_role_redirect_url


@login_required
def post_login_redirect(request):
    """Redirect authenticated users to their role-specific dashboard.

    This view is the target of LOGIN_REDIRECT_URL. After Django's
    LoginView authenticates the user, it redirects here. This view
    then routes the user to the correct panel dashboard.
    """
    url = get_role_redirect_url(request.user)
    return redirect(url)


@login_required
def profile_view(request):
    """Display and edit user profile."""
    from apps.accounts.forms import UserProfileForm
    from django.contrib import messages
    user = request.user
    if request.method == "POST":
        form = UserProfileForm(request.POST, request.FILES or None, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("accounts:profile_view")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = UserProfileForm(instance=user)

    profile = getattr(user, 'profile', None)
    return render(request, "accounts/profile.html", {
        "form": form,
        "user": user,
        "profile": profile,
        "page_title": "My Profile"
    })


@login_required
def profile_edit(request):
    """Redirect to profile_view as it handles display and update."""
    return redirect("accounts:profile_view")

