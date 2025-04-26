from django_filters import rest_framework as filters
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404

from care.emr.api.viewsets.base import (
    EMRBaseViewSet,
    EMRCreateMixin,
    EMRListMixin,
    EMRRetrieveMixin,
    EMRUpdateMixin,
)
from care.emr.models.charge_item_definition import ChargeItemDefinition
from care.emr.resources.charge_item_definition.spec import (
    ChargeItemDefinitionSpec,
    ChargeItemReadSpec,
)
from care.facility.models import Facility


class ChargeItemDefinitionFilters(filters.FilterSet):
    status = filters.CharFilter(lookup_expr="iexact")
    title = filters.CharFilter(lookup_expr="icontains")


class ChargeItemDefinitionViewSet(
    EMRCreateMixin, EMRRetrieveMixin, EMRUpdateMixin, EMRListMixin, EMRBaseViewSet
):
    database_model = ChargeItemDefinition
    pydantic_model = ChargeItemDefinitionSpec
    pydantic_read_model = ChargeItemReadSpec
    filterset_class = ChargeItemDefinitionFilters
    filter_backends = [filters.DjangoFilterBackend]

    def get_facility_obj(self):
        return get_object_or_404(
            Facility, external_id=self.kwargs["facility_external_id"]
        )

    def perform_create(self, instance):
        instance.facility = self.get_facility_obj()
        if ChargeItemDefinition.objects.filter(
            slug__exact=instance.slug, facility=instance.facility
        ).exists():
            raise ValidationError(
                "Charge Item Definition with this slug already exists."
            )
        # TODO: AuthZ pending
        super().perform_create(instance)

    def get_queryset(self):
        """
        If no facility filters are applied, all objects must be returned without a facility filter.
        If facility filter is applied, check for read permission and return all inside facility.
        """
        base_queryset = self.database_model.objects.all()
        facility_obj = self.get_facility_obj()
        return base_queryset.filter(facility=facility_obj)
