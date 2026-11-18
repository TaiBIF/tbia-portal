"""
TBN-TBIA occurrence 查詢共同規格（version 1.01 / 2026.10.29）

- parse_common_query(raw_qs)：解析／驗證共同規格查詢字串（B 方向：TBN → TBIA）
- common_to_tbia(params)：共同規格參數 → TBIA 內部搜尋參數
- tbia_to_common(req_dict)：TBIA 內部搜尋參數 → 共同規格參數（A 方向：TBIA → TBN）

日期：起訖兩端都可單獨使用（只給 from = 起始日（含）以後；只給 to = 結束日（含）以前）。
空間：同時指定 circle 與 polygon 時規格要求須同時符合，本站目前不支援，回錯誤。
"""
import calendar
import math
import re
from datetime import date
from urllib.parse import unquote_plus, urlencode, quote

import requests
import shapely.wkt as wkt
from django.utils.translation import gettext

from conf.settings import SOLR_PREFIX, SOLR_TIMEOUT
from data.utils import (
    get_multi, get_dataset_name, get_tbia_dataset_id, solr_quote, merge_polygons,
    split_group_map, taxon_group_map_c, old_taxon_group_map_c,
    habitat_map, map_occurrence, map_collection, basis_map, to_source_database, param_label,
    normalize_search_params, parse_range, HABITAT_PARAM,
    NATIVENESS_LABELS, PROTECTED_STATUS_LABELS, TYPE_STATUS_LABELS, MEDIA_LABELS,
)
# 本檔自己有 parse_circle（共同規格「經度 緯度 半徑」），網站 v2 的 circle（逗號分隔）用別名
from data.search_params import PROTECTED_STATUS, format_range, parse_circle as parse_v2_circle


TBN_COMMON_SEARCH_URL = 'https://www.tbn.org.tw/commonsearch/occurrence'

# 共同規格英文代碼 → TBIA 物種類群
COMMON_TAXON_GROUP_MAP = {
    'mammals': '哺乳類',
    'birds': '鳥類',
    'reptiles': '爬蟲類',
    'amphibians': '兩棲類',
    'fishes': '魚類',
    'crustaceans': '蝦蟹類',
    'dragonflies': '蜻蛉類',
    'butterflies': '蝶類',
    'moths': '蛾類',
    'beetles': '甲蟲類',
    'other_insects': '其他昆蟲',
    'spiders': '蜘蛛',
    'snails___shells': '蝸牛與貝類',
    'angiosperms': '被子植物',
    'gymnosperms': '裸子植物',
    'ferns': '蕨類植物',
    'mosses': '苔蘚植物',
    'fungi': '真菌',
}
TBIA_TAXON_GROUP_TO_COMMON = {v: k for k, v in COMMON_TAXON_GROUP_MAP.items()}

SINGLE_FIELDS = {
    'taxon_name', 'taxon_id', 'higher_taxon_id', 'is_native', 'is_protected',
    'event_date_from', 'event_date_to', 'county', 'municipality', 'circle', 'polygon',
}
MULTI_FIELDS = {'taxon_group', 'tbia_dataset_id'}
ALL_FIELDS = SINGLE_FIELDS | MULTI_FIELDS
YN_FIELDS = {'is_native', 'is_protected'}

CIRCLE_MAX_RADIUS = 25

# 列舉欄位出現未列出的值時：規格為「必須警告、建議停止」，本站選擇停止，避免忽略該值後查詢範圍變大
STOP_ON_INVALID_ENUM = True

# TBN 尚未支援 tbia_dataset_id（2026.10.29）。False 時 A 方向把資料集列為不可對應、不帶進連結；TBN 支援後改 True
TBN_SUPPORTS_DATASET = False

_DATE_PATTERNS = (
    ('year', re.compile(r'^(\d{4})$')),
    ('month', re.compile(r'^(\d{4})-(\d{2})$')),
    ('day', re.compile(r'^(\d{4})-(\d{2})-(\d{2})$')),
)


class CommonQueryError(ValueError):
    pass


# ---------------------------------------------------------------------------
# 共用小工具
# ---------------------------------------------------------------------------

def _is_blank(val):
    """未指定值：field= 與 field="" 均視為不使用該條件"""
    return val is None or val == '' or val == '""'


