# Generated by Django 4.0.4 on 2024-11-08 08:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0078_remove_taxonstat_year_month_taxonstat_month_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='taxonstat',
            name='count',
            field=models.FloatField(blank=True, null=True),
        ),
    ]