from django.db import transaction
from django_filters import CharFilter, FilterSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404

from care.emr.api.viewsets.base import EMRModelViewSet
from care.emr.api.viewsets.scheduling.schedule import (
    authorize_resource_schedule_create,
    authorize_resource_schedule_list,
    authorize_resource_schedule_update,
    get_or_create_resource,
    validate_resource,
)
from care.emr.models.scheduling.token import TokenSubQueue
from care.emr.resources.scheduling.token_sub_queue.spec import (
    TokenSubQueueCreateSpec,
    TokenSubQueueReadSpec,
)
from care.facility.models import Facility


class TokenSubQueueFilters(FilterSet):
    name = CharFilter(lookup_expr="icontains")


class TokenSubQueueViewSet(EMRModelViewSet):
    database_model = TokenSubQueue
    pydantic_model = TokenSubQueueCreateSpec
    pydantic_read_model = TokenSubQueueReadSpec
    filterset_class = TokenSubQueueFilters
    filter_backends = [DjangoFilterBackend]
    CREATE_QUESTIONNAIRE_RESPONSE = False

    def get_facility_obj(self):
        return get_object_or_404(
            Facility, external_id=self.kwargs["facility_external_id"]
        )

    def perform_create(self, instance):
        facility = self.get_facility_obj()
        with transaction.atomic():
            instance.facility = facility
            resource = get_or_create_resource(
                instance._resource_type,  # noqa SLF001
                instance._resource_id,  # noqa SLF001
                facility,
            )
            instance.resource = resource
            super().perform_create(instance)

    def validate_data(self, instance, model_obj=None):
        if not model_obj:
            validate_resource(
                instance.resource_type, instance.resource_id, self.get_facility_obj()
            )

    def authorize_create(self, instance):
        authorize_resource_schedule_create(
            instance.resource_type,
            instance.resource_id,
            self.get_facility_obj(),
            self.request.user,
        )

    def authorize_update(self, request_obj, model_instance):
        authorize_resource_schedule_update(
            model_instance,
            self.request.user,
        )

    def authorize_destroy(self, instance):
        self.authorize_update({}, instance)

    def clean_create_data(self, request_data):
        request_data["facility"] = self.kwargs["facility_external_id"]
        return request_data

    def authorize_retrieve(self, model_instance):
        obj = self.get_object()
        authorize_resource_schedule_list(
            obj.resource.resource_type,
            None,
            obj.resource.facility,
            self.request.user,
            obj,
        )

    def get_queryset(self):
        facility = self.get_facility_obj()
        queryset = (
            super()
            .get_queryset()
            .select_related("resource", "created_by", "updated_by")
            .order_by("-modified_date")
        )
        if self.action == "list":
            if (
                "resource_type" not in self.request.query_params
                or "resource_id" not in self.request.query_params
            ):
                raise ValidationError("resource_type and resource_id is required")
            resource = get_or_create_resource(
                self.request.query_params["resource_type"],
                self.request.query_params.get("resource_id"),
                facility,
            )
            authorize_resource_schedule_list(
                self.request.query_params["resource_type"],
                self.request.query_params.get("resource_id"),
                facility,
                self.request.user,
            )
            queryset = queryset.filter(resource=resource)
        return queryset
