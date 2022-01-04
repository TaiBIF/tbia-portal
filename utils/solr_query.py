from conf.settings import env
import urllib
import requests
import json

if env in ['dev']:
    SOLR_PREFIX = 'http://127.0.0.1:8983/solr/'
else:
    SOLR_PREFIX = 'http://solr:8983/solr/'


JSON_FACET_MAP = {
    'tbia_collection': {
        'scientificName': {
            'type': 'terms',
            'field': 'scientificName',
            'mincount': 1,
            'limit': -1,
            'facet':{
                'scientificName':{
                    'type': 'terms',
                    'field': 'scientificName',
                    'limit': -1,
                },
            }        
        },
        'common_name_c': {
            'type': 'terms',
            'field': 'common_name_c',
            'mincount': 1,
            'limit': -1,
            'facet':{
                'scientificName':{
                    'type': 'terms',
                    'field': 'scientificName',
                    'limit': -1,
                },
            }
        },
        'alternative_name_c': {
            'type': 'terms',
            'field': 'alternative_name_c',
            'mincount': 1,
            'limit': -1,
            'facet':{
                    'scientificName':{
                        'type': 'terms',
                        'field': 'scientificName',
                        'limit': -1,
                    },
                }
        },
        'synonyms': {
            'type': 'terms',
            'field': 'synonyms',
            'mincount': 1,
            'limit': -1,
            'facet':{
                    'scientificName':{
                        'type': 'terms',
                        'field': 'scientificName',
                        'limit': -1,
                    },
                }
        },
        'rightsHolder': {
            'type': 'terms',
            'field': 'rightsHolder',
            'mincount': 1,
            'limit': -1,
            'facet':{
                    'scientificName':{
                        'type': 'terms',
                        'field': 'scientificName',
                        'limit': -1,
                    },
                }
        },
        'sensitiveCategory': {
            'type': 'terms',
            'field': 'sensitiveCategory',
            'mincount': 1,
            'limit': -1,
            'facet':{
                    'scientificName':{
                        'type': 'terms',
                        'field': 'scientificName',
                        'limit': -1,
                    },
                }
        },
        'taxonRank': {
            'type': 'terms',
            'field': 'taxonRank',
            'mincount': 1,
            'limit': -1,
            'facet':{
                    'scientificName':{
                        'type': 'terms',
                        'field': 'scientificName',
                        'limit': -1,
                    },
                }
        },
        'locality': {
            'type': 'terms',
            'field': 'locality',
            'mincount': 1,
            'limit': -1,
            'facet':{
                    'scientificName':{
                        'type': 'terms',
                        'field': 'scientificName',
                        'limit': -1,
                    },
                }
        },
        'recordedBy': {
            'type': 'terms',
            'field': 'recordedBy',
            'mincount': 1,
            'limit': -1,
            'facet':{
                    'scientificName':{
                        'type': 'terms',
                        'field': 'scientificName',
                        'limit': -1,
                    },
                }
        },
        'typeStatus': {
            'type': 'terms',
            'field': 'typeStatus',
            'mincount': 1,
            'limit': -1,
            'facet':{
                    'scientificName':{
                        'type': 'terms',
                        'field': 'scientificName',
                        'limit': -1,
                    },
                }
        },
        'preservation': {
            'type': 'terms',
            'field': 'preservation',
            'mincount': 1,
            'limit': -1,
            'facet':{
                    'scientificName':{
                        'type': 'terms',
                        'field': 'scientificName',
                        'limit': -1,
                    },
                }
        },
        'datasetName': {
            'type': 'terms',
            'field': 'datasetName',
            'mincount': 1,
            'limit': -1,
            'facet':{
                    'scientificName':{
                        'type': 'terms',
                        'field': 'scientificName',
                        'limit': -1,
                    },
                }
        },
        'license': {
            'type': 'terms',
            'field': 'license',
            'mincount': 1,
            'limit': -1,
            'facet':{
                    'scientificName':{
                        'type': 'terms',
                        'field': 'scientificName',
                        'limit': -1,
                    },
                }
        },

        'kingdom': {
            'type': 'terms',
            'field': 'kingdom',
            'mincount': 1,
            'limit': -1,
            'facet':{
                    'scientificName':{
                        'type': 'terms',
                        'field': 'scientificName',
                        'limit': -1,
                    },
                }
        },
        'phylum': {
            'type': 'terms',
            'field': 'phylum',
            'mincount': 1,
            'limit': -1,
            'facet':{
                    'scientificName':{
                        'type': 'terms',
                        'field': 'scientificName',
                        'limit': -1,
                    },
                }
        },
        'class': {
            'type': 'terms',
            'field': 'class',
            'mincount': 1,
            'limit': -1,
            'facet':{
                    'scientificName':{
                        'type': 'terms',
                        'field': 'scientificName',
                        'limit': -1,
                    },
                }
        },
        'order': {
            'type': 'terms',
            'field': 'order',
            'mincount': 1,
            'limit': -1,
            'facet':{
                    'scientificName':{
                        'type': 'terms',
                        'field': 'scientificName',
                        'limit': -1,
                    },
                }
        },
        'family': {
            'type': 'terms',
            'field': 'family',
            'mincount': 1,
            'limit': -1,
            'facet':{
                    'scientificName':{
                        'type': 'terms',
                        'field': 'scientificName',
                        'limit': -1,
                    },
                }
        },
        'genus': {
            'type': 'terms',
            'field': 'genus',
            'mincount': 1,
            'limit': -1,
            'facet':{
                    'scientificName':{
                        'type': 'terms',
                        'field': 'scientificName',
                        'limit': -1,
                    },
                }
        },
        'species': {
            'type': 'terms',
            'field': 'species',
            'mincount': 1,
            'limit': -1,
            'facet':{
                    'scientificName':{
                        'type': 'terms',
                        'field': 'scientificName',
                        'limit': -1,
                    },
                }
        },
        'kingdom_c': {
            'type': 'terms',
            'field': 'kingdom_c',
            'mincount': 1,
            'limit': -1,
            'facet':{
                    'scientificName':{
                        'type': 'terms',
                        'field': 'scientificName',
                        'limit': -1,
                    },
                }
        },
        'phylum_c': {
            'type': 'terms',
            'field': 'phylum_c',
            'mincount': 1,
            'limit': -1,
            'facet':{
                    'scientificName':{
                        'type': 'terms',
                        'field': 'scientificName',
                        'limit': -1,
                    },
                }
        },
        'class_c': {
            'type': 'terms',
            'field': 'class_c',
            'mincount': 1,
            'limit': -1,
            'facet':{
                    'scientificName':{
                        'type': 'terms',
                        'field': 'scientificName',
                        'limit': -1,
                    },
                }
        },
        'order_c': {
            'type': 'terms',
            'field': 'order_c',
            'mincount': 1,
            'limit': -1,
            'facet':{
                    'scientificName':{
                        'type': 'terms',
                        'field': 'scientificName',
                        'limit': -1,
                    },
                }
        },
        'family_c': {
            'type': 'terms',
            'field': 'family_c',
            'mincount': 1,
            'limit': -1,
            'facet':{
                    'scientificName':{
                        'type': 'terms',
                        'field': 'scientificName',
                        'limit': -1,
                    },
                }
        },
        'genus_c': {
            'type': 'terms',
            'field': 'genus_c',
            'mincount': 1,
            'limit': -1,
            'facet':{
                    'scientificName':{
                        'type': 'terms',
                        'field': 'scientificName',
                        'limit': -1,
                    },
                }
        },
        'id': {
            'type': 'terms',
            'field': 'id',
            'mincount': 1,
            'limit': -1,
        }
    },
    'tbia_occurrence': {
        'scientificName': {
            'type': 'terms',
            'field': 'scientificName',
            'mincount': 1,
            'limit': -1,
            'facet':{
                'scientificName':{
                    'type': 'terms',
                    'field': 'scientificName',
                    'limit': -1,
                },
            }
        },
        'common_name_c': {
            'type': 'terms',
            'field': 'common_name_c',
            'mincount': 1,
            'limit': -1,
            'facet':{
                'scientificName':{
                    'type': 'terms',
                    'field': 'scientificName',
                    'limit': -1,
                },
            }
        },
        'alternative_name_c': {
            'type': 'terms',
            'field': 'alternative_name_c',
            'mincount': 1,
            'limit': -1,
            'facet':{
                    'scientificName':{
                        'type': 'terms',
                        'field': 'scientificName',
                        'limit': -1,
                    },
                }
        },
        'synonyms': {
            'type': 'terms',
            'field': 'synonyms',
            'mincount': 1,
            'limit': -1,
            'facet':{
                    'scientificName':{
                        'type': 'terms',
                        'field': 'scientificName',
                        'limit': -1,
                    },
                }
        },
        'rightsHolder': {
            'type': 'terms',
            'field': 'rightsHolder',
            'mincount': 1,
            'limit': -1,
            'facet':{
                    'scientificName':{
                        'type': 'terms',
                        'field': 'scientificName',
                        'limit': -1,
                    }
                }
        },
        'sensitiveCategory': {
            'type': 'terms',
            'field': 'sensitiveCategory',
            'mincount': 1,
            'limit': -1,
            'facet':{
                    'scientificName':{
                        'type': 'terms',
                        'field': 'scientificName',
                        'limit': -1,
                    }
                }
        },
        'taxonRank': {
            'type': 'terms',
            'field': 'taxonRank',
            'mincount': 1,
            'limit': -1,
            'facet':{
                    'scientificName':{
                        'type': 'terms',
                        'field': 'scientificName',
                        'limit': -1,
                    }
                }
        },
        'locality': {
            'type': 'terms',
            'field': 'locality',
            'mincount': 1,
            'limit': -1,
            'facet':{
                    'scientificName':{
                        'type': 'terms',
                        'field': 'scientificName',
                        'limit': -1,
                    }
                }
        },
        'recordedBy': {
            'type': 'terms',
            'field': 'recordedBy',
            'mincount': 1,
            'limit': -1,
            'facet':{
                    'scientificName':{
                        'type': 'terms',
                        'field': 'scientificName',
                        'limit': -1,
                    }
                }
        },
        'basisOfRecord': {
            'type': 'terms',
            'field': 'basisOfRecord',
            'mincount': 1,
            'limit': -1,
            'facet':{
                    'scientificName':{
                        'type': 'terms',
                        'field': 'scientificName',
                        'limit': -1,
                    }
                }
        },
        'datasetName': {
            'type': 'terms',
            'field': 'datasetName',
            'mincount': 1,
            'limit': -1,
            'facet':{
                    'scientificName':{
                        'type': 'terms',
                        'field': 'scientificName',
                        'limit': -1,
                    }
                }
        },
        'license': {
            'type': 'terms',
            'field': 'license',
            'mincount': 1,
            'limit': -1,
            'facet':{
                    'scientificName':{
                        'type': 'terms',
                        'field': 'scientificName',
                        'limit': -1,
                    }
                }
        },

        'kingdom': {
            'type': 'terms',
            'field': 'kingdom',
            'mincount': 1,
            'limit': -1,
            'facet':{
                    'scientificName':{
                        'type': 'terms',
                        'field': 'scientificName',
                        'limit': -1,
                    },
                }
        },
        'phylum': {
            'type': 'terms',
            'field': 'phylum',
            'mincount': 1,
            'limit': -1,
            'facet':{
                    'scientificName':{
                        'type': 'terms',
                        'field': 'scientificName',
                        'limit': -1,
                    },
                }
        },
        'class': {
            'type': 'terms',
            'field': 'class',
            'mincount': 1,
            'limit': -1,
            'facet':{
                    'scientificName':{
                        'type': 'terms',
                        'field': 'scientificName',
                        'limit': -1,
                    },
                }
        },
        'order': {
            'type': 'terms',
            'field': 'order',
            'mincount': 1,
            'limit': -1,
            'facet':{
                    'scientificName':{
                        'type': 'terms',
                        'field': 'scientificName',
                        'limit': -1,
                    },
                }
        },
        'family': {
            'type': 'terms',
            'field': 'family',
            'mincount': 1,
            'limit': -1,
            'facet':{
                    'scientificName':{
                        'type': 'terms',
                        'field': 'scientificName',
                        'limit': -1,
                    },
                }
        },
        'genus': {
            'type': 'terms',
            'field': 'genus',
            'mincount': 1,
            'limit': -1,
            'facet':{
                    'scientificName':{
                        'type': 'terms',
                        'field': 'scientificName',
                        'limit': -1,
                    },
                }
        },
        'species': {
            'type': 'terms',
            'field': 'species',
            'mincount': 1,
            'limit': -1,
            'facet':{
                    'scientificName':{
                        'type': 'terms',
                        'field': 'scientificName',
                        'limit': -1,
                    },
                }
        },
        'kingdom_c': {
            'type': 'terms',
            'field': 'kingdom_c',
            'mincount': 1,
            'limit': -1,
            'facet':{
                    'scientificName':{
                        'type': 'terms',
                        'field': 'scientificName',
                        'limit': -1,
                    },
                }
        },
        'phylum_c': {
            'type': 'terms',
            'field': 'phylum_c',
            'mincount': 1,
            'limit': -1,
            'facet':{
                    'scientificName':{
                        'type': 'terms',
                        'field': 'scientificName',
                        'limit': -1,
                    },
                }
        },
        'class_c': {
            'type': 'terms',
            'field': 'class_c',
            'mincount': 1,
            'limit': -1,
            'facet':{
                    'scientificName':{
                        'type': 'terms',
                        'field': 'scientificName',
                        'limit': -1,
                    },
                }
        },
        'order_c': {
            'type': 'terms',
            'field': 'order_c',
            'mincount': 1,
            'limit': -1,
            'facet':{
                    'scientificName':{
                        'type': 'terms',
                        'field': 'scientificName',
                        'limit': -1,
                    },
                }
        },
        'family_c': {
            'type': 'terms',
            'field': 'family_c',
            'mincount': 1,
            'limit': -1,
            'facet':{
                    'scientificName':{
                        'type': 'terms',
                        'field': 'scientificName',
                        'limit': -1,
                    },
                }
        },
        'genus_c': {
            'type': 'terms',
            'field': 'genus_c',
            'mincount': 1,
            'limit': -1,
            'facet':{
                    'scientificName':{
                        'type': 'terms',
                        'field': 'scientificName',
                        'limit': -1,
                    },
                }
        },
        'id': {
            'type': 'terms',
            'field': 'id',
            'mincount': 1,
            'limit': -1,
        }
    },
}

