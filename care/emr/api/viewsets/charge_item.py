from django.shortcuts import get_object_or_404
from django_filters import rest_framework as filters
from rest_framework.exceptions import ValidationError

from care.emr.api.viewsets.base import (
    EMRBaseViewSet,
    EMRCreateMixin,
    EMRListMixin,
    EMRRetrieveMixin,
    EMRUpdateMixin,
    EMRUpsertMixin,
)
from care.emr.models.account import Account
from care.emr.models.charge_item import ChargeItem
from care.emr.models.encounter import Encounter
from care.emr.registries.system_questionnaire.system_questionnaire import (
    InternalQuestionnaireRegistry,
)
from care.emr.resources.account.default_account import get_default_account
from care.emr.resources.charge_item.spec import (
    ChargeItemReadSpec,
    ChargeItemSpec,
    ChargeItemWriteSpec,
)
from care.emr.resources.questionnaire.spec import SubjectType
from care.facility.models.facility import Facility


class ChargeItemDefinitionFilters(filters.FilterSet):
    status = filters.CharFilter(lookup_expr="iexact")
    title = filters.CharFilter(lookup_expr="icontains")
    account = filters.UUIDFilter(field_name="account__external_id")
    encounter = filters.UUIDFilter(field_name="encounter__external_id")


class ChargeItemViewSet(
    EMRCreateMixin,
    EMRRetrieveMixin,
    EMRUpdateMixin,
    EMRUpsertMixin,
    EMRListMixin,
    EMRBaseViewSet,
):
    database_model = ChargeItem
    pydantic_model = ChargeItemWriteSpec
    pydantic_update_model = ChargeItemSpec
    pydantic_read_model = ChargeItemReadSpec
    filterset_class = ChargeItemDefinitionFilters
    filter_backends = [filters.DjangoFilterBackend]
    questionnaire_type = "charge_item"
    questionnaire_title = "Charge Item"
    questionnaire_description = "Charge Item"
    questionnaire_subject_type = SubjectType.encounter.value

    def get_facility_obj(self):
        return get_object_or_404(
            Facility, external_id=self.kwargs["facility_external_id"]
        )

    def perform_create(self, instance):
        instance.facility = self.get_facility_obj()
        if not instance.account_id:
            instance.account = get_default_account(
                instance.patient, self.get_facility_obj()
            )
        super().perform_create(instance)

    def authorize_create(self, instance):
        facility = self.get_facility_obj()
        encounter = get_object_or_404(Encounter, external_id=instance.encounter)
        if instance.account:
            account = get_object_or_404(
                Account, external_id=instance.account, encounter=encounter
            )
            if account.facility != facility:
                raise ValidationError("Account is not associated with the facility")
        # TODO: AuthZ pending
        return super().authorize_create(instance)


InternalQuestionnaireRegistry.register(ChargeItemViewSet)
