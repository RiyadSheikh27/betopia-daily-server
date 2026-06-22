from django.db.models import F, Sum, OuterRef, Subquery
from django.db.models.functions import Coalesce, TruncMonth
from rest_framework.views import APIView

from apps.utils.custom_response import APIResponse
from apps.utils.pagination import StandardPagination
from apps.user.models import UserProfile
from apps.user.utils import decode_jwt_payload, get_token_from_request
from apps.checkout.models import Order, OrderItem
from apps.products.models import Product, ProductImage
from .serializers import DashboardDateFilterSerializer, DashboardUserSerializer


def _get_request_profile(request):
    token = get_token_from_request(request)
    if not token:
        return None

    payload = decode_jwt_payload(token)
    if not payload:
        return None

    return UserProfile.objects.filter(uid=payload["uid"]).first()


def _build_date_filters(validated_data, field_name):
    filters = {}
    start_date = validated_data.get("start_date")
    end_date = validated_data.get("end_date")
    if start_date is not None:
        filters[f"{field_name}__date__gte"] = start_date
    if end_date is not None:
        filters[f"{field_name}__date__lte"] = end_date
    return filters


class AdminDashboardBaseView(APIView):
    permission_classes = []

    def dispatch(self, request, *args, **kwargs):
        profile = _get_request_profile(request)
        if not profile or profile.role != "admin":
            return APIResponse.error(message="Admin access required", status_code=403)
        return super().dispatch(request, *args, **kwargs)


class DashboardSummaryView(AdminDashboardBaseView):
    def get(self, request):
        serializer = DashboardDateFilterSerializer(data=request.query_params)
        if not serializer.is_valid():
            return APIResponse.error(errors=serializer.errors, status_code=400)

        order_filters = _build_date_filters(serializer.validated_data, "created_at")
        user_filters = _build_date_filters(serializer.validated_data, "created_at")

        orders = Order.objects.filter(**order_filters)
        accepted_orders = orders.filter(status="accepted")

        summary = {
            "total_sales": float(
                accepted_orders.aggregate(total=Sum("total_amount"))["total"] or 0
            ),
            "total_orders": orders.count(),
            "total_customers": UserProfile.objects.filter(**user_filters).count(),
            "total_pending_orders": orders.filter(status="pending").count(),
            "total_accepted_orders": accepted_orders.count(),
            "total_rejected_orders": orders.filter(status="rejected").count(),
            "stock_products": Product.objects.filter(status=True).count(),
        }
        return APIResponse.success(data=summary)


class DashboardUserListView(AdminDashboardBaseView):
    def get(self, request):
        users = UserProfile.objects.all().order_by("-created_at")
        paginator = StandardPagination()
        page = paginator.paginate_queryset(users, request)
        serializer = DashboardUserSerializer(
            page, many=True, context={"request": request}
        )
        return APIResponse.paginated(
            data=serializer.data,
            pagination_meta=paginator.get_paginated_meta(),
        )


class DashboardTopProductsView(AdminDashboardBaseView):
    def get(self, request):
        serializer = DashboardDateFilterSerializer(data=request.query_params)
        if not serializer.is_valid():
            return APIResponse.error(errors=serializer.errors, status_code=400)

        order_filters = _build_date_filters(
            serializer.validated_data, "order__created_at"
        )
        primary_image = ProductImage.objects.filter(
            product_id=OuterRef("product_id"), is_primary=True
        ).values("image")[:1]
        fallback_image = ProductImage.objects.filter(
            product_id=OuterRef("product_id")
        ).values("image")[:1]

        sold_items = (
            OrderItem.objects.filter(order__status="accepted", **order_filters)
            .values("product_id", "product__slug", "product_name")
            .annotate(
                total_quantity=Sum("quantity"),
                total_amount=Sum(F("discounted_price") * F("quantity")),
                product_image=Coalesce(
                    Subquery(primary_image),
                    Subquery(fallback_image),
                ),
            )
            .order_by("-total_amount")[:5]
        )

        results = [
            {
                "product_id": item["product_id"],
                "product_name": item["product_name"],
                "product_slug": item["product__slug"],
                "product_image": (
                    request.build_absolute_uri(item["product_image"])
                    if item["product_image"]
                    else None
                ),
                "total_quantity": item["total_quantity"],
                "total_amount": float(item["total_amount"] or 0),
            }
            for item in sold_items
        ]

        return APIResponse.success(data=results)


class DashboardRevenueChartView(AdminDashboardBaseView):
    def get(self, request):
        serializer = DashboardDateFilterSerializer(data=request.query_params)
        if not serializer.is_valid():
            return APIResponse.error(errors=serializer.errors, status_code=400)

        order_filters = _build_date_filters(serializer.validated_data, "created_at")
        revenue = (
            Order.objects.filter(status="accepted", **order_filters)
            .annotate(month=TruncMonth("created_at"))
            .values("month")
            .annotate(amount=Sum("total_amount"))
            .order_by("month")
        )

        data = [
            {
                "month": item["month"].strftime("%Y-%m"),
                "amount": float(item["amount"] or 0),
            }
            for item in revenue
        ]

        return APIResponse.success(data=data)
