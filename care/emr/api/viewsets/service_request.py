from django.shortcuts import get_object_or_404
from django_filters import rest_framework as filters
from rest_framework.exceptions import ValidationError

from care.emr.api.viewsets.base import (
    EMRBaseViewSet,
    EMRCreateMixin,
    EMRListMixin,
    EMRRetrieveMixin,
    EMRUpdateMixin,
)
from care.emr.models.encounter import Encounter
from care.emr.models.location import FacilityLocation
from care.emr.models.service_request import ServiceRequest
from care.emr.resources.service_request.spec import (
    BaseServiceRequestSpec,
    ServiceRequestCreateSpec,
    ServiceRequestReadSpec,
)
from care.facility.models.facility import Facility
from care.security.authorization.base import AuthorizationController


class ServiceRequestFilters(filters.FilterSet):
    status = filters.CharFilter(field_name="status", lookup_expr="iexact")


class ServiceRequestViewSet(
    EMRCreateMixin, EMRRetrieveMixin, EMRUpdateMixin, EMRListMixin, EMRBaseViewSet
):
    database_model = ServiceRequest
    pydantic_model = ServiceRequestCreateSpec
    pydantic_update_model = BaseServiceRequestSpec
    pydantic_read_model = ServiceRequestReadSpec
    filterset_class = ServiceRequestFilters
    filter_backends = [filters.DjangoFilterBackend]

    def get_facility_obj(self):
        return get_object_or_404(
            Facility, external_id=self.kwargs["facility_external_id"]
        )

    def perform_create(self, instance):
        instance.facility = self.get_facility_obj()
        return super().perform_create(instance)

    def authorize_create(self, instance):
        encounter = get_object_or_404(Encounter, external_id=instance.encounter)
        if not AuthorizationController.call(
            "can_write_service_request_in_encounter",
            self.request.user,
            encounter,
        ):
            raise ValidationError(
                "You do not have permission to create a service request for this encounter"
            )

    def authorize_update(self, request_obj, model_instance):
        if not AuthorizationController.call(
            "can_write_service_request_in_encounter",
            self.request.user,
            model_instance.encounter,
        ):
            raise ValidationError(
                "You do not have permission to create a service request for this encounter"
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
        for location in model_instance.locations:
            location_obj = get_object_or_404(FacilityLocation, id=location)
            if AuthorizationController.call(
                "can_list_location_service_request",
                self.request.user,
                location_obj,
            ):
                return
        raise ValidationError("You do not have permission to view this service request")

    def get_queryset(self):
        queryset = super().get_queryset().filter(facility=self.get_facility_obj())
        if self.action != "list":
            return queryset  # Authz is handled separately
        if self.request.user.is_superuser:
            return queryset
        if "location" in self.request.GET:
            location = get_object_or_404(
                FacilityLocation, external_id=self.request.GET["location"]
            )
            if not AuthorizationController.call(
                "can_list_location_service_request",
                self.request.user,
                location,
            ):
                raise ValidationError(
                    "You do not have permission to view service requests for this location"
                )
            return queryset.filter(location=location)
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