def split_multi_value(val):
    """
    依共同規格切分多值集合。
    - 逗號分隔；元素可用雙引號包住，內含 \\" 與 \\\\ 跳脫
    - 空元素、引號不成對 → CommonQueryError
    """
    items = []
    i, n = 0, len(val)
    while True:
        if i < n and val[i] == '"':
            # 引號元素
            i += 1
            buf = []
            closed = False
            while i < n:
                c = val[i]
                if c == '\\' and i + 1 < n and val[i + 1] in ('"', '\\'):
                    buf.append(val[i + 1])
                    i += 2
                elif c == '"':
                    closed = True
                    i += 1
                    break
                else:
                    buf.append(c)
                    i += 1
            if not closed:
                raise CommonQueryError(gettext('引號不成對'))
            item = ''.join(buf)
            if i < n and val[i] != ',':
                raise CommonQueryError(gettext('引號不成對'))
        else:
            j = val.find(',', i)
            j = n if j == -1 else j
            item = val[i:j]
            if '"' in item:
                raise CommonQueryError(gettext('引號不成對'))
            i = j
        if item.strip() == '':
            raise CommonQueryError(gettext('多值集合包含空元素'))
        items.append(item.strip())
        if i >= n:
            break
        i += 1  # 跳過逗號
        if i >= n:
            raise CommonQueryError(gettext('多值集合包含空元素'))
    return items


def quote_multi_item(item):
    """組多值集合時，含逗號／引號／反斜線的值要用雙引號包住"""
    if any(c in item for c in ',"\\'):
        return '"' + item.replace('\\', '\\\\').replace('"', '\\"') + '"'
    return item


def parse_event_date(val, is_end):
    """回傳 (精度, 展開後的 date)。起始端展開為第一天，結束端展開為最後一天。"""
    for precision, pattern in _DATE_PATTERNS:
        if m := pattern.match(val):
            parts = [int(x) for x in m.groups()]
            try:
                if precision == 'year':
                    d = date(parts[0], 12, 31) if is_end else date(parts[0], 1, 1)
                elif precision == 'month':
                    last = calendar.monthrange(parts[0], parts[1])[1]
                    d = date(parts[0], parts[1], last if is_end else 1)
                else:
                    d = date(*parts)
            except ValueError:
                raise CommonQueryError(gettext('無效日期：%(value)s') % {'value': val})
            return precision, d
    raise CommonQueryError(gettext('無效日期：%(value)s') % {'value': val})


def normalize_tai(val):
    """台／臺 視為等價，本站統一使用「臺」"""
    return val.replace('台', '臺')


def _check_lon_lat(lon, lat):
    if not (math.isfinite(lon) and math.isfinite(lat)) or not (-180 <= lon <= 180) or not (-90 <= lat <= 90):
        raise CommonQueryError(gettext('空間座標超出經緯度範圍'))


def parse_circle(val):
    parts = val.split()
    if len(parts) != 3:
        raise CommonQueryError(gettext('circle 須為「經度 緯度 半徑」三個數值'))
    try:
        lon, lat, r = (float(p) for p in parts)
    except ValueError:
        raise CommonQueryError(gettext('circle 須為「經度 緯度 半徑」三個數值'))
    _check_lon_lat(lon, lat)
    if not math.isfinite(r) or not (0 < r <= CIRCLE_MAX_RADIUS):
        raise CommonQueryError(gettext('circle 半徑須符合 0 < r ≤ %(max)s') % {'max': CIRCLE_MAX_RADIUS})
    return lon, lat, r


def parse_polygon(val):
    """回傳 shapely Polygon / MultiPolygon；格式錯誤、型別不符、空幾何、無效幾何 → CommonQueryError"""
    if not re.match(r'^\s*(MULTI)?POLYGON\b', val, re.IGNORECASE):
        raise CommonQueryError(gettext('polygon 僅接受完整 WKT 的 POLYGON／MULTIPOLYGON'))
    try:
        geom = wkt.loads(val)
    except Exception:
        raise CommonQueryError(gettext('polygon WKT 格式錯誤'))
    if geom.geom_type not in ('Polygon', 'MultiPolygon'):
        raise CommonQueryError(gettext('polygon 僅接受 POLYGON／MULTIPOLYGON'))
    if geom.is_empty:
        raise CommonQueryError(gettext('polygon 為空幾何'))
    minx, miny, maxx, maxy = geom.bounds
    _check_lon_lat(minx, miny)
    _check_lon_lat(maxx, maxy)
    if not geom.is_valid:
        raise CommonQueryError(gettext('polygon 為無效幾何（例如自相交）'))
    return geom


# ---------------------------------------------------------------------------
# B 方向：共同規格 → TBIA
# ---------------------------------------------------------------------------

