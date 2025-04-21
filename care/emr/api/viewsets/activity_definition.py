from django_filters import rest_framework as filters
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.generics import get_object_or_404

from care.emr.api.viewsets.base import (
    EMRBaseViewSet,
    EMRCreateMixin,
    EMRListMixin,
    EMRRetrieveMixin,
    EMRUpdateMixin,
)
from care.emr.models import ActivityDefinition
from care.emr.resources.activity_definition.spec import (
    ActivityDefinitionReadSpec,
    BaseActivityDefinitionSpec,
)
from care.facility.models import Facility
from care.security.authorization import AuthorizationController


class ActivityDefinitionFilters(filters.FilterSet):
    status = filters.CharFilter(field_name="status", lookup_expr="iexact")


class ActivityDefinitionViewSet(
    EMRCreateMixin, EMRRetrieveMixin, EMRUpdateMixin, EMRListMixin, EMRBaseViewSet
):
    database_model = ActivityDefinition
    pydantic_model = BaseActivityDefinitionSpec
    pydantic_read_model = ActivityDefinitionReadSpec
    filterset_class = ActivityDefinitionFilters
    filter_backends = [filters.DjangoFilterBackend]

    def get_facility_obj(self):
        return get_object_or_404(
            Facility, external_id=self.kwargs["facility_external_id"]
        )

    def perform_create(self, instance):
        instance.facility = self.get_facility_obj()
        if ActivityDefinition.objects.filter(
            slug__exact=instance.slug, facility=instance.facility
        ).exists():
            raise ValidationError("Activity Definition with this slug already exists.")
        super().perform_create(instance)

    def authorize_create(self, instance):
        """
        The user must have permission to create activity definition in the facility.
        """
        facility = self.get_facility_obj()
        if not AuthorizationController.call(
            "can_write_facility_activity_definition",
            self.request.user,
            facility,
        ):
            raise PermissionDenied("Access Denied to Activity Definition")

    def authorize_update(self, request_obj, model_instance):
        self.authorize_create(model_instance)

    def get_queryset(self):
        """
        If no facility filters are applied, all objects must be returned without a facility filter.
        If facility filter is applied, check for read permission and return all inside facility.
        """
        base_queryset = self.database_model.objects.all()
        facility_obj = self.get_facility_obj()
        if not AuthorizationController.call(
            "can_list_facility_activity_definition",
            self.request.user,
            facility_obj,
        ):
            raise PermissionDenied("Access Denied to Activity Definition")
        return base_queryset.filter(facility=facility_obj)
