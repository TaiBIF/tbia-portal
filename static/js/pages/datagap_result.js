var $csrf_token = $('[name="csrfmiddlewaretoken"]').attr("value");
var $lang = $('[name="lang"]').attr('value');

// ============================================================
// 顏色常數
// ============================================================
const COLOR_2024 = '#7FA89E';
const COLOR_2025 = '#D29478';
const COLOR_2024_DECLINE = '#D3D3D3';
const COLOR_2025_DECLINE = '#808080';
const COLOR_NEW_GROWTH = '#00FFFF';

// 年份固定範圍
const YEAR_MIN = 1980;
const YEAR_MAX = 2025;

// Highcharts 共用設定
let commonOptions = {
    chart: { plotBackgroundColor: null, plotBorderWidth: null, plotShadow: false },
    lang: { thousandsSep: "," },
    credits: { enabled: false },
    navigation: { buttonOptions: { enabled: false } },
    title: { text: '' },
    exporting: { enabled: false },
    legend: { enabled: false },
};

var SliderFormat = {
    from: function(value) { return parseInt(value); },
    to: function(value) { return parseInt(value); }
};

// ============================================================
// API 資料容器
// ============================================================
var TAXON_DATA = [];
var TEMPORAL_DATA = null;
var GRID_DATA = null;

window.CURRENT_MAP_MODE = 'after';


// ============================================================
// 年份區間 helper
// ============================================================
function getYearRange() {
    var slider = document.getElementById('partner-temporal-year-slider');
    if (!slider || !slider.noUiSlider) return [YEAR_MIN, YEAR_MAX];
    var vals = slider.noUiSlider.get();
    return [parseInt(vals[0]), parseInt(vals[1])];
}

function getYearRangeLabel() {
    var range = getYearRange();
    return range[0] + '–' + range[1];
}

/** 年份圖：依滑桿區間 slice 全量資料 */
function getSlicedYearData() {
    if (!TEMPORAL_DATA) return null;
    var td = TEMPORAL_DATA.years;
    var range = getYearRange();
    var startIdx = td.categories.indexOf(String(range[0]));
    var endIdx = td.categories.indexOf(String(range[1]));

    if (startIdx < 0) startIdx = 0;
    if (endIdx < 0) endIdx = td.categories.length - 1;
    endIdx += 1;

    return {
        categories: td.categories.slice(startIdx, endIdx),
        data_2024: td.data_2024.slice(startIdx, endIdx),
        data_2025: td.data_2025.slice(startIdx, endIdx),
        taxon_breakdown: td.taxon_breakdown.slice(startIdx, endIdx),
    };
}

/**
 * 月份圖：依年份區間彙整月份資料
 *
 * 使用 TEMPORAL_DATA.year_month（由 Python 產出）:
 * {
 *   "data_2024": { "1980": [m1..m12], "1981": [...], ... },
 *   "data_2025": { "1980": [m1..m12], ... },
 *   "taxon_breakdown": { "1980": [{ "鳥類":{c2024,c2025}, ... }, ...12個], ... }
 * }
 */
function getAggregatedMonthData() {
    if (!TEMPORAL_DATA || !TEMPORAL_DATA.year_month) return null;

    var ym = TEMPORAL_DATA.year_month;
    var range = getYearRange();
    var categories = ['1月','2月','3月','4月','5月','6月','7月','8月','9月','10月','11月','12月'];
    var data_2024 = [0,0,0,0,0,0,0,0,0,0,0,0];
    var data_2025 = [0,0,0,0,0,0,0,0,0,0,0,0];
    var breakdown = [{},{},{},{},{},{},{},{},{},{},{},{}];

    for (var y = range[0]; y <= range[1]; y++) {
        var yStr = String(y);
        var m24 = ym.data_2024[yStr];
        var m25 = ym.data_2025[yStr];
        var mBd = ym.taxon_breakdown[yStr];
        if (!m24 && !m25) continue;

        for (var m = 0; m < 12; m++) {
            if (m24) data_2024[m] += m24[m] || 0;
            if (m25) data_2025[m] += m25[m] || 0;

            if (mBd && mBd[m]) {
                var src = mBd[m];
                Object.keys(src).forEach(function(bg) {
                    if (!breakdown[m][bg]) {
                        breakdown[m][bg] = { c2024: 0, c2025: 0 };
                    }
                    breakdown[m][bg].c2024 += src[bg].c2024 || 0;
                    breakdown[m][bg].c2025 += src[bg].c2025 || 0;
                });
            }
        }
    }

    return {
        categories: categories,
        data_2024: data_2024,
        data_2025: data_2025,
        taxon_breakdown: breakdown,
    };
}


