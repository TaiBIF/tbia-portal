from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_apikey_applicant_apikey_partner_apikey_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='apikey',
            name='status',
            field=models.CharField(blank=True, choices=[('pass', '通過'), ('expired', '過期'), ('disabled', '停用')], max_length=20),
        ),
    ]
