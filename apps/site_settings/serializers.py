from rest_framework import serializers
from .models import HeroImage


class HeroImageSerializer(serializers.ModelSerializer):
    """ Serializer for Hero Section """
    
    image = serializers.SerializerMethodField()

    class Meta:
        model = HeroImage
        fields = ["id", "image", "order", "is_active"]

    def get_image(self, obj):
        request = self.context.get("request")
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None


class HeroImageOrderUpdateSerializer(serializers.ModelSerializer):
    """ Hero Section's Order and Status Management Serializer """
    class Meta:
        model = HeroImage
        fields = ["id", "order", "is_active"]