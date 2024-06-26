# Generated by Django 3.2.10 on 2023-10-27 06:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0026_rename_group_datasetkey_rights_holder'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='datasetkey',
            name='dataset_unique',
        ),
        migrations.AddConstraint(
            model_name='datasetkey',
            constraint=models.UniqueConstraint(fields=('name', 'record_type', 'rights_holder'), name='dataset_unique'),
        ),
    ]
