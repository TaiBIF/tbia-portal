from django.http import request
from django.shortcuts import render, redirect
from conf.settings import STATIC_ROOT
from utils.solr_query import SolrQuery
from pages.models import Resource, News
from django.db.models import Q
import pandas as pd
import numpy as np

taicol = pd.read_csv('/tbia-volumes/bucket/TaiwanSpecies20211019_UTF8.csv')
# taicol = pd.read_csv('/Users/taibif/Documents/GitHub/tbia-volumes/TaiwanSpecies20210618_UTF8.csv')
taicol = taicol[taicol['is_accepted_name']==True][['name','common_name_c']]
taicol = taicol.replace({np.nan: ''})
taicol['common_name_c'] = taicol['common_name_c'].apply(lambda x: x.split(';')[0] if x else x)

facet_collection = ['scientificName', 'common_name_c','alternative_name_c', 
                    'synonyms', 'rightsHolder', 'sensitiveCategory', 'taxonRank', 
                    'locality', 'recordedBy', 'typeStatus', 'preservation', 'datasetName', 'license',
                    'kingdom','phylum','class','order','family','genus','species',
                    'kingdom_c','phylum_c','class_c','order_c','family_c','genus_c']

facet_occurrence = ['scientificName', 'common_name_c', 'alternative_name_c', 
                    'synonyms', 'rightsHolder', 'sensitiveCategory', 'taxonRank', 
                    'locality', 'recordedBy', 'basisOfRecord', 'datasetName', 'license',
                    'kingdom','phylum','class','order','family','genus','species',
                    'kingdom_c','phylum_c','class_c','order_c','family_c','genus_c']

map_occurrence = {
    'sourceScientificName': '原資料庫使用學名',
    'sourceVernacularName': '原資料庫使用中文名',
    'verbatimCoordinateSystem': '座標系統',
    'verbatimSRS': '空間參考系統',
    'organismQuantityType': '數量單位',
    'resourceContacts': '資料集聯絡人',
    'scientificName': '學名',
    'common_name_c': '主要中文名', 
    'alternative_name_c': '中文別名', 
    'synonyms': '同物異名',
    'rightsHolder': '來源資料庫', 
    'sensitiveCategory': '敏感層級', 
    'taxonRank': '分類層級', 
    'locality': '出現地', 
    'recordedBy': '紀錄者', 
    'basisOfRecord': '資料基底', 
    'datasetName': '資料集名稱', 
    'license': '授權狀況',
    'kingdom':'界',
    'phylum':'門',
    'class':'綱',
    'order':'目',
    'family':'科',
    'genus':'屬',
    'species':'種',
    'kingdom_c':'界',
    'phylum_c':'門',
    'class_c':'綱',
    'order_c':'目',
    'family_c':'科',
    'genus_c':'屬'
}

map_collection = {
    'sourceScientificName': '原資料庫使用學名',
    'sourceVernacularName': '原資料庫使用中文名',
    'verbatimCoordinateSystem': '座標系統',
    'verbatimSRS': '空間參考系統',
    'organismQuantityType': '數量單位',
    'resourceContacts': '資料集聯絡人',
    'scientificName': '學名', 
    'common_name_c': '主要中文名', 
    'alternative_name_c': '中文別名', 
    'synonyms': '同物異名',
    'rightsHolder': '典藏單位', 
    'sensitiveCategory': '敏感層級', 
    'taxonRank': '分類層級', 
    'locality': '採集地', 
    'recordedBy': '採集者', 
    'typeStatus': '標本類型', 
    'preservation': '保存方式', 
    'datasetName': '資料集名稱', 
    'license': '授權狀況',
    'kingdom':'界',
    'phylum':'門',
    'class':'綱',
    'order':'目',
    'family':'科',
    'genus':'屬',
    'species':'種',
    'kingdom_c':'界',
    'phylum_c':'門',
    'class_c':'綱',
    'order_c':'目',
    'family_c':'科',
    'genus_c':'屬',
}

