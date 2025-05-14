from enum import Enum

from pydantic import UUID4

from care.emr.resources.base import EMRResource
from care.emr.resources.inventory.product.spec import ProductReadSpec
from care.emr.resources.location.spec import FacilityLocationListSpec
from care.facility.models.facility import InventoryItem


class InventoryItemStatusOptions(str, Enum):
    active = "active"
    inactive = "inactive"
    entered_in_error = "entered_in_error"


class BaseInventoryItemSpec(EMRResource):
    """Base model for inventory item"""

    __model__ = InventoryItem
    __exclude__ = []

    id: UUID4 | None = None

    status: InventoryItemStatusOptions


class InventoryItemWriteSpec(BaseInventoryItemSpec):
    """Inventory item write specification"""


class InventoryItemReadSpec(BaseInventoryItemSpec):
    """Supply delivery read specification"""

    net_content: float
    product: float

    @classmethod
    def perform_extra_serialization(cls, mapping, obj):
        mapping["id"] = obj.external_id
        mapping["product"] = ProductReadSpec.serialize(obj.product).to_json()


class InventoryItemRetrieveSpec(InventoryItemReadSpec):
    """Inventory item retrieve specification"""

    location: dict

    @classmethod
    def perform_extra_serialization(cls, mapping, obj):
        super().perform_extra_serialization(mapping, obj)
        mapping["location"] = FacilityLocationListSpec.serialize(obj.location).to_json()
