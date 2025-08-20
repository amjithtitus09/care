from django.db import transaction
from django.utils import timezone
from django_filters import DateTimeFilter, FilterSet, UUIDFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.generics import get_object_or_404

from care.emr.api.viewsets.base import (
    EMRBaseViewSet,
    EMRCreateMixin,
    EMRDestroyMixin,
    EMRModelViewSet,
)
from care.emr.models.organization import FacilityOrganizationUser
from care.emr.models.scheduling.booking import TokenSlot
from care.emr.models.scheduling.schedule import (
    Availability,
    SchedulableResource,
    Schedule,
)
from care.emr.resources.scheduling.schedule.spec import (
    AvailabilityCreateSpec,
    AvailabilityForScheduleSpec,
    SchedulableResourceTypeOptions,
    ScheduleCreateSpec,
    ScheduleReadSpec,
    ScheduleUpdateSpec,
)
from care.facility.models import Facility
from care.security.authorization import AuthorizationController
from care.users.models import User
from care.utils.lock import Lock


class ScheduleFilters(FilterSet):
    user = UUIDFilter(field_name="resource__user__external_id")
    valid_from = DateTimeFilter(field_name="valid_to", lookup_expr="gte")
    valid_to = DateTimeFilter(field_name="valid_from", lookup_expr="lte")


def validate_resource(
    resource_type: SchedulableResourceTypeOptions, resource_id, facility: Facility
):
    """
    Validate a schedulable resource based on the resource type
    """

    if resource_type == SchedulableResourceTypeOptions.practitioner.value:
        schedule_user = get_object_or_404(
            User.objects.only("id"), external_id=resource_id
        )
        if not FacilityOrganizationUser.objects.filter(
            user=schedule_user, organization__facility=facility
        ).exists():
            raise ValidationError("Schedule User is not part of the facility")
    else:
        raise ValidationError("Invalid Resource Type")


def get_or_create_resource(
    resource_type: SchedulableResourceTypeOptions, resource_id, facility: Facility
):
    if resource_type == SchedulableResourceTypeOptions.practitioner.value:
        schedule_user = get_object_or_404(
            User.objects.only("id"), external_id=resource_id
        )
        resource, _ = SchedulableResource.objects.get_or_create(
            facility=facility,
            user=schedule_user,
        )
        return resource
    raise ValidationError("Invalid Resource Type")


def authorize_resource_schedule_create(
    resource_type: SchedulableResourceTypeOptions,
    resource_id,
    facility: Facility,
    user,
    schedule_obj=None,
):
    if resource_type == SchedulableResourceTypeOptions.practitioner.value:
        if schedule_obj:
            schedule_user = schedule_obj.resource.user
        else:
            schedule_user = get_object_or_404(
                User.objects.only("id"), external_id=resource_id
            )
        if not AuthorizationController.call(
            "can_write_user_schedule", user, facility, schedule_user
        ):
            raise PermissionDenied("You do not have permission to create schedule")
    else:
        raise ValidationError("Invalid Resource Type")


def authorize_resource_schedule_update(schedule: Schedule, user):
    if (
        schedule.resource.resource_type
        == SchedulableResourceTypeOptions.practitioner.value
    ):
        if not AuthorizationController.call(
            "can_write_user_schedule",
            user,
            schedule.resource.facility,
            schedule.resource.user,
        ):
            raise PermissionDenied("You do not have permission to view user schedule")
    else:
        raise ValidationError("Invalid Resource Type")


def authorize_resource_schedule_list(
    resource_type: SchedulableResourceTypeOptions,
    resource_id,
    facility: Facility,
    user,
    schedule_obj=None,
):
    if resource_type == SchedulableResourceTypeOptions.practitioner.value:
        # TODO : Authorize based on the orgs that the user is part of
        if not AuthorizationController.call("can_list_user_schedule", user, facility):
            raise PermissionDenied("You do not have permission to view user schedule")
    else:
        raise ValidationError("Invalid Resource Type")


