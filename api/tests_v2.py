"""5.2 API v2 參數驗證與回傳欄位的單元測試（不需要 Django / DB / Solr）
執行：python -m unittest api.tests_v2 -v"""
import ast
import re
import unittest
from pathlib import Path

from api.v2_params import (
    ParamError, parse_limit, occurrence_query, format_occurrence, taxon_rank_v2,
)
from data.fields import API_OCCURRENCE_FIELDS, DOWNLOAD_FIELDS
from data.search_params import (
    normalize_pairs, TAICOL_RANKS, TAXON_RANK_GROUPS, INFRASPECIES_RANKS, RANK_SOLR_VALUE, RANK_ZH,
)


def q(params, restricted=False):
    return occurrence_query({k: (v if isinstance(v, list) else [v]) for k, v in params.items()}, restricted)


class FieldsTest(unittest.TestCase):
    def test_same_fields_as_download(self):
        self.assertEqual(set(API_OCCURRENCE_FIELDS), set(DOWNLOAD_FIELDS))
        self.assertEqual(len(API_OCCURRENCE_FIELDS), 77)

    def test_partner_name_after_partner_id(self):
        i = API_OCCURRENCE_FIELDS.index('tbiaPartnerID')
        self.assertEqual(API_OCCURRENCE_FIELDS[i + 1], 'partnerName')

    def test_utils_has_no_own_rank_lists(self):
        # 階層表只在 data/search_params.py 定義一份（11/20），utils 不能再自己定義
        src = (Path(__file__).resolve().parents[1] / 'data' / 'utils.py').read_text(encoding='utf-8')
        for name in ('TAXON_RANK_GROUPS', 'INFRASPECIES_RANKS', 'RANK_SOLR_VALUE', 'VALID_TAXON_RANKS'):
            self.assertIsNone(re.search(rf'^{name} =', src, re.M), name)


class RankTableTest(unittest.TestCase):
    """TaiCOL ranks 表（taicol-web 2026-11-20 匯出，57 個）"""
    def test_57_ranks_unique(self):
        keys = [k for k, _, _ in TAICOL_RANKS]
        ens = [en for _, en, _ in TAICOL_RANKS]
        self.assertEqual(len(keys), 57)
        self.assertEqual(len(set(keys)), 57)
        self.assertEqual(len(set(ens)), 57)

    def test_groups_cover_every_rank_once(self):
        keys = [g[0] for g in TAXON_RANK_GROUPS if g[0] != 'sub'] + [r for g in TAXON_RANK_GROUPS for r, _ in g[2]]
        self.assertEqual(sorted(keys), sorted(k for k, _, _ in TAICOL_RANKS))
        for g in TAXON_RANK_GROUPS:
            for r, label in g[2]:
                self.assertEqual(label, RANK_ZH[r])

    def test_solr_values(self):
        self.assertIn('"special form"', INFRASPECIES_RANKS)
        self.assertIn('lusus', INFRASPECIES_RANKS)
        for k in ('"hybrid formula"', '"cultivar group"', 'cultivar'):
            self.assertNotIn(k, INFRASPECIES_RANKS)
        self.assertEqual(RANK_SOLR_VALUE['hybrid-formula'], '"hybrid formula"')


class LimitTest(unittest.TestCase):
    def test_default_and_cap(self):
        self.assertEqual(parse_limit({}), 20)
        self.assertEqual(parse_limit({'limit': ['1000']}), 1000)
        self.assertEqual(parse_limit({'limit': ['5000']}), 1000)

    def test_invalid(self):
        for v in ['0', '-1', 'abc', '1.5']:
            with self.assertRaises(ParamError):
                parse_limit({'limit': [v]})


class VocabTest(unittest.TestCase):
    def test_habitat_freshwater_only(self):
        site, _ = q({'taxonGroupByHabitat': 'marine,freshwater'})
        self.assertEqual(site['taxonGroupByHabitat'], ['marine', 'freshwater'])
        with self.assertRaises(ParamError) as cm:
            q({'taxonGroupByHabitat': 'freshWater'})
        self.assertIn('freshwater', str(cm.exception))
        with self.assertRaises(ParamError):
            q({'taxonGroupByHabitat': 'fossil'})

    def test_case_sensitive(self):
        with self.assertRaises(ParamError):
            q({'taxonRank': 'species'})
        with self.assertRaises(ParamError):
            q({'taxonRank': 'Special form'})
        with self.assertRaises(ParamError):
            q({'typeStatus': 'Holotype'})

    def test_taxon_rank_full_taicol(self):
        site, fq = q({'taxonRank': 'Subspecies'})
        self.assertIn('taxonRank:"subspecies"', fq)
        self.assertNotIn('taxonRank', site)   # 網站 normalize 只認 8 個，API 自己組條件
        _, fq = q({'taxonRank': 'Special Form'})
        self.assertIn('taxonRank:"special form"', fq)
        _, fq = q({'taxonRank': 'Group'})
        self.assertIn('taxonRank:"cultivar group"', fq)
        _, fq = q({'taxonRank': 'Infraspecies'})
        self.assertTrue(any(f.startswith('taxonRank:(subspecies OR') for f in fq))

    def test_taxon_rank_single(self):
        with self.assertRaises(ParamError):
            q({'taxonRank': 'Genus,Species'})

    def test_multi_comma_and_repeated(self):
        site, _ = q({'taxonGroup': ['鳥類,哺乳類', '鳥類', '魚類']})
        self.assertEqual(site['taxonGroup'], ['鳥類', '哺乳類', '魚類'])
        with self.assertRaises(ParamError):
            q({'taxonGroup': '昆蟲'})   # 舊群名，v2 API 不轉換

    def test_basis_of_record(self):
        site, _ = q({'basisOfRecord': 'PreservedSpecimen'})
        self.assertEqual(site['basisOfRecord'], ['PreservedSpecimen'])
        with self.assertRaises(ParamError):
            q({'basisOfRecord': 'preservedspecimen'})


