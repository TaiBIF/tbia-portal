"""API v2 的查詢參數驗證、Solr / SQL 條件與回傳欄位整理（5.2 occurrence；5.3 dataset、map；5.4 partner）。

不需要 Django，單元測試在 api/tests_v2.py：python -m unittest api.tests_v2 -v
規格：user.html 與交接文件「API 規格調整」。和網站共用 data/search_params.py 的控制詞彙、parse_range、parse_circle。
- 值不合法回 400（ParamError），訊息寫出是哪個參數。
- 值區分大小寫（user.html「大小寫規則」），控制詞彙必須完全相同。
- 多值一律用半形逗號分隔、取聯集；重複帶同一參數也接受（併成多值）。
- 規格沒有列的參數不處理（例：locality、organismQuantity，D10）；v1 的 apikey 參數回 400，提示改用 header。
"""
import re
from datetime import datetime

import shapely.wkt
from shapely.errors import ShapelyError

from data.search_params import (
    parse_range, parse_circle, TAXON_GROUPS, HABITAT_PARAM, NATIVENESS, PROTECTED_STATUS,
    TYPE_STATUS, MEDIA_TYPES, BASIS_OF_RECORD, RANK_EN_TO_SOLR, RANK_SOLR_TO_EN, INFRASPECIES_RANKS,
    SOURCE_DATABASE_RENAME, to_source_database,
)
from data.fields import API_OCCURRENCE_FIELDS, RESTRICTED_OVERRIDE, API_DATASET_FIELDS

DEFAULT_LIMIT = 20
MAX_LIMIT = 1000


class ParamError(Exception):
    """查詢參數不合法 → HTTP 400"""
    def __init__(self, param, message=None):
        self.param = param
        super().__init__(message or f'Invalid {param}')


# ---- 共用 ----

def solr_quote(v):
    """同 data.utils.solr_quote：雙引號包起來並跳脫，值當成一整個字串比對"""
    return '"' + str(v).replace('\\', '\\\\').replace('"', '\\"') + '"'


def get_values(params, key):
    """params：{參數: [值, ...]}（QueryDict 轉成 dict(lists())）。
    重複參數與半形逗號都拆成多值，去頭尾空白、去重、丟空值"""
    out = []
    for v in params.get(key) or []:
        for p in str(v).split(','):
            p = p.strip()
            if p and p not in out:
                out.append(p)
    return out


def get_single(params, key):
    """單值參數：重複帶不同值視為不合法；空字串視為沒帶"""
    vals = [str(v).strip() for v in params.get(key) or [] if str(v).strip()]
    if len(set(vals)) > 1:
        raise ParamError(key)
    return vals[0] if vals else None


def parse_limit(params):
    """limit：預設 20，上限 1000（超過以 1000 計）；非整數或小於 1 回 400"""
    v = get_single(params, 'limit')
    if v is None:
        return DEFAULT_LIMIT
    if not re.fullmatch(r'\d+', v) or int(v) < 1:
        raise ParamError('limit')
    return min(int(v), MAX_LIMIT)


def check_vocab(params, key, vocab, multi=True, hint=None):
    vals = get_values(params, key) if multi else ([get_single(params, key)] if get_single(params, key) else [])
    for v in vals:
        if v not in vocab:
            raise ParamError(key, hint(v) if hint and hint(v) else f'Invalid {key}: {v}')
    return vals


def parse_bool(params, key):
    v = get_single(params, key)
    if v is None:
        return None
    if v not in ('true', 'false'):
        raise ParamError(key)
    return v == 'true'


def parse_date_range(value, param):
    """API 的日期參數：嚴格 YYYYMMDD 且為實際存在的日期（網站的 parse_range 另外接受 YYYY-MM-DD、不檢查大小月）；
    區間一邊可為 *（API 規格調整 11/17）。回傳 parse_range 的 (start, end)"""
    for p in value.split(','):
        p = p.strip()
        if p in ('', '*'):
            continue
        try:
            if not re.fullmatch(r'\d{8}', p):
                raise ValueError
            datetime.strptime(p, '%Y%m%d')
        except ValueError:
            raise ParamError(param, f'Invalid {param}: 日期格式為 YYYYMMDD')
    r = parse_range(value)
    if not r:
        raise ParamError(param)
    return r


