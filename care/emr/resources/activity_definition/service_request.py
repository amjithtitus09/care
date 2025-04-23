# Defines how an ActivityDefinition is converted into a ServiceRequest


from care.emr.models.service_request import ServiceRequest
from care.emr.resources.service_request.spec import (
    ServiceRequestIntentChoices,
    ServiceRequestPriorityChoices,
    ServiceRequestStatusChoices,
)


def convert_ad_to_sr(activity_definition, encounter):
    return ServiceRequest(
        facility=activity_definition.facility,
        title=activity_definition.title,
        category=activity_definition.category,
        status=ServiceRequestStatusChoices.draft.value,
        intent=ServiceRequestIntentChoices.proposal.value,
        priority=ServiceRequestPriorityChoices.routine.value,
        do_not_perform=False,
        note=None,
        occurance=None,
        patient_instruction=None,
        code=activity_definition.code,
        body_site=activity_definition.body_site,
        locations=activity_definition.locations,
        patient=encounter.patient,
        encounter=encounter,
        healthcare_service=activity_definition.healthcare_service,
    )
