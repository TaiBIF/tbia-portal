"""網站搜尋參數（3.4，D20）：v2 參數名稱與值、舊寫法轉換、停用條件、存檔白名單。

[COMPAT-KEEP] 舊網址、書籤、外部連結、已存查詢字串（SearchQuery / SearchStat）都靠這裡轉成標準形式，永久保留。
- normalize_pairs：舊參數名 / 舊值 → v2 標準形式；不認得的參數原樣保留（分頁、排序等請求參數照常傳下去）
- canonical_pairs：normalize 後只留查詢條件（白名單）並丟掉不合法的值，存進資料庫一律用它
只用標準函式庫與 data.fields，單元測試不需要 Django（tests/test_search_params.py）。
參數規格見交接文件「API 規格調整」與 user.html；網站與 API 用同一套名稱與值。
"""
import ast
import re
from urllib.parse import parse_qsl, unquote

from data.fields import to_v2_field

# ---- 從 data/utils.py 移過來的對照（utils 仍 re-export，原本的 import 不用改） ----
# 舊類群名稱（英文、舊群名）→ 新類群
old_taxon_group_map_c = {
    'Plants': '維管束植物',
    'Insects': '昆蟲',
    'Vascular Plants': '維管束植物',
    'Ferns': '蕨類植物',
}

taxon_group_map_c = {
    'Birds': '鳥類',
    'Reptiles': '爬蟲類',
    'Mammals': '哺乳類',
    'Beetles': '甲蟲類',
    'Fishes': '魚類',
    'Amphibians': '兩棲類',
    'Moths': '蛾類',
    'Butterflies': '蝶類',
    'Spiders': '蜘蛛',
    'Dragonflies': '蜻蛉類',
    'Snails & Shells': '蝸牛與貝類',
    'Other Insects': '其他昆蟲',
    'Crustaceans': '蝦蟹類',
    'Gymnosperms': '裸子植物',
    'Angiosperms': '被子植物',
    'Ferns': '蕨類植物',
    'Mosses': '苔蘚植物',
    'Fungi': '真菌',
    'Vascular Plants': '維管束植物',
    'Insects': '昆蟲',
    'Algae': '藻類',
    'Viruses': '病毒',
    'Bacteria': '細菌',
}

# 舊父類群拆成新類群
split_group_map = {
    '昆蟲': ['甲蟲類', '蛾類', '蝶類', '蜻蛉類', '其他昆蟲'],
    '維管束植物': ['被子植物', '裸子植物', '蕨類植物'],
}

# v2 來源資料庫名稱（11/12 定案）：舊 rightsHolder → 新 sourceDatabase，只列有改名的
# 與 datahub scripts/utils/export.py 的 SOURCE_DATABASE_MAP 相同，P2-3 改由 Partner.info[].dbname 取得
SOURCE_DATABASE_RENAME = {
    '中央研究院生物多樣性中心動物標本館': '中央研究院動物標本館 ASIZ',
    '中央研究院生物多樣性中心植物標本資料庫': '中央研究院植物標本館 HAST',
    '國家海洋資料庫及共享平台': '國家海洋資料庫及共享平臺',
    '國立海洋生物博物館生物典藏管理系統': '生物典藏管理系統',
    '科博典藏 (NMNS Collection)': '科博典藏',
    '國立臺灣博物館典藏': '國立臺灣博物館生物典藏資料',
    '愛自然-臺灣(iNaturalist Taiwan)': '愛自然-臺灣',
    '中油生態地圖': '中油生態保育資料庫',
}


def to_source_database(name):
    """舊 rightsHolder 名稱 → 新 sourceDatabase 名稱；已是新名稱或未改名的原樣回傳"""
    return SOURCE_DATABASE_RENAME.get(name, name)


# ---- v2 控制詞彙（同 user.html） ----
TAXON_GROUPS = ['鳥類', '爬蟲類', '哺乳類', '甲蟲類', '魚類', '兩棲類', '蛾類', '蝶類', '蜘蛛', '蜻蛉類',
                '蝸牛與貝類', '其他昆蟲', '蝦蟹類', '裸子植物', '被子植物', '蕨類植物', '苔蘚植物',
                '真菌', '藻類', '病毒', '細菌']
