# Generated by Django 4.0.4 on 2024-10-21 07:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0075_searchquery_ark'),
    ]

    operations = [
        migrations.AlterField(
            model_name='searchquery',
            name='ark',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
