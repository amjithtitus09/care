from django.core.management.base import BaseCommand

from odoo.resource.field_manager import OdooFieldManagerResource


class Command(BaseCommand):
    help = "Add x_care_id field to specified Odoo models"

    def handle(self, *args, **options):
        field_manager = OdooFieldManagerResource()

        # List of models that need the x_care_id field
        models = [
            "res.partner",
            "account.move",
            "product.template",
            "account.tax",
            # Add more models as needed
        ]

        self.stdout.write(self.style.SUCCESS("Starting to add x_care_id fields..."))

        results = field_manager.create_care_id_fields(models)

        # Report results
        for model, success in results.items():
            if success:
                self.stdout.write(
                    self.style.SUCCESS(f"Successfully added x_care_id to {model}")
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f"Failed to add x_care_id to {model}")
                )

        self.stdout.write(self.style.SUCCESS("Completed adding x_care_id fields"))
