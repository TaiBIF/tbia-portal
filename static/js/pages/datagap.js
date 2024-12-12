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
        url: "/get_taxon_stat",
        type: 'GET',
    })
    .done(function (response) {
    
        $('#container-taxon_group-stat').highcharts(Highcharts.merge(commonOptions, {
            chart: {
                type: 'pie'
            }, 
            tooltip: {
                formatter:function(){
                    return `<b>${gettext(this.point.name)}</b><br/>${this.point.y} ${gettext('筆')} (${this.point.percentage.toFixed(2)} %)`;
                    }
            },
            accessibility: {
                point: {
                    valueSuffix: '%'
                }
            },
            plotOptions: {
                pie: {
                    size: '90%',
                    allowPointSelect: true,
                    cursor: 'pointer',
                    dataLabels: {
                        formatter: function () {
                            return gettext(this.point.name)
                        },
                        padding: 0,
                        style: {
                            fontSize: '10px'
                        }
                    }
                },
            },
            series: [{
                name: '',
                colorByPoint: true,
                colors: ['#76A578','#DEE9DE','#3F5146','#E2A460','#f4e2c7','#888','#ead065',
                '#555','#3B86C0','#304237','#C65454','#ccc' ],
                data: response.taxon_group_stat,
                cursor: 'pointer',
                point: {
                    events: {
                        click: function () {
                            let now_name = this.name
                            $.ajax({
                                url:  `/get_taxon_group_list?name=${now_name}&group=total`,
                                type: 'GET',
                            })
                            .done(function(resp){
                                $('#taxon_group-stat-title').html('[ ' + gettext(now_name) + ' ]')
                                $('#taxon_group-stat-list').html('')
                                if (resp.length > 0){
                                    for (i of resp){
                                        if ($lang == 'en-us'){
                                            percent_string = `${i.taiwan_percent}% of TaiCOL ${gettext(now_name)} Species in Taiwan`
                                        } else {
                                            percent_string = `佔TaiCOL臺灣${now_name}物種數 ${i.taiwan_percent}%`
                                        }
                                        $('#taxon_group-stat-list').append(`<li>${gettext('共')} ${i.count} ${gettext('筆')}<br><span class="small-gray-text">${percent_string}</span></li>`)
                                    }
                                } else {
                                    $('#taxon_group-stat-list').html(gettext('無資料'))
                                }
                            })
                            .fail(function (xhr, status, errorThrown) {
                                alert(gettext('發生未知錯誤！請聯絡管理員'))
                                console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
                            })
            
                        }
                    }
                }
                }]
            }));

        })


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
                '#ffffcc';
}


function style(feature) {
    return {
        fillColor: getColor(feature.properties.counts),
        weight: 1,
        fillOpacity: 0.7,
        color: '#b2d2dd'
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


L.tileLayer('https://{s}.tile.osm.org/{z}/{x}/{y}.png', {
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
    
    $('.loading_area').removeClass('d-none')
    $(`.resultG_5_${group}`).remove()


    $.ajax({
        url: "/get_map_grid",
        data: `group=total&taxonGroup=${taxon_group}&grid=5&map_bound=` + wkt_range + '&csrfmiddlewaretoken=' + $csrf_token,
        type: 'POST',
        dataType: 'json',
    })
    .done(function (response) {

        window.partner_layer = L.geoJSON(response, {className: `resultG_5_${group}`, style: style }).addTo(current_map);
        $('.loading_area').addClass('d-none')

    })
    .fail(function (xhr, status, errorThrown) {
        if (xhr.status == 504) {
            alert(gettext('要求連線逾時'))
        } else {
            alert(gettext('發生未知錯誤！請聯絡管理員'))
        }
        console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
        $('.loading_area').addClass('d-none')
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

