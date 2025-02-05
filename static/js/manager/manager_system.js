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


    $('.changeMenu').on('click', function () {
        $('.rightbox_content').addClass('d-none')
        $('.rightbox_content.dashboard').removeClass('d-none')
    })

    if ($('input[name=is_admin]').val() == 'True') {

        $.ajax({
            url: "/get_system_stat",
            type: 'GET',
        })
            .done(function (response) {



                // 資料品質左側圓餅圖

                $('#container-data-quality').highcharts(Highcharts.merge(commonOptions, {
                    chart: {
                        type: 'pie'
                    },
                    tooltip: {
                        pointFormat: '<b>{point.y}筆 ({point.percentage:.1f}%)</b>'
                    },
                    accessibility: {
                        point: {
                            valueSuffix: '%'
                        }
                    },
                    plotOptions: {
                        pie: {
                            size: '100%',
                            allowPointSelect: true,
                            cursor: 'pointer',
                            dataLabels: {
                                enabled: false,
                            }
                        }
                    },
                    series: [{
                        name: '',
                        data: response.quality_data_list
                    }]
                }));

                // 右側文字
                $('#quality-stat-list').html('')
                for (ss of response.db_quality_stat){
                    $('#quality-stat-list').append(ss)
                }



                for (i of response.top3_taxon_list){
                    $('#rightsholder_taxon_group_top3').append(`<li><b>${i['rights_holder']}</b>：${i['data']}</li>`)
                }

                for (i of response.top5_family_list){
                    $('#rightsholder_family_top5').append(`<li><b>${i['rights_holder']}</b>：${i['data']}</li>`)
                }


                $('#container').highcharts(Highcharts.merge(commonOptions, {
                    chart: {
                        type: 'pie'
                    },
                    tooltip: {
                        pointFormat: '<b>{point.y}筆 ({point.percentage:.1f}%)</b>'
                    },
                    accessibility: {
                        point: {
                            valueSuffix: '%'
                        }
                    },
                    plotOptions: {
                        pie: {
                            size: '100%',
                            allowPointSelect: true,
                            cursor: 'pointer',
                            dataLabels: {
                                enabled: false,
                            }
                        }
                    },
                    series: [{
                        name: '',
                        colorByPoint: true,
                        data: response.data_total
                    }]
                }));



                // 資料查詢次數
                $('#container-search-times-stat').highcharts(Highcharts.merge(commonOptions, {
                    chart: {
                        type: "column",
                        },
                    yAxis: {
                        title: {
                            text: ''
                        },
                    },
                    xAxis: {
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
                        // headerFormat: '<b>{point.x}</b><br/>',
                        // pointFormat: '{series.name}: {point.y}'
                        pointFormat: '<b>{point.y}筆</b>'
                    },
                }));

                $('select[name=search-times-stat-year], select[name=search-times-stat-rightsholder]').on('change', function(){

                    if ($('select[name=search-times-stat-rightsholder]').find(':selected').val() == 'total'){
                        partner_str = '&group=total'
                    } else {
                        partner_str = '&rights_holder=' + $('select[name=search-times-stat-rightsholder]').find(':selected').val() 
                    }

                    $.ajax({
                        url:  `/get_data_stat?type=search_times&year=${$('select[name=search-times-stat-year]').find(':selected').val()}${partner_str}`,
                        type: 'GET',
                    })
                    .done(function(response){
                        let search_times_chart = $('#container-search-times-stat').highcharts()

                        while (search_times_chart.series.length) {
                            search_times_chart.series[0].remove();
                            }

                            search_times_chart.xAxis[0].setCategories(response.categories, false);

                        for (i of response.data ) {
                            search_times_chart.addSeries(i)
                        }


                    })
                    .fail(function (xhr, status, errorThrown) {
                        alert(gettext('發生未知錯誤！請聯絡管理員'))
                        console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
                    })

                })

                // 起始狀態
                $('select[name=search-times-stat-year]').trigger('change')



                // 資料下載次數
                $('#container-download-times-stat').highcharts(Highcharts.merge(commonOptions, {
                    chart: {
                        type: "column",
                    },
                    yAxis: {
                        title: {
                            text: ''
                        },
                    },
                    xAxis: {
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
                        // headerFormat: '<b>{point.x}</b><br/>',
                        // pointFormat: '{series.name}: {point.y}'
                        pointFormat: '<b>{point.y}筆</b>'
                    },
                }));

                $('select[name=download-times-stat-year],  select[name=download-times-stat-rightsholder]').on('change', function(){


                    if ($('select[name=download-times-stat-rightsholder]').find(':selected').val() == 'total'){
                        partner_str = '&group=total'
                    } else {
                        partner_str = '&rights_holder=' + $('select[name=download-times-stat-rightsholder]').find(':selected').val() 
                    }


                    $.ajax({
                        url:  `/get_data_stat?type=download_times&year=${$('select[name=download-times-stat-year]').find(':selected').val()}${partner_str}`,
                        type: 'GET',
                    })
                    .done(function(response){
                        let download_times_chart = $('#container-download-times-stat').highcharts()

                        while (download_times_chart.series.length) {
                            download_times_chart.series[0].remove();
                        }

                        download_times_chart.xAxis[0].setCategories(response.categories, false);

                        for (i of response.data ) {
                            download_times_chart.addSeries(i)
                        }
                    })
                    .fail(function (xhr, status, errorThrown) {
                        alert(gettext('發生未知錯誤！請聯絡管理員'))
                        console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
                    })

                })

                // 起始狀態
                $('select[name=download-times-stat-year]').trigger('change')





                // 物種類群

                $('#container-taxon_group-stat').highcharts(Highcharts.merge(commonOptions, {
                    chart: {
                        type: 'pie'
                    },
                    tooltip: {
                        pointFormat: '<b>{point.y}筆 ({point.percentage:.1f}%)</b>'
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
                                        url:  `/get_taxon_group_list?name=${now_name}`,
                                        type: 'GET',
                                    })
                                    .done(function(resp){
                                        $('#taxon_group-stat-title').html('[ ' + now_name + ' ]')
                                        $('#taxon_group-stat-list').html('')
                                        if (resp.length > 0){
                                            for (i of resp){
                                                $('#taxon_group-stat-list').append(`<li><a href="/media/taxon_stat/${i.rights_holder}_${now_name}.csv">${i.rights_holder}：${i.count} 筆</a><br><span class="small-gray-text">佔入口網臺灣${now_name}資料筆數 ${i.data_percent}%，佔TaiCOL臺灣${now_name}物種數 ${i.taiwan_percent}%</span></li>`)
                                            }
                                        } else {
                                            $('#taxon_group-stat-list').html('無資料')
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
    
    

                // 影像資料筆數
                $('#container-image-stat').highcharts(Highcharts.merge(commonOptions, {
                    chart: {
                        type: 'pie'
                    },
                    tooltip: {
                        pointFormat: '<b>{point.y}筆 ({point.percentage:.1f}%)</b>'
                    },
                    accessibility: {
                        point: {
                            valueSuffix: '%'
                        }
                    },
                    plotOptions: {
                        pie: {
                            size: '100%',
                            allowPointSelect: true,
                            cursor: 'pointer',
                            dataLabels: {
                                enabled: false,
                            }
                        }
                    },
                    series: [{
                        name: '',
                        colorByPoint: true,
                        data: response.image_data_total
                    }]
                }));

                // TaiCOL對應狀況
                $('#container2').highcharts(Highcharts.merge(commonOptions, {
                    chart: {
                        type: 'pie'
                    },
                    tooltip: {
                        pointFormat: '<b>{point.y}筆 ({point.percentage:.1f}%)</b>'
                    },
                    accessibility: {
                        point: {
                            valueSuffix: '%'
                        }
                    },
                    plotOptions: {
                        pie: {
                            size: '100%',
                            colors: ['#ddd', '#C65454'],
                            allowPointSelect: true,
                            cursor: 'pointer',
                            dataLabels: {
                                enabled: true,
                                format: '<b>{point.name}</b>: {point.percentage:.1f} %'
                            }
                        }
                    },
                    series: [{
                        name: 'Brands',
                        colorByPoint: true,
                        data: [{
                            name: '有對應',
                            y: response.has_taxon,
                            sliced: true,
                            selected: true
                        }, {
                            name: '無對應',
                            y: response.no_taxon
                        }]
                    }]
                }));


            })
            .fail(function (xhr, status, errorThrown) {
                alert(gettext('發生未知錯誤！請聯絡管理員'))
                console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
            })

            // 關鍵字
            $('select[name=keyword-stat-year], select[name=keyword-stat-month]').on('change', function(){
                $.ajax({
                    url:  `/get_keyword_stat?year=${$('select[name=keyword-stat-year]').find(':selected').val()}&month=${$('select[name=keyword-stat-month]').find(':selected').val()}`,
                    type: 'GET',
                })
                .done(function(response){
                    $('#keyword-stat-list').html('')
                    if (response.length > 0){
                        for (i of response){
                            $('#keyword-stat-list').append(`<li>${i.keyword} (${i.count})</li>`)
                        }
                    } else {
                        $('#keyword-stat-list').html('無資料')
                    }
                })
                .fail(function (xhr, status, errorThrown) {
                    alert(gettext('發生未知錯誤！請聯絡管理員'))
                    console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
                })
            })

            // 起始狀態
            $('select[name=keyword-stat-year]').trigger('change')

            // 名錄下載次數
            $('#container-checklist-stat').highcharts(Highcharts.merge(commonOptions, {

                chart: {
                    type: "column",
                  },
                yAxis: {
                    title: {
                        text: '下載次數'
                    }
                },
                xAxis: {
                    categories: [],
                },
                plotOptions: {
                    line: {
                        dataLabels: {
                            enabled: true
                        },
                    }
                },
                series: [{
                    color: "#9fc5e8",
                }],
                tooltip: {
                    pointFormat: '<b>{point.y}次</b>'
                },
            }));

            $('select[name=checklist-stat-year]').on('change', function(){
                $.ajax({
                    url:  `/get_checklist_stat?year=${$('select[name=checklist-stat-year]').find(':selected').val()}`,
                    type: 'GET',
                })
                .done(function(response){
                    checklist_chart = $('#container-checklist-stat').highcharts()
                    checklist_chart.update({series: [{ data: response.data }]});
                    checklist_chart.xAxis[0].update({categories: response.categories});
                })
                .fail(function (xhr, status, errorThrown) {
                    alert(gettext('發生未知錯誤！請聯絡管理員'))
                    console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
                })
            })

            // 起始狀態
            $('select[name=checklist-stat-year]').trigger('change')


            // 資料累積筆數
            $('#container-data-stat').highcharts(Highcharts.merge(commonOptions, {
                chart: {
                    type: "column",
                  },
                yAxis: {
                    title: {
                        text: ''
                    }
                },
                xAxis: {
                    categories: [],
                    labels: {
                        rotation: -45
                    }    
                },
                plotOptions: {
                    line: {
                        dataLabels: {
                            enabled: true
                        },
                    }
                },
                series: [{
                    color: "#9fc5e8",
                }],
                tooltip: {
                    pointFormat: '<b>{point.y}筆</b>'
                },
            }));

            $('select[name=data-stat-year], select[name=data-stat-rightsholder]').on('change', function(){
                $.ajax({
                    url:  `/get_data_stat?type=data&year=${$('select[name=data-stat-year]').find(':selected').val()}&rights_holder=${$('select[name=data-stat-rightsholder]').find(':selected').val()}`,
                    type: 'GET',
                })
                .done(function(response){
                    let data_chart = $('#container-data-stat').highcharts()
                    data_chart.update({series: [{ data: response.data }]});
                    data_chart.xAxis[0].update({categories: response.categories});
                })
                .fail(function (xhr, status, errorThrown) {
                    alert(gettext('發生未知錯誤！請聯絡管理員'))
                    console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
                })

            })

            // 起始狀態
            $('select[name=data-stat-year]').trigger('change')


            // 資料查詢筆數
            $('#container-search-stat').highcharts(Highcharts.merge(commonOptions, {
                chart: {
                    type: "column",
                  },
                yAxis: {
                    title: {
                        text: ''
                    }
                },
                xAxis: {
                    categories: [],
                },
                plotOptions: {
                    line: {
                        dataLabels: {
                            enabled: true
                        },
                    }
                },
                series: [{
                    color: "#3B8D70",
                }],
                tooltip: {
                    pointFormat: '<b>{point.y}筆</b>'
                },
            }));

            $('select[name=search-stat-year], select[name=search-stat-rightsholder]').on('change', function(){
                $.ajax({
                    url:  `/get_data_stat?type=search&year=${$('select[name=search-stat-year]').find(':selected').val()}&rights_holder=${$('select[name=search-stat-rightsholder]').find(':selected').val()}`,
                    type: 'GET',
                })
                .done(function(response){
                    let search_chart = $('#container-search-stat').highcharts()
                    search_chart.update({series: [{ data: response.data }]});
                    search_chart.xAxis[0].update({categories: response.categories});
                })
                .fail(function (xhr, status, errorThrown) {
                    alert(gettext('發生未知錯誤！請聯絡管理員'))
                    console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
                })

            })

            // 起始狀態
            $('select[name=search-stat-year]').trigger('change')

            // 資料下載筆數
            $('#container-download-stat').highcharts(Highcharts.merge(commonOptions, {
                chart: {
                    type: "column",
                  },
                yAxis: {
                    title: {
                        text: ''
                    }
                },
                xAxis: {
                    categories: [],
                },
                plotOptions: {
                    line: {
                        dataLabels: {
                            enabled: true
                        },
                    }
                },
                series: [{
                    color: "#3B8D70",
                }],
                tooltip: {
                    pointFormat: '<b>{point.y}筆</b>'
                },
            }));

            $('select[name=download-stat-year], select[name=download-stat-rightsholder]').on('change', function(){
                $.ajax({
                    url:  `/get_data_stat?type=download&year=${$('select[name=download-stat-year]').find(':selected').val()}&rights_holder=${$('select[name=download-stat-rightsholder]').find(':selected').val()}`,
                    type: 'GET',
                })
                .done(function(response){
                    let download_chart = $('#container-download-stat').highcharts()
                    download_chart.update({series: [{ data: response.data }]});
                    download_chart.xAxis[0].update({categories: response.categories});
                })
                .fail(function (xhr, status, errorThrown) {
                    alert(gettext('發生未知錯誤！請聯絡管理員'))
                    console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
                })

            })

            // 起始狀態
            $('select[name=download-stat-year]').trigger('change')


            // 敏感資料被下載筆數
            $('#container-sensitive-stat').highcharts(Highcharts.merge(commonOptions, {
                chart: {
                    type: "column",
                    },
                yAxis: {
                    title: {
                        text: '累積筆數'
                    }
                },
                xAxis: {
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
                    // headerFormat: '<b>{point.x}</b><br/>',
                    // pointFormat: '{series.name}: {point.y}'
                    pointFormat: '<b>{point.y}筆</b>'
                },
            }));

            $('select[name=sensitive-stat-year], select[name=sensitive-stat-rightsholder]').on('change', function(){


                if ($('select[name=sensitive-stat-rightsholder]').find(':selected').val() == 'total'){
                    partner_str = '&group=total'
                } else {
                    partner_str = '&rights_holder=' + $('select[name=sensitive-stat-rightsholder]').find(':selected').val() 
                }

                $.ajax({
                    url:  `/get_data_stat?type=sensitive&year=${$('select[name=sensitive-stat-year]').find(':selected').val()}${partner_str}`,
                    type: 'GET',
                })
                .done(function(response){
                        
                    let sensitive_chart = $('#container-sensitive-stat').highcharts()

                    while (sensitive_chart.series.length) {
                        sensitive_chart.series[0].remove();
                    }

                    sensitive_chart.xAxis[0].setCategories(response.categories, false);

                    for (i of response.data ) {
                        sensitive_chart.addSeries(i)
                    }
                })
                .fail(function (xhr, status, errorThrown) {
                    alert(gettext('發生未知錯誤！請聯絡管理員'))
                    console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
                })

            })

            // 起始狀態
            $('select[name=sensitive-stat-year]').trigger('change')

            

            // 資料時間空缺 - 年 - 所屬單位

            $('#container-partner-temporal-year-stat').highcharts(Highcharts.merge(commonOptions, {
                chart: {
                    type: "column",
                    },
                yAxis: {
                    title: {
                        text: '筆數'
                    }
                },
                xAxis: {
                    title: {
                        text: '年'
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
                        text: '筆數'
                    }
                },
                xAxis: {
                    title: {
                        text: '月'
                    },
                    categories: [],
                    labels: {
                        rotation: -45
                    }    
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
            
            $('select[name=partner-temporal-taxonGroup], select[name=temporal-stat-rightsholder]').on('change', function(){
                updatePartnerTemporal(PartnerTemporalYearSlider);
            })

            // 起始狀態
            $('select[name=partner-temporal-taxonGroup]').trigger('change')


    }


    $(".mb_fixed_btn").on("click", function (event) {
        $(".mbmove").toggleClass("open");
        $(this).toggleClass("now");
    });

    $(".rd_click").on("click", function (event) {
        $(".rd_click").closest("li").removeClass("now");
        $(this).closest("li").toggleClass("now");
        $(this).closest("li").find(".second_menu").slideToggle();
    });

    $(".second_menu a").on("click", function (event) {
        $(this).parent().parent().parent('ul').children('li.now').removeClass("now");
        $(".second_menu a").removeClass("now");
        $(this).addClass("now")
        $(this).parent().parent('li').addClass('now')
    });

})


function updatePartnerTemporal(PartnerTemporalYearSlider){

    if ($('select[name=temporal-stat-rightsholder]').find(':selected').val() == 'total'){
        partner_str = 'group=total'
    } else {
        partner_str = 'rights_holder=' + $('select[name=temporal-stat-rightsholder]').find(':selected').val() 
    }


    $.ajax({
        url:  `/get_temporal_stat?where=system&rights_holder=${$('select[name=temporal-stat-rightsholder]').find(':selected').val() }&taxon_group=${$('select[name=partner-temporal-taxonGroup]').find(':selected').val()}&start_year=${PartnerTemporalYearSlider.noUiSlider.get()[0]}&end_year=${PartnerTemporalYearSlider.noUiSlider.get()[1]}`,
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

// let portal_map = L.map('portal-map', {gestureHandling: true, minZoom: 2}).setView([23.5, 121.2], 7);
let partner_map = L.map('partner-map', {gestureHandling: true, minZoom: 2}).setView([23.5, 121.2], 7);

var southWest = L.latLng(-89.98155760646617, -179.9);
var northEast = L.latLng(89.99346179538875, 179.9);
var bounds = L.latLngBounds(southWest, northEast);

// portal_map.setMaxBounds(bounds);
// portal_map.on('drag', function() {
//     portal_map.panInsideBounds(bounds, { animate: false });
// });

partner_map.setMaxBounds(bounds);
partner_map.on('drag', function() {
    partner_map.panInsideBounds(bounds, { animate: false });
});



var legend = L.control({position: 'bottomright'});

legend.onAdd = function (map) {
    var div = L.DomUtil.create('div', 'info legend map-legend'),
        grades = [1, 10, 100, 1000, 5000, 10000, 50000, 100000]
    div.innerHTML += `<div class="ml-5px mb-5">${gettext('資料筆數')}</div>`
    for (var i = 0; i < grades.length; i++) {
        div.innerHTML +=
            `<div class="d-flex-ai-c"><div class="count-${grades[i]}"></div>` +
            grades[i] + (grades[i + 1] ? '&ndash;' + grades[i + 1] + '<br>' : '+') 
            + '</div>'
    }
    return div;
};

legend.addTo(partner_map);

// L.tileLayer('https://{s}.tile.osm.org/{z}/{x}/{y}.png', {
//     attribution: '&copy; <a href="https://osm.org/copyright">OpenStreetMap</a> contributors'
// }).addTo(portal_map);

L.tileLayer('https://{s}.tile.osm.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://osm.org/copyright">OpenStreetMap</a> contributors'
}).addTo(partner_map);


// portal_map.on('zoomend', function zoomendEvent(ev) {
//     drawMapGrid(current_map=portal_map,group='total')
// });


// portal_map.on('dragend', function zoomendEvent(ev) {
//     drawMapGrid(current_map=portal_map,group='total')
// });


partner_map.on('zoomend', function zoomendEvent(ev) {
    drawMapGrid(current_map=partner_map,group=$('input[name=current_group]').val())
});


partner_map.on('dragend', function zoomendEvent(ev) {
    drawMapGrid(current_map=partner_map,group=$('input[name=current_group]').val())
});


// $('select[name=portal-spatial-taxonGroup]').on('change', function(){
//     drawMapGrid(current_map=portal_map,group='total')
// })

// // 起始
// $('select[name=portal-spatial-taxonGroup]').trigger('change')

$('select[name=partner-spatial-taxonGroup], select[name=spatial-stat-rightsholder]').on('change', function(){
    drawMapGrid(current_map=partner_map,group=$('input[name=current_group]').val())
})

// 起始
$('select[name=partner-spatial-taxonGroup]').trigger('change')

// 統一畫5公里網格
// TODO 這邊還要加上taxon group
function drawMapGrid(current_map, group){

    console.log('hey');

    // if (group == 'total'){
    //     taxon_group = $('select[name=portal-spatial-taxonGroup]').find(':selected').val()
    // } else {
    taxon_group = $('select[name=partner-spatial-taxonGroup]').find(':selected').val()

    console.log(taxon_group)
    // }
    
    // $('.loading_area').removeClass('d-none')

    $('.loading_area_partial').removeClass('d-none')
    $('.spatial-area-div').addClass('d-none')

    $(`.resultG_5_${group}`).remove()


    $.ajax({
        url: "/get_map_grid",
        data: `rights_holder=${$('select[name=spatial-stat-rightsholder]').find(':selected').val()}&taxonGroup=${taxon_group}&grid=5&map_bound=` + getWKTMap(current_map) + '&csrfmiddlewaretoken=' + $csrf_token,
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

