from django.db import transaction
from django_filters import BooleanFilter, CharFilter, FilterSet, UUIDFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404

from care.emr.api.viewsets.base import EMRModelViewSet
from care.emr.api.viewsets.scheduling.schedule import (
    authorize_resource_schedule_create,
    authorize_resource_schedule_list,
    authorize_resource_schedule_update,
)
from care.emr.models.scheduling.token import Token, TokenQueue
from care.emr.resources.scheduling.token.spec import (
    TokenGenerateSpec,
    TokenReadSpec,
    TokenRetrieveSpec,
    TokenStatusOptions,
    TokenUpdateSpec,
)
from care.facility.models import Facility
from care.utils.lock import Lock


class TokenFilters(FilterSet):
    category = UUIDFilter(field_name="category__external_id")
    sub_queue = UUIDFilter(field_name="sub_queue__external_id")
    status = CharFilter(field_name="status", lookup_expr="iexact")
    is_next = BooleanFilter(field_name="is_next")


class TokenViewSet(EMRModelViewSet):
    database_model = Token
    pydantic_model = TokenGenerateSpec
    pydantic_update_model = TokenUpdateSpec
    pydantic_read_model = TokenReadSpec
    pydantic_retrieve_model = TokenRetrieveSpec
    filterset_class = TokenFilters
    filter_backends = [DjangoFilterBackend]
    CREATE_QUESTIONNAIRE_RESPONSE = False

    def get_facility_obj(self):
        return get_object_or_404(
            Facility, external_id=self.kwargs["facility_external_id"]
        )

    def get_queue_obj(self):
        facility = self.get_facility_obj()
        return facility, get_object_or_404(
            TokenQueue,
            external_id=self.kwargs["token_queue_external_id"],
            facility=facility,
        )

    def perform_create(self, instance):
        facility, queue = self.get_queue_obj()
        with Lock(f"booking:token:{queue.id}"), transaction.atomic():
            instance.facility = facility
            instance.queue = queue
            if queue.facility != instance.category.facility:
                raise ValidationError("Category and Queue are not in the same facility")
            if instance.sub_queue and instance.sub_queue.facility != facility:
                raise ValidationError(
                    "Sub Queue and Queue are not in the same facility"
                )
            instance.number = Token.objects.filter(queue=queue).count() + 1
            instance.status = TokenStatusOptions.CREATED.value
            instance.is_next = False
            super().perform_create(instance)

    def perform_update(self, instance):
        if instance.sub_queue and instance.sub_queue.facility != instance.facility:
            raise ValidationError("Sub Queue and Queue are not in the same facility")
        super().perform_update(instance)

    def authorize_create(self, instance):
        facility, queue = self.get_queue_obj()
        authorize_resource_schedule_create(
            queue.resource.resource_type, None, facility, self.request.user, queue
        )

    def authorize_update(self, request_obj, model_instance):
        _, queue = self.get_queue_obj()
        authorize_resource_schedule_update(
            queue,
            self.request.user,
        )

    def authorize_destroy(self, instance):
        self.authorize_update({}, instance)

    def authorize_retrieve(self, model_instance):
        _, queue = self.get_queue_obj()
        authorize_resource_schedule_list(
            queue.resource.resource_type,
            None,
            queue.resource.facility,
            self.request.user,
            queue,
        )

    def get_queryset(self):
        facility, queue = self.get_queue_obj()
        queryset = (
            super()
            .get_queryset()
            .select_related("created_by", "updated_by")
            .order_by("-modified_date")
        )
        if self.action == "list":
            authorize_resource_schedule_list(
                queue.resource.resource_type, None, facility, self.request.user, queue
            )
            queryset = queryset.filter(queue=queue)
        return queryset

    @action(detail=True, methods=["POST"])
    def set_next(self, request, *args, **kwargs):
        obj = self.get_object()
        queue = obj.queue
        self.authorize_update(None, None)
        queryset = Token.objects.filter(queue=queue)
        if obj.sub_queue:
            queryset = queryset.filter(sub_queue=obj.sub_queue)
        else:
            queryset = queryset.filter(sub_queue__isnull=True)
        queryset = queryset.update(is_next=False)
        obj.is_next = True
        obj.save()
        return self.get_retrieve_pydantic_model().serialize(obj).to_json()