// ============================================================
// 靜態 JSON 載入
// ============================================================
function fetchSummary() {
    return $.getJSON('/static/datagap/summary.json').done(renderSummaryCards);
}

function fetchTaxonStats() {
    return $.getJSON('/static/datagap/taxon_stats.json').done(function(data) {
        TAXON_DATA = data;
        renderTaxonChart();
        renderTaxaCards(data);
    });
}

function fetchTemporalStats(taxonGroup) {
    var filename = taxonGroup || 'all';
    return $.getJSON('/static/datagap/temporal/' + encodeURIComponent(filename) + '.json').done(function(data) {
        TEMPORAL_DATA = data;
        refreshTemporalCharts();
    });
}

/**
 * 載入底圖網格（只做一次），然後載入資料
 */
function initSpatialMap(taxonGroup) {
    $('.loading_area_partial').removeClass('is-hidden');
    $.getJSON('/static/datagap/grids/base_grid.geojson').done(function(baseData) {
        // 建立底圖圖層 + gridcode → layer lookup
        window.gridLayerLookup = {};
        window.partner_layer = L.geoJSON(baseData, {
            style: baseGridStyle,
            onEachFeature: function(feature, layer) {
                window.gridLayerLookup[feature.properties.gridcode] = layer;
            }
        }).addTo(partner_map);

        // 載入資料
        fetchSpatialData(taxonGroup);
    });
}

/**
 * 載入某個類群的資料 JSON，套用到底圖圖層上
 */
function fetchSpatialData(taxonGroup) {
    var filename = taxonGroup || 'all';
    $('.loading_area_partial').removeClass('is-hidden');
    $.getJSON('/static/datagap/grids/' + encodeURIComponent(filename) + '.json').done(function(data) {
        GRID_DATA = data; // { gridcode: { counts_2024, counts_2025, taxon_breakdown } }
        applyGridData();
        $('.loading_area_partial').addClass('is-hidden');
    }).fail(function() {
        $('.loading_area_partial').addClass('is-hidden');
    });
}


// ============================================================
// ① 統計卡片渲染
// ============================================================
function renderSummaryCards(data) {
    $('#stat-filled-grids').text(Highcharts.numberFormat(data.filled_grids, 0));
    $('#stat-filled-grids-sub').text(
        gettext('成功新填補') + ' ' + data.filled_grids_delta + ' ' + gettext('個空間網格缺口')
    );
    $('#stat-conservation-records').text(Highcharts.numberFormat(data.conservation_records, 0));
    $('#stat-coverage-rate').text(data.coverage_rate + '%');
    $('#stat-filled-delta-text').html(
        '2025 ' + gettext('年共填補了') + ' <span class="spatial-stat-number">' + data.filled_grids_delta + '</span> ' +
        gettext('個網格缺口。全台覆蓋率達') + ' <span class="spatial-stat-number">' + data.coverage_rate + '%</span>。'
    );
    $('.metric-badge__value').text(data.gap_rate + '%');
}


// ============================================================
// ③ 主要類群卡片渲染
// ============================================================
var TAXA_CARD_CONFIG = {
    '兩棲類':     { icon: '🐸', cssClass: 'taxa-card--amphibian' },
    '鳥類':       { icon: '🐦', cssClass: 'taxa-card--bird' },
    '蕨類植物':   { icon: '🌿', cssClass: 'taxa-card--fern' },
    '哺乳類':     { icon: '🦇', cssClass: 'taxa-card--mammal' },
    '魚類':       { icon: '🐟', cssClass: 'taxa-card--fish' },
};

