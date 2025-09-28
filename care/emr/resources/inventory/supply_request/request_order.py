from enum import Enum

from pydantic import UUID4
from rest_framework.exceptions import ValidationError

from care.emr.models.location import FacilityLocation
from care.emr.models.supply_request import RequestOrder
from care.emr.resources.base import EMRResource
from care.emr.resources.location.spec import FacilityLocationListSpec
from care.emr.resources.organization.spec import (
    Organization,
    OrganizationReadSpec,
    OrganizationTypeChoices,
)
from care.utils.shortcuts import get_object_or_404


class SupplyRequestOrderStatusOptions(str, Enum):
    draft = "draft"
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    abandoned = "abandoned"
    entered_in_error = "entered_in_error"


class SupplyRequestIntentOptions(str, Enum):
    proposal = "proposal"
    plan = "plan"
    directive = "directive"
    order = "order"
    original_order = "original_order"
    reflex_order = "reflex_order"
    filler_order = "filler_order"
    instance_order = "instance_order"


class SupplyRequestCategoryOptions(str, Enum):
    central = "central"
    nonstock = "nonstock"


class SupplyRequestPriorityOptions(str, Enum):
    routine = "routine"
    urgent = "urgent"
    asap = "asap"
    stat = "stat"


class SupplyRequestReason(str, Enum):
    patient_care = "patient_care"
    ward_stock = "ward_stock"


SUPPLY_REQUEST_ORDER_COMPLETED_STATUSES = [
    SupplyRequestOrderStatusOptions.abandoned.value,
    SupplyRequestOrderStatusOptions.entered_in_error.value,
    SupplyRequestOrderStatusOptions.completed.value,
]


class BaseSupplyRequestOrderSpec(EMRResource):
    __model__ = RequestOrder

    id: UUID4 | None = None

    status: SupplyRequestOrderStatusOptions
    name: str
    note: str | None = None

    intent: SupplyRequestIntentOptions
    category: SupplyRequestCategoryOptions
    priority: SupplyRequestPriorityOptions
    reason: SupplyRequestReason


class SupplyRequestOrderWriteSpec(BaseSupplyRequestOrderSpec):
    supplier: UUID4 | None = None
    deliver_from: UUID4 | None = None
    deliver_to: UUID4

    def perform_extra_deserialization(self, is_update, obj):
        if self.supplier:
            obj.supplier = get_object_or_404(
                Organization.objects.only("id").filter(external_id=self.supplier)
            )
            if obj.supplier.org_type != OrganizationTypeChoices.product_supplier.value:
                msg = f"Supplier organization must be of type product_supplier, got: {obj.supplier.org_type}"
                raise ValidationError(msg)

        obj.deliver_to = get_object_or_404(
            FacilityLocation.objects.only("id").filter(external_id=self.deliver_to)
        )
        if self.deliver_from:
            obj.deliver_from = get_object_or_404(
                FacilityLocation.objects.only("id").filter(
                    external_id=self.deliver_from
                )
            )


class SupplyRequestOrderReadSpec(BaseSupplyRequestOrderSpec):
    supplier: OrganizationReadSpec | None = None
    deliver_from: dict | None = None
    deliver_to: dict

    @classmethod
    def perform_extra_serialization(cls, mapping, obj):
        mapping["id"] = obj.external_id
        if obj.supplier:
            mapping["supplier"] = OrganizationReadSpec.serialize(obj.supplier).to_json()
        if obj.deliver_from:
            mapping["deliver_from"] = FacilityLocationListSpec.serialize(
                obj.deliver_from
            ).to_json()
        mapping["deliver_to"] = FacilityLocationListSpec.serialize(
            obj.deliver_to
        ).to_json()
