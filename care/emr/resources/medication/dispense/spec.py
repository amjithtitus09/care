from datetime import datetime
from enum import Enum

from django.shortcuts import get_object_or_404
from pydantic import UUID4, BaseModel

from care.emr.models.encounter import Encounter
from care.emr.models.location import FacilityLocation
from care.emr.models.medication_dispense import MedicationDispense
from care.emr.models.medication_request import MedicationRequest
from care.emr.models.product import Product
from care.emr.resources.base import EMRResource
from care.emr.resources.charge_item.spec import ChargeItemReadSpec
from care.emr.resources.inventory.product.spec import ProductReadSpec
from care.emr.resources.medication.administration.spec import Dosage


class MedicationDispenseStatus(str, Enum):
    preparation = "preparation"
    in_progress = "in_progress"
    cancelled = "cancelled"
    on_hold = "on_hold"
    completed = "completed"
    entered_in_error = "entered_in_error"
    stopped = "stopped"
    declined = "declined"


class MedicationDispenseNotPerformedReason(str, Enum):
    outofstock = "outofstock"
    washout = "washout"
    surg = "surg"
    sintol = "sintol"
    sddi = "sddi"
    sdupther = "sdupther"
    saig = "saig"
    preg = "preg"


class MedicationDispenseCategory(str, Enum):
    inpatient = "inpatient"
    outpatient = "outpatient"
    community = "community"


class SubstitutionType(str, Enum):
    E = "E"
    EC = "EC"
    BC = "BC"
    G = "G"
    TE = "TE"
    TB = "TB"
    TG = "TG"
    F = "F"
    N = "N"


class SubstitutionReason(str, Enum):
    CT = "CT"
    FP = "FP"
    OS = "OS"
    RR = "RR"


class MedicationDispenseSubstitution(BaseModel):
    was_substituted: bool
    substitution_type: SubstitutionType
    reason: SubstitutionReason


class BaseMedicationDispenseSpec(EMRResource):
    __model__ = MedicationDispense
    __exclude__ = [
        "patient",
        "encounter",
        "authorizing_prescription",
        "product",
        "location",
    ]
    id: UUID4 = None

    status: MedicationDispenseStatus
    not_performed_reason: MedicationDispenseNotPerformedReason | None = None
    category: MedicationDispenseCategory | None = None
    when_prepared: datetime | None = None
    when_handed_over: datetime | None = None
    note: str | None = None
    dosage_instruction: Dosage | None = None
    substitution: MedicationDispenseSubstitution | None = None


class MedicationDispenseWriteSpec(BaseMedicationDispenseSpec):
    encounter: UUID4
    location: UUID4
    authorizing_prescription: UUID4 | None = None
    product: UUID4
    quantity: float
    days_supply: float

    def perform_extra_deserialization(self, is_update, obj):
        obj.encounter = get_object_or_404(
            Encounter.objects.filter(external_id=self.encounter).only("id")
        )
        obj.patient = obj.encounter.patient
        if self.authorizing_prescription:
            obj.authorizing_prescription = get_object_or_404(
                MedicationRequest.objects.filter(
                    external_id=self.authorizing_prescription,
                    encounter=obj.encounter,
                ).only("id")
            )
        obj.location = get_object_or_404(
            FacilityLocation.objects.filter(
                external_id=self.location, facility=obj.encounter.facility
            ).only("id")
        )
        obj.product = get_object_or_404(
            Product.objects.filter(
                external_id=self.product, facility=obj.encounter.facility
            ).only("id")
        )


class MedicationDispenseUpdateSpec(BaseMedicationDispenseSpec):
    pass


class MedicationDispenseReadSpec(BaseMedicationDispenseSpec):
    product: dict
    charge_item: dict | None = None

    @classmethod
    def perform_extra_serialization(cls, mapping, obj):
        mapping["id"] = obj.external_id
        mapping["product"] = ProductReadSpec.serialize(obj.product).to_json()
        if obj.charge_item:
            mapping["charge_item"] = ChargeItemReadSpec.serialize(
                obj.charge_item
            ).to_json()
