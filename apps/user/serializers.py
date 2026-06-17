from rest_framework import serializers
from .models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ["uid", "employee_id", "email", "user_type", "company", "role", "created_at", "updated_at"]
        read_only_fields = ["role", "created_at", "updated_at"]
        extra_kwargs = {
            "employee_id": {"validators": []},
            "uid": {"validators": []},
        }