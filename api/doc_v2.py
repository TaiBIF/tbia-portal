"""5.5 API v2 說明頁（/api/doc）的內容：查詢參數表、回傳欄位表、控制詞彙。

以 for_api_docs/v4/user.html 為底，套用交接文件「API 規格調整」的各項修改。
- 回傳欄位的順序與 data/fields.py 的 API_OCCURRENCE_FIELDS / API_DATASET_FIELDS 相同（api/tests_v2.py 有檢查）
- 每個範例網址都由 scripts/v2_migration/check_step5.py 5.5-2 實際呼叫，確認回 200
- 文字用 gettext_lazy 標記，英文翻譯在 7.1 補（django.po）
"""
from django.utils.translation import gettext_lazy as _

from data.search_params import (
    TAICOL_RANKS, TAXON_RANK_GROUPS, NATIVENESS, PROTECTED_STATUS, TYPE_STATUS, BASIS_OF_RECORD, TAXON_GROUPS,
    HABITAT_PARAM,
)

# 範例用的固定值（測試站與正式站都存在；tbiaPartnerID 由 title 以 uuid5 算出、固定不變，D28）
EX_PARTNER_ID = 'c33522a5-342e-5809-9fbc-fbe07af56ef5'   # 農業部生物多樣性研究所
EX_PARTNER_ID_2 = 'd69b5ba8-9c69-532a-afd3-22340c955d5f'  # 國立自然科學博物館


def example(url):
    """範例網址：(顯示文字, 實際連結)。實際連結加 from_example=1，不列入使用統計"""
    return url, url + ('&' if '?' in url else '?') + 'from_example=1'


# 更新紀錄的 v2 上線日期：8.1 上線時確認（排定 12/10 切換）
V2_RELEASE_DATE = '2026-12-10'

# ---- 查詢參數：(參數, 型值, 說明, 範例網址, 必填) ----

