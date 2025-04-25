from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError

from care.emr.api.viewsets.base import (
    EMRBaseViewSet,
    EMRCreateMixin,
    EMRListMixin,
    EMRRetrieveMixin,
    EMRUpdateMixin,
)
from care.emr.models.diagnostic_report import DiagnosticReport
from care.emr.models.encounter import Encounter
from care.emr.models.service_request import ServiceRequest
from care.emr.resources.diagnostic_report.spec import (
    DiagnosticReportCreateSpec,
    DiagnosticReportListSpec,
    DiagnosticReportRetrieveSpec,
    DiagnosticReportUpdateSpec,
)
from care.facility.models.facility import Facility
from care.security.authorization.base import AuthorizationController


class DiagnosticReportViewSet(
    EMRCreateMixin,
    EMRRetrieveMixin,
    EMRUpdateMixin,
    EMRListMixin,
    EMRBaseViewSet,
):
    database_model = DiagnosticReport
    pydantic_model = DiagnosticReportCreateSpec
    pydantic_update_model = DiagnosticReportUpdateSpec
    pydantic_read_model = DiagnosticReportListSpec
    pydantic_retrieve_model = DiagnosticReportRetrieveSpec

    def get_facility_obj(self):
        return get_object_or_404(
            Facility, external_id=self.kwargs["facility_external_id"]
        )

    def perform_create(self, instance):
        instance.facility = self.get_facility_obj()
        instance.patient = instance.service_request.patient
        instance.encounter = instance.service_request.encounter
        if (
            instance.encounter.facility != instance.facility
            or instance.service_request.facility != instance.facility
        ):
            raise ValidationError(
                "Diagnostic report facility must be the same as the encounter and service request facility"
            )
        return super().perform_create(instance)

    def authorize_create(self, instance):
        # TODO : AuthZ Pending
        service_request = get_object_or_404(
            ServiceRequest,
            external_id=instance.service_request,
            facility=self.get_facility_obj(),
        )

    def authorize_retrieve(self, model_instance):
        """
        The user must have access to the location or encounter to access the SR
        """
        encounter = model_instance.encounter
        if AuthorizationController.call(
            "can_view_service_request_for_encounter",
            self.request.user,
            encounter,
        ):
            return
        return
        # TODO : AuthZ Pending

    def get_queryset(self):
        queryset = super().get_queryset().filter(facility=self.get_facility_obj())
        if self.action != "list":
            return queryset  # Authz is handled separately
        if self.request.user.is_superuser:
            return queryset
        if "service_request" in self.request.GET:
            service_request = get_object_or_404(
                ServiceRequest, external_id=self.request.GET["service_request"]
            )
            # TODO : AuthZ Pending
            return queryset.filter(service_request=service_request)
        if "encounter" in self.request.GET:
            encounter = get_object_or_404(
                Encounter, external_id=self.request.GET["encounter"]
            )
            if not AuthorizationController.call(
                "can_view_service_request_for_encounter",
                self.request.user,
                encounter,
            ):
                raise ValidationError(
                    "You do not have permission to view service requests for this encounter"
                )
            return queryset.filter(encounter=encounter)
        raise ValidationError("Location or encounter is required")

    def create_observation_from_definition(self, definition: dict):
        pass

    def create_observation(self, definition: dict):
        pass

    def update_observation(self, definition: dict):
        pass
