var $csrf_token = $('[name="csrfmiddlewaretoken"]').attr("value");
var $lang = $('[name="lang"]').attr('value');


// highcharts common options
let commonOptions = {
    chart: {
        plotBackgroundColor: null,
        plotBorderWidth: null,
        plotShadow: false,
    },
    lang: {
        thousandsSep: ","
    },
    credits: {
        enabled: false
    },
    navigation: {
        buttonOptions: {
            enabled: false
        }
    },
    title: {
        text: ''
    },
    exporting: { enabled: false },
    credits: { enabled: false },
    legend: { enabled: false },
}

var SliderFormat = {
    from: function(value) {
        return parseInt(value);
    },
    to: function(value) {
            return parseInt(value);
        }
    };

$(document).ready(function () {

    $('.exportPartnerKML').on('click', function(){
        exportToKML(window.partner_layer)
    })

    var PartnerTemporalYearSlider = document.getElementById('partner-temporal-year-slider');

    noUiSlider.create(PartnerTemporalYearSlider, {
        start: [1900, new Date().getFullYear()],
        range: { min: 1900, max: new Date().getFullYear() },
        connect: true,
        step: 1,
        tooltips: true,
        format: SliderFormat,
    });

    PartnerTemporalYearSlider.noUiSlider.on('change', function( values, handle ) {
        updatePartnerTemporal(PartnerTemporalYearSlider);
    });



    $.ajax({
        url: "/get_taxon_group_stat?rights_holder=total",
        type: 'GET',
    })
    .done(function(response){

        $('#container-taxon_group-stat').highcharts(Highcharts.merge(commonOptions, {
            chart: {
                type: 'bar',
                events: {
                    load: function() {
                        
                        var chart = this;
                        var categories = ['昆蟲', '蜘蛛', '魚類', '爬蟲類', '兩棲類', '鳥類', '哺乳類', 
                                        '維管束植物', '蕨類植物', '苔蘚植物', '藻類', '病毒', '細菌', '真菌', '其他'];
                        
                        // 為 x 軸標籤添加點擊事件
                        chart.xAxis[0].labelGroup.element.childNodes.forEach(function(label, index) {
                            $(label).css('cursor', 'pointer')
                                .on('click', function() {
                                    var category = categories[index];
                                    var allPoints = [];
                                    
                                    // 取得該類別的所有 series 資料
                                    chart.series.forEach(function(series) {
                                        if (series.data[index] && series.data[index].y > 0) {
                                            allPoints.push(series.data[index]);
                                        }
                                    });
                                    
                                    // 產生與原 tooltip 相同的內容
                                    var html = generateCategoryInfo(category, allPoints, chart);
                                    
                                    // 顯示到指定的 container
                                    $('#taxon_group-stat-content').html(html).show();
                                });
                        });
                    }
                },            
            },

            tooltip: {
                shared: true,
                formatter: function() {
                    const categories = ['昆蟲', '蜘蛛', '魚類', '爬蟲類', '兩棲類', '鳥類', '哺乳類', 
                                    '維管束植物', '蕨類植物', '苔蘚植物', '藻類', '病毒', '細菌', '真菌', '其他'];
                    
                    let category = categories[this.x];
                    
                    let systemPoints = this.points.filter(p => p.series.name.includes('-系統') && p.y > 0);
                    let unitPoints = this.points.filter(p => p.series.name.includes('-單位') && p.y > 0);
                    
                    let html = `${gettext(category)}<br/>`;
                    
                    // 計算所有系統總數
                    let totalSystemCount = 0;
                    this.points.forEach(p => {
                        if (p.series.name.includes('-系統')) {
                            totalSystemCount += p.series.data.reduce((sum, point) => sum + (point.y || 0), 0);
                        }
                    });
                    
                    // 計算所有單位總數
                    let totalUnitCount = 0;
                    this.points.forEach(p => {
                        if (p.series.name.includes('-單位')) {
                            totalUnitCount += p.series.data.reduce((sum, point) => sum + (point.y || 0), 0);
                        }
                    });
                    
                    if (systemPoints.length > 0) {
                        let systemCount = systemPoints[0].y;
                        let systemPercentage = (systemCount / totalSystemCount * 100).toFixed(2);
                        html += `<br><b>系統整體：</b><br>${Highcharts.numberFormat(systemCount, 0)} 筆 (${systemPercentage}%)<br>`;
                    }
                    
                    if (unitPoints.length > 0) {
                        let unitCount = unitPoints[0].y;
                        let unitTotalPercentage = (unitCount / totalUnitCount * 100).toFixed(2);
                        html += `<br>${Highcharts.numberFormat(unitCount, 0)} ${gettext('筆')} (${unitTotalPercentage}%)<br>`;
                    }

                    return html;
                }
            },
            accessibility: {
                point: {
                    valueSuffix: '%'
                }
            },
            xAxis: {
                categories: [gettext('昆蟲'), gettext('蜘蛛'), gettext('魚類'), gettext('爬蟲類'), gettext('兩棲類'), gettext('鳥類'), gettext('哺乳類'), 
                            gettext('維管束植物'), gettext('蕨類植物'), gettext('苔蘚植物'), gettext('藻類'), gettext('病毒'), gettext('細菌'), gettext('真菌'), gettext('其他')],
                title: {
                    text: null
                },
                crosshair: true,  // 啟用十字線
            },
            yAxis: {
                breaks: [{
                    from: 6000000,
                    to: 18000000,
                    breakSize: 1
                }],
                labels: {
                    step: 2,              // 每隔一個刻度顯示
                },
                title: {
                    text: gettext('資料筆數')
                }
            },

            legend: {
                align: 'center',
                verticalAlign: 'bottom'
            },
            plotOptions: {
                bar: {
                    pointWidth: 8, // 固定寬度（像素）
                    groupPadding: 0.1, // 組間距離（0-1）
                    pointPadding: 0.05, // bar間距離（0-1）
                    dataLabels: {
                        enabled: false
                    },
                    
                }
            },
            series: response.taxon_group_stat
        }));
    })
    .fail(function (xhr, status, errorThrown) {
        alert(gettext('發生未知錯誤！請聯絡管理員'))
        console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
    })




    // $.ajax({
    //     url: "/get_taxon_stat",
    //     type: 'GET',
    // })
    // .done(function (response) {
    
    //     $('#container-taxon_group-stat').highcharts(Highcharts.merge(commonOptions, {
    //         chart: {
    //             type: 'pie'
    //         }, 
    //         tooltip: {
    //             formatter:function(){
    //                 return `<b>${gettext(this.point.name)}</b><br/>${this.point.y} ${gettext('筆')} (${this.point.percentage.toFixed(2)} %)`;
    //                 }
    //         },
    //         accessibility: {
    //             point: {
    //                 valueSuffix: '%'
    //             }
    //         },
    //         plotOptions: {
    //             pie: {
    //                 size: '90%',
    //                 allowPointSelect: true,
    //                 cursor: 'pointer',
    //                 dataLabels: {
    //                     formatter: function () {
    //                         return gettext(this.point.name)
    //                     },
    //                     padding: 0,
    //                     style: {
    //                         fontSize: '10px'
    //                     }
    //                 }
    //             },
    //         },
    //         series: [{
    //             name: '',
    //             colorByPoint: true,
    //             colors: ['#76A578','#DEE9DE','#3F5146','#E2A460','#f4e2c7','#888','#ead065',
    //             '#555','#3B86C0','#304237','#C65454','#ccc' ],
    //             data: response.taxon_group_stat,
    //             cursor: 'pointer',
    //             point: {
    //                 events: {
    //                     click: function () {
    //                         let now_name = this.name
    //                         $.ajax({
    //                             url:  `/get_taxon_group_list?name=${now_name}&group=total`,
    //                             type: 'GET',
    //                         })
    //                         .done(function(resp){
    //                             $('#taxon_group-stat-title').html('[ ' + gettext(now_name) + ' ]')
    //                             $('#taxon_group-stat-list').html('')
    //                             if (resp.length > 0){
    //                                 for (i of resp){
    //                                     if ($lang == 'en-us'){
    //                                         percent_string = `${i.taiwan_percent}% of TaiCOL ${gettext(now_name)} Species in Taiwan`
    //                                     } else {
    //                                         percent_string = `佔TaiCOL臺灣${now_name}物種數 ${i.taiwan_percent}%`
    //                                     }
    //                                     $('#taxon_group-stat-list').append(`<li>${gettext('共')} ${i.count} ${gettext('筆')}<br><span class="small-gray-text"><a href="/media/taxon_stat/total_${now_name}.csv">${percent_string}</a></span></li>`)
    //                                 }
    //                             } else {
    //                                 $('#taxon_group-stat-list').html(gettext('無資料'))
    //                             }
    //                         })
    //                         .fail(function (xhr, status, errorThrown) {
    //                             alert(gettext('發生未知錯誤！請聯絡管理員'))
    //                             console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
    //                         })
            
    //                     }
    //                 }
    //             }
    //             }]
    //         }));

    //     })


        // 資料時間空缺 - 年 - 所屬單位

        $('#container-partner-temporal-year-stat').highcharts(Highcharts.merge(commonOptions, {
            chart: {
                type: "column",
                },
            yAxis: {
                title: {
                    text: gettext('筆數')
                }
            },
            xAxis: {
                title: {
                    text: gettext('年')
                },
                categories: [],
            },
            plotOptions: {
                column: {
                    stacking: 'normal',
                    dataLabels: {
                        enabled: false
                    },
                },
            },
            tooltip: {
                // headerFormat: `<b>{point.category} ${gettext('年')}</b><br/>`,
                pointFormat: '{point.y} ' + gettext('筆'),
            },
        }));
        
        // 資料時間空缺 - 月 - 所屬單位
        
        $('#container-partner-temporal-month-stat').highcharts(Highcharts.merge(commonOptions, {
            chart: {
                type: "column",
                },
            yAxis: {
                title: {
                    text: gettext('筆數')
                }
            },
            xAxis: {
                title: {
                    text: gettext('月')
                },
                categories: [],
            },
            plotOptions: {
                column: {
                    stacking: 'normal',
                    dataLabels: {
                        enabled: false
                    },
                },
            },
            tooltip: {
                // headerFormat: '<b>{point.category}月</b><br/>',
                pointFormat: '{point.y} ' + gettext('筆')
            },
        }));
        
        $('select[name=partner-temporal-taxonGroup]').on('change', function(){
            updatePartnerTemporal(PartnerTemporalYearSlider);
        })

        // 起始狀態
        $('select[name=partner-temporal-taxonGroup]').trigger('change')

})