OCCURRENCE_PARAMS = [
    ('tbiaID', 'string', _('取得指定 TBIA 物種出現紀錄編碼的出現紀錄資料。'),
     '/api/v2/occurrence?tbiaID=6540d35818aad00028ecda95'),
    ('occurrenceID', 'string', _('取得指定來源資料庫的物種出現紀錄編碼的出現紀錄資料。'),
     '/api/v2/occurrence?occurrenceID=TAIF:PLANT:8540:1:1:186874'),
    ('catalogNumber', 'string', _('取得指定典藏機構登錄號的出現紀錄資料。'),
     '/api/v2/occurrence?catalogNumber=186874'),
    ('recordNumber', 'string', _('取得指定採集號的出現紀錄資料。'),
     '/api/v2/occurrence?recordNumber=218114'),
    ('name', 'string', _('取得指定學名／中文名／中文別名／同物異名／誤用名的出現紀錄資料。'),
     '/api/v2/occurrence?name=臺灣獼猴'),
    ('taxonID', 'string', _('取得指定臺灣物種名錄（TaiCOL）物種編號的出現紀錄資料。'),
     '/api/v2/occurrence?taxonID=t0052516'),
    ('higherTaxonID', 'string', _('以臺灣物種名錄（TaiCOL）物種編號指定分類群，回傳該分類群本身及其下所有子分類群的紀錄。與 taxonID 僅比對單一分類群不同。'),
     '/api/v2/occurrence?higherTaxonID=t0002476'),
    ('taxonGroup', 'string', _('取得指定物種類群的出現紀錄資料，可複合查詢，請見控制詞彙列表。'),
     '/api/v2/occurrence?taxonGroup=鳥類,哺乳類'),
    ('taxonGroupByHabitat', 'string', _('取得指定物種類群（以棲地區分）的出現紀錄資料，可複合查詢，請見控制詞彙列表。'),
     '/api/v2/occurrence?taxonGroupByHabitat=marine,freshwater'),
    ('taxonRank', 'string', _('取得指定鑑定層級的出現紀錄資料，請見控制詞彙列表。'),
     '/api/v2/occurrence?taxonRank=Species'),
    ('isCollection', 'boolean', _('是否為自然史典藏資料，是=true，否=false。'),
     '/api/v2/occurrence?isCollection=true'),
    ('nativeness', 'string', _('取得指定原生性的出現紀錄資料，可複合查詢，請見控制詞彙列表。'),
     '/api/v2/occurrence?nativeness=native'),
    ('protectedStatus', 'string', _('取得指定保育類等級的出現紀錄資料，可複合查詢，請見控制詞彙列表。'),
     '/api/v2/occurrence?protectedStatus=I'),
    ('hasMedia', 'boolean', _('是否具有多媒體，是=true，否=false。'),
     '/api/v2/occurrence?hasMedia=true'),
    ('mediaType', 'string', _('取得指定多媒體類型的出現紀錄資料，影像=image，影片=video，音檔=audio；可複合查詢，三種都選等同不限類型。使用此參數時 hasMedia 必須為 true。'),
     '/api/v2/occurrence?hasMedia=true&mediaType=image,audio'),
    ('tbiaPartnerID', 'string', _('取得指定 TBIA 夥伴單位識別碼的出現紀錄資料，可複合查詢，識別碼請見 Partner API。'),
     f'/api/v2/occurrence?tbiaPartnerID={EX_PARTNER_ID}'),
    ('sourceDatabase', 'string', _('取得指定來源資料庫的出現紀錄資料，可複合查詢，請見控制詞彙列表。'),
     '/api/v2/occurrence?sourceDatabase=台灣生物多樣性網絡 TBN,濕地環境資料庫'),
    ('recordedBy', 'string', _('取得指定記錄者／採集者的出現紀錄資料。'),
     '/api/v2/occurrence?recordedBy=志工小組'),
    ('resourceContacts', 'string', _('取得指定資料集聯絡人的出現紀錄資料。'),
     '/api/v2/occurrence?resourceContacts=台灣兩棲類保育志工團隊'),
    ('tbiaDatasetID', 'string', _('取得指定 TBIA 資料集識別碼的出現紀錄資料，可複合查詢。'),
     '/api/v2/occurrence?tbiaDatasetID=d674d7e0ec3bd2c006cefb438'),
    ('datasetID', 'string', _('取得指定來源資料庫的資料集識別碼的出現紀錄資料，可複合查詢。不同來源資料庫的資料集識別碼可能重複，建議優先使用 tbiaDatasetID。'),
     '/api/v2/occurrence?datasetID=ac869aba-ac34-4416-9eda-075258fef27a'),
    ('basisOfRecord', 'string', _('取得指定紀錄類型的出現紀錄資料，請見控制詞彙列表。'),
     '/api/v2/occurrence?basisOfRecord=PreservedSpecimen'),
    ('eventDate', 'date', _('取得指定紀錄日期的出現紀錄資料，日期格式：YYYYMMDD（以日期為粒度，自動比對當日整段時間）。支援單一值或區間查詢。'),
     '/api/v2/occurrence?eventDate=20240101,20240131'),
    ('preparations', 'string', _('取得指定典藏保存方式的出現紀錄資料。'),
     '/api/v2/occurrence?preparations=浸液'),
    ('typeStatus', 'string', _('取得指定標本類型的出現紀錄資料，可複合查詢，請見控制詞彙列表。'),
     '/api/v2/occurrence?typeStatus=HOLOTYPE'),
    ('county', 'string', _('取得指定縣市的出現紀錄資料。'),
     '/api/v2/occurrence?county=臺東縣'),
    ('municipality', 'string', _('取得指定行政區的出現紀錄資料，本參數最細支援至鄉/鎮/市/區層級。'),
     '/api/v2/occurrence?municipality=綠島鄉'),
    ('boundedBy', 'string', _('取得指定四邊形座標範圍內出現紀錄資料，輸入值={最大經度},{最大緯度},{最小經度},{最小緯度}。'),
     '/api/v2/occurrence?boundedBy=122,23,121,22'),
    ('polygon', 'string', _('取得指定多邊形座標範圍內的出現紀錄資料。僅支援有效且閉合的 WKT POLYGON 格式。'),
     '/api/v2/occurrence?polygon=POLYGON((121 22,122 22,122 23,121 23,121 22))'),
    ('circle', 'string', _('取得指定圓形座標範圍內的出現紀錄資料，輸入值={經度},{緯度},{半徑}。半徑單位為公里，須大於 0 且不超過 50，可為小數。'),
     '/api/v2/occurrence?circle=121.5,23.5,10'),
    ('created', 'date', _('取得指定資料建立時間的出現紀錄資料，日期格式：YYYYMMDD（以日期為粒度，自動比對當日整段時間）。支援單一值或區間查詢。'),
     '/api/v2/occurrence?created=20240101,20241231'),
    ('modified', 'date', _('取得指定資料更新時間的出現紀錄資料，日期格式：YYYYMMDD（以日期為粒度，自動比對當日整段時間）。支援單一值或區間查詢。'),
     '/api/v2/occurrence?modified=20240101,*'),
]

