"""7.1：下載檔案欄位說明頁（/data-fields），取代原本的 /media/資料欄位說明文件.pdf、名錄欄位說明文件.pdf

- 物種出現紀錄、資料集的欄位名稱與說明沿用 api/doc_v2.py（下載欄位與 API v2 回傳欄位相同，3.3 / 5.2 / 5.3），
  只有提到「公開 API／限制型 API」的欄位另寫下載用的說明（DOWNLOAD_REMARKS）
- 欄位順序依實際下載檔案：DOWNLOAD_FIELDS、DATASET_DOWNLOAD_COLUMNS（11/26 起兩者都同 API v2）、SPECIES_DOWNLOAD_COLUMNS
- 物種名錄欄位 API 沒有，說明寫在 SPECIES_FIELDS
"""
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from api.doc_v2 import OCCURRENCE_FIELDS, DATASET_FIELDS, vocab_link
from data.fields import DOWNLOAD_FIELDS, RESTRICTED_OVERRIDE, SPECIES_DOWNLOAD_COLUMNS, API_DATASET_FIELDS

# 資料集下載的欄位與順序：11/26 起同 API v2（data/views.py download_dataset_results 也用這份）
DATASET_DOWNLOAD_COLUMNS = API_DATASET_FIELDS

# API 說明寫「公開 API／限制型 API」的欄位，下載改寫成「一般下載／有權限的下載」
DOWNLOAD_REMARKS = {
    'verbatimLongitude': _('來源提供的原始經度。如該筆紀錄經模糊化處理，本欄位為空值。'),
    'verbatimLatitude': _('來源提供的原始緯度。如該筆紀錄經模糊化處理，本欄位為空值。'),
    'dataGeneralizations': _('說明公開座標經 TBIA 依敏感層級統一模糊化的方式（例：公開座標由 TBIA 統一模糊化，取至小數點後 1 位），未模糊化以空值表示。'),
    'decimalLongitude': _('校正後十進位制經度坐標，大地基準採用 EPSG:4326 (WGS84)。如該筆紀錄經模糊化處理，為模糊化後的值。'),
    'decimalLatitude': _('校正後十進位制緯度坐標，大地基準採用 EPSG:4326 (WGS84)。如該筆紀錄經模糊化處理，為模糊化後的值。'),
    'county': _('十進位坐標所在的直轄市或省轄縣市。如該筆紀錄經模糊化處理，依模糊化後坐標推算。'),
    'countyCode': _('十進位坐標所在的直轄市或省轄縣市代碼。如該筆紀錄經模糊化處理，依模糊化後坐標推算。'),
    'municipality': _('十進位坐標所在的行政區（鄉/鎮/市/區層級）。如該筆紀錄經模糊化處理，依模糊化後坐標推算。'),
}

