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
# 參數值 → Solr 欄位（fossil 為 user.html 誤植，11/20 決定移除；Solr 雖有 is_fossil，網站與 API 都不提供）
# 11/18：freshWater → freshwater（freshwater 是一個字）；網站仍接受測試站 11/17～18 存下的 freshWater，API 只認 freshwater
HABITAT_PARAM = {'terrestrial': 'is_terrestrial', 'freshwater': 'is_freshwater',
                 'brackish': 'is_brackish', 'marine': 'is_marine'}
# 網站進階搜尋的鑑定層級（只列常見階層，方便使用）；API 接受 TaiCOL 全部階層（TAICOL_RANKS）
TAXON_RANKS = ['Kingdom', 'Phylum', 'Class', 'Order', 'Family', 'Genus', 'Species', 'Infraspecies']

# ---- TaiCOL 分類階層（11/20，taicol-web ranks 表 2026-11-20 匯出） ----
# (key, en-us, zh-tw)，依 ranks.order 由高到低。API v2 的 taxonRank 查詢與輸出值 = en-us（D26 修訂）。
# Solr（taxa core 與 records）存的是小寫、以空白分隔的名稱：key 的連字號換成空白（special-form → special form）
TAICOL_RANKS = [
    ('unranked', 'Unranked', '未定義階層'),
    ('realm', 'Realm', '病毒域'),
    ('subrealm', 'Subrealm', '病毒亞域'),
    ('domain', 'Domain', '域'),
    ('superkingdom', 'Superkingdom', '總界'),
    ('kingdom', 'Kingdom', '界'),
    ('subkingdom', 'Subkingdom', '亞界'),
    ('infrakingdom', 'Infrakingdom', '下界'),
    ('superdivision', 'Superdivision', '超部|總部'),
    ('division', 'Division', '部|類'),
    ('subdivision', 'Subdivision', '亞部|亞類'),
    ('infradivision', 'Infradivision', '下部|下類'),
    ('parvdivision', 'Parvdivision', '小部|小類'),
    ('superphylum', 'Superphylum', '超門|總門'),
    ('phylum', 'Phylum', '門'),
    ('subphylum', 'Subphylum', '亞門'),
    ('infraphylum', 'Infraphylum', '下門'),
    ('microphylum', 'Microphylum', '微門'),
    ('parvphylum', 'Parvphylum', '小門'),
    ('megaclass', 'Megaclass', '高綱'),
    ('superclass', 'Superclass', '超綱|總綱'),
    ('grandclass', 'Grandclass', '大綱'),
    ('mirclass', 'Mirclass', '上綱'),
    ('class', 'Class', '綱'),
    ('subclass', 'Subclass', '亞綱'),
    ('infraclass', 'Infraclass', '下綱'),
    ('superorder', 'Superorder', '超目|總目'),
    ('order', 'Order', '目'),
    ('suborder', 'Suborder', '亞目'),
    ('infraorder', 'Infraorder', '下目'),
    ('superfamily', 'Superfamily', '超科|總科'),
    ('epifamily', 'Epifamily', '領科'),
    ('family', 'Family', '科'),
    ('subfamily', 'Subfamily', '亞科'),
    ('tribe', 'Tribe', '族'),
    ('subtribe', 'Subtribe', '亞族'),
    ('genus', 'Genus', '屬'),
    ('subgenus', 'Subgenus', '亞屬'),
    ('section', 'Section', '組|節'),
    ('subsection', 'Subsection', '亞組|亞節'),
    ('species', 'Species', '種'),
    ('subspecies', 'Subspecies', '亞種'),
    ('nothosubspecies', 'Nothosubspecies', '雜交亞種'),
    ('variety', 'Variety', '變種'),
    ('subvariety', 'Subvariety', '亞變種'),
    ('nothovariety', 'Nothovariety', '雜交變種'),
    ('form', 'Form', '型'),
    ('subform', 'Subform', '亞型'),
    ('special-form', 'Special Form', '特別品型'),
    ('race', 'Race', '種族'),
    ('stirp', 'Stirp', '血統'),
    ('morph', 'Morph', '形態型'),
    ('aberration', 'Aberration', '異常個體'),
    ('lusus', 'Lusus', '畸變'),
    ('hybrid-formula', 'Hybrid Formula', '雜交組合'),
    ('cultivar-group', 'Group', '品種群'),
    ('cultivar', 'Cultivar', '品種'),
]
RANK_ZH = {k: zh for k, _, zh in TAICOL_RANKS}


def rank_solr_value(key):
    """ranks.key → Solr 的 taxonRank 值（special-form → special form）"""
    return key.replace('-', ' ')


def _solr_term(v):
    """Solr 查詢用：含空白的值加引號"""
    return f'"{v}"' if ' ' in v else v