def parse_common_query(raw_qs):
    """
    解析原始查詢字串（request.META['QUERY_STRING']）。
    回傳 (params, warnings, errors)；errors 不為空時必須停止整筆查詢。
    params 只包含有使用的條件，多值欄位為 list。
    """
    params, warnings, errors = {}, [], []
    invalid_enum = False

    # 1. 拆參數、檢查重複（不分大小寫）
    raw = {}
    seen = set()
    for pair in (raw_qs or '').split('&'):
        if pair == '':
            continue
        k, _, v = pair.partition('=')
        k = unquote_plus(k).strip().lower()
        v = unquote_plus(v)
        if k in seen:
            errors.append(gettext('重複參數：%(field)s') % {'field': k})
            continue
        seen.add(k)
        raw[k] = v

    for k in raw:
        if k not in ALL_FIELDS:
            warnings.append(gettext('不支援的欄位：%(field)s') % {'field': k})

    # 2. 各欄位
    for k, v in raw.items():
        if k not in ALL_FIELDS or _is_blank(v):
            continue
        try:
            if k in MULTI_FIELDS:
                params[k] = split_multi_value(v)
            elif k in YN_FIELDS:
                vv = v.strip().lower()
                if vv in ('y', 'n'):
                    params[k] = vv
                else:
                    warnings.append(gettext('%(field)s 不接受的值：%(value)s') % {'field': k, 'value': v})
                    invalid_enum = True
            elif k in ('county', 'municipality'):
                params[k] = normalize_tai(v.strip())
            else:
                params[k] = v.strip()
        except CommonQueryError as e:
            errors.append(gettext('%(field)s：%(msg)s') % {'field': k, 'msg': e})

    # taxon_group 列舉值檢查（不分大小寫）
    if tg := params.get('taxon_group'):
        tg = [t.lower() for t in tg]
        if invalid := [t for t in tg if t not in COMMON_TAXON_GROUP_MAP]:
            warnings.append(gettext('%(field)s 不接受的值：%(value)s') % {'field': 'taxon_group', 'value': ','.join(invalid)})
            invalid_enum = True
        params['taxon_group'] = [t for t in tg if t in COMMON_TAXON_GROUP_MAP]
        if not params['taxon_group']:
            params.pop('taxon_group')

    # 3. 日期
    d_from, d_to = params.get('event_date_from'), params.get('event_date_to')
    try:
        p_from = parse_event_date(d_from, is_end=False) if d_from else None
        p_to = parse_event_date(d_to, is_end=True) if d_to else None
        if p_from and p_to:
            if p_from[0] != p_to[0]:
                raise CommonQueryError(gettext('起迄日期精度不同'))
            if p_to[1] < p_from[1]:
                raise CommonQueryError(gettext('結束日期早於起始日期'))
        if p_from:
            params['event_date_from'] = p_from[1]
        if p_to:
            params['event_date_to'] = p_to[1]
    except CommonQueryError as e:
        errors.append(gettext('%(field)s：%(msg)s') % {'field': gettext('日期'), 'msg': e})

    # 4. 行政區
    if params.get('municipality') and not params.get('county'):
        errors.append(gettext('指定 municipality 時必須指定 county'))

    # 5. 空間
    if params.get('circle'):
        try:
            params['circle'] = parse_circle(params['circle'])
        except CommonQueryError as e:
            errors.append(gettext('%(field)s：%(msg)s') % {'field': 'circle', 'msg': e})
    if params.get('polygon'):
        try:
            params['polygon'] = parse_polygon(params['polygon'])
        except CommonQueryError as e:
            errors.append(gettext('%(field)s：%(msg)s') % {'field': 'polygon', 'msg': e})
    if params.get('circle') and params.get('polygon'):
        errors.append(gettext('本站不支援同時指定 circle 與 polygon'))

    if STOP_ON_INVALID_ENUM and invalid_enum:
        errors.append(gettext('列舉欄位包含不接受的值，停止查詢'))

    return params, warnings, errors


