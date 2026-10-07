from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0094_matchreport_matchstat_category_key'),
    ]

    operations = [
        migrations.AddField(
            model_name='matchstat',
            name='info_id',
            field=models.IntegerField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name='matchreport',
            name='info_id',
            field=models.IntegerField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name='matchreport',
            name='rights_holder',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
