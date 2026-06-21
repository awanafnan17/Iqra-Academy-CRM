from apps.core.models import RolePermission

def has_permission(user, module, action):
    """Enforce granular role/group permission matrix checks.

    Returns True if user is authorized, False otherwise.
    Superusers and users belonging to the 'Admin' group get full access automatically.
    """
    if not user or not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    roles = list(user.groups.values_list("name", flat=True))
    if "Admin" in roles:
        return True

    if not roles:
        return False

    field_name = f"can_{action}"

    filter_kwargs = {
        "role_name__in": roles,
        "module_name": module,
        field_name: True
    }
    return RolePermission.objects.filter(**filter_kwargs).exists()


def seed_default_permissions():
    """Seed the database with the default role/module permission matrix."""
    defaults = {
        "Admin": {
            "finance": {"view": True, "create": True, "edit": True, "delete": True, "export": True, "approve": True},
            "exams": {"view": True, "create": True, "edit": True, "delete": True, "export": True, "approve": True},
            "attendance": {"view": True, "create": True, "edit": True, "delete": True, "export": True, "approve": True},
            "students": {"view": True, "create": True, "edit": True, "delete": True, "export": True, "approve": True},
            "notifications": {"view": True, "create": True, "edit": True, "delete": True, "export": True, "approve": True},
            "users": {"view": True, "create": True, "edit": True, "delete": True, "export": True, "approve": True},
        },
        "Principal": {
            "finance": {"view": True, "create": False, "edit": False, "delete": False, "export": True, "approve": False},
            "exams": {"view": True, "create": True, "edit": True, "delete": True, "export": True, "approve": True},
            "attendance": {"view": True, "create": True, "edit": True, "delete": True, "export": True, "approve": True},
            "students": {"view": True, "create": True, "edit": True, "delete": True, "export": True, "approve": True},
            "notifications": {"view": True, "create": True, "edit": True, "delete": True, "export": True, "approve": True},
            "users": {"view": False, "create": False, "edit": False, "delete": False, "export": False, "approve": False},
        },
        "Teacher": {
            "finance": {"view": False, "create": False, "edit": False, "delete": False, "export": False, "approve": False},
            "exams": {"view": True, "create": True, "edit": True, "delete": False, "export": True, "approve": False},
            "attendance": {"view": True, "create": True, "edit": True, "delete": False, "export": True, "approve": False},
            "students": {"view": True, "create": False, "edit": False, "delete": False, "export": False, "approve": False},
            "notifications": {"view": True, "create": True, "edit": False, "delete": False, "export": False, "approve": False},
            "users": {"view": False, "create": False, "edit": False, "delete": False, "export": False, "approve": False},
        },
        "Accountant": {
            "finance": {"view": True, "create": True, "edit": True, "delete": False, "export": True, "approve": True},
            "exams": {"view": False, "create": False, "edit": False, "delete": False, "export": False, "approve": False},
            "attendance": {"view": False, "create": False, "edit": False, "delete": False, "export": False, "approve": False},
            "students": {"view": True, "create": False, "edit": False, "delete": False, "export": False, "approve": False},
            "notifications": {"view": True, "create": True, "edit": False, "delete": False, "export": False, "approve": False},
            "users": {"view": False, "create": False, "edit": False, "delete": False, "export": False, "approve": False},
        },
        "Registrar": {
            "finance": {"view": False, "create": False, "edit": False, "delete": False, "export": False, "approve": False},
            "exams": {"view": True, "create": False, "edit": False, "delete": False, "export": False, "approve": False},
            "attendance": {"view": True, "create": False, "edit": False, "delete": False, "export": False, "approve": False},
            "students": {"view": True, "create": True, "edit": True, "delete": False, "export": True, "approve": False},
            "notifications": {"view": True, "create": True, "edit": False, "delete": False, "export": False, "approve": False},
            "users": {"view": False, "create": False, "edit": False, "delete": False, "export": False, "approve": False},
        },
        "Student": {
            "finance": {"view": True, "create": False, "edit": False, "delete": False, "export": False, "approve": False},
            "exams": {"view": True, "create": False, "edit": False, "delete": False, "export": False, "approve": False},
            "attendance": {"view": True, "create": False, "edit": False, "delete": False, "export": False, "approve": False},
            "students": {"view": False, "create": False, "edit": False, "delete": False, "export": False, "approve": False},
            "notifications": {"view": True, "create": False, "edit": False, "delete": False, "export": False, "approve": False},
            "users": {"view": False, "create": False, "edit": False, "delete": False, "export": False, "approve": False},
        },
        "Guardian": {
            "finance": {"view": True, "create": False, "edit": False, "delete": False, "export": False, "approve": False},
            "exams": {"view": True, "create": False, "edit": False, "delete": False, "export": False, "approve": False},
            "attendance": {"view": True, "create": False, "edit": False, "delete": False, "export": False, "approve": False},
            "students": {"view": False, "create": False, "edit": False, "delete": False, "export": False, "approve": False},
            "notifications": {"view": True, "create": False, "edit": False, "delete": False, "export": False, "approve": False},
            "users": {"view": False, "create": False, "edit": False, "delete": False, "export": False, "approve": False},
        }
    }

    for role, modules in defaults.items():
        for module, actions in modules.items():
            RolePermission.objects.update_or_create(
                role_name=role,
                module_name=module,
                defaults={
                    "can_view": actions.get("view", False),
                    "can_create": actions.get("create", False),
                    "can_edit": actions.get("edit", False),
                    "can_delete": actions.get("delete", False),
                    "can_export": actions.get("export", False),
                    "can_approve": actions.get("approve", False),
                }
            )
