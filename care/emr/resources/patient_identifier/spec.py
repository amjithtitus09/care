from enum import Enum

from pydantic import UUID4, BaseModel

from care.emr.models.patient import FacilityPatientIdentifierConfig
from care.emr.resources.base import EMRResource


class PatientIdentifierUse(str, Enum):
    usual = "usual"
    official = "official"
    temp = "temp"
    secondary = "secondary"
    old = "old"


class PatientIdentifierRetrieveConfig(BaseModel):
    retrieve_with_dob: bool = False
    retrieve_with_year_of_birth: bool = False
    retrieve_with_otp: bool = False
    retrieve_without_extra: bool = False


class PatientIdentifierConfig(BaseModel):
    use: PatientIdentifierUse
    description: str = ""
    system: str
    required: bool
    unique: bool
    regex: str
    display: str
    retrieve_config: PatientIdentifierRetrieveConfig = {}


class BasePatientIdentifierSpec(EMRResource):
    __model__ = FacilityPatientIdentifierConfig
    __exclude__ = []

    id: UUID4 | None = None
    config: PatientIdentifierConfig


class PatientListSpec(BasePatientIdentifierSpec):
    @classmethod
    def perform_extra_serialization(cls, mapping, obj):
        mapping["id"] = obj.external_id