function updatePartnerTemporal(PartnerTemporalYearSlider){
    $.ajax({
        url:  `/get_temporal_stat?group=total&taxon_group=${$('select[name=partner-temporal-taxonGroup]').find(':selected').val()}&start_year=${PartnerTemporalYearSlider.noUiSlider.get()[0]}&end_year=${PartnerTemporalYearSlider.noUiSlider.get()[1]}`,
        type: 'GET',
    })
    .done(function(response){

        // 年
         
        let partner_temporal_year_chart = $('#container-partner-temporal-year-stat').highcharts()

        while (partner_temporal_year_chart.series.length) {
            partner_temporal_year_chart.series[0].remove();
        }

        partner_temporal_year_chart.xAxis[0].setCategories(response.year_categories, false);

        for (i of response.year_data ) {
            partner_temporal_year_chart.addSeries(i)
        }

        // 月

        let partner_temporal_month_chart = $('#container-partner-temporal-month-stat').highcharts()

        while (partner_temporal_month_chart.series.length) {
            partner_temporal_month_chart.series[0].remove();
        }

        partner_temporal_month_chart.xAxis[0].setCategories(response.month_categories, false);

        for (i of response.month_data ) {
            partner_temporal_month_chart.addSeries(i)
        }



    })
    .fail(function (xhr, status, errorThrown) {
        alert(gettext('發生未知錯誤！請聯絡管理員'))
        console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
    })

}