def common_to_tbia(params):
    """parse_common_query 的結果 → TBIA /search/occurrence 參數（list of tuples，支援多值）"""
    out = []
    # 3.4：輸出 v2 網站參數
    simple = {'taxon_name': 'name', 'taxon_id': 'taxonID', 'higher_taxon_id': 'higherTaxonID',
              'county': 'county', 'municipality': 'municipality'}
    for k, tbia_k in simple.items():
        if v := params.get(k):
            out.append((tbia_k, v))

    if v := params.get('is_native'):
        out += [('nativeness', 'native')] if v == 'y' else [('nativeness', x) for x in ('naturalized', 'invasive', 'cultured')]
    if v := params.get('is_protected'):
        if v == 'y':
            out += [('protectedStatus', x) for x in PROTECTED_STATUS]
        else:
            # 「非保育類」已停止提供：照舊參數帶過去，搜尋頁 normalize 時會移除並提示使用者
            out.append(('is_protected', 'n'))

    for t in params.get('taxon_group', []):
        out.append(('taxonGroup', COMMON_TAXON_GROUP_MAP[t]))

    for d in params.get('tbia_dataset_id', []):
        out.append(('tbiaDatasetID', d))

    s, e = params.get('event_date_from'), params.get('event_date_to')
    if s or e:
        out.append(('eventDate', format_range(s.strftime('%Y%m%d') if s else None, e.strftime('%Y%m%d') if e else None)))

    if c := params.get('circle'):
        lon, lat, r = c
        # .10g 讓 1.0 → '1'，才能對上前端半徑選單的值
        out.append(('circle', f'{lon:.10g},{lat:.10g},{r:.10g}'))
    elif g := params.get('polygon'):
        # 前端以多個 polygon 參數表示，逐一拆開（孔洞保留在各自的 Polygon 內）
        polys = g.geoms if g.geom_type == 'MultiPolygon' else [g]
        for p in polys:
            out.append(('polygon', p.wkt))

    return out


# ---------------------------------------------------------------------------
# A 方向：TBIA → 共同規格（取代原 create_tbn_query）
# ---------------------------------------------------------------------------

def _to_iso_date(val):
    try:
        return date.fromisoformat(val.strip()).isoformat()
    except (ValueError, AttributeError):
        return None