DATASET_PARAMS = [
    ('tbiaDatasetID', 'string', _('以 TBIA 資料集識別碼取得指定的資料集。'),
     '/api/v2/dataset?tbiaDatasetID=d674d7dc6c3bd2c006cefad10'),
    ('datasetID', 'string', _('以來源資料庫的資料集編碼取得指定的資料集。'),
     '/api/v2/dataset?datasetID=ac869aba-ac34-4416-9eda-075258fef27a'),
    ('gbifDatasetID', 'string', _('以 GBIF 的資料集編碼取得指定的資料集。'),
     '/api/v2/dataset?gbifDatasetID=275319e1-f91c-406f-b239-62cb9d4185cb'),
    ('tbiaPartnerID', 'string', _('取得指定 TBIA 夥伴單位識別碼的資料集，可複合查詢，識別碼請見 Partner API。'),
     f'/api/v2/dataset?tbiaPartnerID={EX_PARTNER_ID},{EX_PARTNER_ID_2}'),
    ('sourceDatabase', 'string', _('取得指定來源資料庫的資料集，可複合查詢，請見控制詞彙列表。'),
     '/api/v2/dataset?sourceDatabase=台灣生物多樣性網絡 TBN,濕地環境資料庫'),
    ('datasetName', 'string', _('以資料集名稱查詢，支援部分查詢。'),
     '/api/v2/dataset?datasetName=eBird'),
    ('datasetTaxonGroup', 'string', _('取得涵蓋指定物種類群的資料集，可複合查詢，請見控制詞彙列表。'),
     '/api/v2/dataset?datasetTaxonGroup=鳥類,哺乳類'),
    ('created', 'date', _('資料集建立時間，日期格式：YYYYMMDD（以日期為粒度，自動比對當日整段時間）。支援單一值或區間查詢。'),
     '/api/v2/dataset?created=20240101,20241231'),
    ('modified', 'date', _('資料集更新時間，日期格式：YYYYMMDD（以日期為粒度，自動比對當日整段時間）。支援單一值或區間查詢。'),
     '/api/v2/dataset?modified=20240101,*'),
]

MAP_PARAMS = [
    ('boundedBy', 'string', _('取得指定四邊形座標範圍內物種出現紀錄網格資料，輸入值={最大經度},{最大緯度},{最小經度},{最小緯度}。經緯度跨度不得超過網格允許之最大跨度。'),
     '/api/v2/map?boundedBy=122,24,121,23&grid=1', True),
    ('grid', 'integer', _('網格大小，提供 1、5、10、100 公里網格。'),
     '/api/v2/map?boundedBy=122,24,121,23&grid=5', True),
    ('taxonID', 'string', _('取得指定臺灣物種名錄（TaiCOL）物種編號的物種網格資料。'),
     '/api/v2/map?boundedBy=122,24,121,23&grid=1&taxonID=t0052516'),
    ('taxonGroup', 'string', _('取得涵蓋指定物種類群的網格資料，可複合查詢，請見控制詞彙列表。'),
     '/api/v2/map?boundedBy=122,24,121,23&grid=1&taxonGroup=鳥類,哺乳類'),
    ('year', 'integer', _('取得指定資料年份的網格資料，年份格式：yyyy。支援單一值或區間查詢。'),
     '/api/v2/map?boundedBy=122,24,121,23&grid=1&year=2018,2021'),
    ('county', 'string', _('取得指定縣市的網格資料。'),
     '/api/v2/map?boundedBy=122,23,121,22&grid=1&county=臺東縣'),
    ('municipality', 'string', _('取得指定行政區的網格資料，本參數最細支援至鄉/鎮/市/區層級。'),
     '/api/v2/map?boundedBy=122,23,121,22&grid=1&municipality=綠島鄉'),
]

