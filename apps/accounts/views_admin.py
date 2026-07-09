"""
Admin views for user management.
Enforces permissions at view level and coordinates with UserService for all state modifications.
"""

from django.contrib import messages
from django.contrib.auth.models import Group
from django.db.models import Q
from django.http import JsonResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from apps.accounts.models import CustomUser
from apps.accounts.services import UserService
from apps.academics.models import Session, Subject
from apps.core.decorators import permission_required, post_required, _get_client_ip


@permission_required("users", "view")
def user_list(request):
    """List all users with filters and options to perform administrative actions."""
    search_query = request.GET.get("search", "").strip()
    role_filter = request.GET.get("role", "").strip()

    users = CustomUser.objects.all().prefetch_related(
        "groups",
        "teaching_assignments__session",
        "teaching_assignments__subject",
    ).order_by("-date_joined")

    if search_query:
        users = users.filter(
            Q(email__icontains=search_query) |
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(phone__icontains=search_query)
        )

    if role_filter:
        users = users.filter(groups__name=role_filter)

    from apps.core.models import RolePermission
    roles = [(role[0], f"{role[1]} Role") for role in RolePermission.ROLE_CHOICES]
    sessions = Session.objects.filter(status="Active")
    subjects = Subject.objects.filter(is_active=True)

    context = {
        "users": users,
        "roles": roles,
        "sessions": sessions,
        "subjects": subjects,
        "search_query": search_query,
        "selected_role": role_filter,
        "role": "Admin",  # Needed for layout sidebar logic
    }
    return render(request, "accounts/user_list.html", context)


@permission_required("users", "edit")
@post_required
def user_toggle_activation(request, pk):
    """Toggle a user's is_active and status fields."""
    user = get_object_or_404(CustomUser, pk=pk)

    if "active" in request.POST:
        active = request.POST.get("active") == "true"
    else:
        active = not user.is_active

    ip = _get_client_ip(request)
    ua = request.META.get("HTTP_USER_AGENT", "")

    try:
        UserService.toggle_user_activation(
            user_id=user.pk,
            active=active,
            admin_user=request.user,
            ip_address=ip,
            user_agent=ua,
        )
        msg = f"User '{user.email}' has been {'activated' if active else 'deactivated'}."
        messages.success(request, msg)
    except Exception as e:
        messages.error(request, str(e))

    return redirect(reverse("admin_panel:users:user_list"))


@permission_required("users", "edit")
@post_required
def user_toggle_lock(request, pk):
    """Toggle a user's lock/unlock status."""
    user = get_object_or_404(CustomUser, pk=pk)

    if "lock" in request.POST:
        lock = request.POST.get("lock") == "true"
    else:
        lock = not user.is_locked_out

    ip = _get_client_ip(request)
    ua = request.META.get("HTTP_USER_AGENT", "")

    try:
        UserService.toggle_user_lock(
            user_id=user.pk,
            lock=lock,
            admin_user=request.user,
            ip_address=ip,
            user_agent=ua,
        )
        msg = f"User '{user.email}' has been {'locked' if lock else 'unlocked'}."
        messages.success(request, msg)
    except Exception as e:
        messages.error(request, str(e))

    return redirect(reverse("admin_panel:users:user_list"))


@permission_required("users", "edit")
@post_required
def user_reset_password(request, pk):
    """Reset user password to a new value."""
    user = get_object_or_404(CustomUser, pk=pk)
    new_password = request.POST.get("new_password", "").strip()

    ip = _get_client_ip(request)
    ua = request.META.get("HTTP_USER_AGENT", "")

    try:
        UserService.reset_user_password(
            user_id=user.pk,
            new_password=new_password,
            admin_user=request.user,
            ip_address=ip,
            user_agent=ua,
        )
        messages.success(request, f"Password for '{user.email}' has been reset successfully.")
    except Exception as e:
        messages.error(request, str(e))

    referer = request.META.get("HTTP_REFERER", "")
    if referer and "edit" in referer:
        return redirect(reverse("admin_panel:users:user_edit", args=[user.pk]))
    return redirect(reverse("admin_panel:users:user_list"))


@permission_required("users", "edit")
@post_required
def user_assign_role(request, pk):
    """Assign a user to a specific group/role."""
    user = get_object_or_404(CustomUser, pk=pk)
    role_name = request.POST.get("role_name", "").strip()

    ip = _get_client_ip(request)
    ua = request.META.get("HTTP_USER_AGENT", "")

    try:
        UserService.assign_user_role(
            user_id=user.pk,
            role_name=role_name,
            admin_user=request.user,
            ip_address=ip,
            user_agent=ua,
        )
        messages.success(request, f"Assigned role '{role_name}' to user '{user.email}'.")
    except Exception as e:
        messages.error(request, str(e))

    return redirect(reverse("admin_panel:users:user_list"))


