from care.emr.models.inventory_item import InventoryItem
from care.emr.models.location import FacilityLocation
from care.emr.models.product import Product
from care.emr.resources.inventory.inventory_item.spec import InventoryItemStatusOptions


def create_inventory_item(product: Product, location: FacilityLocation):
    inventory_obj = InventoryItem.objects.filter(product=product, location=location)
    if not inventory_obj.exists():
        InventoryItem(
            status=InventoryItemStatusOptions.active.value,
            product=product,
            location=location,
            net_content=0,
        ).save()
