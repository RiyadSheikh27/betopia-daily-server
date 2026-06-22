from rest_framework import serializers

from apps.user.models import UserProfile


class DashboardUserSerializer(serializers.ModelSerializer):
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
            "role",
            "created_at",
        ]

    def get_avatar(self, obj):
        request = self.context.get("request")
        if obj.avatar and request:
            return request.build_absolute_uri(obj.avatar.url)
        return None


class DashboardDateFilterSerializer(serializers.Serializer):
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)

    def validate(self, attrs):
        start_date = attrs.get("start_date")
        end_date = attrs.get("end_date")
        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError(
                "end_date must be equal to or later than start_date."
            )
        return attrs
