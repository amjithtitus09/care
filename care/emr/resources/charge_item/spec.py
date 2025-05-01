from enum import Enum

from pydantic import UUID4, BaseModel, model_validator

from care.emr.models.account import Account
from care.emr.models.charge_item import ChargeItem
from care.emr.models.encounter import Encounter
from care.emr.resources.base import EMRResource
from care.emr.resources.charge_item_definition.spec import ChargeItemDefinitionReadSpec
from care.emr.resources.common.coding import Coding
from care.emr.resources.common.monetory_component import (
    MonetoryComponent,
    MonetoryComponentType,
)


class ChargeItemStatusOptions(str, Enum):
    planned = "planned"
    billable = "billable"
    not_billable = "not_billable"
    aborted = "aborted"
    billed = "billed"
    entered_in_error = "entered_in_error"


class ChargeItemOverrideReason(BaseModel):
    text: str
    code: Coding | None = None


class ChargeItemSpec(EMRResource):
    """Base model for ChargeItem"""

    __model__ = ChargeItem
    __exclude__ = ["encounter", "account"]

    id: UUID4 | None = None
    title: str
    description: str | None = None
    status: ChargeItemStatusOptions
    code: Coding | None = None
    quantity: float
    unit_price_components: list[MonetoryComponent]
    note: str | None = None
    override_reason: ChargeItemOverrideReason | None = None

    @model_validator(mode="after")
    def check_duplicate_codes(self):
        codes = [
            component.code for component in self.unit_price_components if component.code
        ]
        if len(codes) != len(set(codes)):
            raise ValueError("Duplicate codes are not allowed.")
        return self

    @model_validator(mode="after")
    def check_single_base_component(self):
        component_types = [
            component.monetory_component_type
            for component in self.unit_price_components
        ]
        if component_types.count(MonetoryComponentType.base) > 1:
            raise ValueError("Only one base component is allowed.")
        return self

    @model_validator(mode="after")
    def validate_monetory_codes(self):
        # Validate that the codes used in the components are defined
        # in the facility or in the instance level
        # TODO
        return self


class ChargeItemWriteSpec(ChargeItemSpec):
    encounter: UUID4
    account: UUID4 | None = None

    def perform_extra_deserialization(self, is_update, obj):
        obj.encounter = Encounter.objects.get(external_id=self.encounter)
        obj.patient = obj.encounter.patient
        if self.account:
            obj.account = Account.objects.get(external_id=self.account)


class ChargeItemReadSpec(ChargeItemSpec):
    """Account read specification"""

    total_price_components: list[dict]
    total_price: float
    charge_item_definition: dict

    @classmethod
    def perform_extra_serialization(cls, mapping, obj):
        mapping["id"] = obj.external_id
        if obj.charge_item_definition:
            mapping["charge_item_definition"] = ChargeItemDefinitionReadSpec.serialize(
                obj.charge_item_definition
            ).to_json()
