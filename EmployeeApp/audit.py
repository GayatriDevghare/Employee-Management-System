from .models import AuditLog



def get_client_ip(request):
    """
    Get the user's IP address from the request.
    """
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    return request.META.get("REMOTE_ADDR")


def log_activity(
    request,
    action,
    description="",
    user=None,
):
    """
    Create an Activity/Audit Log.

    Parameters:
        request      : Django request object
        action       : LOGIN, LOGOUT, CREATE, UPDATE, DELETE, etc.
        description  : Human-readable description
        user         : Employee object responsible for the action
    """

    try:
        username = None
        role = None

        # If Employee object is supplied
        if user:
            username = getattr(user, "name", None)
            role = getattr(user, "role", None)

        # Otherwise try to get information from session
        if not username:
            username = request.session.get("name")

        if not role:
            role = request.session.get("role")

        AuditLog.objects.create(
            user=user,
            username=username,
            role=role,
            action=action,
            description=description,
            ip_address=get_client_ip(request),
        )

    except Exception as e:
        # Activity logging should never break the main application.
        print(f"Activity Log Error: {e}")