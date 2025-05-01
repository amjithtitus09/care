# def calculate_invoice_amount(invoice: Invoice):
#     charge_items = ChargeItem.objects.filter(id__in=invoice.charge_items)
#     costs = {}
#     net = 0
#     gross = 0
#     for charge_item in charge_items:
#         for price_component in charge_item.total_price_component:
#             # Update each code individually
#             pass
#     return costs, net, gross
