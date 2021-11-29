import pandas as pd
from data.models import Taxon

def is_contain_chinese(check_str):
    """
    判断字符串中是否包含中文
    :param check_str: {str} 需要检测的字符串
    :return: {bool} 包含返回True， 不包含返回False
    """
    for ch in check_str:
        if u'\u4e00' <= ch <= u'\u9fff':
            return True
    return False

# TBN taxon
df = pd.read_csv('../tbia-volumes/data/tbntaxonbio-expor-6028-20210830111927-5fa0e.csv', encoding='utf-8-sig')
df = df.fillna('')
for i in range(len(df)):
    print(i)
    row = df.iloc[i]
    # check alternative name
    names = row.alternativeName
    alt_name_c = []
    syn = []
    if names != '':
        for j in names.split(','):
            if is_contain_chinese(j):
                alt_name_c.append(j)
            else:
                syn.append(j)
    Taxon.objects.create(
        taxonUUID = row.taxonUUID,
        name_id = int(row.taiCoLNameCode) if str(row.taiCoLNameCode)[-2:]=='.0' else row.taiCoLNameCode,
        formatted_name = row.scientificName,
        synonyms = ','.join(syn),
        common_name_c = row.vernacularName,
        alternative_name_c = ','.join(alt_name_c),
        rank = row.taxonRank,
        domain = row.domain,
        domain_c = row.domainTW,
        superkingdom = row.superkingdom,
        superkingdom_c = row.superkingdomTW,
        kingdom = row.kingdom,
        kingdom_c = row.kingdomTW,
        subkingdom = row.subkingdom,
        subkingdom_c = row.subkingdomTW,
        superphylum = row.superphylum,
        superphylum_c = row.superphylumTW,
        phylum = row.phylum,
        phylum_c = row.phylumTW,
        subphylum = row.subphylum,
        subphylum_c = row.subphylumTW,
        superclass = row.superclass,
        superclass_c = row.superclassTW,
        Class = row['class'],
        Class_c = row.classTW,
        subclass = row.subclass,
        subclass_c = row.subclassTW,
        superorder = row.superorder,
        superorder_c = row.superorderTW,
        order = row.order,
        order_c = row.orderTW,
        suborder = row.suborder,
        suborder_c = row.suborderTW,
        superfamily = row.superfamily,
        superfamily_c = row.superfamilyTW,
        family = row.family,
        family_c = row.familyTW,
        subfamily = row.subfamily,
        subfamily_c = row.subfamilyTW,
        genus = row.genus,
        genus_c = row.genusTW,
        subgenus = row.subgenus,
        subgenus_c = row.subgenusTW,
        species = row.specificEpithet,
        subspecies = row.subspecies,
        variety = row.variety,
        form = row.form,
    )
    


