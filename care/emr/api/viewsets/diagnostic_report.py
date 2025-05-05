from django.shortcuts import get_object_or_404
from django_filters import rest_framework as filters
from drf_spectacular.utils import extend_schema
from pydantic import UUID4, BaseModel
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from care.emr.api.viewsets.base import (
    EMRBaseViewSet,
    EMRCreateMixin,
    EMRListMixin,
    EMRRetrieveMixin,
    EMRUpdateMixin,
)
from care.emr.models.diagnostic_report import DiagnosticReport
from care.emr.models.encounter import Encounter
from care.emr.models.observation import Observation
from care.emr.models.observation_definition import ObservationDefinition
from care.emr.models.service_request import ServiceRequest
from care.emr.resources.diagnostic_report.spec import (
    DiagnosticReportCreateSpec,
    DiagnosticReportListSpec,
    DiagnosticReportRetrieveSpec,
    DiagnosticReportUpdateSpec,
)
from care.emr.resources.observation.spec import ObservationUpdateSpec
from care.emr.resources.observation_definition.observation import (
    convert_od_to_observation,
)
from care.emr.resources.questionnaire.spec import SubjectType
from care.facility.models.facility import Facility
from care.security.authorization.base import AuthorizationController


class ApplyObservationDefinitionRequest(BaseModel):
    observation_definition: UUID4
    observation: ObservationUpdateSpec


class UpsertObservationRequest(BaseModel):
    observation: ObservationUpdateSpec
    observation_id: UUID4 | None = None
    observation_definition: UUID4 | None = None


class BatchUpdateObservationRequest(BaseModel):
    observations: list[UpsertObservationRequest]


class DiagnosticReportFilters(filters.FilterSet):
    status = filters.CharFilter(lookup_expr="iexact")


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
    filterset_class = DiagnosticReportFilters
    filter_backends = [filters.DjangoFilterBackend]

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
        get_object_or_404(
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

    @extend_schema(
        request=BatchUpdateObservationRequest,
    )
    @action(detail=True, methods=["POST"])
    def upsert_observations(self, request, *args, **kwargs):
        """
        Create observation from observation definition, from scratch or update existing observation
        """
        request_params = BatchUpdateObservationRequest(**request.data)
        diagnostic_report = self.get_object()
        facility = self.get_facility_obj()
        for request_param in request_params.observations:
            if request_param.observation_definition:
                observation_definition = get_object_or_404(
                    ObservationDefinition,
                    external_id=request_param.observation_definition,
                    facility=facility,
                )
                observation_obj = convert_od_to_observation(
                    observation_definition, diagnostic_report.encounter
                )
                serializer_obj = ObservationUpdateSpec.model_validate(
                    request_param.observation.model_dump(mode="json")
                )
                model_instance = serializer_obj.de_serialize(obj=observation_obj)
                model_instance.observation_definition = observation_definition
                model_instance.created_by = self.request.user
            elif request_param.observation_id:
                # TODO : Check if there is a diagnostic report, else reject update
                observation = get_object_or_404(
                    Observation, external_id=request_param.observation_id
                )
                serializer_obj = ObservationUpdateSpec.model_validate(
                    request_param.observation.model_dump(mode="json")
                )
                model_instance = serializer_obj.de_serialize(obj=observation)
                model_instance.updated_by = self.request.user
            else:
                observation_obj = Observation()
                serializer_obj = ObservationUpdateSpec.model_validate(
                    request_param.observation.model_dump(mode="json")
                )
                model_instance = serializer_obj.de_serialize(obj=observation_obj)
                model_instance.created_by = self.request.user
            model_instance.updated_by = self.request.user
            model_instance.encounter = diagnostic_report.encounter
            model_instance.patient = diagnostic_report.patient
            model_instance.subject_id = diagnostic_report.encounter.external_id
            model_instance.diagnostic_report = diagnostic_report
            model_instance.subject_type = SubjectType.encounter.value
            model_instance.save()
        return Response({"message": "Observations updated successfully"})
