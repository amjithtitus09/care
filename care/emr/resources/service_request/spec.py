import datetime
from enum import Enum

from django.shortcuts import get_object_or_404
from pydantic import UUID4

from care.emr.models.encounter import Encounter
from care.emr.models.patient import Patient
from care.emr.models.service_request import ServiceRequest
from care.emr.resources.activity_definition.spec import (
    ActivityDefinitionCategoryOptions,
)
from care.emr.resources.activity_definition.valueset import (
    ACTIVITY_DEFINITION_PROCEDURE_CODE_VALUESET,
)
from care.emr.resources.base import EMRResource
from care.emr.resources.observation.valueset import CARE_BODY_SITE_VALUESET
from care.emr.utils.valueset_coding_type import ValueSetBoundCoding


class ServiceRequestStatusChoices(str, Enum):
    """Status values for service requests"""

    draft = "draft"
    active = "active"
    on_hold = "on_hold"
    entered_in_error = "entered_in_error"
    ended = "ended"
    completed = "completed"
    revoked = "revoked"
    unknown = "unknown"


class ServiceRequestIntentChoices(str, Enum):
    """Intent values for service requests"""

    proposal = "proposal"
    plan = "plan"
    directive = "directive"
    order = "order"


class ServiceRequestPriorityChoices(str, Enum):
    """Priority values for service requests"""

    routine = "routine"
    urgent = "urgent"
    asap = "asap"
    stat = "stat"


class BaseServiceRequestSpec(EMRResource):
    """Base model for service requests"""

    __model__ = ServiceRequest
    __exclude__ = []

    id: str | None = None
    title: str
    status: ServiceRequestStatusChoices
    intent: ServiceRequestIntentChoices
    priority: ServiceRequestPriorityChoices
    category: ActivityDefinitionCategoryOptions
    do_not_perform: bool | None = None
    note: str | None = None
    locations: list[UUID4] = []
    body_site: ValueSetBoundCoding[CARE_BODY_SITE_VALUESET.slug] | None = None
    code: ValueSetBoundCoding[ACTIVITY_DEFINITION_PROCEDURE_CODE_VALUESET.slug]
    occurance: datetime.datetime
    patient_instruction: str


class ServiceRequestCreateSpec(BaseServiceRequestSpec):
    """Create specification for service requests"""

    patient: UUID4
    encounter: UUID4

    def perform_extra_deserialization(self, is_update, obj):
        obj.patient = get_object_or_404(Patient, external_id=self.patient)
        obj.encounter = get_object_or_404(Encounter, external_id=self.encounter)


class ServiceRequestReadSpec(BaseServiceRequestSpec):
    """Read specification for service requests"""

    @classmethod
    def perform_extra_serialization(cls, mapping, obj):
        mapping["id"] = obj.external_id
