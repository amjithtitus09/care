from enum import Enum

from pydantic import UUID4

from care.emr.models import ActivityDefinition
from care.emr.resources.activity_definition.valueset import (
    ACTIVITY_DEFINITION_PROCEDURE_CODE_VALUESET,
)
from care.emr.resources.base import EMRResource
from care.emr.resources.observation.valueset import CARE_BODY_SITE_VALUESET
from care.emr.utils.valueset_coding_type import ValueSetBoundCoding


class ActivityDefinitionStatusOptions(str, Enum):
    """Status options for activity definition"""

    draft = "draft"
    active = "active"
    retired = "retired"
    unknown = "unknown"


class ActivityDefinitionKindOptions(str, Enum):
    service_request = "service_request"


class ActivityDefinitionCategoryOptions(str, Enum):
    laboratory = "laboratory"
    imaging = "imaging"
    counselling = "counselling"
    surgical_procedure = "surgical_procedure"


class BaseActivityDefinitionSpec(EMRResource):
    """Base model for activity definition"""

    __model__ = ActivityDefinition
    __exclude__ = ["facility"]

    id: str | None = None
    slug: str
    title: str
    derived_from_uri: str | None = None
    status: ActivityDefinitionStatusOptions
    description: str = ""
    usage: str = ""
    category: ActivityDefinitionCategoryOptions
    kind: ActivityDefinitionKindOptions
    code: ValueSetBoundCoding[ACTIVITY_DEFINITION_PROCEDURE_CODE_VALUESET.slug]
    body_site: ValueSetBoundCoding[CARE_BODY_SITE_VALUESET.slug] | None = None
    specimen_requirement: list[UUID4]
    observation_result_requirement: list[UUID4]
    locations: list[UUID4] = []


class ActivityDefinitionReadSpec(BaseActivityDefinitionSpec):
    """Activity definition read specification"""

    version: int | None = None

    @classmethod
    def perform_extra_serialization(cls, mapping, obj):
        mapping["id"] = obj.external_id


class ActivityDefinitionRetrieveSpec(ActivityDefinitionReadSpec):
    @classmethod
    def perform_extra_serialization(cls, mapping, obj):
        super().perform_extra_serialization(mapping, obj)