# 網格大小、經緯度最大跨度、範例（同 api/v2_params.py GRID_MAX_SPAN）
MAP_GRIDS = [
    ('1 km', _('1 度'), '/api/v2/map?boundedBy=122,23,121,22&grid=1'),
    ('5 km', _('10 度'), '/api/v2/map?boundedBy=125,25,115,15&grid=5'),
    ('10 km', _('20 度'), '/api/v2/map?boundedBy=122,23,102,3&grid=10'),
    ('100 km', _('40 度'), '/api/v2/map?boundedBy=120,25,80,-15&grid=100'),
]

PARTNER_PARAMS = [
    ('tbiaPartnerID', 'string', _('以 TBIA 夥伴單位識別碼取得指定的夥伴單位。'),
     f'/api/v2/partner?tbiaPartnerID={EX_PARTNER_ID}'),
    ('partnerName', 'string', _('以夥伴單位名稱查詢，支援部分查詢。'),
     '/api/v2/partner?partnerName=博物館'),
]

PAGING_PARAMS = [
    ('limit', 'integer', _('限制單頁回傳的最大筆數。預設 20 筆，上限 1000（超過以 1000 計）；非正整數回 400。'),
     '/api/v2/occurrence?limit=1000'),
]

# ---- 回傳欄位：(欄位, 名稱, 型值, 備註) ----