RANK_EN_TO_SOLR = {en: rank_solr_value(k) for k, en, _ in TAICOL_RANKS}
RANK_SOLR_TO_EN = {v: en for en, v in RANK_EN_TO_SOLR.items()}


def taxon_rank_v2(value):
    """Solr taxonRank（TaiCOL 小寫、空白分隔，例 special form）→ TaiCOL ranks 表的 en-us（Special Form）。
    11/20 Kim 決定與 TaiCOL 階層一致（D26 修訂）；對不到的值（ranks 表沒有）首字大寫原樣輸出，check_step5 會列出。
    API v2、紀錄下載、名錄下載共用（7.1：下載的值以 API 為準）"""
    if not value:
        return None
    return RANK_SOLR_TO_EN.get(value) or value[:1].upper() + value[1:]

# 全站搜尋物種卡片的「分類階層」下拉：(大標題 key, 大標題名稱, [(子階層 key, 名稱), ...])，名稱取 RANK_ZH。
# 分組大致依 ranks 表的 parent_group；種下（sub）是網站自訂的群組，Infraspecies 只含 INFRASPECIES_RANK_KEYS。
# cultivar-group 是 TaiCOL 新階層，Solr 目前可能還沒有，Solr 寫法（暫定 cultivar group）於 P2 資料更新程式碼一併處理
def _g(key, subs, label=None):
    return (key, label or RANK_ZH[key], [(s, RANK_ZH[s]) for s in subs])


INFRASPECIES_RANK_KEYS = ['subspecies', 'nothosubspecies', 'variety', 'subvariety', 'nothovariety', 'form', 'subform',
                          'special-form', 'race', 'stirp', 'morph', 'aberration', 'lusus']   # lusus 11/20 Kim 加入
# 列在「種下」組、但不算 Infraspecies（目前沒有）
SUB_GROUP_EXTRA_KEYS = []
TAXON_RANK_GROUPS = [
    _g('species', []),
    ('sub', '種下', [(s, RANK_ZH[s]) for s in INFRASPECIES_RANK_KEYS + SUB_GROUP_EXTRA_KEYS]),
    # 雜交組合、品種群、品種：不屬於種下，各自獨立（11/20 Kim）
    _g('hybrid-formula', []),
    _g('cultivar-group', []),
    _g('cultivar', []),
    _g('genus', ['subgenus', 'section', 'subsection']),
    _g('family', ['subfamily', 'tribe', 'subtribe']),
    _g('order', ['suborder', 'infraorder', 'superfamily', 'epifamily']),
    _g('class', ['subclass', 'infraclass', 'superorder']),
    _g('phylum', ['subphylum', 'infraphylum', 'microphylum', 'parvphylum', 'megaclass', 'superclass',
                  'grandclass', 'mirclass']),
    _g('division', ['subdivision', 'infradivision', 'parvdivision', 'superphylum']),
    _g('kingdom', ['subkingdom', 'infrakingdom', 'superdivision']),
    _g('domain', ['superkingdom', 'realm', 'subrealm']),   # realm 照原本放在「域」組（11/20 Kim）
    _g('unranked', []),
]
# 種下階層的 Solr 查詢值（網站 taxonRank=Infraspecies、全站搜尋「種下」、API Infraspecies 共用）
INFRASPECIES_RANKS = [_solr_term(rank_solr_value(k)) for k in INFRASPECIES_RANK_KEYS]
# 全站搜尋下拉的 key → Solr 查詢值（只列和 key 不同的）
RANK_SOLR_VALUE = {k: _solr_term(rank_solr_value(k)) for k, _, _ in TAICOL_RANKS if '-' in k}
VALID_TAXON_RANKS = {g[0] for g in TAXON_RANK_GROUPS} | {r[0] for g in TAXON_RANK_GROUPS for r in g[2]}
NATIVENESS = ['native', 'naturalized', 'invasive', 'cultured']
PROTECTED_STATUS = ['I', 'II', 'III', 'CHPA']
TYPE_STATUS = ['HOLOTYPE', 'PARATYPE', 'ISOTYPE', 'ALLOTYPE', 'SYNTYPE', 'LECTOTYPE',
               'PARALECTOTYPE', 'NEOTYPE', 'TOPOTYPE']
MEDIA_TYPES = ['image', 'video', 'audio']
BASIS_OF_RECORD = ['HumanObservation', 'MachineObservation', 'PreservedSpecimen', 'MaterialSample',
                   'LivingSpecimen', 'FossilSpecimen', 'MaterialCitation', 'MaterialEntity', 'Taxon',
                   'Occurrence', 'Event']
GRID_LEVELS = ['grid_1', 'grid_5', 'grid_10', 'grid_100']
CIRCLE_MAX_KM = 25

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
    """'經度,緯度,半徑（公里）' → (lon, lat, r) 浮點數；不合法回傳 None（0 < r ≤ CIRCLE_MAX_KM）"""
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
        old['freshWater'] = 'freshwater'
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
