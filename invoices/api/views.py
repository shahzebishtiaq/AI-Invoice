from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from invoices.models import Invoice

from .serializers import InvoiceSerializer


class InvoiceViewSet(ModelViewSet):
    serializer_class = InvoiceSerializer

    permission_classes = [
        IsAuthenticated,
    ]

    def get_queryset(self):
        return Invoice.objects.filter(
            user=self.request.user,
        ).select_related(
            "client"
        ).prefetch_related(
            "items"
        )