# 參數值 → Solr 欄位（user.html 另有 fossil，Solr 沒有對應欄位，網站與查詢都不提供）
HABITAT_PARAM = {'terrestrial': 'is_terrestrial', 'freshWater': 'is_freshwater',
                 'brackish': 'is_brackish', 'marine': 'is_marine'}
TAXON_RANKS = ['Kingdom', 'Phylum', 'Class', 'Order', 'Family', 'Genus', 'Species', 'Infraspecies']
NATIVENESS = ['native', 'naturalized', 'invasive', 'cultured']
PROTECTED_STATUS = ['I', 'II', 'III', 'CHPA']
TYPE_STATUS = ['HOLOTYPE', 'PARATYPE', 'ISOTYPE', 'ALLOTYPE', 'SYNTYPE', 'LECTOTYPE',
               'PARALECTOTYPE', 'NEOTYPE', 'TOPOTYPE']
MEDIA_TYPES = ['image', 'video', 'audio']
BASIS_OF_RECORD = ['HumanObservation', 'MachineObservation', 'PreservedSpecimen', 'MaterialSample',
                   'LivingSpecimen', 'FossilSpecimen', 'MaterialCitation', 'MaterialEntity', 'Taxon',
                   'Occurrence', 'Event']
GRID_LEVELS = ['grid_1', 'grid_5', 'grid_10', 'grid_100']
CIRCLE_MAX_KM = 50

# ---- 參數名稱 ----
# 舊參數名 → v2（值不用轉換的）
RENAME = {
    'rightsHolder': 'sourceDatabase',
    'preservation': 'preparations',
    'datasetName': 'tbiaDatasetID',
    'higherTaxa': 'higherTaxonID',
    'habitat': 'taxonGroupByHabitat',
    'bioGroup': 'taxonGroup',
}
# 多值參數（網站用重複參數；API 式的半形逗號也接受，見 COMMA_PARAMS）
MULTI_PARAMS = ['taxonGroup', 'taxonGroupByHabitat', 'nativeness', 'protectedStatus', 'typeStatus', 'mediaType',
                'sourceDatabase', 'tbiaDatasetID', 'locality', 'polygon']
# 值可以用半形逗號分隔多值的參數（locality、polygon 的值本身可能有逗號，不拆）
COMMA_PARAMS = {'taxonGroup', 'taxonGroupByHabitat', 'nativeness', 'protectedStatus', 'typeStatus', 'mediaType',
                'sourceDatabase', 'tbiaDatasetID'}

# 存進資料庫的查詢條件白名單（其餘：分頁、排序、表單欄位、追蹤參數、掃描工具亂填的參數一律不存）
SEARCH_PARAMS = [
    'record_type',
    'name', 'taxonID', 'higherTaxonID', 'taxonGroup', 'taxonGroupByHabitat', 'taxonRank',
    'nativeness', 'protectedStatus', 'hasMedia', 'mediaType',
    'sourceDatabase', 'tbiaDatasetID', 'recordedBy', 'resourceContacts', 'preparations',
    'occurrenceID', 'catalogNumber', 'recordNumber', 'organismQuantity', 'basisOfRecord',
    'sensitiveCategory', 'typeStatus',
    'county', 'municipality', 'locality', 'eventDate',
    'circle', 'polygon', 'geojson_id', 'current_grid_level', 'current_grid',
    # 全站搜尋
    'keyword', 'key', 'value', 'scientific_name', 'get_record',
]

# 舊的地圖 / 日期 / 多媒體參數（轉換後移除）
_OLD_GEO = ('geo_type', 'center_lat', 'center_lon', 'circle_radius')
_OLD_DATE = ('start_date', 'end_date')

_DATE8 = re.compile(r'^\d{8}$')
_NUM = re.compile(r'^-?\d+(\.\d+)?$')


