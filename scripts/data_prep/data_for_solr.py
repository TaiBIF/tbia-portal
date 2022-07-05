import pandas as pd
import glob
import numpy as np
from data.utils import convert_date

taxon_cols = ['id',
'taxonUUID',
'name_id',
'formatted_name',
'synonyms',
'misapplied',
'rank',
'common_name_c',
'alternative_name_c',
'originalModified',
'originalCreated',
'created',
'modified',
'domain',
'domain_c',
'superkingdom',
'superkingdom_c',
'kingdom',
'kingdom_c',
'subkingdom',
'subkingdom_c',
'infrakingdom',
'infrakingdom_c',
'superdivision',
'superdivision_c',
'division',
'division_c',
'subdivision',
'subdivision_c',
'infradivision',
'infradivision_c',
'parvdivision',
'parvdivision_c',
'superphylum',
'superphylum_c',
'phylum',
'phylum_c',
'subphylum',
'subphylum_c',
'infraphylum',
'infraphylum_c',
'microphylum',
'microphylum_c',
'parvphylum',
'parvphylum_c',
'superclass',
'superclass_c',
'class',
'class_c',
'subclass',
'subclass_c',
'infraclass',
'infraclass_c',
'superorder',
'superorder_c',
'order',
'order_c',
'suborder',
'suborder_c',
'infraorder',
'infraorder_c',
'superfamily',
'superfamily_c',
'family',
'family_c',
'subfamily',
'subfamily_c',
'tribe',
'tribe_c',
'subtribe',
'subtribe_c',
'genus',
'genus_c',
'subgenus',
'subgenus_c',
'section',
'section_c',
'subsection',
'subsection_c',
'species',
'species_c',
'subspecies',
'nothosubspecies',
'variety',
'subvariety',
'nothovariety',
'form',
'subform',
'specialForm',
'race',
'stirp',
'morph',
'aberration',
'hybridFormula']

merged_cols = [
'recordType',
'tbiaUUID',
'taxonUUID',
'originalModified',
'originalCreated',
'modified',
'created',
'rightsHolder',
'occurrenceID',
'originalScientificName',
'originalVernacularName',
'sensitiveCategory',
'taxonRank',
'eventDate',
'standardDate',
'verbatimLongitude',
'verbatimLatitude',
'verbatimCoordinateSystem',
'verbatimSRS',
'standardLongitude',
'standardLatitude',
'coordinateUncertaintyInMeters',
'dataGeneralizations',
'coordinatePrecision',
'locality',
'organismQuantity',
'organismQuantityType',
'recordedBy',
'scientificNameID',
'basisOfRecord',
'datasetName',
'resourceContacts',
'references',
'license',
'selfProduced',
'collectionID',
'associatedMedia',
'recordNumber',
'preservation',
'synonyms',
'misapplied',
'common_name_c',
'alternative_name_c',
'domain',
'domain_c',
'superkingdom',
'superkingdom_c',
'kingdom',
'kingdom_c',
'subkingdom',
'subkingdom_c',
'infrakingdom',
'infrakingdom_c',
'superdivision',
'superdivision_c',
'division',
'division_c',
'subdivision',
'subdivision_c',
'infradivision',
'infradivision_c',
'parvdivision',
'parvdivision_c',
'superphylum',
'superphylum_c',
'phylum',
'phylum_c',
'subphylum',
'subphylum_c',
'infraphylum',
'infraphylum_c',
'microphylum',
'microphylum_c',
'parvphylum',
'parvphylum_c',
'superclass',
'superclass_c',
'class',
'class_c',
'subclass',
'subclass_c',
'infraclass',
'infraclass_c',
'superorder',
'superorder_c',
'order',
'order_c',
'suborder',
'suborder_c',
'infraorder',
'infraorder_c',
'superfamily',
'superfamily_c',
'family',
'family_c',
'subfamily',
'subfamily_c',
'tribe',
'tribe_c',
'subtribe',
'subtribe_c',
'genus',
'genus_c',
'subgenus',
'subgenus_c',
'section',
'section_c',
'subsection',
'subsection_c',
'species',
'species_c',
'subspecies',
'nothosubspecies',
'variety',
'subvariety',
'nothovariety',
'form',
'subform',
'specialForm',
'race',
'stirp',
'morph',
'aberration',
'hybridFormula'
]

