from rest_framework.permissions import BasePermission

from .models import UserProfile
from .utils import decode_jwt_payload, get_token_from_request


def _get_profile_from_request(request) -> UserProfile | None:
    """Resolve the UserProfile from the JWT in the request."""
    token = get_token_from_request(request)
    if not token:
        return None

    payload = decode_jwt_payload(token)
    if not payload:
        return None

    uid = payload["uid"]
    profile = UserProfile.objects.filter(uid=uid).first()
    if profile is not None:
        return profile

    # fallback when tokens still carry a numeric employee_id as uid
    try:
        employee_id = int(uid)
    except (TypeError, ValueError):
        return None
    return UserProfile.objects.filter(employee_id=employee_id).first()


class IsAuthenticated(BasePermission):
    """Allow access only to requests with a valid, non-expired JWT."""

    message = "Authentication required."

    def has_permission(self, request, view):
        token = get_token_from_request(request)
        if not token:
            return False
        return decode_jwt_payload(token) is not None


class IsAuthenticatedOrReadOnly(BasePermission):
    """Allow read (GET, HEAD, OPTIONS) to anyone; write requires a valid JWT."""

    message = "Authentication required for this action."

    def has_permission(self, request, view):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        token = get_token_from_request(request)
        if not token:
            return False
        return decode_jwt_payload(token) is not None


class IsAdminOrReadOnly(BasePermission):
    """Allow read to anyone; write only to users with role='admin'."""

    message = "Admin access required."

    def has_permission(self, request, view):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        profile = _get_profile_from_request(request)
        return profile is not None and profile.role == "admin"
