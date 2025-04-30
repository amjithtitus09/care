from django.db import transaction
from django.shortcuts import get_object_or_404
from django_filters import rest_framework as filters
from drf_spectacular.utils import extend_schema
from pydantic import UUID4, BaseModel
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from care.emr.api.viewsets.base import (
    EMRBaseViewSet,
    EMRCreateMixin,
    EMRListMixin,
    EMRRetrieveMixin,
    EMRUpdateMixin,
)
from care.emr.models.account import Account
from care.emr.models.charge_item import ChargeItem
from care.emr.models.invoice import Invoice
from care.emr.resources.charge_item.spec import ChargeItemStatusOptions
from care.emr.resources.invoice.spec import (
    INVOICE_CANCELLED_STATUS,
    BaseInvoiceSpec,
    InvoiceReadSpec,
    InvoiceRetrieveSpec,
    InvoiceStatusOptions,
    InvoiceWriteSpec,
)
from care.facility.models.facility import Facility


class InvoiceFilters(filters.FilterSet):
    status = filters.CharFilter(lookup_expr="iexact")
    title = filters.CharFilter(lookup_expr="icontains")
    account = filters.UUIDFilter(field_name="account__external_id")
    encounter = filters.UUIDFilter(field_name="encounter__external_id")


class AttachChargeItemToInvoiceRequest(BaseModel):
    charge_items: list[UUID4]


class RemoveChargeItemFromInvoiceRequest(BaseModel):
    charge_item: UUID4


class InvoiceViewSet(
    EMRCreateMixin,
    EMRRetrieveMixin,
    EMRUpdateMixin,
    EMRListMixin,
    EMRBaseViewSet,
):
    database_model = Invoice
    pydantic_model = InvoiceWriteSpec
    pydantic_update_model = BaseInvoiceSpec
    pydantic_read_model = InvoiceReadSpec
    pydantic_retrieve_model = InvoiceRetrieveSpec
    filterset_class = InvoiceFilters
    filter_backends = [filters.DjangoFilterBackend]

    def get_facility_obj(self):
        return get_object_or_404(
            Facility, external_id=self.kwargs["facility_external_id"]
        )

    def perform_create(self, instance):
        instance.facility = self.get_facility_obj()
        instance.charge_items = list(
            ChargeItem.objects.filter(
                account=instance.account,
                status=ChargeItemStatusOptions.billable.value,
                external_id__in=instance.charge_items,
            ).values_list("id", flat=True)
        )
        super().perform_create(instance)

    def authorize_create(self, instance):
        facility = self.get_facility_obj()
        account = get_object_or_404(Account, external_id=instance.account)
        if account.facility != facility:
            raise ValidationError("Account is not associated with the facility")
        # TODO: AuthZ pending
        return super().authorize_create(instance)

    def perform_update(self, instance):
        old_invoice = Invoice.objects.get(id=instance.id)
        if old_invoice.status != instance.status:
            if (
                old_invoice.status in INVOICE_CANCELLED_STATUS
                and instance.status not in INVOICE_CANCELLED_STATUS
            ):
                raise ValidationError("Invoice is already cancelled")
            if old_invoice.status == InvoiceStatusOptions.balanced.value:
                raise ValidationError("Invoice is already balanced")
            if (
                old_invoice.status == InvoiceStatusOptions.issued.value
                and instance.status == InvoiceStatusOptions.draft.value
            ):
                raise ValidationError("Invoice is already issued")
            if (
                old_invoice.status not in INVOICE_CANCELLED_STATUS
                and instance.status in INVOICE_CANCELLED_STATUS
            ):
                # TODO : Lock Account
                ChargeItem.objects.filter(
                    account=instance.account,
                    status=ChargeItemStatusOptions.billed.value,
                    id__in=instance.charge_items,
                ).update(status=ChargeItemStatusOptions.billable.value)
        return super().perform_update(instance)

    def check_invoice_in_draft(self, instance):
        if instance.status == InvoiceStatusOptions.draft.value:
            return True
        raise ValidationError("Invoice is not in draft")

    @extend_schema(
        request=AttachChargeItemToInvoiceRequest,
    )
    @action(methods=["POST"], detail=False)
    def attach_items_to_invoice(self, request, *args, **kwargs):
        # TODO : Add Account Lock
        invoice = self.get_object()
        self.check_invoice_in_draft(invoice)
        request_params = AttachChargeItemToInvoiceRequest(**request.data)
        with transaction.atomic():
            charge_items = ChargeItem.objects.filter(
                external_id__in=request_params.charge_items,
                account=invoice.account,
                status=ChargeItemStatusOptions.billable.value,
            )
            invoice.charge_items = list(charge_items.values_list("id", flat=True))
            invoice.save()
            charge_items.update(status=ChargeItemStatusOptions.billed.value)
        return Response(InvoiceRetrieveSpec.serialize(invoice).to_json())

    @extend_schema(
        request=RemoveChargeItemFromInvoiceRequest,
    )
    @action(methods=["POST"], detail=True)
    def remove_item_from_invoice(self, request, *args, **kwargs):
        # TODO : Add Account Lock
        invoice = self.get_object()
        self.check_invoice_in_draft(invoice)
        request_params = RemoveChargeItemFromInvoiceRequest(**request.data)
        charge_item = get_object_or_404(
            ChargeItem, external_id=request_params.charge_item, account=invoice.account
        )
        try:
            with transaction.atomic():
                invoice.charge_items.remove(charge_item.id)
                invoice.save()
                charge_item.status = ChargeItemStatusOptions.billable.value
                charge_item.save()
        except ValueError as e:
            raise ValidationError("Charge item not found in invoice") from e

        return Response(InvoiceRetrieveSpec.serialize(invoice).to_json())

    @action(methods=["POST"], detail=False)
    def attach_account_to_invoice(self, request, *args, **kwargs):
        # TODO : Add Account Lock
        invoice = self.get_object()
        self.check_invoice_in_draft(invoice)
        with transaction.atomic():
            charge_items = ChargeItem.objects.filter(
                account=invoice.account, status=ChargeItemStatusOptions.billable.value
            )
            invoice.charge_items = charge_items.values_list("id", flat=True)
            invoice.save()
            charge_items.update(status=ChargeItemStatusOptions.billed.value)
        return Response(InvoiceRetrieveSpec.serialize(invoice).to_json())
