"""TBIA portal 欄位定義（D29）

records core（tbia_records，v2 欄位名稱）、taxa core（D21 維持舊名）、網址搜尋參數三者的對照集中在這裡，
其他程式一律從這裡取，不再各自寫死欄位清單。

- records 欄位：送給前端的 key、表格欄位、排序值都用 v2 名稱
- taxa core：查詢時用舊名，取回的結果用 TAXA_TO_RECORD 換成 v2 名稱再給前端
- 網址參數：3.4 前維持舊參數名，查詢時用 PARAM_TO_FIELD 換成 v2 欄位（舊值轉新值見 data/utils.py）
- v1 API 用的欄位清單在 api/v1_query.py，v1 停用（8.2）時整個檔案刪除

標籤（可 grep）：[V1-API-REMOVE] v1 API 停用時刪除；[P2-2-REMOVE] P2-2 後刪除；
[COMPAT-KEEP] 舊網址 / 已存查詢相容，永久保留
"""

# ---- taxa core（舊名）↔ records v2 ----
# taxa core 維持舊名（D21）；只列名稱不同的欄位
TAXA_TO_RECORD = {
    'common_name_c': 'vernacularName',
    'kingdom_c': 'kingdomChinese',
    'phylum_c': 'phylumChinese',
    'class_c': 'classChinese',
    'order_c': 'orderChinese',
    'family_c': 'familyChinese',
    'genus_c': 'genusChinese',
    'bioGroup': 'taxonGroup',
    'name_author': 'scientificNameAuthorship',
}
RECORD_TO_TAXA = {v: k for k, v in TAXA_TO_RECORD.items()}


def to_record_field(taxa_field):
    """taxa core 欄位名 → records v2 欄位名（同名的原樣回傳）"""
    return TAXA_TO_RECORD.get(taxa_field, taxa_field)


def to_taxa_field(record_field):
    """records v2 欄位名 → taxa core 欄位名（同名的原樣回傳）"""
    return RECORD_TO_TAXA.get(record_field, record_field)


# ---- v1 → v2 欄位名稱（records） ---- [COMPAT-KEEP] 已存資料一直會有舊欄位名，永久保留
# 讀已存的舊資料用：例如全站搜尋下載存下來的 key（SearchQuery.query 的 key=common_name_c）
V1_TO_V2_FIELD = {
    **TAXA_TO_RECORD,
    'sourceScientificName': 'verbatimScientificName',
    'sourceVernacularName': 'verbatimVernacularName',
    'originalScientificName': 'verbatimIdentification',
    'rightsHolder': 'sourceDatabase',
    'eventDate': 'verbatimEventDate',
    'preservation': 'preparations',
    'sourceDatasetID': 'datasetID',
    'standardLatitude': 'decimalLatitude',
    'standardLongitude': 'decimalLongitude',
    'standardRawLatitude': 'rawDecimalLatitude',
    'standardRawLongitude': 'rawDecimalLongitude',
    'verbatimRawLatitude': 'rawVerbatimLatitude',
    'verbatimRawLongitude': 'rawVerbatimLongitude',
    'standardOrganismQuantity': 'organismQuantity',
}


def to_v2_field(name):
    return V1_TO_V2_FIELD.get(name, name)


# ---- 網址搜尋參數 → records v2 欄位 ---- [COMPAT-KEEP]
# 3.4 參數改 v2 名稱時，舊參數名改由轉換表處理，這裡只剩參數名與欄位名不同的項目
PARAM_TO_FIELD = {
    'rightsHolder': 'sourceDatabase',
    'preservation': 'preparations',
    'eventDate': 'verbatimEventDate',
    'bioGroup': 'taxonGroup',
}


def param_field(param):
    return PARAM_TO_FIELD.get(param, param)


# ---- records v2 欄位分組 ----
TAXON_NAME_FIELDS = ['scientificName', 'vernacularName', 'alternative_name_c', 'synonyms', 'misapplied']
TAXON_RANK_FIELDS = ['kingdom', 'phylum', 'class', 'order', 'family', 'genus', 'species']
TAXON_RANK_C_FIELDS = ['kingdomChinese', 'phylumChinese', 'classChinese', 'orderChinese', 'familyChinese', 'genusChinese']
# 來源資料庫提供的名稱
SOURCE_NAME_FIELDS = ['verbatimScientificName', 'verbatimVernacularName', 'verbatimIdentification']

# 全站搜尋：與分類相關的欄位（同一物種的命中合併成一張卡片）
TAXON_FACETS = TAXON_NAME_FIELDS + ['taxonRank'] + TAXON_RANK_FIELDS + TAXON_RANK_C_FIELDS
# 查詢時去除重複空格的欄位
TAXON_KEYWORD_FIELDS = TAXON_FACETS + SOURCE_NAME_FIELDS + ['taxonID']
# 進階搜尋 name 參數查詢的欄位
NAME_SEARCH_FIELDS = TAXON_NAME_FIELDS + SOURCE_NAME_FIELDS

