""" 寄送學名比對狀況信件（讀共享 volume 上 build_match_report.py 的產出）

    python manage.py send_match_report 2026-09                    # 寄出當月全部信件
    python manage.py send_match_report 2026-09 --dry-run          # 不寄出，信件存成 html 檔預覽
    python manage.py send_match_report 2026-09 --to me@example.com   # 全部改寄到測試信箱
    python manage.py send_match_report 2026-09 --only partner --group namr   # 只寄單一單位
    python manage.py send_match_report 2026-09 --resend           # 忽略已寄送紀錄，重新寄出

一般由 stat_match 匯入完成後自動呼叫（見 stat_match.py）。

寄送對象：
  partner  各單位的單位管理員（is_partner_admin），信件內嵌比對狀況圖、附夥伴可修清單
           同一 group 有多個資料庫（如 nps_0、nps_1）時合併成一封，內含各資料庫的圖與附件
  taicol   TaiCOL 管理員（.env 的 TAICOL_ADMIN_EMAILS，逗號分隔），附各單位合併的回報清單
  system   系統管理員（is_system_admin），各單位彙整表 + 回報 TaiCOL 清單

已寄送紀錄存在 MEDIA_ROOT/match_report/<year_month>/_mailed.json，避免 stat_match 重跑時重複寄信。

.env 設定：
  SITE_URL=https://dev.tbiadata.tw            網站根網址（不含結尾斜線），用於信件中的後台連結
  TAICOL_ADMIN_EMAILS=a@example.com,b@example.com
  MATCH_MAIL_TEST_TO=engineer@example.com     測試站使用：設定後所有信件改寄到這些信箱
                                              （主旨加 [測試]、內文列出原收件人、不寫入寄送紀錄）
                                              正式站請留空或不設定
"""
import csv
import json
import re
from datetime import datetime
from email.mime.image import MIMEImage
from pathlib import Path

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.management.base import BaseCommand, CommandError

from conf.settings import env
from manager.models import Partner, User

MATCH_REPORT_DIR = Path(settings.MEDIA_ROOT) / 'match_report'
FROM_EMAIL = 'TBIA <no-reply@tbiadata.tw>'
SUBJECT_PREFIX = '[TBIA 生物多樣性資料庫共通查詢系統] '
SITE_URL = env('SITE_URL', default='https://tbiadata.tw').rstrip('/')
MANAGER_URL = f'{SITE_URL}/zh-hant/manager/partner'          # 夥伴後台（比對狀況面板所在頁）
SYSTEM_MANAGER_URL = f'{SITE_URL}/zh-hant/manager/system'    # 系統管理員後台
# 測試站：所有信件改寄到這些信箱（逗號分隔）；正式站留空
TEST_TO = [e.strip() for e in env('MATCH_MAIL_TEST_TO', default='').split(',') if e.strip()]

SIGNATURE = """
<br>臺灣生物多樣性資訊聯盟
<br>Taiwan Biodiversity Information Alliance
"""

# 內嵌 CSS（信件用 inline style，多數信件軟體不支援 <style>）
BOX = 'background:#f6f8f5;border-left:3px solid {c};padding:10px 14px;margin:12px 0;'
TH = 'border:1px solid #dfe4de;padding:6px 10px;background:#f6f8f5;text-align:left;'
TD = 'border:1px solid #dfe4de;padding:6px 10px;'
TDN = TD + 'text-align:right;'
BTN = ('display:inline-block;background:#2f6b5e;color:#fff;text-decoration:none;'
       'padding:8px 16px;border-radius:4px;')


def fmt(n):
    return f'{int(n or 0):,}'


def read_json(p):
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else None


def atrank_rate(snapshot):
    total = sum(r['records'] for r in snapshot) or 1
    at = sum(r['records'] for r in snapshot
             if (r.get('category_key') == 'atrank') or r.get('category') == '對到（來源階層）')
    return round(at / total * 100, 1), sum(r['records'] for r in snapshot)


