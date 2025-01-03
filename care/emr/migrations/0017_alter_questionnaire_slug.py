# Generated by Django 5.1.1 on 2024-12-05 14:06

import uuid
from django.db import migrations, models


def gen_uuid(apps, schema_editor):
    Questionnaire = apps.get_model("emr", "questionnaire")
    for row in Questionnaire.objects.all():
        row.slug = str(uuid.uuid4())
        row.save()


class Migration(migrations.Migration):

    dependencies = [
        ('emr', '0016_questionnaire_slug'),
    ]

    operations = [
                migrations.RunPython(gen_uuid , reverse_code=migrations.RunPython.noop),
        migrations.AlterField(
            model_name='questionnaire',
            name='slug',
            field=models.CharField(default=uuid.uuid4, max_length=255, unique=True),
        ),
    ]
