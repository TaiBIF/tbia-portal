"""3.4 網站搜尋參數轉換的單元測試（不需要 Django / DB / Solr）
執行：python -m unittest data.tests_search_params -v
每一種舊寫法（舊網址、書籤、已存的 SearchQuery / SearchStat 字串）都列在這裡；改轉換規則時先改測試。"""
import unittest
from urllib.parse import parse_qsl

from data.search_params import (
    normalize_pairs, canonical_pairs, parse_range, parse_circle, TYPE_STATUS, PROTECTED_STATUS,
)


def norm(qs):
    pairs, removed, notes = normalize_pairs(parse_qsl(qs, keep_blank_values=True))
    d = {}
    for k, v in pairs:
        d.setdefault(k, []).append(v)
    return d, removed, notes


def canon(qs):
    pairs, removed, notes = canonical_pairs(parse_qsl(qs, keep_blank_values=True))
    d = {}
    for k, v in pairs:
        d.setdefault(k, []).append(v)
    return d, removed, notes


class RenameTests(unittest.TestCase):
    def test_simple_renames(self):
        d, _, _ = norm('preservation=浸液&datasetName=abc&higherTaxa=t0001&bioGroup=鳥類')
        self.assertEqual(d['preparations'], ['浸液'])
        self.assertEqual(d['tbiaDatasetID'], ['abc'])
        self.assertEqual(d['higherTaxonID'], ['t0001'])
        self.assertEqual(d['taxonGroup'], ['鳥類'])
        for old in ('preservation', 'datasetName', 'higherTaxa', 'bioGroup'):
            self.assertNotIn(old, d)

    def test_source_database_old_name(self):
        d, _, _ = norm('rightsHolder=科博典藏 (NMNS Collection)&rightsHolder=GBIF&sourceDatabase=科博典藏')
        self.assertEqual(d['sourceDatabase'], ['科博典藏', 'GBIF'])

    def test_list_literal(self):
        d, _, _ = norm("rightsHolder=['臺灣魚類資料庫', '中油生態地圖']&locality=['墾丁']")
        self.assertEqual(d['sourceDatabase'], ['臺灣魚類資料庫', '中油生態保育資料庫'])
        self.assertEqual(d['locality'], ['墾丁'])

    def test_comma_values(self):
        d, _, _ = norm('taxonGroup=鳥類,哺乳類&nativeness=native,invasive&locality=a,b')
        self.assertEqual(d['taxonGroup'], ['鳥類', '哺乳類'])
        self.assertEqual(d['nativeness'], ['native', 'invasive'])
        self.assertEqual(d['locality'], ['a,b'])  # locality 的值本身可能有逗號，不拆

    def test_search_str_flatten(self):
        d, _, _ = norm('from_full=yes&search_str=keyword%3D%E9%B3%A5%26key%3DrightsHolder%26value%3DGBIF')
        self.assertEqual(d['keyword'], ['鳥'])
        self.assertEqual(d['key'], ['sourceDatabase'])
        self.assertNotIn('search_str', d)