class MediaTest(unittest.TestCase):
    def test_media_type_needs_has_media(self):
        with self.assertRaises(ParamError):
            q({'mediaType': 'image'})
        with self.assertRaises(ParamError):
            q({'hasMedia': 'false', 'mediaType': 'image'})
        site, _ = q({'hasMedia': 'true', 'mediaType': 'image,audio'})
        self.assertEqual(site['mediaType'], ['image', 'audio'])

    def test_all_types_is_has_media(self):
        site, _ = q({'hasMedia': 'true', 'mediaType': 'image,video,audio'})
        self.assertEqual(site['hasMedia'], ['true'])
        self.assertNotIn('mediaType', site)

    def test_bool(self):
        with self.assertRaises(ParamError):
            q({'hasMedia': 'True'})
        with self.assertRaises(ParamError):
            q({'isCollection': '1'})


class CollectionTest(unittest.TestCase):
    def test_is_collection(self):
        site, fq = q({'isCollection': 'true'})
        self.assertEqual(site['record_type'], ['col'])
        site, fq = q({'isCollection': 'false'})
        self.assertIn('recordType:occ', fq)


class DateTest(unittest.TestCase):
    def test_created_modified(self):
        _, fq = q({'created': '20240101'})
        self.assertIn('created:[2024-01-01T00:00:00Z TO 2024-01-01T23:59:59Z]', fq)
        _, fq = q({'modified': '20240101,*'})
        self.assertIn('modified:[2024-01-01T00:00:00Z TO *]', fq)
        _, fq = q({'created': '*,20240131'})
        self.assertIn('created:[* TO 2024-01-31T23:59:59Z]', fq)

    def test_invalid(self):
        for k, v in [('created', '2024-01-01'), ('eventDate', '20240230'), ('modified', '20240201,20240101'),
                     ('eventDate', '*,*')]:
            with self.assertRaises(ParamError, msg=f'{k}={v}'):
                q({k: v})

    def test_event_date_to_site(self):
        site, _ = q({'eventDate': '20240101,20240131'})
        self.assertEqual(site['eventDate'], ['20240101,20240131'])


class SpatialTest(unittest.TestCase):
    def test_bounded_by(self):
        _, fq = q({'boundedBy': '122,23,121,22'})
        self.assertIn('location_rpt:[22.0,121.0 TO 23.0,122.0]', fq)
        _, fq = q({'boundedBy': '122,23,121,22'}, restricted=True)
        self.assertIn('(location_rpt:[22.0,121.0 TO 23.0,122.0] OR raw_location_rpt:[22.0,121.0 TO 23.0,122.0])', fq)
        for v in ['121,23,122,22', '122,23,121', 'a,b,c,d', '200,23,121,22']:
            with self.assertRaises(ParamError, msg=v):
                q({'boundedBy': v})

    def test_circle(self):
        _, fq = q({'circle': '121.5,23.5,50'})
        self.assertIn('_query_:"{!geofilt sfield=location_rpt pt=23.5,121.5 d=50.0}"', fq)
        _, fq = q({'circle': '121.5,23.5,0.3'}, restricted=True)
        self.assertTrue(any('raw_location_rpt' in f and 'location_rpt pt' in f for f in fq))
        for v in ['121.5,23.5,51', '121.5,23.5,0', '121.5,23.5', '121.5,95,1']:
            with self.assertRaises(ParamError, msg=v):
                q({'circle': v})

    def test_polygon(self):
        site, _ = q({'polygon': 'POLYGON((121 22,122 22,122 23,121 23,121 22))'})
        self.assertIn('polygon', site)
        for v in ['POLYGON((121 22,122 22,122 23))', 'POLYGON((0 0,1 1,1 0,0 1,0 0))',
                  'POINT(121 22)', 'MULTIPOLYGON(((121 22,122 22,122 23,121 23,121 22)))', 'abc']:
            with self.assertRaises(ParamError, msg=v):
                q({'polygon': v})