def _expand_literal(v):
    """DB 既有舊格式 key=['A','B'] 展開成多值"""
    if isinstance(v, str) and v.startswith('[') and v.endswith(']'):
        try:
            lit = ast.literal_eval(v)
            if isinstance(lit, list):
                return [str(x) for x in lit]
        except (ValueError, SyntaxError):
            pass
    return [v]


def _to_date8(v):
    """YYYY-MM-DD / YYYYMMDD → YYYYMMDD；不合法回傳 None"""
    v = (v or '').strip()
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}', v):
        v = v.replace('-', '')
    if not _DATE8.match(v):
        return None
    y, m, d = int(v[:4]), int(v[4:6]), int(v[6:])
    if not (1 <= m <= 12 and 1 <= d <= 31 and y >= 1):
        return None
    return v


def parse_range(value):
    """區間值 'A,B'（A / B 可為 *）或單一值 → (start, end)，單一值為 (v, v)；不合法回傳 None。
    用於 eventDate（YYYYMMDD）；API 的 created / modified / year 共用同一寫法（5.2 / 5.3）"""
    value = (value or '').strip()
    if ',' not in value:
        d = _to_date8(value)
        return (d, d) if d else None
    parts = value.split(',')
    if len(parts) != 2:
        return None
    out = []
    for p in parts:
        p = p.strip()
        if p in ('', '*'):
            out.append(None)
        else:
            d = _to_date8(p)
            if not d:
                return None
            out.append(d)
    if out[0] is None and out[1] is None:
        return None
    if out[0] and out[1] and out[0] > out[1]:
        return None
    return tuple(out)


def format_range(start, end):
    if start and end and start == end:
        return start
    return f'{start or "*"},{end or "*"}'


def parse_circle(value):
    """'經度,緯度,半徑（公里）' → (lon, lat, r) 浮點數；不合法回傳 None（0 < r ≤ 50）"""
    parts = [p.strip() for p in (value or '').split(',')]
    if len(parts) != 3 or not all(_NUM.match(p) for p in parts):
        return None
    lon, lat, r = (float(p) for p in parts)
    if not (-180 <= lon <= 180 and -90 <= lat <= 90 and 0 < r <= CIRCLE_MAX_KM):
        return None
    return lon, lat, r


def _num_str(v):
    v = (v or '').strip()
    return v if _NUM.match(v) else None


class _Multi:
    """保持參數第一次出現順序的多值 dict"""
    def __init__(self):
        self.d = {}

    def add(self, k, v):
        self.d.setdefault(k, []).append(v)

    def get(self, k):
        vals = self.d.get(k) or []
        return vals[0] if vals else None

    def getlist(self, k):
        return list(self.d.get(k) or [])

    def setlist(self, k, vals):
        if vals:
            self.d[k] = list(vals)
        else:
            self.d.pop(k, None)

    def pop(self, k):
        return self.d.pop(k, None)

    def __contains__(self, k):
        return k in self.d

    def pairs(self):
        return [(k, v) for k, vals in self.d.items() for v in vals]


def _dedupe(vals):
    return list(dict.fromkeys(v for v in vals if v not in (None, '')))


