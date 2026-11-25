import os
import time
import psycopg2
import requests
import json
import re
import threading
from conf.background import run_light, run_heavy
import random
import string
import html
import math
import pandas as pd
import numpy as np
import bisect
import mimetypes
import zipfile
import logging
import csv
import codecs
import contextlib
from os.path import exists
from dateutil import parser
from datetime import datetime
import geopandas as gpd
import shapely.wkt as wkt
from shapely.geometry import MultiPolygon
from shapely.ops import unary_union
from data.solr_query import *
from pages.templatetags.tags import highlight, process_text_variants
from conf.settings import MEDIA_ROOT, SOLR_PREFIX, env, datahub_db_settings, SOLR_TIMEOUT, SOLR_TIMEOUT_LONG, RECORDS_URL, RECORDS_V1_URL
from django.db.models import Q
from django.db import connection
from django.utils import timezone, translation
from django.utils.translation import gettext
from django.http import QueryDict
from manager.models import User, Partner, SearchStat, Ark
from urllib.parse import urlencode, parse_qsl
import ast
from contextlib import contextmanager

# 3.4：參數相容層與類群 / 來源資料庫對照移到 data/search_params.py，這裡 re-export 給既有的 import
from data.search_params import (
    old_taxon_group_map_c, taxon_group_map_c, split_group_map, SOURCE_DATABASE_RENAME, to_source_database,
    normalize_pairs, canonical_pairs, parse_range, parse_circle, HABITAT_PARAM, TYPE_STATUS,
    TAXON_RANK_GROUPS, INFRASPECIES_RANKS, RANK_SOLR_VALUE, VALID_TAXON_RANKS, taxon_rank_v2,
)
from data.fields import (
    TAXON_FACETS, TAXON_KEYWORD_FIELDS, NAME_SEARCH_FIELDS, SOURCE_NAME_FIELDS,
    LATIN_TXT_FIELDS, BIGRAM_FIELDS, NGRAM_FIELDS, map_occurrence, map_collection,
    DOWNLOAD_FIELDS, DOWNLOAD_FIELDS_WITH_SENSITIVE, SENSITIVE_FIELDS, UNSORTABLE_KEYS,
    DOWNLOAD_SOLR_FL, DOWNLOAD_SOLR_FL_WITH_SENSITIVE, RESTRICTED_OVERRIDE,
    SPECIES_DOWNLOAD_COLUMNS, SPECIES_DOWNLOAD_BOOL_COLUMNS,
    to_record_field, to_taxa_field, to_v2_field, param_field, param_label,
)

# 欄位清單改由 data/fields.py 定義（D29）；以下名稱保留給既有 import 使用
taxon_facets = TAXON_FACETS
taxon_keyword_list = TAXON_KEYWORD_FIELDS


# --- ngram 子字串查詢工具 ---
# 單字元異體字由 Solr text_ngram 的 MappingCharFilter 折疊；此處只在查詢端展開會意字，
# 以保留「只搜其中一個字」的子字串行為。
with open('/code/data/composites.json', 'r', encoding='utf-8') as _f:
    _COMPOSITE_MAP = json.load(_f)


def _expand_composite_forms(keyword):
    """回傳關鍵字的所有會意字等價形（雙向替換）。"""
    forms = {keyword}
    changed = True
    while changed:
        changed = False
        for a, b in _COMPOSITE_MAP.items():
            for f in list(forms):
                for src, dst in ((a, b), (b, a)):
                    if src in f and f.replace(src, dst) not in forms:
                        forms.add(f.replace(src, dst))
                        changed = True
    return forms


# 拉丁欄位走分詞+前綴(edge-ngram, A+)；BIGRAM_FIELDS 走 bigram；其餘走 unigram（清單見 data/fields.py）


def _esc_q(s):
    return s.replace(chr(92), chr(92) * 2).replace(chr(34), chr(92) + chr(34))



def build_keyword_reg(val):
    """關鍵字轉成不分大小寫的 Solr regex 片段（英文字母 → [Aa]，其他字元跳脫）。
    原本在多處各自用 for 迴圈組字串，結果相同。"""
    return ''.join(f"[{j.upper()}{j.lower()}]" if is_alpha(j) else escape_solr_query(j) for j in val)

def solr_quote(val):
    """把使用者輸入包成 Solr 片語（跳脫反斜線與雙引號），避免輸入改寫查詢語法。
    對 string / point 欄位而言，"值" 與 值 的查詢結果相同。"""
    return '"' + _esc_q(str(val)) + '"'


def ngram_contains_query(field, keyword):
    """依欄位型別建立查詢：
    - 拉丁欄位(_txt)：分詞 + 前綴，各詞皆須命中（整詞可在任何位置、支援前綴 typeahead）。
    - datasetName(_bi)：長度>=2 走 bigram，否則 unigram；含會意字 OR 展開。
    - 其餘(_ngram)：unigram 子字串；含會意字 OR 展開。
    單字元異體字一律由 Solr charfilter 折疊。"""
    kw = re.sub(' +', ' ', keyword).strip()
    if not kw:
        return f'{field}_ngram:""'
    if field in LATIN_TXT_FIELDS:
        parts = [f'+{field}_txt:"{_esc_q(w)}"' for w in kw.split(' ') if w]
        return '(' + ' '.join(parts) + ')' if parts else f'{field}_txt:""'
    suffix = '_bi' if (field in BIGRAM_FIELDS and len(kw) >= 2) else '_ngram'
    clauses = [f'{field}{suffix}:"{_esc_q(form)}"' for form in _expand_composite_forms(kw)]
    return '(' + ' OR '.join(clauses) + ')'


def contains_clause(field, keyword, keyword_reg):
    """單一欄位的 contains 查詢：有 _ngram 就走 ngram，否則沿用舊 regex（keyword_reg 已含變體展開）。"""
    if field in NGRAM_FIELDS:
        return ngram_contains_query(field, keyword)
    return f'{field}:/.*{keyword_reg}.*/'


name_status_map = {
    'not-accepted': '的無效名',
    'misapplied': '的誤用名',
}


basis_map = {
    "HumanObservation":"人為觀測",
    "MachineObservation":"機器觀測",
    "PreservedSpecimen":"保存標本",
    "MaterialSample":"材料樣本",
    "LivingSpecimen":"活體標本",
    "FossilSpecimen":"化石標本",
    "MaterialCitation":"文獻紀錄",
    "MaterialEntity":"材料實體",
    "Taxon":"分類群",
    "Occurrence":"出現紀錄",
    "Event":"調查活動"
}


rights_holder_map = {
    'GBIF': 'gbif',
    '中央研究院生物多樣性中心動物標本館': 'asiz',
    '中央研究院生物多樣性中心植物標本資料庫': 'hast',
    '台灣生物多樣性網絡 TBN': 'tbri',
    '國立臺灣博物館典藏': 'ntm',
    '林業試驗所昆蟲標本館': 'fact',
    '林業試驗所植物標本資料庫': 'taif',
    '河川環境資料庫': 'wra',
    '濕地環境資料庫': 'nps',
    '生態調查資料庫系統': 'forest',
    '臺灣國家公園生物多樣性資料庫': 'nps',
    '臺灣生物多樣性資訊機構 TaiBIF': 'brcas',
    '海洋保育資料倉儲系統': 'oca',
    '科博典藏 (NMNS Collection)': 'nmns',
    '臺灣魚類資料庫': 'ascdc',
    '國家海洋資料庫及共享平台': 'namr',
    '集水區友善環境生態資料庫': 'ardswc',
    '中油生態地圖': 'cpc',
    '作物種原資訊系統': 'npgrc',
    '國立海洋生物博物館生物典藏管理系統': 'nmmba',
    '愛自然-臺灣(iNaturalist Taiwan)': 'ntuforestry'
}

rights_holder_list = list(rights_holder_map.values())

# v2 sourceDatabase（新名稱）→ group；rights_holder_map（舊名稱）保留給讀舊紀錄（3.2 / 4.2）
source_database_map = {SOURCE_DATABASE_RENAME.get(k, k): v for k, v in rights_holder_map.items()}


_SOURCE_DATABASE_OLD = {v: k for k, v in SOURCE_DATABASE_RENAME.items()}


def source_database_aliases(name):
    """[P2-2-REMOVE] 同一來源資料庫的新舊名稱（去重、新名稱在前）。
    P2-2 把 dataset core / PG dataset 改成新名稱後，呼叫端改用 to_source_database（舊網址的舊名稱仍要轉）即可刪除。
    第一階段 dataset core 與 PG dataset 表仍是舊名稱（P2-2 才改），網頁下拉改用新名稱後，查 dataset 時新舊都要比對"""
    new = to_source_database(name)
    return list(dict.fromkeys([new, _SOURCE_DATABASE_OLD.get(new, new), name]))
rights_holder_color_map = ['#FBEAD6', '#A8B89A', '#7A9B87', '#8DA3B5', '#B89AAC', '#F08A7A', '#DCB791', '#9CAA82', '#6E9B87', '#92BCD4', '#D199AC', '#DA816B', '#D99758', '#C8C4A3', '#587164', '#7AA8D9', '#936572', '#C2674A', '#B48556', '#C9C280', '#B1C0B8', '#5C668E', '#C69B9A', '#B45631', '#AA8B6B', '#837D40', '#ADD5B8', '#4A4F67', '#E28A88', '#C25519']


@contextmanager
def datahub_conn():
    conn = psycopg2.connect(**datahub_db_settings)
    try:
        yield conn
        conn.commit()          # 正常結束才提交（純查詢也無妨）
    except Exception:
        conn.rollback()        # 出錯回滾，避免半套交易
        raise
    finally:
        conn.close()           # 無論如何都關閉


def to_int(value, default=0):
    """安全轉 int:None / 空字串 / 非數字都回 default。"""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def build_query_string(mapping):
    """統一產生 SearchStat.query，正確處理多值。"""
    if isinstance(mapping, QueryDict):
        return mapping.urlencode()
    return urlencode(mapping, doseq=True)


def parse_query_string(query, normalize=True):
    """統一讀取已存的查詢字串（SearchQuery.query / SearchStat.query），回傳 QueryDict。
       相容 DB 既有舊格式 key=['A','B']，自動展開成真正的多值。
       normalize=True（預設）時轉成 v2 標準形式（3.4），回傳值帶 .removed / .notes（見 normalize_search_params）；
       統計 v1 API 的原始參數時用 normalize=False"""
    qd = QueryDict('', mutable=True)
    for key, value in parse_qsl(query or '', keep_blank_values=True):
        if value.startswith('[') and value.endswith(']'):
            try:
                lit = ast.literal_eval(value)
                if isinstance(lit, list):
                    for item in lit:
                        qd.appendlist(key, str(item))
                    continue
            except (ValueError, SyntaxError):
                pass
        qd.appendlist(key, value)
    return normalize_search_params(qd) if normalize else qd


def _mapping_pairs(mapping):
    """QueryDict / dict（值可能是 list）→ (key, value) 清單"""
    if hasattr(mapping, 'lists'):
        return [(k, v) for k, vals in mapping.lists() for v in vals]
    pairs = []
    for k, v in (mapping or {}).items():
        for x in (v if isinstance(v, (list, tuple)) else [v]):
            if x is not None:
                pairs.append((k, str(x)))
    return pairs


STAT_EXCLUDE_KEYS = {
    'apikey', 'csrfmiddlewaretoken',
    'page', 'offset', 'limit', 'cursor', 'orderby', 'sort',
    'from', 'selected_col', 'grid', 'map_bound', 'taxon', 'record_type',
    'is_agreed_report', 'user_affiliation', 'user_role', 'user_purpose',
    'from_example',
}

# 可重播查詢的排除集：保留 record_type（重播要用它分 col/occ），並排掉全站下載的路由旗標
QUERY_REPLAY_EXCLUDE_KEYS = (STAT_EXCLUDE_KEYS - {'record_type'}) | {'from_full'}

# 敏感申請表單專屬欄位（只在建立 request 時寫進 SensitiveDataRequest，不進任何 query）
SENSITIVE_FORM_FIELDS = {
    'applicant', 'phone', 'address', 'affiliation', 'job_title', 'type',
    'project_name', 'project_affiliation', 'abstract', 'users',
    'principal_investigator', 'research_proposal',
}

def build_stat_query_string(mapping):
    """產生要存進 SearchStat.query 的字串，濾掉分頁/敏感/內部參數。"""
    if isinstance(mapping, QueryDict):
        mapping = mapping.copy()
        for k in STAT_EXCLUDE_KEYS:
            mapping.pop(k, None)
        return mapping.urlencode()
    clean = {k: v for k, v in mapping.items() if k not in STAT_EXCLUDE_KEYS}
    return urlencode(clean, doseq=True)