class ValueTests(unittest.TestCase):
    def test_taxon_group(self):
        d, _, _ = norm('taxonGroup=Insects&taxonGroup=Birds&taxonGroup=維管束植物&taxonGroup=亂碼')
        self.assertEqual(d['taxonGroup'], ['甲蟲類', '蛾類', '蝶類', '蜻蛉類', '其他昆蟲', '鳥類', '被子植物', '裸子植物', '蕨類植物'])

    def test_habitat(self):
        d, _, _ = norm('habitat=is_marine&habitat=is_freshwater&taxonGroupByHabitat=brackish&habitat=fossil')
        self.assertEqual(d['taxonGroupByHabitat'], ['marine', 'freshWater', 'brackish'])

    def test_has_image(self):
        for old, has, mt in (('n', 'false', None), ('false', 'false', None), ('y', 'true', None),
                             ('true', 'true', None), ('image', 'true', 'image'), ('audio', 'true', 'audio')):
            d, _, _ = norm(f'has_image={old}')
            self.assertEqual(d['hasMedia'], [has], old)
            self.assertEqual(d.get('mediaType'), [mt] if mt else None, old)
            self.assertNotIn('has_image', d)

    def test_media_type_multi(self):
        d, _, _ = norm('hasMedia=true&mediaType=image&mediaType=audio')
        self.assertEqual(d['mediaType'], ['image', 'audio'])
        d, _, _ = norm('hasMedia=true&mediaType=audio,image')
        self.assertEqual(d['mediaType'], ['image', 'audio'])
        d, _, _ = norm('mediaType=image,video,audio')        # 三種全選 = 有任何多媒體
        self.assertEqual(d['hasMedia'], ['true'])
        self.assertNotIn('mediaType', d)
        d, _, _ = norm('has_image=image&has_image=video')    # 前端多選
        self.assertEqual((d['hasMedia'], d['mediaType']), (['true'], ['image', 'video']))
        d, _, _ = norm('has_image=n&has_image=image')
        self.assertEqual(d['hasMedia'], ['false'])
        self.assertNotIn('mediaType', d)

    def test_media_type_requires_has_media(self):
        d, _, _ = norm('mediaType=video')
        self.assertEqual(d['hasMedia'], ['true'])
        d, _, _ = norm('hasMedia=false&mediaType=video')
        self.assertEqual(d['hasMedia'], ['false'])
        self.assertNotIn('mediaType', d)

    def test_is_native(self):
        self.assertEqual(norm('is_native=y')[0]['nativeness'], ['native'])
        self.assertEqual(norm('is_native=true')[0]['nativeness'], ['native'])
        self.assertEqual(norm('is_native=n')[0]['nativeness'], ['naturalized', 'invasive', 'cultured'])

    def test_is_protected(self):
        d, removed, _ = norm('is_protected=y')
        self.assertEqual(d['protectedStatus'], PROTECTED_STATUS)
        self.assertEqual(removed, [])
        d, removed, _ = norm('is_protected=n&record_type=occ')
        self.assertNotIn('protectedStatus', d)
        self.assertNotIn('is_protected', d)
        self.assertEqual(removed, ['是否為保育類：否'])

    def test_type_status(self):
        d, removed, notes = norm('typeStatus=模式')
        self.assertNotIn('typeStatus', d)
        self.assertEqual(removed, ['標本類型：模式'])
        d, removed, _ = norm('typeStatus=一般')
        self.assertNotIn('typeStatus', d)
        self.assertEqual(removed, ['標本類型：一般'])
        d, removed, _ = norm('typeStatus=%25E4%25B8%2580%25E8%2588%25AC')   # 存過兩次編碼的「一般」
        self.assertEqual(removed, ['標本類型：一般'])
        d, _, _ = norm('typeStatus=holotype&typeStatus=PARATYPE&typeStatus=xx')
        self.assertEqual(d['typeStatus'], ['HOLOTYPE', 'PARATYPE'])

    def test_taxon_rank(self):
        for old, new in (('species', 'Species'), ('family', 'Family'), ('Kingdom', 'Kingdom'),
                         ('sub', 'Infraspecies'), ('infraspecies', 'Infraspecies')):
            self.assertEqual(norm(f'taxonRank={old}')[0]['taxonRank'], [new], old)
        self.assertNotIn('taxonRank', norm('taxonRank=family0"XOR(sleep(15))')[0])

    def test_dates(self):
        self.assertEqual(norm('start_date=2024-01-01&end_date=2024-01-31')[0]['eventDate'], ['20240101,20240131'])
        self.assertEqual(norm('start_date=2024-01-01')[0]['eventDate'], ['20240101,*'])
        self.assertEqual(norm('end_date=2024-01-31')[0]['eventDate'], ['*,20240131'])
        self.assertEqual(norm('start_date=2024-01-05&end_date=2024-01-05')[0]['eventDate'], ['20240105'])
        self.assertNotIn('eventDate', norm('start_date=2024-02-01&end_date=2024-01-01')[0])   # 起訖顛倒
        self.assertNotIn('eventDate', norm('start_date=abc')[0])
        d, _, _ = norm('start_date=2024-01-01&end_date=2024-01-31')
        self.assertNotIn('start_date', d)
        self.assertNotIn('end_date', d)

    def test_event_date_v2(self):
        self.assertEqual(norm('eventDate=20240101,*')[0]['eventDate'], ['20240101,*'])
        self.assertEqual(norm('eventDate=*,20240131')[0]['eventDate'], ['*,20240131'])
        self.assertEqual(norm('eventDate=20240101')[0]['eventDate'], ['20240101'])
        self.assertNotIn('eventDate', norm('eventDate=*,*')[0])
        self.assertNotIn('eventDate', norm('eventDate=2024-13-01')[0])

    def test_circle(self):
        d, _, _ = norm('geo_type=circle&center_lat=23.5&center_lon=121.5&circle_radius=3&polygon=x&geojson_id=g')
        self.assertEqual(d['circle'], ['121.5,23.5,3'])
        for k in ('geo_type', 'center_lat', 'center_lon', 'circle_radius', 'polygon', 'geojson_id'):
            self.assertNotIn(k, d)
        self.assertEqual(norm('circle=121.5,23.5,50')[0]['circle'], ['121.5,23.5,50'])
        self.assertNotIn('circle', norm('circle=121.5,23.5,51')[0])
        self.assertNotIn('circle', norm('circle=121.5,23.5,0')[0])
        self.assertNotIn('circle', norm('geo_type=circle&center_lat=23.5&center_lon=121.5&circle_radius=')[0])

    def test_map_and_upload(self):
        d, _, _ = norm('geo_type=map&polygon=P1&polygon=P2&geojson_id=g')
        self.assertEqual(d['polygon'], ['P1', 'P2'])
        self.assertNotIn('geojson_id', d)
        d, _, _ = norm('geo_type=polygon&geojson_id=abc-1&polygon=P1')
        self.assertEqual(d['geojson_id'], ['abc-1'])
        self.assertNotIn('polygon', d)
        self.assertNotIn('geojson_id', norm('geojson_id=../../etc/passwd')[0])
        # 舊程式沒有 geo_type 就不套用地圖條件
        self.assertNotIn('polygon', norm('polygon=P1&circle_radius=1')[0])

    def test_key(self):
        self.assertEqual(norm('key=common_name_c')[0]['key'], ['vernacularName'])
        self.assertEqual(norm('key=rightsHolder')[0]['key'], ['sourceDatabase'])

    def test_other_params_kept(self):
        d, _, _ = norm('page=2&limit=10&orderby=scientificName&from=search')
        self.assertEqual(d['page'], ['2'])
        self.assertEqual(d['orderby'], ['scientificName'])


