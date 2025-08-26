from django.db import transaction
from django_filters import CharFilter, DateFilter, FilterSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.generics import get_object_or_404

from care.emr.api.viewsets.base import EMRModelViewSet
from care.emr.api.viewsets.scheduling.schedule import get_or_create_resource
from care.emr.models.scheduling.token import TokenQueue
from care.emr.resources.scheduling.token_queue.spec import (
    TokenQueueCreateSpec,
    TokenQueueReadSpec,
    TokenQueueUpdateSpec,
)
from care.facility.models import Facility
from care.security.authorization.base import AuthorizationController


class TokenQueueFilters(FilterSet):
    name = CharFilter(field_name="name", lookup_expr="icontains")
    date = DateFilter(field_name="date")


class TokenQueueViewSet(EMRModelViewSet):
    database_model = TokenQueue
    pydantic_model = TokenQueueCreateSpec
    pydantic_update_model = TokenQueueUpdateSpec
    pydantic_read_model = TokenQueueReadSpec
    filterset_class = TokenQueueFilters
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
            if instance._set_is_primary:  # noqa SLF001
                TokenQueue.objects.filter(resource=resource, date=instance.date).update(
                    is_primary=False
                )
                instance.is_primary = True
            else:
                instance.is_primary = False
            super().perform_create(instance)

    def authorize_create(self, instance):
        facility = self.get_facility_obj()
        resource = get_or_create_resource(
            instance.resource_type, instance.resource_id, facility
        )
        if not AuthorizationController.call(
            "can_write_token",
            resource,
            self.request.user,
        ):
            raise PermissionDenied("You do not have permission to create token queue")

    def authorize_update(self, request_obj, model_instance):
        resource = model_instance.resource
        if not AuthorizationController.call(
            "can_write_token",
            resource,
            self.request.user,
        ):
            raise PermissionDenied("You do not have permission to create token queue")

    def authorize_destroy(self, instance):
        self.authorize_update({}, instance)

    def clean_create_data(self, request_data):
        request_data["facility"] = self.kwargs["facility_external_id"]
        return request_data

    def can_read_resource_token(self, resource_obj):
        if not AuthorizationController.call(
            "can_list_token",
            resource_obj,
            self.request.user,
        ):
            raise PermissionDenied("You do not have permission to list token queue")

    def authorize_retrieve(self, model_instance):
        resource_obj = model_instance.resource
        self.can_read_resource_token(resource_obj)

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
            self.can_read_resource_token(resource)
            queryset = queryset.filter(resource=resource)
        return queryset

    @action(detail=True, methods=["POST"])
    def set_primary(self, request, *args, **kwargs):
        obj = self.get_object()
        self.authorize_update(None, obj)
        TokenQueue.objects.filter(resource=obj.resource, date=obj.date).update(
            is_primary=False
        )
        obj.is_primary = True
        obj.save()
        return self.get_retrieve_pydantic_model().serialize(obj).to_json()
