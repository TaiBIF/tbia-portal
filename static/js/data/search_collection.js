var $csrf_token = $('[name="csrfmiddlewaretoken"]').attr("value");

let selectBox = new vanillaSelectBox("#rightsHolder", 
                {"placeHolder": "來源資料庫", search: true, disableSelectAll: true,
                    translations: { "all": "全部", "items": " 個選項", "selectAll": "全選", "clearAll": "重設"} 
                });

$('#rightsHolder').on('change', function(e){
    $(".loading_area").removeClass('d-none');
    e.preventDefault()
    let res = selectBox.getResult()
    let h_str = ''
    for(r of res) { 
        h_str += 'holder=' + r + '&'
    }
    $.ajax({
        url: "/change_dataset?" + h_str,
        dataType : 'json',
    })
    .done(function(response) {
        if (response.length > 0){
            selectBox2.enable()
            selectBox2.changeTree(response)
            if (window.has_par){
                selectBox2.setValue(window.d_list)
            }
        } else {
                selectBox2.disable()
        }
        $(".loading_area").addClass('d-none');
    })
    .fail(function(){
        $(".loading_area").addClass('d-none');
    })
})


let selectBox2 = new vanillaSelectBox("#datasetName",{"placeHolder":"資料集名稱",search:true, disableSelectAll: true,
translations: { "all": "全部", "items": " 個選項", "selectAll": "全選", "clearAll": "重設"} 
});

/*
let selectBox3 = new vanillaSelectBox("#sensitiveCategory",{"placeHolder":"敏感層級",search:false, disableSelectAll: true,
});*/

let selectBox4 = new vanillaSelectBox("#typeStatus",{"placeHolder":"標本類型",search:false, disableSelectAll: true,
});

let selectBox5 = new vanillaSelectBox("#taxonRank",{"placeHolder":"鑑定層級",search:false, disableSelectAll: true,
});

let selectBox6 = new vanillaSelectBox("#circle_radius",{"placeHolder":"半徑",search:false, disableSelectAll: true,
});
selectBox6.setValue('1')

let selectBox7 = new vanillaSelectBox("#has_image",{"placeHolder":"有無影像",search:false, disableSelectAll: true,
});

let selectBox8 = new vanillaSelectBox("#higherTaxa",
{
    "search": true,
    "placeHolder" : "較高分類群",
    "disableSelectAll": true,
    "remote": {
        "onSearch": doSearch, // used for search and init
        "onInitSize": 10, // if > 0 onSearch is used for init to populate le select element with the {onInitSize} first elements
        "onInit": inithigherTaxa,
    }
});

let selectBox9 = new vanillaSelectBox("#taxonGroup",{"placeHolder":"物種類群",search:false, disableSelectAll: true,
});

let selectBox10 = new vanillaSelectBox("#locality",
{
    "search": true,
    "placeHolder" : "採集地",
    "disableSelectAll": true,
    "remote": {
        "onSearch": doSearchLocality, // used for search and init
        "onInitSize": 10, // if > 0 onSearch is used for init to populate le select element with the {onInitSize} first elements
        "onInit": initLocality,
    },
    translations: { "all": "全部", "items": " 個選項", "selectAll": "全選", "clearAll": "重設"}
});

function doSearchLocality(what, datasize) {
    let valueProperty = "value";
    let textProperty = "text";
    
    return new Promise(function (resolve, reject) {
        var xhr = new XMLHttpRequest();
        xhr.overrideMimeType("application/json");
        xhr.open('GET','/get_locality?record_type=col&locality=' + what, true);
        xhr.onload = function () {
            if (this.status >= 200 && this.status < 300) {
                var data = JSON.parse(xhr.response);

                if (what == "" && datasize != undefined && datasize > 0) { // for init to show some data
                    data = data.slice(0, datasize);
                    data = data.map(function (x) {
                        return {
                            value: x[valueProperty],
                            text: x[textProperty]
                        }
                    });
                } else {
                    data = data.filter(function (x) {
                        let name = x[textProperty].toLowerCase();
                        what = what.toLowerCase();
                        if (name.slice(what).search(getVariants(what)) != -1)
                            return {
                                value: x[valueProperty],
                                text: x[textProperty]
                            }
                    });
                }
                //data = [{'value': '', 'text': '-- 不限 --'}].concat(data)
                resolve(data);
            } else {
                reject({
                    status: this.status,
                    statusText: xhr.statusText
                });
            }
        };
        xhr.onerror = function () {
            reject({
                status: this.status,
                statusText: xhr.statusText
            });
        };
        xhr.send();
    });
}

function initLocality(what, datasize){
    let valueProperty = "value";
    let textProperty = "text";
    let urlParams = new URLSearchParams(window.location.search);
    let keyword_list = urlParams.getAll('locality')

    return new Promise(function (resolve, reject) {
        var xhr = new XMLHttpRequest();
        xhr.overrideMimeType("application/json");
        xhr.open('GET','/get_locality_init?record_type=col&locality=' + keyword_list.join('&locality='), true);
        xhr.onload = function () {
            if (this.status >= 200 && this.status < 300) {
                var data = JSON.parse(xhr.response);
                if (what == "" && datasize != undefined && datasize > 0) { // for init to show some data
                    data = data.slice(0, datasize);
                    data = data.map(function (x) {
                        return {
                            value: x[valueProperty],
                            text: x[textProperty]
                        }
                    });
                } else {
                    data = data.filter(function (x) {
                        let name = x[textProperty].toLowerCase();
                        what = what.toLowerCase();
                        if (name.slice(what).search(getVariants(what)) != -1)
                            return {
                                value: x[valueProperty],
                                text: x[textProperty]
                            }
                    });
                }
                //data = [{'value': '', 'text': '-- 不限 --'}].concat(data)
                resolve(data);
            } else {
                reject({
                    status: this.status,
                    statusText: xhr.statusText
                });
            }
        };
        xhr.onerror = function () {
            reject({
                status: this.status,
                statusText: xhr.statusText
            });
        };
        xhr.send();
    });
}

