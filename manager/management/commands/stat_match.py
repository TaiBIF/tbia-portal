""" 從共享 volume 的 snapshot.json / meta.json 匯入 MatchStat、MatchReport

    python manage.py stat_match 2026-09              # 匯入當月全部單位
    python manage.py stat_match 2026-09 --group namr  # 只匯入單一單位（驗證用，預設不寄信）
    python manage.py stat_match 2026-09 --no-mail     # 只匯入、不寄信

匯入全部單位後會自動呼叫 send_match_report 寄信（已寄過的對象不會重複寄）。

datahub 端 build_match_report.py 會把 snapshot.json、meta.json 寫到共享 volume；
web 端對應路徑為 MEDIA_ROOT/match_report/<year_month>/<group>/。
"""
import json
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction

from manager.models import MatchStat, MatchReport

# 共享 volume 上比對報告的根目錄（web 端 = /tbia-volumes/media/match_report）
MATCH_REPORT_DIR = Path(settings.MEDIA_ROOT) / 'match_report'


class Command(BaseCommand):
    help = '讀 snapshot.json / meta.json 匯入 MatchStat、MatchReport（不直接讀 match_log）'

    def add_arguments(self, parser):
        parser.add_argument('year_month', help='YYYY-MM，例如 2026-09')
        parser.add_argument('--group', default=None,
                            help='只匯入單一單位（省略則當月全部）')
        parser.add_argument('--no-mail', action='store_true',
                            help='匯入後不寄信')
        parser.add_argument('--send-mail', action='store_true',
                            help='搭配 --group 時仍寄出該單位的夥伴信件')

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

        rows, reports, used = [], [], 0
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
                    category_key=r.get('category_key') or '',
                    category=r.get('category'),
                    responsibility=r.get('responsibility'),
                    records=r.get('records'),
                    unique_names=r.get('unique_names'),
                ))

            # meta.json 為新版報告才有；舊版報告略過（網頁端視為可比較、無學名變化摘要）
            meta_path = d / 'meta.json'
            if meta_path.exists():
                m = json.loads(meta_path.read_text(encoding='utf-8'))
                reports.append(MatchReport(
                    group=m.get('group') or d.name,
                    year_month=m.get('year_month', year_month),
                    prev_year_month=m.get('prev_year_month'),
                    logic_changed=bool(m.get('logic_changed')),
                    compare=m.get('compare'),
                ))

        # 與 stat_data 相同的可重跑策略：先刪當月（或當月該單位）舊資料再寫入。
        # 帶 --group 時只覆蓋該單位，不動其他單位，方便逐一驗證。
        with transaction.atomic():
            for model in (MatchStat, MatchReport):
                qs = model.objects.filter(year_month=year_month)
                if group:
                    qs = qs.filter(group=group)
                qs.delete()
            MatchStat.objects.bulk_create(rows)
            MatchReport.objects.bulk_create(reports)

        self.stdout.write(self.style.SUCCESS(
            f'{year_month} 匯入 {len(rows)} 列、{len(reports)} 份報告資訊，來自 {used} 個單位'))

        # 匯入後自動寄信：全部單位匯入時預設寄出；單一單位（驗證用）需加 --send-mail
        if options['no_mail'] or not used:
            return
        if group:
            if options['send_mail']:
                call_command('send_match_report', year_month, group=group, only=['partner'])
            return
        call_command('send_match_report', year_month)