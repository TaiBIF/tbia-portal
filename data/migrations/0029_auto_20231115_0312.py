# Generated by Django 3.2.10 on 2023-11-15 03:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0028_auto_20231107_0910'),
    ]

    operations = [
        migrations.DeleteModel(
            name='DatasetKey',
        ),
        migrations.DeleteModel(
            name='Namecode',
        ),
        migrations.DeleteModel(
            name='Taxon',
        ),
    ]
