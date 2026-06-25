from django.utils.deprecation import MiddlewareMixin


class DisableCSRFForAPIMiddleware(MiddlewareMixin):
    """Disable CSRF checks for API requests handled under /api/v1/."""

    def process_view(self, request, callback, callback_args, callback_kwargs):
        if request.path.startswith("/api/v1/"):
            request._dont_enforce_csrf_checks = True
        return None