# 全站搜尋 物種出現紀錄 / 自然史典藏 的卡片欄位（順序即側欄順序）
OCC_CARD_FIELDS = (TAXON_NAME_FIELDS + SOURCE_NAME_FIELDS + TAXON_RANK_FIELDS + TAXON_RANK_C_FIELDS
                   + ['sourceDatabase', 'sensitiveCategory', 'locality', 'recordedBy', 'basisOfRecord',
                      'datasetName', 'license', 'verbatimEventDate'])
COL_CARD_FIELDS = (TAXON_NAME_FIELDS + SOURCE_NAME_FIELDS + TAXON_RANK_FIELDS + TAXON_RANK_C_FIELDS
                   + ['sourceDatabase', 'sensitiveCategory', 'locality', 'recordedBy',
                      'datasetName', 'license', 'verbatimEventDate', 'typeStatus', 'preparations'])

# 全站搜尋 物種卡片：查 taxa core，用 taxa 舊名
TAXA_CARD_FIELDS = (['scientificName', 'common_name_c', 'alternative_name_c', 'synonyms', 'misapplied']
                    + TAXON_RANK_FIELDS
                    + ['kingdom_c', 'phylum_c', 'class_c', 'order_c', 'family_c', 'genus_c'])

# ---- 子字串查詢方式（records v2 與 taxa core 共用，依 Solr 上實際建的衍生欄位） ----
# 拉丁欄位走 _txt（分詞 + 前綴）
LATIN_TXT_FIELDS = frozenset([
    'scientificName', 'verbatimScientificName', 'verbatimIdentification',
    'kingdom', 'phylum', 'class', 'order', 'family', 'genus', 'species',
    'synonyms', 'misapplied',
])
# 長度 >= 2 走 _bi（bigram）；common_name_c 是 taxa core 的欄位
BIGRAM_FIELDS = frozenset([
    'datasetName', 'locality', 'recordedBy', 'resourceContacts',
    'verbatimVernacularName', 'vernacularName', 'alternative_name_c',
    'common_name_c',
])
# records v2 上有 _ngram / _txt / _bi 的欄位；不在清單內的沿用 regex
NGRAM_FIELDS = frozenset(
    TAXON_NAME_FIELDS + TAXON_RANK_FIELDS + TAXON_RANK_C_FIELDS + SOURCE_NAME_FIELDS + [
        'locality', 'recordedBy', 'datasetName', 'basisOfRecord', 'license',
        'sourceDatabase', 'sensitiveCategory', 'verbatimEventDate', 'typeStatus', 'preparations',
        'resourceContacts',
    ])

# ---- 標籤 ----
# taxonRank 值 → 中文（同時是表格中各階層欄位的標籤）
RANK_LABELS = {
    'domain': '域', 'superkingdom': '總界', 'kingdom': '界', 'subkingdom': '亞界', 'infrakingdom': '下界',
    'superdivision': '超部|總部', 'division': '部|類', 'subdivision': '亞部|亞類', 'infradivision': '下部|下類',
    'parvdivision': '小部|小類', 'superphylum': '超門|總門', 'phylum': '門', 'subphylum': '亞門',
    'infraphylum': '下門', 'microphylum': '微門', 'parvphylum': '小門', 'superclass': '超綱|總綱',
    'class': '綱', 'subclass': '亞綱', 'infraclass': '下綱', 'superorder': '超目|總目', 'order': '目',
    'suborder': '亞目', 'infraorder': '下目', 'superfamily': '超科|總科', 'family': '科', 'subfamily': '亞科',
    'tribe': '族', 'subtribe': '亞族', 'genus': '屬', 'subgenus': '亞屬', 'section': '組|節',
    'subsection': '亞組|亞節', 'species': '種', 'subspecies': '亞種', 'nothosubspecies': '雜交亞種',
    'variety': '變種', 'subvariety': '亞變種', 'nothovariety': '雜交變種', 'form': '型', 'subform': '亞型',
    'special form': '特別品型', 'race': '種族', 'stirp': '血統', 'morph': '形態型', 'aberration': '異常個體',
    'hybrid formula': '雜交組合',
}

# 各階層中文名欄位：records v2 只有 6 個主要階層改名（kingdomChinese…），其餘維持 *_c
RANK_C_LABELS = {
    (to_record_field(f'{r}_c')): f'{label}中文名' for r, label in RANK_LABELS.items()
}