OCCURRENCE_FIELDS = [
    ('tbiaID', _('TBIA物種出現紀錄編碼'), 'string', _('該筆紀錄於TBIA入口網的永久識別編號。')),
    ('occurrenceID', _('物種出現紀錄編碼'), 'string', _('該筆紀錄於來源資料庫的永久識別編號。')),
    ('catalogNumber', _('典藏機構登錄號'), 'string', _('存證物件（如存證標本）入藏典藏機構（如博物館）後，由典藏機構於登錄或編目過程賦予的正式編碼，也可稱館號或編目號。')),
    ('eventID', _('調查活動編碼'), 'string', _('調查活動識別碼；同一調查活動所產生的多筆物種出現紀錄使用相同的 eventID。')),
    ('created', _('臺灣本地時區之資料建立時間'), 'string', _('該筆紀錄於TBIA入口網的建立時間，值格式為 YYYYMMDD HHMMSS。')),
    ('modified', _('臺灣本地時區之資料更新時間'), 'string', _('該筆紀錄於TBIA入口網的更新時間，值格式為 YYYYMMDD HHMMSS。')),
    ('selfProduced', _('第一手資料'), 'boolean', _('資料提供單位自行或委託他方獲取之第一手資料，而非介接自其他資料庫／集。')),
    ('license', _('資料授權標示或條款'), 'string', _('該筆紀錄資料授權標示或條款。')),
    ('basisOfRecord', _('紀錄類型'), 'string', _('資料於記錄當下的類型，請見控制詞彙列表。')),
    ('recordNumber', _('採集號'), 'string', _('該筆紀錄關聯之標本採集識別編號。')),
    ('recordedBy', _('記錄者／採集者'), 'string', _('該筆紀錄之實際觀察／調查／記錄／採集者。')),
    ('samplingProtocol', _('調查方法'), 'string', _('該筆紀錄使用之調查方法，可為採集／觀測方法或流程的名稱、描述，或參考文獻。')),
    ('partner', _('調查同行者'), 'string', _('該筆紀錄所屬調查活動「記錄者／採集者」以外的同行人員。')),
    ('identifiedBy', _('鑑定者'), 'string', _('該筆紀錄的物種鑑定負責人。')),
    ('datasetName', _('資料集名稱'), 'string', _('該筆紀錄所屬之資料集名稱。')),
    ('tbiaDatasetID', _('TBIA資料集識別碼'), 'string', _('該筆紀錄所屬資料集於TBIA入口網的永久識別編號，可對應 Dataset API 的 tbiaDatasetID。')),
    ('datasetID', _('資料集識別碼'), 'string', _('該筆紀錄所屬資料集於來源資料庫的識別碼。')),
    ('resourceCitationIdentifier', _('資料集連結網址'), 'string', _('該筆紀錄所屬資料集的連結網址（URL）。')),
    ('resourceContacts', _('資料集聯絡人'), 'string', _('該筆紀錄所屬之資料集聯絡人。')),
    ('associatedMedia', _('關聯多媒體'), 'string', _('該筆紀錄關聯的多媒體資源連結網址（URL）。')),
    ('mediaLicense', _('多媒體資料授權標示或條款'), 'string', _('該筆資料關聯之多媒體資料其授權標示或條款。')),
    ('individualCount', _('個體數量'), 'integer', _('經標準化後該筆紀錄代表的個體數量。')),
    ('organismQuantity', _('數量'), 'number', _('經標準化後對該筆紀錄的生物定量，須與 organismQuantityType 搭配使用。')),
    ('organismQuantityType', _('數量單位'), 'string', _('生物定量單位，須與 organismQuantity 搭配使用。')),
    ('references', _('來源資料庫URL'), 'string', _('該筆紀錄於來源資料庫的網頁URL。')),
    ('tbiaPartnerID', _('TBIA夥伴單位識別碼'), 'string', _('資料來源的TBIA夥伴單位識別碼，請見 Partner API；GBIF 資料為 null。')),
    ('partnerName', _('夥伴單位名稱'), 'string', _('tbiaPartnerID 對應的夥伴單位名稱。')),
    ('sourceDatabase', _('來源資料庫'), 'string', _('資料來源所屬的資料庫，請見控制詞彙列表。')),
    ('typeStatus', _('典藏模式/引證類型'), 'string', _('典藏被引證的類型；模式引證的詞彙請見控制詞彙列表。多項引證以「|」分隔。')),
    ('preparations', _('典藏保存方式'), 'string', _('典藏的前處理、製作和保存方式；多項以「|」分隔。')),
    ('institutionCode', _('典藏機構代碼'), 'string', _('典藏機構所使用的名稱或縮寫。')),
    ('institutionID', _('典藏機構ID'), 'string', _('研究機構唯一識別碼，建議使用 ROR 或 GRSciColl 機構代碼。')),
    ('collectionCode', _('典藏代碼'), 'string', _('用於標示典藏或資料集的名稱、縮寫、代碼或首字母縮寫詞。')),
    ('collectionID', _('典藏ID'), 'string', _('典藏紀錄唯一識別碼，建議使用 GRSciColl 唯一識別碼。')),
    ('locality', _('地區'), 'string', _('該筆紀錄的最小地點描述。')),
    ('verbatimLongitude', _('原始經度'), 'string', _('來源提供的原始經度。公開 API 中如該筆紀錄經模糊化處理，本欄位為空值；限制型 API 為原始值。')),
    ('verbatimLatitude', _('原始緯度'), 'string', _('來源提供的原始緯度。公開 API 中如該筆紀錄經模糊化處理，本欄位為空值；限制型 API 為原始值。')),
    ('verbatimCoordinateSystem', _('原始坐標系統'), 'string', _('原始經度及原始緯度欄位使用之坐標系統（坐標格式）。')),
    ('verbatimSRS', _('原始大地基準'), 'string', _('原始經度及原始緯度欄位使用之大地基準（空間參考系統）。')),
    ('geodeticDatum', _('大地基準'), 'string', _('十進位經度與十進位緯度採用之大地基準，採用 EPSG:4326 (WGS84)。')),
    ('coordinateUncertaintyInMeters', _('以公尺為單位的坐標誤差'), 'number', _('以公尺為單位的坐標誤差，給定涵蓋實際調查對象所在位置的最小圓形區域半徑。')),
    ('dataGeneralizations', _('模糊化方式說明'), 'string', _('說明公開座標經 TBIA 依敏感層級統一模糊化的方式（例：公開座標由 TBIA 統一模糊化，取至小數點後 1 位），未模糊化以空值表示。限制型 API 的座標為原始值，本欄內容與公開 API 相同。')),
    ('decimalLongitude', _('十進位經度'), 'number', _('校正後十進位制經度坐標，大地基準採用 EPSG:4326 (WGS84)。公開 API 為模糊化後的值；限制型 API 為原始值。')),
    ('decimalLatitude', _('十進位緯度'), 'number', _('校正後十進位制緯度坐標，大地基準採用 EPSG:4326 (WGS84)。公開 API 為模糊化後的值；限制型 API 為原始值。')),
    ('countryCode', _('國家代碼'), 'string', _('國家標準代碼，遵循 ISO 3166-1 alpha-2 二位字母代碼。')),
    ('county', _('直轄市或省轄縣市'), 'string', _('十進位坐標所在的直轄市或省轄縣市。公開 API 依模糊化後坐標推算；限制型 API 依原始坐標推算。')),
    ('countyCode', _('縣市別代碼'), 'string', _('十進位坐標所在的直轄市或省轄縣市代碼。公開 API 依模糊化後坐標推算；限制型 API 依原始坐標推算。')),
    ('municipality', _('行政區'), 'string', _('十進位坐標所在的行政區（鄉/鎮/市/區層級）。公開 API 依模糊化後坐標推算；限制型 API 依原始坐標推算。')),
    ('verbatimEventDate', _('原始調查日期'), 'string', _('最原始記錄且未被轉譯過的調查日期。')),
    ('year', _('西元年'), 'integer', _('原始調查日期標準化後的觀察記錄起始日期之西元年。')),
    ('month', _('月'), 'integer', _('原始調查日期標準化後的觀察記錄起始日期之月。')),
    ('day', _('日'), 'integer', _('原始調查日期標準化後的觀察記錄起始日期之日。')),
    ('eventTime', _('觀察記錄起始時間'), 'string', _('原始調查日期標準化後的觀察記錄起始時間。')),
    ('verbatimIdentification', _('原始鑑定物種名稱'), 'string', _('資料原始觀察或採集者所鑑定的物種名稱，可以是俗名或學名。')),
    ('verbatimScientificName', _('原始鑑定物種學名'), 'string', _('資料原始提供者所鑑定之物種學名。')),
    ('verbatimVernacularName', _('原始鑑定物種俗名'), 'string', _('資料原始提供者所鑑定之物種俗名。')),
    ('taxonID', _('臺灣物種名錄物種編號'), 'string', _('採用的臺灣物種名錄（TaiCOL）物種編號（taxon_id）。')),
    ('scientificName', _('校定物種學名'), 'string', _('採用的臺灣物種名錄（TaiCOL）物種編號所對應的物種學名。')),
    ('scientificNameAuthorship', _('校定學名作者'), 'string', _('採用的臺灣物種名錄（TaiCOL）物種編號所對應的學名作者。')),
    ('vernacularName', _('校定物種俗名'), 'string', _('採用的臺灣物種名錄（TaiCOL）物種編號所對應的物種俗名。')),
    ('scientificNameID', _('校定物種學名編號'), 'string', _('校定物種學名於臺灣物種名錄（TaiCOL）的學名編碼（name_id）。')),
    ('nameAccordingTo', _('校定學名來源依據'), 'string', _('校定物種學名的參考來源，如臺灣物種名錄的版本。')),
    ('taxonRank', _('鑑定層級'), 'string', _('採用的臺灣物種名錄（TaiCOL）物種編號所對應的分類位階，請見控制詞彙列表。')),
    ('taxonGroup', _('生物類群'), 'string', _('採用的臺灣物種名錄（TaiCOL）物種編號所對應的物種類群，請見控制詞彙列表。')),
    ('sensitiveCategory', _('敏感層級'), 'string', _('依據生物多樣性敏感資料開放作業原則標準所列之敏感層級類別。')),
    ('kingdom', _('界'), 'string', _('「界」之科學名稱。')),
    ('kingdomChinese', _('界中文名'), 'string', _('「界」之中文名稱。')),
    ('phylum', _('門'), 'string', _('「門」之科學名稱。')),
    ('phylumChinese', _('門中文名'), 'string', _('「門」之中文名稱。')),
    ('class', _('綱'), 'string', _('「綱」之科學名稱。')),
    ('classChinese', _('綱中文名'), 'string', _('「綱」之中文名稱。')),
    ('order', _('目'), 'string', _('「目」之科學名稱。')),
    ('orderChinese', _('目中文名'), 'string', _('「目」之中文名稱。')),
    ('family', _('科'), 'string', _('「科」之科學名稱。')),
    ('familyChinese', _('科中文名'), 'string', _('「科」之中文名稱。')),
    ('genus', _('屬'), 'string', _('「屬」之科學名稱。')),
    ('genusChinese', _('屬中文名'), 'string', _('「屬」之中文名稱。')),
]

