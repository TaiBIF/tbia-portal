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

                console.log(response.taxon_group_stat)

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


