"""
Account utility functions for the Academy CRM.

Provides the post-login redirect routing logic based on
Django Group membership.
"""


def get_role_redirect_url(user):
    """Return the dashboard URL for the user's highest-priority role.

    Checks group membership in priority order. If a user belongs
    to multiple groups, the highest-priority match wins.

    Priority (highest to lowest):
        Admin > Principal > Accountant > Registrar > Teacher > Student > Guardian

    Returns:
        str: Dashboard URL path for the matched role, or login URL as fallback.
    """
    if not user.is_authenticated:
        return "/accounts/login/"

    # Superusers always go to admin panel
    if user.is_superuser:
        return "/panel/admin/dashboard/"

    # Cache group names to avoid multiple DB hits
    user_groups = set(user.groups.values_list("name", flat=True))

    # Priority-ordered role to URL mapping
    role_redirects = [
        ("Admin", "/panel/admin/dashboard/"),
        ("Principal", "/panel/principal/dashboard/"),
        ("Accountant", "/panel/accounts/dashboard/"),
        ("Registrar", "/panel/registrar/dashboard/"),
        ("Teacher", "/panel/teacher/dashboard/"),
        ("Student", "/portal/student/dashboard/"),
        ("Guardian", "/portal/guardian/dashboard/"),
    ]

    for group_name, url in role_redirects:
        if group_name in user_groups:
            return url

    # No matching group found
    return "/accounts/login/"
