# Generated by Django 3.2.10 on 2023-11-07 07:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0044_partner_index_order'),
    ]

    operations = [
        migrations.CreateModel(
            name='workday',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.CharField(blank=True, max_length=8, null=True)),
                ('is_dayoff', models.BooleanField(default=False)),
            ],
        ),
    ]