def date_range_fq(field, value, param):
    """YYYYMMDD 或區間（一邊可為 *）→ Solr 日期區間；以日期為粒度（當日 00:00:00～23:59:59）。
    created / modified 存的是台灣時間（D3），直接比對日期字面"""
    r = parse_date_range(value, param)
    start = f'{r[0][:4]}-{r[0][4:6]}-{r[0][6:]}T00:00:00Z' if r[0] else '*'
    end = f'{r[1][:4]}-{r[1][4:6]}-{r[1][6:]}T23:59:59Z' if r[1] else '*'
    return f'{field}:[{start} TO {end}]'


def parse_bounded_by(value, param='boundedBy'):
    """{最大經度},{最大緯度},{最小經度},{最小緯度} → (max_lon, max_lat, min_lon, min_lat)"""
    parts = [p.strip() for p in value.split(',')]
    try:
        max_lon, max_lat, min_lon, min_lat = (float(p) for p in parts)
    except ValueError:
        raise ParamError(param)
    if not (-180 <= min_lon <= max_lon <= 180 and -90 <= min_lat <= max_lat <= 90):
        raise ParamError(param)
    return max_lon, max_lat, min_lon, min_lat


def parse_polygon(value):
    """只接受有效且閉合的 WKT POLYGON（user.html）"""
    try:
        geom = shapely.wkt.loads(value)
    except (ShapelyError, ValueError, TypeError):
        raise ParamError('polygon')
    if geom.geom_type != 'Polygon' or not geom.is_valid or geom.is_empty:
        raise ParamError('polygon')
    return geom


def or_spatial(clauses):
    return clauses[0] if len(clauses) == 1 else '(' + ' OR '.join(clauses) + ')'


# ---- occurrence ----

# 直接轉成 create_search_query（網站查詢）的參數；值已在這裡驗證過，網站那邊的轉換對它們不會再改變什麼
_SITE_TEXT = ['name', 'taxonID', 'higherTaxonID', 'recordedBy', 'resourceContacts', 'preparations',
              'occurrenceID', 'catalogNumber', 'recordNumber', 'county', 'municipality']


def _habitat_hint(v):
    if v == 'freshWater':
        return 'Invalid taxonGroupByHabitat: freshWater（請改用 freshwater）'
    return None


