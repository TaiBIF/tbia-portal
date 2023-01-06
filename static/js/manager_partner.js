var $csrf_token = $('[name="csrfmiddlewaretoken"]').attr("value");

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

    if ($('input[name=is_partner]').val()=='True'){

        $.ajax({
            url: "/get_partner_stat?partner_group=" + $('input[name=partner_group]').val(),
            type: 'GET',
        })
        .done(function(response) {
            Highcharts.setOptions({
                lang: {
                    thousandsSep: ","
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
                        colors: ['#76A578','#DEE9DE','#3F5146','#E2A460','#f4e2c7','#888','#ead065',
                        '#555','#3B86C0','#304237','#C65454','#ccc' ],
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
            alert('發生未知錯誤！請聯絡管理員')
            console.log( 'Error: ' + errorThrown + 'Status: ' + xhr.status)
        })  
    }

})

function getNoTaxonCSV(){
    $.ajax({
        url: "/generate_no_taxon_csv",
        data: {'group': $('input[name=partner_group]').val(), csrfmiddlewaretoken: $csrf_token},
        type: 'POST',
        dataType : 'json',
    })
    .done(function(response) {
        alert(response.url)
    })
    .fail(function( xhr, status, errorThrown ) {
        alert('發生未知錯誤！請聯絡管理員')
        console.log( 'Error: ' + errorThrown + 'Status: ' + xhr.status)
    })  
}


function updateInfo(){
    // remove all notice first
    $('.noticbox').css('display','none')

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
    
    if (checked){
        $.ajax({
            url: "/update_partner_info",
            data: $('#updateForm').serialize(),
            type: 'POST',
            dataType : 'json',
        })
        .done(function(response) {
            alert(response.message)
            if (response.message=='修改完成！'){
                window.location = '/'
            }
        })
        .fail(function( xhr, status, errorThrown ) {
            alert('發生未知錯誤！請聯絡管理員')
            console.log( 'Error: ' + errorThrown + 'Status: ' + xhr.status)
        })  
    }
}