DATASET_FIELDS = [
    ('datasetName', _('資料集名稱'), 'string', _('該資料集的名稱。')),
    ('tbiaPartnerID', _('TBIA夥伴單位識別碼'), 'string', _('該資料集的TBIA夥伴單位識別碼，請見 Partner API；GBIF 資料集為 null。')),
    ('partnerName', _('夥伴單位名稱'), 'string', _('tbiaPartnerID 對應的夥伴單位名稱。')),
    ('sourceDatabase', _('來源資料庫'), 'string', _('該資料集所屬的資料庫，請見控制詞彙列表。')),
    ('tbiaDatasetID', _('TBIA資料集識別碼'), 'string', _('該資料集於TBIA入口網的永久識別編號。')),
    ('datasetID', _('資料集編碼'), 'string', _('該資料集於來源資料庫的識別編號。')),
    ('gbifDatasetID', _('GBIF資料集識別碼'), 'string', _('該資料集於GBIF的識別編號。')),
    ('resourceContacts', _('資料集聯絡人'), 'string', _('該資料集的聯絡人。')),
    ('occurrenceCount', _('涵蓋資料筆數'), 'integer', _('該資料集涵蓋資料筆數。')),
    ('datasetDateStart', _('涵蓋日期起始'), 'string', _('該資料集涵蓋的起始日期，值格式為 YYYYMMDD。')),
    ('datasetDateEnd', _('涵蓋日期結束'), 'string', _('該資料集涵蓋的結束日期，值格式為 YYYYMMDD。')),
    ('resourceCitationIdentifier', _('資料集連結網址'), 'string', _('該資料集的連結網址（URL）。')),
    ('datasetPublisher', _('資料集發布者'), 'string', _('該資料集的發布者。')),
    ('datasetLicense', _('資料集授權標示或條款'), 'string', _('該資料集的授權標示或條款。')),
    ('datasetTaxonGroup', _('涵蓋物種類群'), 'string', _('該資料集涵蓋之物種類群。')),
    ('created', _('臺灣本地時區之資料集建立時間'), 'string', _('該資料集於TBIA入口網的建立時間，值格式為 YYYYMMDD HHMMSS。')),
    ('modified', _('臺灣本地時區之資料集更新時間'), 'string', _('該資料集於TBIA入口網的更新時間，值格式為 YYYYMMDD HHMMSS。')),
]

