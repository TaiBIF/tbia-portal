# Generated by Django 3.2.10 on 2022-10-26 03:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0028_alter_searchquery_modified'),
    ]

    operations = [
        migrations.AlterField(
            model_name='searchquery',
            name='created',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='searchquery',
            name='modified',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]