from conf.settings import env
from data.fields import OCC_CARD_FIELDS, COL_CARD_FIELDS, TAXA_CARD_FIELDS

SOLR_PREFIX = env('SOLR_PREFIX')

# 全站搜尋卡片欄位定義在 data/fields.py（records 用 v2 名稱、taxa core 用舊名）
occ_fields = OCC_CARD_FIELDS
col_fields = COL_CARD_FIELDS


def create_facet_list(record_type):
    if record_type == 'col':
        field_list = col_fields
    else:
        field_list = occ_fields
    facets = {}
    facets['facet'] = {}
    for f in field_list:
        facets['facet'][f] = {
            'type': 'terms',
            'field': f,
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': False,
            'facet':{
                'taxonID':{
                    'type': 'terms',
                    'field': 'taxonID',
                    'limit': 30,
                    'numBuckets': False,
                },
            } 
        }
    return facets


def create_taxon_facet_list():
    # taxa core 欄位（舊名，D21）
    taxon_fields = TAXA_CARD_FIELDS

    facets = {}
    facets['facet'] = {}

    for f in taxon_fields:
        facets['facet'][f] = {
                'type': 'terms',
                'field': f,
                'mincount': 1,
                'allBuckets': True,
                'numBuckets': False,
        }

    return facets