# Generated by Django 3.2.10 on 2023-10-27 06:19

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='APIkey',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=100)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(blank=True, choices=[('pass', '通過'), ('expired', '過期')], max_length=20)),
            ],
        ),
    ]