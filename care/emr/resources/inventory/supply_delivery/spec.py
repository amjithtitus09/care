from enum import Enum

from django.shortcuts import get_object_or_404
from pydantic import UUID4

from care.emr.models.location import FacilityLocation
from care.emr.models.product import Product
from care.emr.models.supply_delivery import SupplyDelivery
from care.emr.resources.base import EMRResource
from care.emr.resources.inventory.product.spec import ProductReadSpec
from care.emr.resources.location.spec import FacilityLocationListSpec


class SupplyDeliveryStatusOptions(str, Enum):
    in_progress = "in_progress"
    completed = "completed"
    abandoned = "abandoned"
    entered_in_error = "entered_in_error"


class SupplyDeliveryTypeOptions(str, Enum):
    product = "product"
    device = "device"


class SupplyDeliveryConditionOptions(str, Enum):
    normal = "normal"
    damaged = "damaged"


class BaseSupplyDeliverySpec(EMRResource):
    """Base model for supply delivery"""

    __model__ = SupplyDelivery
    __exclude__ = ["supplied_item", "origin", "destination"]

    id: UUID4 | None = None

    status: SupplyDeliveryStatusOptions
    supplied_item_condition: SupplyDeliveryConditionOptions | None = None


class SupplyDeliveryWriteSpec(BaseSupplyDeliverySpec):
    """Supply delivery write specification"""

    supplied_item_quantity: float
    supplied_item: UUID4
    origin: UUID4 | None = None
    destination: UUID4
    # delivery_type: SupplyDeliveryTypeOptions

    def perform_extra_deserialization(self, is_update, obj):
        obj.supplied_item = get_object_or_404(
            Product.objects.only("id").filter(external_id=self.supplied_item)
        )
        obj.destination = get_object_or_404(
            FacilityLocation.objects.only("id").filter(external_id=self.destination)
        )
        if self.origin:
            obj.origin = get_object_or_404(
                FacilityLocation.objects.only("id").filter(external_id=self.origin)
            )
        return obj


class SupplyDeliveryReadSpec(BaseSupplyDeliverySpec):
    """Supply delivery read specification"""

    supplied_item_quantity: int
    supplied_item: UUID4
    origin: dict
    destination: dict

    @classmethod
    def perform_extra_serialization(cls, mapping, obj):
        mapping["id"] = obj.external_id
        if obj.origin:
            mapping["origin"] = FacilityLocationListSpec.serialize(obj.origin).to_json()
        mapping["destination"] = FacilityLocationListSpec.serialize(
            obj.destination
        ).to_json()
        mapping["supplied_item"] = ProductReadSpec.serialize(
            obj.supplied_item
        ).to_json()
