from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError


def get_token_from_request(request):
    """Extract bearer token from the Authorization header."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    return auth_header.split(" ", 1)[1].strip()


def decode_jwt_payload(token):
    """Decode and validate our own issued JWT, return payload dict or None."""
    try:
        access = AccessToken(token)
        return {"uid": access["uid"], "email": access.get("email")}
    except TokenError:
        return None