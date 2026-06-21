import logging
import jwt
import requests
from jwt import PyJWKClient
from django.conf import settings

logger = logging.getLogger(__name__)

JWKS_URL = (
    f"https://login.microsoftonline.com/{settings.MS_SSO_TENANT_ID}/discovery/v2.0/keys"
)


class SSOServiceError(Exception):
    def __init__(self, message, status_code=401):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def verify_microsoft_token(access_token):
    """
    Verify the Microsoft access token signature using Microsoft's JWKS,
    and validate issuer, audience, and expiry.
    Returns decoded claims on success.
    """
    try:
        unverified = jwt.decode(access_token, options={"verify_signature": False})
        logger.warning("DEBUG unverified claims: %s", unverified)
    except Exception as exc:
        logger.error("Could not decode token for debug: %s", exc)

    try:
        jwk_client = PyJWKClient(JWKS_URL)
        signing_key = jwk_client.get_signing_key_from_jwt(access_token)

        claims = jwt.decode(
            access_token,
            signing_key.key,
            algorithms=["RS256"],
            audience=settings.MS_SSO_CLIENT_ID,
            issuer=f"https://login.microsoftonline.com/{settings.MS_SSO_TENANT_ID}/v2.0",
            options={"verify_exp": True},
        )
        return claims
    except jwt.ExpiredSignatureError:
        raise SSOServiceError("Microsoft token has expired.", status_code=401)
    except jwt.InvalidTokenError as exc:
        logger.warning("Invalid Microsoft token: %s", exc)
        raise SSOServiceError("Invalid Microsoft token.", status_code=401)
    except Exception as exc:
        logger.error("JWKS verification failed: %s", exc)
        raise SSOServiceError("Unable to verify Microsoft token.", status_code=503)

def fetch_graph_profile(access_token):
    """
    Optional - call Microsoft Graph to fetch extra profile info.
    Returns dict or None if it fails, never blocks login.
    """
    try:
        response = requests.get(
            "https://graph.microsoft.com/v1.0/me",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        if response.status_code == 200:
            return response.json()
    except requests.RequestException as exc:
        logger.warning("Microsoft Graph call failed: %s", exc)
    return None
