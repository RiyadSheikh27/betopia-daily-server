import logging
from rest_framework.views import APIView
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken


from apps.utils.custom_response import APIResponse
from .models import UserProfile
from .serializers import UserProfileSerializer, SSOLoginSerializer
from .utils import decode_jwt_payload, get_token_from_request
from .services.sso_service import verify_microsoft_token, fetch_graph_profile, SSOServiceError

logger = logging.getLogger(__name__)

class UserProfileView(APIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def _get_payload(self, request):
        token = get_token_from_request(request)
        if not token:
            return None, APIResponse.error(
                message="Access token is required.", status_code=401
            )
        payload = decode_jwt_payload(token)
        if not payload:
            return None, APIResponse.error(
                message="Invalid or expired access token.", status_code=401
            )
        return payload, None

    def get(self, request):
        payload, error = self._get_payload(request)
        if error:
            return error

        # Lookup profile by uid extracted from JWT — no params needed
        profile = UserProfile.objects.filter(uid=payload["uid"]).first()
        if not profile:
            return APIResponse.error(message="Profile not found.", status_code=404)

        return APIResponse.success(
            data=UserProfileSerializer(profile, context={"request": request}).data,
            message="Profile retrieved successfully.",
        )

    def post(self, request):
        payload, error = self._get_payload(request)
        if error:
            return error

        employee_id = request.data.get("employee_id")
        if not employee_id:
            return APIResponse.error(
                message="employee_id is required.", status_code=400
            )

        # uid always comes from JWT — user cannot spoof it
        uid = payload["uid"]

        # Look up by uid first since it is JWT-verified, fallback to employee_id for legacy rows
        profile = UserProfile.objects.filter(uid=uid).first()
        if not profile:
            profile = UserProfile.objects.filter(employee_id=employee_id).first()

        if profile:
            updated = False

            if profile.uid != uid:
                profile.uid = uid
                updated = True

            if profile.employee_id != employee_id:
                profile.employee_id = employee_id
                updated = True

            for field_name in (
                "email",
                "user_type",
                "company",
                "company_address",
                "phone",
                "access_token",
            ):
                new_value = request.data.get(field_name)
                if new_value is not None and getattr(profile, field_name) != new_value:
                    setattr(profile, field_name, new_value)
                    updated = True

            avatar = request.FILES.get("avatar")
            if avatar is not None:
                current_avatar_name = profile.avatar.name if profile.avatar else None
                if current_avatar_name != avatar.name:
                    profile.avatar = avatar
                    updated = True

            if updated:
                profile.save()
                message = "Profile updated successfully."
            else:
                message = "No changes detected. Profile remains unchanged."

            return APIResponse.success(
                data=UserProfileSerializer(profile, context={"request": request}).data,
                message=message,
            )

        data = request.data.copy()
        data["uid"] = uid
        serializer = UserProfileSerializer(data=data, context={"request": request})
        if not serializer.is_valid():
            return APIResponse.error(errors=serializer.errors, status_code=400)
        serializer.save()
        return APIResponse.success(
            data=serializer.data,
            message="Profile created successfully.",
        )

class SSOLoginView(APIView):
    """Verify Microsoft access token via JWKS, issue our own JWT."""

    def post(self, request):
        serializer = SSOLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return APIResponse.error(
                errors=serializer.errors,
                message="Invalid request payload.",
                status_code=422,
            )

        ms_token = serializer.validated_data["access_token"]

        try:
            claims = verify_microsoft_token(ms_token)
        except SSOServiceError as exc:
            logger.error("SSO login failed: %s", exc.message)
            return APIResponse.error(message=exc.message, status_code=exc.status_code)

        azure_oid = claims.get("oid")
        email = claims.get("preferred_username") or claims.get("upn") or claims.get("email")

        if not azure_oid:
            return APIResponse.error(message="Microsoft token missing required claims.", status_code=422)

        # Optional Graph call for richer profile info, never blocks login
        graph_profile = fetch_graph_profile(ms_token)
        display_name = graph_profile.get("displayName") if graph_profile else claims.get("name")

        # Issue our own JWT, formatted similar to old ERP login response
        refresh = RefreshToken.for_user_id(azure_oid) if hasattr(RefreshToken, "for_user_id") else None

        # SimpleJWT needs a Django User instance by default, so we mint tokens manually instead
        from rest_framework_simplejwt.tokens import AccessToken

        access = AccessToken()
        access["uid"] = azure_oid
        access["email"] = email

        refresh = RefreshToken()
        refresh["uid"] = azure_oid
        refresh["email"] = email

        return APIResponse.success(
            data={
                "access_token": str(access),
                "refresh_token": str(refresh),
                "user": {
                    "id": azure_oid,
                    "email": email,
                    "name": display_name,
                },
            },
            message="SSO login successful",
        )