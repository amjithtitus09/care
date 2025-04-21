from enum import Enum

from pydantic import UUID4

from care.emr.models.specimen_definition import SpecimenDefinition
from care.emr.resources.activity_definition.valueset import (
    ACTIVITY_DEFINITION_CATEGORY_CODE_VALUESET,
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


class BaseActivityDefinitionSpec(EMRResource):
    """Base model for activity definition"""

    __model__ = SpecimenDefinition
    __exclude__ = ["facility"]

    id: str | None = None
    slug: str
    title: str
    subtitle: str = ""
    derived_from_uri: str | None = None
    status: ActivityDefinitionStatusOptions
    description: str
    purpose: str
    usage: str
    category: ValueSetBoundCoding[ACTIVITY_DEFINITION_CATEGORY_CODE_VALUESET.slug]
    kind: ActivityDefinitionKindOptions
    code: (
        ValueSetBoundCoding[ACTIVITY_DEFINITION_PROCEDURE_CODE_VALUESET.slug] | None
    ) = None
    body_site: ValueSetBoundCoding[CARE_BODY_SITE_VALUESET.slug] | None = None
    # specimen_requirement : list[UUID4]
    # observation_result_requirement : list[UUID4]



class ActivityDefinitionReadSpec(BaseActivityDefinitionSpec):
    """Activity definition read specification"""

    version: int | None = None

    @classmethod
    def perform_extra_serialization(cls, mapping, obj):
        mapping["id"] = obj.external_id
