# 5.4：SearchStat / SearchCount 的 search_location 新增 api_partner（夥伴單位API）。只改 choices，不動資料表
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0099_stat_source_database_v2'),
    ]

    operations = [
        migrations.AlterField(
            model_name='searchstat',
            name='search_location',
            field=models.CharField(blank=True, choices=[
                ('full', '全站搜尋'), ('occ', '物種出現紀錄進階搜尋'), ('col', '自然史典藏進階搜尋'),
                ('api_occ', '物種出現紀錄API'), ('api_map', '地圖API'), ('api_dataset', '資料集API'),
                ('dataset', '資料集搜尋'), ('api_partner', '夥伴單位API')], max_length=20),
        ),
        migrations.AlterField(
            model_name='searchcount',
            name='search_location',
            field=models.CharField(blank=True, choices=[
                ('api_occ', '物種出現紀錄API'), ('api_dataset', '資料集API'), ('api_map', '地圖API'),
                ('api_partner', '夥伴單位API')], max_length=20),
        ),
    ]