# 物種名錄下載：taxonID、scientificName 之後依 SPECIES_DOWNLOAD_COLUMNS；與紀錄同名的欄位沿用紀錄的說明
SPECIES_FIELDS = {
    'isEndemic': (_('臺灣特有種'), 'boolean', _('是否為臺灣特有種，依臺灣物種名錄（TaiCOL），值為 <code>true</code> / <code>false</code>；TaiCOL 未提供為空值。')),
    'nativeness': (_('原生性'), 'string', _('依臺灣物種名錄（TaiCOL），值為 <code>native</code>（原生）、<code>naturalized</code>（歸化）、<code>invasive</code>（入侵）、<code>cultured</code>（栽培豢養）；TaiCOL 未提供為空值。')),
    'protectedStatus': (_('保育類等級'), 'string', _('值為 <code>I</code>（瀕臨絕種）、<code>II</code>（珍貴稀有）、<code>III</code>（其他應予保育）、<code>CHPA</code>（文化資產保存法珍貴稀有植物）；非保育類為空值。')),
    'suggestedSensitiveCategory': (_('建議敏感層級'), 'string', _('依據生物多樣性敏感資料開放作業原則標準，建議該物種適用的敏感層級類別，值為「輕度」「重度」「縣市」「座標不開放」；非敏感物種為空值。')),
    'citesAppendix': (_('CITES 附錄'), 'string', _('瀕臨絕種野生動植物國際貿易公約（CITES）附錄等級，值為 <code>I</code>、<code>II</code>、<code>III</code>、<code>NC</code>，多個以「/」分隔（例：<code>I/II</code>）；未列入為空值。')),
    'iucnRedListCategory': (_('IUCN 紅皮書評估類別'), 'string', _('IUCN 紅皮書名錄的評估類別，值見下方「IUCN 紅皮書評估類別」；未評估為空值。')),
    'taiwanRedListCategory': (_('臺灣紅皮書評估類別'), 'string', _('臺灣紅皮書名錄的評估類別，值見下方「臺灣紅皮書評估類別」；未評估為空值。')),
    'isFossil': (_('化石種'), 'boolean', _('是否為化石種，依臺灣物種名錄（TaiCOL），值為 <code>true</code> / <code>false</code>；TaiCOL 未提供為空值。')),
    'isTerrestrial': (_('陸生'), 'boolean', _('棲地是否包含陸域，依臺灣物種名錄（TaiCOL），值為 <code>true</code> / <code>false</code>；TaiCOL 未提供為空值。')),
    'isFreshwater': (_('淡水'), 'boolean', _('棲地是否包含淡水，依臺灣物種名錄（TaiCOL），值為 <code>true</code> / <code>false</code>；TaiCOL 未提供為空值。')),
    'isBrackish': (_('半鹹水'), 'boolean', _('棲地是否包含半鹹水，依臺灣物種名錄（TaiCOL），值為 <code>true</code> / <code>false</code>；TaiCOL 未提供為空值。')),
    'isMarine': (_('海洋'), 'boolean', _('棲地是否包含海洋，依臺灣物種名錄（TaiCOL），值為 <code>true</code> / <code>false</code>；TaiCOL 未提供為空值。')),
}

SPECIES_COLUMNS = ['taxonID', 'scientificName'] + [c for _, c in SPECIES_DOWNLOAD_COLUMNS]

# 11/26：紅皮書評估類別（API 沒有，列在欄位說明頁）；臺灣紅皮書的值已由 NCR 等轉成 CR 等（data/utils.py TAIWAN_RED_LIST_FIX）
TAIWAN_RED_LIST_VOCAB = [
    ('EX', _('絕滅（EX, Extinct）')),
    ('EW', _('野外絕滅（EW, Extinct in the Wild）')),
    ('RE', _('區域滅絕（RE, Regionally Extinct）')),
    ('CR', _('極危（CR, Critically Endangered）')),
    ('EN', _('瀕危（EN, Endangered）')),
    ('VU', _('易危（VU, Vulnerable）')),
    ('NT', _('接近受脅（NT, Near Threatened）')),
    ('LC', _('暫無危機（LC, Least Concern）')),
    ('DD', _('資料缺乏（DD, Data Deficient）')),
    ('NA', _('不適用（NA, Not Applicable）')),
    ('NE', _('未評估（NE, Not Evaluated）')),
]
IUCN_RED_LIST_VOCAB = [v for v in TAIWAN_RED_LIST_VOCAB if v[0] != 'NA']


def _link_api(text):
    """API 說明的頁內連結（#vocab-area 等）改指到 API 說明頁"""
    return str(text).replace('href="#', f'href="{reverse("api_doc")}#')


def _rows(columns, defs, remarks=None):
    remarks = remarks or {}
    out = []
    for f in columns:
        label, typ, remark = defs[f]
        out.append({'name': f, 'label': label, 'type': typ, 'remark': _link_api(vocab_link(f, remarks.get(f, remark))),
                    'restricted': f in RESTRICTED_OVERRIDE})
    return out


def field_doc_context():
    occ = {f: (n, t, rm) for f, n, t, rm in OCCURRENCE_FIELDS}
    ds = {f: (n, t, rm) for f, n, t, rm in DATASET_FIELDS}
    species = {**occ, **SPECIES_FIELDS}
    return {
        'occurrence_fields': _rows(DOWNLOAD_FIELDS, occ, DOWNLOAD_REMARKS),
        'dataset_fields': _rows(DATASET_DOWNLOAD_COLUMNS, ds),
        'species_fields': _rows(SPECIES_COLUMNS, species),
        'taiwan_red_list_vocab': TAIWAN_RED_LIST_VOCAB,
        'iucn_red_list_vocab': IUCN_RED_LIST_VOCAB,
        'api_doc_url': reverse('api_doc'),
    }
