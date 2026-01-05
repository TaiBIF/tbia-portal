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


function updatePartnerStat(){
            $.ajax({
            // url: "/get_partner_stat?partner_id=" + $('input[name=partner_id]').val(),
            url: "/get_partner_stat?rights_holder=" + $('select[name=rightsholder-select]').find(':selected').val(),
            type: 'GET',
        })
        .done(function (response) {


            $('.download_taxon_a').attr('href', response.download_url)

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
                        allowPointSelect: true,
                        cursor: 'pointer',
                        dataLabels: {
                            enabled: false,
                        },
                        center: ['50%', '50%'],
                        slicedOffset: 0,
                        point: {
                            events: {
                                click: function () {
                                    // 移除之前的中間文字
                                    if (this.series.chart.centerText) {
                                        this.series.chart.centerText.destroy();
                                    }
                                    // 在中間顯示點擊的片段資訊
                                    this.series.chart.centerText = this.series.chart.renderer.text(
                                        this.name + '<br/>' + this.y + '筆<br/>(' + this.percentage.toFixed(1) + '%)',
                                        this.series.chart.plotLeft + this.series.chart.plotWidth / 2,
                                        this.series.chart.plotTop + this.series.chart.plotHeight / 2 - 10,
                                        true
                                    ).attr({
                                        align: 'center'
                                    }).css({
                                        fontSize: '14px',
                                        fontWeight: 'bold',
                                        color: '#333',
                                        textAlign: 'center'
                                    }).add();
                                }
                            }
                        }
                    }
                },
                colors: ['#FFD700', '#C0C0C0', '#CD7F32', '#B8860B', '#A9A9A9', '#8B4513'],
                series: [{
                    // name: '系統整體',
                    data: response.quality_data_list_system, // 你的原始資料
                    size: '100%',
                    innerSize: '60%'
                }, {
                    // name: '某單位',
                    data: response.quality_data_list_holder, // 你的原始資料
                    size: '60%',
                    innerSize: '40%'
                }]
            }));

        // $('#container-data-quality').highcharts(Highcharts.merge(commonOptions, {
            //     chart: {
            //         type: 'pie'
            //     },
            //     tooltip: {
            //         pointFormat: '<b>{point.y}筆 ({point.percentage:.1f}%)</b>'
            //     },
            //     accessibility: {
            //         point: {
            //             valueSuffix: '%'
            //         }
            //     },
            //     plotOptions: {
            //         pie: {
            //             size: '100%',
            //             innerSize: '50%', // 甜甜圈內圈大小
            //             allowPointSelect: true,
            //             cursor: 'pointer',
            //             dataLabels: {
            //                 enabled: false,
            //             },
            //             center: ['50%', '50%'],
            //             slicedOffset: 0, // 片段不會移動
            //             point: {
            //                 events: {
            //                     click: function () {
            //                         // 移除之前的中間文字
            //                         if (this.series.chart.centerText) {
            //                             this.series.chart.centerText.destroy();
            //                         }
            //                         // 在中間顯示點擊的片段資訊
            //                         this.series.chart.centerText = this.series.chart.renderer.text(
            //                             this.name + '<br/>' + this.y + '筆<br/>(' + this.percentage.toFixed(1) + '%)',
            //                             this.series.chart.plotLeft + this.series.chart.plotWidth / 2,
            //                             this.series.chart.plotTop + this.series.chart.plotHeight / 2 - 10,
            //                             true
            //                         ).attr({
            //                             align: 'center'
            //                         }).css({
            //                             fontSize: '14px',
            //                             fontWeight: 'bold',
            //                             color: '#333',
            //                             textAlign: 'center'
            //                         }).add();
            //                     }
            //                 }
            //             }
            //         }
            //     },
            //     series: [{
            //         name: '',
            //         data: response.quality_data_list
            //     }]
            // }));

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
                        innerSize: '50%', // 甜甜圈內圈大小
                        allowPointSelect: true,
                        cursor: 'pointer',
                        dataLabels: {
                            enabled: false,
                        },
                        center: ['50%', '50%'],
                        slicedOffset: 0, // 片段不會移動
                        point: {
                            events: {
                                click: function () {
                                    // 移除之前的中間文字
                                    if (this.series.chart.centerText) {
                                        this.series.chart.centerText.destroy();
                                    }
                                    // 在中間顯示點擊的片段資訊
                                    this.series.chart.centerText = this.series.chart.renderer.text(
                                        this.name + '<br/>' + this.y + '筆<br/>(' + this.percentage.toFixed(1) + '%)',
                                        this.series.chart.plotLeft + this.series.chart.plotWidth / 2,
                                        this.series.chart.plotTop + this.series.chart.plotHeight / 2 - 10,
                                        true
                                    ).attr({
                                        align: 'center'
                                    }).css({
                                        fontSize: '14px',
                                        fontWeight: 'bold',
                                        color: '#333',
                                        textAlign: 'center'
                                    }).add();
                                }
                            }
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
                        innerSize: '50%', // 甜甜圈內圈大小
                        allowPointSelect: true,
                        cursor: 'pointer',
                        dataLabels: {
                            enabled: false,
                        },
                        center: ['50%', '50%'],
                        slicedOffset: 0, // 片段不會移動
                        point: {
                            events: {
                                click: function () {
                                    // 移除之前的中間文字
                                    if (this.series.chart.centerText) {
                                        this.series.chart.centerText.destroy();
                                    }
                                    // 在中間顯示點擊的片段資訊
                                    this.series.chart.centerText = this.series.chart.renderer.text(
                                        this.name + '<br/>' + this.y + '筆<br/>(' + this.percentage.toFixed(1) + '%)',
                                        this.series.chart.plotLeft + this.series.chart.plotWidth / 2,
                                        this.series.chart.plotTop + this.series.chart.plotHeight / 2 - 10,
                                        true
                                    ).attr({
                                        align: 'center'
                                    }).css({
                                        fontSize: '14px',
                                        fontWeight: 'bold',
                                        color: '#333',
                                        textAlign: 'center'
                                    }).add();
                                }
                            }
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
                        selected: true,
                        color: '#E6B8C4',
                    }, {
                        name: '無對應',
                        y: response.no_taxon,
                        color: '#ddd'
                    }]
                }]
            }));



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
                                    console.log('hi');
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
                    
                    let html = `${category}<br/>`;
                    
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
                        // let unitPercentage = unitPoints[0].series.options.unitPercentage || 0;
                        // let taiwanPercentage = unitPoints[0].series.options.taiwanPercentage || 0;
                        html += `<br><b>來源資料庫：</b><br>${Highcharts.numberFormat(unitCount, 0)} 筆 (${unitTotalPercentage}%)<br>`;
                        // html += `佔入口網臺灣${category}資料筆數 ${unitPercentage}%<br>佔TaiCOL臺灣${category}物種數 ${taiwanPercentage}%`;
                    }

                    // html += `<br><a href="#">📥 下載清單</a>`;


                    return html;
                }
            },
            accessibility: {
                point: {
                    valueSuffix: '%'
                }
            },
            xAxis: {
                categories: ['昆蟲', '蜘蛛', '魚類', '爬蟲類', '兩棲類', '鳥類', '哺乳類', 
                            '維管束植物', '蕨類植物', '苔蘚植物', '藻類', '病毒', '細菌', '真菌', '其他'],
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
                    text: '資料筆數'
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
                    // cursor: 'pointer',
                    dataLabels: {
                        enabled: false
                    },
                    
                }
            },
            series: response.taxon_group_stat
        }));


            // $('#container-taxon_group-stat').highcharts(Highcharts.merge(commonOptions, {
            //     chart: {
            //         type: 'pie'
            //     },
            //     tooltip: {
            //         pointFormat: '<b>{point.y}筆 ({point.percentage:.1f}%)</b>'
            //     },
            //     accessibility: {
            //         point: {
            //             valueSuffix: '%'
            //         }
            //     },
            //     plotOptions: {
            //         pie: {
            //             size: '90%',
            //             allowPointSelect: true,
            //             cursor: 'pointer',
            //             dataLabels: {
            //                 padding: 0,
            //                 style: {
            //                   fontSize: '10px'
            //                 }
            //             }
            //         },
            //     },
            //     series: [{
            //         name: '',
            //         colorByPoint: true,
            //         colors: ['#76A578','#DEE9DE','#3F5146','#E2A460','#f4e2c7','#888','#ead065',
            //         '#555','#3B86C0','#304237','#C65454','#ccc' ],
            //         data: response.taxon_group_stat,
            //         cursor: 'pointer',
            //         point: {
            //             events: {
            //                 click: function () {
            //                     let now_name = this.name
            //                     $.ajax({
            //                         url:  `/get_taxon_group_list?name=${now_name}&group=${$('input[name=current_group]').val()}`,
            //                         type: 'GET',
            //                     })
            //                     .done(function(resp){
            //                         $('#taxon_group-stat-title').html('[ ' + now_name + ' ]')
            //                         $('#taxon_group-stat-list').html('')
            //                         if (resp.length > 0){
            //                             for (i of resp){
            //                                 $('#taxon_group-stat-list').append(`<li><a href="/media/taxon_stat/${i.rights_holder}_${now_name}.csv">${i.rights_holder}：${i.count} 筆</a><br><span class="small-gray-text">佔入口網臺灣${now_name}資料筆數 ${i.data_percent}%，佔TaiCOL臺灣${now_name}物種數 ${i.taiwan_percent}%</span></li>`)
            //                             }
            //                         } else {
            //                             $('#taxon_group-stat-list').html('無資料')
            //                         }
            //                     })
            //                     .fail(function (xhr, status, errorThrown) {
            //                         alert(gettext('發生未知錯誤！請聯絡管理員'))
            //                         console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
            //                     })
                
            //                 }
            //             }
            //         }

            //     }]
            // }));


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
                        innerSize: '50%', // 甜甜圈內圈大小
                        allowPointSelect: true,
                        cursor: 'pointer',
                        dataLabels: {
                            enabled: false,
                        },
                        center: ['50%', '50%'],
                        slicedOffset: 0, // 片段不會移動
                        point: {
                            events: {
                                click: function () {
                                    // 移除之前的中間文字
                                    if (this.series.chart.centerText) {
                                        this.series.chart.centerText.destroy();
                                    }
                                    // 在中間顯示點擊的片段資訊
                                    this.series.chart.centerText = this.series.chart.renderer.text(
                                        this.name + '<br/>' + this.y + '筆<br/>(' + this.percentage.toFixed(1) + '%)',
                                        this.series.chart.plotLeft + this.series.chart.plotWidth / 2,
                                        this.series.chart.plotTop + this.series.chart.plotHeight / 2 - 10,
                                        true
                                    ).attr({
                                        align: 'center'
                                    }).css({
                                        fontSize: '14px',
                                        fontWeight: 'bold',
                                        color: '#333',
                                        textAlign: 'center'
                                    }).add();
                                }
                            }
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

        // 以上為 get_partner_stat
}