function renderTaxaCards(data) {
    var cards = data
        .filter(function(t) { return t.taicol_species_total != null; })
        .sort(function(a, b) { return b.ratio_2025 - a.ratio_2025; })
        .slice(0, 5);

    var $grid = $('.taxa-grid');
    $grid.empty();

    cards.forEach(function(t) {
        var cfg = TAXA_CARD_CONFIG[t.name] || { icon: '🔬', cssClass: '' };
        var html = '';
        html += '<div class="taxa-card ' + cfg.cssClass + '">';
        html +=   '<div class="taxa-card__icon">' + cfg.icon + '</div>';
        html +=   '<div class="taxa-card__name">' + gettext(t.name) + '</div>';
        html +=   '<div class="taxa-card__value">' + t.ratio_2025.toFixed(2) + '%</div>';
        html +=   '<div class="taxa-card__meta">';
        html +=     '<div class="taxa-card__meta-row"><span>TaiCOL</span><span>' +
                    Highcharts.numberFormat(t.taicol_species_covered, 0) + ' / ' +
                    Highcharts.numberFormat(t.taicol_species_total, 0) + ' ' + gettext('種') + '</span></div>';
        html +=     '<div class="taxa-card__bar"><div class="taxa-card__bar-fill" style="width:' + t.ratio_2025 + '%"></div></div>';
        html +=   '</div>';
        html += '</div>';
        $grid.append(html);
    });
}


// ============================================================
// Leaflet 地圖初始化
// ============================================================
let partner_map = L.map('partner-map', { gestureHandling: true, minZoom: 2 }).setView([23.5, 121.2], 7);

var southWest = L.latLng(-89.98155760646617, -179.9);
var northEast = L.latLng(89.99346179538875, 179.9);
var mapBounds = L.latLngBounds(southWest, northEast);

partner_map.setMaxBounds(mapBounds);
partner_map.on('drag', function() {
    partner_map.panInsideBounds(mapBounds, { animate: false });
});

L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://osm.org/copyright">OpenStreetMap</a> contributors'
}).addTo(partner_map);

// GeoJSON 是完整台灣範圍，Leaflet 自動處理視窗裁切，不需要在 zoomend/dragend 重新載入


// ============================================================
// 地圖輔助函式
// ============================================================
function getColor(d) {
    return d > 100000 ? '#bd0026' :
           d > 50000  ? '#e31a1c' :
           d > 10000  ? '#fc4e2a' :
           d > 5000   ? '#fd8d3c' : 'transparent';
}

/** 底圖灰框樣式（無資料） */
var baseGridStyle = {
    fillColor: 'transparent',
    fillOpacity: 0,
    weight: 0.8,
    color: '#94a3b8',
    opacity: 0.7
};

/** 根據資料值算出有資料網格的樣式 */
function dataGridStyle(c24, c25) {
    var mode = window.CURRENT_MAP_MODE;
    var val = (mode === 'before') ? c24 : c25;

    if (val <= 5000) return baseGridStyle;

    var isNewGrowth = (mode === 'after' && c24 < 5000 && c25 >= 5000);
    return {
        fillColor: isNewGrowth ? COLOR_NEW_GROWTH : getColor(val),
        fillOpacity: isNewGrowth ? 0.9 : 0.8,
        weight: isNewGrowth ? 1.5 : 1,
        opacity: 1,
        color: '#94a3b8'
    };
}

/**
 * 將 GRID_DATA 套用到底圖圖層：setStyle + 綁定/解綁事件
 */
function applyGridData() {
    if (!window.gridLayerLookup || !GRID_DATA) return;

    // 遍歷所有底圖網格
    Object.keys(window.gridLayerLookup).forEach(function(gridcode) {
        var layer = window.gridLayerLookup[gridcode];
        var d = GRID_DATA[gridcode];

        // 清除舊事件
        layer.off('click mouseover mouseout');

        if (!d) {
            // 無資料：還原灰框
            layer.setStyle(baseGridStyle);
            return;
        }

        var c24 = d.counts_2024 || 0;
        var c25 = d.counts_2025 || 0;
        var style = dataGridStyle(c24, c25);
        layer.setStyle(style);

        var val = window.CURRENT_MAP_MODE === 'before' ? c24 : c25;
        if (val > 5000) {
            layer.on('click', function() { showMapGridDetail(gridcode, d); });
            layer.on('mouseover', function() {
                layer.setStyle({ weight: 2, color: '#3F5146', opacity: 1 });
            });
            layer.on('mouseout', function() {
                layer.setStyle(dataGridStyle(c24, c25));
            });
        }
    });
}

