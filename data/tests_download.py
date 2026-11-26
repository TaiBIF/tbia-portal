"""7.1 下載檔案的值以 API v2 為準：紀錄下載（write_download_rows）、名錄下載（format_species_download）
執行：python -m unittest data.tests_download -v（容器內，需要 Django 設定，不需要 DB / Solr）"""
import csv
import io
import os
import unittest

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'conf.settings')
django.setup()

from api.v2_params import format_occurrence  # noqa: E402
from data.fields import SPECIES_DOWNLOAD_COLUMNS  # noqa: E402
from data.utils import write_download_rows, format_species_download  # noqa: E402
from data.search_params import NATIVENESS, PROTECTED_STATUS  # noqa: E402


def taxa_doc(**kw):
    """taxa core 的一筆（舊欄位名），值的寫法照 source_taicol_for_tbia_solr CSV"""
    d = {'id': 't0000001', 'name_author': 'Linnaeus, 1758', 'taxonRank': 'species', 'common_name_c': '測試種',
         'bioGroup': '鳥類', 'kingdom': 'Animalia', 'kingdom_c': '動物界', 'is_endemic': 'f', 'alien_type': 'native',
         'protected': '', 'sensitive': '', 'cites': '', 'iucn': '', 'redlist': '', 'is_fossil': '',
         'is_terrestrial': 't', 'is_freshwater': '', 'is_brackish': '', 'is_marine': 'f'}
    d.update(kw)
    return d


class SpeciesDownloadTest(unittest.TestCase):
    def one(self, **kw):
        return format_species_download([taxa_doc(**kw)])[0]

    def test_columns(self):
        row = self.one()
        self.assertEqual(list(row), ['taxonID'] + [c for _, c in SPECIES_DOWNLOAD_COLUMNS])
        self.assertEqual(row['scientificNameAuthorship'], 'Linnaeus, 1758')
        self.assertEqual(row['vernacularName'], '測試種')
        self.assertEqual(row['taxonGroup'], '鳥類')

    def test_taxon_rank_same_as_api(self):
        for solr, api in [('species', 'Species'), ('special form', 'Special Form'),
                          ('hybrid formula', 'Hybrid Formula'), ('subfamily', 'Subfamily')]:
            self.assertEqual(self.one(taxonRank=solr)['taxonRank'], api)
            self.assertEqual(format_occurrence({'taxonRank': solr}, False, {})['taxonRank'], api)

    def test_protected_status(self):
        for v in ['I', 'II', 'III']:
            self.assertEqual(self.one(protected=v)['protectedStatus'], v)
        self.assertEqual(self.one(protected='1')['protectedStatus'], 'CHPA')
        self.assertEqual(self.one(protected='')['protectedStatus'], '')
        for v in ['I', 'II', 'III', '1']:
            self.assertIn(self.one(protected=v)['protectedStatus'], PROTECTED_STATUS)

    def test_nativeness(self):
        for v in NATIVENESS:
            self.assertEqual(self.one(alien_type=v)['nativeness'], v)
        self.assertEqual(self.one(alien_type='cultivated')['nativeness'], 'cultured')
        self.assertEqual(self.one(alien_type='')['nativeness'], '')

    def test_booleans(self):
        row = self.one(is_endemic='t', is_fossil='f', is_freshwater='')
        self.assertEqual((row['isEndemic'], row['isFossil'], row['isFreshwater']), ('true', 'false', ''))
        row = self.one(is_endemic=True, is_fossil=False, is_marine=1)   # Solr 布林欄位回傳 JSON true / false
        self.assertEqual((row['isEndemic'], row['isFossil'], row['isMarine']), ('true', 'false', 'true'))

    def test_other_values_as_is(self):
        row = self.one(cites='I/II/NC', iucn='LR/cd', redlist='DD', sensitive='座標不開放')
        self.assertEqual((row['citesAppendix'], row['iucnRedListCategory'], row['taiwanRedListCategory'],
                          row['suggestedSensitiveCategory']), ('I/II/NC', 'LR/cd', 'DD', '座標不開放'))

    def test_taiwan_red_list(self):
        # 11/26：taxa core 的國家評估代碼 NCR 等 → CR 等；其他值不變
        for src, out in [('NCR', 'CR'), ('NEN', 'EN'), ('NVU', 'VU'), ('NNT', 'NT'), ('NLC', 'LC'),
                         ('EX', 'EX'), ('EW', 'EW'), ('RE', 'RE'), ('DD', 'DD'), ('NA', 'NA'), ('NE', 'NE'), ('', '')]:
            self.assertEqual(self.one(redlist=src)['taiwanRedListCategory'], out)
        self.assertEqual(self.one(iucn='CR')['iucnRedListCategory'], 'CR')

    def test_list_values(self):
        self.assertEqual(self.one(taxonRank=['variety'])['taxonRank'], 'Variety')


class RecordDownloadTest(unittest.TestCase):
    def write(self, header, rows, out_cols):
        src = io.StringIO()
        w = csv.writer(src)
        w.writerow(header)
        w.writerows(rows)
        out = io.StringIO()
        write_download_rows([src.getvalue().encode('utf-8')], csv.writer(out), out_cols)
        return list(csv.reader(io.StringIO(out.getvalue())))

    def test_taxon_rank_and_dates_same_as_api(self):
        cols = ['tbiaID', 'taxonRank', 'created']
        rows = self.write(['tbiaID', 'taxonRank', 'created'],
                          [['a', 'special form', '2026-11-05T01:23:45Z'], ['b', '', '2026-11-05T01:23:45Z']], cols)
        api = format_occurrence({'taxonRank': 'special form', 'created': '2026-11-05T01:23:45Z'}, False, {})
        self.assertEqual(rows[0], ['a', api['taxonRank'], api['created']])
        self.assertEqual(rows[0][1:], ['Special Form', '20261105 012345'])
        self.assertEqual(rows[1][1], '')


if __name__ == '__main__':
    unittest.main()