def search_full_doc(request, result_type, keyword):
    # TODO 要帶著occurrence & collection的count & facet
    print(result_type, keyword)
    if result_type != 'resource':
        news = News.objects.filter(type=result_type).filter(Q(title__contains=keyword)|Q(content__contains=keyword))
        count = news.count()
        rows = []
        for x in news.all():
            rows.append({
                'title': x.title,
                'content': x.content,
                'id': x.id
            })
    else:
        resource = Resource.objects.filter(title__contains=keyword)
        count = resource.count()
        rows = []
        for x in resource.all():
            rows.append({
                'title': x.title,
                'extension': x.extension,
                'url': x.url,
                'date': x.modified.strftime("%Y.%m.%d")
            })

    response = {
        'type': result_type,
        'count': count,
        'rows': rows,
        'keyword': keyword
    }
    return render(request, 'pages/search_full_doc.html', response)


def search_full(request):
    keyword = request.GET.get('keyword', '')
    # 如果查中文俗名，包含所有別名的結果
    # 如果查同物異名，回傳正式學名結果

    if keyword:
        # TODO 階層
        query_list = [('q', keyword), ('rows', 0)]
        # collection
        solr = SolrQuery('tbia_collection',facet_collection)
        req = solr.request(query_list)
        c_collection = req['solr_response']['response']['numFound']
        collection_rows = []
        facets = req['solr_response']['facets']
        facets.pop('count', None)
        collection_card = []
        for i in facets:
            x = facets[i]
            tmp = [ i for i in x['buckets'] if keyword.lower() in i['val'].lower() ]
            if tmp:
                collection_rows.append({
                    'title': map_collection[i],
                    'buckets': tmp,
                    'total_count': sum(item['count'] for item in tmp)
                })
                for k in tmp:
                    tmp_s = {map_collection[i]: k['val']}
                    if i == 'scientificName':
                        # for q in k['rightsHolder']['buckets']:
                        collection_card.append({
                                'content':{
                                    '主要中文名': taicol.loc[taicol['name']==k['val']].common_name_c.values[0],
                                    '學名': k['val'],
                                    },
                                'count': k['count'],
                            })
                        if len(occurrence_card) > 10:
                            break
                    elif i == 'common_name_c':
                        # for q in k['rightsHolder']['buckets']:
                        collection_card.append({
                                'content':{
                                    '主要中文名': k['val'],
                                    '學名': taicol.loc[taicol['common_name_c']==k['val']].name.values[0],
                                    },
                                'count': k['count'],
                            })
                        if len(collection_card) > 10:
                            break
                    elif i != 'scientificName' and i != 'common_name_c':
                        for q in k['scientificName']['buckets']:
                            for_check_duplicated = {'content':{
                                '主要中文名': taicol.loc[taicol['name']==q['val']].common_name_c.values[0],
                                '學名': q['val']}, 'count': q['count']}
                            
                            if for_check_duplicated not in collection_card:
                                collection_card.append({
                                    'content':{
                                        '主要中文名': taicol.loc[taicol['name']==q['val']].common_name_c.values[0],
                                        '學名': q['val'],
                                        map_collection[i]: k['val'],
                                    },
                                    'count': q['count'],
                                })
                                if len(collection_card) > 10:
                                    break

        # occurrence
        solr = SolrQuery('tbia_occurrence',facet_occurrence)
        req = solr.request(query_list)
        c_occurrence = req['solr_response']['response']['numFound']
        occurrence_rows = []
        facets = req['solr_response']['facets']
        facets.pop('count', None)
        occurrence_card = []
        for i in facets:
            x = facets[i]
            tmp = [ i for i in x['buckets'] if keyword.lower() in i['val'].lower() ]
            if tmp:
                occurrence_rows.append({
                    'title': map_occurrence[i],
                    'buckets': tmp,
                    'total_count': sum(item['count'] for item in tmp)
                })
                for k in tmp:
                    tmp_s = {map_occurrence[i]: k['val']}
                    if i == 'scientificName':
                        # for q in k['rightsHolder']['buckets']:
                        occurrence_card.append({
                                'content':{
                                    '主要中文名': taicol.loc[taicol['name']==k['val']].common_name_c.values[0],
                                    '學名': k['val']},
                                'count': k['count'],
                            })
                        if len(occurrence_card) > 10:
                            break
                    elif i == 'common_name_c':
                        # for q in k['rightsHolder']['buckets']:
                        occurrence_card.append({
                                'content':{
                                    '主要中文名': k['val'],
                                    '學名': taicol.loc[taicol['common_name_c']==k['val']].name.values[0],},
                                'count': k['count'],
                            })
                        if len(occurrence_card) > 10:
                            break
                    elif i != 'scientificName' and i != 'common_name_c':
                        for q in k['scientificName']['buckets']:
                            for_check_duplicated = {
                                'content':{
                                '主要中文名': taicol.loc[taicol['name']==q['val']].common_name_c.values[0],
                                '學名': q['val']}, 'count': q['count']}
                            if for_check_duplicated not in occurrence_card:
                                occurrence_card.append({
                                    'content':{
                                        '主要中文名': taicol.loc[taicol['name']==q['val']].common_name_c.values[0],
                                        '學名': q['val'],
                                        map_occurrence[i]: k['val'],
                                    },
                                    'count': q['count'],
                                })
                                if len(occurrence_card) > 10:
                                    break
        # news
        news = News.objects.filter(type='news').filter(Q(title__contains=keyword)|Q(content__contains=keyword))
        c_news = news.count()
        news_rows = []
        for x in news.all()[:6]:
            news_rows.append({
                'title': x.title,
                'content': x.content,
                'id': x.id
            })
        event = News.objects.filter(type='event').filter(Q(title__contains=keyword)|Q(content__contains=keyword))
        c_event = event.count()
        event_rows = []
        for x in event.all()[:6]:
            event_rows.append({
                'title': x.title,
                'content': x.content,
                'id': x.id
            })
        project = News.objects.filter(type='project').filter(Q(title__contains=keyword)|Q(content__contains=keyword))
        c_project = project.count()
        project_rows = []
        for x in project.all()[:6]:
            project_rows.append({
                'title': x.title,
                'content': x.content,
                'id': x.id
            })
        # resource
        resource = Resource.objects.filter(title__contains=keyword)
        c_resource = resource.count()
        resource_rows = []
        for x in resource.all()[:6]:
            resource_rows.append({
                'title': x.title,
                'extension': x.extension,
                'url': x.url,
                'date': x.modified.strftime("%Y.%m.%d")
            })
        
        occurrence_more = True if len(occurrence_card) > 9 else False
        collection_more = True if len(collection_card) > 9 else False
        
        response = {
            'keyword': keyword,
            'occurrence': {'rows': occurrence_rows, 'count': c_occurrence, 'card': occurrence_card[:9], 'more': occurrence_more},
            'collection': {'rows': collection_rows, 'count': c_collection, 'card': collection_card[:9], 'more': collection_more},
            'news': {'rows': news_rows, 'count': c_news},
            'event': {'rows': event_rows, 'count': c_event},
            'project': {'rows': project_rows, 'count': c_project},
            'resource': {'rows': resource_rows, 'count': c_resource},
            }
    else:
        response = {

        }

    
    return render(request, 'pages/search_full.html', response)


def search_full_result(request):
    print(request)
    response = {}



    # 先不考慮階層
    # http://127.0.0.1:8983/solr/tbia_records/select?q=*species*&hl=on&hl.fl=*
    return render(request, 'pages/search_full_result.html')




def search_collection(request):
    return render(request, 'pages/search_collection.html')


def search_collection_details(request, tbiauuid):
    return render(request, 'pages/search_collection_details.html')


def search_occurrence(request):
    return render(request, 'pages/search_occurrence.html')


def search_occurrence_details(request, tbiauuid):
    return render(request, 'pages/search_occurrence_details.html')