def occurrence_query(params, restricted):
    """occurrence 查詢參數 → (site_params, extra_fq)
    site_params：{參數: [值]}，交給網站的 create_search_query(get_raw_map=restricted) 組條件
                 （name / higherTaxonID 的比對方式與網站一致）；
    extra_fq：網站沒有、或 API 取值不同的條件（tbiaID、tbiaPartnerID、datasetID、tbiaDatasetID、sourceDatabase、
              isCollection=false、created / modified、boundedBy、circle）。
    限制型（restricted）的空間與縣市條件同時比對公開與原始欄位（交接文件「限制型輸出與查詢對照」）"""
    if params.get('apikey'):
        raise ParamError('apikey', 'apikey 參數已停用，請改用 Authorization: Bearer <API_KEY> header')

    site, fq = {}, []

    for k in _SITE_TEXT:
        if v := get_single(params, k):
            site[k] = [v]

    # 控制詞彙
    for key, vocab, hint in [('taxonGroup', TAXON_GROUPS, None),
                             ('taxonGroupByHabitat', list(HABITAT_PARAM), _habitat_hint),
                             ('nativeness', NATIVENESS, None),
                             ('protectedStatus', PROTECTED_STATUS, None),
                             ('typeStatus', TYPE_STATUS, None)]:
        if vals := check_vocab(params, key, vocab, hint=hint):
            site[key] = vals
    # taxonRank：TaiCOL 全部階層的 en-us 名稱（11/20）；Infraspecies 同網站，查所有種下階層（不列在控制詞彙表）
    # 網站的 normalize 只認 8 個常見階層，所以這裡自己組條件，不交給 create_search_query
    if vals := check_vocab(params, 'taxonRank', list(RANK_EN_TO_SOLR) + ['Infraspecies'], multi=False):
        if vals[0] == 'Infraspecies':
            fq.append(f'taxonRank:({" OR ".join(INFRASPECIES_RANKS)})')
        else:
            fq.append(f'taxonRank:{solr_quote(RANK_EN_TO_SOLR[vals[0]])}')
    if vals := check_vocab(params, 'basisOfRecord', BASIS_OF_RECORD, multi=False):
        site['basisOfRecord'] = vals

    # 多媒體：mediaType 需 hasMedia=true
    has_media = parse_bool(params, 'hasMedia')
    media_types = check_vocab(params, 'mediaType', MEDIA_TYPES)
    if media_types and has_media is not True:
        raise ParamError('mediaType', 'Invalid mediaType: 使用 mediaType 時 hasMedia 必須為 true')
    if has_media is not None:
        site['hasMedia'] = ['true' if has_media else 'false']
    if media_types and len(media_types) < len(MEDIA_TYPES):  # 三種全選等於不限類型
        site['mediaType'] = media_types

    # 自然史典藏
    is_col = parse_bool(params, 'isCollection')
    if is_col is True:
        site['record_type'] = ['col']
    elif is_col is False:
        fq.append('recordType:occ')

    # 日期
    if v := get_single(params, 'eventDate'):
        parse_date_range(v, 'eventDate')
        site['eventDate'] = [v]
    for k in ('created', 'modified'):
        if v := get_single(params, k):
            fq.append(date_range_fq(k, v, k))

    # 識別碼與來源（多值聯集）
    if v := get_single(params, 'tbiaID'):
        fq.append(f'id:{solr_quote(v)}')
    for key in ('tbiaPartnerID', 'sourceDatabase', 'tbiaDatasetID', 'datasetID'):
        if vals := get_values(params, key):
            fq.append(f'{key}:({" OR ".join(solr_quote(v) for v in vals)})')

    # 空間
    if v := get_single(params, 'polygon'):
        parse_polygon(v)
        site['polygon'] = [v]   # create_search_query：限制型同時查 raw_location_rpt
    if v := get_single(params, 'boundedBy'):
        max_lon, max_lat, min_lon, min_lat = parse_bounded_by(v)
        box = f'[{min_lat},{min_lon} TO {max_lat},{max_lon}]'
        fields = ['location_rpt', 'raw_location_rpt'] if restricted else ['location_rpt']
        fq.append(or_spatial([f'{f}:{box}' for f in fields]))
    if v := get_single(params, 'circle'):
        c = parse_circle(v)
        if not c:
            raise ParamError('circle', 'Invalid circle: 格式為 {經度},{緯度},{半徑}，0 < 半徑 ≤ 25 公里')
        lon, lat, r = c
        fields = ['location_rpt', 'raw_location_rpt'] if restricted else ['location_rpt']
        fq.append(or_spatial([f'_query_:"{{!geofilt sfield={f} pt={lat},{lon} d={r}}}"' for f in fields]))

    return site, fq


# ---- 回傳欄位 ----

def taxon_rank_v2(value):
    """Solr taxonRank（TaiCOL 小寫、空白分隔，例 special form）→ TaiCOL ranks 表的 en-us（Special Form）。
    11/20 Kim 決定與 TaiCOL 階層一致（D26 修訂）；對不到的值（ranks 表沒有）首字大寫原樣輸出，check_step5 會列出"""
    if not value:
        return None
    return RANK_SOLR_TO_EN.get(value) or value[:1].upper() + value[1:]


def format_solr_date(value):
    """同 data.utils.format_solr_date：2026-11-05T01:23:45Z → 20261105 012345（時間已是台灣時間，D3）"""
    if isinstance(value, str) and len(value) >= 19 and value[4] == '-' and value[10] == 'T':
        return f'{value[:4]}{value[5:7]}{value[8:10]} {value[11:13]}{value[14:16]}{value[17:19]}'
    return value


def _empty(v):
    return v is None or v == '' or v == []


