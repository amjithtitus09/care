from django.shortcuts import get_object_or_404
from django_filters import rest_framework as filters
from rest_framework.decorators import action
from rest_framework.response import Response

from care.emr.api.viewsets.base import (
    EMRBaseViewSet,
    EMRCreateMixin,
    EMRListMixin,
    EMRRetrieveMixin,
    EMRUpdateMixin,
)
from care.emr.models.account import Account
from care.emr.resources.account.spec import (
    AccountCreateSpec,
    AccountReadSpec,
    AccountRetrieveSpec,
    AccountSpec,
)
from care.emr.resources.account.sync_items import sync_account_items
from care.facility.models.facility import Facility


class AccountFilters(filters.FilterSet):
    status = filters.CharFilter(lookup_expr="iexact")
    name = filters.CharFilter(lookup_expr="icontains")
    billing_status = filters.CharFilter(lookup_expr="iexact")
    patient = filters.UUIDFilter(field_name="patient__external_id")


class AccountViewSet(
    EMRCreateMixin, EMRRetrieveMixin, EMRUpdateMixin, EMRListMixin, EMRBaseViewSet
):
    database_model = Account
    pydantic_model = AccountCreateSpec
    pydantic_update_model = AccountSpec
    pydantic_read_model = AccountReadSpec
    pydantic_retrieve_model = AccountRetrieveSpec
    filterset_class = AccountFilters
    filter_backends = [filters.DjangoFilterBackend]

    def get_facility_obj(self):
        return get_object_or_404(
            Facility,
            external_id=self.kwargs["facility_external_id"],
        )

    def perform_create(self, instance):
        instance.facility = self.get_facility_obj()
        instance.save()
        return instance

    @action(methods=["POST"], detail=True)
    def rebalance(self, request, *args, **kwargs):
        account = self.get_object()
        sync_account_items(account)
        account.save()
        return Response(AccountRetrieveSpec.serialize(account).to_json())