$(document).ready(function () {

    updatePartnerStat()

    $('select[name=rightsholder-select]').on('change', function(){
        updatePartnerStat()
    })


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

    // if ($('input[name=is_partner]').val() == 'True') {



        // 使用者下載統計
        $('#container-user-download-stat').highcharts(Highcharts.merge(commonOptions, {
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
                labels: {
                    rotation: -45
                }
            },
            plotOptions: {
                column: {
                    stacking: 'normal',
                    color: '#9AC4E8',
                    dataLabels: {
                        enabled: false
                    },
                },
            },
            tooltip: {
                headerFormat: '',
                pointFormat: '<span style="color:{series.color}">{series.name}</span>: <b>{point.y}</b> 筆<br/>',
                footerFormat: '總計: <b>{point.total}</b> 筆',
                shared: true,
                useHTML: true
            },
        }));

        $('select[name=user-download-stat-year],select[name=user-download-stat-type]').on('change', function(){
            $.ajax({
                // url:  `/get_data_stat?type=search_times&year=${$('select[name=search-times-stat-year]').find(':selected').val()}&group=${$('input[name=current_group]').val()}`,
                url:  `/get_user_download_stat?type=${$('select[name=user-download-stat-type]').find(':selected').val()}&year=${$('select[name=user-download-stat-year]').find(':selected').val()}&rights_holder=${$('select[name=rightsholder-select]').find(':selected').val()}`,
                type: 'GET',
            })
            .done(function(response){
                let user_download_stat_chart = $('#container-user-download-stat').highcharts()

                while (user_download_stat_chart.series.length) {
                    user_download_stat_chart.series[0].remove();
                    }

                    user_download_stat_chart.xAxis[0].setCategories(response.categories, false);

                for (i of response.data ) {
                    user_download_stat_chart.addSeries(i)
                }


            })
            .fail(function (xhr, status, errorThrown) {
                alert(gettext('發生未知錯誤！請聯絡管理員'))
                console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
            })

        })

        // 起始狀態
        $('select[name=user-download-stat-year]').trigger('change')







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
                    color: '#9AC4E8',
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
                // url:  `/get_data_stat?type=search_times&year=${$('select[name=search-times-stat-year]').find(':selected').val()}&group=${$('input[name=current_group]').val()}`,
                url:  `/get_data_stat?type=search_times&year=${$('select[name=search-times-stat-year]').find(':selected').val()}&rights_holder=${$('select[name=rightsholder-select]').find(':selected').val()}`,
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
                    color: '#B2D4B2',
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
                // url:  `/get_data_stat?type=search&year=${$('select[name=search-stat-year]').find(':selected').val()}&group=${$('input[name=current_group]').val()}`,
                url:  `/get_data_stat?type=search&year=${$('select[name=search-stat-year]').find(':selected').val()}&rights_holder=${$('select[name=rightsholder-select]').find(':selected').val()}`,
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
                    color: '#E8C4AC', 
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
                // url:  `/get_data_stat?type=download&year=${$('select[name=download-stat-year]').find(':selected').val()}&group=${$('input[name=current_group]').val()}`,
                url:  `/get_data_stat?type=download&year=${$('select[name=download-stat-year]').find(':selected').val()}&rights_holder=${$('select[name=rightsholder-select]').find(':selected').val()}`,
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
                    color: '#D2C2E0',
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
                url:  `/get_data_stat?type=download_times&year=${$('select[name=download-times-stat-year]').find(':selected').val()}&rights_holder=${$('select[name=rightsholder-select]').find(':selected').val()}`,
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
                    color: '#C2D8D8',
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
                // url:  `/get_data_stat?type=data&year=${$('select[name=data-stat-year]').find(':selected').val()}&group=${$('input[name=current_group]').val()}`,
                url:  `/get_data_stat?type=data&year=${$('select[name=data-stat-year]').find(':selected').val()}&rights_holder=${$('select[name=rightsholder-select]').find(':selected').val()}`,
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
                    color: '#F2E394',
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
                // url:  `/get_data_stat?type=sensitive&year=${$('select[name=sensitive-stat-year]').find(':selected').val()}&group=${$('input[name=current_group]').val()}`,
                url:  `/get_data_stat?type=sensitive&year=${$('select[name=sensitive-stat-year]').find(':selected').val()}&rights_holder=${$('select[name=rightsholder-select]').find(':selected').val()}`,
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

    // }

})


