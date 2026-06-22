from django.urls import path
from .views import (
    DashboardSummaryView,
    DashboardUserListView,
    DashboardTopProductsView,
    DashboardRevenueChartView,
)

urlpatterns = [
    path(
        "dashboard/summary/", DashboardSummaryView.as_view(), name="dashboard-summary"
    ),
    path(
        "dashboard/users/", DashboardUserListView.as_view(), name="dashboard-user-list"
    ),
    path(
        "dashboard/top-products/",
        DashboardTopProductsView.as_view(),
        name="dashboard-top-products",
    ),
    path(
        "dashboard/revenue-chart/",
        DashboardRevenueChartView.as_view(),
        name="dashboard-revenue-chart",
    ),
]
