from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from invoices.api.views import InvoiceViewSet


router = DefaultRouter()

router.register(
    "invoices",
    InvoiceViewSet,
    basename="invoice-api",
)

urlpatterns = [
    path("admin/", admin.site.urls),

    path("", include("dashboard.urls")),
    path("accounts/", include("accounts.urls")),
    path("clients/", include("clients.urls")),
    path("invoices/", include("invoices.urls")),
    path("ai/", include("ai_tools.urls")),
    path(
        "subscriptions/",
        include("subscriptions.urls"),
    ),
    path("api/", include(router.urls)),
]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
