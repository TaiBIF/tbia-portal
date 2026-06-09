import json
import math
from datetime import datetime

import pandas as pd
import requests
from numpy import nan

from django.core.management.base import BaseCommand

from conf.settings import SOLR_PREFIX
from data.utils import rights_holder_map
from manager.models import TaxonStat


# 只取 year 從1900開始的
# 也有可能有 year 但沒有 month
# 這樣的話沒有month的year會被漏掉
# 所以計算的時候 後面要再加一個 -month:*的 year facet 把 month為空值的部分考慮進去

# 以 group + rightsHolder 為單位


taxon_group_map_e = {
    '鳥類': 'Birds',
    '爬蟲類': 'Reptiles',
    '哺乳類': 'Mammals',
    '甲蟲類': 'Beetles',
    '魚類': 'Fishes',
    '兩棲類': 'Amphibians',
    '蛾類': 'Moths',
    '蝶類': 'Butterflies',
    '蜘蛛': 'Spiders',
    '蜻蛉類': 'Dragonflies',
    '蝸牛與貝類': 'Snails & Shells',
    '其他昆蟲': 'Other Insects',
    '蝦蟹類': 'Crustaceans',
    '裸子植物': 'Gymnosperms',
    '被子植物': 'Angiosperms',
    '蕨類植物': 'Ferns',
    '苔蘚植物': 'Mosses',
    '真菌': 'Fungi',
    '藻類': 'Algae',
    '病毒': 'Viruses',
    '細菌': 'Bacteria',
}


# 共用：taxon rank 篩選條件（種 & 種下）
TAXON_RANK_FQ = 'taxonRank:(species OR subspecies OR nothosubspecies OR variety OR subvariety OR nothovariety OR form OR subform OR "special form" OR race OR stirp OR morph OR aberration)'


def fetch_year_month_buckets(filter_list):
    """從 tbia_records 取得 (year+month) 與 (no-month) 的 facet buckets。
    回傳 list of (year, month, count)；month='x' 表示原始資料無 month。"""
    base = f'{SOLR_PREFIX}tbia_records/select'
    body = json.dumps({"offset": 0, "limit": 0, "filter": filter_list})
    headers = {'content-type': 'application/json'}
    results = []

    # 1. year + month pivot
    url1 = f'{base}?q=*:*&facet.pivot=year,month&facet=true&facet.limit=-1&facet.mincount=1'
    data1 = requests.post(url1, data=body, headers=headers).json()
    for dd in data1['facet_counts']['facet_pivot']['year,month']:
        for ddd in (dd.get('pivot') or []):
            results.append((
                int(float(dd['value'])),
                int(float(ddd['value'])),
                ddd['count'],
            ))

    # 2. 沒有 month 的，依 year facet
    url2 = f'{base}?q=-month:*&facet.field=year&facet=true&facet.limit=-1&facet.mincount=1'
    data2 = requests.post(url2, data=body, headers=headers).json()
    yfacet = data2['facet_counts']['facet_fields']['year']
    for i in range(0, len(yfacet), 2):
        results.append((int(float(yfacet[i])), 'x', int(float(yfacet[i + 1]))))

    return results