class ScheduleViewSet(EMRModelViewSet):
    database_model = Schedule
    pydantic_model = ScheduleCreateSpec
    pydantic_update_model = ScheduleUpdateSpec
    pydantic_read_model = ScheduleReadSpec
    filterset_class = ScheduleFilters
    filter_backends = [DjangoFilterBackend]
    CREATE_QUESTIONNAIRE_RESPONSE = False

    def get_facility_obj(self):
        return get_object_or_404(
            Facility, external_id=self.kwargs["facility_external_id"]
        )

    def perform_create(self, instance):
        with transaction.atomic():
            resource = get_or_create_resource(
                instance._resource_type,  # noqa SLF001
                instance._resource_id,  # noqa SLF001
                self.get_facility_obj(),
            )
            instance.resource = resource
            super().perform_create(instance)
            for availability in instance.availabilities:
                availability_obj = availability.de_serialize()
                availability_obj.schedule = instance
                availability_obj.save()

    def perform_update(self, instance):
        with Lock(f"booking:resource:{instance.resource.id}"):
            super().perform_update(instance)

    def perform_destroy(self, instance):
        with Lock(f"booking:resource:{instance.resource.id}"), transaction.atomic():
            # Check if there are any tokens allocated for this schedule in the future
            availabilities = instance.availability_set.all()
            availability_ids = list(availabilities.values_list("id"))
            has_future_bookings = TokenSlot.objects.filter(
                resource=instance.resource,
                availability_id__in=availability_ids,
                start_datetime__gt=timezone.now(),
                allocated__gt=0,
            ).exists()
            if has_future_bookings:
                raise ValidationError(
                    "Cannot delete schedule as there are future bookings associated with it"
                )
            availabilities.update(deleted=True)
            slots = TokenSlot.objects.filter(
                resource=instance.resource, availability_id__in=availability_ids
            )
            slots.update(deleted=True)
            super().perform_destroy(instance)

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
        if self.action == "list":
            if "resource_type" not in self.request.query_params:
                raise ValidationError("resource_type is required")
            authorize_resource_schedule_list(
                self.request.query_params["resource_type"],
                self.request.query_params.get("resource_id"),
                facility,
                self.request.user,
            )
        return (
            super()
            .get_queryset()
            .filter(resource__facility=facility)
            .select_related("resource", "created_by", "updated_by")
            .order_by("-modified_date")
        )


class AvailabilityViewSet(EMRCreateMixin, EMRDestroyMixin, EMRBaseViewSet):
    database_model = Availability
    pydantic_model = AvailabilityCreateSpec
    pydantic_retrieve_model = AvailabilityForScheduleSpec

    def get_facility_obj(self):
        return get_object_or_404(
            Facility, external_id=self.kwargs["facility_external_id"]
        )

    def get_schedule_obj(self):
        return get_object_or_404(
            Schedule, external_id=self.kwargs["schedule_external_id"]
        )

    def get_queryset(self):
        schedule_obj = self.get_schedule_obj()
        authorize_resource_schedule_list(
            schedule_obj.resource.resource_type,
            None,
            schedule_obj.resource.facility,
            self.request.user,
            schedule_obj,
        )
        return (
            super()
            .get_queryset()
            .filter(schedule=schedule_obj)
            .select_related(
                "schedule",
                "schedule__resource",
                "created_by",
                "updated_by",
            )
            .order_by("-modified_date")
        )

    def clean_create_data(self, request_data):
        request_data["schedule"] = self.kwargs["schedule_external_id"]
        return request_data

    def perform_create(self, instance):
        schedule = self.get_schedule_obj()
        instance.schedule = schedule
        super().perform_create(instance)

    def perform_destroy(self, instance):
        with Lock(f"booking:resource:{instance.schedule.resource.id}"):
            has_future_bookings = TokenSlot.objects.filter(
                availability_id=instance.id,
                start_datetime__gt=timezone.now(),
                allocated__gt=0,
            ).exists()
            if has_future_bookings:
                raise ValidationError(
                    "Cannot delete availability as there are future bookings associated with it"
                )
            TokenSlot.objects.filter(availability_id=instance.id).update(deleted=True)
            super().perform_destroy(instance)

    def authorize_create(self, instance):
        schedule_obj = self.get_schedule_obj()
        authorize_resource_schedule_create(
            schedule_obj.resource.resource_type,
            None,
            schedule_obj.resource.facility,
            self.request.user,
            schedule_obj,
        )

    def authorize_destroy(self, instance):
        self.authorize_create(None)
