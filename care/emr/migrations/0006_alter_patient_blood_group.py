# Generated by Django 5.1.3 on 2025-01-10 15:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('emr', '0005_alter_availability_slot_size_in_minutes_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='patient',
            name='blood_group',
            field=models.CharField(max_length=16),
        ),
    ]