def format_occurrence(doc, restricted, partner_names):
    """Solr doc → v2 occurrence 一筆。全部欄位都輸出、沒有值為 null，順序同 API_OCCURRENCE_FIELDS。
    限制型：raw 欄位有值就取代對應的公開欄位（RESTRICTED_OVERRIDE，與下載相同），raw 欄位本身不輸出。
    dataGeneralizations 原樣輸出（11/20 決定，與限制型下載 CSV 相同）"""
    out = {}
    for f in API_OCCURRENCE_FIELDS:
        v = doc.get(f)
        if isinstance(v, list):  # v2 schema 皆為單值；保險起見
            v = v[0] if v else None
        out[f] = None if _empty(v) else v
    if restricted:
        for f, raw in RESTRICTED_OVERRIDE.items():
            v = doc.get(raw)
            if isinstance(v, list):
                v = v[0] if v else None
            if not _empty(v):
                out[f] = v
    for f in ('created', 'modified'):
        out[f] = format_solr_date(out[f])
    out['taxonRank'] = taxon_rank_v2(out['taxonRank'])
    pid = out['tbiaPartnerID']
    out['partnerName'] = partner_names.get(str(pid)) or None if pid else None
    return out


# ---- dataset（5.3） ----
# PG dataset 第一階段仍是舊欄位名稱與舊來源資料庫名稱（P2-2 改名），這裡用 SQL 別名輸出 v2 名稱。
# [P2-2-REMOVE] P2-2 之後：rights_holder → sourceDatabase、sourceDatasetID → datasetID、datasetURL → resourceCitationIdentifier，
# tbiaPartnerID 直接查欄位，_SOURCE_DATABASE_OLD 與 group 對照都可拿掉

_SOURCE_DATABASE_OLD = {v: k for k, v in SOURCE_DATABASE_RENAME.items()}   # 新名稱 → 舊名稱

DATASET_SELECT = (
    'SELECT "id", "name" AS "datasetName", "group", "rights_holder", "tbiaDatasetID", '
    '"sourceDatasetID" AS "datasetID", "gbifDatasetID", "resourceContacts", "occurrenceCount", '
    '"datasetDateStart", "datasetDateEnd", "datasetURL" AS "resourceCitationIdentifier", '
    '"datasetPublisher", "datasetLicense", "datasetTaxonGroup", '
    "TO_CHAR(\"created\", 'YYYYMMDD HH24MISS') AS \"created\", "
    "TO_CHAR(\"modified\", 'YYYYMMDD HH24MISS') AS \"modified\" "
    'FROM dataset'
)


def like_escape(v):
    """LIKE 的萬用字元當一般字元比對（PostgreSQL 預設跳脫字元為反斜線）"""
    return v.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')


def parse_cursor_id(params):
    """dataset 的游標是 PG dataset.id（由 links.next 帶入）；第一頁為 None"""
    v = get_single(params, 'cursor')
    if v is None or v == '*':
        return None
    if not re.fullmatch(r'\d+', v):
        raise ParamError('cursor', 'Invalid cursor')
    return int(v)


def _pg_date(yyyymmdd):
    return f'{yyyymmdd[:4]}-{yyyymmdd[4:6]}-{yyyymmdd[6:]}'


