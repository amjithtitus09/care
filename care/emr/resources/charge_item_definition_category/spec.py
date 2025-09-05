from enum import Enum

from pydantic import Field

from care.emr.models.charge_item_definition import ChargeItemDefinitionCategory
from care.emr.resources.base import EMRResource


class ChargeItemDefinitionCategoryResourceTypeOptions(str, Enum):
    appointment = "appointment"
    service_request = "service_request"
    other = "other"


class ChargeItemDefinitionCategoryBaseSpec(EMRResource):
    """Base model for ChargeItemDefinition"""

    __model__ = ChargeItemDefinitionCategory
    __exclude__ = ["parent"]

    title: str
    slug: str = Field(max_length=20)
    description: str | None = None
    resource_type: ChargeItemDefinitionCategoryResourceTypeOptions


class ChargeItemDefinitionCategoryWriteSpec(ChargeItemDefinitionCategoryBaseSpec):
    """ChargeItemDefinition Category write specification"""

    parent: str | None = None

    def perform_extra_deserialization(self, is_update, obj):
        if self.parent:
            obj.parent = ChargeItemDefinitionCategory.objects.get(slug=self.parent)


class ChargeItemDefinitionCategoryReadSpec(ChargeItemDefinitionCategoryBaseSpec):
    """ChargeItemDefinition Category write specification"""

    parent: dict

    @classmethod
    def perform_extra_serialization(cls, mapping, obj):
        mapping["parent"] = obj.get_parent_json()
