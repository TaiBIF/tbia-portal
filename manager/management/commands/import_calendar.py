""" python manage.py import_calendar calendar_2027.csv """
from datetime import datetime
from os.path import exists, join

import pandas as pd
from django.core.management.base import BaseCommand, CommandError

from manager.models import Workday

CALENDAR_FOLDER = '/tbia-volumes/bucket/calendar'


class Command(BaseCommand):
    help = '從政府開放資料平台的行事曆 CSV 匯入工作日曆'

    def add_arguments(self, parser):
        parser.add_argument('filename', help='CSV 檔名，例如 calendar_2027.csv')

    def handle(self, *args, **options):
        path = join(CALENDAR_FOLDER, options['filename'])
        if not exists(path):
            raise CommandError(f'找不到檔案：{path}')

        df = pd.read_csv(path, usecols=['西元日期', '是否放假'])
        df = df.rename(columns={'西元日期': 'date', '是否放假': 'is_dayoff'})
        df['is_dayoff'] = df['is_dayoff'].replace({0: False, 2: True})
        df['date'] = df['date'].apply(lambda x: datetime.strptime(str(x), '%Y%m%d').date())

        for row in df.itertuples(index=False):
            Workday.objects.update_or_create(
                date=row.date,
                defaults={'is_dayoff': row.is_dayoff},
            )

        self.stdout.write(self.style.SUCCESS(f'{options["filename"]} 匯入完成，共 {len(df)} 筆'))