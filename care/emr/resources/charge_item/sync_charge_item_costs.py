from care.emr.resources.common.monetory_component import (
    MonetoryComponents,
    MonetoryComponentType,
)


def calculate_amount(component, quantity, base):
    if component.amount:
        component.amount = component.amount * quantity
        return component
    if component.factor:
        component.amount = base * component.factor / 100
        return component
    return None


def sync_charge_item_costs(charge_item):
    """
    Calculate total cost of charge item based on quantity and other factors
    """
    charge_item_price_components = MonetoryComponents(charge_item.unit_price_components)
    quantity = charge_item.quantity
    components = []
    total_price = 0
    base = 0
    for component in charge_item_price_components:
        if component.monetory_component_type == MonetoryComponentType.base.value:
            component.amount = component.amount * quantity
            total_price = component.amount
            base = component.amount
            components.append(component.model_dump(mode="json", exclude_defaults=True))
    for component in charge_item_price_components:
        if component.monetory_component_type == MonetoryComponentType.surcharge.value:
            _component = calculate_amount(component, quantity, base)
            total_price += _component.amount
            components.append(_component.model_dump(mode="json", exclude_defaults=True))
    net_price = total_price
    for component in charge_item_price_components:
        if component.monetory_component_type == MonetoryComponentType.discount.value:
            _component = calculate_amount(component, quantity, net_price)
            total_price -= _component.amount
            components.append(_component.model_dump(mode="json", exclude_defaults=True))
    taxable_price = total_price
    for component in charge_item_price_components:
        if component.monetory_component_type == MonetoryComponentType.tax.value:
            _component = calculate_amount(component, quantity, taxable_price)
            total_price += _component.amount
            components.append(_component.model_dump(mode="json", exclude_defaults=True))

    return total_price, components
