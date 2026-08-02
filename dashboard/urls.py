from django.urls import path

from .views import (
    dashboard_view,
    landing_page,
    pricing_page,
)


urlpatterns = [
    path(
        "",
        landing_page,
        name="landing_page",
    ),
    path(
        "dashboard/",
        dashboard_view,
        name="dashboard",
    ),
    path(
        "pricing/",
        pricing_page,
        name="pricing",
    ),
]