@permission_required("users", "edit")
@post_required
def user_assign_session(request, pk):
    """Assign a teacher to a session and optionally a subject."""
    user = get_object_or_404(CustomUser, pk=pk)
    session_id = request.POST.get("session_id", "").strip()
    subject_id = request.POST.get("subject_id", "").strip()

    ip = _get_client_ip(request)
    ua = request.META.get("HTTP_USER_AGENT", "")

    try:
        if not session_id:
            raise ValueError("Session is required.")

        subject_pk = int(subject_id) if subject_id else None

        UserService.assign_teacher_session(
            teacher_id=user.pk,
            session_id=int(session_id),
            subject_id=subject_pk,
            admin_user=request.user,
            ip_address=ip,
            user_agent=ua,
        )
        messages.success(request, f"Successfully assigned session to teacher '{user.email}'.")
    except Exception as e:
        messages.error(request, str(e))

    return redirect(reverse("admin_panel:users:user_list"))


@permission_required("users", "edit")
def user_create(request):
    """Admin-only view to create a new user account with dynamic group/profile setup."""
    from django.db import transaction
    from apps.accounts.forms import AdminUserCreateForm
    from apps.staff.models import FacultyProfile

    if request.method == "POST":
        form = AdminUserCreateForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save(commit=False)
                    user.set_password(form.cleaned_data["password"])
                    user.save()

                    role = form.cleaned_data.get("role")
                    group, _ = Group.objects.get_or_create(name=role)
                    user.groups.add(group)

                    if role == "Teacher":
                        FacultyProfile.objects.create(
                            user=user,
                            designation=form.cleaned_data.get("designation"),
                            department=form.cleaned_data.get("department"),
                            is_active=user.is_active
                        )

                    ip = _get_client_ip(request)
                    ua = request.META.get("HTTP_USER_AGENT", "")
                    UserService.audit_on_commit(
                        user=request.user,
                        action="create",
                        model_name="accounts.CustomUser",
                        object_id=user.pk,
                        changes={
                            "email": user.email,
                            "username": user.username,
                            "role": role,
                            "is_active": user.is_active
                        },
                        ip_address=ip,
                        user_agent=ua
                    )

                messages.success(request, f"User account '{user.email}' has been created successfully.")
                return redirect(reverse("admin_panel:users:user_list"))
            except Exception as e:
                messages.error(request, f"Failed to create user: {str(e)}")
    else:
        form = AdminUserCreateForm()

    context = {
        "form": form,
        "role": "Admin",
    }
    return render(request, "accounts/user_create.html", context)


@permission_required("users", "edit")
def user_edit(request, pk):
    """Admin-only view to edit an existing user account and update role/profile structures."""
    from django.db import transaction
    from apps.accounts.forms import AdminUserEditForm
    from apps.staff.models import FacultyProfile
    from apps.core.models import RolePermission

    user = get_object_or_404(CustomUser, pk=pk)

    if request.method == "POST":
        form = AdminUserEditForm(request.POST, instance=user)
        if form.is_valid():
            try:
                with transaction.atomic():
                    updated_user = form.save()
                    new_role = form.cleaned_data.get("role")
                    
                    canonical_roles = [r[0] for r in RolePermission.ROLE_CHOICES]
                    current_groups = list(user.groups.all())

                    for g in current_groups:
                        if g.name in canonical_roles and g.name != new_role:
                            user.groups.remove(g)

                    new_group, _ = Group.objects.get_or_create(name=new_role)
                    if new_group not in user.groups.all():
                        user.groups.add(new_group)

                    if new_role == "Teacher":
                        profile, created = FacultyProfile.objects.get_or_create(
                            user=updated_user,
                            defaults={
                                "designation": form.cleaned_data.get("designation"),
                                "department": form.cleaned_data.get("department"),
                                "is_active": updated_user.is_active
                            }
                        )
                        if not created:
                            profile.designation = form.cleaned_data.get("designation")
                            profile.department = form.cleaned_data.get("department")
                            profile.is_active = updated_user.is_active
                            profile.save()
                    else:
                        FacultyProfile.objects.filter(user=updated_user).delete()

                    ip = _get_client_ip(request)
                    ua = request.META.get("HTTP_USER_AGENT", "")
                    UserService.audit_on_commit(
                        user=request.user,
                        action="update",
                        model_name="accounts.CustomUser",
                        object_id=updated_user.pk,
                        changes={
                            "email": updated_user.email,
                            "role": new_role,
                            "is_active": updated_user.is_active
                        },
                        ip_address=ip,
                        user_agent=ua
                    )

                messages.success(request, f"User account '{updated_user.email}' has been updated successfully.")
                return redirect(reverse("admin_panel:users:user_list"))
            except Exception as e:
                messages.error(request, f"Failed to update user: {str(e)}")
    else:
        form = AdminUserEditForm(instance=user)

    context = {
        "form": form,
        "edit_user": user,
        "role": "Admin",
    }
    return render(request, "accounts/user_edit.html", context)
