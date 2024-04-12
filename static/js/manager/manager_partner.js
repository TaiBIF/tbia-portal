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

$(document).ready(function () {

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
                                            $('#taxon_group-stat-list').append(`<li>${i.rights_holder}：${i.count} (${i.percent}%)</li>`)
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
                            enabled: true
                        },
                    },
                },
                tooltip: {
                    headerFormat: '<b>{point.x}</b><br/>',
                    pointFormat: '{series.name}: {point.y}'
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
                            enabled: true
                        },
                    },
                },
                tooltip: {
                    headerFormat: '<b>{point.x}</b><br/>',
                    pointFormat: '{series.name}: {point.y}'
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
                },
                plotOptions: {
                    column: {
                        stacking: 'normal',
                        dataLabels: {
                            enabled: true
                        },
                    },
                },
                tooltip: {
                    headerFormat: '<b>{point.x}</b><br/>',
                    pointFormat: '{series.name}: {point.y}'
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

    }

})


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
