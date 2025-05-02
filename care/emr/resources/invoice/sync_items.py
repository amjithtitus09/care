from care.emr.models.charge_item import ChargeItem
from care.emr.models.invoice import Invoice
from care.emr.resources.charge_item.spec import ChargeItemReadSpec
from care.emr.resources.common.monetory_component import (
    MonetoryComponent,
    MonetoryComponentType,
)


def update_amount(price_component, total_price_components):
    if price_component["monetory_component_type"] not in total_price_components:
        total_price_components[price_component["monetory_component_type"]] = {}
    if "code" in price_component:
        key = (
            price_component["code"].get("system", "") + price_component["code"]["code"]
        )
    else:
        key = "No-Code"
    existing_component = total_price_components[
        price_component["monetory_component_type"]
    ].get(key)
    if existing_component is None:
        existing_component = MonetoryComponent(
            monetory_component_type=price_component["monetory_component_type"],
            amount=price_component["amount"],
            code=price_component.get("code"),
        ).model_dump(mode="json")
    else:
        existing_component["amount"] += price_component["amount"]
    total_price_components[price_component["monetory_component_type"]][key] = (
        existing_component
    )


def sync_invoice_items(invoice: Invoice):
    """
    Calculate the total net, gross, price components and copy the charge items
    net amount has tax excluded
    gross amount has tax included
    """

    charge_items = ChargeItem.objects.filter(id__in=invoice.charge_items)

    costs = {}
    charge_items_copy = []
    total_price_components = {}
    net = 0
    gross = 0

    for charge_item in charge_items:
        for price_component in charge_item.total_price_components:
            costs[price_component["monetory_component_type"]] = [
                *costs.get(price_component["monetory_component_type"], []),
                price_component,
            ]
        charge_items_copy.append(ChargeItemReadSpec.serialize(charge_item).to_json())

    for price_component in costs.get(MonetoryComponentType.base.value, []):
        update_amount(price_component, total_price_components)
        net += price_component["amount"]
    total_price_components[MonetoryComponentType.surcharge.value] = {}
    for price_component in costs.get(MonetoryComponentType.surcharge.value, []):
        update_amount(price_component, total_price_components)
        net += price_component["amount"]
    for price_component in costs.get(MonetoryComponentType.discount.value, []):
        update_amount(price_component, total_price_components)
        net -= price_component["amount"]
    gross = net
    for price_component in costs.get(MonetoryComponentType.tax.value, []):
        update_amount(price_component, total_price_components)
        gross += price_component["amount"]

    final_price_components = []
    for price_component in total_price_components.values():
        final_price_components.extend(list(price_component.values()))
    invoice.total_net = net
    invoice.total_gross = gross
    invoice.total_price_components = final_price_components
    invoice.charge_items_copy = charge_items_copy