# df_occ = pd.read_csv('../tbia-volumes/solr/csvs/occurrence.csv') # 34
# df_occ['recordType'] = 'occ'
# df_col = pd.read_csv('../tbia-volumes/solr/csvs/collection.csv') # 38
# df_col['recordType'] = 'col'

# taxon = pd.read_csv('../tbia-volumes/solr/csvs/taxon.csv', names=taxon_cols)


# taicol = pd.read_csv('/Users/taibif/Documents/04-TaiCoL/TaiwanSpecies20211019_UTF8.csv')
# taicol = taicol[taicol['is_accepted_name']==True]
# syn = pd.read_csv('/Users/taibif/Documents/04-TaiCoL/namecorrespond20211019.csv')
# taxon = pd.merge(taicol, syn, on="accepted_name_code", how="left")


# ['kingdom', 'kingdom_c', 'phylum', 'phylum_c', 'class', 'class_c',
#        'order', 'order_c', 'family', 'family_c', 'genus',
#        'genus_c', 'species', 'name', 'common_name_c',

# df = pd.concat([df_col,df_occ], axis=0, ignore_index=True)

# df_t = pd.merge(df, taxon, on="taxonUUID", how="left")

# # 同物異名

#-------- from scratch ---------#
import bson

from numpy import nan
import requests
from datetime import datetime, tzinfo,timedelta
from dateutil import parser
import time
import os


rank = pd.read_csv('../tbia-volumes/bucket/taxa_c.csv', names=['rank_c','rank'])
syn = pd.read_csv('../tbia-volumes/bucket/namecorrespond20211019.csv')
taicol = pd.read_csv('../tbia-volumes/bucket/TaiwanSpecies20211019_UTF8.csv')
taicol = taicol[taicol['is_accepted_name']==True]

tbn_path = '../tbia-volumes/bucket'
# tbn_path = '/Users/taibif/Documents/GitHub/tbia-volumes/tbn_data'
extension = 'csv'
os.chdir(tbn_path)
files = glob.glob('e1b7adf8-9315-4134-aced-729a09da40f6_*')
# idx = files.index("f58922e2-93ed-4703-ba22-12a0674d1b54.csv")
# files = files[idx:]
len_f = len(files)


