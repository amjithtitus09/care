from pydantic import UUID4, BaseModel, Field, field_validator

from care.emr.models.observation_definition import ObservationDefinition
from care.emr.resources.base import EMRResource
from care.emr.resources.common import Coding
from care.emr.resources.facility.spec import FacilityBareMinimumSpec
from care.emr.resources.observation.valueset import (
    CARE_BODY_SITE_VALUESET,
    CARE_OBSERVATION_COLLECTION_METHOD,
)
from care.emr.resources.questionnaire.spec import QuestionType
from care.facility.models import Facility


class ObservationDefinitionComponentSpec(BaseModel):
    code: Coding
    permitted_data_type: QuestionType
    permitted_unit: Coding

    @field_validator("permitted_data_type")
    @classmethod
    def validate_unit(cls, permitted_data_type):
        if permitted_data_type == QuestionType.group.value:
            raise ValueError("Cannot create a definition of a group")
        return permitted_data_type


class BaseObservationDefinitionSpec(EMRResource):
    __model__ = ObservationDefinition
    __exclude__ = ["facility"]

    id: str
    slug: str
    name: str
    status: str
    description: str
    category: Coding | None = None
    code: Coding | None = None
    permitted_data_type: QuestionType
    component: list[ObservationDefinitionComponentSpec] = []
    body_site: Coding | None = Field(
        None,
        json_schema_extra={"slug": CARE_BODY_SITE_VALUESET.slug},
    )
    method: Coding | None = Field(
        None,
        json_schema_extra={"slug": CARE_OBSERVATION_COLLECTION_METHOD.slug},
    )
    permitted_unit: Coding
    derived_from_uri: str | None = None

    @field_validator("permitted_data_type")
    @classmethod
    def validate_unit(cls, permitted_data_type):
        if permitted_data_type == QuestionType.group.value:
            raise ValueError("Cannot create a definition of a group")
        return permitted_data_type


class ObservationDefinitionCreateSpec(BaseObservationDefinitionSpec):
    facility: UUID4 | None = None

    @field_validator("facility")
    @classmethod
    def validate_facility_exists(cls, facility):
        if not Facility.objects.filter(external_id=facility).exists():
            err = "Facility not found"
            raise ValueError(err)
        return facility

    def perform_extra_deserialization(self, is_update, obj):
        if self.facility:
            obj.facility = Facility.objects.get(external_id=self.facility)


class ObservationDefinitionReadSpec(BaseObservationDefinitionSpec):
    version: int | None = None
    facility: dict | None = None

    @classmethod
    def perform_extra_serialization(cls, mapping, obj):
        mapping["id"] = obj.external_id
        if obj.facility:
            mapping["facility"] = FacilityBareMinimumSpec.serialize(
                obj.faciltiy
            ).to_json()
