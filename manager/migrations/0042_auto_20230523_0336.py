# Generated by Django 3.2.10 on 2023-05-23 03:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0041_partner_select_title'),
    ]

    operations = [
        migrations.AlterField(
            model_name='matchlog',
            name='group',
            field=models.CharField(blank=True, db_index=True, max_length=50),
        ),
        migrations.AlterField(
            model_name='matchlog',
            name='occurrenceID',
            field=models.CharField(blank=True, db_index=True, max_length=1000),
        ),
        migrations.AlterField(
            model_name='matchlog',
            name='tbiaID',
            field=models.CharField(blank=True, db_index=True, max_length=50),
        ),
    ]