class SolrQuery(object):
    def __init__(self, core, facet_values=[]):
        self.solr_tuples = [
            ('q.op', 'OR'),
            ('wt', 'json'),
        ]
        self.core = core
        self.facet_values = facet_values
        self.solr_error = ''
        self.solr_response = {}
        self.solr_url = ''
        self.solr_q = '*:*'
    def generate_solr_url(self, req_lists=[]):
        for key, values in req_lists:
            if key == 'q' and values:
                self.solr_q = values
            elif key == 'offset':
                self.solr_tuples.append(('start', values))
            elif key == 'rows':
                self.rows = int(values)
                self.solr_tuples.append(('rows', self.rows))
            elif key == 'fl': # fl: field list
                self.solr_tuples.append(('fl', values))
            elif key == 'wt': # wt: response writer
                self.solr_tuples.remove(('wt', 'json'))
                self.solr_tuples.append(('wt', values))
            elif key in JSON_FACET_MAP[self.core]: # fq: filter query
                self.solr_tuples.append(('fq', f'{key}:"{values}"'))
                # field = JSON_FACET_MAP[self.core][key]['field']
                # if len(values) == 1:
                #     if ',' in values[0]:
                #         vlist = values[0].split(',')
                #         self.solr_tuples.append(('fq', f'{key}:[{vlist[0]} TO {vlist[1]}]'))
                #     else:
                #         if key in JSON_FACET_MAP[self.core]:
                #             self.solr_tuples.append(('fq', '{}:"{}"'.format(field, values[0])))
                # else:
                #     self.solr_tuples.append(('fq', ' OR '.join([f'{field}:"{x}"' for x in values])))
        self.solr_tuples.append(('q', self.solr_q))
        if len(self.facet_values):
            self.solr_tuples.append(('facet', 'true'))
            s = ''
            flist = []
            for i in self.facet_values:
                flist.append('{}:{}'.format(i, str(JSON_FACET_MAP[self.core][i]).replace("'", '',).replace(' ', '')))
            s = ','.join(flist)
            self.solr_tuples.append(('json.facet', '{'f'{s}''}'))
        query_string = urllib.parse.urlencode(self.solr_tuples)
        self.solr_url = f'{SOLR_PREFIX}{self.core}/select?{query_string}'
        return self.solr_url
    def request(self, req_lists=[]):
        self.generate_solr_url(req_lists)
        try:
            resp =urllib.request.urlopen(self.solr_url)
            resp_dict = resp.read().decode()
            self.solr_response = json.loads(resp_dict)
        except urllib.request.HTTPError as e:
            self.solr_error = str(e)
        return {
            'solr_response': self.solr_response,
            'solr_error': self.solr_error,
        }
    def get_response(self):
        '''get solr response and convert to gbif-like response
        '''
        if not self.solr_response:
            return
        resp = self.solr_response['response']
        facets = self.solr_response.get('facets', [])
        is_last = False
        if resp['start'] + int(self.rows) >= resp['numFound']:
            is_last = True
        for i in resp['docs']:
            i['taibif_occurrence_id'] = i['taibif_occ_id']
        return {
            'offset': resp['start'],
            'limit': self.rows,
            'count': resp['numFound'],
            'results': resp['docs'],
            'endOfRecords': is_last,
            'facets': facets, # TODO: redundant with menus
        }