function getWKTMap(current_map) {
    var neLat = current_map.getBounds().getNorthEast()['lat'] 
    var neLng = current_map.getBounds().getNorthEast()['lng']
    var swLat = current_map.getBounds().getSouthWest()['lat']
    var swLng = current_map.getBounds().getSouthWest()['lng'] 

    return Number(swLat).toFixed(2) + ',' + Number(swLng).toFixed(2) + ' TO ' + Number(neLat).toFixed(2)+ ',' + Number(neLng).toFixed(2)
}

function getColor(d) {
    return d > 100000 ? '#bd0026' :
            d > 50000 ? '#e31a1c' :
            d > 10000 ? '#fc4e2a' :
            d > 5000 ? '#fd8d3c' :
            d > 1000 ? '#feb24c' :
            d > 100 ? '#fed976' :
            d > 10 ? '#ffeda0' :
            d > 0 ?   '#ffffcc' : 'transparent';
}


function style(feature) {
    return {
        fillColor: getColor(feature.properties.counts),
        weight: 1,
        fillOpacity: 0.7,
        color: feature.properties.counts > 0 ? '#b2d2dd' : 'transparent'
    };
}

let partner_map = L.map('partner-map', {gestureHandling: true, minZoom: 2}).setView([23.5, 121.2], 7);

