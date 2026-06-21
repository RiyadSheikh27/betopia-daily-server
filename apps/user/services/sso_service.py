import logging
from functools import lru_cache

import jwt
import requests
from jwt import PyJWKClient
from django.conf import settings

logger = logging.getLogger(__name__)

GRAPH_AUDIENCE = "00000003-0000-0000-c000-000000000000"


class SSOServiceError(Exception):
    def __init__(self, message, status_code=401):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def _normalize_issuer(issuer):
    if not isinstance(issuer, str):
        raise SSOServiceError(
            "Microsoft token issuer is missing or invalid.", status_code=401
        )
    return issuer.rstrip("/")


def _get_openid_configuration_url(issuer):
    issuer = _normalize_issuer(issuer)

    if issuer.endswith("/.well-known/openid-configuration"):
        return issuer

    if issuer.startswith("https://sts.windows.net/"):
        tenant_id = issuer.split("/")[-1]
        return f"https://login.microsoftonline.com/{tenant_id}/v2.0/.well-known/openid-configuration"

    if issuer.startswith("https://login.microsoftonline.com/"):
        if issuer.endswith("/v2.0"):
            return f"{issuer}/.well-known/openid-configuration"
        return f"{issuer}/v2.0/.well-known/openid-configuration"

    if ".b2clogin.com" in issuer:
        if issuer.endswith("/v2.0"):
            return f"{issuer}/.well-known/openid-configuration"
        return f"{issuer}/.well-known/openid-configuration"

    raise SSOServiceError("Unsupported Microsoft issuer.", status_code=401)


@lru_cache(maxsize=8)
def _fetch_openid_configuration(metadata_url):
    try:
        response = requests.get(metadata_url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        logger.error(
            "Failed to fetch Microsoft OpenID configuration from %s: %s",
            metadata_url,
            exc,
        )
        raise SSOServiceError(
            "Unable to load Microsoft OpenID configuration.", status_code=503
        )


def _get_signing_key_from_token(token):
    try:
        unverified_claims = jwt.decode(
            token,
            options={
                "verify_signature": False,
                "verify_exp": False,
                "verify_aud": False,
                "verify_iss": False,
            },
        )
        issuer = unverified_claims.get("iss")
        if not issuer:
            raise SSOServiceError("Microsoft token issuer is missing.", status_code=401)

        metadata_url = _get_openid_configuration_url(issuer)
        metadata = _fetch_openid_configuration(metadata_url)
        jwks_uri = metadata.get("jwks_uri")
        if not jwks_uri:
            raise SSOServiceError(
                "Microsoft JWKS URI could not be determined.", status_code=503
            )

        jwk_client = PyJWKClient(jwks_uri)
        signing_key = jwk_client.get_signing_key_from_jwt(token)
        return signing_key
    except Exception as exc:
        logger.warning("Unable to parse or verify Microsoft token key: %s", exc)
        raise SSOServiceError("Invalid Microsoft token.", status_code=401)


def _validate_claims(claims):
    accepted_audiences = {
        settings.MS_SSO_CLIENT_ID,
        GRAPH_AUDIENCE,
        f"api://{settings.MS_SSO_CLIENT_ID}",
    }
    accepted_issuers = {
        f"https://sts.windows.net/{settings.MS_SSO_TENANT_ID}",
        f"https://login.microsoftonline.com/{settings.MS_SSO_TENANT_ID}",
        f"https://login.microsoftonline.com/{settings.MS_SSO_TENANT_ID}/v2.0",
        "https://login.microsoftonline.com/common",
        "https://login.microsoftonline.com/common/v2.0",
        "https://login.microsoftonline.com/organizations",
        "https://login.microsoftonline.com/organizations/v2.0",
    }

    issuer = _normalize_issuer(claims.get("iss"))
    if issuer not in accepted_issuers:
        logger.warning("Microsoft token issuer mismatch: %s", issuer)
        raise SSOServiceError("Microsoft token issuer is invalid.", status_code=401)

    aud = claims.get("aud")
    aud_values = aud if isinstance(aud, list) else [aud]
    if not any(value in accepted_audiences for value in aud_values):
        logger.warning("Microsoft token audience mismatch: %s", aud_values)
        raise SSOServiceError("Microsoft token audience is invalid.", status_code=401)

    appid = claims.get("appid")
    azp = claims.get("azp")
    if appid is not None:
        if appid != settings.MS_SSO_CLIENT_ID:
            logger.warning("Token appid mismatch: %s", appid)
            raise SSOServiceError(
                "Token was not issued for this application.", status_code=401
            )
    elif azp != settings.MS_SSO_CLIENT_ID:
        logger.warning("Token azp mismatch: %s", azp)
        raise SSOServiceError(
            "Token was not issued for this application.", status_code=401
        )


def verify_microsoft_token(access_token):
    """
    Verify a Microsoft token using Azure AD JWKS.
    Returns decoded claims on success.
    """
    try:
        signing_key = _get_signing_key_from_token(access_token)
        claims = jwt.decode(
            access_token,
            signing_key.key,
            algorithms=["RS256"],
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_aud": False,
                "verify_iss": False,
            },
        )

        _validate_claims(claims)
        return claims
    except jwt.ExpiredSignatureError:
        raise SSOServiceError("Microsoft token has expired.", status_code=401)
    except SSOServiceError:
        raise
    except jwt.InvalidTokenError as exc:
        logger.warning(
            "Microsoft JWT signature validation failed, attempting Graph token validation: %s",
            exc,
        )
        graph_claims = verify_microsoft_token_via_graph(access_token)
        if graph_claims:
            return graph_claims
        raise SSOServiceError("Invalid Microsoft token.", status_code=401)
    except Exception as exc:
        logger.error("JWKS verification failed: %s", exc)
        raise SSOServiceError("Unable to verify Microsoft token.", status_code=503)


def verify_microsoft_token_via_graph(access_token):
    profile = fetch_graph_profile(access_token)
    if not profile:
        return None

    if not profile.get("id"):
        return None

    return {
        "oid": profile.get("id"),
        "preferred_username": profile.get("userPrincipalName") or profile.get("mail"),
        "name": profile.get("displayName"),
    }


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