PARTNER_FIELDS = [
    ('tbiaPartnerID', _('TBIA夥伴單位識別碼'), 'string', _('TBIA夥伴單位的識別碼，對應 Occurrence API 與 Dataset API 的 tbiaPartnerID。')),
    ('partnerName', _('夥伴單位名稱'), 'string', _('TBIA夥伴單位的名稱。')),
]

MAP_PROPERTIES = [
    ('counts', _('網格內資料筆數（不含數量為 0 的未發現紀錄）')),
    ('current_grid_level', _('網格大小')),
    ('current_grid', _('網格編號')),
]

MAP_COLORS = [
    ('1 - 10', '#ffffcc'), ('11 - 100', '#ffeda0'), ('101 - 1,000', '#fed976'), ('1,001 - 5,000', '#feb24c'),
    ('5,001 - 10,000', '#fd8d3c'), ('10,001 - 50,000', '#fc4e2a'), ('50,001 - 100,000', '#e31a1c'),
    ('100,001+', '#bd0026'),
]

# ---- 控制詞彙 ----

VOCAB_BASIS_OF_RECORD = list(zip(BASIS_OF_RECORD, [
    _('人為觀測'), _('機器觀測'), _('保存標本'), _('組織樣本'), _('活體標本'), _('化石標本'), _('引用資料'),
    _('材料實體'), _('分類資訊'), _('出現記錄'), _('調查活動')]))
VOCAB_NATIVENESS = list(zip(NATIVENESS, [_('原生'), _('歸化'), _('入侵'), _('栽培豢養')]))
VOCAB_PROTECTED = list(zip(PROTECTED_STATUS, [
    _('瀕臨絕種保育類野生動物'), _('珍貴稀有保育類野生動物'), _('其他應予保育之野生動物'), _('文化資產保存法 珍貴稀有植物')]))
VOCAB_TYPE_STATUS = list(zip(TYPE_STATUS, [
    _('正模標本'), _('副模標本'), _('複模標本'), _('配模標本'), _('總模標本'), _('選模標本'), _('副選模標本'),
    _('新模標本'), _('模式地標本')]))
_HABITAT_ZH = {'terrestrial': _('陸生'), 'freshwater': _('淡水'), 'brackish': _('半鹹水域'), 'marine': _('海洋')}
VOCAB_HABITAT = [(k, _HABITAT_ZH[k]) for k in HABITAT_PARAM]
VOCAB_TAXON_GROUPS = TAXON_GROUPS