def dataset_query(params, partner_groups):
    """dataset 查詢參數 → (where, values)：where 為 SQL 條件字串清單（%s 佔位），values 依序對應。
    partner_groups：{tbiaPartnerID: [Partner.group, ...]}（PG dataset 沒有 tbiaPartnerID，靠 group 篩選）。
    - datasetName：部分比對、區分大小寫（user.html 大小寫規則；網站資料集搜尋是 ILIKE，API 同 v1 用 LIKE）
    - sourceDatabase：只認新名稱（不接受舊名，11/23 Kim）；PG 仍存舊名稱，所以新名稱同時比對對應的舊名稱
    - 對不到任何值（夥伴單位 ID 都不存在、來源資料庫都是舊名）→ 查無資料，而不是不加條件
    - 只有公開版：apikey 參數與 Authorization header 都不處理（規格沒列的參數忽略）"""
    where, values = ['"deprecated" = \'f\''], []

    for key, col in (('tbiaDatasetID', 'tbiaDatasetID'), ('datasetID', 'sourceDatasetID'),
                     ('gbifDatasetID', 'gbifDatasetID')):
        if v := get_single(params, key):
            where.append(f'"{col}" = %s')
            values.append(v)

    if vals := get_values(params, 'tbiaPartnerID'):
        groups = []
        for pid in vals:
            for g in partner_groups.get(pid, []):
                if g not in groups:
                    groups.append(g)
        if groups:
            where.append('"group" IN (' + ', '.join(['%s'] * len(groups)) + ')')
            values += groups
        else:
            where.append('FALSE')

    if vals := get_values(params, 'sourceDatabase'):
        names = []
        for v in vals:
            if to_source_database(v) != v:   # 舊名稱：不接受（API 規格調整 11/20：API 不轉換舊名稱）
                continue
            for n in (v, _SOURCE_DATABASE_OLD.get(v)):
                if n and n not in names:
                    names.append(n)
        if names:
            where.append('"rights_holder" IN (' + ', '.join(['%s'] * len(names)) + ')')
            values += names
        else:
            where.append('FALSE')

    if v := get_single(params, 'datasetName'):
        where.append('"name" LIKE %s')
        values.append(f'%{like_escape(v)}%')

    if vals := check_vocab(params, 'datasetTaxonGroup', TAXON_GROUPS):
        where.append('(' + ' OR '.join(['"datasetTaxonGroup" LIKE %s'] * len(vals)) + ')')
        values += [f'%{like_escape(v)}%' for v in vals]

    # created / modified 為台灣時間（同下載 CSV，TO_CHAR 直接輸出），以日期為粒度
    for k in ('created', 'modified'):
        if v := get_single(params, k):
            start, end = parse_date_range(v, k)
            if start:
                where.append(f'"{k}" >= %s')
                values.append(_pg_date(start))
            if end:
                where.append(f'"{k}" < (%s::date + 1)')
                values.append(_pg_date(end))

    return where, values


def format_ymd(value):
    """datasetDateStart / End → YYYYMMDD（11/23 Kim）；date / datetime 或 YYYY-MM-DD 開頭的字串都轉，其他格式原樣輸出"""
    if value is None or value == '':
        return None
    if hasattr(value, 'strftime'):
        return value.strftime('%Y%m%d')
    s = str(value)
    if re.match(r'\d{4}-\d{2}-\d{2}', s):
        return s[:4] + s[5:7] + s[8:10]
    return s


def format_dataset(row, partner_id_by_group, partner_names):
    """PG dataset 一列（DATASET_SELECT 的欄位）→ v2 dataset 一筆；順序同 API_DATASET_FIELDS，沒有值為 null"""
    row = dict(row)
    rh = row.get('rights_holder')
    row['sourceDatabase'] = to_source_database(rh) if rh else None   # [P2-2-REMOVE]
    pid = partner_id_by_group.get(row.get('group')) or None
    row['tbiaPartnerID'] = pid
    row['partnerName'] = (partner_names.get(str(pid)) or None) if pid else None
    for f in ('datasetDateStart', 'datasetDateEnd'):
        row[f] = format_ymd(row.get(f))
    return {f: (None if _empty(row.get(f)) else row.get(f)) for f in API_DATASET_FIELDS}


# ---- map（5.3） ----
# 網格大小（公里）→ boundedBy 經緯度最大跨度（度），同 v1 check_grid_bound 與 user.html
GRID_MAX_SPAN = {1: 1, 5: 10, 10: 20, 100: 40}


def parse_year(value):
    """year：yyyy 單一值（該年，v1 是該年以後）或區間，一邊可為 *（API 規格調整 11/17）→ Solr 條件"""
    parts = [p.strip() for p in value.split(',')]
    if len(parts) > 2 or any(p not in ('', '*') and not re.fullmatch(r'\d{4}', p) for p in parts):
        raise ParamError('year', 'Invalid year: 格式為 yyyy 或 yyyy,yyyy')
    if len(parts) == 1:
        if parts[0] in ('', '*'):
            raise ParamError('year')
        return f'year:{int(parts[0])}'
    start, end = (p if p not in ('', '*') else '*' for p in parts)
    if start == '*' and end == '*':
        raise ParamError('year')
    if start != '*' and end != '*' and int(start) > int(end):
        raise ParamError('year', 'Invalid year: 起始年大於結束年')
    return f'year:[{start} TO {end}]'