/**
 * 年份模式切換時重新套用樣式（不重新載入資料）
 */
function refreshGridStyles() {
    applyGridData();
}

function showMapGridDetail(gridcode, d) {
    var c24 = d.counts_2024 || 0;
    var c25 = d.counts_2025 || 0;
    var isNewGrowth = c24 < 5000 && c25 >= 5000;
    var mode = window.CURRENT_MAP_MODE;

    $('#map-detail-total').text(Highcharts.numberFormat(mode === 'before' ? c24 : c25, 0));

    var $box = $('#map-detail-composition');
    $box.empty();

    var selectedTaxon = $('select[name=partner-spatial-taxonGroup]').val();
    var breakdown = d.taxon_breakdown || {};
    var entries;

    if (selectedTaxon) {
        var bd = breakdown[selectedTaxon];
        entries = bd ? [{ name: selectedTaxon, c2024: bd.c2024, c2025: bd.c2025 }] : [];
    } else {
        entries = Object.entries(breakdown)
            .map(function(pair) { return { name: pair[0], c2024: pair[1].c2024, c2025: pair[1].c2025 }; })
            .sort(function(a, b) { return b.c2025 - a.c2025; });
    }

    var html = buildCompositionTable(entries, gettext('此網格無該類群資料'));

    if (isNewGrowth) {
        html += '<div class="composition-row composition-row--highlight">';
        html +=   '<span>✨ ' + gettext('2025 新增突破區域') + '</span>';
        html += '</div>';
    }
    $box.html(html);

    $('#map-detail-empty').addClass('is-hidden');
    $('#map-detail-filled').removeClass('is-hidden');
}


// ============================================================
// ⑤ 物種類群長條圖 (2024 vs 2025)
// ============================================================
function renderTaxonChart() {
    var sorted = TAXON_DATA.slice().sort(function(a, b) { return a.ratio_2025 - b.ratio_2025; });

    var data2024 = sorted.map(function(t) {
        return { y: t.ratio_2024, color: t.ratio_2025 < t.ratio_2024 ? COLOR_2024_DECLINE : COLOR_2024 };
    });
    var data2025 = sorted.map(function(t) {
        return { y: t.ratio_2025, color: t.ratio_2025 < t.ratio_2024 ? COLOR_2025_DECLINE : COLOR_2025 };
    });

    $('#container-taxon_group-stat').highcharts(Highcharts.merge(commonOptions, {
        chart: { type: 'bar', backgroundColor: 'transparent' },
        xAxis: {
            categories: sorted.map(function(t) { return gettext(t.name); }),
            lineColor: 'transparent',
            tickLength: 0,
            labels: { style: { fontSize: '13px', fontWeight: 'bold', color: '#334155' } },
        },
        yAxis: {
            title: { text: gettext('資料筆數'), style: { color: '#64748b', fontSize: '12px' } },
            max: 100,
            gridLineDashStyle: 'Dash',
            gridLineColor: '#e2e8f0',
            labels: { rotation: -20, format: '{value}%', style: { color: '#94a3b8', fontSize: '12px' } },
        },
        legend: {
            enabled: true,
            align: 'center',
            verticalAlign: 'bottom',
            itemStyle: { fontSize: '12px', fontWeight: 'bold' },
        },
        tooltip: {
            shared: true,
            backgroundColor: '#1e293b',
            borderColor: 'transparent',
            borderRadius: 8,
            style: { color: '#fff' },
            formatter: function() {
                var t = sorted[this.x];
                var d = (t.ratio_2025 - t.ratio_2024).toFixed(2);
                var sign = d >= 0 ? '+' : '';
                return '<b>' + gettext(t.name) + '</b><br/>' +
                       '2024: ' + t.ratio_2024.toFixed(2) + '%<br/>' +
                       '2025: ' + t.ratio_2025.toFixed(2) + '%<br/>' +
                       gettext('變化') + ': ' + sign + d + ' ' + gettext('百分點');
            }
        },
        plotOptions: {
            bar: {
                grouping: false,
                pointPadding: 0,
                borderWidth: 0,
                cursor: 'pointer',
                dataLabels: { enabled: false },
                point: {
                    events: {
                        click: function() { showTaxonDetail(sorted[this.x]); }
                    }
                }
            }
        },
        series: [
            { name: '2025', data: data2025, pointPadding: 0, color: COLOR_2025 },
            { name: '2024', data: data2024, pointPadding: 0, color: COLOR_2024 }
        ]
    }));
}

