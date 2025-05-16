from django.db import transaction
from django_filters import rest_framework as filters

from care.emr.api.viewsets.base import (
    EMRBaseViewSet,
    EMRCreateMixin,
    EMRListMixin,
    EMRRetrieveMixin,
    EMRUpdateMixin,
)
from care.emr.models.medication_dispense import MedicationDispense
from care.emr.resources.charge_item.apply_charge_item_definition import (
    apply_charge_item_definition,
)
from care.emr.resources.medication.dispense.spec import (
    MedicationDispenseReadSpec,
    MedicationDispenseUpdateSpec,
    MedicationDispenseWriteSpec,
)


class MedicationDispenseFilters(filters.FilterSet):
    status = filters.CharFilter(lookup_expr="iexact")
    category = filters.CharFilter(lookup_expr="iexact")
    encounter = filters.UUIDFilter(field_name="encounter__external_id")
    patient = filters.UUIDFilter(field_name="patient__external_id")
    location = filters.UUIDFilter(field_name="location__external_id")
    item = filters.UUIDFilter(field_name="item__external_id")


class MedicationDispenseViewSet(
    EMRCreateMixin, EMRRetrieveMixin, EMRUpdateMixin, EMRListMixin, EMRBaseViewSet
):
    database_model = MedicationDispense
    pydantic_model = MedicationDispenseWriteSpec
    pydantic_update_model = MedicationDispenseUpdateSpec
    pydantic_read_model = MedicationDispenseReadSpec
    filterset_class = MedicationDispenseFilters
    filter_backends = [filters.DjangoFilterBackend]

    def perform_create(self, instance):
        with transaction.atomic():
            if instance.item.product.charge_item_definition:
                charge_item = apply_charge_item_definition(
                    instance.item.product.charge_item_definition,
                    instance.encounter,
                    quantity=instance.quantity,
                )
                charge_item.save()
                instance.charge_item = charge_item
            super().perform_create(instance)