var southWest = L.latLng(-89.98155760646617, -179.9);
var northEast = L.latLng(89.99346179538875, 179.9);
var bounds = L.latLngBounds(southWest, northEast);

partner_map.setMaxBounds(bounds);
partner_map.on('drag', function() {
    partner_map.panInsideBounds(bounds, { animate: false });
});


L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://osm.org/copyright">OpenStreetMap</a> contributors'
}).addTo(partner_map);



partner_map.on('zoomend', function zoomendEvent(ev) {
    // syncMaps(partner_map, portal_map)
    drawMapGrid(current_map=partner_map,group='total',wkt_range=getWKTMap(partner_map))
});


partner_map.on('dragend', function zoomendEvent(ev) {
    // syncMaps(partner_map, portal_map)
    drawMapGrid(current_map=partner_map,group='total',wkt_range=getWKTMap(partner_map))
});


$('select[name=partner-spatial-taxonGroup]').on('change', function(){
    drawMapGrid(current_map=partner_map,group=$('input[name=current_group]').val(),wkt_range=getWKTMap(partner_map))
})

// 起始
$('select[name=partner-spatial-taxonGroup]').trigger('change')

// 統一畫5公里網格
function drawMapGrid(current_map, group, wkt_range){

    taxon_group = $('select[name=partner-spatial-taxonGroup]').find(':selected').val()
    
    $('.loading_area_partial').removeClass('d-none')
    $('.spatial-area-div').addClass('d-none')
    $(`.resultG_5_${group}`).remove()


    $.ajax({
        url: "/get_tw_grid",
        data: `group=total&taxonGroup=${taxon_group}&map_bound=` + wkt_range + '&csrfmiddlewaretoken=' + $csrf_token,
        type: 'POST',
        dataType: 'json',
    })
    .done(function (response) {

        window.partner_layer = L.geoJSON(response, {className: `resultG_5_${group}`, style: style }).addTo(current_map);
        $('.loading_area_partial').addClass('d-none')
        $('.spatial-area-div').removeClass('d-none')

    })
    .fail(function (xhr, status, errorThrown) {
        if (xhr.status == 504) {
            alert(gettext('要求連線逾時'))
        } else {
            alert(gettext('發生未知錯誤！請聯絡管理員'))
        }
        console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
        $('.loading_area_partial').addClass('d-none')
        $('.spatial-area-div').removeClass('d-none')
    
    })

}

