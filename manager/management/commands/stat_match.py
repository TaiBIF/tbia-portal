""" 從共享 volume 的 snapshot.json / meta.json 匯入 MatchStat、MatchReport

    python manage.py stat_match 2026-09                         # 匯入當月全部單位
    python manage.py stat_match 2026-09 --group nps namr        # 只匯入這些 group 的資料庫（驗證用，預設不寄信）
    python manage.py stat_match 2026-09 --unit nps_1 namr_0     # 只匯入這些資料庫（驗證用，預設不寄信）
    python manage.py stat_match 2026-09 --group nps --send-mail # 部分匯入後仍寄出這些單位的夥伴信件
    python manage.py stat_match 2026-09 --no-mail               # 只匯入、不寄信

匯入全部單位後會自動呼叫 send_match_report 寄信（已寄過的對象不會重複寄）。

datahub 端 build_match_report.py 會把 snapshot.json、meta.json 寫到共享 volume；
web 端對應路徑為 MEDIA_ROOT/match_report/<year_month>/<group>_<info_id>/。
同一 group 可能有多個資料庫（如 nps_0、nps_1），各自匯入，以 (group, info_id) 區分。
"""
import json
import re
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q

from manager.models import MatchStat, MatchReport

# 共享 volume 上比對報告的根目錄（web 端 = /tbia-volumes/media/match_report）
MATCH_REPORT_DIR = Path(settings.MEDIA_ROOT) / 'match_report'


class Command(BaseCommand):
    help = '讀 snapshot.json / meta.json 匯入 MatchStat、MatchReport（不直接讀 match_log）'

    def add_arguments(self, parser):
        parser.add_argument('year_month', help='YYYY-MM，例如 2026-09')
        parser.add_argument('--group', nargs='+', default=None,
                            help='只匯入這些 group 的資料庫，可傳多個（省略則當月全部）')
        parser.add_argument('--unit', nargs='+', default=None,
                            help='只匯入這些資料庫，格式 {group}_{info_id}，可傳多個')
        parser.add_argument('--no-mail', action='store_true',
                            help='匯入後不寄信')
        parser.add_argument('--send-mail', action='store_true',
                            help='搭配 --group / --unit 時仍寄出這些單位的夥伴信件')

    def handle(self, *args, **options):
        year_month = options['year_month']
        groups, units = options['group'], options['unit']
        partial = bool(groups or units)

        base = MATCH_REPORT_DIR / year_month
        dirs, keys = [], []          # keys：實際匯入的 (group, info_id)，部分匯入時只覆蓋這些
        if base.exists():
            for p in sorted(base.iterdir()):
                # 只認 {group}_{info_id} 目錄；略過 _mail_preview 等內部目錄與舊格式（只有 group）
                m = re.fullmatch(r'(.+)_(\d+)', p.name)
                if not p.is_dir() or p.name.startswith('_') or not m:
                    continue
                if groups and m.group(1) not in groups:
                    continue
                if units and p.name not in units:
                    continue
                dirs.append(p)
                keys.append((m.group(1), int(m.group(2))))

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
                    info_id=r.get('info_id'),
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
                    group=m.get('group'),
                    info_id=m.get('info_id'),
                    rights_holder=m.get('rights_holder'),
                    year_month=m.get('year_month', year_month),
                    prev_year_month=m.get('prev_year_month'),
                    logic_changed=bool(m.get('logic_changed')),
                    compare=m.get('compare'),
                ))

        # 與 stat_data 相同的可重跑策略：先刪當月（或當月指定單位）舊資料再寫入。
        # 帶 --group / --unit 時只覆蓋這次實際匯入的資料庫，不動其他單位，方便逐一驗證。
        if partial and not keys:
            self.stdout.write(self.style.WARNING('沒有符合的資料庫，未做任何變更'))
            return
        with transaction.atomic():
            for model in (MatchStat, MatchReport):
                qs = model.objects.filter(year_month=year_month)
                if partial:
                    cond = Q()
                    for g, i in keys:
                        cond |= Q(group=g, info_id=i)
                    qs = qs.filter(cond)
                qs.delete()
            MatchStat.objects.bulk_create(rows)
            MatchReport.objects.bulk_create(reports)

        self.stdout.write(self.style.SUCCESS(
            f'{year_month} 匯入 {len(rows)} 列、{len(reports)} 份報告資訊，來自 {used} 個資料庫'))

        # 匯入後自動寄信：全部單位匯入時預設寄出；部分單位（驗證用）需加 --send-mail，且只寄夥伴信件
        if options['no_mail'] or not used:
            return
        if partial:
            if options['send_mail']:
                call_command('send_match_report', year_month,
                             unit=[f'{g}_{i}' for g, i in keys], only=['partner'])
            return
        call_command('send_match_report', year_month)