# for count in range(0,len_f):
#     df = pd.read_csv(files[count])
#     unique_sci = df.scientificName.unique()
#     unique_sci = [x for x in unique_sci if str(x) != 'nan']
#     # NomenMatch
#     sci_match = []
#     for s in unique_sci:
#         taxon_id, sensitiveState, name_code, precision, data_generalize,rank_e, name = None, None, None, None, None, None, None
#         if not s.split(' ')[0] in ['Kingdom', 'Phylum', 'Class', 'Order', 'Family', 'Genus', 'Species']:
#             if len(df[df['scientificName']==s]):
#                 request_url = f"https://www.tbn.org.tw/api/v2/species?uuid={df[df['scientificName']==s].taxonUUID.values[0]}"
#                 response = requests.get(request_url)
#                 t = response.json()['data']
#                 if t:
#                     sensitiveState = t[0]['sensitiveState']
#                     if sensitiveState == '輕度':
#                         precision = 0.01
#                         data_generalize = True
#                     elif sensitiveState == '重度':
#                         precision = 0.1
#                         data_generalize = True
#                     taxon_rank = t[0]['taxonRank']
#                     rank_e = rank[rank['rank_c']==taxon_rank]['rank'].values[0] if taxon_rank in rank.rank_c.to_list() else None
#             request_url = f"http://match.taibif.tw/api.php?names={s}&best=yes&format=json"
#             response = requests.get(request_url)
#             res = response.json()['results'][0][0]
#             if res['best']:
#                 if res['best']:
#                     taxon_id = res['best'].get('taicol',None)
#                     if taxon_id:
#                         # directly read taicol df
#                         tc_results = taicol[taicol['name_code']==str(taxon_id)][['accepted_name_code','name']]
#                         if len(tc_results):
#                             name = tc_results.name.values[0]
#                             name_code = tc_results.accepted_name_code.values[0]
#                         # request_url = f"https://api.taicol.tw/v1/?namecode={taxon_id}"
#                         # response = requests.get(request_url, verify=False)
#                         # t = response.json()[1]
#                         # name = t['name']
#                         # name_code = t['accepted_name_code']
#             tmp = {'scientificName': s, 'taxon_id':taxon_id, 'sensitiveState': sensitiveState, 'name_code': name_code,
#             'precision': precision, 'data_generalize': data_generalize, 'rank': rank_e, 'matchedName':name }
#             sci_match.append(tmp)
#     sci_match = pd.DataFrame(sci_match)
#     if len(sci_match):
#         sci_match['rank'] = sci_match['rank'].replace('Class','class')
#     row_list = []
#     for k in range(len(df)):
#         print(files[count],k)
#         # print(k)
#         row = df.iloc[k]
#         common_name_c, kingdom, phylum, Class, order, family, genus, species, kingdom_c, phylum_c, class_c, order_c, family_c, genus_c =  None, None, None, None, None, None, None, None, None, None, None, None, None, None
#         synonyms, alternative_name_c = None, None
#         sensitiveState, rank_str, name_code, data_generalize, precision, name = None, None, None, None, None, None
#         sci_match_row = sci_match.loc[sci_match['scientificName']==row.scientificName] if len(sci_match) else []
#         if len(sci_match_row):
#             sensitiveState = sci_match_row.sensitiveState.values[0]
#             rank_str = sci_match_row['rank'].values[0]
#             name_code = sci_match_row.name_code.values[0]
#             data_generalize = sci_match_row.data_generalize.values[0]
#             precision = sci_match_row.precision.values[0]
#             name = sci_match_row.matchedName.values[0]
#             tc_info = taicol.loc[taicol['name_code']==sci_match_row.name_code.values[0]]
#             if len(tc_info):
#                 common_name_c = str(tc_info.common_name_c.values[0]).replace(';',',')
#                 alternative_name_c = str(common_name_c.split(',')[1:])[1:-1].replace('\'','') if common_name_c else None
#                 common_name_c = common_name_c.split(',')[0] if common_name_c else common_name_c
#                 kingdom = tc_info.kingdom.values[0]
#                 phylum = tc_info.phylum.values[0]
#                 Class = tc_info['class'].values[0]
#                 order = tc_info.order.values[0]
#                 family = tc_info.family.values[0]
#                 genus = tc_info.genus.values[0]
#                 species = tc_info.species.values[0]
#                 kingdom_c = tc_info.kingdom_c.values[0]
#                 phylum_c = tc_info.phylum_c.values[0]
#                 class_c = tc_info.class_c.values[0]
#                 order_c = tc_info.order_c.values[0]
#                 family_c = tc_info.family_c.values[0]
#                 genus_c = tc_info.genus_c.values[0]
#             tc_syn = syn.loc[syn['accepted_name_code']==sci_match_row.name_code.values[0]]
#             if tc_syn.synonyms.values:
#                 synonyms = tc_syn.synonyms.values[0].replace('||',',')
#         tmp = {
#         'recordType' : 'occ' if 'Specimen' not in str(row.basisOfRecord) else 'col',
#         'tbiaUUID' : bson.objectid.ObjectId(),
#         'sourceModified' : convert_date(row.modified),
#         'sourceCreated' : convert_date(row.created),
#         'modified' : datetime.now(),
#         'created' : datetime.now(),
#         'rightsHolder' : 'TBN',
#         'occurrenceID' : row.occurrenceUUID,
#         'originalScientificName' : row.proposedTaxon, # ignore at this momemnt
#         'sourceScientificName' : row.scientificName,
#         'sourceVernacularName' : row.vernacularName,
#         'sensitiveCategory' : sensitiveState,
#         'taxonRank' : rank_str,
#         'eventDate' : row.eventDate,
#         'standardDate' : convert_date(row.eventDate),
#         'verbatimLongitude' : row.decimalLongitude,
#         'verbatimLatitude' : row.decimalLatitude,
#         'verbatimCoordinateSystem' : 'decimalDegrees' if row.decimalLongitude and row.decimalLatitude else None,
#         'verbatimSRS' : 'WGS84' if row.decimalLongitude and row.decimalLatitude else None,
#         'standardLongitude' : float(row.decimalLongitude) if row.decimalLongitude not in ['', None, '0', 'WGS84'] else None,
#         'standardLatitude' : float(row.decimalLatitude) if row.decimalLatitude not in ['', None] else None,
#         'coordinateUncertaintyInMeters' : row.coordinateUncertaintyInMeters,
#         'dataGeneralizations' : data_generalize,
#         'coordinatePrecision' : precision,
#         'locality' : row.eventPlaceAdminarea,
#         'organismQuantity' : row.organismQuantityType if row.individualCount == '' else row.individualCount,
#         'organismQuantityType' : row.organismQuantityType,
#         'recordedBy' : None, # TBN didn't have this column
#         'scientificNameID' : name_code,
#         'scientificName' : name,
#         'basisOfRecord' : row.basisOfRecord,
#         'datasetName' : row.datasetName,
#         'resourceContacts' : row.datasetAuthor,
#         'references' : f"https://www.tbn.org.tw/occurrence/{row.tbnID}",
#         'license' : row.license,
#         'selfProduced' : None,
#         'collectionID' : None,
#         'associatedMedia' : None,
#         'recordNumber' : None,
#         'preservation' : None,
#         'synonyms' : synonyms,
#         'misapplied' : None,
#         'common_name_c' : common_name_c,
#         'alternative_name_c' : alternative_name_c,
#         'domain' : None,
#         'superkingdom' : None,
#         'kingdom' : kingdom,
#         'subkingdom' : None,
#         'infrakingdom' : None,
#         'superdivision' : None,
#         'division' : None,
#         'subdivision' : None,
#         'infradivision' : None,
#         'parvdivision' : None,
#         'superphylum' : None,
#         'phylum' : phylum,
#         'subphylum' : None,
#         'infraphylum' : None,
#         'microphylum' : None,
#         'parvphylum' : None,
#         'superclass' : None,
#         'class' : Class,
#         'subclass' : None,
#         'infraclass' : None,
#         'superorder' : None,
#         'order' : order,
#         'suborder' : None,
#         'infraorder' : None,
#         'superfamily' : None,
#         'family' : family,
#         'subfamily' : None,
#         'tribe' : None,
#         'subtribe' : None,
#         'genus' : genus,
#         'subgenus' : None,
#         'section' : None,
#         'subsection' : None,
#         'species' : species,
#         'domain_c' : None,
#         'superkingdom_c' : None,
#         'kingdom_c' : kingdom_c,
#         'subkingdom_c' : None,
#         'infrakingdom_c' : None,
#         'superdivision_c' : None,
#         'division_c' : None,
#         'subdivision_c' : None,
#         'infradivision_c' : None,
#         'parvdivision_c' : None,
#         'superphylum_c' : None,
#         'phylum_c' : phylum_c,
#         'subphylum_c' : None,
#         'infraphylum_c' : None,
#         'microphylum_c' : None,
#         'parvphylum_c' : None,
#         'superclass_c' : None,
#         'class_c' : class_c,
#         'subclass_c' : None,
#         'infraclass_c' : None,
#         'superorder_c' : None,
#         'order_c' : order_c,
#         'suborder_c' : None,
#         'infraorder_c' : None,
#         'superfamily_c' : None,
#         'family_c' : family_c,
#         'subfamily_c' : None,
#         'tribe_c' : None,
#         'subtribe_c' : None,
#         'genus_c' : genus_c,
#         'subgenus_c' : None,
#         'section_c' : None,
#         'subsection_c' : None,
#         # 'species_c' : tc_info.species_c.values[0],
#         'subspecies' : None,
#         'nothosubspecies' : None,
#         'variety' : None,
#         'subvariety' : None,
#         'nothovariety' : None,
#         'form' : None,
#         'subform' : None,
#         'specialForm' : None,
#         'race' : None,
#         'stirp' : None,
#         'morph' : None,
#         'aberration' : None,
#         'hybridFormula' : None
#         }
#         row_list.append(tmp)
#     df_cleaned = pd.DataFrame(row_list)
#     df_occ = df_cleaned[df_cleaned['recordType']=='occ']
#     df_col = df_cleaned[df_cleaned['recordType']=='col']
#     if len(df_occ):
#         df_occ.to_csv(f'../solr/csvs/occ/{files[count]}', index=False)
#     if len(df_col):
#         df_col.to_csv(f'../solr/csvs/col/{files[count]}', index=False)


