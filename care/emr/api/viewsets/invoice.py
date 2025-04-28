from django.shortcuts import get_object_or_404
from django_filters import rest_framework as filters
from rest_framework.exceptions import ValidationError

from care.emr.api.viewsets.base import (
    EMRBaseViewSet,
    EMRCreateMixin,
    EMRListMixin,
    EMRRetrieveMixin,
    EMRUpdateMixin,
)
from care.emr.models.account import Account
from care.emr.models.invoice import Invoice
from care.emr.resources.invoice.spec import (
    BaseInvoiceSpec,
    InvoiceReadSpec,
    InvoiceWriteSpec,
)
from care.facility.models.facility import Facility


class InvoiceFilters(filters.FilterSet):
    status = filters.CharFilter(lookup_expr="iexact")
    title = filters.CharFilter(lookup_expr="icontains")
    account = filters.UUIDFilter(field_name="account__external_id")
    encounter = filters.UUIDFilter(field_name="encounter__external_id")


class InvoiceViewSet(
    EMRCreateMixin,
    EMRRetrieveMixin,
    EMRUpdateMixin,
    EMRListMixin,
    EMRBaseViewSet,
):
    database_model = Invoice
    pydantic_model = InvoiceWriteSpec
    pydantic_update_model = BaseInvoiceSpec
    pydantic_read_model = InvoiceReadSpec
    filterset_class = InvoiceFilters
    filter_backends = [filters.DjangoFilterBackend]

    def get_facility_obj(self):
        return get_object_or_404(
            Facility, external_id=self.kwargs["facility_external_id"]
        )

    def perform_create(self, instance):
        instance.facility = self.get_facility_obj()
        super().perform_create(instance)

    def authorize_create(self, instance):
        facility = self.get_facility_obj()
        account = get_object_or_404(Account, external_id=instance.account)
        if account.facility != facility:
            raise ValidationError("Account is not associated with the facility")
        # TODO: AuthZ pending
        return super().authorize_create(instance)
