# Generated by Django 4.0.4 on 2023-11-20 09:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0029_auto_20231115_0312'),
    ]

    operations = [
        migrations.CreateModel(
            name='Variant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('char', models.CharField(blank=True, max_length=10000, null=True)),
                ('pattern', models.CharField(blank=True, max_length=10000, null=True)),
            ],
        ),
    ]