# edit 2022-01-06

# for count in range(0,len_f):
df = pd.read_csv('97c21d3f-774b-45e7-9149-4c0697fadbde.csv', index_col=0)
unique_sci = df.scientificName.unique()
unique_sci = [x for x in unique_sci if str(x) != 'nan']
# NomenMatch
sci_match = []
for s in unique_sci:
    taxon_id, name_code, rank_e, name = None, None, None, None
    if not s.split(' ')[0] in ['Kingdom', 'Phylum', 'Class', 'Order', 'Family', 'Genus', 'Species']:
        if len(df[df['scientificName']==s]):
            request_url = f"https://www.tbn.org.tw/api/v2/species?uuid={df[df['scientificName']==s].taxonUUID.values[0]}"
            response = requests.get(request_url)
            t = response.json()['data']
            if t:
                taxon_rank = t[0]['taxonRank']
                rank_e = rank[rank['rank_c']==taxon_rank]['rank'].values[0] if taxon_rank in rank.rank_c.to_list() else None
        request_url = f"http://match.taibif.tw/api.php?names={s}&best=yes&format=json"
        response = requests.get(request_url)
        res = response.json()['results'][0][0]
        if res['best']:
            if res['best']:
                taxon_id = res['best'].get('taicol',None)
                if taxon_id:
                    # directly read taicol df
                    tc_results = taicol[taicol['name_code']==str(taxon_id)][['accepted_name_code','name']]
                    if len(tc_results):
                        name = tc_results.name.values[0]
                        name_code = tc_results.accepted_name_code.values[0]
                    # request_url = f"https://api.taicol.tw/v1/?namecode={taxon_id}"
                    # response = requests.get(request_url, verify=False)
                    # t = response.json()[1]
                    # name = t['name']
                    # name_code = t['accepted_name_code']
        tmp = {'scientificName': s, 'taxon_id':taxon_id, 'name_code': name_code,
        'rank': rank_e, 'matchedName':name }
        sci_match.append(tmp)