def taxon_rank_groups():
    """鑑定層級控制詞彙：依 TAXON_RANK_GROUPS 分組（同全站搜尋的分類階層下拉），每組可開合。
    回傳 [(組名, [(en-us, 中文), ...])]，值為 TaiCOL ranks 表的 en-us（11/20 決定；Infraspecies 可查詢但不列）"""
    en = {k: e for k, e, _zh in TAICOL_RANKS}
    zh = {k: z for k, _e, z in TAICOL_RANKS}
    out = []
    for key, label, subs in TAXON_RANK_GROUPS:
        items = [] if key == 'sub' else [(en[key], zh[key])]
        items += [(en[s], zh[s]) for s, _name in subs]
        out.append((label, items))
    return out


def all_examples():
    """說明頁上所有範例網址（check_step5 5.5-2 逐一呼叫）"""
    urls = [p[3] for table in (OCCURRENCE_PARAMS, DATASET_PARAMS, MAP_PARAMS, PARTNER_PARAMS, PAGING_PARAMS)
            for p in table]
    urls += [g[2] for g in MAP_GRIDS]
    urls += EXTRA_EXAMPLES
    return list(dict.fromkeys(urls))


# 「進階查詢說明」與「基本說明」裡的範例
EXAMPLE_INTERSECT = '/api/v2/occurrence?boundedBy=122,24,121,23&sourceDatabase=GBIF'
EXAMPLE_UNION = '/api/v2/occurrence?taxonGroup=鳥類,哺乳類'
EXAMPLE_DATE_RANGE = '/api/v2/occurrence?eventDate=20211021,20211025'
EXAMPLE_DATE_OPEN = '/api/v2/occurrence?eventDate=20240101,*'
EXAMPLE_YEAR_RANGE = '/api/v2/map?boundedBy=122,23,121,22&grid=1&year=2020,2025'
EXTRA_EXAMPLES = [EXAMPLE_INTERSECT, EXAMPLE_UNION, EXAMPLE_DATE_RANGE, EXAMPLE_DATE_OPEN, EXAMPLE_YEAR_RANGE,
                  '/api/v2/dataset', '/api/v2/partner', '/api/v2/occurrence']


def _params(rows):
    out = []
    for r in rows:
        shown, href = example(r[3])
        out.append({'name': r[0], 'type': r[1], 'desc': r[2], 'example': shown, 'href': href,
                    'required': len(r) > 4 and r[4]})
    return out


def _fields(rows):
    return [{'name': f, 'label': n, 'type': t, 'remark': rm} for f, n, t, rm in rows]


def doc_context(source_databases):
    """api_doc view 的 context；source_databases：v2 來源資料庫名稱清單（新名稱）"""
    ex = {k: dict(zip(('example', 'href'), example(v))) for k, v in {
        'intersect': EXAMPLE_INTERSECT, 'union': EXAMPLE_UNION, 'date_range': EXAMPLE_DATE_RANGE,
        'date_open': EXAMPLE_DATE_OPEN, 'year_range': EXAMPLE_YEAR_RANGE}.items()}
    return {
        'occurrence_params': _params(OCCURRENCE_PARAMS),
        'dataset_params': _params(DATASET_PARAMS),
        'map_params': _params(MAP_PARAMS),
        'partner_params': _params(PARTNER_PARAMS),
        'paging_params': _params(PAGING_PARAMS),
        'map_grids': [{'size': s, 'span': sp, 'example': example(u)[0], 'href': example(u)[1]} for s, sp, u in MAP_GRIDS],
        'occurrence_fields': _fields(OCCURRENCE_FIELDS),
        'dataset_fields': _fields(DATASET_FIELDS),
        'partner_fields': _fields(PARTNER_FIELDS),
        'map_properties': MAP_PROPERTIES,
        'map_colors': MAP_COLORS,
        'vocab_basis_of_record': VOCAB_BASIS_OF_RECORD,
        'vocab_nativeness': VOCAB_NATIVENESS,
        'vocab_protected': VOCAB_PROTECTED,
        'vocab_type_status': VOCAB_TYPE_STATUS,
        'vocab_habitat': VOCAB_HABITAT,
        'vocab_taxon_groups': VOCAB_TAXON_GROUPS,
        'vocab_source_databases': source_databases,
        'taxon_rank_groups': taxon_rank_groups(),
        'ex': ex,
        'v2_release_date': V2_RELEASE_DATE,
    }