_RECORD_LABELS = {
    'higherTaxa': '較高分類群',
    'taxonGroup': '物種類群（以分類區分）',
    'scientificName': '學名',
    'vernacularName': '中文名',
    'alternative_name_c': '中文別名',
    'synonyms': '同物異名',
    'misapplied': '誤用名',
    'verbatimScientificName': '來源資料庫使用學名',
    'verbatimVernacularName': '來源資料庫使用中文名',
    'verbatimIdentification': '原始紀錄物種',
    'habitat': '物種類群（以棲地區分）',
    'taxonRank': '鑑定層級',
    'sensitiveCategory': '敏感層級',
    'sourceDatabase': '來源資料庫',
    'taxonID': 'TaiCOL物種編號',
    'verbatimEventDate': '紀錄日期',
    'county': '縣市',
    'municipality': '鄉鎮市區',
    'date': '紀錄日期',
    'locality': '出現地',
    'organismQuantity': '數量',
    'quantity': '數量',
    'organismQuantityType': '數量單位',
    'recordedBy': '記錄者',
    'verbatimLongitude': '經度',
    'verbatimLatitude': '緯度',
    'lon': '經度',
    'lat': '緯度',
    'verbatimSRS': '空間參考系統',
    'verbatimCoordinateSystem': '座標系統',
    'coordinateUncertaintyInMeters': '座標誤差（公尺）',
    'dataGeneralizations': '座標是否有模糊化',  # v2 改文字，標籤與說明 7.1 調整
    'coordinatePrecision': '座標模糊化程度',
    'basisOfRecord': '紀錄類型',
    'datasetName': '資料集名稱',
    'resourceContacts': '資料集聯絡人',
    'license': '授權狀況',
    'occurrenceID': 'occurrenceID',
    'grid_1': '1公里網格編號',
    'grid_5': '5公里網格編號',
    'grid_10': '10公里網格編號',
    'grid_100': '100公里網格編號',
}

# key 順序即進階搜尋表格的欄位順序；key 是 records v2 欄位（或顯示用欄位，如 date、lat）
map_occurrence = {'associatedMedia': '多媒體', **RANK_LABELS, **RANK_C_LABELS, **_RECORD_LABELS}

map_collection = dict(map_occurrence)
map_collection.update({
    'verbatimEventDate': '採集日期',
    'date': '採集日期',
    'locality': '採集地',
    'recordedBy': '採集者',
    'recordNumber': '採集號',
    'typeStatus': '標本類型',
    'preparations': '保存方式',
    'catalogNumber': '館藏號',
})


# 表格欄位中不是 Solr 欄位的 key（顯示用或查詢參數），不能拿來排序
UNSORTABLE_KEYS = frozenset([
    'associatedMedia', 'habitat', 'higherTaxa', 'date', 'quantity', 'lat', 'lon',
    'special form', 'hybrid formula', 'special form_c', 'hybrid formula_c',
])


def param_label(param, map_dict):
    """網址參數名 → 標籤（create_query_display / common_search 用）；查不到回傳 None"""
    return map_dict.get(param_field(param))


# ---- 下載 ----
# 3.2：v1 下載欄位逐一換成 v2 名稱（gbifDatasetID 與原始字串 organismQuantity 在 v2 已移除）
# 最終對外欄位與公開 / 限制型取值規則於 3.3 依 v2 API 調整
DOWNLOAD_FIELDS = [
    'id', 'created', 'modified', 'standardDate',
    'decimalLatitude', 'decimalLongitude', 'organismQuantity',
    'associatedMedia', 'basisOfRecord', 'catalogNumber', 'coordinatePrecision',
    'coordinateUncertaintyInMeters', 'dataGeneralizations', 'datasetName', 'tbiaDatasetID',
    'datasetID', 'verbatimEventDate', 'county', 'municipality', 'license', 'locality',
    'mediaLicense', 'occurrenceID', 'organismQuantityType', 'verbatimIdentification',
    'preparations', 'recordedBy', 'recordNumber', 'references', 'resourceContacts',
    'sourceDatabase', 'sensitiveCategory', 'sourceCreated', 'sourceModified',
    'verbatimScientificName', 'verbatimVernacularName', 'typeStatus', 'verbatimCoordinateSystem',
    'verbatimLatitude', 'verbatimLongitude', 'verbatimSRS', 'scientificNameID', 'taxonID',
    'match_higher_taxon', 'scientificName', 'scientificNameAuthorship', 'taxonGroup', 'taxonRank',
    'vernacularName', 'alternative_name_c', 'synonyms', 'misapplied',
    'kingdom', 'kingdomChinese', 'phylum', 'phylumChinese', 'class', 'classChinese',
    'order', 'orderChinese', 'family', 'familyChinese', 'genus', 'genusChinese',
]

SENSITIVE_FIELDS = [
    'rawDecimalLatitude', 'rawDecimalLongitude',
    'rawVerbatimLatitude', 'rawVerbatimLongitude',
    'rawCounty', 'rawMunicipality',
]

DOWNLOAD_FIELDS_WITH_SENSITIVE = DOWNLOAD_FIELDS + SENSITIVE_FIELDS

# 進階搜尋 物種名錄下載：從 taxa core 取的欄位（taxa 舊名），輸出時換成 v2 名稱
SPECIES_DOWNLOAD_TAXA_FIELDS = [
    'common_name_c', 'alternative_name_c', 'synonyms', 'misapplied', 'id', 'bioGroup',
    'cites', 'iucn', 'redlist', 'protected', 'sensitive', 'alien_type', 'is_endemic',
    'is_fossil', 'is_terrestrial', 'is_freshwater', 'is_brackish', 'is_marine',
    'kingdom', 'kingdom_c', 'phylum', 'phylum_c', 'class', 'class_c', 'order', 'order_c',
    'family', 'family_c', 'genus', 'genus_c',
]