sci_match = pd.DataFrame(sci_match)
if len(sci_match):
    sci_match['rank'] = sci_match['rank'].replace('Class','class')
row_list = []
for k in range(len(df)):
    print(k)
    row = df.iloc[k]
    precision, sensitiveState, data_generalize = None, None, None
    sensitiveState = row.dataSensitiveIndicator
    if sensitiveState == '輕度':
        precision = 0.01
        data_generalize = True
    elif sensitiveState == '重度':
        precision = 0.1
        data_generalize = True
    elif sensitiveState == '縣市':
        data_generalize = True
    common_name_c, kingdom, phylum, Class, order, family, genus, species, kingdom_c, phylum_c, class_c, order_c, family_c, genus_c =  None, None, None, None, None, None, None, None, None, None, None, None, None, None
    synonyms, alternative_name_c = None, None
    rank_str, name_code, name = None, None, None
    sci_match_row = sci_match.loc[sci_match['scientificName']==row.scientificName] if len(sci_match) else []
    if len(sci_match_row):
        rank_str = sci_match_row['rank'].values[0]
        name_code = sci_match_row.name_code.values[0]
        name = sci_match_row.matchedName.values[0]
        tc_info = taicol.loc[taicol['name_code']==sci_match_row.name_code.values[0]]
        if len(tc_info):
            common_name_c = str(tc_info.common_name_c.values[0]).replace(';',',')
            alternative_name_c = str(common_name_c.split(',')[1:])[1:-1].replace('\'','') if common_name_c else None
            common_name_c = common_name_c.split(',')[0] if common_name_c else common_name_c
            kingdom = tc_info.kingdom.values[0]
            phylum = tc_info.phylum.values[0]
            Class = tc_info['class'].values[0]
            order = tc_info.order.values[0]
            family = tc_info.family.values[0]
            genus = tc_info.genus.values[0]
            species = tc_info.species.values[0]
            kingdom_c = tc_info.kingdom_c.values[0]
            phylum_c = tc_info.phylum_c.values[0]
            class_c = tc_info.class_c.values[0]
            order_c = tc_info.order_c.values[0]
            family_c = tc_info.family_c.values[0]
            genus_c = tc_info.genus_c.values[0]
        tc_syn = syn.loc[syn['accepted_name_code']==sci_match_row.name_code.values[0]]
        if tc_syn.synonyms.values:
            synonyms = tc_syn.synonyms.values[0].replace('||',',')
    try:
        name_code = str(int(name_code))
    except:
        pass
    tmp = {
    'recordType' : 'occ' if 'Specimen' not in str(row.basisOfRecord) else 'col',
    'id' : bson.objectid.ObjectId(),
    'sourceModified' : convert_date(row.modified),
    'sourceCreated' : convert_date(row.created),
    'modified' : datetime.now(),
    'created' : datetime.now(),
    'rightsHolder' : 'TBN',
    'occurrenceID' : row.occurrenceUUID,
    'originalScientificName' : row.proposedTaxon, # ignore at this momemnt
    'sourceScientificName' : row.scientificName,
    'sourceVernacularName' : row.vernacularName,
    'sensitiveCategory' : sensitiveState,
    'taxonRank' : rank_str,
    'eventDate' : row.eventDate,
    'standardDate' : convert_date(row.eventDate),
    'verbatimLongitude' : row.decimalLongitude,
    'verbatimLatitude' : row.decimalLatitude,
    'verbatimCoordinateSystem' : 'decimalDegrees' if row.decimalLongitude and row.decimalLatitude else None,
    'verbatimSRS' : 'WGS84' if row.decimalLongitude and row.decimalLatitude else None,
    'standardLongitude' : float(row.decimalLongitude) if row.decimalLongitude not in ['', None, '0', 'WGS84'] else None,
    'standardLatitude' : float(row.decimalLatitude) if row.decimalLatitude not in ['', None] else None,
    'coordinateUncertaintyInMeters' : row.coordinateUncertaintyInMeters,
    'dataGeneralizations' : data_generalize,
    'coordinatePrecision' : precision,
    'locality' : row.eventPlaceAdminarea,
    'organismQuantity' : row.organismQuantityType if row.individualCount == '' else row.individualCount,
    'organismQuantityType' : row.organismQuantityType,
    'recordedBy' : None, # TBN didn't have this column
    'scientificNameID' : name_code,
    'scientificName' : name,
    'basisOfRecord' : row.basisOfRecord,
    'datasetName' : row.datasetName,
    'resourceContacts' : row.datasetAuthor,
    'references' : f"https://www.tbn.org.tw/occurrence/{str(int(row.tbnID))}",
    'license' : row.license,
    'selfProduced' : None,
    'collectionID' : None,
    'associatedMedia' : None,
    'recordNumber' : None,
    'preservation' : None,
    'synonyms' : synonyms,
    'misapplied' : None,
    'common_name_c' : common_name_c,
    'alternative_name_c' : alternative_name_c,
    'domain' : None,
    'superkingdom' : None,
    'kingdom' : kingdom,
    'subkingdom' : None,
    'infrakingdom' : None,
    'superdivision' : None,
    'division' : None,
    'subdivision' : None,
    'infradivision' : None,
    'parvdivision' : None,
    'superphylum' : None,
    'phylum' : phylum,
    'subphylum' : None,
    'infraphylum' : None,
    'microphylum' : None,
    'parvphylum' : None,
    'superclass' : None,
    'class' : Class,
    'subclass' : None,
    'infraclass' : None,
    'superorder' : None,
    'order' : order,
    'suborder' : None,
    'infraorder' : None,
    'superfamily' : None,
    'family' : family,
    'subfamily' : None,
    'tribe' : None,
    'subtribe' : None,
    'genus' : genus,
    'subgenus' : None,
    'section' : None,
    'subsection' : None,
    'species' : species,
    'domain_c' : None,
    'superkingdom_c' : None,
    'kingdom_c' : kingdom_c,
    'subkingdom_c' : None,
    'infrakingdom_c' : None,
    'superdivision_c' : None,
    'division_c' : None,
    'subdivision_c' : None,
    'infradivision_c' : None,
    'parvdivision_c' : None,
    'superphylum_c' : None,
    'phylum_c' : phylum_c,
    'subphylum_c' : None,
    'infraphylum_c' : None,
    'microphylum_c' : None,
    'parvphylum_c' : None,
    'superclass_c' : None,
    'class_c' : class_c,
    'subclass_c' : None,
    'infraclass_c' : None,
    'superorder_c' : None,
    'order_c' : order_c,
    'suborder_c' : None,
    'infraorder_c' : None,
    'superfamily_c' : None,
    'family_c' : family_c,
    'subfamily_c' : None,
    'tribe_c' : None,
    'subtribe_c' : None,
    'genus_c' : genus_c,
    'subgenus_c' : None,
    'section_c' : None,
    'subsection_c' : None,
    # 'species_c' : tc_info.species_c.values[0],
    'subspecies' : None,
    'nothosubspecies' : None,
    'variety' : None,
    'subvariety' : None,
    'nothovariety' : None,
    'form' : None,
    'subform' : None,
    'specialForm' : None,
    'race' : None,
    'stirp' : None,
    'morph' : None,
    'aberration' : None,
    'hybridFormula' : None
    }
    row_list.append(tmp)