def get_multi(req_dict, key):
    """取多值，相容 QueryDict / 普通 dict / 舊的 '[...]' 字面格式。"""
    if hasattr(req_dict, 'getlist'):
        vals = req_dict.getlist(key)
    else:
        v = req_dict.get(key)
        vals = v if isinstance(v, list) else ([v] if v not in (None, '') else [])
    out = []
    for v in vals:
        if isinstance(v, str) and v.startswith('[') and v.endswith(']'):
            try:
                lit = ast.literal_eval(v)
                if isinstance(lit, list):
                    out.extend(str(x) for x in lit)
                    continue
            except (ValueError, SyntaxError):
                pass
        out.append(v)
    return out


_PARTNER_NAME_CACHE = {'t': 0, 'zh': {}, 'en': {}, 'group': {}}


def get_partner_name_map(lang=None):
    """tbiaPartnerID → partnerName（Partner.title；lang='en' 用 title_en，沒有就退回 title）。
    Solr 與 PG dataset 只存 tbiaPartnerID，顯示 / 下載時才帶入名稱；結果快取 5 分鐘，
    避免每次請求（表格每列、下載每列）都查 DB。下載 CSV 一律用中文 title（與 API 一致）"""
    now = time.time()
    if now - _PARTNER_NAME_CACHE['t'] > 300 or not _PARTNER_NAME_CACHE['zh']:
        zh, en, by_group = {}, {}, {}
        for pid, title, title_en, group in Partner.objects.exclude(tbia_partner_id__isnull=True).order_by('id').values_list('tbia_partner_id', 'title', 'title_en', 'group'):
            zh.setdefault(str(pid), title)  # 同一單位多列 Partner 的 title 相同（D28）
            en.setdefault(str(pid), title_en or title)
            by_group.setdefault(group, str(pid))
        _PARTNER_NAME_CACHE.update(t=now, zh=zh, en=en, group=by_group)
    if lang is None:
        lang = 'en' if str(translation.get_language() or '').startswith('en') else 'zh'
    return _PARTNER_NAME_CACHE[lang]


def get_partner_name(partner_id, lang=None):
    return get_partner_name_map(lang).get(str(partner_id), '') if partner_id else ''


def get_partner_id_by_group(group):
    """records.group / dataset.group → tbiaPartnerID（PG dataset 沒有 tbiaPartnerID，靠 group 對 Partner）；gbif 沒有"""
    get_partner_name_map()  # 確保快取已更新
    return _PARTNER_NAME_CACHE['group'].get(group, '')


def get_dataset_name(key):
    # 2024-12 修改為tbiaDatasetID
    name = ''

    qk = solr_quote(key)
    response = requests.get(f'{SOLR_PREFIX}dataset/select', params={'q.op': 'OR', 'q': f'id:{qk} OR tbiaDatasetID:{qk}', 'rows': 20, 'fq': 'deprecated:false'}, timeout=SOLR_TIMEOUT)
    d_list = response.json()['response']['docs']

    # solr內的id和datahub的postgres互通
    for l in d_list:
        name = l['name'] 
        if l.get('is_duplicated_name'):
            name += ' ({})'.format(to_source_database(l['rights_holder']))  # [P2-2-REMOVE]
    return name


def get_tbia_dataset_id(key):
    # 2024-12 修改為tbiaDatasetID
    try:
        key = int(key)
        query = 'SELECT "tbiaDatasetID" FROM dataset WHERE "id" = %s'  # 不考慮deprecated
    except (ValueError, TypeError):
        query = 'SELECT "tbiaDatasetID" FROM dataset WHERE "tbiaDatasetID" = %s'  # 不考慮deprecated

    with datahub_conn() as conn, conn.cursor() as cursor:
        cursor.execute(query, (key,))
        results = cursor.fetchone()

    return results[0] if results else None


def get_species_images(taxon_id):
    query = "SELECT taieol_id, images FROM species_images WHERE taxon_id = %s"
    with datahub_conn() as conn, conn.cursor() as cursor:
        cursor.execute(query, (taxon_id,))
        results = cursor.fetchone()
    return results


def get_dataset_by_key(key_list):

    if not key_list:
        return []

    results = []
    
    query = ''' select "tbiaDatasetID", name FROM dataset WHERE "tbiaDatasetID" IN %s AND deprecated = 'f' '''

    with datahub_conn() as conn, conn.cursor() as cursor:
        cursor.execute(query, (tuple(key_list), ))
        results = cursor.fetchall()
        
    return results


spe_chars = ['+','-', '&','&&', '||', '!','(', ')', '{', '}', '[', ']', '^', '"', '~', '*', '?', ':', '/']

def escape_solr_query(string):
    final_string = ''
    for s in string:
        if s in spe_chars:
            final_string += f'\\{s}'  # 用 \\ 表示一個反斜線
        else:
            final_string += s
    return final_string



logger = logging.getLogger(__name__)


csv.field_size_limit(2 ** 31 - 1)  # associatedMedia 等欄位可能很長


def format_solr_date(value):
    """Solr 日期 2026-11-05T01:23:45Z → API 格式 YYYYMMDD HHMMSS（D3，時間本身已是台灣時間）；不是日期格式的原樣回傳"""
    if len(value) >= 19 and value[4] == '-' and value[10] == 'T':
        return f'{value[:4]}{value[5:7]}{value[8:10]} {value[11:13]}{value[14:16]}{value[17:19]}'
    return value


def iter_text_lines(chunks):
    """bytes 區塊 → 保留換行的文字行（只依 \n 切；引號內的換行由 csv.reader 接回同一欄）"""
    decoder = codecs.getincrementaldecoder('utf-8')()
    buf = ''
    for chunk in chunks:
        buf += decoder.decode(chunk)
        parts = buf.split('\n')
        buf = parts.pop()
        for part in parts:
            yield part + '\n'
    buf += decoder.decode(b'', final=True)
    if buf:
        yield buf


# 7.1：名錄下載與 API 重複的欄位，值以 API 為準
# taxa core 的 alien_type 有 1 筆 cultivated（TaiCOL 舊值），併入 API 的 cultured
SPECIES_NATIVENESS_FIX = {'cultivated': 'cultured'}
# 文資法珍貴稀有植物在 taxa core 是 1（D12）
SPECIES_PROTECTED_FIX = {'1': 'CHPA'}


def format_species_download(taxa_docs):
    """taxa core 的 docs（舊欄位名，D21）→ 名錄下載的欄位（v2 名稱，順序同 SPECIES_DOWNLOAD_COLUMNS，含 taxonID）。
    taxonRank 同 API（Special Form），protectedStatus / nativeness 用 API 的詞彙，布林欄位為 true / false，沒有值為空字串"""
    rows = []
    for d in taxa_docs:
        row = {'taxonID': d.get('id', '')}
        for src, out in SPECIES_DOWNLOAD_COLUMNS:
            v = d.get(src)
            if isinstance(v, list):
                v = v[0] if v else None
            if v is None or v == '':
                row[out] = ''
            elif out in SPECIES_DOWNLOAD_BOOL_COLUMNS:
                row[out] = 'true' if v in (True, 1, 't', 'true', 'True', '1') else 'false'
            elif out == 'taxonRank':
                row[out] = taxon_rank_v2(str(v))
            elif out == 'protectedStatus':
                row[out] = SPECIES_PROTECTED_FIX.get(str(v), str(v))
            elif out == 'nativeness':
                row[out] = SPECIES_NATIVENESS_FIX.get(str(v), str(v))
            else:
                row[out] = v
        rows.append(row)
    return rows


def write_download_rows(chunks, writer, out_cols, public_writer=None):
    """把 Solr 的 CSV 內容依 out_cols 重排後寫出：Solr 沒有的欄位補空值、多取的欄位丟掉，
    created / modified、taxonRank 轉成 API 格式（7.1：值以 API 為準）。表頭由呼叫端寫（每個查詢的表頭不一定相同）。
    限制型取值（同 API）：Solr 結果若含 raw 欄位且有值，就取代 writer 那份的對應公開欄位（RESTRICTED_OVERRIDE）。
    public_writer 給了就同時寫一份只有公開值的版本（永久保存用），兩份來自同一次查詢。"""
    reader = csv.reader(iter_text_lines(chunks))
    header = next(reader, None)
    if header is None:
        return
    pos = {c: i for i, c in enumerate(header)}
    picks = [pos.get(c) for c in out_cols]
    date_idx = [k for k, c in enumerate(out_cols) if c in ('created', 'modified')]
    rank_idx = out_cols.index('taxonRank') if 'taxonRank' in out_cols else None
    # (輸出欄位位置, raw 欄位在 Solr 結果的位置)：只有這次查詢真的取了 raw 欄位才會有
    overrides = [(out_cols.index(c), pos[r]) for c, r in RESTRICTED_OVERRIDE.items() if c in out_cols and r in pos]
    # partnerName 不在 Solr：由 tbiaPartnerID 帶入
    name_idx = out_cols.index('partnerName') if 'partnerName' in out_cols else None
    id_idx = out_cols.index('tbiaPartnerID') if 'tbiaPartnerID' in out_cols else None
    partner_names = get_partner_name_map('zh') if name_idx is not None and id_idx is not None else {}
    for row in reader:
        if not row:
            continue
        new = [row[i] if i is not None and i < len(row) else '' for i in picks]
        for k in date_idx:
            new[k] = format_solr_date(new[k])
        if rank_idx is not None and new[rank_idx]:
            new[rank_idx] = taxon_rank_v2(new[rank_idx])
        if partner_names and new[id_idx]:
            new[name_idx] = partner_names.get(new[id_idx], '')
        if public_writer:
            public_writer.writerow(new)
        for k, ri in overrides:
            if ri < len(row) and row[ri] != '':
                new[k] = row[ri]
        writer.writerow(new)