function getWKTMap(grid) {
    let div = grid/100;
    var neLat = map.getBounds().getNorthEast()['lat'] + div*5;
    var neLng = map.getBounds().getNorthEast()['lng'] + div*5;
    var swLat = map.getBounds().getSouthWest()['lat'] - div*5;
    var swLng = map.getBounds().getSouthWest()['lng'] - div*5;

    return "POLYGON((" +
            swLng + " " + swLat + "," +
            swLng + " " + neLat + "," +
            neLng + " " + neLat + "," +
            neLng + " " + swLat + "," +
            swLng + " " + swLat +
            "))";
}

function getColor(d) {
  return d > 1000 ? '#C50101' :
          d > 500  ? '#D71414' :
          d > 200  ? '#E72424' :
          d > 100  ? '#F73535' :
          d > 50   ? '#FB4C4C' :
          d > 20   ? '#FB6262' :
          d > 10   ? '#FC7E7E' :
                    '#FD9696';
}

function style(feature) {
    return {
        fillColor: getColor(feature.properties.counts),
        weight: 0,
        //opacity: 0.5,
        //color: 'black',
        //dashArray: '3',
        fillOpacity: 0.7
    };
}

let map = L.map('map').setView([23.5, 121.2],7);
L.tileLayer('https://{s}.tile.osm.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://osm.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);
var drawnItems = new L.FeatureGroup();
map.addLayer(drawnItems);
drawControl = new L.Control.Draw({
    draw : {
        position : 'topleft',
        polyline : false,
        rectangle : true,
        circle : false,
        polygon: true,
        marker: false,
        circlemarker: false,

    },
    edit : {
      featureGroup: drawnItems,
      edit: false,
      remove: false 
    }
});


map.addControl(drawControl); 

$('.leaflet-control.leaflet-draw').addClass('d-none')
    map.on(L.Draw.Event.CREATED, function (e) {
    // 先把之前的移除
    drawnItems.clearLayers();
    var layer = e.layer;
    drawnItems.addLayer(layer);}
);

map.on('zoomend', function zoomendEvent(ev) {
    if (window.grid_100){

        var currentZoomLevel = ev.target.getZoom()
        $('.loading_area').removeClass('d-none')
        if (currentZoomLevel < 5) {
            $('[class^=resultG_]').addClass('d-none')
            if ($('path.resultG_100').length < 1){
                if (window.grid_100){
                    L.geoJSON(window.grid_100,{className: 'resultG_100', style: style}).addTo(map);
                }
            }
            $('.resultG_100').removeClass('d-none')
        } else if (currentZoomLevel < 8){
            $('[class^=resultG_]').addClass('d-none')
            $('.resultG_10').removeClass('d-none')
        } else if (currentZoomLevel < 12){
            $('[class^=resultG_]').addClass('d-none')
            $('.resultG_5').remove()
            $.ajax({
                url: "/get_map_grid",
                data: window.condition + '&grid=5&map_bound=' + getWKTMap(5) + '&csrfmiddlewaretoken=' + $csrf_token ,
                type: 'POST',
                dataType : 'json',
            })
            .done(function(response) {
                L.geoJSON(response,{className: 'resultG_5', style: style}).addTo(map);
            })
            .fail(function( xhr, status, errorThrown ) {
                if (xhr.status==504){
                    alert('要求連線逾時')
                } else {
                    alert($('input[name=unexpected-error-alert]').val())

                }
                console.log( 'Error: ' + errorThrown + 'Status: ' + xhr.status)
            })

            $('.resultG_5').removeClass('d-none')
        } else {
            $('[class^=resultG_]').addClass('d-none')
            $('.resultG_1').remove()

            $.ajax({
                url: "/get_map_grid",
                data: window.condition + '&grid=1&map_bound=' + getWKTMap(1) + '&csrfmiddlewaretoken=' + $csrf_token ,
                type: 'POST',
                dataType : 'json',
            })
            .done(function(response) {
                L.geoJSON(response,{className: 'resultG_1', style: style}).addTo(map);
            })
            .fail(function( xhr, status, errorThrown ) {
                if (xhr.status==504){
                    alert('要求連線逾時')
                } else {
                    alert($('input[name=unexpected-error-alert]').val())

                }
                console.log( 'Error: ' + errorThrown + 'Status: ' + xhr.status)
            })

            $('.resultG_1').removeClass('d-none')
        }
        $('.loading_area').addClass('d-none')
    }
});


map.on('dragend', function zoomendEvent(ev) {
    if (window.grid_100){
        var currentZoomLevel = ev.target.getZoom()
        if (currentZoomLevel >= 8){
            $('.loading_area').removeClass('d-none')
            if (currentZoomLevel < 12){
                $('[class^=resultG_]').addClass('d-none')
                $('.resultG_5').remove()
                $.ajax({
                    url: "/get_map_grid",
                    data: window.condition + '&grid=5&map_bound=' + getWKTMap(5) + '&csrfmiddlewaretoken=' + $csrf_token ,
                    type: 'POST',
                    dataType : 'json',
                })
                .done(function(response) {
                    L.geoJSON(response,{className: 'resultG_5', style: style}).addTo(map);
                })
                .fail(function( xhr, status, errorThrown ) {
                    if (xhr.status==504){
                        alert('要求連線逾時')
                    } else {
                        alert($('input[name=unexpected-error-alert]').val())

                    }
                    console.log( 'Error: ' + errorThrown + 'Status: ' + xhr.status)
                })

                $('.resultG_5').removeClass('d-none')
            } else {
                $('[class^=resultG_]').addClass('d-none')
                $('.resultG_1').remove()

                $.ajax({
                    url: "/get_map_grid",
                    data: window.condition + '&grid=1&map_bound=' + getWKTMap(1) + '&csrfmiddlewaretoken=' + $csrf_token ,
                    type: 'POST',
                    dataType : 'json',
                })
                .done(function(response) {
                    L.geoJSON(response,{className: 'resultG_1', style: style}).addTo(map);
                })
                .fail(function( xhr, status, errorThrown ) {
                    if (xhr.status==504){
                        alert('要求連線逾時')
                    } else {
                        alert($('input[name=unexpected-error-alert]').val())

                    }
                    console.log( 'Error: ' + errorThrown + 'Status: ' + xhr.status)
                })

                $('.resultG_1').removeClass('d-none')
            }    
            $('.loading_area').addClass('d-none')

        }
    }
});


$( function() {
    
    // $(document).on("keydown", "form", function(event) { 
    //     if(event.key  == 'Enter') {

    //         if ($('.popbg').length == $('.popbg.d-none').length && $('.vsb-menu[style*="visibility: visible"]').length == 0 ){
    //             $('.search_condition_are .submitSearch').trigger('click')
    //         }
    //     } 
    //     return event.key != "Enter";
    // });
    
    $('.resetSearch').on('click', function(){
        $('.clearGeo').trigger('click')
        $('.search_condition_are #searchForm').trigger("reset");
        window.has_par = false
        selectBox.empty()
        selectBox2.empty()
        //selectBox3.empty()
        selectBox4.empty()
        selectBox5.empty()
        selectBox6.empty()
        selectBox7.empty()
        selectBox8.empty()
        selectBox9.empty()
        selectBox10.empty()
    })

    $('.sendSelected').on('click', function(){
        sendSelected()
    })

    $('.selectAll').on('click', function(){
        $(`.col-choice input:checkbox`).prop('checked', true);
    })
    
    $('.resetAll').on('click', function(){
        $(`.col-choice input:checkbox:not(:disabled)`).prop('checked', false);
    })

    $('.submitSearch').on('click', function(){
        submitSearch($(this).data('page'),$(this).data('from'),$(this).data('new_click'))
    })

    let date_locale = { days: ['周日', '周一', '周二', '周三', '周四', '周五', '周六'],
                    daysShort: ['日', '一', '二', '三', '四', '五', '六'],
                    daysMin: ['日', '一', '二', '三', '四', '五', '六'],
                    months: ['一月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '十一月', '十二月'],
                    monthsShort: ['一月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '十一月', '十二月'],
                    today: '今天',
                    clear: '重設',
                    dateFormat: 'yyyy-MM-dd',   
                    timeFormat: 'HH:mm',
                    firstDay: 1}

    let start_date_picker = new AirDatepicker('#start_date',
        { locale: date_locale});


    let end_date_picker = new AirDatepicker('#end_date',
        { locale: date_locale });

    $('.show_start').on('click', function(){
        if (start_date_picker.visible) {
            start_date_picker.hide();
        } else {
            start_date_picker.show();
        }
    })
    
    $('.show_end').on('click', function(){
        if (end_date_picker.visible) {
            end_date_picker.hide();
        } else {
            end_date_picker.show();
        }
    })
      

    $('.mapGeo').on('click', function(){
        $('.addC, .addG').remove()
        $('p.active').removeClass('active')
        $('.mapGeo').addClass('active');
        $('.leaflet-control.leaflet-draw').removeClass('d-none')
    })

    // 從圓中心框選
    $('.circleGeo').on('click', function(){
        $('.addC, .addG').remove()
        //drawnItems.clearLayers();
        //$('p.active').removeClass('active')
        //$('.circleGeo').addClass('active');
        $('.leaflet-control.leaflet-draw').addClass('d-none')
        $(".circle_popup").removeClass('d-none')
    })

    $('.popupGeo').on('click', function(){
        $('.addC').remove()
        //drawnItems.clearLayers();
        //$('p.active').removeClass('active')
        //$('.popupGeo').addClass('active');
        $('.leaflet-control.leaflet-draw').addClass('d-none')
        $(".geojson_popup").removeClass('d-none')
    })

    $('.clearGeo').on('click', function(){
        $('p.active').removeClass('active')
        $('.leaflet-control.leaflet-draw').addClass('d-none')
        drawnItems.clearLayers();
        $('.addG, .addC').remove()
        $('input[name=center_lat]').val('')
        $('input[name=center_lon]').val('')
        $("#circle_radius").val("1").trigger("change");
        $('#geojson_textarea').val('')
        $('input[name=geojson_id]').val('')
        $('[class^=resultG_]').remove()
    })

    $(".popbg .xx,.popbg .ovhy").click(function (e) {
        if ($(e.target).hasClass("choice-xx") || $(e.target).hasClass("choice-ovhy")) {
            window.not_selected.prop('checked', false);
            window.selected.prop('checked', true);
        }
    });
    
    // disable string input in 數量單位
    $("#searchForm input[name=organismQuantity]").on("keyup", function() {
        this.value = this.value.replace(/\D/g,'');
    });
    
    $('.circle_send').click( function(){
        // 先把舊的移除
        $('.addC, [class^=resultG_], .addM, .addG').remove()
        if (($('input[name=center_lat]').val() == '') | ($('input[name=center_lon]').val() == '')){
          alert('框選失敗！請檢查經緯度格式是否正確')
        } else if ($('input[name=center_lat]').val() > 90 | $('input[name=center_lat]').val() < -90 | $('input[name=center_lon]').val() > 180 | $('input[name=center_lon]').val() < -180 ) {
            alert('框選失敗！請檢查經緯度數值是否正確')
        } else {
          try {
            let circle = L.circle([$('input[name=center_lat]').val(),$('input[name=center_lon]').val()],
                        parseInt($('select[name=circle_radius]').val(),10)*1000, { className: 'addC'}).addTo(map);
            drawnItems.clearLayers();
            drawnItems.addLayer(circle);
            map.fitBounds(circle.getBounds());
            $('p.active').removeClass('active')
            $('.circleGeo').addClass('active');
            $(".circle_popup").addClass('d-none')
          } catch (e) {
            alert('框選失敗！請檢查經緯度格式是否正確')
          }
        }
    })
    
    $('.geojson_send').click( function(){
        // 先把舊的移除
        $('.addG, [class^=resultG_], .addC, .addM').remove()
        try {
            let geoObj = JSON.parse($('#geojson_textarea').val());
            //var regionsDissolved = turf.dissolve(geoObj);
            $.ajax({
                url: "/save_geojson",
                data: { geojson_text: JSON.stringify(geoObj),
                        csrfmiddlewaretoken: $csrf_token},
                type: 'POST',
                dataType : 'json',
            })
            .done(function(response) {
                $('input[name=geojson_id]').val(response.geojson_id)
                geoJSON = L.geoJSON(JSON.parse(response.geojson),{ className: 'addG'}).addTo(map);
                map.fitBounds(geoJSON.getBounds());
                $('p.active').removeClass('active')
                $(".geojson_popup").addClass('d-none')
                $('.popupGeo').addClass('active');
                drawnItems.clearLayers();
            })
            .fail(function( xhr, status, errorThrown ) {
                if (xhr.status==504){
                    alert('要求連線逾時')
                } else {
                    alert($('input[name=unexpected-error-alert]').val())

                }
                console.log( 'Error: ' + errorThrown + 'Status: ' + xhr.status)
            })
        } catch (e) {
            alert('上傳失敗！請檢查GeoJSON格式是否正確或檔案是否超過大小上限')
        }
    })
    
    // 如果直接從帶有參數網址列進入
    //changeAction(); 

    // 如果按上下一頁
    window.onpopstate = function(event) {
        drawnItems.clearLayers();
        $('.addG, .addC, .addM, .resultG_1, .resultG_10, .resultG_5, .resultG_100').remove()
       changeAction();
    };

});



function inithigherTaxa(what, datasize){
    let valueProperty = "value";
    let textProperty = "text";
    let urlParams = new URLSearchParams(window.location.search);
    let taxon_id = urlParams.get('higherTaxa')

    return new Promise(function (resolve, reject) {
        var xhr = new XMLHttpRequest();
        xhr.overrideMimeType("application/json");
        xhr.open('GET','/get_higher_taxa?taxon_id=' + taxon_id, true);
        xhr.onload = function () {
            if (this.status >= 200 && this.status < 300) {
                var data = JSON.parse(xhr.response);

                if (what == "" && datasize != undefined && datasize > 0) { // for init to show some data
                    data = data.slice(0, datasize);
                    data = data.map(function (x) {
                        return {
                            value: x[valueProperty],
                            text: x[textProperty]
                        }
                    });
                } else {
                    data = data.filter(function (x) {
                        let name = x[textProperty].toLowerCase();
                        what = what.toLowerCase();
                        if (name.slice(what).search(getVariants(what)) != -1)
                            return {
                                value: x[valueProperty],
                                text: x[textProperty]
                            }
                    });
                }
                data = [{'value': '', 'text': '-- 不限 --'}].concat(data)
                resolve(data);
            } else {
                reject({
                    status: this.status,
                    statusText: xhr.statusText
                });
            }
        };
        xhr.onerror = function () {
            reject({
                status: this.status,
                statusText: xhr.statusText
            });
        };
        xhr.send();
    });
}

function doSearch(what, datasize) {
    let valueProperty = "value";
    let textProperty = "text";
    
    return new Promise(function (resolve, reject) {
        var xhr = new XMLHttpRequest();
        xhr.overrideMimeType("application/json");
        xhr.open('GET','/get_higher_taxa?keyword=' + what, true);
        xhr.onload = function () {
            if (this.status >= 200 && this.status < 300) {
                var data = JSON.parse(xhr.response);

                if (what == "" && datasize != undefined && datasize > 0) { // for init to show some data
                    data = data.slice(0, datasize);
                    data = data.map(function (x) {
                        return {
                            value: x[valueProperty],
                            text: x[textProperty]
                        }
                    });
                } else {
                    data = data.filter(function (x) {
                        let name = x[textProperty].toLowerCase();
                        what = what.toLowerCase();
                        if (name.slice(what).search(getVariants(what)) != -1)
                            return {
                                value: x[valueProperty],
                                text: x[textProperty]
                            }
                    });
                }
                data = [{'value': '', 'text': '-- 不限 --'}].concat(data)
                resolve(data);
            } else {
                reject({
                    status: this.status,
                    statusText: xhr.statusText
                });
            }
        };
        xhr.onerror = function () {
            reject({
                status: this.status,
                statusText: xhr.statusText
            });
        };
        xhr.send();
    });
}


function changeAction(){
    
    console.log('changeAction')

    $('#btn-group-circle_radius button span.title').addClass('black').removeClass('color-707070')

    $('.vsb-main button').css('border','').css('background','')
    $('span.caret').addClass('d-none')

    /*
    $('.vsb-main button').on('click',function(){
        if ($(this).next('.vsb-menu').css('visibility')=='visible'){
            $(this).next('.vsb-menu').addClass('visible')
        } else {
            $(this).next('.vsb-menu').css('visibility', '')
            $(this).next('.vsb-menu').removeClass('visible')
        }
    })*/


    let select_length = $(".search_condition_are select, .circle_popup select").length;
    for (let i = 0; i < select_length; i++) {
        let tmp_id = $(".search_condition_are select, .circle_popup select")[i].id;

        $(`#${tmp_id}`).on('change',function(){
            if ($(`#btn-group-${tmp_id} ul li.active`).length>0){
                $(`#btn-group-${tmp_id} button span.title`).addClass('black').removeClass('color-707070')
            } else {
                $(`#btn-group-${tmp_id} button span.title`).addClass('color-707070').removeClass('black')
            }
        })
    }

    let queryString = window.location.search;
    let urlParams = new URLSearchParams(queryString);

    //selectBox10.setValue('')

    if (queryString.split('&').length>1){
        // 把條件填入表格
        let entries = urlParams.entries(); 

        let d_list = Array();
        let r_list = Array();
        let l_list = Array();

        for(const [key, value] of entries) { 
            if (key=='datasetName') {
                d_list.push(value)
            } else if (key == 'rightsHolder') {
                r_list.push(value)
            /*} else if (key == 'sensitiveCategory') {
                selectBox3.setValue(value)*/
            } else if (key == 'typeStatus') {
                selectBox4.setValue(value)
            } else if (key == 'taxonRank'){
                selectBox5.setValue(value)
            } else if (key == 'has_image'){
                selectBox7.setValue(value)
            } else if (key == 'higherTaxa'){
                console.log(value)
            } else if (key == 'taxonGroup'){
                selectBox9.setValue(value)
            } else if (key == 'locality'){
                l_list.push(value)
                //selectBox10.setValue(value)
            } else {

                $(`[name=${key}]`).val(value)
                // map按鈕
                if (key == 'geo_type'){
                    $(`p[data-type=${value}]`).addClass("active")

                    // 把地圖畫上去
                    if (urlParams.get('geo_type') == 'circle') {
                        let circle = L.circle([urlParams.get('center_lat'),urlParams.get('center_lon')],
                        parseInt(urlParams.get('circle_radius'),10)*1000, { className: 'addC'}).addTo(map);
                        drawnItems.addLayer(circle);
                        map.fitBounds(circle.getBounds());
                    } else if (urlParams.get('geo_type') == 'map') {
                        var wkt = new Wkt.Wkt();
                        if (urlParams.getAll('polygon')){
                            for (let i = 0; i < urlParams.getAll('polygon').length; i++) {
                                wkt.read(urlParams.getAll('polygon')[i])
                                obj = wkt.toObject({className: 'addM'}); 
                                obj.addTo(map);
                            }
                        }
                    } 
                }
                if ((key == 'geojson_id') && (value != '')){ 
                    
                    fetch(`/media/geojson/${value}.json`).then((res) => {
                        if (res.ok) {
                            $('#geojson_textarea').val(JSON.stringify(res.json()))
                            $.getJSON(`/media/geojson/${value}.json`, function (ret) {
                                geoJSON = L.geoJSON(ret,{ className: 'addG'}).addTo(map);
                                map.fitBounds(geoJSON.getBounds());
                            });
                        } else {
                            $(`p[data-type=polygon]`).removeClass("active")
                        }
                    });
                }
            } 
        }

        if (d_list.length > 0){
            window.d_list = d_list;
            window.has_par = true;
        }

        selectBox.setValue(r_list);
        selectBox2.setValue(d_list);
        selectBox10.setValue(l_list);


        // 如果有選項的 顏色改為黑色
        let select_length = $(".search_condition_are [id^=btn-group-], .circle_popup [id^=btn-group-]").length;
        for (let i = 0; i < select_length; i++) {
            let tmp_id = $(".search_condition_are [id^=btn-group-], .circle_popup [id^=btn-group-]")[i].id;
            if ($(`#${tmp_id} .vsb-menu ul li.active`).length>0){
                $(`#${tmp_id} button span.title`).addClass('black').removeClass('color-707070')
            } else {
                $(`#${tmp_id} button span.title`).addClass('color-707070').removeClass('black')
            }
        }
        
        if (urlParams.get('page')){
            page = urlParams.get('page')
        } else {
            page = 1
        }
        submitSearch(page, 'search', false, urlParams.get('limit'), urlParams.get('orderby'),urlParams.get('sort'), false)//{

    }
}

function setTable(response, queryString, from, orderby, sort){
    // 把之前的清掉
    if (from=='search'){
        //drawnItems.clearLayers();
        //$('.addG, .addC, .addM, .resultG_1, .resultG_10, .resultG_5, .resultG_100').remove()
        $('.resultG_1, .resultG_10, .resultG_5, .resultG_100').remove()

        L.geoJSON(response.map_geojson.grid_10,{className: 'resultG_10',style: style}).addTo(map);
        window.grid_100 = response.map_geojson.grid_100
    }

    // 如果有資料回傳則顯示table
    $('.search_condition_are').after(`
    <div class="sc_result">
    <div class="result_inf_top">
        <div class="d-flex-ai-c res_flex">
        <button class="cate_btn mr-20px popupField">欄位選項 +</button>
        <div class="w-200px per_page">每頁顯示
            <select name="shownumber" data-query='${queryString}'>
            <option value="10">10</option>
            <option value="20">20</option>
            <option value="50">50</option>
            <option value="100">100</option>
            </select> 筆
        </div>
        </div>
        <div class="rightmore">
        <p class="datenum">資料筆數 ： ${response.count.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",")}</p>
        <button class="dw downloadData" data-query="${queryString}" data-count="${response.count}">資料下載</button>
        <button class="dw downloadTaxon" data-query="${queryString}">名錄下載</button>
        <a href="/qa?qa_id=14" target="_blank" class="qmark"></a>
        <button class="dw downloadSensitive" data-query="${queryString}" data-count="${response.count}">申請單次使用去模糊化敏感資料</button>
        <a href="/qa?qa_id=15" target="_blank" class="qmark"></a>
        </div>
    </div>
    <div class="result_table flow-x-auto">
        <table cellspacing="0" cellspacing="0" class="table_style1 record_table">
        </table>						
    </div>
    </div>`)

    $('select[name=shownumber]').on('change',function(){
        submitSearch(1,'page',false,$(this).val(),orderby, sort)
    })
    
    // 如果querystring裡面有limit的，修改shownumber
    $("select[name=shownumber]").val(response.limit);

    // 如果有敏感資料才有申請按鈕

    if (!response.has_sensitive){
        $('button.downloadSensitive').prop('disabled', true);
        $('button.downloadSensitive').removeClass('downloadSensitive dw').addClass('dwd')
    }
    if (!response.has_species){
        $('button.downloadTaxon').prop('disabled', true);
        $('button.downloadTaxon').removeClass('downloadTaxon dw').addClass('dwd')
    }

    // 
    if (!response.has_species){
        $('button.downloadTaxon').prop('disabled', true);
        $('button.downloadTaxon').removeClass('downloadTaxon dw').addClass('dwd')
    }

    // table title
    var table_title = document.createElement("tr");
    table_title.classList.add('table_title');
    let map_dict = response.map_dict;

    var function_td = document.createElement("td");
    var text = document.createTextNode('功能');
    function_td.appendChild(text);
    table_title.appendChild(function_td); 

    for (let i = 0; i < Object.keys(map_dict).length; i++) {
        var this_td = document.createElement("td");
        this_td.className = `row-${Object.keys(map_dict)[i]} d-none`;
        //this_td.style.cssText = 'display:none';
        var text = document.createTextNode(map_dict[Object.keys(map_dict)[i]]);
        let a = document.createElement("a");
        a.className = 'orderby';
        a.dataset.orderby = Object.keys(map_dict)[i]; 
        a.dataset.sort = 'asc';       
        this_td.appendChild(text);
        this_td.appendChild(a);
        table_title.appendChild(this_td); 
    }

    $('.record_table').append(table_title);
    
    // append rows
    for (let i = 0; i < response.rows.length; i++) {
        let tmp = response.rows[i];
        let tmp_td;
        let tmp_value;
        let url_mask = "/collection/" + tmp.id.toString();
        tmp_td += `<td><a href=${url_mask} class="more" target="_blank">查看</a></td>`
        for (let j = 0; j < Object.keys(map_dict).length; j++){
            tmp_value = tmp[Object.keys(map_dict)[j]];
            if (tmp_value == null){
                tmp_td += `<td class="row-${Object.keys(map_dict)[j]} d-none"></td>`
            } else {
                tmp_td += `<td class="row-${Object.keys(map_dict)[j]} d-none">${tmp_value}</td>`
            }
        }
        $('.record_table').append(`<tr>${tmp_td}</tr>`)
    }

    // 如果queryString裡面沒有指定orderby，使用scientificName
    $('.orderby').not(`[data-orderby=${response.orderby}]`).append('<i class="fa-solid fa-sort sort-icon"></i>')
    if (response.sort == 'asc'){
        $(`.orderby[data-orderby=${response.orderby}]`).append('<i class="fa-solid fa-sort-down sort-icon-active"></i>')
    } else {
        $(`.orderby[data-orderby=${response.orderby}]`).append('<i class="fa-solid fa-sort-up sort-icon-active"></i>')
        $(`.orderby[data-orderby=${response.orderby}]`).data('sort','desc');
    }

    $('.orderby').on('click',function(){
        if ($(this).children('svg').hasClass('fa-sort')){
            $('.orderby:not(this)').children('svg').removeClass('fa-sort-down fa-sort-up sort-icon-active sort-icon').addClass('fa-sort sort-icon');
            $(this).children('svg').removeClass('fa-sort sort-icon-active sort-icon').addClass('fa-sort-down sort-icon-active');
            $(this).data('sort','asc');
        } else if ($(this).children('svg').hasClass('fa-sort-down')) {
            $('.orderby:not(this)').children('svg').removeClass('fa-sort-down fa-sort-up sort-icon-active sort-icon').addClass('fa-sort sort-icon');
            $(this).children('svg').removeClass('fa-sort sort-icon-active sort-icon').addClass('fa-sort-up sort-icon-active')
            $(this).data('sort','desc');
        } else {
            $('.orderby:not(this)').children('svg').removeClass('fa-sort-down fa-sort-up sort-icon-active sort-icon').addClass('fa-sort sort-icon');
            $(this).children('svg').removeClass('fa-sort sort-icon-active sort-icon').addClass('fa-sort-down sort-icon-active')
            $(this).data('sort','asc');
        }

        submitSearch(1,'orderby',false,response.limit,$(this).data('orderby'),$(this).data('sort'))
        //getRecordByURL(queryString,null,response.limit,$(this).data('orderby'),$(this).data('sort'))
    })

    $('.downloadData').on('click', function(){
        let queryString = $(this).data('query')
        let total_count = $(this).data('count')
        if ($('input[name=is_authenticated]').val() == 'True'){
            $.ajax({
                url: "/send_download_request",
                data: queryString + '&csrfmiddlewaretoken=' + $csrf_token + '&total_count=' + total_count,
                type: 'POST',
                dataType : 'json',
            })
            .done(function(response) {
                alert('請求已送出，下載檔案處理完成後將以email通知')
            })
            .fail(function( xhr, status, errorThrown ) {
                if (xhr.status==504){
                    alert('要求連線逾時')
                } else {
                    alert($('input[name=unexpected-error-alert]').val())

                }
                console.log( 'Error: ' + errorThrown + 'Status: ' + xhr.status)
            })
        } else {
            alert('請先登入')
        }  
    })

    $('.downloadTaxon').on('click', function(){
        let queryString = $(this).data('query')
        if ($('input[name=is_authenticated]').val() == 'True'){
            $.ajax({
                url: "/send_download_request",
                data: queryString + '&csrfmiddlewaretoken=' + $csrf_token + '&taxon=yes',
                type: 'POST',
                dataType : 'json',
            })
            .done(function(result) {
                alert('請求已送出，下載檔案處理完成後將以email通知')
            })
            .fail(function( xhr, status, errorThrown ) {
                if (xhr.status==504){
                    alert('要求連線逾時')
                } else {
                    alert($('input[name=unexpected-error-alert]').val())

                }
                console.log( 'Error: ' + errorThrown + 'Status: ' + xhr.status)
            })
        } else {
            alert('請先登入')
        }
    })

    $('.downloadSensitive').on('click', function(){
        let queryString = $(this).data('query')
        let total_count = $(this).data('count')
        if ($('input[name=is_authenticated]').val() == 'True'){
            window.open('/sensitive_agreement?' + queryString + '&total_count=' + total_count)
        } else {
            alert('請先登入')
        }    
    })

    $('.popupField').on('click', function(){
        $(`.col-choice`).removeClass('d-none')
        window.not_selected = $(`.col-choice input:not(:checked)`)
        window.selected = $(`.col-choice input:checked`)
    })
}

// submit search form   
function submitSearch (page, from, new_click, limit, orderby, sort, push_state){
    console.log('submitSearch')

    if (push_state == null){ push_state = true }

    let map_condition = ''

    if (new_click & ($('.btnupload p.active').data('type')=='map')){
        $.ajax({
            url: "/return_geojson_query",
            data: { geojson_text: JSON.stringify(drawnItems.toGeoJSON()),
                    csrfmiddlewaretoken: $csrf_token},
            type: 'POST',
            dataType : 'json',
        })
        .done(function(response) {
            window.g_list = response.polygon
            submitSearch (page, from)
        })
        .fail(function( xhr, status, errorThrown ) {
            if (xhr.status==504){
                alert('要求連線逾時')
            } else {
                alert($('input[name=unexpected-error-alert]').val())

            }
            console.log( 'Error: ' + errorThrown + 'Status: ' + xhr.status)
        })

    } else {

        if ($('.btnupload p.active').data('type')){

            map_condition = '&' + $.param({'geo_type': $('.btnupload p.active').data('type')})

            if ($('.btnupload p.active').data('type')=='circle'){
                map_condition += '&' + $.param({'circle_radius': $('select[name=circle_radius]').val(),
                'center_lon': $('input[name=center_lon]').val(), 'center_lat': $('input[name=center_lat]').val()})
            } else if ($('.btnupload p.active').data('type')=='map') {
                if (window['g_list']){
                    for (let i = 0; i < window['g_list'].length; i++) {
                        map_condition += '&' + $.param({'polygon': window['g_list'][i]})
                    }
                } else {
                    //let queryString = window.location.search;
                    let urlParams = new URLSearchParams(window.location.search);
                    if (urlParams.getAll('polygon')){
                        for (let i = 0; i < urlParams.getAll('polygon').length; i++) {
                            map_condition += '&' + $.param({'polygon':  urlParams.getAll('polygon')[i]})
                        }
                    }
                }
            }
        }

        let selected_col = ''

        // 如果是按搜尋，重新給query參數，若是從分頁則不用
        if (from == 'search'){   
            var form = $(); 
            $('#searchForm input, #searchForm select').each(function() {
                if ($(this).val()!='') {
                    form = form.add($(this));
                }
            })
            window.condition = form.serialize() + map_condition
        } else {
            // 如果是從分頁，要記錄selected columns
            $(`.col-choice input:checked`).each(function(){
                selected_col += '&selected_col=' + $(this).attr('id').replace('col-','')
            })
        }

        if (limit == null) {
            limit = 10
        }

        // 如果調整orderby and sort
        let orderby_str = ''
        if (orderby != null){
            if (from == 'orderby'){
                page = 1
            }
            orderby_str = '&orderby=' + orderby + '&sort=' + sort
        }

        let queryString = window.condition + '&page=' +  page + '&from=' + from + '&limit=' + limit + orderby_str

        if (queryString.length > 2000) {
            alert('您查詢的條件網址超過 2000 個字元，可能無法在所有瀏覽器中正常運作。')
        } else {

            if (push_state){
                history.pushState(null, '', window.location.pathname + '?' + queryString)
            }

            $(".loading_area").removeClass('d-none');

            $.ajax({
                url: "/get_conditional_records",
                data: queryString + '&csrfmiddlewaretoken=' + $csrf_token + selected_col,
                type: 'POST',
                dataType : 'json',
            })
            .done(function(response) {

                // clear previous results
                $('.sc_result').remove()
                //$('.resultG_1, .resultG_10, .resultG_5, .resultG_100').remove()
                if (response.count == 0){
                    // TODO 這邊如果有map的圖案要加回來
                    $('.resultG_1, .resultG_10, .resultG_5, .resultG_100').remove()
                    $('.search_condition_are').after(`<div class="sc_result"><div class="no_data">無資料</div></div>`)
                } else {
                    setTable(response, window.condition, from, orderby, sort)
                    // 判斷是從分頁或搜尋點選
                    if (from == 'search'){
                        // uncheck all first
                        $(`input[id^="col-"]`).prop('checked',false)
                        // show selected columns
                        for (let i = 0; i < response.selected_col.length; i++) {
                            $(`.row-${response.selected_col[i]}`).removeClass('d-none');
                            $(`#col-${response.selected_col[i]}`).prop('checked',true);
                        }
                    } else {
                        sendSelected()
                    }

                    // disable checkebox for common_name_c & scientificName
                    $('#col-common_name_c, #col-scientificName').prop('disabled',true);
                    $('#col-common_name_c, #col-scientificName').prop('checked',true);
                    // append pagination
                    if (response.total_page > 1){  // 判斷是否有下一頁，有才加分頁按鈕
                        $('.result_table').after(
                            `<div class="page-inf">
                            <div class="page_number">
                            <a href="javascript:;" class="pre">
                                <span></span>
                            </a>
                            <a href="javascript:;" class="next">
                                <span></span>
                            </a>
                            </div>
                            <span>
                                跳至<input name="jumpto" type="number" min="1" step="1" class="page-jump">頁
                                <a class="jumpto pointer">GO</a>  
                            </span>
                            </div>`)
                    }
                    
                    $('.jumpto').on('click', function(){
                        submitSearch($('input[name=jumpto]').val(),'page',false,limit,orderby,sort)
                    })
                        
                    let html = ''
                    for (let i = 0; i < response.page_list.length; i++) {
                        if (response.page_list[i] == response.current_page){
                            html += `<a href="javascript:;" class="num now submitSearch" data-page="${response.page_list[i]}" data-from="page">${response.page_list[i]}</a>  `;
                        } else {
                            html += `<a href="javascript:;" class="num submitSearch" data-page="${response.page_list[i]}" data-from="page">${response.page_list[i]}</a>  `
                        }
                    }
                    $('.pre').after(html)

                    // 如果有上一頁，改掉pre的onclick
                    if ((response.current_page - 1) > 0 ){
                        $('.pre').addClass('submitSearch')
                        $('.pre').data('page', response.current_page-1)
                        $('.pre').data('from', 'page')
                    }
                    // 如果有下一頁，改掉next的onclick
                    if (response.current_page < response.total_page){
                        $('.next').addClass('submitSearch')
                        $('.next').data('page', response.current_page+1)
                        $('.next').data('from', 'page')
                    }

                    // 如果有前面的page list, 加上...
                    if (response.current_page > 5){
                        $('.pre').after(`<a href="javascript:;" class="num bd-0 submitSearch" data-page="${response.current_page-5}" data-from="page">...</a> `)
                    }
                    // 如果有後面的page list, 加上...
                    if (response.page_list[response.page_list.length - 1] < response.total_page){
                        if (response.current_page +5 > response.total_page){
                            $('.next').before(`<a href="javascript:;" class="num bd-0 submitSearch" data-page="${response.total_page}" data-from="page">...</a> `)
                        } else {
                            $('.next').before(`<a href="javascript:;" class="num bd-0 submitSearch" data-page="${response.current_page+5}" data-from="page">...</a>`)
                        }
                    }

                    if (limit) {
                        $('.page_number a.submitSearch').data('limit', limit)
                    }

                    if (orderby) {
                        $('.page_number a.submitSearch').data('orderby', orderby)
                    }

                    if (sort) {
                        $('.page_number a.submitSearch').data('sort', sort)
                    }

                    $('.page_number a.submitSearch').on('click', function(){
                        submitSearch($(this).data('page'),$(this).data('from'),false,$(this).data('limit'),$(this).data('orderby'),$(this).data('sort'))
                    })

                }
                $(".loading_area").addClass('d-none');
                $([document.documentElement, document.body]).animate({
                    scrollTop: $(".sc_result").offset().top - 100 }, 200);
            })
            .fail(function( xhr, status, errorThrown ) {
                if (xhr.status==504){
                    alert('要求連線逾時')
                } else {
                    alert($('input[name=unexpected-error-alert]').val())

                } 
                $(".loading_area").addClass('d-none');
                console.log( 'Error: ' + errorThrown + 'Status: ' + xhr.status)
            })
        }
       
    }
}
  
function sendSelected(){
    let selected_field = $(`.col-choice input:checked`)
    // 所有都先隱藏，除了common_name_c & scientificName
    $('td[class^="row-"]').addClass('d-none');
    $('.row-common_name_c, .row-scientificName').removeClass('d-none');
    // 再顯示選擇的欄位
    for (let i = 0; i < selected_field.length; i++) {
        $(`td.row-${selected_field[i].id.split('-')[1]}`).removeClass('d-none');
    }
    $(".popbg").addClass('d-none');
}