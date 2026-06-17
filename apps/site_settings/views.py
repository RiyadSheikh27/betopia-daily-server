from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from apps.utils.custom_response import APIResponse
from .models import HeroImage
from .serializers import HeroImageSerializer, HeroImageOrderUpdateSerializer


class HeroImageView(APIView):
    """
    GET    — list all hero images ordered by order field
    POST   — upload one or more images
    DELETE — delete a single image by image_id
    PATCH  — update order of a single image by image_id
    """

    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        images = HeroImage.objects.all()
        serializer = HeroImageSerializer(images, many=True, context={"request": request})
        return APIResponse.success(data=serializer.data)

    def post(self, request):
        files = request.FILES.getlist("images")
        if not files:
            return APIResponse.error(message="No images provided")

        # Start order after the current max
        last_order = HeroImage.objects.order_by("-order").values_list("order", flat=True).first() or 0

        created = []
        for index, file in enumerate(files):
            img = HeroImage.objects.create(image=file, order=last_order + index + 1)
            created.append(img)

        serializer = HeroImageSerializer(created, many=True, context={"request": request})
        return APIResponse.success(data=serializer.data, message="Images uploaded successfully")

    def delete(self, request):
        image_id = request.data.get("image_id")
        if not image_id:
            return APIResponse.error(message="image_id is required")
        try:
            image = HeroImage.objects.get(pk=image_id)
            image.delete()
            return APIResponse.success(message="Image deleted successfully")
        except HeroImage.DoesNotExist:
            return APIResponse.error(message="Image not found", status_code=404)

    def patch(self, request):
        image_id = request.data.get("image_id")
        if not image_id:
            return APIResponse.error(message="image_id is required")
        try:
            image = HeroImage.objects.get(pk=image_id)
        except HeroImage.DoesNotExist:
            return APIResponse.error(message="Image not found", status_code=404)

        serializer = HeroImageOrderUpdateSerializer(image, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return APIResponse.success(
                data=HeroImageSerializer(image, context={"request": request}).data,
                message="Order updated successfully"
            )
        return APIResponse.error(errors=serializer.errors)