class Command(BaseCommand):
    help = '產生 TaxonStat 的 temporal / taxon_group / family / taiwan_percentage 統計'

    def handle(self, *args, **options):
        now = datetime.now()
        rights_holder_map['total'] = 'total'

        # ===== 1. temporal stat（時間空缺） =====

        stat_list = []
        for k in rights_holder_map.keys():
            print(k)
            fq = ['county:* OR rawCounty:*']
            if k != 'total':
                fq.append(f'rightsHolder:"{k}"')
            for year, month, count in fetch_year_month_buckets(fq):
                stat_list.append({
                    'year': year, 'month': month, 'count': count,
                    'rights_holder': k, 'group': rights_holder_map[k],
                })

        stat_df = pd.DataFrame(stat_list)
        stat_df = stat_df[(stat_df.month.isin(range(1, 13))) | (stat_df.month == 'x')]
        stat_df = stat_df[stat_df.year.isin(range(1900, now.year + 1))]
        stat_df = stat_df.groupby(
            ['year', 'month', 'rights_holder', 'group'], as_index=False
        ).sum()
        stat_df['type'] = 'temporal'

        # 需要把之前的都刪掉 不然有可能沒辦法更新到
        TaxonStat.objects.filter(type='temporal').delete()
        TaxonStat.objects.bulk_create(
            [TaxonStat(**row) for row in stat_df.to_dict('records')],
            batch_size=1000,
        )


        # ===== 2. taxon_group stat（區分類群） =====
        # 這邊要只計算種 & 種下

        taxon_stat_list = []
        for tt in taxon_group_map_e.keys():
            base_fq = [
                'county:* OR rawCounty:*',
                f'bioGroup:{tt}',
                TAXON_RANK_FQ,
                'is_in_taiwan:1',
            ]
            for k in rights_holder_map.keys():
                fq = list(base_fq)
                if k != 'total':
                    fq.append(f'rightsHolder:"{k}"')

                # 1+2. year+month 與 no-month
                for year, month, count in fetch_year_month_buckets(fq):
                    taxon_stat_list.append({
                        'year': year, 'month': month, 'count': count,
                        'rights_holder': k, 'group': rights_holder_map[k],
                        'name': taxon_group_map_e[tt],
                    })

                # 3. 完全沒有時間考慮的總和
                body = json.dumps({"query": "*:*", "offset": 0, "limit": 0, "filter": fq})
                resp = requests.post(
                    f'{SOLR_PREFIX}tbia_records/select',
                    data=body, headers={'content-type': 'application/json'},
                ).json()
                taxon_stat_list.append({
                    'year': 'x', 'month': 'x', 'count': resp['response']['numFound'],
                    'rights_holder': k, 'group': rights_holder_map[k],
                    'name': taxon_group_map_e[tt],
                })

        taxon_stat_df = pd.DataFrame(taxon_stat_list)
        taxon_stat_df = taxon_stat_df[
            (taxon_stat_df.month.isin(range(1, 13))) | (taxon_stat_df.month == 'x')
        ]
        taxon_stat_df = taxon_stat_df[
            (taxon_stat_df.year.isin(range(1900, now.year + 1))) | (taxon_stat_df.year == 'x')
        ]
        taxon_stat_df = taxon_stat_df.groupby(
            ['year', 'month', 'rights_holder', 'group', 'name'], as_index=False
        ).sum()
        taxon_stat_df['type'] = 'taxon_group'

        # 需要把之前的都刪掉 不然有可能沒辦法更新到
        TaxonStat.objects.filter(type='taxon_group').delete()
        TaxonStat.objects.bulk_create(
            [TaxonStat(**row) for row in taxon_stat_df.to_dict('records')],
            batch_size=1000,
        )


        # ===== 3. family stat =====
        # 不需要區分台灣範圍
        # 只需要取前五
        # 用taxon group區分


        family_objs = []
        for r in rights_holder_map.keys():
            query = {
                "query": "*:*",
                "offset": 0, "limit": 0,
                "filter": [f'rightsHolder:"{r}"'],
                "facet": {
                    "family": {
                        "type": "terms",
                        "field": "family",
                        "limit": 5,
                        "sort": "count",
                    }
                },
            }
            resp = requests.post(
                f'{SOLR_PREFIX}tbia_records/select',
                data=json.dumps(query), headers={'content-type': 'application/json'},
            ).json()
            if resp['facets'].get('count'):
                for d in resp['facets']['family']['buckets']:
                    family_objs.append(TaxonStat(
                        rights_holder=r, name=d['val'], type='family',
                        count=d['count'], group=rights_holder_map[r],
                    ))

        TaxonStat.objects.filter(type='family').delete()
        TaxonStat.objects.bulk_create(family_objs, batch_size=1000)


        # ===== 4. 產生名錄列表 & 台灣種比例 =====
        # 1. 先從taxa找出 is_in_taiwan=1 & taxonRank = 種和種下 & 依據各類群的篩選條件
        # 2. 再從tbia_records找出 is_in_taiwan=1 & taxonRank = 種和種下 & 依據各類群的篩選條件

        # 佔TaiCOL臺灣鳥類物種數 1% <- 單位所有階層含有鳥綱的台灣種 / TaiCOL所有階層含有鳥綱的台灣種
        # type = taiwan_percentage
        # 計算的時候只從上面取taxonRank=species的資料

        # 可以點選文字後下載TaiCOL所有臺灣鳥類名錄，檔案中標明哪些是單位內有收錄的物種
        # csv 欄位: 學名 主要中文名 階層 所屬單位資料庫是否有收錄


        taicol_df = pd.DataFrame()
        dfs = []

        for tt in taxon_group_map_e.keys():
            query_list = []
            query_list += [f'bioGroup:{tt}']
            query_list += [TAXON_RANK_FQ]
            query_list += ['is_in_taiwan:1']
            query = {
                "query": "*:*",
                "offset": 0,
                "limit": 1000000,
                "filter": query_list,
                "fields": ['id', 'scientificName', 'common_name_c', 'taxonRank'],
            }
            response = requests.post(
                f'{SOLR_PREFIX}taxa/select',
                data=json.dumps(query), headers={'content-type': 'application/json'},
            )
            data = response.json()['response']['docs']
            df = pd.DataFrame(data)
            df['taxon_group'] = taxon_group_map_e[tt]
            dfs.append(df)

        taicol_df = pd.concat(dfs, ignore_index=True)
        taicol_df = taicol_df.drop_duplicates(subset=['id'])
        taicol_df = taicol_df.replace({nan: None})
        taicol_df = taicol_df.rename(columns={'id': 'taxon_id'})

        for tt in taxon_group_map_e.keys():
            for k in rights_holder_map.keys():
                query_list = []
                if k != 'total':
                    query_list += [f'rightsHolder:"{k}"']
                query_list += [f'bioGroup:{tt}']
                query_list += [TAXON_RANK_FQ]
                query_list += ['is_in_taiwan:1']
                query = {
                    "query": "*:*",
                    "offset": 0,
                    "limit": 0,
                    "filter": query_list,
                    "facet": {
                        "taxon_id": {
                            "type": "terms",
                            "field": "taxonID",
                            "limit": -1,
                        }
                    },
                }
                response = requests.post(
                    f'{SOLR_PREFIX}tbia_records/select',
                    data=json.dumps(query), headers={'content-type': 'application/json'},
                )
                if response.json()['facets']['count']:
                    data = response.json()['facets']['taxon_id']['buckets']
                    df = pd.DataFrame(data)
                    df = df.rename(columns={'val': 'taxon_id'})
                else:
                    df = pd.DataFrame(columns=['taxon_id', 'count'])
                now_taicol_df = taicol_df[
                    (taicol_df.taxon_group == taxon_group_map_e[tt])
                ].merge(df, how='left')
                # 後面的計算邏輯不用動
                taicol_len = len(now_taicol_df[
                    (now_taicol_df.taxon_group == taxon_group_map_e[tt])
                    & (now_taicol_df.taxonRank == 'species')
                ])
                partner_len = len(now_taicol_df[
                    (now_taicol_df.taxonRank == 'species')
                    & (now_taicol_df['count'].notna())
                ])
                if taicol_len == 0 and partner_len == 0:
                    tw_percentage = 0
                else:
                    tw_percentage = round((partner_len / taicol_len) * 100, 2)
                print(k, tt, tw_percentage)
                # 存在則update
                if TaxonStat.objects.filter(type='taiwan_percentage',
                                            rights_holder=k,
                                            group=rights_holder_map[k],
                                            name=taxon_group_map_e[tt]).exists():
                    ts_obj = TaxonStat.objects.get(type='taiwan_percentage',
                                            rights_holder=k,
                                            group=rights_holder_map[k],
                                            name=taxon_group_map_e[tt])
                    ts_obj.count = tw_percentage
                    ts_obj.save()
                # 不存在則新增
                else:
                    ts_obj = TaxonStat.objects.create(type='taiwan_percentage',
                                            rights_holder=k, group=rights_holder_map[k],
                                            name=taxon_group_map_e[tt], count=tw_percentage)
                # csv 欄位: 學名 主要中文名 階層 所屬單位資料庫是否有收錄
                if k == 'total':
                    now_taicol_df['TBIA入口網是否有收錄'] = now_taicol_df['count'].apply(lambda x: False if math.isnan(x) else True)
                    now_taicol_df = now_taicol_df[['scientificName', 'common_name_c', 'taxonRank', 'taxon_id', 'TBIA入口網是否有收錄']]
                    now_taicol_df = now_taicol_df.rename(columns={'scientificName': '學名', 'common_name_c': '中文名', 'taxonRank': '分類階層',
                                                                'taxon_id': 'taxonID'})
                    now_taicol_df.to_csv('/tbia-volumes/media/taxon_stat/{}_{}.csv'.format(k, tt), index=None)
                else:
                    now_taicol_df['所屬單位資料庫是否有收錄'] = now_taicol_df['count'].apply(lambda x: False if math.isnan(x) else True)
                    now_taicol_df = now_taicol_df[['scientificName', 'common_name_c', 'taxonRank', 'taxon_id', '所屬單位資料庫是否有收錄']]
                    now_taicol_df = now_taicol_df.rename(columns={'scientificName': '學名', 'common_name_c': '中文名', 'taxonRank': '分類階層',
                                                                'taxon_id': 'taxonID'})
                    now_taicol_df.to_csv('/tbia-volumes/media/taxon_stat/{}_{}.csv'.format(k, tt), index=None)