def solr_csv_to_zip(queries, csv_file_path, zip_file_path, out_cols=None, public_zip_path=None):
    """依序把 queries 的 Solr CSV 結果寫入 csv_file_path（第 2 組起去掉表頭），再壓成 zip_file_path。
    取代原本 shell=True 的 curl / cat / tail / zip 指令。成功回傳 True；失敗記錄錯誤、清掉半成品並回傳 False。
    給 out_cols（下載 CSV）時逐列重排成該欄位（見 write_download_rows），所有查詢的欄位因此一致；
    不給（v1 API）則原樣串接 Solr 輸出。
    public_zip_path：同時產出只有公開值的版本（zip 內檔名與主檔相同），給永久保存用；僅在 out_cols 時有效。"""
    url = f'{RECORDS_URL}?wt=csv'
    ok = False
    public_csv_path = f'{csv_file_path}.public' if out_cols and public_zip_path else None
    try:
        with open(csv_file_path, 'w' if out_cols else 'wb', **({'encoding': 'utf-8', 'newline': ''} if out_cols else {})) as out, \
                (open(public_csv_path, 'w', encoding='utf-8', newline='') if public_csv_path else contextlib.nullcontext()) as pub_out:
            writer = public_writer = None
            if out_cols:
                writer = csv.writer(out, lineterminator='\n')
                writer.writerow(out_cols)
                if pub_out:
                    public_writer = csv.writer(pub_out, lineterminator='\n')
                    public_writer.writerow(out_cols)
            for n, query in enumerate(queries):
                with requests.post(url, data=json.dumps(query), headers={'content-type': 'application/json'},
                                   stream=True, timeout=(10, SOLR_TIMEOUT_LONG)) as r:
                    r.raise_for_status()
                    if out_cols:
                        write_download_rows(r.iter_content(chunk_size=1 << 20), writer, out_cols, public_writer)
                        continue
                    skip_header = n > 0
                    for chunk in r.iter_content(chunk_size=1 << 20):
                        if skip_header:
                            pos = chunk.find(b'\n')
                            if pos < 0:
                                continue
                            chunk = chunk[pos + 1:]
                            skip_header = False
                        out.write(chunk)
        with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as z:
            z.write(csv_file_path, arcname=os.path.basename(csv_file_path))
        if public_csv_path:
            with zipfile.ZipFile(public_zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
                z.write(public_csv_path, arcname=os.path.basename(csv_file_path))
        ok = True
    except Exception:
        logger.exception('solr_csv_to_zip failed: %s', zip_file_path)
        for f in (zip_file_path, public_zip_path):
            if f and os.path.exists(f):
                os.remove(f)
    finally:
        for f in (csv_file_path, public_csv_path):
            if f and os.path.exists(f):
                os.remove(f)
    return ok


def public_zip_path_for(folder, download_id):
    """永久保存用的公開版 zip 路徑（download/<folder>_public/<download_id>.zip），資料夾不存在就建立。
    檔案與主檔同期限，由 scripts/system/check_file_expired.py 一併清除。"""
    public_dir = os.path.join(MEDIA_ROOT, 'download', f'{folder}_public')
    os.makedirs(public_dir, exist_ok=True)
    return os.path.join(public_dir, f'{download_id}.zip')



taxon_group_map_e = {
    '鳥類':	'Birds',
    '爬蟲類':	'Reptiles',
    '哺乳類':	'Mammals',
    '甲蟲類': 	'Beetles',
    '魚類':	'Fishes',
    '兩棲類':	'Amphibians',
    '蛾類': 	'Moths',
    '蝶類': 	'Butterflies',
    '蜘蛛':	'Spiders',
    '蜻蛉類': 	'Dragonflies',
    '蝸牛與貝類': 	'Snails & Shells',
    '其他昆蟲':	'Other Insects',
    '蝦蟹類': 	'Crustaceans',
    '裸子植物': 	'Gymnosperms',
    '被子植物': 	'Angiosperms',
    '蕨類植物':	'Ferns',
    '苔蘚植物':	'Mosses',
    '真菌':	'Fungi',
    '維管束植物':	'Vascular Plants',
    '昆蟲':	'Insects',
    '藻類':	'Algae',
    '病毒':	'Viruses',
    '細菌':	'Bacteria',
}


# taxon_group_map_tbn = {
#     "昆蟲": "beetles,butterflies,moths,dragonflies,otherinsects",
#     '甲蟲類':    'beetles',
#     '蛾類':      'moths',
#     '蝶類':      'butterflies',
#     '蜻蛉類':    'dragonflies',
#     '其他昆蟲':  'otherinsects',
#     '蜘蛛':      'spiders',
#     '蝸牛與貝類':'snailsshells',
#     '魚類':      'fishes',
#     '兩棲類':    'amphibians',
#     '爬蟲類':    'reptiles',
#     '鳥類':      'birds',
#     '哺乳類':    'mammals',
#     '蝦蟹類':    'crustaceans',
#     '被子植物':  'angiosperms',
#     '裸子植物':  'gymnosperms',
#     '蕨類植物':  'ferns,lycophytes',
#     "維管束植物": "lycophytes,gymnosperms,angiosperms,ferns",
#     '苔蘚植物':  'mosses',
#     '藻類':      'chromista',
#     '真菌':      'fungi',
# }

taxon_group_map_tbn = [
    '鳥類',
    '爬蟲類',
    '哺乳類',
    '魚類',
    '兩棲類',
    '真菌',
]


habitat_map = {
    'is_terrestrial': '陸域',
    'is_freshwater': '淡水',
    'is_brackish': '半鹹水',
    'is_marine': '海洋',
}

def convert_coor_to_grid(x, y, grid):
    list_x = np.arange(-180, 180+grid, grid)
    list_y = np.arange(-90, 90+grid, grid)
    grid_x = bisect.bisect(list_x, x)-1
    grid_y = bisect.bisect(list_y, y)-1
    return grid_x, grid_y


def convert_grid_to_square(grid_x, grid_y, grid):
    list_x = np.arange(-180, 180+grid, grid)
    list_y = np.arange(-90, 90+grid, grid)
    x1 = round(list_x[grid_x],4)
    x2 = round(list_x[grid_x+1],4)
    y1 = round(list_y[grid_y],4)
    y2 = round(list_y[grid_y+1],4)
    return [[x1,y1],[x2,y1],[x2,y2],[x1,y2],[x1,y1]]


def format_grid(grid_x, grid_y, grid, count):
    dic = {
            "type": "Feature",
            "geometry":{"type":"Polygon","coordinates":[convert_grid_to_square(grid_x, grid_y, grid/100)]},
            "properties": {
                "counts": count
            }
        }
    return dic


rank_list = ['domain', 'superkingdom', 'kingdom', 'subkingdom', 'infrakingdom', 'superdivision', 'division', 'subdivision', 
            'infradivision', 'parvdivision', 'superphylum', 'phylum', 'subphylum', 'infraphylum', 'microphylum', 'parvphylum', 
            'superclass', 'class', 'subclass', 'infraclass', 'superorder', 'order', 'suborder', 'infraorder', 'superfamily', 'family', 
            'subfamily', 'tribe', 'subtribe', 'genus', 'subgenus', 'section', 'subsection', 'species', 'subspecies', 'nothosubspecies', 
            'variety', 'subvariety', 'nothovariety', 'form', 'subform', 'specialform', 'race', 'stirp', 'morph', 'aberration', 'hybridformula']


def get_page_list(current_page, total_page, window=5):
  list_index = math.ceil(current_page/window)
  if list_index*window > total_page:
    page_list = list(range(list_index*window-(window-1),total_page+1))
  else:
    page_list = list(range(list_index*window-(window-1),list_index*window+1))
  return page_list


def is_alpha(word):
    try:
        return word.encode('ascii').isalpha()
    except:
        return False


# 進階搜尋查詢name欄位
name_search_col = NAME_SEARCH_FIELDS

def get_key(val, my_dict):
    for key, value in my_dict.items():
         if val == value:
             return key
    return "key doesn't exist"

# map_occurrence / map_collection 由 data/fields.py 定義（key 為 records v2 欄位）


date_formats = ['%Y/%m/%d','%Y%m%d','%Y-%m-%d','%Y/%m/%d %H:%M:%S','%Y-%m-%d %H:%M',
                '%Y/%m/%d %H:%M','%Y-%m-%d %H:%M:%S','%Y/%m/%d %H:%M:%S',
                '%Y/%m/%d %p %I:%M:%S', '%Y/%m/%d %H', '%Y-%m-%d %H', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%SZ']
# 要和datahub同步
def convert_date(date):
    formatted_date = None
    if date != '' and date is not None:
        date = str(date)
        date = date.replace('上午','AM').replace('下午','PM')
        for ff in date_formats:
            try:
                formatted_date = datetime.strptime(date, ff)
                return formatted_date
            except:
                formatted_date = None
        if not formatted_date:
            try:
                formatted_date = parser.parse(date)
            except:
                formatted_date = None
        if not formatted_date:
            try: 
                date = date.split('T')[0]
                formatted_date = datetime.strptime(date, '%Y-%m-%d')
                return formatted_date
            except:
                formatted_date = None        
        if not formatted_date:
            try:
                formatted_date = datetime.fromtimestamp(int(date))
                return formatted_date
            except:
                formatted_date = None
    return formatted_date


download_cols = DOWNLOAD_FIELDS  # 輸出欄位（CSV 表頭）
download_cols_with_sensitive = DOWNLOAD_FIELDS_WITH_SENSITIVE
download_fl = DOWNLOAD_SOLR_FL  # 送給 Solr 的 fl（tbiaID 用別名取 id）
download_fl_with_sensitive = DOWNLOAD_SOLR_FL_WITH_SENSITIVE
sensitive_cols = SENSITIVE_FIELDS


def get_media_html(url, media_type=None):
    if not media_type:
        mime_type, _ = mimetypes.guess_type(url.split('?')[0])
        media_type = mime_type.split('/')[0] if mime_type else 'image'

    err_msg = gettext('多媒體無法正常顯示')

    if media_type == 'image':
        return '<img class="icon-size-50" alt="{}" title="{}" src="{}">'.format(err_msg, err_msg, url)
    elif media_type == 'video':
        return '<video class="icon-size-50" controls><source src="{}">{}</video>'.format(url, err_msg)
    elif media_type == 'audio':
        return '<audio controls><source src="{}">{}</audio>'.format(url, err_msg)
    else:
        return '<img class="icon-size-50" alt="{}" title="{}" src="{}">'.format(err_msg, err_msg, url)


def get_media_type(url):
    mime_type, _ = mimetypes.guess_type(url.split('?')[0])
    if mime_type:
        return mime_type.split('/')[0]
    return 'image'


# 整理搜尋條件
# 3.4：查詢條件顯示用的值標籤（v2 參數值 → 中文，顯示時 gettext）
NATIVENESS_LABELS = {'native': '原生', 'naturalized': '歸化', 'invasive': '入侵', 'cultured': '栽培豢養'}
PROTECTED_STATUS_LABELS = {'I': '第 I 級（瀕臨絕種）', 'II': '第 II 級（珍貴稀有）', 'III': '第 III 級（其他應予保育）',
                           'CHPA': '文化資產保存法珍貴稀有植物'}
TYPE_STATUS_LABELS = {'HOLOTYPE': '正模標本', 'PARATYPE': '副模標本', 'ISOTYPE': '複模標本', 'ALLOTYPE': '配模標本',
                      'SYNTYPE': '總模標本', 'LECTOTYPE': '選模標本', 'PARALECTOTYPE': '副選模標本',
                      'NEOTYPE': '新模標本', 'TOPOTYPE': '模式地標本'}
MEDIA_LABELS = {'false': '無多媒體', 'true': '有多媒體', 'image': '影像', 'video': '影片', 'audio': '音檔'}


def _ymd(d8):
    return f'{d8[:4]}-{d8[4:6]}-{d8[6:]}' if d8 else ''


def create_query_display(search_dict, lang=None, escape_values=True):
    """搜尋條件的文字說明（後台下載紀錄、敏感申請、申請頁）。輸入可為舊字串讀出的條件，一律先轉成 v2 標準形式；
       已停止提供的條件列在最後（標示已停用），讓使用者知道再次查詢的結果會和當初不同
       escape_values：輸出到網頁時跳脫使用者輸入（預設）；轉純文字（敏感資料報表 Excel）時傳 False（11/21 main 合入）"""
    _v = (lambda x: html.escape(str(x)) if x is not None else '') if escape_values else (lambda x: '' if x is None else x)
    if lang:
        translation.activate(lang)
    sd = normalize_search_params(search_dict)
    removed = list(dict.fromkeys((getattr(search_dict, 'removed', None) or []) + sd.removed))
    notes = list(dict.fromkeys((getattr(search_dict, 'notes', None) or []) + sd.notes))

    sep = gettext('：')
    def line(label, val, raw=False):
        # raw=True：val 是程式組好的 HTML（只用在 GeoJSON 下載連結），其餘一律跳脫
        return f'<br><b>{gettext(label)}</b>{sep}{val if raw else _v(val)}'

    query = ''
    if sd.get('record_type') == 'occ':
        query += f'<b>{gettext("類別")}</b>{sep}{gettext("物種出現紀錄")}'
        map_dict = map_occurrence
    else:
        map_dict = map_collection
        query += f'<b>{gettext("類別")}</b>{sep}{gettext("自然史典藏")}'

    d_list, r_list, l_list = [], [], []

    if sd.get('current_grid_level') in map_dict.keys() and sd.get('current_grid'):
        query += line(map_dict[sd['current_grid_level']], sd.get('current_grid'))

    for k in sd.keys():
        vals = sd.getlist(k)
        if k == 'name':
            query += line('學名/中文名/中文別名/同物異名/誤用名', sd.get(k))
        elif k == 'taxonRank':
            v = sd.get(k)
            text = gettext('種下') if v == 'Infraspecies' else gettext(map_dict.get(v.lower(), v))
            query += line(map_dict['taxonRank'], text)
        elif k == 'tbiaDatasetID':
            d_list = [n for n in (get_dataset_name(d) for d in vals) if n]
        elif k == 'sourceDatabase':
            r_list = vals
        elif k == 'locality':
            l_list = vals
        elif k == 'higherTaxonID':
            response = requests.get(f'{SOLR_PREFIX}taxa/select', params={'q': f'id:{solr_quote(sd.get(k))}'}, timeout=SOLR_TIMEOUT)
            if response.status_code == 200 and (data := response.json()['response']['docs']):
                data = data[0]
                query += line(map_dict['higherTaxa'], f"{data.get('scientificName')} {data.get('common_name_c') or ''}")
        elif k == 'taxonGroupByHabitat':
            query += line(map_dict['habitat'], '、'.join(gettext(habitat_map[HABITAT_PARAM[v]]) for v in vals if v in HABITAT_PARAM))
        elif k == 'taxonGroup':
            display_vals = [taxon_group_map_e.get(v, v) for v in vals] if lang == 'en-us' else vals
            query += line(map_dict['taxonGroup'], '、'.join(display_vals))
        elif k == 'nativeness':
            query += line('原生性', '、'.join(gettext(NATIVENESS_LABELS.get(v, v)) for v in vals))
        elif k == 'protectedStatus':
            query += line('保育類等級', '、'.join(gettext(PROTECTED_STATUS_LABELS.get(v, v)) for v in vals))
        elif k == 'typeStatus':
            query += line('標本類型', '、'.join(gettext(TYPE_STATUS_LABELS.get(v, v)) for v in vals))
        elif k == 'hasMedia':
            media = sd.getlist('mediaType') or [sd.get(k)]
            query += line('有無多媒體', '、'.join(gettext(MEDIA_LABELS.get(v, v)) for v in media))
        elif k == 'eventDate':
            if r := parse_range(sd.get(k)):
                if r[0]:
                    query += line('起始日期', _ymd(r[0]))
                if r[1]:
                    query += line('結束日期', _ymd(r[1]))
        elif k == 'circle':
            if c := parse_circle(sd.get(k)):
                lon, lat, rad = sd.get(k).split(',')
                query += line('圓中心框選', f"{gettext('半徑')} {rad} KM {gettext('中心點經度')} {lon} {gettext('中心點緯度')} {lat}")
        elif k == 'polygon':
            query += line('地圖框選', '; '.join(vals))
        elif k == 'geojson_id':
            geojson_path = f"media/geojson/{sd.get(k)}.json"
            if exists(os.path.join('/tbia-volumes/', geojson_path)):
                query += line('上傳Polygon', f"<a target='_blank' href='/{_v(geojson_path)}'>{gettext('點此下載GeoJSON')}</a>", raw=True)
        elif k in ('mediaType', 'record_type', 'current_grid_level', 'current_grid'):
            continue
        elif label := param_label(k, map_dict):
            if k in ['basisOfRecord', 'dataGeneralizations']:
                query += line(label, gettext(sd.get(k)))
            else:
                query += line(label, sd.get(k))
    if r_list:
        query += line('來源資料庫', '、'.join(gettext(r) for r in r_list))
    if d_list:
        query += line('資料集名稱', '、'.join(d_list))
    if l_list:
        query += line(map_dict['locality'], '、'.join(l_list))
    for r in removed:
        query += f"<br><b>{_v(gettext(r))}</b> <span class=\"color-silver\">（{gettext('已停用')}）</span>"
    for n in notes:
        query += f"<br><small class=\"color-silver\">※ {_v(gettext(n))}</small>"
    return query


# [COMPAT-KEEP] 搜尋參數正規化（3.4，D20）：舊網址、再次查詢連結、書籤、已存查詢帶的舊參數名 / 舊值轉成 v2 標準形式
# 規則在 data/search_params.py；網頁入口（搜尋頁、AJAX 查詢）、parse_query_string、create_search_query 都經過這裡，可重複呼叫
def normalize_search_params(query_dict):
    """回傳新的 QueryDict（可修改），另帶兩個屬性：
       removed：已停止提供、被自動移除的條件說明；notes：轉換後結果可能略有不同的提示（都是中文，顯示時再 gettext）"""
    pairs, removed, notes = normalize_pairs(_mapping_pairs(query_dict))
    qd = QueryDict('', mutable=True)
    for k, v in pairs:
        qd.appendlist(k, v)
    qd.removed, qd.notes = removed, notes
    return qd


def canonical_query_string(mapping):
    """存進資料庫的查詢字串（下載、敏感申請、網站搜尋紀錄）：v2 標準形式＋只留查詢條件（白名單）。
       分頁、排序、表單欄位、追蹤參數、掃描工具亂填的參數與不合法的值都不會存進去"""
    pairs, _, _ = canonical_pairs(_mapping_pairs(mapping))
    return urlencode(pairs)


def search_notices(qd):
    """搜尋頁 / 後台顯示用：已停用條件與轉換提示（已翻譯）"""
    out = []
    if removed := getattr(qd, 'removed', None):
        out.append(gettext('以下篩選條件已停止提供，已自動移除：') + '、'.join(gettext(r) for r in removed))
    for n in getattr(qd, 'notes', None) or []:
        out.append(gettext(n))
    return out


def search_again_url(raw_query, search_dict, search_prefix):
    """「再次查詢」連結。條件有被停用（search_dict.removed）時連原始字串，
       讓搜尋頁轉址成 v2 並跳出「已停止提供」提示；否則直接給 v2 網址"""
    if getattr(search_dict, 'removed', None):
        return f'/search/{search_prefix}?{raw_query}'
    tmp_a = create_query_a(search_dict)
    rest = search_dict.copy()
    rest.pop('taxonGroup', None)          # 已由 tmp_a 正規化輸出，避免重複
    return f'/search/{search_prefix}?' + build_query_string(rest) + tmp_a


def create_query_a(search_dict):
    """只負責 taxonGroup 舊→新群名正規化(前端不處理這塊)。
       其餘多值參數由 build_query_string 產生。"""
    query_a = ''
    for v in get_multi(search_dict, 'taxonGroup'):
        if v in split_group_map:
            for mapped in split_group_map[v]:
                query_a += f'&taxonGroup={mapped}'
        elif v in taxon_group_map_c:
            query_a += f'&taxonGroup={taxon_group_map_c[v]}'
        elif v in old_taxon_group_map_c:
            query_a += f'&taxonGroup={old_taxon_group_map_c[v]}'
        else:
            query_a += f'&taxonGroup={v}'
    return query_a


def query_a_href(query, query_a, lang=None):
    if lang:
        translation.activate(lang)
    query += f'''<br><a class="search-again-a" target="_blank" href="{html.escape(query_a)}">{gettext('再次查詢')}<svg class="search-again-icon" xmlns="http://www.w3.org/2000/svg" width="25" height="25" viewBox="0 0 25 25"><g id="loupe" transform="translate(0 -0.003)"><g id="Group_13" data-name="Group 13" transform="translate(0 0.003)"><path id="Path_54" data-name="Path 54" d="M24.695,23.225l-7.109-7.109a9.915,9.915,0,1,0-1.473,1.473L23.222,24.7a1.041,1.041,0,1,0,1.473-1.473ZM9.9,17.711A7.812,7.812,0,1,1,17.708,9.9,7.821,7.821,0,0,1,9.9,17.711Z" transform="translate(0 -0.003)" fill="#3f5146"></path></g></g></svg></a>'''
    return query


def return_selected_grid_text(req_dict,map_dict):

    string = ''
    if req_dict.get('current_grid_level') in ['grid_1','grid_10','grid_100','grid_5'] and req_dict.get('current_grid'):
        string = f'''{gettext(map_dict[req_dict["current_grid_level"]])} {req_dict.get('current_grid')}'''
    return string


# 已經預先存好的req_dict, getlist改為get
# generate_sensitive_csv (v), transfer_sensitive_response (v), submit_sensitive_request(v)

# 直接從form傳過來的req_dict, 使用getlist
# datasetName, rightsHolder, locality, polygon
# , generate_download_csv, generate_species_csv(v), get_map_grid(v), get_conditional_records(v)

def merge_polygons(g_list):
    """多個 WKT（POLYGON / MULTIPOLYGON）攤平後取聯集，回傳 Polygon 或 MultiPolygon"""
    polys = []
    for g in g_list:
        geom = wkt.loads(g)
        if geom.geom_type == 'MultiPolygon':
            polys.extend(geom.geoms)
        elif geom.geom_type == 'Polygon':
            polys.append(geom)
        else:
            raise ValueError(f'unsupported geometry: {geom.geom_type}')
    return unary_union(polys)


def create_search_query(req_dict, get_raw_map=False):
    """網站搜尋條件 → Solr filter 清單。參數為 v2 標準形式（3.4）；舊參數名 / 舊值在這裡先轉換（normalize 可重複呼叫）"""
    req_dict = normalize_search_params(req_dict)
    query_list = []

    # 多媒體：hasMedia=true/false，mediaType 限定類型（可多個，聯集；需 hasMedia=true）
    has_media = req_dict.get('hasMedia')
    if has_media == 'false':
        query_list += ['-associatedMedia:*']
    elif has_media == 'true':
        if media_types := req_dict.getlist('mediaType'):
            query_list += [f'associatedMediaType:({" OR ".join(media_types)})']
        else:
            query_list += ['associatedMedia:*']

    # 原生性
    if vals := req_dict.getlist('nativeness'):
        query_list += [f'alien_type:({" OR ".join(vals)})']

    # 保育類等級：CHPA 過渡期同時對應 taxa core 的舊值 1（D12）
    if vals := req_dict.getlist('protectedStatus'):
        vals = vals + ['1'] if 'CHPA' in vals else vals
        query_list += [f'protected:({" OR ".join(solr_quote(v) for v in vals)})']

    if req_dict.get('record_type') == 'col':  # occurrence include occurrence + collection
        query_list += ['recordType:col']

    if bio_groups := req_dict.getlist('taxonGroup'):
        query_list += [f'taxonGroup:({" OR ".join(solr_quote(g) for g in bio_groups)})']

    if habitat_vals := [HABITAT_PARAM[v] for v in req_dict.getlist('taxonGroupByHabitat') if v in HABITAT_PARAM]:
        query_list += [f'({" OR ".join([f"{v}:true" for v in habitat_vals])})']

    for i in ['recordedBy', 'resourceContacts', 'preparations']:
        if val := req_dict.get(i):
            if val != 'undefined':
                val = val.strip()
                val = html.unescape(val)
                keyword_reg = build_keyword_reg(val)
                keyword_reg = process_text_variants(keyword_reg)
                query_list += [contains_clause(i, val, keyword_reg)]

    for i in ['taxonID', 'occurrenceID', 'catalogNumber', 'recordNumber']:
        if val := req_dict.get(i):
            query_list += [f'{i}:{solr_quote(val)}']

    # 這邊會不會有模糊化的問題
    if req_dict.get('current_grid_level') in ['grid_1','grid_10','grid_100','grid_5'] and req_dict.get('current_grid'):
        query_list += [f"{req_dict.get('current_grid_level')}:{solr_quote(req_dict.get('current_grid'))}"]

    # higherTaxonID：該分類群本身及其下所有子分類群
    # 11/20：taxa core 查不到時查無資料（原本不加條件，等於回傳全部資料）；taxa core 錯誤直接丟例外，不靜默放寬條件
    if val := req_dict.get('higherTaxonID'):
        response = requests.get(f'{SOLR_PREFIX}taxa/select', params={'q': f'id:{solr_quote(val)}'}, timeout=SOLR_TIMEOUT)
        response.raise_for_status()
        if data := response.json()['response']['docs']:
            data = data[0]
            higher_rank = data.get('taxonRank')
            higher_name = data.get('scientificName')
            query_list += [f'({higher_rank}:{solr_quote(higher_name)} OR taxonID:{solr_quote(val)})']
        else:
            query_list += ['-*:*']

    if quantity := req_dict.get('organismQuantity'):
        try:
            float(quantity)  # 前端是 number 欄位；非數字忽略
            query_list += [f'organismQuantity:{solr_quote(quantity.strip())}']
        except ValueError:
            pass

    # typeStatus：控制詞彙；Solr 多值以 | 串在同一個字串（D23），用 regex 比對其中一段
    if vals := [v for v in req_dict.getlist('typeStatus') if v in TYPE_STATUS]:
        query_list += ['(' + ' OR '.join(f'typeStatus:/(.*\\|)?{v}(\\|.*)?/' for v in vals) + ')']

    if val := req_dict.get('basisOfRecord'):
        if val in basis_map.keys():
            query_list += [f'basisOfRecord:{val}']

    if val := req_dict.get('sensitiveCategory'):
        if val == '無':
            query_list += [f'-(-sensitiveCategory:{val} sensitiveCategory:*)']
        else:
            query_list += [f'sensitiveCategory:{solr_quote(val)}']

    # taxonRank：v2 值首字大寫，Solr 維持 TaiCOL 小寫（D26）
    if val := req_dict.get('taxonRank'):
        if val == 'Infraspecies':
            query_list += [f'taxonRank:({" OR ".join(INFRASPECIES_RANKS)})']
        else:
            query_list += [f'taxonRank:{solr_quote(val.lower())}']

    # 資料集（值為 tbiaDatasetID；舊的數字 id 由 get_tbia_dataset_id 轉換）
    # 11/20：有帶資料集但全部對不到時查無資料（原本不加條件，等於回傳全部資料）
    if d_vals := req_dict.getlist('tbiaDatasetID'):
        d_list = [d_id for d_id in (get_tbia_dataset_id(v) for v in d_vals) if d_id]
        if d_list:
            query_list += [f'tbiaDatasetID:({" OR ".join(solr_quote(d) for d in d_list)})']
        else:
            query_list += ['-*:*']

    if r_list := req_dict.getlist('sourceDatabase'):
        query_list += [f'sourceDatabase:({" OR ".join(solr_quote(r) for r in r_list)})']

    if l_list := req_dict.getlist('locality'):
        query_list += [f'locality:({" OR ".join(solr_quote(l) for l in l_list)})']

    # eventDate：YYYYMMDD 或區間（一邊可為 *），以日期為粒度
    if r := parse_range(req_dict.get('eventDate')):
        start = f'{r[0][:4]}-{r[0][4:6]}-{r[0][6:]}T00:00:00Z' if r[0] else '*'
        end = f'{r[1][:4]}-{r[1][4:6]}-{r[1][6:]}T23:59:59Z' if r[1] else '*'
        query_list += [f'standardDate:[{start} TO {end}]']

    #  要處理敏感資料
    if county := req_dict.get('county'):
        if get_raw_map:
            query_list += [f'county:{solr_quote(county)} OR rawCounty:{solr_quote(county)}']
        else:
            query_list += [f'county:{solr_quote(county)}']

    if municipality := req_dict.get('municipality'):
        if get_raw_map:
            query_list += [f'municipality:{solr_quote(municipality)} OR rawMunicipality:{solr_quote(municipality)}']
        else:
            query_list += [f'municipality:{solr_quote(municipality)}']

    # 地圖框選（可多個 polygon）：資料皆為點位，使用 Intersects，落在邊線上的點也符合（共同規格要求包含邊界）
    if g_list := req_dict.getlist('polygon'):
        try:
            mp = merge_polygons(g_list)
            if get_raw_map:
                query_list += ['{!cache=false}location_rpt: "Intersects(%s)" OR raw_location_rpt: "Intersects(%s)" ' % (mp, mp)]
            else:
                query_list += ['{!cache=false}location_rpt: "Intersects(%s)"' % mp]
        except:
            pass

    # 上傳polygon：geojson_id 會組成檔案路徑，只接受英數、底線、連字號（normalize 已檢查），避免路徑穿越
    if (g_id := req_dict.get('geojson_id')) and re.fullmatch(r'[\w-]+', g_id):
        try:
            with open(f'/tbia-volumes/media/geojson/{g_id}.json', 'r') as j:
                geojson = json.loads(j.read())
                geo_df = gpd.GeoDataFrame.from_features(geojson)
                g_list = []
                for i in geo_df.to_wkt()['geometry']:
                    g_list += ['"Intersects(%s)"' % i]
                if get_raw_map:
                    query_list += [ f"{{!cache=false}}location_rpt: ({' OR '.join(g_list)}) OR raw_location_rpt: ({' OR '.join(g_list)})" ]
                else:
                    query_list += [ f"{{!cache=false}}location_rpt: ({' OR '.join(g_list)})" ]
        except:
            pass

    # 圓形範圍：circle=經度,緯度,半徑（公里，0 < 半徑 ≤ CIRCLE_MAX_KM）
    if c := parse_circle(req_dict.get('circle')):
        lon, lat, radius = c
        query_list += ['{!geofilt cache=false pt=%s,%s sfield=location_rpt d=%s}' % (lat, lon, radius)]

    # 學名相關
    if val := req_dict.get('name'):
        val = val.strip()
        # 去除重複空格
        val = re.sub(' +', ' ', val)
        # 去除頭尾空格
        val = val.strip()
        val = html.unescape(val)
        keyword_reg = build_keyword_reg(val)
        keyword_reg = process_text_variants(keyword_reg)
        col_list = [ contains_clause(i, val, keyword_reg) for i in name_search_col ]
        query_str = ' OR '.join( col_list )
        query_list += [ '(' + query_str + ')' ]

    # group (後台儀表板的query)
    if group := req_dict.get('group'):
        if group != 'total':
            query_list += [f'group:{solr_quote(group)}']

    # rights_holder (後台儀表板的query)
    if rights_holder := req_dict.get('rights_holder'):
        if rights_holder != 'total':
            query_list += [f'sourceDatabase:{solr_quote(to_source_database(rights_holder))}']

    return query_list


def summarize_names(names, keyword, keyword_reg, limit=2, do_highlight=True):
    """
    names: 逗號分隔的名稱字串（可含 <i> 等 HTML 標籤）
    最多顯示 limit 個，有對到關鍵字的優先，超過則加 '...'
    """
    if not names:
        return names
    regexp = re.compile(keyword_reg)
    items = [n.strip() for n in names.split(',') if n.strip()]
    # 去除 HTML 標籤再比對
    matched = [n for n in items if regexp.search(re.sub(r'<[^>]+>', '', n))]
    others = [n for n in items if n not in matched]
    result = ', '.join((matched + others)[:limit])
    if len(items) > limit:
        result += '...'
    return highlight(result, keyword, '1') if do_highlight else result


# 全站搜尋 物種出現紀錄 / 自然史典藏
def get_search_full_counts(keyword, lang=None, is_first_time=False):
    """全站搜尋頁面用：一次 Solr 請求同時算出 occ 與 col 的總數與側欄，回傳 (occ_resp, col_resp)。
    結果與 get_search_full_cards(counts_only=True) 分別對 .occ / .col 相同。
    兩者的欄位子句完全相同（col 只多 recordType:col），合併後冷啟動只需讀一次 postings，也不會互搶 IO。"""
    if lang:
        translation.activate(lang)

    keyword = keyword.strip()
    # 與 get_search_full_cards 相同的日期判斷
    if re.match(r'^([\s\d]+)$', keyword):
        enable_query_date = False
    elif re.match(r'^[0-9-]*$', keyword):
        try:
            datetime.strptime(keyword, '%Y-%m-%d')
            enable_query_date = True
        except:
            enable_query_date = False
    else:
        enable_query_date = True

    keyword = html.unescape(keyword)
    keyword_name = re.sub(' +', ' ', keyword)

    fields = {}
    for rt in ['occ', 'col']:
        fields[rt] = [f for f in create_facet_list(record_type=rt)['facet'] if enable_query_date or f != 'verbatimEventDate']

    clauses = {}
    for f in fields['occ'] + fields['col']:
        if f not in clauses:
            clauses[f] = ngram_contains_query(f, keyword_name if f in taxon_keyword_list else keyword)

    union = {rt: ' OR '.join(f'filter({clauses[f]})' for f in fields[rt]) for rt in fields}
    col_fq = 'filter(recordType:col)'
    facet = {
        'occ_total': {'type': 'query', 'q': union['occ']},
        'col_total': {'type': 'query', 'q': f"+{col_fq} +({union['col']})"},
    }
    for f in fields['occ']:
        facet[f'occ__{f}'] = {'type': 'query', 'q': f'filter({clauses[f]})'}
    for f in fields['col']:
        facet[f'col__{f}'] = {'type': 'query', 'q': f'+{col_fq} +filter({clauses[f]})'}

    query = {
        "query": '*:*',
        "limit": 0,
        "filter": [' OR '.join(f'filter({c})' for c in clauses.values())],
        "facet": facet,
    }
    resp = requests.post(RECORDS_URL, data=json.dumps(query), headers={'content-type': "application/json" }, timeout=SOLR_TIMEOUT).json()
    cf = resp.get('facets', {})

    if is_first_time:
        query_string = urlencode({'keyword': keyword})
        run_light(background_search_stat, union['occ'], 'full', query_string)

    def build(rt, map_dict):
        return {
            'total_count': cf.get(f'{rt}_total', {}).get('count', 0),
            'menu_rows': [{'title': map_dict[f], 'total_count': cf[f'{rt}__{f}']['count'], 'key': f}
                          for f in fields[rt] if cf.get(f'{rt}__{f}', {}).get('count', 0) > 0],
            'data': [],
            'has_more': False,
            'reach_end': False,
            'item_class': None,
            'card_class': None,
            'title': None,
        }

    return build('occ', map_occurrence), build('col', map_collection)


def get_search_full_cards(keyword, card_class, is_sub, offset, key, lang=None, is_first_time=False, counts_only=False, hit_fields=None):
    if lang:
        translation.activate(lang)

    keyword = keyword.strip()

    if re.match(r'^([\s\d]+)$', keyword):
        # 純數字
        enable_query_date = False
    elif re.match(r'^[0-9-]*$', keyword):
        # 數字和-的組合 一定要符合日期格式才行
        try:
            datetime.strptime(keyword, '%Y-%m-%d')
            enable_query_date = True
        except:
            enable_query_date = False
    else:
        enable_query_date = True

    query_list = []

    query = {
        "query": '*:*',
        "limit": 0,
        "facet": {},
        "sort":  "scientificName asc"
    }

    q = ''
    keyword = html.unescape(keyword)
    keyword_reg = build_keyword_reg(keyword)
    keyword_reg = process_text_variants(keyword_reg)

    # 查詢學名相關欄位時 去除重複空格
    keyword_name = re.sub(' +', ' ', keyword)
    keyword_name_reg = build_keyword_reg(keyword_name)
    keyword_name_reg = process_text_variants(keyword_name_reg)

    if card_class.startswith('.col'):
        map_dict = map_collection
        record_type = 'col'
        title_prefix = f'{gettext("自然史典藏")} > '
        query_list.append('recordType:col')
    else: # taxon 跟 occ 都算在這裡
        map_dict = map_occurrence
        query.pop('filter', None)
        record_type = 'occ'
        title_prefix = f'{gettext("物種出現紀錄")} > '

    facet_list = create_facet_list(record_type=record_type)

    if not enable_query_date:
        if 'verbatimEventDate' in facet_list['facet'].keys():
            facet_list['facet'].pop('verbatimEventDate')

    # 是否為特定facet卡片底下的
    if is_sub == 'true':
        facet_list = {'facet': {k: v for k, v in facet_list['facet'].items() if k == key} }

    clauses = {}
    for i in facet_list['facet']:
        kw = keyword_name if i in taxon_keyword_list else keyword
        clauses[i] = ngram_contains_query(i, kw)

    # 每個子句用 filter() 包住：各自進 filterCache，facet domain 用同一字串可直接命中，不必再讀一次
    q = ' OR '.join(f'filter({c})' for c in clauses.values())

    query.update(facet_list)
    query_list.append(q)
    query['filter'] = query_list

    # 前端已知命中欄位（側欄）時跳過第一階段；只接受本次欄位清單內的 key，順序依原本欄位順序
    if hit_fields is not None and is_sub != 'true' and not counts_only:
        hit_set = set(hit_fields)
        hit_fields = [i for i in clauses if i in hit_set]
    else:
        hit_fields = None

    # 第一階段：只算各欄位命中數（query facet，子句已在 filterCache）
    count_query = {
        "query": '*:*',
        "limit": 0,
        "filter": query_list,
        "facet": {i: {'type': 'query', 'q': c} for i, c in clauses.items()},
    }
    total_count = 0
    if hit_fields is None:
        resp1 = requests.post(RECORDS_URL, data=json.dumps(count_query), headers={'content-type': "application/json" }, timeout=SOLR_TIMEOUT).json()
        total_count = resp1['response']['numFound']
        count_facets = resp1.get('facets', {})
        hit_fields = [i for i in clauses if count_facets.get(i, {}).get('count', 0) > 0]

    # 只要總數與側欄：頁面先出，卡片由前端另外呼叫 get_more_cards 載入
    # 欄位皆為單值 string，query facet 的 count 等於原本 terms facet 的 allBuckets count
    if counts_only:
        if is_first_time:
            query_string = urlencode({'keyword': keyword})
            run_light(background_search_stat, q,'full',query_string)
        return {
            'total_count': total_count,
            'menu_rows': [{'title': map_dict[i], 'total_count': count_facets[i]['count'], 'key': i} for i in hit_fields],
            'data': [],
            'has_more': False,
            'reach_end': False,
            'item_class': None,
            'card_class': None,
            'title': None,
        }

    # 第二階段：只對有命中的欄位做 terms facet（順序維持原本；沒命中的欄位原本也不會產生任何結果）
    facets = {}
    if hit_fields:
        for i in hit_fields:
            domain = {'query': clauses[i]}
            if card_class.startswith('.col'):
                domain['filter'] = ['recordType:col']
            facet_list['facet'][i].update({'domain': domain})
        query['facet'] = {i: facet_list['facet'][i] for i in hit_fields}
        response = requests.post(RECORDS_URL, data=json.dumps(query), headers={'content-type': "application/json" }, timeout=SOLR_TIMEOUT)
        facets = response.json()['facets']
        facets.pop('count', None)
        # 第二階段用同一組主 filter，numFound 即總數（跳過第一階段時由此取得）
        total_count = response.json()['response']['numFound']
    if is_first_time:
        # 背景處理stat：移到主查詢之後才啟動，避免和卡片查詢搶 Solr / 磁碟 IO
        query_string = urlencode({'keyword': keyword})

        run_light(background_search_stat, q,'full',query_string)


    menu_rows = [] # 側邊欄
    result = [] # 卡片
    has_more = False

    # 2023/11/20前 如果是對到高階層的話，存parentTaxonID，會有taxonID是空值，但其實有對到高階層的情況，產生bug
    # 目前全部改存taxonID

    seen = set()  # 去重：(val, count, matched_value, matched_col)，取代逐筆 list 比對

    def add_result(val, count, matched_value, matched_col):
        k_ = (val, count, matched_value, matched_col)
        if k_ not in seen:
            seen.add(k_)
            result.append({'val': val, 'count': count, 'matched_value': matched_value, 'matched_col': matched_col})

    for i in facets:
        x = facets[i]
        if x['allBuckets']['count']:
            menu_rows.append({
                'title': map_dict[i],
                'total_count': x['allBuckets']['count'],
                'key': i
            })
        for k in x['buckets']:
            bucket = k['taxonID']['buckets']
            if bucket:
                if i == 'verbatimEventDate':
                    if f_date := convert_date(k['val']):
                        f_date = f_date.strftime('%Y-%m-%d %H:%M:%S')
                        for item in bucket:
                            add_result(item['val'], item['count'], f_date, i)
                else:
                    for item in bucket:
                        add_result(item['val'], item['count'], k['val'], i)
            elif not bucket and k['count']:
                add_result('', k['count'], k['val'], i)

    # 卡片
    result_df = pd.DataFrame(result)
    res_c = 0
    result_dict_all = []

    if len(result_df):
        # 每個 taxonID 只切一次（保留原本列順序），取代每輪對整張表重新篩選
        source_cols = SOURCE_NAME_FIELDS
        is_taxon = result_df.matched_col.isin(taxon_facets)
        is_source = result_df.matched_col.isin(source_cols)
        groups = {t: g.index for t, g in result_df.groupby('val', sort=False)}
        for t in result_df.val.unique():
            g_idx = groups[t]
            taxon_idx = g_idx[is_taxon[g_idx].values]
            # 若是taxon-related的算在同一張
            rows = []
            if len(taxon_idx):
                if res_c in range(offset,offset+9):
                    rows = result_df.loc[taxon_idx]
                    matched = []
                    for ii in rows.index:
                        match_val = result_df.loc[ii].matched_value
                        # 改成後面一起處理
                        matched.append({'key': result_df.loc[ii].matched_col, 
                                        'matched_col': map_dict[result_df.loc[ii].matched_col], 
                                        'matched_value_ori': match_val,
                                        'matched_value': highlight(match_val,keyword,'1'),
                                        })
                    result_dict_all.append({
                        'val': t,
                        'count': result_df.loc[taxon_idx]['count'].values[0],
                        'matched': matched,
                        'match_type': 'taxon-related'
                    })
                res_c += 1
            # 如果沒有任何taxon-related的對到，則顯示來源資料庫使用的名稱
            else: # 內容不一樣 要拆成不同卡片
                rows = result_df.loc[g_idx[is_source[g_idx].values]]
                for ii in rows.index:
                    if res_c in range(offset,offset+9):
                        matched = [{'key': result_df.loc[ii].matched_col, 
                                    'matched_col': map_dict[result_df.loc[ii].matched_col], 
                                    'matched_value_ori': result_df.loc[ii].matched_value,
                                    'matched_value': highlight(result_df.loc[ii].matched_value,keyword,'1'),
                                    }]
                        result_dict_all.append({
                            'val': t,
                            'count': result_df.loc[ii]['count'],
                            'matched': matched,
                            'match_type': 'non-taxon-related'
                        })
                    res_c += 1
            for ii in g_idx[~(is_taxon[g_idx].values | is_source[g_idx].values)]:
                if res_c in range(offset,offset+9):
                    matched= [{'key': result_df.loc[ii].matched_col,
                                'matched_col': map_dict[result_df.loc[ii].matched_col], 
                                'matched_value_ori': result_df.loc[ii].matched_value,
                                'matched_value': highlight(result_df.loc[ii].matched_value,keyword),
                                }]
                    result_dict_all.append({
                        'val': result_df.loc[ii].val,
                        'count': result_df.loc[ii]['count'],
                        'matched': matched,
                        'match_type': 'non-taxon-related'
                    })
                res_c += 1
            if offset >= 27:
                if res_c > offset+3:
                    has_more = True
                    break
            else:
                if res_c > offset+9:
                    has_more = True
                    break

        if offset >= 27:
            result_df = pd.DataFrame(result_dict_all[:3])
        else:
            result_df = pd.DataFrame(result_dict_all[:9])

        # s = time.time()
        result_df = result_df.replace({None:'', np.nan: ''}) 
        taicol = pd.DataFrame()
        if len(result_df):
            taxon_ids = [f"id:{d}" for d in result_df[result_df.val!=''].val.unique()]
            response = requests.get(f'{SOLR_PREFIX}taxa/select?q={" OR ".join(taxon_ids)}&fl=common_name_c,formatted_name,id,scientificName,taxonRank,formatted_misapplied,formatted_synonyms', timeout=SOLR_TIMEOUT)
            if response.status_code == 200:
                resp = response.json()
                if data := resp['response']['docs']:
                    taicol = pd.DataFrame(data)
                    used_cols = ['common_name_c','formatted_name','id','scientificName','taxonRank', 'formatted_misapplied', 'formatted_synonyms']
                    for u in used_cols:
                        if u not in taicol.keys():
                            taicol[u] = ''
                    taicol = taicol[used_cols]
                    # taxa core 舊名 → v2（common_name_c → vernacularName）
                    taicol = taicol.rename(columns={'scientificName': 'name', 'id': 'taxonID', 'common_name_c': 'vernacularName'})
            if len(taicol):
                result_df = pd.merge(result_df,taicol,left_on='val',right_on='taxonID', how='left')
                result_df = result_df.replace({np.nan:'', None:''})
                result_df['taxonRank'] = result_df['taxonRank'].apply(lambda x: map_dict[x] if x else x)
                # 如果match_col是synonyms & misapplied 要修改
            else:
                result_df['vernacularName'] = ''
                result_df['formatted_name'] = ''
                result_df['taxonID'] = ''
                result_df['name'] = ''
                result_df['taxonRank'] = ''
            result_df['val'] = result_df['formatted_name']
            if (is_sub != 'true') or (is_sub == 'true' and key == 'scientificName'):
                result_df['val'] = result_df['val'].apply(lambda x: highlight(x, keyword,'1'))
            if (is_sub != 'true') or (is_sub == 'true' and key == 'vernacularName'):
                result_df['vernacularName'] = result_df['vernacularName'].apply(lambda x: highlight(x, keyword,'1'))
            result_df = result_df.replace({np.nan:'', None:''})
            result_df = result_df.drop(columns=['formatted_name'],errors='ignore')

    # get_focus_card 使用
    if key:
        title = f"{title_prefix}{gettext(map_dict[key])}"
        item_class = f"item_{record_type}_{key}"
        card_class = f"{record_type}-{key}-card"
    else:
        title = None
        item_class = None
        card_class = None

    data = []

    for rr in result_df.to_dict('records'):
        matches = rr.get('matched')
        new_matches = []
        for mm in matches:
            tmp_m = mm
            if mm.get('key') in ['synonyms', 'misapplied']:
                if f"formatted_{mm.get('key')}" in taicol.keys():
                    new_value = taicol[taicol.taxonID==rr.get('taxonID')][f"formatted_{mm.get('key')}"].values[0]
                    new_value = summarize_names(new_value, keyword, keyword_name_reg)
                    tmp_m.update({'matched_value': new_value})
            new_matches.append(tmp_m)
        rr.update({'matched': new_matches})
        data += [rr]

    response = {
        'total_count': total_count, # 總數
        'menu_rows': menu_rows, # 側邊欄
        'data': data, # 卡片
        'has_more': has_more,
        'reach_end': True if offset >= 27 else False,
        'item_class': item_class,
        'card_class': card_class,
        'title': title,
    }

    return response


# 全站搜尋 物種
def get_search_full_cards_taxon(keyword, card_class, is_sub, offset, lang=None, taxon_rank=''):
    if lang:
        translation.activate(lang)

    taxon_result_dict = []
    offset = int(offset) if offset else offset
    # key 是前端用的 v2 名稱；查 taxa core 時換回舊名（D21）
    if card_class and card_class != '.taxon-card':
        key = card_class.split('-')[1]
    else:
        key = None
    taxa_key = to_taxa_field(key) if key else None

    taxon_facet_list = create_taxon_facet_list()

    keyword = html.unescape(keyword)
    keyword_reg = build_keyword_reg(keyword)
    keyword_reg = process_text_variants(keyword_reg)

    # 查詢學名相關欄位時 去除重複空格
    keyword_name = re.sub(' +', ' ', keyword)
    keyword_name_reg = build_keyword_reg(keyword_name)
    keyword_name_reg = process_text_variants(keyword_name_reg)
    
    if is_sub == 'true':
        taxon_facet_list = {'facet': {k: v for k, v in taxon_facet_list['facet'].items() if k == taxa_key} }

    taxon_q = ''
    rank_fq = get_taxon_rank_fq(taxon_rank)

    for i in taxon_facet_list['facet']:
        ngram_q = ngram_contains_query(i, keyword_name)
        boost = "^3 AND (is_in_taiwan:1^1 or is_in_taiwan:*)" if i in ["scientificName", "common_name_c", "alternative_name_c"] else ""
        facet_taxon_query = f'{ngram_q} OR ({i}:/{keyword_name_reg}/{boost}) '
        taxon_q += f'{ngram_q} OR '
        taxon_q += f'({i}:/{keyword_name_reg}/{boost} ) OR '
        taxon_facet_list['facet'][i].update({'domain': { 'query': facet_taxon_query}})

    taxon_q = taxon_q[:-4]

    query = {}
    query['query'] = taxon_q
    if rank_fq:
        query['filter'] = [rank_fq]
    query['limit'] = 4 if offset < 28 else 2
    query['offset'] = offset
    query['facet'] = taxon_facet_list['facet']

    response = requests.post(f'{SOLR_PREFIX}taxa/select', data=json.dumps(query), headers={'content-type': "application/json" }, timeout=SOLR_TIMEOUT)
    facets = response.json()['facets']
    facets.pop('count', None)
    data = response.json()['response']

    total_count = data['numFound']
    if total_count:
        taicol = pd.DataFrame(data['docs'])
        taicol_cols = [c for c in ['common_name_c', 'alternative_name_c', 'synonyms', 'formatted_name', 'id', 'taxon_name_id','taxonRank', 'formatted_misapplied', 'formatted_synonyms'] if c in taicol.keys()]
        taicol = taicol[taicol_cols]
        taicol = taicol.rename(columns={'scientificName': 'name', 'id': 'taxonID', 'common_name_c': 'vernacularName'})

    # 側邊欄
    menu_rows = []
    for i in facets:
        x = facets[i]
        if x['allBuckets']['count']:
            menu_rows.append({
                'title': map_collection[to_record_field(i)],
                'total_count': x['allBuckets']['count'],
                'key': to_record_field(i)
            })

    taxon_result = []
    regexp = re.compile(keyword_name_reg)
    for d in data['docs']:
        for k in taxon_facet_list['facet'].keys():
            if d.get(k):
                if regexp.search(d.get(k)):
                    taxon_result.append({
                        'val': d.get('id'),
                        'matched_value': d.get(k),
                        'matched_col': k,
                    })

    # 物種整理
    taxon_result_df = pd.DataFrame(taxon_result)
    taxon_result_dict_all = []

    if len(taxon_result_df):
        for tt in taxon_result_df.val.unique(): ## tt = taxonID
            rows = []
            if len(taxon_result_df[(taxon_result_df.val==tt)]):
                # tt_c += 1
                rows = taxon_result_df[(taxon_result_df.val==tt)]
                matched = []
                for ii in rows.index:
                    match_val = taxon_result_df.loc[ii].matched_value
                    match_col = taxon_result_df.loc[ii].matched_col
                    if match_col in ['synonyms','misapplied']:
                        if f'formatted_{match_col}' in taicol.keys():
                            if len(taicol[taicol.taxonID==tt]):
                                match_val = taicol.loc[taicol.taxonID==tt][f'formatted_{match_col}'].values[0]
                        if match_val:
                            match_val = (', ').join(match_val.split(','))
                    matched.append({'key': to_record_field(match_col), 'matched_col': map_collection[to_record_field(match_col)], 'matched_value': match_val})
                taxon_result_dict_all.append({
                    'val': tt,
                    'matched': matched,
                })

    taxon_result_df = pd.DataFrame(taxon_result_dict_all[:4])

    if len(taxon_result_df):
        taxon_result_df = pd.merge(taxon_result_df,taicol,left_on='val',right_on='taxonID', how='left')
        taxon_result_df = taxon_result_df.replace({np.nan:'', None:''})
        taxon_result_df['taxonRank'] = taxon_result_df['taxonRank'].apply(lambda x: map_occurrence[x] if x else x)
        taxon_result_df = taxon_result_df.replace({np.nan:'', None:''})
        if 'synonyms' in taxon_result_df.keys():
            if 'formatted_synonyms' in taxon_result_df.keys():
                taxon_result_df['synonyms'] = taxon_result_df['formatted_synonyms']
            taxon_result_df['synonyms'] = taxon_result_df['synonyms'].apply(lambda x: ', '.join(x.split(',')))
        taxon_result_df['col_count'] = 0 
        taxon_result_df['occ_count'] = 0 
        # 取得出現紀錄及自然史典藏筆數
        # 每個 taxonID 一個 query facet（走倒排索引），取代 facet.pivot=taxonID,recordType：
        # recordType 是 text 欄位、pivot 冷啟動要先 uninvert 整個欄位，很慢；兩者筆數相同
        tids = [t for t in taxon_result_df.taxonID.unique() if t]
        count_facet = {f't{n}': {'type': 'query', 'q': f'taxonID:{solr_quote(t)}',
                                 'facet': {'col': {'type': 'query', 'q': 'recordType:col'}}}
                       for n, t in enumerate(tids)}
        if count_facet:
            response = requests.post(RECORDS_URL,
                                     data=json.dumps({'query': '*:*', 'limit': 0, 'facet': count_facet}),
                                     headers={'content-type': "application/json"}, timeout=SOLR_TIMEOUT)
            cf = response.json().get('facets', {})
            for n, t in enumerate(tids):
                f = cf.get(f't{n}', {})
                taxon_result_df.loc[taxon_result_df.taxonID==t,'occ_count'] = f.get('count', 0)
                taxon_result_df.loc[taxon_result_df.taxonID==t,'col_count'] = f.get('col', {}).get('count', 0)
        
        # 處理hightlight
        # taxon_result_df['matched_value'] = taxon_result_df['matched_value'].apply(lambda x: highlight(x,keyword,'1'))
        # TODO 這邊應該可以簡化
        if 'vernacularName' in taxon_result_df.keys():
            if (is_sub == 'false') or (is_sub != 'false' and key == 'vernacularName') :
                taxon_result_df['vernacularName'] = taxon_result_df['vernacularName'].apply(lambda x: highlight(x,keyword,'1'))
        if 'alternative_name_c' in taxon_result_df.keys():
            if (is_sub == 'false') or (is_sub != 'false' and key == 'alternative_name_c') :
                taxon_result_df['alternative_name_c'] = taxon_result_df['alternative_name_c'].apply(lambda x: highlight(x,keyword,'1'))
        if 'synonyms' in taxon_result_df.keys():
            do_hl = (is_sub == 'false') or (key == 'synonyms')
            taxon_result_df['synonyms'] = taxon_result_df['synonyms'].apply(
                lambda x: summarize_names(x, keyword, keyword_name_reg, do_highlight=do_hl))
        if (is_sub == 'false') or (is_sub != 'false' and key == 'scientificName') :
            taxon_result_df['formatted_name'] = taxon_result_df['formatted_name'].apply(lambda x: highlight(x,keyword,'1'))
        for required_cols in ['vernacularName', 'alternative_name_c', 'synonyms']:
            if required_cols not in taxon_result_df.keys():
                taxon_result_df[required_cols] = ''
        taxon_result_df = taxon_result_df.replace({np.nan:'', None:''})
    # 照片
    taxon_result_dict = []
    for tr in taxon_result_df.to_dict('records'):
        tr['images'] = []
        results = get_species_images(tr['taxonID'])
        if results:
            tr['taieol_id'] = results[0]
            tr['images'] = results[1]

        tmp = []
        for ii in tr['matched']:
            match_val = ii['matched_value']
            if ii['matched_col'] == map_collection['misapplied']:
                match_val = summarize_names(tr.get('formatted_misapplied') or match_val, keyword, keyword_name_reg)
            else:
                match_val = highlight(match_val, keyword, '1')
            tmp.append({'matched_col': ii['matched_col'], 'matched_value': match_val})
        tr['matched'] = tmp
        taxon_result_dict.append(tr)

    # get_focus_card_taxon 使用
    map_dict = map_occurrence # occ或col沒有差別

    if key:
        title = f"{gettext('物種')} > {gettext(map_dict[key])}"
        item_class = f"item_taxon_{key}"
        card_class = f"taxon-{key}-card"
    else:
        title = None
        item_class = None
        card_class = None

    response = {
        'title': title,
        'item_class': item_class,
        'card_class': card_class,
        'total_count': total_count, # 總數
        'menu_rows': menu_rows, # 側邊欄
        'data': taxon_result_dict,
        'has_more': True if total_count > offset + 4  else False,
        'reach_end': True if offset >= 28 else False
    }

    return response


def if_raw_map(user_id):
    if User.objects.filter(id=user_id).filter(Q(is_partner_account=True,partner__is_collaboration=False)|Q(is_partner_admin=True,partner__is_collaboration=False)|Q(is_system_admin=True)).exists():
        return True
    else:
        return False


def get_map_geojson(data_c, grid):

    map_geojson = {}
    map_geojson[f'grid_{grid}'] = {"type":"FeatureCollection","features":[]}
    for cc in data_c:
        if len(cc['val'].split('_')) > 1:
            current_grid_x = int(cc['val'].split('_')[0])
            current_grid_y = int(cc['val'].split('_')[1])
            current_count = cc['count']
            if current_grid_x > 0 and current_grid_y > 0:
                borders = convert_grid_to_square(current_grid_x, current_grid_y, grid/100)
                tmp = [{
                    "type": "Feature",
                    "geometry":{"type":"Polygon","coordinates":[borders]},
                    "properties": {
                        "counts": current_count,
                        "current_grid_level": f'grid_{grid}',
                        "current_grid": cc['val'],
                    }
                }]
                map_geojson[f'grid_{grid}']['features'] += tmp
    return map_geojson


def get_map_response(map_query, grid_list, get_raw_map):

    map_geojson = {}

    facet_str = ''
    for g in grid_list:
        map_geojson[f'grid_{g}'] = {"type":"FeatureCollection","features":[]}
        if get_raw_map:
            facet_str += f'&facet.field=grid_{g}'
        else:
            facet_str += f'&facet.field=grid_{g}_blurred'
            
    map_response = requests.post(f'{RECORDS_URL}?facet=true&rows=0&facet.mincount=1&facet.limit=-1{facet_str}', data=json.dumps(map_query), headers={'content-type': "application/json" }, timeout=SOLR_TIMEOUT) 

    data_c = {}
    for grid in grid_list:
        if get_raw_map:
            facet_grid = f'grid_{grid}'
        else:
            facet_grid = f'grid_{grid}_blurred'
        data_c = map_response.json()['facet_counts']['facet_fields'][facet_grid]
        for i in range(0, len(data_c), 2):
            if len(data_c[i].split('_')) > 1:
                current_grid_x = int(data_c[i].split('_')[0])
                current_grid_y = int(data_c[i].split('_')[1])
                current_count = data_c[i+1]
                if current_grid_x > 0 and current_grid_y > 0:
                    borders = convert_grid_to_square(current_grid_x, current_grid_y, grid/100)
                    tmp = [{
                        "type": "Feature",
                        "geometry":{"type":"Polygon","coordinates":[borders]},
                        "properties": {
                            "counts": current_count
                        }
                    }]
                    map_geojson[f'grid_{grid}']['features'] += tmp

    return map_geojson


# occurrence & collection detail頁面整理
def create_data_detail(id, user_id, record_type):

    path_str = ''
    logo = ''

    query = {
        'query': "*:*",
        'limit': 1,
        'filter': f"id:{id}",
        }
    response = requests.post(f'{RECORDS_URL}?', data=json.dumps(query), headers={'content-type': "application/json" }, timeout=SOLR_TIMEOUT)
    row = pd.DataFrame(response.json()['response']['docs'])
    row = row.replace({np.nan: '', 'nan': ''})
    row = row.to_dict('records')
    row = row[0]

    if record_type == 'col':
        link_prefix = 'collection'
    else:
        link_prefix = 'occurrence'

    # recordType 在 v1 是多值（['col']），v2 為單值字串，兩種都接受
    row_record_type = row.get('recordType')
    if isinstance(row_record_type, list):
        row_record_type = row_record_type[0] if row_record_type else ''

    if (record_type == 'col' and row_record_type == 'col') or record_type == 'occ':
        if row.get('taxonRank', ''):
            row.update({'taxonRank': map_occurrence[row['taxonRank']]})

        am = []
        if ams := row.get('associatedMedia'):
            if ';' in ams:
                img_sep = ';'
            else:
                img_sep = '|'
            ams = ams.split(img_sep)
            if row.get('mediaLicense'):
                mls = row.get('mediaLicense').split(';')
                if len(mls) == 1:
                    for a in ams:
                        am.append({'img': a, 'license': row.get('mediaLicense'), 'media_type': get_media_type(a)})
                else:
                    img_len = len(ams)
                    for i in range(img_len):
                        am.append({'img': ams[i], 'license': mls[i], 'media_type': get_media_type(ams[i])})
            else:
                for a in ams:
                    am.append({'img': a, 'license': '', 'media_type': get_media_type(a)})
        row.update({'associatedMedia': am})

        # dataGeneralizations：v2 為文字說明（2.3），直接顯示

        # date（v2 單值，D27）
        if date := row.get('standardDate'):
            date = date.split('T')[0]
        else:
            date = None
        row.update({'date': date})

        # 經緯度（v2 單值，D27）：有權限且為模糊化紀錄時用原始座標
        def valid_coord(v, limit):
            return v if v != '' and v is not None and -limit <= v <= limit else None

        if row.get('raw_location_rpt') and if_raw_map(user_id):
            row.update({'lat': valid_coord(row.get('rawDecimalLatitude'), 90)})
            row.update({'lon': valid_coord(row.get('rawDecimalLongitude'), 180)})

            if row.get('rawCounty'):
                row.update({'county': row.get('rawCounty')})

            if row.get('rawMunicipality'):
                row.update({'municipality': row.get('rawMunicipality')})

            # 模糊化的紀錄公開 verbatim 座標為空（2.3），有權限時改顯示原始值
            for k in ('verbatimLatitude', 'verbatimLongitude'):
                if row.get(f'raw{k[0].upper()}{k[1:]}'):
                    row.update({k: row.get(f'raw{k[0].upper()}{k[1:]}')})

        else:
            row.update({'lat': valid_coord(row.get('decimalLatitude'), 90)})
            row.update({'lon': valid_coord(row.get('decimalLongitude'), 180)})

        # 數量（v2 organismQuantity 即原 standardOrganismQuantity，單值）
        if (quantity := row.get('organismQuantity')) not in ('', None):
            quantity = str(quantity)
            if quantity.endswith('.0'):
                quantity = quantity[:-2]
        else:
            quantity = None
        row.update({'quantity': quantity})

        # taxon
        path = []
        path_taxon_id = None
        if row.get('taxonID'):
            path_taxon_id = row.get('taxonID')
        if path_taxon_id:
            response = requests.get(f'{SOLR_PREFIX}taxa/select', params={'q': f'id:{solr_quote(path_taxon_id)}'}, timeout=SOLR_TIMEOUT)
            data = response.json()
            t_rank = data['response']['docs'][0]
            for r in rank_list:
                if t_rank.get(r):
                    if t_rank.get(f"formatted_{r}"):
                        current_str = t_rank.get(f"formatted_{r}")
                    else:
                        current_str = t_rank.get(r)
                    if t_rank.get(f"{r}_c"):
                        current_str += ' ' + t_rank.get(f"{r}_c")

                    t_taxonID = t_rank.get(f"{r}_taxonID")

                    current_str = f'{r.capitalize()} <a target="_blank" href="/search/{link_prefix}?higherTaxonID={t_taxonID}&from=search">{current_str}</a>'
                    path.append(current_str)

        path_str = ' > '.join(path)

        # logo
        if group := row.get('group'):
            if group == 'gbif':
                logo = 'GBIF-2015.png'
            elif logo := Partner.objects.filter(group=group).values('logo'):
                logo = logo[0]['logo']
                logo = 'partner/' + logo

        # references：同一 group 可能有多列 Partner（原本用 get 會 MultipleObjectsReturned），
        # 依該筆 sourceDatabase 對到 info 中相同 dbname 的 link，對不到用第一項
        if not row.get('references') and group:
            if partner := Partner.objects.filter(group=group).order_by('id').first():
                info = partner.info or []
                source_db = row.get('sourceDatabase')
                matched = [i for i in info if to_source_database(i.get('dbname', '')) == source_db]
                if link := (matched or info or [{}])[0].get('link'):
                    row['references'] = link

        row['partnerName'] = get_partner_name(row.get('tbiaPartnerID'))

        modified = (row.get('modified') or '').split('.')[0].replace('T',' ').replace('Z',' ')
        row.update({'modified': modified})
    else:
        row = [] # 如果不是自然史典藏，在自然史典藏頁面不顯示
    return row, path_str, logo


# 表格排序：前端欄位 key（v2）→ Solr 排序欄位（to_v2_field 為 [COMPAT-KEEP]）；回傳 None 表示用呼叫端的預設排序
def records_sort(orderby, sort, get_raw_map, map_dict):
    orderby = to_v2_field(orderby)  # 相容舊 key
    if orderby == 'verbatimEventDate':
        return f'standardDate {sort}'
    if orderby in ('verbatimLatitude', 'verbatimLongitude'):
        axis = 'Latitude' if orderby == 'verbatimLatitude' else 'Longitude'
        if get_raw_map:
            return f'rawDecimal{axis} {sort},decimal{axis} {sort}'
        return f'decimal{axis} {sort}'
    if orderby in map_dict and orderby not in UNSORTABLE_KEYS:
        return f'{orderby} {sort}'
    return None


# 進階搜尋 / 全站搜尋 表格整理
def create_data_table(docs, user_id, obv_str, has_image=None):
    rows = []
    get_raw_map = if_raw_map(user_id)  # 原本每一列都查一次 DB

    for i in docs.index:
        docs = docs.replace({np.nan:None})
        row = docs.iloc[i]
        if row.get('scientificName') and row.get('formatted_name'):
            docs.loc[i, 'scientificName'] = docs.loc[i, 'formatted_name']

        # 這邊如果太長的時候不顯示全部

        syns, misapplied = '', ''

        if row.get('formatted_synonyms'):
            syns = row.get('formatted_synonyms')
        elif row.get('synonyms'):
            syns = row.get('synonyms')
        
        if syns:
            syns = syns.split(',')
            if len(syns) > 1:
                syns = syns[:2]
                syns = ', '.join(syns) + '...'
            else:
                syns = ', '.join(syns)
            docs.loc[i, 'synonyms'] = syns

        if row.get('formatted_misapplied'):
            misapplied = row.get('formatted_misapplied')
        elif row.get('misapplied'):
            misapplied = row.get('misapplied')
        
        if misapplied:
            misapplied = misapplied.split(',')
            if len(misapplied) > 1:
                misapplied = misapplied[:2]
                misapplied = ', '.join(misapplied) + '...'
            else:
                misapplied = ', '.join(misapplied)
            docs.loc[i, 'misapplied'] = misapplied

        # date（v2 單值，D27）：表格的日期欄位 key 為 verbatimEventDate
        if date := row.get('standardDate'):
            docs.loc[i , 'verbatimEventDate'] = date.split('T')[0]
        else:
            if row.get('verbatimEventDate'):
                date_str = gettext(f'原始{obv_str}日期')
                docs.loc[i , 'verbatimEventDate'] = f'---<br><small class="color-silver">[{date_str}]' + row.get('verbatimEventDate') + '</small>'

        # 經緯度：表格欄位 key 為 verbatimLatitude / verbatimLongitude，優先顯示十進位座標
        # 有權限且為模糊化紀錄時用原始座標（raw*）
        if row.get('raw_location_rpt') and get_raw_map:
            lat_cols = ('rawDecimalLatitude', 'rawVerbatimLatitude')
            lon_cols = ('rawDecimalLongitude', 'rawVerbatimLongitude')
            if row.get('rawCounty'):
                docs.loc[i , 'county'] = row.get('rawCounty')
            if row.get('rawMunicipality'):
                docs.loc[i , 'municipality'] = row.get('rawMunicipality')
        else:
            lat_cols = ('decimalLatitude', 'verbatimLatitude')
            lon_cols = ('decimalLongitude', 'verbatimLongitude')

        for out_col, (dec_col, verbatim_col), label in [('verbatimLatitude', lat_cols, '原始紀錄緯度'),
                                                         ('verbatimLongitude', lon_cols, '原始紀錄經度')]:
            if (val := row.get(dec_col)) not in ('', None):
                docs.loc[i , out_col] = val
            elif row.get(verbatim_col):
                docs.loc[i , out_col] = f'---<br><small class="color-silver">[{gettext(label)}]' + row.get(verbatim_col) + '</small>'
            else:
                docs.loc[i , out_col] = ''

        # 數量：v2 只存數值（原始字串不進 Solr）
        if (quantity := row.get('organismQuantity')) not in ('', None):
            quantity = str(quantity)
            if quantity.endswith('.0'):
                quantity = quantity[:-2]
            docs.loc[i , 'organismQuantity'] = quantity

        # 分類階層
        if row.get('taxonRank', ''):
            now_rank = row.get('taxonRank')
            docs.loc[i , 'taxonRank'] = map_collection[now_rank]

        # dataGeneralizations：v2 為文字說明（2.3），直接顯示

        # 紀錄類型
        if row.get('basisOfRecord',''):
            if row.get('basisOfRecord') in basis_map.keys():
                docs.loc[i , 'basisOfRecord'] = basis_map[row.get('basisOfRecord')]

        if media_list := row.get('associatedMedia'):
            img_sep = ';' if ';' in media_list else '|'
            media_list = media_list.split(img_sep)

            # 取得對應的 associatedMediaType list
            mt_list = []
            mt_raw = row.get('associatedMediaType')
            if mt_raw:
                # 兼容 Solr 多值欄位（list）與單值欄位（string）
                items = mt_raw if isinstance(mt_raw, list) else [mt_raw]
                for item in items:
                    item_str = str(item)
                    sep = ';' if ';' in item_str else '|'
                    mt_list.extend(m.strip() for m in item_str.split(sep))
    
            # 若使用者有指定媒體類型，挑出第一筆符合的 index
            target_idx = 0
            if has_image in ['image', 'video', 'audio'] and mt_list:
                for idx, mt in enumerate(mt_list):
                    if has_image in mt.lower():
                        target_idx = idx
                        break

            media_type = mt_list[target_idx] if target_idx < len(mt_list) else None

            if target_idx < len(media_list):
                docs.loc[i, 'associatedMedia'] = get_media_html(media_list[target_idx].strip(), media_type)

    docs = docs.replace({np.nan: ''})
    docs = docs.replace({'nan': ''})

    # 夥伴單位：Solr 只存 tbiaPartnerID，這裡帶入名稱
    if len(docs):
        partner_names = get_partner_name_map()
        docs['partnerName'] = docs['tbiaPartnerID'].map(lambda x: partner_names.get(str(x), '') if x else '') if 'tbiaPartnerID' in docs else ''

    # 棲地:將 is_* 欄位轉成文字,多值以「、」串接
    # （原本在 to_dict 之後才算，habitat 不會出現在回傳結果，改到前面）
    def get_habitat_text(r):
        vals = []
        for k, v in habitat_map.items():
            if str(r.get(k)).lower() in ['true', '1']:
                vals.append(gettext(v))
        return '、'.join(vals)

    if len(docs):
        docs['habitat'] = docs.apply(get_habitat_text, axis=1)

    rows = docs.to_dict('records')

    return rows


def get_resource_cate(extension):
    if extension.lower() in ['docx','csv','json','xlsx', 'xls']:
        cate = 'doc'
    elif extension.lower() in ['ppt','doc','pdf','xml', 'link']:
        cate = extension.lower()
    else:
        cate = 'other'
    return cate


def check_map_bound(map_bound, add_buffer=True):

    map_str = map_bound.split(' TO ')
    map_min_lat =  float(map_str[0].split(',')[0])
    map_min_lon = float(map_str[0].split(',')[1])
    map_max_lat =  float(map_str[1].split(',')[0])
    map_max_lon =  float(map_str[1].split(',')[1])
    if map_min_lon < -180 :
        map_min_lon = -180
    if map_min_lat < -90:
        map_min_lat = -90
    if map_max_lon > 180:
        map_max_lon = 180
    if map_max_lat > 90:
        map_max_lat = 90

    if add_buffer:
        map_min_lat -= 0.1
        map_min_lon -= 0.1
        map_max_lat += 0.1
        map_max_lon += 0.1

    new_map_bound = f'[{map_min_lat},{map_min_lon} TO {map_max_lat},{map_max_lon}]'
    return new_map_bound


def create_search_stat(query_list, q="*:*", v1=False):
    """依來源資料庫統計筆數。[V1-API-REMOVE] v1 參數與分支：v1=True 給 v1 API 用：查 tbia_records_v1 的 rightsHolder，
    名稱在寫入前轉成新名稱，存進 SearchStat 的一律是 v2 名稱（4.4）"""
    url, field = (RECORDS_V1_URL, 'rightsHolder') if v1 else (RECORDS_URL, 'sourceDatabase')

    stat_query = { "query": q,
            "offset": 0,
            "limit": 0,
            "filter": query_list,
            "facet": {
                "stat_rightsHolder": {
                    'type': 'terms',
                    'field': field,
                    'mincount': 1,
                    'limit': -1,
                    'allBuckets': False,
                    'numBuckets': False
                }
            }
        }
    
    if not query_list:
        stat_query.pop('filter', None)

    response = requests.post(url, data=json.dumps(stat_query), headers={'content-type': "application/json" }, timeout=SOLR_TIMEOUT)
    facets = response.json()['facets']

    total_count = response.json()['response']['numFound']

    stat_rightsHolder = []

    if total_count:
        stat_rightsHolder = facets['stat_rightsHolder']['buckets']
        if v1:
            merged = {}
            for b in stat_rightsHolder:
                name = to_source_database(b['val'])
                merged[name] = merged.get(name, 0) + b['count']
            stat_rightsHolder = [{'val': k, 'count': v} for k, v in merged.items()]

    stat_rightsHolder.append({'val': 'total', 'count': total_count})

    return stat_rightsHolder


def background_search_stat(query_list, record_type, query_string, compute_stat=True, v1=False):  # [V1-API-REMOVE] v1 參數
    allowed = {value for value, _ in SearchStat.location_choice}
    if record_type not in allowed:
        return

    # 型別統一：filter 一律正規化成 list（相容舊呼叫傳字串的情況）
    if isinstance(query_list, str):
        query_list = [query_list] if query_list else []

    try:
        stat_rightsHolder = create_search_stat(query_list=query_list, v1=v1) if compute_stat else None
        SearchStat.objects.create(
            query=query_string,
            search_location=record_type,
            stat=stat_rightsHolder,
            created=timezone.now(),
        )
    finally:
        # 手動建立的 thread 不走 request 生命週期，需自行關閉借出的 DB 連線
        connection.close()


def create_sensitive_partner_stat(query_list, q="*:*"):

    query_list.append("rawDecimalLatitude:*")  # 等同 raw_location_rpt:*，冷啟動較快

    query = { "query": q,
                "offset": 0,
                "limit": 0,
                "filter": query_list,
                "facet": {
                    "stat_rightsHolder": {
                        'type': 'terms',
                        'field': 'sourceDatabase',
                        'mincount': 1,
                        'limit': -1,
                        'allBuckets': False,
                        'numBuckets': False
                    }
                }
            }

    if not query_list:
        query.pop('filter')

    response = requests.post(RECORDS_URL, data=json.dumps(query), headers={'content-type': "application/json" }, timeout=SOLR_TIMEOUT)
    facets = response.json()['facets']

    total_count = response.json()['response']['numFound']

    stat_rightsHolder = []

    if total_count: # 有的話再存
        stat_rightsHolder = facets['stat_rightsHolder']['buckets']
        stat_rightsHolder.append({'val': 'total', 'count': total_count})

    return stat_rightsHolder


def create_dataset_stat(query_list, q="*:*"):

    query = { "query": q,
                "offset": 0,
                "limit": 0,
                "filter": query_list,
                "facet": {
                    "stat_tbiaDatasetID": {
                        'type': 'terms',
                        'field': 'tbiaDatasetID',
                        'mincount': 1,
                        'limit': -1,
                        'allBuckets': False,
                        'numBuckets': False
                    }
                }
            }

    if not query_list:
        query.pop('filter', None)

    response = requests.post(RECORDS_URL, data=json.dumps(query), headers={'content-type': "application/json" }, timeout=SOLR_TIMEOUT)
    facets = response.json()['facets']

    # 不一定會有資料
    stat_tbiaDatasetID = []
    if facets.get('stat_tbiaDatasetID'):
        stat_tbiaDatasetID = facets['stat_tbiaDatasetID']['buckets']
        
    if stat_tbiaDatasetID:
        with datahub_conn() as conn, conn.cursor() as cursor:
            for row in stat_tbiaDatasetID:
                cursor.execute(
                    'UPDATE dataset set "downloadCount" = "downloadCount" + 1 WHERE "tbiaDatasetID" = %s',
                    (row.get('val'),),
                )
            # 迴圈結束後由 datahub_conn() 統一 commit

    return 'done'



def ark_generator(data_type, size=6, chars=string.ascii_lowercase + string.digits, mode=env('ENV')):
    if mode == 'prod':
        prefix_number = '1' # 正式站
    else:
        prefix_number = '2' # 測試站


    if data_type == 'news':
        prefix_char = 'n' # 文章

    elif data_type == 'docs':
        prefix_char = 'c' # 文件網站

    elif data_type == 'resource':
        prefix_char = 'r' # 相關資源

    else:
        prefix_char = 'd' # 資料


    new_ark = prefix_char + prefix_number + ''.join(random.choice(chars) for _ in range(size))
    # 要確認有沒有存在在資料庫中
    is_new_ark = False
    while not is_new_ark:
        if Ark.objects.filter(ark=new_ark).exists():
            new_ark = ''.join(random.choice(chars) for _ in range(size))
        else:
            is_new_ark = True

    return new_ark


def get_family_taxon_ids(taxon_ids):

    subset_taxon_list = []
    ids = [f"id:{d}" for d in taxon_ids]

    for tt in range(0, len(taxon_ids), 20):
        taxa_query = {'query': " OR ".join(ids[tt:tt+20]), 'limit': 20, 'fields': ['family_taxonID','genus_taxonID','species_taxonID']}
        response = requests.post(f'{SOLR_PREFIX}taxa/select', data=json.dumps(taxa_query), headers={'content-type': "application/json" }, timeout=SOLR_TIMEOUT)
        if response.status_code == 200:
            resp = response.json()
            if data := resp['response']['docs']:
                subset_taxon_list += data

    taxon = pd.DataFrame(subset_taxon_list)

    final_taxon_ids = []

    for k in ['family_taxonID','genus_taxonID','species_taxonID']:
        if k in taxon.keys():
            final_taxon_ids += taxon[k].to_list()

    return list(set(final_taxon_ids))

# 階層篩選選項 TAXON_RANK_GROUPS、種下 INFRASPECIES_RANKS、RANK_SOLR_VALUE、VALID_TAXON_RANKS
# 11/20 移到 data/search_params.py（依 TaiCOL ranks 表），上方 import 後在這裡沿用


def get_taxon_rank_fq(taxon_rank):
    """回傳 Solr 條件；空值或不在白名單內回傳 ''（= 不篩選）"""
    if taxon_rank == 'sub':
        return f'taxonRank:({" OR ".join(INFRASPECIES_RANKS)})'
    if taxon_rank in VALID_TAXON_RANKS:
        return f'taxonRank:{RANK_SOLR_VALUE.get(taxon_rank, taxon_rank)}'
    return ''