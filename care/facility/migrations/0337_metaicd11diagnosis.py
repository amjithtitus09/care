# Generated by Django 2.2.11 on 2023-03-30 06:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('facility', '0336_auto_20230222_1602'),
    ]

    operations = [
        migrations.CreateModel(
            name='MetaICD11Diagnosis',
            fields=[
                ('id', models.CharField(max_length=255, primary_key=True, serialize=False)),
                ('_id', models.IntegerField()),
                ('average_depth', models.IntegerField()),
                ('is_adopted_child', models.BooleanField()),
                ('parent_id', models.CharField(max_length=255, null=True)),
                ('class_kind', models.CharField(max_length=255)),
                ('is_leaf', models.BooleanField()),
                ('label', models.CharField(max_length=255)),
                ('breadth_value', models.DecimalField(decimal_places=22, max_digits=24)),
            ],
            options={
                'db_table': 'meta_icd11_diagnosis',
            },
        ),
    ]