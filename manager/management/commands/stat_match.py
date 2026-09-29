""" 從共享 volume 的 snapshot.json 匯入 MatchStat

    python manage.py stat_match 2026-09              # 匯入當月全部單位
    python manage.py stat_match 2026-09 --group namr  # 只匯入單一單位（驗證用）

datahub 端 build_match_report.py 會把 snapshot.json 寫到共享 volume；
web 端對應路徑為 MEDIA_ROOT/match_report/<year_month>/<group>/snapshot.json。
"""
import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from manager.models import MatchStat

# 共享 volume 上比對報告的根目錄（web 端 = /tbia-volumes/media/match_report）
MATCH_REPORT_DIR = Path(settings.MEDIA_ROOT) / 'match_report'


class Command(BaseCommand):
    help = '讀 snapshot.json 匯入 MatchStat（不直接讀 match_log）'

    def add_arguments(self, parser):
        parser.add_argument('year_month', help='YYYY-MM，例如 2026-09')
        parser.add_argument('--group', default=None,
                            help='只匯入單一單位（省略則當月全部）')

    def handle(self, *args, **options):
        year_month = options['year_month']
        group = options['group']

        base = MATCH_REPORT_DIR / year_month
        if group:
            dirs = [base / group]
        elif base.exists():
            dirs = sorted(p for p in base.iterdir() if p.is_dir())
        else:
            dirs = []

        rows, used = [], 0
        for d in dirs:
            snap = d / 'snapshot.json'
            if not snap.exists():
                self.stdout.write(self.style.WARNING(f'略過（無 snapshot.json）：{d.name}'))
                continue
            used += 1
            for r in json.loads(snap.read_text(encoding='utf-8')):
                rows.append(MatchStat(
                    group=r.get('group'),
                    rights_holder=r.get('rights_holder'),
                    year_month=r.get('year_month', year_month),
                    axis=r.get('axis'),
                    category=r.get('category'),
                    responsibility=r.get('responsibility'),
                    records=r.get('records'),
                    unique_names=r.get('unique_names'),
                ))

        # 與 stat_data 相同的可重跑策略：先刪當月（或當月該單位）舊資料再寫入。
        # 帶 --group 時只覆蓋該單位，不動其他單位，方便逐一驗證。
        qs = MatchStat.objects.filter(year_month=year_month)
        if group:
            qs = qs.filter(group=group)
        qs.delete()
        MatchStat.objects.bulk_create(rows)

        self.stdout.write(self.style.SUCCESS(
            f'{year_month} 匯入 {len(rows)} 列，來自 {used} 個單位'))