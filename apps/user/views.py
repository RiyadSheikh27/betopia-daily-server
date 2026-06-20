from rest_framework.views import APIView
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle

from apps.utils.custom_response import APIResponse
from .models import UserProfile
from .serializers import UserProfileSerializer
from .utils import decode_jwt_payload, get_token_from_request


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
        serializer = UserProfileSerializer(
            data=data, files=request.FILES, context={"request": request}
        )
        if not serializer.is_valid():
            return APIResponse.error(errors=serializer.errors, status_code=400)
        serializer.save()
        return APIResponse.success(
            data=serializer.data,
            message="Profile created successfully.",
        )
