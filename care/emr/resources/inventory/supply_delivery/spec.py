import datetime
from enum import Enum

from django.shortcuts import get_object_or_404
from pydantic import UUID4

from care.emr.models.location import FacilityLocation
from care.emr.models.product import Product
from care.emr.models.supply_delivery import SupplyDelivery
from care.emr.models.supply_request import SupplyRequest
from care.emr.resources.base import EMRResource
from care.emr.resources.inventory.product.spec import ProductReadSpec
from care.emr.resources.inventory.supply_request.spec import SupplyRequestReadSpec
from care.emr.resources.location.spec import FacilityLocationListSpec
from care.emr.resources.user.spec import UserSpec


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
    __exclude__ = ["supplied_item", "origin", "destination", "supply_request"]

    id: UUID4 | None = None

    status: SupplyDeliveryStatusOptions
    supplied_item_condition: SupplyDeliveryConditionOptions | None = None


class SupplyDeliveryWriteSpec(BaseSupplyDeliverySpec):
    """Supply delivery write specification"""

    supplied_item_quantity: float
    supplied_item: UUID4
    origin: UUID4 | None = None
    destination: UUID4
    supply_request: UUID4 | None = None

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
        if self.supply_request:
            obj.supply_request = get_object_or_404(
                SupplyRequest.objects.only("id").filter(external_id=self.supply_request)
            )
        return obj


class SupplyDeliveryReadSpec(BaseSupplyDeliverySpec):
    """Supply delivery read specification"""

    supplied_item_quantity: int
    supplied_item: UUID4
    origin: dict
    destination: dict
    created_date: datetime.datetime
    modified_date: datetime.datetime

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


class SupplyDeliveryRetrieveSpec(SupplyDeliveryReadSpec):
    """Supply delivery retrieve specification"""

    supply_request: dict | None = None
    created_by: UserSpec = dict
    updated_by: UserSpec = dict

    @classmethod
    def perform_extra_serialization(cls, mapping, obj):
        super().perform_extra_serialization(mapping, obj)
        if obj.supply_request:
            mapping["supply_request"] = SupplyRequestReadSpec.serialize(
                obj.supply_request
            ).to_json()
        cls.serialize_audit_users(mapping, obj)
