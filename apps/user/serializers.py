from rest_framework import serializers
from .models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = [
            "uid",
            "employee_id",
            "email",
            "user_type",
            "company",
            "company_address",
            "avatar",
            "phone",
            "access_token",
            "role",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["role", "created_at", "updated_at"]
        extra_kwargs = {
            "employee_id": {"validators": []},
            "uid": {"validators": []},
        }

    def get_avatar(self, obj):
        request = self.context.get("request")
        if obj.avatar and request:
            return request.build_absolute_uri(obj.avatar.url)
        return None

class SSOLoginSerializer(serializers.Serializer):
    access_token = serializers.CharField(required=True, allow_blank=False)