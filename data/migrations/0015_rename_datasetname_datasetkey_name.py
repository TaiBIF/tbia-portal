# Generated by Django 3.2.10 on 2023-01-13 08:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0014_datasetkey'),
    ]

    operations = [
        migrations.RenameField(
            model_name='datasetkey',
            old_name='datasetName',
            new_name='name',
        ),
    ]