class Command(BaseCommand):
    help = '寄送學名比對狀況信件給夥伴單位、TaiCOL 管理員、系統管理員'

    def add_arguments(self, parser):
        parser.add_argument('year_month', help='YYYY-MM，例如 2026-09')
        parser.add_argument('--group', default=None, help='只處理該 group（僅影響夥伴信件）')
        parser.add_argument('--only', choices=['partner', 'taicol', 'system'], action='append',
                            help='只寄特定對象，可重複指定；省略則三者都寄')
        parser.add_argument('--dry-run', action='store_true', help='不寄出，信件存成 html 檔')
        parser.add_argument('--to', default=None, help='全部信件改寄到此信箱（測試用，逗號分隔）')
        parser.add_argument('--resend', action='store_true', help='忽略已寄送紀錄，重新寄出')

    # ── 主流程 ──────────────────────────────────────────────
    def handle(self, *args, **o):
        self.ym = o['year_month']
        self.base = MATCH_REPORT_DIR / self.ym
        if not self.base.exists():
            raise CommandError(f'找不到比對報告目錄：{self.base}')
        self.dry_run, self.resend = o['dry_run'], o['resend']
        # 改寄優先序：--to 參數 > .env 的 MATCH_MAIL_TEST_TO
        self.override_to = [e.strip() for e in (o['to'] or '').split(',') if e.strip()] or TEST_TO
        # 改寄時不寫入寄送紀錄，避免測試寄送擋住之後的正式寄送
        self.record = not self.dry_run and not self.override_to
        if self.override_to:
            self.stdout.write(self.style.WARNING(f'測試模式：所有信件改寄到 {", ".join(self.override_to)}'))
        targets = set(o['only'] or ['partner', 'taicol', 'system'])

        self.log_path = self.base / '_mailed.json'
        self.log = read_json(self.log_path) or {'partner': {}}
        self.preview_dir = self.base / '_mail_preview'

        units = self.load_units(o['group'])
        if not units:
            self.stdout.write(self.style.WARNING('沒有可寄送的單位（無 snapshot.json）'))
            return

        if 'partner' in targets:
            by_group = {}
            for u in units:
                by_group.setdefault(u['group'], []).append(u)
            for g, us in by_group.items():
                self.send_partner(g, us)

        # TaiCOL / 系統管理員信件是全部單位的彙整，指定 --group 時不寄
        if o['group'] and targets & {'taicol', 'system'}:
            self.stdout.write(self.style.WARNING('指定 --group 時不寄 TaiCOL／系統管理員彙整信'))
        else:
            all_units = units if not o['group'] else self.load_units(None)
            merged = self.merge_taicol(all_units)
            if 'taicol' in targets:
                self.send_taicol(all_units, merged)
            if 'system' in targets:
                self.send_system(all_units, merged)

        if self.record:
            self.log_path.write_text(json.dumps(self.log, ensure_ascii=False, indent=2),
                                     encoding='utf-8')

    # ── 讀取各單位產出 ──────────────────────────────────────
    def load_units(self, group):
        """讀取各資料庫（{group}_{info_id} 目錄）的產出，依 group、info_id 排序。"""
        units = []
        for d in sorted(self.base.iterdir()):
            m = re.fullmatch(r'(.+)_(\d+)', d.name)
            if not d.is_dir() or d.name.startswith('_') or not m:
                continue
            if group and m.group(1) != group:
                continue
            snap = read_json(d / 'snapshot.json')
            if not snap:
                continue
            meta = read_json(d / 'meta.json') or {}
            rate, total = atrank_rate(snap)
            prev_rate = None
            prev_ym = meta.get('prev_year_month')
            if prev_ym and not meta.get('logic_changed'):
                prev = read_json(MATCH_REPORT_DIR / prev_ym / d.name / 'snapshot.json')
                if prev:
                    prev_rate = atrank_rate(prev)[0]
            units.append({
                'unit': d.name, 'group': m.group(1), 'info_id': int(m.group(2)),
                'dir': d, 'snapshot': snap, 'meta': meta,
                'rights_holder': snap[0].get('rights_holder') or d.name,
                'rate': rate, 'total': total,
                'overall': round(sum(r['records'] for r in snap if r['axis'] == 'matched')
                                 / (total or 1) * 100, 1),
                'delta': None if prev_rate is None else round(rate - prev_rate, 1),
            })
        units.sort(key=lambda u: (u['group'], u['info_id']))
        return units

    # ── 寄送共用 ────────────────────────────────────────────
    def deliver(self, key, to, subject, html, attachments=(), inline_pngs=()):
        """key 用於預覽檔名與紀錄；attachments = [(Path, 檔名)]；
        inline_pngs = [(content_id, Path)]，內文以 <img src="cid:{content_id}"> 引用"""
        original = [e for e in dict.fromkeys(to) if e]
        if self.override_to:
            # 測試寄送：主旨加註、內文最上方列出原收件人，方便確認收件人是否正確
            to = self.override_to
            subject = '[測試] ' + subject
            html = (f'<div style="{BOX.format(c="#c0533f")}font-size:13px">測試信件：正式寄送時收件人為 '
                    f'{", ".join(original) or "（無收件人，正式寄送時會略過）"}</div>') + html
        else:
            to = original
        if not to:
            self.stdout.write(self.style.WARNING(f'略過（無收件人）：{key}'))
            return False
        subject = SUBJECT_PREFIX + subject

        if self.dry_run:
            self.preview_dir.mkdir(exist_ok=True)
            page = html
            for cid, png in inline_pngs:
                page = page.replace(f'cid:{cid}', f'../{png.parent.name}/{png.name}')
            names = '、'.join(n for _, n in attachments) or '無'
            head = (f'<p style="font:13px sans-serif;color:#5f6a64">收件者：{", ".join(to)}<br>'
                    f'主旨：{subject}<br>附件：{names}</p><hr>')
            (self.preview_dir / f'{key}.html').write_text(head + page, encoding='utf-8')
            self.stdout.write(f'[dry-run] {key} → {", ".join(to)}')
            return True

        msg = EmailMultiAlternatives(subject=subject, body='本信件為 HTML 格式，請使用支援 HTML 的信件軟體閱讀。',
                                     from_email=FROM_EMAIL, to=to)
        msg.attach_alternative(html, 'text/html')
        if inline_pngs:
            msg.mixed_subtype = 'related'
        for cid, png in inline_pngs:
            if png.exists():
                img = MIMEImage(png.read_bytes(), 'png')
                img.add_header('Content-ID', f'<{cid}>')
                img.add_header('Content-Disposition', 'inline', filename=f'{cid}.png')
                msg.attach(img)
        for path, name in attachments:
            if path.exists():
                msg.attach(name, path.read_bytes(), 'text/csv')
        msg.send()
        self.stdout.write(self.style.SUCCESS(f'已寄出 {key} → {", ".join(to)}'))
        return True

    # ── 夥伴單位 ────────────────────────────────────────────
    def partner_recipients(self, group):
        # 單位管理員；若該單位沒有管理員，退回該單位所有審核通過的帳號
        qs = User.objects.filter(partner__group=group, is_active=True)
        emails = list(qs.filter(is_partner_admin=True).values_list('email', flat=True))
        if not emails:
            emails = list(qs.filter(is_partner_account=True, status='pass')
                          .values_list('email', flat=True))
        return emails

    def unit_section(self, u, cid, multi):
        """單一資料庫的段落：摘要、比對狀況圖、前次比較。"""
        meta, c = u['meta'], u['meta'].get('compare')
        h = ''
        if multi:
            h += f'<h3 style="font-size:16px;margin:24px 0 4px">{u["rights_holder"]}</h3>'
        h += (f'<p>本次共 {fmt(u["total"])} 筆紀錄，其中 <b>{u["rate"]:.1f}%</b> 對到來源提供的階層。</p>')
        h += (f'<img src="cid:{cid}" alt="{u["rights_holder"]} 學名比對狀況圖" '
              'style="max-width:100%;border:1px solid #dfe4de;border-radius:4px">')
        if c and not meta.get('logic_changed'):
            worse = c.get('worse', 0)
            h += (f'<div style="{BOX.format(c="#c0533f" if worse else "#2f6b5e")}">'
                  f'與前次（{meta.get("prev_year_month")}）相比：新對到來源階層 <b>{fmt(c.get("new_atrank"))}</b> 個學名、'
                  f'未對到原因改變 {fmt(c.get("reason_changed"))} 個、新增未對到學名 {fmt(c.get("new_name"))} 個。')
            if worse:
                h += (f'<br>另有 <b>{fmt(worse)}</b> 個學名原本對到、本次未對到，'
                      '請至後台下載「學名變化清單」確認。')
            h += '</div>'
        return h

    def send_partner(self, g, units):
        """同一 group 的所有資料庫合併成一封信。"""
        if not self.resend and g in self.log['partner']:
            self.stdout.write(f'略過（已寄送 {self.log["partner"][g]}）：partner_{g}')
            return
        p = Partner.objects.filter(group=g).first()
        name = (p.title if p and p.title else None) or units[0]['rights_holder']
        multi = len(units) > 1

        h = '<div style="font-size:14.5px;line-height:1.75;color:#191e1b;max-width:680px">'
        h += f'<p>{name} 您好：</p>'
        h += (f'<p>TBIA 已完成 {self.ym} 資料更新，以下為貴單位'
              + (f' {len(units)} 個資料庫' if multi else '資料') + '的學名比對狀況。</p>')
        if any(u['meta'].get('logic_changed') for u in units):
            h += (f'<div style="{BOX.format(c="#2f6b5e")}">本次 TBIA 更新了學名比對邏輯並重新比對全部資料，'
                  '比對結果的變化主要來自比對方式調整，並非貴單位資料變動，因此本次不與前次比較。</div>')
        pngs, atts = [], []
        for u in units:
            cid = f'match_{u["unit"]}'
            h += self.unit_section(u, cid, multi)
            pngs.append((cid, u['dir'] / 'email.png'))
            atts.append((u['dir'] / 'unmatched_partner.csv',
                         f'unmatched_partner_{u["unit"]}_{self.ym}.csv'))
        h += ('<p>附件為' + ('各資料庫' if multi else '貴單位') + '可協助修正的學名清單，每筆附有原因說明與格式提醒。'
              '「TaiCOL 尚未收錄」的學名已由 TBIA 彙整回報，無需貴單位處理。</p>')
        h += f'<p><a href="{MANAGER_URL}" style="{BTN}">前往後台查看完整比對狀況</a></p>'
        h += f'<p>{SIGNATURE}</p></div>'

        ok = self.deliver(f'partner_{g}', self.partner_recipients(g),
                          f'{name} 學名比對狀況（{self.ym}）', h,
                          attachments=atts, inline_pngs=pngs)
        if ok and self.record:
            self.log['partner'][g] = datetime.now().strftime('%Y-%m-%d %H:%M')

    # ── 合併回報 TaiCOL 清單 ────────────────────────────────
    def merge_taicol(self, units):
        """合併各單位 for_taicol.csv；回傳 (合併檔 Path, {rights_holder: 統計})"""
        out = self.base / f'for_taicol_{self.ym}.csv'
        stats, header, rows = {}, None, []
        for u in units:
            p = u['dir'] / 'for_taicol.csv'
            if not p.exists():
                continue
            with open(p, newline='', encoding='utf-8-sig') as f:
                r = csv.reader(f)
                h = next(r, None)
                header = header or h
                s = stats.setdefault(u['rights_holder'],
                                     {'none_n': 0, 'none_r': 0, 'higher_n': 0, 'higher_r': 0})
                for row in r:
                    rows.append(row)
                    kind = 'none' if row[1] == 'TaiCOL 尚未收錄' else 'higher'
                    s[f'{kind}_n'] += 1
                    s[f'{kind}_r'] += int(row[2] or 0)
        if header:
            rows.sort(key=lambda x: -int(x[2] or 0))      # 依影響筆數排序
            with open(out, 'w', newline='', encoding='utf-8-sig') as f:
                w = csv.writer(f)
                w.writerow(header)
                w.writerows(rows)
        return (out if header else None), stats

    def taicol_table(self, stats):
        h = (f'<table style="border-collapse:collapse;font-size:13.5px;margin:10px 0">'
             f'<tr><th style="{TH}">單位</th><th style="{TH}">尚未收錄（學名數）</th>'
             f'<th style="{TH}">影響筆數</th><th style="{TH}">僅對到上階（學名數）</th>'
             f'<th style="{TH}">影響筆數</th></tr>')
        tot = {'none_n': 0, 'none_r': 0, 'higher_n': 0, 'higher_r': 0}
        for rh, s in sorted(stats.items(), key=lambda x: -x[1]['none_r']):
            h += f'<tr><td style="{TD}">{rh}</td>'
            for k in tot:
                tot[k] += s[k]
                h += f'<td style="{TDN}">{fmt(s[k])}</td>'
            h += '</tr>'
        h += f'<tr><th style="{TH}">合計</th>' + ''.join(
            f'<th style="{TH}text-align:right">{fmt(v)}</th>' for v in tot.values()) + '</tr></table>'
        return h

    def send_taicol(self, units, merged):
        if not self.resend and self.log.get('taicol'):
            self.stdout.write(f'略過（已寄送 {self.log["taicol"]}）：taicol')
            return
        path, stats = merged
        to = [e.strip() for e in env('TAICOL_ADMIN_EMAILS', default='').split(',') if e.strip()]
        logic_changed = any(u['meta'].get('logic_changed') for u in units)

        h = '<div style="font-size:14.5px;line-height:1.75;color:#191e1b;max-width:680px">'
        h += '<p>TaiCOL 管理員您好：</p>'
        h += (f'<p>{self.ym} 資料更新後，以下學名在 TaiCOL 尚未收錄，或只能對到較來源更上層的階層，'
              '彙整如附件，請協助確認是否需要收錄或補充。已排除非正規學名（sp.、cf. 等）與暫定名。</p>')
        if logic_changed:
            h += (f'<div style="{BOX.format(c="#2f6b5e")}">本次更新了學名比對邏輯並重新比對全部資料，'
                  '數量與前次的差異主要來自比對方式調整。</div>')
        h += self.taicol_table(stats) if stats else '<p>本次沒有需要回報的學名。</p>'
        h += '<p>附件依影響筆數排序，並附來源中文名、科與格式提醒欄位，方便判斷是否為格式問題。</p>'
        h += f'<p>{SIGNATURE}</p></div>'

        ok = self.deliver('taicol', to, f'{self.ym} 待 TaiCOL 確認學名清單', h,
                          attachments=[(path, path.name)] if path else [])
        if ok and not self.dry_run:
            self.log['taicol'] = datetime.now().strftime('%Y-%m-%d %H:%M')

    # ── 系統管理員 ──────────────────────────────────────────
    def send_system(self, units, merged):
        if not self.resend and self.log.get('system'):
            self.stdout.write(f'略過（已寄送 {self.log["system"]}）：system')
            return
        path, stats = merged
        to = list(User.objects.filter(is_system_admin=True, is_active=True)
                  .values_list('email', flat=True))

        h = '<div style="font-size:14.5px;line-height:1.75;color:#191e1b;max-width:760px">'
        h += '<p>系統管理員您好：</p>'
        h += f'<p>{self.ym} 學名比對狀況報告已產出並匯入後台，各單位摘要如下。</p>'
        h += (f'<table style="border-collapse:collapse;font-size:13.5px;margin:10px 0">'
              f'<tr><th style="{TH}">單位</th><th style="{TH}">對到來源階層</th><th style="{TH}">較前次</th>'
              f'<th style="{TH}">整體對到</th><th style="{TH}">總筆數</th>'
              f'<th style="{TH}">變差學名數</th><th style="{TH}">夥伴信件</th></tr>')
        for u in sorted(units, key=lambda x: x['rate']):
            m = u['meta']
            if m.get('logic_changed'):
                d = '邏輯更新'
            elif u['delta'] is None:
                d = '—'
            else:
                d = f'{"▲" if u["delta"] >= 0 else "▼"} {u["delta"]:+.1f}%'
            worse = (m.get('compare') or {}).get('worse')
            worse_s = '—' if worse is None or m.get('logic_changed') else fmt(worse)
            warn = ' style="color:#c0533f;font-weight:600"' if worse and not m.get('logic_changed') else ''
            sent = self.log['partner'].get(u['group'], '未寄出')
            h += (f'<tr><td style="{TD}">{u["rights_holder"]}</td>'
                  f'<td style="{TDN}">{u["rate"]:.1f}%</td><td style="{TDN}">{d}</td>'
                  f'<td style="{TDN}">{u["overall"]:.1f}%</td><td style="{TDN}">{fmt(u["total"])}</td>'
                  f'<td style="{TDN}"><span{warn}>{worse_s}</span></td><td style="{TD}">{sent}</td></tr>')
        h += '</table>'
        h += ('<p>「變差學名數」為原本對到來源階層、本次未對到的學名數，建議優先確認。'
              '附件為本次回報 TaiCOL 的合併清單。</p>')
        h += f'<p><a href="{SYSTEM_MANAGER_URL}" style="{BTN}">前往系統管理員後台</a></p>'
        h += f'<p>{SIGNATURE}</p></div>'

        ok = self.deliver('system', to, f'{self.ym} 學名比對狀況報告', h,
                          attachments=[(path, path.name)] if path else [])
        if ok and not self.dry_run:
            self.log['system'] = datetime.now().strftime('%Y-%m-%d %H:%M')
