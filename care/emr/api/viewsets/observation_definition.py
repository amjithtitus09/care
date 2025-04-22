from django_filters import rest_framework as filters
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import get_object_or_404

from care.emr.api.viewsets.base import (
    EMRBaseViewSet,
    EMRCreateMixin,
    EMRListMixin,
    EMRRetrieveMixin,
    EMRUpdateMixin,
)
from care.emr.models.observation_definition import ObservationDefinition
from care.emr.resources.observation_definition.spec import (
    BaseObservationDefinitionSpec,
    ObservationDefinitionCreateSpec,
    ObservationDefinitionReadSpec,
)
from care.facility.models import Facility
from care.security.authorization import AuthorizationController


class ObservationDefinitionFilters(filters.FilterSet):
    facility = filters.UUIDFilter(field_name="facility__external_id")
    category = filters.CharFilter(lookup_expr="iexact")


class ObservationDefinitionViewSet(
    EMRCreateMixin, EMRRetrieveMixin, EMRUpdateMixin, EMRListMixin, EMRBaseViewSet
):
    database_model = ObservationDefinition
    pydantic_model = ObservationDefinitionCreateSpec
    pydantic_update_model = BaseObservationDefinitionSpec
    pydantic_read_model = ObservationDefinitionReadSpec
    filterset_class = ObservationDefinitionFilters
    filter_backends = [filters.DjangoFilterBackend]

    def authorize_create(self, instance):
        """
        Only superusers can create observation definitions that are not facility-specific.
        The user must have permission to create the observation definition in the facility.
        """
        if not instance.facility and not self.request.user.is_superuser:
            raise PermissionDenied("Access Denied to Observation Definition")
        if instance.facility and not AuthorizationController.call(
            "can_write_facility_observation_definition",
            self.request.user,
            instance.facility,
        ):
            raise PermissionDenied("Access Denied to Observation Definition")

    def authorize_update(self, request_obj, model_instance):
        """
        Only superusers can update observation definitions that are not facility-specific.
        The user must have permission to update the observation definition in the facility.
        """
        if not model_instance.facility and not self.request.user.is_superuser:
            raise PermissionDenied("Access Denied to Observation Definition")

        if model_instance.facility and not AuthorizationController.call(
            "can_write_facility_observation_definition",
            self.request.user,
            model_instance.facility,
        ):
            raise PermissionDenied("Access Denied to Observation Definition")

    def authorize_retrieve(self, model_instance):
        if not model_instance.facility:
            # All users can view non-facility specific observation definitions
            return
        if not AuthorizationController.call(
            "can_list_facility_observation_definition",
            self.request.user,
            model_instance.facility,
        ):
            raise PermissionDenied("Access Denied to Observation Definition")

    def get_queryset(self):
        """
        If no facility filters are applied, all objects must be returned without a facility filter.
        If facility filter is applied, check for read permission and return all inside facility.
        """
        base_queryset = self.database_model.objects.all()
        if self.action in ["list"]:
            if "facility" in self.request.GET:
                facility_id = self.request.GET["facility"]
                facility_obj = get_object_or_404(Facility, external_id=facility_id)
                if not AuthorizationController.call(
                    "can_list_facility_observation_definition",
                    self.request.user,
                    facility_obj,
                ):
                    raise PermissionDenied("Access Denied to Observation Definition")
                return base_queryset.filter(facility=facility_obj)
            base_queryset = base_queryset.filter(facility__isnull=True)
        return base_queryset