function updatePartnerTemporal(PartnerTemporalYearSlider){
    $.ajax({
        // url:  `/get_temporal_stat?group=${$('input[name=current_group]').val()}&taxon_group=${$('select[name=partner-temporal-taxonGroup]').find(':selected').val()}&start_year=${PartnerTemporalYearSlider.noUiSlider.get()[0]}&end_year=${PartnerTemporalYearSlider.noUiSlider.get()[1]}`,
        url:  `/get_temporal_stat?rights_holder=${$('select[name=rightsholder-select]').find(':selected').val()}&taxon_group=${$('select[name=partner-temporal-taxonGroup]').find(':selected').val()}&start_year=${PartnerTemporalYearSlider.noUiSlider.get()[0]}&end_year=${PartnerTemporalYearSlider.noUiSlider.get()[1]}`,
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




function generateCategoryInfo(category, points, chart) {
    var systemPoints = points.filter(p => p.series.name.includes('-系統') && p.y > 0);
    var unitPoints = points.filter(p => p.series.name.includes('-單位') && p.y > 0);
    
    var html = `<p class="fs-18px">[ ${category} ]</p>`;
    
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
        html += `<p><b>來源資料庫：</b><br>${Highcharts.numberFormat(unitCount, 0)} 筆 (${unitTotalPercentage}%)<br>`;
        html += `<b>佔入口網臺灣${category}資料筆數：</b><br>${unitPercentage}%<br><b>佔TaiCOL臺灣${category}物種數：</b><br>${taiwanPercentage}%</p>`;
    }
    
    html += `<br><a href="/media/taxon_stat/${$('select[name=rightsholder-select]').find(':selected').val()}_${category}.csv">📥 下載比對結果清單</a>`;
    
    return html;

}
