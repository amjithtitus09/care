from django.core.exceptions import PermissionDenied
from django_filters import rest_framework as filters
from pydantic import ValidationError

from care.emr.api.viewsets.base import (
    EMRBaseViewSet,
    EMRCreateMixin,
    EMRListMixin,
    EMRRetrieveMixin,
    EMRUpdateMixin,
)
from care.emr.models.patient import PatientIdentifierConfig
from care.emr.resources.patient_identifier.spec import (
    BasePatientIdentifierSpec,
    PatientIdentifierCreateSpec,
    PatientIdentifierListSpec,
)


class PatientIdentifierConfigFilters(filters.FilterSet):
    facility = filters.UUIDFilter(field_name="facility__external_id")


class PatientIdentifierConfigViewSet(
    EMRCreateMixin, EMRRetrieveMixin, EMRUpdateMixin, EMRListMixin, EMRBaseViewSet
):
    database_model = PatientIdentifierConfig
    pydantic_model = PatientIdentifierCreateSpec
    pydantic_update_model = BasePatientIdentifierSpec
    pydantic_read_model = PatientIdentifierListSpec
    filterset_class = PatientIdentifierConfigFilters
    filter_backends = [filters.DjangoFilterBackend]

    def authorize_create(self, instance):
        if not instance.facility and not self.request.user.is_superuser:
            raise PermissionDenied(
                "You are not authorized to create a patient identifier config"
            )

    def authorize_update(self, request_obj, model_instance):
        self.authorize_create(model_instance)

    def validate_data(self, instance, model_obj=None):
        # Validate that the system is not present at the instance or the facility level
        # System can be duplicated within multiple facilties
        queryset = PatientIdentifierConfig.objects.filter(
            config__system=instance.config.system
        )
        if model_obj:
            queryset = queryset.exclude(id=model_obj.id)
        if queryset.filter(facility__isnull=True).exists():
            raise ValidationError(
                "A patient identifier config with this system already exists"
            )
        if model_obj and model_obj.facility:
            queryset = queryset.filter(facility=model_obj.facility)
        elif instance.facility:
            queryset = queryset.filter(facility__external_id=instance.facility)
        if queryset.exists():
            raise ValidationError(
                "A patient identifier config with this system already exists in this facility"
            )

    def get_queryset(self):
        if not self.request.GET.get("facility"):
            return super().get_queryset().filter(facility__isnull=True)
        # TODO Authz for facility
        return super().get_queryset()
