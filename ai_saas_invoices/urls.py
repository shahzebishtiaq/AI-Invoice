from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from django.views.generic import TemplateView
from rest_framework.routers import DefaultRouter

from invoices.api.views import InvoiceViewSet
from sitemaps import StaticViewSitemap


router = DefaultRouter()

router.register(
    "invoices",
    InvoiceViewSet,
    basename="invoice-api",
)


sitemaps = {
    "static": StaticViewSitemap,
}


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

    # Sitemap
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),

    # Robots.txt
    path(
        "robots.txt",
        TemplateView.as_view(
            template_name="robots.txt",
            content_type="text/plain",
        ),
        name="robots_txt",
    ),
]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )