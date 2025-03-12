from pydantic import UUID4, BaseModel, Field, field_validator

from care.emr.models.observation_definition import ObservationDefinition
from care.emr.resources.base import EMRResource
from care.emr.resources.common import Coding
from care.emr.resources.observation.valueset import (
    CARE_BODY_SITE_VALUESET,
    CARE_OBSERVATION_COLLECTION_METHOD,
)
from care.emr.resources.questionnaire.spec import QuestionType


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
    title: str
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

    @field_validator("permitted_data_type")
    @classmethod
    def validate_unit(cls, permitted_data_type):
        if permitted_data_type == QuestionType.group.value:
            raise ValueError("Cannot create a definition of a group")
        return permitted_data_type


class ObservationDefinitionCreateSpec(BaseObservationDefinitionSpec):
    facility: UUID4 | None = None
    derivedFromUri: str


class ObservationDefinitionReadSpec(BaseObservationDefinitionSpec):
    version: int | None = None