class IdTest(unittest.TestCase):
    def test_ids_and_sources(self):
        _, fq = q({'tbiaID': 'abc', 'tbiaPartnerID': 'p1,p2', 'sourceDatabase': '科博典藏',
                   'datasetID': 'd"1', 'tbiaDatasetID': 't1'})
        self.assertIn('id:"abc"', fq)
        self.assertIn('tbiaPartnerID:("p1" OR "p2")', fq)
        self.assertIn('sourceDatabase:("科博典藏")', fq)
        self.assertIn('datasetID:("d\\"1")', fq)
        self.assertIn('tbiaDatasetID:("t1")', fq)

    def test_apikey_param_rejected(self):
        with self.assertRaises(ParamError) as cm:
            q({'apikey': 'xxx'})
        self.assertIn('Authorization', str(cm.exception))

    def test_unlisted_params_ignored(self):
        site, fq = q({'locality': '綠島', 'organismQuantity': '3', 'rightsHolder': 'x'})
        self.assertEqual((site, fq), ({}, []))


class NormalizeInvariantTest(unittest.TestCase):
    """交給網站 create_search_query 的參數已是 v2 標準形式，網站的 normalize 不應再改變它們"""
    def test_invariant(self):
        site, _ = q({
            'name': '臺灣獼猴', 'taxonID': 't0001', 'higherTaxonID': 't0002', 'taxonGroup': '鳥類,蝸牛與貝類',
            'taxonGroupByHabitat': 'terrestrial,freshwater,brackish,marine',
            'nativeness': 'native,cultured', 'protectedStatus': 'I,CHPA', 'typeStatus': 'HOLOTYPE,TOPOTYPE',
            'hasMedia': 'true', 'mediaType': 'image', 'basisOfRecord': 'HumanObservation',
            'eventDate': '20240101,*', 'county': '臺東縣', 'municipality': '綠島鄉', 'isCollection': 'true',
            'recordedBy': 'A', 'resourceContacts': 'B', 'preparations': '浸液',
            'occurrenceID': 'o1', 'catalogNumber': 'c1', 'recordNumber': 'r1',
            'polygon': 'POLYGON((121 22,122 22,122 23,121 23,121 22))',
        })
        pairs = [(k, v) for k, vals in site.items() for v in vals]
        out, removed, notes = normalize_pairs(pairs)
        self.assertEqual(sorted(out), sorted(pairs))
        self.assertEqual((removed, notes), ([], []))


class FormatTest(unittest.TestCase):
    DOC = {
        'tbiaID': 'x1', 'created': '2026-11-05T01:23:45Z', 'modified': '2026-11-06T13:00:00Z',
        'decimalLatitude': 23.1, 'decimalLongitude': 121.1, 'county': '臺東縣', 'countyCode': '10014',
        'rawDecimalLatitude': 23.12345, 'rawDecimalLongitude': 121.12345, 'rawCounty': '花蓮縣',
        'rawCountyCode': '10015', 'rawVerbatimLatitude': '23.12345', 'taxonRank': 'subspecies',
        'tbiaPartnerID': 'p1', 'dataGeneralizations': '公開座標由 TBIA 統一模糊化，取至小數點後 1 位',
        'locality': '', 'year': 2024,
    }

    def test_public(self):
        r = format_occurrence(self.DOC, False, {'p1': '國立自然科學博物館'})
        self.assertEqual(list(r), API_OCCURRENCE_FIELDS)
        self.assertEqual(r['decimalLatitude'], 23.1)
        self.assertEqual(r['county'], '臺東縣')
        self.assertIsNone(r['verbatimLatitude'])
        self.assertIsNone(r['locality'])
        self.assertIsNone(r['eventID'])
        self.assertEqual(r['created'], '20261105 012345')
        self.assertEqual(r['taxonRank'], 'Subspecies')
        self.assertEqual(r['partnerName'], '國立自然科學博物館')
        self.assertEqual(r['year'], 2024)
        self.assertFalse(any(k.startswith('raw') for k in r))

    def test_restricted(self):
        r = format_occurrence(self.DOC, True, {})
        self.assertEqual(r['decimalLatitude'], 23.12345)
        self.assertEqual(r['verbatimLatitude'], '23.12345')
        self.assertEqual((r['county'], r['countyCode']), ('花蓮縣', '10015'))
        self.assertEqual(r['municipality'], None)
        self.assertEqual(r['dataGeneralizations'], self.DOC['dataGeneralizations'])
        self.assertIsNone(r['partnerName'])
        self.assertFalse(any(k.startswith('raw') for k in r))

    def test_taxon_rank(self):
        self.assertEqual(taxon_rank_v2('species'), 'Species')
        self.assertEqual(taxon_rank_v2('variety'), 'Variety')
        self.assertEqual(taxon_rank_v2('special form'), 'Special Form')
        self.assertEqual(taxon_rank_v2('hybrid formula'), 'Hybrid Formula')
        self.assertEqual(taxon_rank_v2('cultivar group'), 'Group')
        self.assertEqual(taxon_rank_v2('subfamily'), 'Subfamily')
        self.assertEqual(taxon_rank_v2('xyz rank'), 'Xyz rank')   # ranks 表沒有的值
        self.assertIsNone(taxon_rank_v2(None))


if __name__ == '__main__':
    unittest.main()
