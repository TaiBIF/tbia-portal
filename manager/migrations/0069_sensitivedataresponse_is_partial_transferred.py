# Generated by Django 4.0.4 on 2024-05-24 08:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0068_rename_is_agreeed_report_sensitivedatarequest_is_agreed_report'),
    ]

    operations = [
        migrations.AddField(
            model_name='sensitivedataresponse',
            name='is_partial_transferred',
            field=models.BooleanField(default=False),
        ),
    ]
