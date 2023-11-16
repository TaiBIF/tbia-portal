$(document).ready(function () {

    $('.changeMenu').on('click', function(){
        $('.rightbox_content').addClass('d-none')
        $('.rightbox_content.dashboard').removeClass('d-none')
    })

    if ($('input[name=is_admin]').val()=='True'){

        $.ajax({
            url: "/get_system_stat",
            type: 'GET',
        })
        .done(function(response) {
            Highcharts.setOptions({
                lang: {
                    thousandsSep: ","
                },
                credits: {
                    enabled: false
                }
            })
            Highcharts.chart('container', {
                chart: {
                    plotBackgroundColor: null,
                    plotBorderWidth: null,
                    plotShadow: false,
                    type: 'pie'
                },
                navigation: {
                    buttonOptions: {
                        enabled: false
                        }
                },                
                title: {
                    text: ''
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
                        size:'100%',
                        /*
                        colors: ['#76A578','#DEE9DE','#3F5146','#E2A460','#f4e2c7','#888','#ead065',
                        '#555','#3B86C0','#304237','#C65454','#ccc' ],*/
                        allowPointSelect: true,
                        cursor: 'pointer',
                        dataLabels: {
                            enabled: true,
                            format: '<b>{point.name}</b>: {point.percentage:.1f} %'
                        }
                    }
                },
                series: [{
                    name: '',
                    colorByPoint: true,
                    data: response.data_total
                }]
            });
    
            Highcharts.chart('container2', {
                chart: {
                    plotBackgroundColor: null,
                    plotBorderWidth: null,
                    plotShadow: false,
                    type: 'pie'
                },
                navigation: {
                    buttonOptions: {
                        enabled: false
                    }
                },                
                title: {
                    text: ''
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
                        size:'100%',
                        colors: ['#ddd','#C65454'],
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
            });
        })
        .fail(function( xhr, status, errorThrown ) {
            alert($('input[name=unexpected-error-alert]').val())
            console.log( 'Error: ' + errorThrown + 'Status: ' + xhr.status)
        })  
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


