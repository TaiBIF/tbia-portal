from conf.settings import env
import urllib
import requests
import json

if env in ['dev']:
    SOLR_PREFIX = 'http://127.0.0.1:8983/solr/'
else:
    SOLR_PREFIX = 'http://solr:8983/solr/'

class SolrQuery(object):
    def __init__(self, core):
        self.solr_tuples = [
            ('q.op', 'OR'),
            ('wt', 'json'),
        ]
        self.core = core
        # self.facet_values = facet_values
        self.solr_error = ''
        self.solr_response = {}
        self.solr_url = ''
        self.solr_q = '*:*'
    def generate_solr_url(self, req_lists=[]):
        for key, values in req_lists:
            if key == 'q' and values:
                self.solr_tuples.append(('q', values))
            elif key == 'offset':
                self.solr_tuples.append(('start', values))
            elif key == 'sort':
                self.solr_tuples.append(('sort', values))
            elif key == 'rows':
                self.rows = int(values)
                self.solr_tuples.append(('rows', self.rows))
            elif key == 'fl': # fl: field list
                self.solr_tuples.append(('fl', values))
            # elif key == 'facet.contains.ignoreCase': 
            #     self.solr_tuples.append(('facet.contains.ignoreCase', values))
            # elif key == 'facet.contains': 
            #     self.solr_tuples.append(('facet.contains', values))
            elif key == 'wt': # wt: response writer
                self.solr_tuples.remove(('wt', 'json'))
                self.solr_tuples.append(('wt', values))
            # elif key in JSON_FACET_MAP[self.core]: # fq: filter query
            #     self.solr_tuples.append(('fq', f'{key}:"{values}"'))
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
            elif key == 'fq':
                self.solr_tuples.append(('fq', values))
            else:
                self.solr_tuples.append((key, values))
        # self.solr_tuples.append(self.solr_q)
        # if len(self.facet_values):
        #     self.solr_tuples.append(('facet', 'true'))
        #     s = ''
        #     flist = []
        #     for i in self.facet_values:
        #         tmp_dict = JSON_FACET_MAP[self.core][i]
        #         # keyword = self.solr_q.replace('"','')
        #         # tmp_dict.update({'domain': { 'query': f'{i}:*{keyword}*' }})
        #         # print(tmp_dict)
        #         flist.append('{}:{}'.format(i, str(tmp_dict).replace("'", '"',).replace(' ', '')))
        #     s = ','.join(flist)
        #     self.solr_tuples.append(('json.facet', '{'f'{s}''}'))
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


occ_facets = {  'facet': {
        'scientificName': {
            'type': 'terms',
            'field': 'scientificName',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                'taxonID':{
                    'type': 'terms',
                    'field': 'taxonID',
                    'limit': 30,
                    'numBuckets': True,
                },
            }
        },
        'common_name_c': {
            'type': 'terms',
            'field': 'common_name_c',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                'taxonID':{
                    'type': 'terms',
                    'field': 'taxonID',
                    'limit': 30,
                    'numBuckets': True,
                },
            }
        },
        'alternative_name_c': {
            'type': 'terms',
            'field': 'alternative_name_c',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'numBuckets': True,
                    },
                }
        },
        'synonyms': {
            'type': 'terms',
            'field': 'synonyms',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'numBuckets': True,
                    },
                }
        },
        'misapplied': {
            'type': 'terms',
            'field': 'misapplied',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'numBuckets': True,
                    },
                }
        },
        'sourceScientificName': {
            'type': 'terms',
            'field': 'sourceScientificName',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'numBuckets': True,
                    },
                }
        },
        'sourceVernacularName': {
            'type': 'terms',
            'field': 'sourceVernacularName',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'numBuckets': True,
                    },
                }
        },
        'taxonRank': {
            'type': 'terms',
            'field': 'taxonRank',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'numBuckets': True,
                    }
                }
        },
        'kingdom': {
            'type': 'terms',
            'field': 'kingdom',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'numBuckets': True,
                    },
                }
        },
        'phylum': {
            'type': 'terms',
            'field': 'phylum',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'numBuckets': True,
                    },
                }
        },
        'class': {
            'type': 'terms',
            'field': 'class',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'numBuckets': True,
                    },
                }
        },
        'order': {
            'type': 'terms',
            'field': 'order',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'numBuckets': True,
                    },
                }
        },
        'family': {
            'type': 'terms',
            'field': 'family',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'numBuckets': True,
                    },
                }
        },
        'genus': {
            'type': 'terms',
            'field': 'genus',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'numBuckets': True,
                    },
                }
        },
        'species': {
            'type': 'terms',
            'field': 'species',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'numBuckets': True,
                    },
                }
        },
        'kingdom_c': {
            'type': 'terms',
            'field': 'kingdom_c',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'numBuckets': True,
                    },
                }
        },
        'phylum_c': {
            'type': 'terms',
            'field': 'phylum_c',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'numBuckets': True,
                    },
                }
        },
        'class_c': {
            'type': 'terms',
            'field': 'class_c',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'numBuckets': True,
                    },
                }
        },
        'order_c': {
            'type': 'terms',
            'field': 'order_c',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'numBuckets': True,
                    },
                }
        },
        'family_c': {
            'type': 'terms',
            'field': 'family_c',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'numBuckets': True,
                    },
                }
        },
        'genus_c': {
            'type': 'terms',
            'field': 'genus_c',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'numBuckets': True,
                    },
                }
        },
        'rightsHolder': {
            'type': 'terms',
            'field': 'rightsHolder',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'numBuckets': True,
                    }
                }
        },
        'sensitiveCategory': {
            'type': 'terms',
            'field': 'sensitiveCategory',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'numBuckets': True,
                    }
                }
        },
        'locality': {
            'type': 'terms',
            'field': 'locality',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'numBuckets': True,
                    }
                }
        },
        'recordedBy': {
            'type': 'terms',
            'field': 'recordedBy',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'numBuckets': True,
                    }
                }
        },
        'basisOfRecord': {
            'type': 'terms',
            'field': 'basisOfRecord',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'numBuckets': True,
                    }
                }
        },
        'datasetName': {
            'type': 'terms',
            'field': 'datasetName',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'numBuckets': True,
                    }
                }
        },
        'license': {
            'type': 'terms',
            'field': 'license',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'numBuckets': True,
                    }
                }
        },
        'eventDate': {
            'type': 'terms',
            'field': 'eventDate',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                'taxonID':{
                    'type': 'terms',
                    'field': 'taxonID',
                    'limit': 30,
                    'numBuckets': True,
                },
            }        
        },
    },
}


