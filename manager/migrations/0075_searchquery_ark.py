# Generated by Django 4.0.4 on 2024-10-21 04:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0074_sensitivedatarequest_principal_investigator'),
    ]

    operations = [
        migrations.AddField(
            model_name='searchquery',
            name='ark',
            field=models.CharField(blank=True, max_length=50),
        ),
    ]
