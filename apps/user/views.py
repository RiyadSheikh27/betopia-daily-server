from rest_framework.views import APIView

from apps.utils.custom_response import APIResponse
from .models import UserProfile
from .serializers import UserProfileSerializer
from .utils import decode_jwt_payload, get_token_from_request


class UserProfileView(APIView):

    def _get_payload(self, request):
        token = get_token_from_request(request)
        if not token:
            return None, APIResponse.error(message="Access token is required.", status_code=401)
        payload = decode_jwt_payload(token)
        if not payload:
            return None, APIResponse.error(message="Invalid or expired access token.", status_code=401)
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
            data=UserProfileSerializer(profile).data,
            message="Profile retrieved successfully.",
        )

    def post(self, request):
        payload, error = self._get_payload(request)
        if error:
            return error

        employee_id = request.data.get("employee_id")
        if not employee_id:
            return APIResponse.error(message="employee_id is required.", status_code=400)

        # uid always comes from JWT — user cannot spoof it
        uid = payload["uid"]

        try:
            profile = UserProfile.objects.get(employee_id=employee_id)
            profile.uid = uid
            profile.email = request.data.get("email", profile.email)
            profile.user_type = request.data.get("user_type", profile.user_type)
            profile.company = request.data.get("company", profile.company)
            profile.save()
            return APIResponse.success(
                data=UserProfileSerializer(profile).data,
                message="Profile updated successfully.",
            )
        except UserProfile.DoesNotExist:
            data = request.data.copy()
            data["uid"] = uid
            serializer = UserProfileSerializer(data=data)
            if not serializer.is_valid():
                return APIResponse.error(errors=serializer.errors, status_code=400)
            serializer.save()
            return APIResponse.success(
                data=serializer.data,
                message="Profile created successfully.",
            )