col_facets = { 'facet': {
        'scientificName': {
            'type': 'terms',
            'field': 'scientificName',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                'taxonID':{
                    'type': 'terms',
                    'field': 'taxonID',
                    'limit': 30,
                    'numBuckets': True,
                },
            }        
        },
        'common_name_c': {
            'type': 'terms',
            'field': 'common_name_c',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                'taxonID':{
                    'type': 'terms',
                    'field': 'taxonID',
                    'limit': 30,
                    'numBuckets': True,
                },
            }
        },
        'alternative_name_c': {
            'type': 'terms',
            'field': 'alternative_name_c',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'numBuckets': True,
                    },
                }
        },
        'synonyms': {
            'type': 'terms',
            'field': 'synonyms',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'numBuckets': True,
                    },
                }
        },
        'misapplied': {
            'type': 'terms',
            'field': 'misapplied',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'numBuckets': True,
                    },
                }
        },
        'sourceScientificName': {
            'type': 'terms',
            'field': 'sourceScientificName',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'numBuckets': True,
                    },
                }
        },
        'sourceVernacularName': {
            'type': 'terms',
            'field': 'sourceVernacularName',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'numBuckets': True,
                    },
                }
        },
        'rightsHolder': {
            'type': 'terms',
            'field': 'rightsHolder',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'numBuckets': True,
                    },
                }
        },
        'sensitiveCategory': {
            'type': 'terms',
            'field': 'sensitiveCategory',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'allBuckets': True,
                        'numBuckets': True,
                    },
                }
        },
        'taxonRank': {
            'type': 'terms',
            'field': 'taxonRank',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'allBuckets': True,
                        'numBuckets': True,
                    },
                }
        },
        'locality': {
            'type': 'terms',
            'field': 'locality',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'allBuckets': True,
                        'numBuckets': True,
                    },
                }
        },
        'recordedBy': {
            'type': 'terms',
            'field': 'recordedBy',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'allBuckets': True,
                        'numBuckets': True,
                    },
                }
        },
        'typeStatus': {
            'type': 'terms',
            'field': 'typeStatus',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'allBuckets': True,
                        'numBuckets': True,
                    },
                }
        },
        'preservation': {
            'type': 'terms',
            'field': 'preservation',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'allBuckets': True,
                        'numBuckets': True,
                    },
                }
        },
        'datasetName': {
            'type': 'terms',
            'field': 'datasetName',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'allBuckets': True,
                        'numBuckets': True,
                    },
                }
        },
        'license': {
            'type': 'terms',
            'field': 'license',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'allBuckets': True,
                        'numBuckets': True,
                    },
                }
        },

        'kingdom': {
            'type': 'terms',
            'field': 'kingdom',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'allBuckets': True,
                        'numBuckets': True,
                    },
                }
        },
        'phylum': {
            'type': 'terms',
            'field': 'phylum',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'allBuckets': True,
                        'numBuckets': True,
                    },
                }
        },
        'class': {
            'type': 'terms',
            'field': 'class',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'allBuckets': True,
                        'numBuckets': True,
                    },
                }
        },
        'order': {
            'type': 'terms',
            'field': 'order',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'allBuckets': True,
                        'numBuckets': True,
                    },
                }
        },
        'family': {
            'type': 'terms',
            'field': 'family',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'allBuckets': True,
                        'numBuckets': True,
                    },
                }
        },
        'genus': {
            'type': 'terms',
            'field': 'genus',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'allBuckets': True,
                        'numBuckets': True,
                    },
                }
        },
        'species': {
            'type': 'terms',
            'field': 'species',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'allBuckets': True,
                        'numBuckets': True,
                    },
                }
        },
        'kingdom_c': {
            'type': 'terms',
            'field': 'kingdom_c',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'allBuckets': True,
                        'numBuckets': True,
                    },
                }
        },
        'phylum_c': {
            'type': 'terms',
            'field': 'phylum_c',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'allBuckets': True,
                        'numBuckets': True,
                    },
                }
        },
        'class_c': {
            'type': 'terms',
            'field': 'class_c',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'allBuckets': True,
                        'numBuckets': True,
                    },
                }
        },
        'order_c': {
            'type': 'terms',
            'field': 'order_c',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'allBuckets': True,
                        'numBuckets': True,
                    },
                }
        },
        'family_c': {
            'type': 'terms',
            'field': 'family_c',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'allBuckets': True,
                        'numBuckets': True,
                    },
                }
        },
        'genus_c': {
            'type': 'terms',
            'field': 'genus_c',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'allBuckets': True,
                        'numBuckets': True,
                    },
                }
        },
        'eventDate': {
            'type': 'terms',
            'field': 'eventDate',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                'taxonID':{
                    'type': 'terms',
                    'field': 'taxonID',
                    'limit': 30,
                    'numBuckets': True,
                },
            }        
        },
    }}


