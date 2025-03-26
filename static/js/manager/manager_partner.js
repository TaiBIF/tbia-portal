var $csrf_token = $('[name="csrfmiddlewaretoken"]').attr("value");

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

    $('.exportPortalKML').on('click', function(){
        exportToKML(window.portal_layer)
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


    var PortalTemporalYearSlider = document.getElementById('portal-temporal-year-slider');

    noUiSlider.create(PortalTemporalYearSlider, {
        start: [1900, new Date().getFullYear()],
        range: { min: 1900, max: new Date().getFullYear() },
        connect: true,
        step: 1,
        tooltips: true,
        format: SliderFormat,
    });
    
    PortalTemporalYearSlider.noUiSlider.on('change', function( values, handle ) {
        updatePortalTemporal(PortalTemporalYearSlider);
    });

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

    if ($('input[name=is_partner]').val() == 'True') {

        $.ajax({
            url: "/get_partner_stat?partner_id=" + $('input[name=partner_id]').val(),
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
                                    url:  `/get_taxon_group_list?name=${now_name}&group=${$('input[name=current_group]').val()}`,
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

            
        })
        .fail(function (xhr, status, errorThrown) {
            alert(gettext('發生未知錯誤！請聯絡管理員'))
            console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
        })



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
                pointFormat: '<b>{point.y}次</b>'
            },
        }));

        $('select[name=search-times-stat-year]').on('change', function(){
            $.ajax({
                url:  `/get_data_stat?type=search_times&year=${$('select[name=search-times-stat-year]').find(':selected').val()}&group=${$('input[name=current_group]').val()}`,
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


        // 資料查詢筆數
        $('#container-search-stat').highcharts(Highcharts.merge(commonOptions, {
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

        $('select[name=search-stat-year]').on('change', function(){
            $.ajax({
                url:  `/get_data_stat?type=search&year=${$('select[name=search-stat-year]').find(':selected').val()}&group=${$('input[name=current_group]').val()}`,
                type: 'GET',
            })
            .done(function(response){
                let search_chart = $('#container-search-stat').highcharts()

                while (search_chart.series.length) {
                    search_chart.series[0].remove();
                    }

                search_chart.xAxis[0].setCategories(response.categories, false);

                for (i of response.data ) {
                    search_chart.addSeries(i)
                }


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

        $('select[name=download-stat-year]').on('change', function(){
            $.ajax({
                url:  `/get_data_stat?type=download&year=${$('select[name=download-stat-year]').find(':selected').val()}&group=${$('input[name=current_group]').val()}`,
                type: 'GET',
            })
            .done(function(response){
                let download_chart = $('#container-download-stat').highcharts()

                while (download_chart.series.length) {
                    download_chart.series[0].remove();
                    }

                download_chart.xAxis[0].setCategories(response.categories, false);

                for (i of response.data ) {
                    download_chart.addSeries(i)
                }
            })
            .fail(function (xhr, status, errorThrown) {
                alert(gettext('發生未知錯誤！請聯絡管理員'))
                console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
            })

        })

        // 起始狀態
        $('select[name=download-stat-year]').trigger('change')

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
                pointFormat: '<b>{point.y}次</b>'
            },
        }));

        $('select[name=download-times-stat-year]').on('change', function(){
            $.ajax({
                url:  `/get_data_stat?type=download_times&year=${$('select[name=download-times-stat-year]').find(':selected').val()}&group=${$('input[name=current_group]').val()}`,
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



        // 資料累積筆數
        $('#container-data-stat').highcharts(Highcharts.merge(commonOptions, {
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
                // headerFormat: '<b>{point.x}</b><br/>',
                // pointFormat: '{series.name}: {point.y}'
                pointFormat: '<b>{point.y}筆</b>'
            },
        }));

        $('select[name=data-stat-year]').on('change', function(){
            $.ajax({
                url:  `/get_data_stat?type=data&year=${$('select[name=data-stat-year]').find(':selected').val()}&group=${$('input[name=current_group]').val()}`,
                type: 'GET',
            })
            .done(function(response){
                    
                let data_chart = $('#container-data-stat').highcharts()

                while (data_chart.series.length) {
                    data_chart.series[0].remove();
                }

                data_chart.xAxis[0].setCategories(response.categories, false);

                for (i of response.data ) {
                    data_chart.addSeries(i)
                }
            })
            .fail(function (xhr, status, errorThrown) {
                alert(gettext('發生未知錯誤！請聯絡管理員'))
                console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
            })

        })
        // 起始狀態
        $('select[name=data-stat-year]').trigger('change')

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

        $('select[name=sensitive-stat-year]').on('change', function(){
            $.ajax({
                url:  `/get_data_stat?type=sensitive&year=${$('select[name=sensitive-stat-year]').find(':selected').val()}&group=${$('input[name=current_group]').val()}`,
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


        //

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
                pointFormat: '<b>{point.y}筆</b>'
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
                // pointFormat: '{point.y} ' + gettext('筆')
                pointFormat: '<b>{point.y}筆</b>'
            },
        }));
        
        $('select[name=partner-temporal-taxonGroup]').on('change', function(){
            updatePartnerTemporal(PartnerTemporalYearSlider);
        })

        // 起始狀態
        $('select[name=partner-temporal-taxonGroup]').trigger('change')

        // 資料時間空缺 - 年 - 入口網

        $('#container-portal-temporal-year-stat').highcharts(Highcharts.merge(commonOptions, {
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
                // headerFormat: '<b>{point.x}</b><br/>',
                // pointFormat: '{series.name}: {point.y}'
                pointFormat: '<b>{point.y}筆</b>'
            },
        }));
        
        // 資料時間空缺 - 月 - 入口網
        
        $('#container-portal-temporal-month-stat').highcharts(Highcharts.merge(commonOptions, {
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
                // headerFormat: '<b>{point.x}月</b><br/>',
                // pointFormat: '{series.name}: {point.y}'
                pointFormat: '<b>{point.y}筆</b>'
            },
        }));
        
        $('select[name=portal-temporal-taxonGroup]').on('change', function(){
            updatePortalTemporal(PortalTemporalYearSlider);
        })

        // 起始狀態
        $('select[name=portal-temporal-taxonGroup]').trigger('change')

    }

})


function updatePartnerTemporal(PartnerTemporalYearSlider){
    $.ajax({
        url:  `/get_temporal_stat?group=${$('input[name=current_group]').val()}&taxon_group=${$('select[name=partner-temporal-taxonGroup]').find(':selected').val()}&start_year=${PartnerTemporalYearSlider.noUiSlider.get()[0]}&end_year=${PartnerTemporalYearSlider.noUiSlider.get()[1]}`,
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

function updatePortalTemporal(PortalTemporalYearSlider){
    $.ajax({
        url:  `/get_temporal_stat?group=total&taxon_group=${$('select[name=portal-temporal-taxonGroup]').find(':selected').val()}&start_year=${PortalTemporalYearSlider.noUiSlider.get()[0]}&end_year=${PortalTemporalYearSlider.noUiSlider.get()[1]}`,
        type: 'GET',
    })
    .done(function(response){

        // 年
         
        let portal_temporal_year_chart = $('#container-portal-temporal-year-stat').highcharts()

        while (portal_temporal_year_chart.series.length) {
            portal_temporal_year_chart.series[0].remove();
        }

        portal_temporal_year_chart.xAxis[0].setCategories(response.year_categories, false);

        for (i of response.year_data ) {
            portal_temporal_year_chart.addSeries(i)
        }

        // 月

        let portal_temporal_month_chart = $('#container-portal-temporal-month-stat').highcharts()

        while (portal_temporal_month_chart.series.length) {
            portal_temporal_month_chart.series[0].remove();
        }

        portal_temporal_month_chart.xAxis[0].setCategories(response.month_categories, false);

        for (i of response.month_data ) {
            portal_temporal_month_chart.addSeries(i)
        }

    })
    .fail(function (xhr, status, errorThrown) {
        alert(gettext('發生未知錯誤！請聯絡管理員'))
        console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
    })

}

function updateInfo() {
    // remove all notice first
    $('.noticbox').css('display', 'none')

    let checked = true;

    // 這邊的判斷不能直接用input -> 加上forloop counter?
    /*if (!$('input[name=link]').val()){ 
        $('input[name=link]').next('.noticbox').css('display','')
        checked = false
    }  

    if (!$('input[name=description]').val()){ 
        $('input[name=description]').next('.noticbox').css('display','')
        checked = false
    }  */

    if (checked) {
        $.ajax({
            url: "/update_partner_info",
            data: $('#updateForm').serialize(),
            type: 'POST',
            dataType: 'json',
        })
            .done(function (response) {
                alert(gettext(response.message))
                if (response.message == '修改完成！') {
                    window.location = '/'
                }
            })
            .fail(function (xhr, status, errorThrown) {
                alert(gettext('發生未知錯誤！請聯絡管理員'))
                console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
            })
    }
}


function syncMaps(sourceMap, targetMap) {
    // targetMap.off('moveend'); // 暫時取消事件以避免循環觸發
    targetMap.setView(sourceMap.getCenter(), sourceMap.getZoom(), { animate: false });
    // 兩個地圖都要畫
    // targetMap.on('moveend', () => syncMaps(targetMap, sourceMap)); // 再次添加事件
    let wkt_range = getWKTMap(sourceMap);

    drawMapGrid(current_map=portal_map,group='total',wkt_range=wkt_range)
    drawMapGrid(current_map=partner_map,group=$('input[name=current_group]').val(),wkt_range=wkt_range)

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

let portal_map = L.map('portal-map', {gestureHandling: true, minZoom: 2}).setView([23.5, 121.2], 7);
let partner_map = L.map('partner-map', {gestureHandling: true, minZoom: 2}).setView([23.5, 121.2], 7);

var southWest = L.latLng(-89.98155760646617, -179.9);
var northEast = L.latLng(89.99346179538875, 179.9);
var bounds = L.latLngBounds(southWest, northEast);

portal_map.setMaxBounds(bounds);
portal_map.on('drag', function() {
    portal_map.panInsideBounds(bounds, { animate: false });
});

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
var legend2 = L.control({position: 'bottomright'});

legend2.onAdd = function (map) {
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
legend2.addTo(portal_map);


L.tileLayer('https://{s}.tile.osm.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://osm.org/copyright">OpenStreetMap</a> contributors'
}).addTo(portal_map);

L.tileLayer('https://{s}.tile.osm.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://osm.org/copyright">OpenStreetMap</a> contributors'
}).addTo(partner_map);


portal_map.on('zoomend', function zoomendEvent(ev) {
    syncMaps(portal_map, partner_map)
});


portal_map.on('dragend', function zoomendEvent(ev) {
    syncMaps(portal_map, partner_map)
});


partner_map.on('zoomend', function zoomendEvent(ev) {
    syncMaps(partner_map, portal_map)
});


partner_map.on('dragend', function zoomendEvent(ev) {
    syncMaps(partner_map, portal_map)
});



$('select[name=portal-spatial-taxonGroup]').on('change', function(){
    // wkt_range = getWKTMap(portal_map)
    drawMapGrid(current_map=portal_map,group='total',wkt_range=getWKTMap(portal_map))
})

// 起始
$('select[name=portal-spatial-taxonGroup]').trigger('change')

$('select[name=partner-spatial-taxonGroup]').on('change', function(){
    drawMapGrid(current_map=partner_map,group=$('input[name=current_group]').val(),wkt_range=getWKTMap(partner_map))
})

// 起始
$('select[name=partner-spatial-taxonGroup]').trigger('change')

// 統一畫5公里網格
// TODO 這邊還要加上taxon group
function drawMapGrid(current_map, group, wkt_range){

    if (group == 'total'){
        $('.total.loading_area_partial').removeClass('d-none')
        $('.total-spatial-area-div').addClass('d-none')
        taxon_group = $('select[name=portal-spatial-taxonGroup]').find(':selected').val()
    } else {
        $('.loading_area_partial').not('.total').removeClass('d-none')
        $('.spatial-area-div').addClass('d-none')

        taxon_group = $('select[name=partner-spatial-taxonGroup]').find(':selected').val()
    }
    
    $(`.resultG_5_${group}`).remove()


    $.ajax({
        url: "/get_tw_grid",
        data: `group=${group}&taxonGroup=${taxon_group}&map_bound=` + wkt_range + '&csrfmiddlewaretoken=' + $csrf_token,
        type: 'POST',
        dataType: 'json',
    })
    .done(function (response) {
        if (group == 'total'){
            window.portal_layer = L.geoJSON(response, {className: `resultG_5_${group}`, style: style }).addTo(current_map);
            $('.total.loading_area_partial').addClass('d-none')
            $('.total-spatial-area-div').removeClass('d-none')
        } else {
            window.partner_layer = L.geoJSON(response, {className: `resultG_5_${group}`, style: style }).addTo(current_map);
            $('.loading_area_partial').not('.total').addClass('d-none')
            $('.spatial-area-div').removeClass('d-none')
        }
    })
    .fail(function (xhr, status, errorThrown) {
        if (xhr.status == 504) {
            alert(gettext('要求連線逾時'))
        } else {
            alert(gettext('發生未知錯誤！請聯絡管理員'))

        }
        console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
        $('.loading_area_partial, .total.loading_area_partial').addClass('d-none')
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

