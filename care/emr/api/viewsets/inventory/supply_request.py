from django.shortcuts import get_object_or_404
from django_filters import rest_framework as filters
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import OrderingFilter

from care.emr.api.viewsets.base import (
    EMRBaseViewSet,
    EMRCreateMixin,
    EMRListMixin,
    EMRRetrieveMixin,
    EMRUpdateMixin,
    EMRUpsertMixin,
)
from care.emr.models.location import FacilityLocation
from care.emr.models.supply_request import SupplyRequest
from care.emr.resources.inventory.supply_request.spec import (
    SupplyRequestReadSpec,
    SupplyRequestWriteSpec,
)
from care.security.authorization.base import AuthorizationController
from care.utils.filters.null_filter import NullFilter


class SupplyRequestFilters(filters.FilterSet):
    status = filters.CharFilter(lookup_expr="iexact")
    priority = filters.CharFilter(lookup_expr="iexact")
    item = filters.UUIDFilter(field_name="item__external_id")
    deliver_from_isnull = NullFilter(field_name="deliver_from")
    supplier = filters.UUIDFilter(field_name="supplier__external_id")


class SupplyRequestViewSet(
    EMRCreateMixin,
    EMRRetrieveMixin,
    EMRUpdateMixin,
    EMRListMixin,
    EMRUpsertMixin,
    EMRBaseViewSet,
):
    database_model = SupplyRequest
    pydantic_model = SupplyRequestWriteSpec
    pydantic_read_model = SupplyRequestReadSpec
    filterset_class = SupplyRequestFilters
    filter_backends = [filters.DjangoFilterBackend, OrderingFilter]
    ordering_fields = ["created_date", "modified_date"]

    def authorize_location_read(self, location_obj):
        if not AuthorizationController.call(
            "can_list_facility_supply_request", self.request.user, location_obj
        ):
            raise PermissionDenied("Cannot list supply requests")

    def authorize_location_write(self, location_obj):
        if not AuthorizationController.call(
            "can_write_facility_supply_request", self.request.user, location_obj
        ):
            raise PermissionDenied("Cannot write supply requests")

    def authorize_create(self, instance):
        if instance.deliver_from:
            from_location = get_object_or_404(
                FacilityLocation, external_id=instance.deliver_from
            )
            self.authorize_location_write(from_location)

    def authorize_update(self, request_obj, model_instance):
        if model_instance.deliver_from:
            self.authorize_location_write(model_instance.deliver_from)

    def authorize_retrieve(self, model_instance):
        if model_instance.deliver_from:
            self.authorize_location_read(model_instance.deliver_from)
        if model_instance.deliver_to:
            self.authorize_location_read(model_instance.deliver_to)
        return super().authorize_retrieve(model_instance)

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == "list":
            if (
                "deliver_from" not in self.request.GET
                and "deliver_to" not in self.request.GET
            ):
                raise PermissionDenied("Either deliver_from or deliver_to is required")
            if "deliver_from" in self.request.GET:
                from_location = get_object_or_404(
                    FacilityLocation, external_id=self.request.GET["deliver_from"]
                )
                self.authorize_location_read(from_location)
                queryset = queryset.filter(deliver_from=from_location)
            if "deliver_to" in self.request.GET:
                to_location = get_object_or_404(
                    FacilityLocation, external_id=self.request.GET["deliver_to"]
                )
                self.authorize_location_read(to_location)
                queryset = queryset.filter(deliver_to=to_location)
        return queryset