function showTaxonDetail(t) {
    $('#taxon-detail-empty').addClass('is-hidden');
    $('#taxon_group-stat-content').removeClass('is-hidden');

    var delta = (t.ratio_2025 - t.ratio_2024).toFixed(2);
    var recordDelta = t.records_2025 - t.records_2024;
    var sign = delta >= 0 ? '+' : '';
    var deltaClass = t.ratio_2025 < t.ratio_2024 ? 'delta-decline' : 'delta-growth';
    var recordSign = recordDelta >= 0 ? '+' : '';
    var recordClass = recordDelta >= 0 ? 'delta-growth' : 'delta-decline';

    var html = '';
    html += '<p class="fs-18px">[ ' + gettext(t.name) + ' ]</p>';
    html += '<p class="mt-5px"><b>2024 ' + gettext('填補率') + '：</b>' + t.ratio_2024.toFixed(2) + '%</p>';
    html += '<p><b>2025 ' + gettext('填補率') + '：</b>' + t.ratio_2025.toFixed(2) + '%</p>';
    html += '<p><b>' + gettext('年度變化') + '：</b><span class="' + deltaClass + '">' + sign + delta + ' ' + gettext('百分點') + '</span></p>';
    html += '<p class="mt-5px"><b>2024 ' + gettext('資料筆數') + '：</b>' + Highcharts.numberFormat(t.records_2024, 0) + '</p>';
    html += '<p><b>2025 ' + gettext('資料筆數') + '：</b>' + Highcharts.numberFormat(t.records_2025, 0) + '</p>';
    html += '<p><b>' + gettext('筆數增長') + '：</b><span class="' + recordClass + '">' + recordSign + Highcharts.numberFormat(recordDelta, 0) + '</span></p>';
    $('#taxon-detail-inner').html(html);
}


// ============================================================
// ④ 時間圖：年（依年份區間 slice）
// ============================================================
function renderTemporalYearChart() {
    var sliced = getSlicedYearData();
    if (!sliced) return;

    $('#container-partner-temporal-year-stat').highcharts(Highcharts.merge(commonOptions, {
        chart: { type: 'column', backgroundColor: 'transparent', spacing: [8, 0, 8, 0] },
        xAxis: {
            categories: sliced.categories,
            lineColor: 'transparent',
            tickLength: 0,
            labels: { rotation: -45, style: { color: '#94a3b8', fontSize: '12px', fontWeight: 'bold' }, step: 5 }
        },
        yAxis: {
            title: { text: null },
            gridLineDashStyle: 'Dash',
            gridLineColor: '#e2e8f0',
            labels: { style: { color: '#94a3b8', fontSize: '12px' } }
        },
        legend: {
            enabled: true,
            align: 'center',
            verticalAlign: 'bottom',
            itemStyle: { fontSize: '12px', fontWeight: 'bold' }
        },
        tooltip: {
            shared: true,
            backgroundColor: '#1e293b',
            borderColor: 'transparent',
            borderRadius: 8,
            style: { color: '#fff' },
            pointFormat: '{series.name}: <b>{point.y:,.0f}</b> ' + gettext('筆') + '<br/>'
        },
        plotOptions: {
            column: {
                grouping: false,
                pointPadding: 0,
                borderWidth: 0,
                cursor: 'pointer',
                dataLabels: { enabled: false },
                point: {
                    events: {
                        click: function() { updateTemporalDetail(this.category, null); }
                    }
                }
            }
        },
        series: [
            { name: '2025', data: sliced.data_2025.slice(), color: COLOR_2025, pointPadding: 0 },
            { name: '2024', data: sliced.data_2024.slice(), color: COLOR_2024, pointPadding: 0 }
        ]
    }));
}