class IdempotentTests(unittest.TestCase):
    SAMPLES = [
        'record_type=occ&rightsHolder=科博典藏 (NMNS Collection)&has_image=image&is_native=n&is_protected=n'
        '&habitat=is_marine&taxonRank=sub&start_date=2024-01-01&geo_type=circle&center_lat=23.5'
        '&center_lon=121.5&circle_radius=3&taxonGroup=Insects&typeStatus=模式',
        "record_type=col&geo_type=map&polygon=['P1', 'P2']&datasetName=d1&end_date=2024-03-01",
        'from_full=yes&search_str=keyword%3D%E9%B3%A5%26key%3Dcommon_name_c',
        'taxonGroup=鳥類,哺乳類&nativeness=native&protectedStatus=I,II&hasMedia=true&mediaType=image&circle=121,23,0.5',
    ]

    def test_idempotent(self):
        for qs in self.SAMPLES:
            once, _, _ = normalize_pairs(parse_qsl(qs, keep_blank_values=True))
            twice, removed, notes = normalize_pairs(once)
            self.assertEqual(once, twice, qs)
            self.assertEqual((removed, notes), ([], []), qs)


class CanonicalTests(unittest.TestCase):
    def test_whitelist(self):
        d, _, _ = canon('record_type=occ&name=鳥&limit=10&orderby=a&sort=asc&from_full=yes&lang=zh-hant&fbclid=x'
                        '&user_affiliation=a1&csrfmiddlewaretoken=t&is_agreed_report=on&page=1&selected_col=a'
                        '&partner_id=&email=&powershell -command x=1')
        self.assertEqual(d, {'record_type': ['occ'], 'name': ['鳥']})

    def test_invalid_values_dropped(self):
        d, _, _ = canon("record_type=occ&has_image=-1 OR 5*5=25&is_native=n0'XOR(sleep(15))&taxonRank=(select 1)"
                        '&basisOfRecord=xx&current_grid_level=grid_1&organismQuantity=abc&key=a b')
        self.assertEqual(d, {'record_type': ['occ']})

    def test_grid_pair(self):
        self.assertEqual(canon('current_grid_level=grid_1&current_grid=1_2')[0],
                         {'current_grid_level': ['grid_1'], 'current_grid': ['1_2']})

    def test_empty_values(self):
        d, _, _ = canon('record_type=occ&name=&county=&circle_radius=')
        self.assertEqual(d, {'record_type': ['occ']})


class HelperTests(unittest.TestCase):
    def test_parse_range(self):
        self.assertEqual(parse_range('20240101,20240131'), ('20240101', '20240131'))
        self.assertEqual(parse_range('20240101,*'), ('20240101', None))
        self.assertEqual(parse_range('*,20240131'), (None, '20240131'))
        self.assertEqual(parse_range('20240101'), ('20240101', '20240101'))
        self.assertIsNone(parse_range('*,*'))
        self.assertIsNone(parse_range('20240201,20240101'))
        self.assertIsNone(parse_range(''))

    def test_parse_circle(self):
        self.assertEqual(parse_circle('121.5,23.5,0.2'), (121.5, 23.5, 0.2))
        self.assertIsNone(parse_circle('200,23.5,1'))
        self.assertIsNone(parse_circle('121,23'))
        self.assertIsNone(parse_circle('121,23,abc'))


if __name__ == '__main__':
    unittest.main()
