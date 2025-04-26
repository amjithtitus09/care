from enum import Enum

from pydantic import UUID4

from care.emr.models.charge_item_definition import ChargeItemDefinition
from care.emr.resources.base import EMRResource
from care.emr.resources.common.monetory_component import MonetoryComponent


class ChargeItemDefinitionStatusOptions(str, Enum):
    draft = "draft"
    active = "active"
    retired = "retired"


class ChargeItemDefinitionSpec(EMRResource):
    """Base model for ChargeItemDefinition"""

    __model__ = ChargeItemDefinition
    __exclude__ = []

    id: UUID4 | None = None
    status: ChargeItemDefinitionStatusOptions
    title: str
    slug: str
    derived_from_uri: str | None = None
    description: str | None = None
    purpose: str | None = None
    price_component: list[MonetoryComponent]


class ChargeItemReadSpec(ChargeItemDefinitionSpec):
    """Account read specification"""

    version: int | None = None

    @classmethod
    def perform_extra_serialization(cls, mapping, obj):
        mapping["id"] = obj.external_id
