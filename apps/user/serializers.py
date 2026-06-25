from rest_framework import serializers
from .models import UserProfile


class UserProfileLimitedSerializer(serializers.ModelSerializer):
    """Limited user profile serializer for admin views - excludes sensitive fields."""

    avatar = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = [
            "uid",
            "employee_id",
            "full_name",
            "email",
            "company",
            "avatar",
            "phone",
        ]

    def get_avatar(self, obj):
        request = self.context.get("request")
        if obj.avatar and request:
            return request.build_absolute_uri(obj.avatar.url)
        return None


class UserProfileSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = [
            "uid",
            "employee_id",
            "full_name",
            "email",
            "user_type",
            "company",
            "company_address",
            "avatar",
            "phone",
            "role",
            "microsoft_access_token",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["role", "created_at", "updated_at"]
        extra_kwargs = {
            "employee_id": {"validators": []},
            "uid": {"validators": []},
            "microsoft_access_token": {"write_only": True},
        }

    def get_avatar(self, obj):
        request = self.context.get("request")
        if obj.avatar and request:
            return request.build_absolute_uri(obj.avatar.url)
        return None


class SSOLoginSerializer(serializers.Serializer):
    access_token = serializers.CharField(required=False, allow_blank=False)
    id_token = serializers.CharField(required=False, allow_blank=False)

    def validate(self, attrs):
        if not attrs.get("access_token") and not attrs.get("id_token"):
            raise serializers.ValidationError(
                "Either access_token or id_token is required."
            )
        return attrs
