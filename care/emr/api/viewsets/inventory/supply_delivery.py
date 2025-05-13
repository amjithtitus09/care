from django_filters import rest_framework as filters

from care.emr.api.viewsets.base import (
    EMRBaseViewSet,
    EMRCreateMixin,
    EMRListMixin,
    EMRRetrieveMixin,
    EMRUpdateMixin,
)
from care.emr.models.supply_delivery import SupplyDelivery
from care.emr.resources.inventory.supply_delivery.spec import (
    BaseSupplyDeliverySpec,
    SupplyDeliveryReadSpec,
    SupplyDeliveryWriteSpec,
)


class SupplyDeliveryFilters(filters.FilterSet):
    status = filters.CharFilter(lookup_expr="iexact")
    origin = filters.UUIDFilter(field_name="origin__external_id")
    destination = filters.UUIDFilter(field_name="destination__external_id")
    supplied_item = filters.UUIDFilter(field_name="supplied_item__external_id")


class SupplyDeliveryViewSet(
    EMRCreateMixin, EMRRetrieveMixin, EMRUpdateMixin, EMRListMixin, EMRBaseViewSet
):
    database_model = SupplyDelivery
    pydantic_model = SupplyDeliveryWriteSpec
    pydantic_update_model = BaseSupplyDeliverySpec
    pydantic_read_model = SupplyDeliveryReadSpec
    filterset_class = SupplyDeliveryFilters
    filter_backends = [filters.DjangoFilterBackend]