// ============================================================
// ④ 時間圖：月（依年份區間彙整）
// ============================================================
function renderTemporalMonthChart() {
    var agg = getAggregatedMonthData();
    if (!agg) return;

    $('#temporal-month-title').text(gettext('月份分布') + '（' + getYearRangeLabel() + '）');

    $('#container-partner-temporal-month-stat').highcharts(Highcharts.merge(commonOptions, {
        chart: { type: 'column', backgroundColor: 'transparent', spacing: [8, 0, 8, 0] },
        xAxis: {
            categories: agg.categories,
            lineColor: 'transparent',
            tickLength: 0,
            labels: { style: { color: '#94a3b8', fontSize: '12px', fontWeight: 'bold' } }
        },
        yAxis: {
            title: { text: null },
            gridLineDashStyle: 'Dash',
            gridLineColor: '#e2e8f0',
            labels: { style: { color: '#94a3b8', fontSize: '12px' } }
        },
        legend: {
            enabled: true,
            align: 'center',
            verticalAlign: 'bottom',
            itemStyle: { fontSize: '12px', fontWeight: 'bold' }
        },
        tooltip: {
            shared: true,
            backgroundColor: '#1e293b',
            borderColor: 'transparent',
            borderRadius: 8,
            style: { color: '#fff' },
            pointFormat: '{series.name}: <b>{point.y:,.0f}</b> ' + gettext('筆') + '<br/>'
        },
        plotOptions: {
            column: {
                grouping: false,
                pointPadding: 0,
                borderWidth: 0,
                cursor: 'pointer',
                dataLabels: { enabled: false },
                point: {
                    events: {
                        click: function() { updateTemporalDetail(null, this.category); }
                    }
                }
            }
        },
        series: [
            { name: '2025', data: agg.data_2025.slice(), color: COLOR_2025, pointPadding: 0 },
            { name: '2024', data: agg.data_2024.slice(), color: COLOR_2024, pointPadding: 0 }
        ]
    }));
}


// ============================================================
// ④ 刷新時間圖
// ============================================================
function refreshTemporalCharts() {
    renderTemporalYearChart();
    renderTemporalMonthChart();

    // 關閉詳情面板
    $('#temporal-detail-filled').addClass('is-hidden');
    $('#temporal-detail-empty').removeClass('is-hidden');
}


// ============================================================
// ④ 時間詳情面板
// ============================================================
function updateTemporalDetail(year, month) {
    if (!TEMPORAL_DATA) return;

    $('#temporal-detail-empty').addClass('is-hidden');
    $('#temporal-detail-filled').removeClass('is-hidden');

    var val2024, val2025, breakdown, titleText;

    if (month) {
        // 月份：使用年份區間彙整後的資料
        var agg = getAggregatedMonthData();
        if (!agg) return;

        var monthIndex = parseInt(String(month).replace(/[^0-9]/g, '')) - 1;
        if (monthIndex < 0 || monthIndex > 11) monthIndex = 0;
        val2024 = agg.data_2024[monthIndex];
        val2025 = agg.data_2025[monthIndex];
        breakdown = agg.taxon_breakdown[monthIndex];
        titleText = agg.categories[monthIndex] + '（' + getYearRangeLabel() + '）';
    } else {
        // 年份：該單一年份的資料（從全量資料取，不受 slider 影響）
        var td = TEMPORAL_DATA.years;
        var yearIndex = td.categories.indexOf(String(year));
        if (yearIndex < 0) return;
        val2024 = td.data_2024[yearIndex];
        val2025 = td.data_2025[yearIndex];
        breakdown = td.taxon_breakdown[yearIndex];
        titleText = year;
    }

    var delta = val2025 - val2024;
    var deltaSign = delta >= 0 ? '+' : '';
    var deltaClass = delta >= 0 ? 'delta-growth' : 'delta-decline';

    $('#temporal-detail-title').text(titleText);
    $('#temporal-detail-records').text(Highcharts.numberFormat(val2025, 0));
    $('#temporal-detail-delta').attr('class', 'detail-panel__total-delta ' + deltaClass)
        .text('（' + deltaSign + Highcharts.numberFormat(delta, 0) + '）');

    var selectedTaxon = $('select[name=partner-temporal-taxonGroup]').val();
    var entries;
    if (selectedTaxon) {
        var d = breakdown[selectedTaxon];
        entries = d ? [{ name: selectedTaxon, c2024: d.c2024, c2025: d.c2025 }] : [];
    } else {
        entries = Object.entries(breakdown)
            .map(function(pair) { return { name: pair[0], c2024: pair[1].c2024, c2025: pair[1].c2025 }; })
            .sort(function(a, b) { return b.c2025 - a.c2025; });
    }

    $('#temporal-detail-composition').html(
        buildCompositionTable(entries, gettext('此時段無該類群資料'))
    );
}