df_cleaned = pd.DataFrame(row_list)

df_cleaned['location_rpt'] = None
# df_cleaned['location_rpt'] = "POINT(" + df_cleaned["standardLongitude"].astype(str) + ' ' + df_cleaned["standardLatitude"].astype(str) + ")"

df_cleaned.loc[(df_cleaned["standardLongitude"].notnull())&(df_cleaned["standardLatitude"].notnull()),'location_rpt'] = "POINT(" + df_cleaned[(df_cleaned["standardLongitude"].notnull())&(df_cleaned["standardLatitude"].notnull())]["standardLongitude"].astype(str) + ' ' + df_cleaned[(df_cleaned["standardLongitude"].notnull())&(df_cleaned["standardLatitude"].notnull())]["standardLatitude"].astype(str) + ")"

# df_cleaned[df_cleaned[['standardLatitude','standardLongitude']].notnull()]['location_rpt'] = "POINT(" + df_cleaned[df_cleaned[['standardLatitude','standardLongitude']].notnull()]["standardLongitude"].astype(str) + ' ' + df_cleaned[df_cleaned[['standardLatitude','standardLongitude']].notnull()]["standardLatitude"].astype(str) + ")"
df_cleaned = df_cleaned.replace({np.nan: ''})

df_occ = df_cleaned[df_cleaned['recordType']=='occ']
df_col = df_cleaned[df_cleaned['recordType']=='col']
if len(df_occ):
    df_occ.to_csv(f'../solr/csvs/occ/e1b7adf8-9315-4134-aced-729a09da40f6.csv', index=False)
if len(df_col):
    df_col.to_csv(f'../solr/csvs/col/97c21d3f-774b-45e7-9149-4c0697fadbde.csv', index=False)


#  nohup sh -c 'poetry shell; python -u ./scripts/data_prep/data_for_solr.py' > for_solr.out 2>&1
