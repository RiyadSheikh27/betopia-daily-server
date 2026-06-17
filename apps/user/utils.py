import base64
import json
import time


def decode_jwt_payload(token: str) -> dict | None:
    """
    Decode JWT payload without signature verification.
    Returns payload dict or None if token is invalid/expired.
    """
    try:
        # JWT structure: header.payload.signature
        payload_b64 = token.split(".")[1]

        # Base64 padding fix
        padding = 4 - len(payload_b64) % 4
        payload_b64 += "=" * padding

        payload = json.loads(base64.urlsafe_b64decode(payload_b64))

        # Check expiry
        if payload.get("exp", 0) < time.time():
            return None

        return payload

    except Exception:
        return None


def get_token_from_request(request) -> str | None:
    auth = request.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        return auth.split(" ", 1)[1].strip()
    return None