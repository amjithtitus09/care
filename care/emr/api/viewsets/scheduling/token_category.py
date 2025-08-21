from django_filters import rest_framework as filters
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import get_object_or_404

from care.emr.api.viewsets.base import (
    EMRBaseViewSet,
    EMRCreateMixin,
    EMRListMixin,
    EMRRetrieveMixin,
    EMRUpdateMixin,
)
from care.emr.models.scheduling.token import TokenCategory
from care.emr.resources.scheduling.token_category.spec import (
    TokenCategoryCreateSpec,
    TokenCategoryReadSpec,
    TokenCategoryRetrieveSpec,
)
from care.facility.models import Facility
from care.security.authorization import AuthorizationController


class TokenCategoryFilters(filters.FilterSet):
    resource_type = filters.CharFilter(lookup_expr="iexact")
    name = filters.CharFilter(lookup_expr="icontains")
    shorthand = filters.CharFilter(lookup_expr="icontains")


class TokenCategoryViewSet(
    EMRCreateMixin, EMRRetrieveMixin, EMRUpdateMixin, EMRListMixin, EMRBaseViewSet
):
    database_model = TokenCategory
    pydantic_model = TokenCategoryCreateSpec
    pydantic_read_model = TokenCategoryReadSpec
    pydantic_retrieve_model = TokenCategoryRetrieveSpec
    filterset_class = TokenCategoryFilters
    filter_backends = [filters.DjangoFilterBackend]

    def get_facility_obj(self):
        return get_object_or_404(
            Facility, external_id=self.kwargs["facility_external_id"]
        )

    def perform_create(self, instance):
        instance.facility = self.get_facility_obj()
        super().perform_create(instance)

    def check_write_access_facility(self, facility):
        if not AuthorizationController.call(
            "can_write_facility_token_category",
            self.request.user,
            facility,
        ):
            raise PermissionDenied("Access Denied to Token Category")

    def authorize_create(self, instance):
        facility = self.get_facility_obj()
        self.check_write_access_facility(facility)

    def authorize_update(self, request_obj, model_instance):
        self.check_write_access_facility(request_obj.facility)

    def get_queryset(self):
        base_queryset = super().get_queryset()
        facility_obj = self.get_facility_obj()
        if not AuthorizationController.call(
            "can_list_facility_token_category",
            self.request.user,
            facility_obj,
        ):
            raise PermissionDenied("Access Denied to Token Category")
        return base_queryset.filter(facility=facility_obj)