def map_query(params):
    """map 查詢參數 → (grid, fq)。只有公開版（模糊化網格 grid_N_blurred、公開的縣市），不看金鑰（11/23 Kim）。
    boundedBy、grid 必填；跨度不得超過該網格允許的最大跨度。
    排除 organismQuantity=0（未發現紀錄），與網站地圖相同（v1 API 沒有排除）"""
    v = get_single(params, 'grid')
    if v is None:
        raise ParamError('grid', 'Parameter grid is required')
    if not re.fullmatch(r'\d+', v) or int(v) not in GRID_MAX_SPAN:
        raise ParamError('grid', 'Invalid grid: 只提供 1、5、10、100')
    grid = int(v)

    v = get_single(params, 'boundedBy')
    if v is None:
        raise ParamError('boundedBy', 'Parameter boundedBy is required')
    max_lon, max_lat, min_lon, min_lat = parse_bounded_by(v)
    span = GRID_MAX_SPAN[grid]
    if max_lon - min_lon > span or max_lat - min_lat > span:
        raise ParamError('boundedBy', f'Invalid boundedBy: {grid} 公里網格的經緯度跨度不得超過 {span} 度')

    fq = [f'location_rpt:[{min_lat},{min_lon} TO {max_lat},{max_lon}]', '-organismQuantity:0']
    if v := get_single(params, 'taxonID'):
        fq.append(f'taxonID:{solr_quote(v)}')
    if vals := check_vocab(params, 'taxonGroup', TAXON_GROUPS):
        fq.append(f'taxonGroup:({" OR ".join(solr_quote(g) for g in vals)})')
    if v := get_single(params, 'year'):
        fq.append(parse_year(v))
    for k in ('county', 'municipality'):
        if v := get_single(params, k):
            fq.append(f'{k}:{solr_quote(v)}')
    return grid, fq


# ---- partner（5.4） ----
# 資料來源：manager.Partner。一個夥伴單位可能有多列（同 title、同 tbia_partner_id，D28），以 tbiaPartnerID 合併；
# GBIF（tbia_partner_id 為空）不是夥伴，不列。排序與游標 = 該單位最早一列的 Partner.id（建立順序）

def unique_partners(rows):
    """[(Partner.id, tbia_partner_id, title), ...]（依 Partner.id 排序）→
    [{'order': 最早的 Partner.id, 'tbiaPartnerID', 'partnerName'}]，每個 tbiaPartnerID 一筆"""
    out, seen = [], set()
    for pk, pid, title in sorted(rows, key=lambda r: r[0]):
        if not pid or str(pid) in seen:
            continue
        seen.add(str(pid))
        out.append({'order': pk, 'tbiaPartnerID': str(pid), 'partnerName': title or None})
    return out


def partner_query(partners, params):
    """partners：unique_partners 的結果 → 符合條件的清單（不分頁）。
    tbiaPartnerID 完全比對（單值）；partnerName 部分比對、區分大小寫，只比中文 title（11/23 Kim）"""
    pid = get_single(params, 'tbiaPartnerID')
    name = get_single(params, 'partnerName')
    return [p for p in partners
            if (pid is None or p['tbiaPartnerID'] == pid)
            and (name is None or name in (p['partnerName'] or ''))]


def partner_page(matched, cursor, limit):
    """依 order 分頁：回傳 (本頁, 下一頁游標或 None)。多看 1 筆判斷有沒有下一頁"""
    rest = [p for p in matched if cursor is None or p['order'] > cursor]
    page = rest[:limit]
    next_cursor = page[-1]['order'] if len(rest) > limit else None
    return page, next_cursor


def format_partner(p):
    return {'tbiaPartnerID': p['tbiaPartnerID'], 'partnerName': p['partnerName']}