def normalize_pairs(pairs):
    """參數 (key, value) 清單 → (標準形式的 pairs, removed, notes)。
    removed：已停用、自動移除的條件說明；notes：轉換後結果可能和原本略有不同的提示。兩者都是要顯示給使用者的中文字串（gettext 由呼叫端處理）"""
    removed, notes = [], []
    m = _Multi()
    for k, v in pairs:
        if k == 'search_str':       # 舊全站搜尋下載把條件包在 search_str（manager 讀取時攤平）
            for ik, iv in parse_qsl(v or '', keep_blank_values=True):
                for x in _expand_literal(iv):
                    m.add(ik, x)
            continue
        for x in _expand_literal(v):
            m.add(RENAME.get(k, k), x)

    # 逗號分隔的多值
    for k in COMMA_PARAMS:
        if k in m:
            vals = []
            for v in m.getlist(k):
                vals.extend(s.strip() for s in v.split(','))
            m.setlist(k, vals)

    # 舊 has_image → hasMedia / mediaType（舊值為單一值；前端多選時也走這裡，見 search_params.js）
    if 'has_image' in m:
        olds = [(v or '').strip().lower() for v in m.pop('has_image')]
        if 'hasMedia' not in m:
            types = [v for v in MEDIA_TYPES if v in olds]
            if 'n' in olds or 'false' in olds:
                m.add('hasMedia', 'false')
            elif types:
                m.add('hasMedia', 'true')
                if 'mediaType' not in m:
                    for t in types:
                        m.add('mediaType', t)
            elif 'y' in olds or 'true' in olds:
                m.add('hasMedia', 'true')
    if 'hasMedia' in m:
        v = (m.get('hasMedia') or '').strip().lower()
        v = {'y': 'true', 'n': 'false'}.get(v, v)
        m.setlist('hasMedia', [v] if v in ('true', 'false') else [])
    # mediaType 可多選（11/17）；需 hasMedia=true，三種全選等於「有任何多媒體」（不限類型）
    if 'mediaType' in m:
        types = [v for v in MEDIA_TYPES if v in {x.strip().lower() for x in m.getlist('mediaType')}]
        if types and m.get('hasMedia') != 'false':
            m.setlist('hasMedia', ['true'])
            m.setlist('mediaType', types if len(types) < len(MEDIA_TYPES) else [])
        else:
            m.pop('mediaType')

    # 舊 is_native → nativeness
    if 'is_native' in m:
        v = (m.pop('is_native')[0] or '').strip().lower()
        if 'nativeness' not in m:
            if v in ('y', 'true'):
                m.add('nativeness', 'native')
            elif v in ('n', 'false'):
                for x in ('naturalized', 'invasive', 'cultured'):
                    m.add('nativeness', x)
    if 'nativeness' in m:
        m.setlist('nativeness', [v for v in _dedupe(s.strip().lower() for s in m.getlist('nativeness')) if v in NATIVENESS])

    # 舊 is_protected → protectedStatus；「非保育類」API 沒有對應值，已停止提供（11/17 決定）
    if 'is_protected' in m:
        v = (m.pop('is_protected')[0] or '').strip().lower()
        if 'protectedStatus' not in m:
            if v in ('y', 'true'):
                for x in PROTECTED_STATUS:
                    m.add('protectedStatus', x)
            elif v in ('n', 'false'):
                removed.append('是否為保育類：否')
    if 'protectedStatus' in m:
        m.setlist('protectedStatus', [v for v in _dedupe(s.strip().upper() for s in m.getlist('protectedStatus')) if v in PROTECTED_STATUS])

    # typeStatus：改用 9 個控制詞彙；舊的「一般」「模式」已停止提供（11/17 決定）
    if 'typeStatus' in m:
        vals = []
        for v in m.getlist('typeStatus'):
            v = v.strip()
            if '%' in v:
                v = unquote(v)
            if v in ('一般', '模式'):
                removed.append(f'標本類型：{v}')
            elif v.upper() in TYPE_STATUS:
                vals.append(v.upper())
        m.setlist('typeStatus', _dedupe(vals))

    # taxonGroup：英文 / 舊群名 → 新類群，舊父類群拆開
    if 'taxonGroup' in m:
        vals = []
        for v in m.getlist('taxonGroup'):
            v = v.strip()
            v = taxon_group_map_c.get(v) or old_taxon_group_map_c.get(v) or v
            vals.extend(split_group_map.get(v, [v]))
        m.setlist('taxonGroup', [v for v in _dedupe(vals) if v in TAXON_GROUPS])

    # taxonGroupByHabitat：舊值是 Solr 欄位名（is_marine）
    if 'taxonGroupByHabitat' in m:
        old = {f: p for p, f in HABITAT_PARAM.items()}
        vals = [old.get(v.strip(), v.strip()) for v in m.getlist('taxonGroupByHabitat')]
        m.setlist('taxonGroupByHabitat', [v for v in _dedupe(vals) if v in HABITAT_PARAM])

    # taxonRank：首字大寫；舊值 sub / infraspecies → Infraspecies
    if 'taxonRank' in m:
        v = (m.get('taxonRank') or '').strip()
        lower = {r.lower(): r for r in TAXON_RANKS}
        lower.update({'sub': 'Infraspecies'})
        v = lower.get(v.lower())
        m.setlist('taxonRank', [v] if v else [])

    if 'sourceDatabase' in m:
        m.setlist('sourceDatabase', _dedupe(to_source_database(v.strip()) for v in m.getlist('sourceDatabase')))
    for k in ('tbiaDatasetID', 'locality', 'polygon'):
        if k in m:
            m.setlist(k, _dedupe(v.strip() for v in m.getlist(k)))

    # 舊 start_date / end_date（YYYY-MM-DD）→ eventDate（YYYYMMDD 區間，一邊可為 *）
    if any(k in m for k in _OLD_DATE):
        s = _to_date8(m.get('start_date'))
        e = _to_date8(m.get('end_date'))
        for k in _OLD_DATE:
            m.pop(k)
        if 'eventDate' not in m and (s or e):
            if not (s and e and s > e):
                m.add('eventDate', format_range(s, e))
    if 'eventDate' in m:
        r = parse_range(m.get('eventDate'))
        m.setlist('eventDate', [format_range(*r)] if r else [])

    # 舊地圖參數 → circle / polygon / geojson_id（v2 不再需要 geo_type）
    if any(k in m for k in _OLD_GEO):
        geo_type = (m.get('geo_type') or '').strip()
        lon, lat, r = (_num_str(m.get(k)) for k in ('center_lon', 'center_lat', 'circle_radius'))
        for k in _OLD_GEO:
            m.pop(k)
        if geo_type == 'circle':
            m.pop('polygon')
            m.pop('geojson_id')
            if 'circle' not in m and lon and lat and r:
                m.add('circle', f'{lon},{lat},{r}')
        elif geo_type == 'map':
            m.pop('geojson_id')
        elif geo_type == 'polygon':
            m.pop('polygon')
        else:                       # 沒有 geo_type：舊程式不會套用任何地圖條件
            m.pop('polygon')
            m.pop('geojson_id')
    if 'circle' in m:
        c = parse_circle(m.get('circle'))
        m.setlist('circle', [m.get('circle').replace(' ', '')] if c else [])
    if 'geojson_id' in m:
        v = (m.get('geojson_id') or '').strip()
        m.setlist('geojson_id', [v] if re.fullmatch(r'[\w-]+', v) else [])

    # 全站搜尋的 key 是欄位名稱：舊欄位名換成 v2
    if 'key' in m:
        m.setlist('key', [to_v2_field(m.get('key'))])

    return m.pairs(), removed, notes


def canonical_pairs(pairs):
    """存進資料庫用：normalize 後只留查詢條件白名單，丟掉空值與不合法的值"""
    out, removed, notes = normalize_pairs(pairs)
    keep = set(SEARCH_PARAMS)
    clean = []
    for k, v in out:
        if k not in keep or v in (None, ''):
            continue
        v = v.strip()
        if not v:
            continue
        if k == 'record_type' and v not in ('occ', 'col'):
            continue
        if k == 'basisOfRecord' and v not in BASIS_OF_RECORD:
            continue
        if k == 'current_grid_level' and v not in GRID_LEVELS:
            continue
        if k == 'key' and not re.fullmatch(r'\w+', v):
            continue
        if k == 'organismQuantity' and not _NUM.match(v):
            continue
        clean.append((k, v))
    # 只有網格編號沒有層級（或反之）時兩個都不留
    keys = {k for k, _ in clean}
    if ('current_grid_level' in keys) != ('current_grid' in keys):
        clean = [(k, v) for k, v in clean if k not in ('current_grid_level', 'current_grid')]
    return clean, removed, notes
