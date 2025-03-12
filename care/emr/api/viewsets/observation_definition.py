from rest_framework.exceptions import PermissionDenied

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


class ObservationViewSet(
    EMRCreateMixin, EMRRetrieveMixin, EMRUpdateMixin, EMRListMixin, EMRBaseViewSet
):
    database_model = ObservationDefinition
    pydantic_model = ObservationDefinitionCreateSpec
    pydantic_update_model = BaseObservationDefinitionSpec
    pydantic_read_model = ObservationDefinitionReadSpec

    def authorize_create(self, instance):
        if not self.request.user.is_superuser:
            raise PermissionDenied("Access Denied to Observation Definition")

    def authorize_update(self, instance):
        if not self.request.user.is_superuser:
            raise PermissionDenied("Access Denied to Observation Definition")

    def get_queryset(self):
        if self.request.user.is_superuser:
            return self.database_model.objects.all()
        return self.database_model.objects.none()