// ============================================================
// 共用：composition 表格建構
// ============================================================
function buildCompositionTable(entries, emptyMsg) {
    var html = '';
    html += '<div class="composition-row composition-row--header">';
    html +=   '<span class="comp-col-name">' + gettext('類群') + '</span>';
    html +=   '<span class="comp-col-num">2024</span>';
    html +=   '<span class="comp-col-num">2025</span>';
    html +=   '<span class="comp-col-num">' + gettext('變化') + '</span>';
    html += '</div>';

    if (entries.length === 0) {
        html += '<div class="composition-row"><span style="color:#94a3b8">' + emptyMsg + '</span></div>';
    } else {
        entries.forEach(function(e) {
            var d = e.c2025 - e.c2024;
            var cls = d >= 0 ? 'composition-row--growth' : 'composition-row--decline';
            var sign = d >= 0 ? '+' : '';
            html += '<div class="composition-row ' + cls + '">';
            html +=   '<span class="comp-col-name">' + e.name + '</span>';
            html +=   '<span class="comp-col-num">' + Highcharts.numberFormat(e.c2024, 0) + '</span>';
            html +=   '<span class="comp-col-num">' + Highcharts.numberFormat(e.c2025, 0) + '</span>';
            html +=   '<span class="comp-col-num comp-col-delta">' + sign + Highcharts.numberFormat(d, 0) + '</span>';
            html += '</div>';
        });
    }
    return html;
}


// ============================================================
// Ready
// ============================================================
$(document).ready(function() {

    // 年份區間滑桿（固定 1980–2025）
    var PartnerTemporalYearSlider = document.getElementById('partner-temporal-year-slider');
    noUiSlider.create(PartnerTemporalYearSlider, {
        start: [YEAR_MIN, YEAR_MAX],
        range: { min: YEAR_MIN, max: YEAR_MAX },
        connect: true,
        step: 1,
        tooltips: true,
        format: SliderFormat,
    });
    PartnerTemporalYearSlider.noUiSlider.on('change', function() {
        refreshTemporalCharts();
    });

    // 時間類群選單（重新載入該類群 JSON）
    $('select[name=partner-temporal-taxonGroup]').on('change', function() {
        fetchTemporalStats($(this).val());
    });

    // 空間類群選單（只換資料，不重建圖層）
    $('select[name=partner-spatial-taxonGroup]').on('change', function() {
        fetchSpatialData($(this).val());
    });

    // 年份模式切換 (2024/2025)（只重新套樣式，不重建圖層）
    $('.year-toggle__btn').on('click', function() {
        $('.year-toggle__btn').removeClass('active');
        $(this).addClass('active');
        window.CURRENT_MAP_MODE = $(this).data('mode');
        refreshGridStyles();
    });

    // 面板關閉
    $('#map-detail-close').on('click', function() {
        $('#map-detail-filled').addClass('is-hidden');
        $('#map-detail-empty').removeClass('is-hidden');
    });
    $('#temporal-detail-close').on('click', function() {
        $('#temporal-detail-filled').addClass('is-hidden');
        $('#temporal-detail-empty').removeClass('is-hidden');
    });
    $('#taxon-detail-close').on('click', function() {
        $('#taxon_group-stat-content').addClass('is-hidden');
        $('#taxon-detail-empty').removeClass('is-hidden');
    });

    // 載入資料
    fetchSummary();
    fetchTaxonStats();
    fetchTemporalStats('');
    initSpatialMap('');
});