function exportToKML(layer) {
    const geoJsonData = layer.toGeoJSON(); // 將圖層轉為 GeoJSON
    const kmlData = tokml(geoJsonData); // 使用 tokml 轉為 KML 格式
    
    // 將 KML 資料導出為檔案
    const blob = new Blob([kmlData], { type: 'application/vnd.google-earth.kml+xml' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'map.kml';
    link.click();
}





function generateCategoryInfo(category, points, chart) {
    var systemPoints = points.filter(p => p.series.name.includes('-系統') && p.y > 0);
    var unitPoints = points.filter(p => p.series.name.includes('-單位') && p.y > 0);
    
    var html = `<p class="fs-18px">[ ${gettext(category)} ]</p>`;
    
    // 計算總數的邏輯...
    var totalSystemCount = 0;
    var totalUnitCount = 0;
    
    chart.series.forEach(function(series) {
        if (series.name.includes('-系統')) {
            totalSystemCount += series.data.reduce((sum, point) => sum + (point.y || 0), 0);
        }
        if (series.name.includes('-單位')) {
            totalUnitCount += series.data.reduce((sum, point) => sum + (point.y || 0), 0);
        }
    });
    
    if (systemPoints.length > 0) {
        var systemCount = systemPoints[0].y;
        var systemPercentage = (systemCount / totalSystemCount * 100).toFixed(2);
        html += `<p class="mt-5px"><b>系統整體：</b><br>${Highcharts.numberFormat(systemCount, 0)} 筆 (${systemPercentage}%)</p>`;
    }
    
    if (unitPoints.length > 0) {
        var unitCount = unitPoints[0].y;
        var unitTotalPercentage = (unitCount / totalUnitCount * 100).toFixed(2);
        var unitPercentage = unitPoints[0].series.options.unitPercentage || 0;
        var taiwanPercentage = unitPoints[0].series.options.taiwanPercentage || 0;
        // if ($('select[name=taxon-group-stat-rightsholder]').find(':selected').val() != 'total'){
        //     html += `<p><b>來源資料庫：</b><br>${Highcharts.numberFormat(unitCount, 0)} 筆 (${unitTotalPercentage}%)<br>`;
        // // }
        // // if ($('select[name=taxon-group-stat-rightsholder]').find(':selected').val() != 'total'){
        //     html += `<b>佔入口網臺灣${category}資料筆數：</b><br>${unitPercentage}%<br>`;
        // }

        if ($lang == 'en-us'){
            html += `<p>${Highcharts.numberFormat(unitCount, 0)} records (${unitTotalPercentage}%)<br>`;
            html += `${taiwanPercentage}% of TaiCOL ${gettext(category)} Species in Taiwan</p>`
            html += `<br><a href="/media/taxon_stat/total_${category}.csv">📥 Download comparison list</a>`;
        } else {
            html += `<p>${Highcharts.numberFormat(unitCount, 0)} 筆 (${unitTotalPercentage}%)<br>`;
            html += `<b>佔TaiCOL臺灣${category}物種數：</b><br>${taiwanPercentage}%</p>`;
            html += `<br><a href="/media/taxon_stat/total_${category}.csv">📥 下載比對結果清單</a>`;
        }


        // html += `<b>佔入口網臺灣${category}資料筆數：</b><br>${unitPercentage}%<br><b>佔TaiCOL臺灣${category}物種數：</b><br>${taiwanPercentage}%</p>`;
    }
    
    
    return html;

}
