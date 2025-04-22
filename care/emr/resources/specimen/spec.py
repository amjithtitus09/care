import datetime
from enum import Enum

from pydantic import UUID4, BaseModel, field_validator

from care.emr.models.specimen import Specimen
from care.emr.resources.base import EMRResource
from care.emr.resources.common import Coding
from care.emr.resources.observation.valueset import CARE_BODY_SITE_VALUESET
from care.emr.resources.specimen.valueset import (
    COLLECTION_METHOD_VALUESET,
    FASTING_STATUS_VALUESET,
    SPECIMEN_CONDITION_VALUESET,
)
from care.emr.resources.specimen_definition.valueset import SPECIMEN_TYPE_CODE_VALUESET
from care.emr.utils.valueset_coding_type import ValueSetBoundCoding
from care.facility.models import Facility
from care.users.models import User


class SpecimenStatusOptions(str, Enum):
    """Status options for specimen"""

    available = "available"
    unavailable = "unavailable"
    unsatisfactory = "unsatisfactory"
    entered_in_error = "entered_in_error"


class QuantitySpec(BaseModel):
    """Represents a quantity with value and unit"""

    value: float
    unit: Coding


class DurationSpec(BaseModel):
    """Duration specification using value and unit"""

    # Needs to be moved into the common specs, with datetime based valueset check
    value: int
    unit: Coding


class CollectionSpec(BaseModel):
    """Specimen collection details"""

    collector: UUID4 | None = None
    collected_date_time: datetime.datetime | None = None  # Check for TZ
    quantity: QuantitySpec | None = None
    method: ValueSetBoundCoding[COLLECTION_METHOD_VALUESET.slug] | None = None
    procedure: UUID4 | None = None
    body_site: ValueSetBoundCoding[CARE_BODY_SITE_VALUESET.slug] | None = None
    fasting_status_codeable_concept: (
        ValueSetBoundCoding[FASTING_STATUS_VALUESET.slug] | None
    ) = None
    fasting_status_duration: DurationSpec | None = None

    @field_validator("collector")
    @classmethod
    def validate_collector(cls, collector):
        if collector and not User.objects.filter(external_id=collector).exists():
            raise ValueError("Collector user not found")
        return collector


class ProcessingSpec(BaseModel):
    """Specimen processing details"""

    description: str
    method: Coding | None = None
    performer: UUID4 | None = None
    time_date_time: str

    @field_validator("performer")
    @classmethod
    def validate_performer(cls, performer):
        if performer and not User.objects.filter(external_id=performer).exists():
            raise ValueError("Performer user not found")
        return performer


class BaseSpecimenSpec(EMRResource):
    """Base model for specimen"""

    __model__ = Specimen
    __exclude__ = ["facility", "subject", "request", "collection", "processing"]

    id: UUID4 | None = None
    accession_identifier: list[str] = []
    status: SpecimenStatusOptions
    specimen_type: ValueSetBoundCoding[SPECIMEN_TYPE_CODE_VALUESET.slug]
    subject: dict | None = None
    received_time: str | None = None
    request: dict | None = None
    collection: CollectionSpec
    processing: list[ProcessingSpec] = []
    condition: list[ValueSetBoundCoding[SPECIMEN_CONDITION_VALUESET.slug]] = []
    note: str | None = None


class SpecimenCreateSpec(BaseSpecimenSpec):
    """Specimen creation specification"""

    facility: UUID4 | None = None
    subject_patient: UUID4
    subject_encounter: UUID4 | None = None
    request: UUID4 | None = None
    collection: CollectionSpec
    processing: list[ProcessingSpec] = []

    @field_validator("facility")
    @classmethod
    def validate_facility_exists(cls, facility):
        if not Facility.objects.filter(external_id=facility).exists():
            # Check if user is in the given facility
            raise ValueError("Facility not found")
        return facility

    def perform_extra_deserialization(self, is_update, obj):
        if self.facility:
            obj.facility = Facility.objects.get(external_id=self.facility)


class SpecimenReadSpec(BaseSpecimenSpec):
    """Specimen read specification"""

    @classmethod
    def perform_extra_serialization(cls, mapping, obj):
        mapping["id"] = obj.external_id
