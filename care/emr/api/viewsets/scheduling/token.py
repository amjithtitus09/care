from django.db import transaction
from django_filters import BooleanFilter, CharFilter, FilterSet, UUIDFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.generics import get_object_or_404

from care.emr.api.viewsets.base import EMRModelViewSet
from care.emr.models.scheduling.token import Token, TokenQueue
from care.emr.resources.scheduling.token.spec import (
    TokenGenerateSpec,
    TokenReadSpec,
    TokenRetrieveSpec,
    TokenStatusOptions,
    TokenUpdateSpec,
)
from care.facility.models import Facility
from care.security.authorization.base import AuthorizationController
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
        _, queue = self.get_queue_obj()
        instance.queue = queue
        instance.facility = queue.facility
        if queue.facility != instance.category.facility:
            raise ValidationError("Category and Queue are not in the same facility")
        if instance.sub_queue and instance.sub_queue.facility != queue.facility:
            raise ValidationError("Sub Queue and Queue are not in the same facility")
        with Lock(f"booking:token:{queue.id}"), transaction.atomic():
            instance.number = (
                Token.objects.filter(queue=queue, category=instance.category).count()
                + 1
            )
            instance.status = TokenStatusOptions.CREATED.value
            instance.is_next = False
            super().perform_create(instance)

    def perform_update(self, instance):
        if instance.sub_queue and instance.sub_queue.facility != instance.facility:
            raise ValidationError("Sub Queue and Queue are not in the same facility")
        super().perform_update(instance)

    def perform_destroy(self, instance):
        instance.status = TokenStatusOptions.ENTERED_IN_ERROR.value
        instance.save()
        return super().perform_destroy(instance)

    def authorize_create(self, instance):
        _, queue = self.get_queue_obj()
        resource = queue.resource
        if not AuthorizationController.call(
            "can_write_token",
            resource,
            self.request.user,
        ):
            raise PermissionDenied("You do not have permission to create token queue")

    def authorize_update(self, request_obj, model_instance):
        self.authorize_create(model_instance)

    def authorize_destroy(self, instance):
        self.authorize_destroy(instance)

    def authorize_retrieve(self, model_instance):
        _, queue = self.get_queue_obj()
        resource = queue.resource
        if not AuthorizationController.call(
            "can_list_token",
            resource,
            self.request.user,
        ):
            raise PermissionDenied("You do not have permission to create token queue")

    def get_queryset(self):
        _, queue = self.get_queue_obj()
        queryset = (
            super()
            .get_queryset()
            .select_related("created_by", "updated_by")
            .order_by("-modified_date")
        )
        if self.action == "list":
            if not AuthorizationController.call(
                "can_list_token",
                queue.resource,
                self.request.user,
            ):
                raise PermissionDenied(
                    "You do not have permission to create token queue"
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