def tbia_to_common(req_dict):
    """
    回傳 (common_params, query_str_list, error_str_list)
    common_params：可對應的共同規格參數（dict）
    query_str_list：可對應查詢（顯示用）
    error_str_list：不可對應查詢（顯示用）
    """
    common = {}
    query_str_list, error_str_list = [], []
    req_dict = normalize_search_params(req_dict)  # 3.4：讀 v2 網站參數（舊參數也先轉換）

    def ok(label, val):
        query_str_list.append('{} = {}'.format(gettext(label), val))

    def ng(label, val=None):
        error_str_list.append(gettext(label) if val is None else '{} = {}'.format(gettext(label), val))

    # 學名相關
    if val := req_dict.get('name'):
        val = re.sub(' +', ' ', val).strip()
        if val:
            common['taxon_name'] = val
            ok('學名/中文名/中文別名/同物異名/誤用名', val)

    if val := req_dict.get('taxonID'):
        if val != 'undefined':
            common['taxon_id'] = val.strip()
            ok(map_occurrence['taxonID'], val.strip())

    if val := req_dict.get('higherTaxonID'):
        common['higher_taxon_id'] = val
        display = val
        try:
            response = requests.get(f'{SOLR_PREFIX}taxa/select', params={'q': f'id:{solr_quote(val)}'}, timeout=SOLR_TIMEOUT)
            if response.status_code == 200 and (docs := response.json()['response']['docs']):
                data = docs[0]
                display = f"{data.get('scientificName')} {data.get('common_name_c') or ''}".strip()
        except requests.RequestException:
            pass
        ok('較高分類群', display)

    # 物種類群：展開父類群、相容英文舊值
    groups = req_dict.getlist('taxonGroup')   # normalize 已展開父類群、轉換英文舊值
    if valid := [g for g in groups if g in TBIA_TAXON_GROUP_TO_COMMON]:
        common['taxon_group'] = ','.join(TBIA_TAXON_GROUP_TO_COMMON[g] for g in valid)
        ok('物種類群', ','.join(gettext(g) for g in valid))
    if invalid := [g for g in groups if g not in TBIA_TAXON_GROUP_TO_COMMON]:
        ng('物種類群', ','.join(gettext(g) for g in invalid))

    # 原生性／保育類：共同規格只有是／否
    if vals := req_dict.getlist('nativeness'):
        label_val = '、'.join(gettext(NATIVENESS_LABELS.get(v, v)) for v in vals)
        if set(vals) == {'native'}:
            common['is_native'] = 'y'
            ok('原生性', label_val)
        elif set(vals) == {'naturalized', 'invasive', 'cultured'}:
            common['is_native'] = 'n'
            ok('原生性', label_val)
        else:
            ng('原生性', label_val)
    if vals := req_dict.getlist('protectedStatus'):
        label_val = '、'.join(gettext(PROTECTED_STATUS_LABELS.get(v, v)) for v in vals)
        if set(vals) == set(PROTECTED_STATUS):
            common['is_protected'] = 'y'
            ok('保育類等級', label_val)
        else:
            ng('保育類等級', label_val)

    # 日期（eventDate=YYYYMMDD 區間，一邊可為 *）
    if r := parse_range(req_dict.get('eventDate')):
        for d8, common_key, label in ((r[0], 'event_date_from', '起始日期'), (r[1], 'event_date_to', '結束日期')):
            if d8:
                d = f'{d8[:4]}-{d8[4:6]}-{d8[6:]}'
                common[common_key] = d
                ok(label, d)

    # 行政區
    if county := req_dict.get('county'):
        common['county'] = county
        ok('縣市', county)
        if municipality := req_dict.get('municipality'):
            common['municipality'] = municipality
            ok('鄉鎮市區', municipality)
    elif municipality := req_dict.get('municipality'):
        ng('鄉鎮市區', municipality)

    # 資料集
    if d_ids := req_dict.getlist('tbiaDatasetID'):
        tbia_ids, names = [], []
        for d in d_ids:
            if tid := get_tbia_dataset_id(d):
                tbia_ids.append(tid)
                names.append(get_dataset_name(d) or tid)
            else:
                ng('資料集名稱', d)
        if tbia_ids:
            if TBN_SUPPORTS_DATASET:
                common['tbia_dataset_id'] = ','.join(quote_multi_item(t) for t in tbia_ids)
                ok('資料集名稱', ','.join(names))
            else:
                ng('資料集名稱', ','.join(names))

    # 空間
    if g_list := req_dict.getlist('polygon'):
        try:
            geom = merge_polygons(g_list)
            if geom.is_empty or not geom.is_valid:
                raise ValueError
            common['polygon'] = geom.wkt
            ok('地圖框選', geom.wkt)
        except Exception:
            ng('地圖框選', ','.join(g_list))
    elif req_dict.get('geojson_id'):
        ng('上傳Polygon')
    elif c_raw := req_dict.get('circle'):
        lon_s, lat_s, r_s = (c_raw.split(',') + ['', '', ''])[:3]
        label_val = f"{gettext('半徑')} {r_s} KM {gettext('中心點經度')} {lon_s} {gettext('中心點緯度')} {lat_s}"
        c = parse_v2_circle(c_raw)
        if c and c[2] <= CIRCLE_MAX_RADIUS:
            lon, lat, r = c
            common['circle'] = f'{lon:.10g} {lat:.10g} {r:.10g}'
            ok('圓中心框選', label_val)
        else:
            ng('圓中心框選', label_val)

    # 共同規格沒有的欄位
    if has_media := req_dict.get('hasMedia'):
        ng('有無多媒體', '、'.join(gettext(MEDIA_LABELS.get(v, v)) for v in (req_dict.getlist('mediaType') or [has_media])))

    if hb_vals := req_dict.getlist('taxonGroupByHabitat'):
        ng('物種類群（以棲地區分）', ','.join(gettext(habitat_map.get(HABITAT_PARAM.get(v, v), v)) for v in hb_vals))

    if val := req_dict.get('taxonRank'):
        ng('鑑定層級', gettext('種下') if val == 'Infraspecies' else gettext(map_occurrence.get(val.lower(), val)))

    if l_list := get_multi(req_dict, 'locality'):
        ng('出現地', ','.join(l_list))

    if r_list := req_dict.getlist('sourceDatabase'):
        ng('來源資料庫', ','.join(r_list))

    if val := req_dict.get('basisOfRecord'):
        ng('紀錄類型', gettext(basis_map.get(val, val)))

    for i in ['recordedBy', 'resourceContacts', 'preparations', 'occurrenceID', 'catalogNumber',
              'recordNumber', 'organismQuantity']:
        if (val := req_dict.get(i)) and val != 'undefined':
            ng(param_label(i, map_collection) or i, gettext(val))
    if vals := req_dict.getlist('typeStatus'):
        ng('標本類型', '、'.join(gettext(TYPE_STATUS_LABELS.get(v, v)) for v in vals))

    return common, query_str_list, error_str_list


def build_common_url(base_url, common_params):
    # 空白用 %20（circle 內含空白），逗號等保留給多值語法的字元照常編碼
    return base_url + '?' + urlencode(common_params, quote_via=quote)