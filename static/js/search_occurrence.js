var $csrf_token = $('[name="csrfmiddlewaretoken"]').attr("value");

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
        weight: 1,
        opacity: 0.5,
        color: 'black',
        //dashArray: '3',
        fillOpacity: 1
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
        circlemarker: false
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
    var layer = e.layer;
    drawnItems.addLayer(layer);
});

map.on('zoomend', function zoomendEvent(ev) {
    var currentZoomLevel = ev.target.getZoom()
    if (currentZoomLevel < 5) {
        $('[class^=resultG_]').addClass('d-none')
        $('.resultG_100').removeClass('d-none')
    } else if (currentZoomLevel < 8){
        $('[class^=resultG_]').addClass('d-none')
        $('.resultG_10').removeClass('d-none')
    } else if (currentZoomLevel < 9){
        $('[class^=resultG_]').addClass('d-none')
        $('.resultG_5').removeClass('d-none')
    } else {
        $('[class^=resultG_]').addClass('d-none')
        $('.resultG_1').removeClass('d-none')
    }
});



$( function() {

    $('.sendSelected').on('click', function(){
        sendSelected()
    })

    $('.selectAll').on('click', function(){
        $(`.occ-choice input:checkbox`).prop('checked', true);
    })
    
    $('.resetAll').on('click', function(){
        $(`.occ-choice input:checkbox:not(:disabled)`).prop('checked', false);
    })

    $('.submitSearch').on('click', function(){
        submitSearch($(this).data('page'),$(this).data('from'))
    })

    $('.show_start').on('click', function(){
        $('#start_date').datepicker('show')
    })

    $('.show_end').on('click', function(){
        $('#end_date').datepicker('show')
    })

    $( "#start_date" ).datepicker({ dateFormat: 'yy-mm-dd' });
    $( "#end_date" ).datepicker({ dateFormat: 'yy-mm-dd' });

    $('.mapGeo').on('click', function(){
        $('.addC, .addG').remove()
        $('p.active').removeClass('active')
        $('.mapGeo').addClass('active');
        $('.leaflet-control.leaflet-draw').removeClass('d-none')
    })

    // 從圓中心框選
    $('.circleGeo').on('click', function(){
        $('.addC, .addG').remove()
        drawnItems.clearLayers();
        $('p.active').removeClass('active')
        $('.circleGeo').addClass('active');
        $('.leaflet-control.leaflet-draw').addClass('d-none')
        $(".circle_popup").removeClass('d-none')
    })

    $('.popupGeo').on('click', function(){
        $('.addC').remove()
        drawnItems.clearLayers();
        $('p.active').removeClass('active')
        $('.popupGeo').addClass('active');
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
    })

    $(".popbg .xx,.popbg .ovhy").click(function (e) {
        if ($(e.target).hasClass("choice-xx") || $(e.target).hasClass("choice-ovhy")) {
            window.not_selected.prop('checked', false);
            window.selected.prop('checked', true);
        }
    });
    
    // disable string input in 數量單位
    $("input[name=organismQuantity]").on("keyup", function() {
        this.value = this.value.replace(/\D/g,'');
    });
    

    $('.circle_send').click( function(){
    // 先把舊的移除
        $('.addC, [class^=resultG_]').remove()
        if (($('input[name=center_lat]').val() == '') | ($('input[name=center_lon]').val() == '')){
            alert('框選失敗！請檢查經緯度格式是否正確')
        } else {
            try {
            let circle = L.circle([$('input[name=center_lat]').val(),$('input[name=center_lon]').val()],
                        parseInt($('select[name=circle_radius]').val(),10)*1000, { className: 'addC'}).addTo(map);
            drawnItems.addLayer(circle);
            map.fitBounds(circle.getBounds());
            $(".circle_popup").addClass('d-none')
            } catch (e) {
            alert('框選失敗！請檢查經緯度格式是否正確')
            }
        }
    })
    
    $('.geojson_send').click( function(){
        // 先把舊的移除
        $('.addG, [class^=resultG_]').remove()
        try {
            let geoObj = JSON.parse($('#geojson_textarea').val());
            //geoJSON = L.geoJSON(geoObj,{ className: 'addG'}).addTo(map);
            //var ucbRegions = L.geoJson(data).addTo(map);
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
            })
            .fail(function( xhr, status, errorThrown ) {
                if (xhr.status==504){
                    alert('要求連線逾時')
                } else {
                    alert('發生未知錯誤！請聯絡管理員')
                }
                console.log( 'Error: ' + errorThrown + 'Status: ' + xhr.status)
            })
    
            geoJSON = L.geoJSON(regionsDissolved,{ className: 'addG'}).addTo(map);
            map.fitBounds(geoJSON.getBounds());
            $(".geojson_popup").addClass('d-none')
        } catch (e) {
            alert('上傳失敗！請檢查GeoJSON格式是否正確或檔案是否超過大小上限')
        }
    })

    // 如果直接從帶有參數網址列進入
    changeAction(); 

    // 如果按上下一頁
    window.onpopstate = function(event) {
        drawnItems.clearLayers();
        $('.addG, .addC, .resultG_1, .resultG_10, .resultG_5, .resultG_100').remove()
        changeAction();
    };

} );



function changeAction(){
    
    let selectBox = new vanillaSelectBox("#rightsHolder",{"placeHolder":"來源資料庫",search:true,
        translations: { "all": "全部", "items": " 個選項", "selectAll": '全選', "clearAll": '清除' } 
    });

    let selectBox2 = new vanillaSelectBox("#datasetName",{"placeHolder":"資料集名稱",search:true,
        translations: { "all": "全部", "items": " 個選項", "selectAll": '全選', "clearAll": '清除' } 
    });

    $('.vsb-main button').css('border','').css('background','')
    $('span.caret').addClass('d-none')

    $('.vsb-main button').on('click',function(){
        if ($(this).next('.vsb-menu').css('visibility')=='visible'){
            $(this).next('.vsb-menu').addClass('visible')
        } else {
            $(this).next('.vsb-menu').css('visibility', '')
            $(this).next('.vsb-menu').removeClass('visible')
        }
    })

    $('#rightsHolder').on('change',function(){
        if ($('#btn-group-rightsHolder ul.multi li.active').length>0){
            $('#btn-group-rightsHolder button span.title').addClass('black').removeClass('color-707070')
        } else {
            $('#btn-group-rightsHolder button span.title').addClass('color-707070').removeClass('black')
        }
    })

    $('#datasetName').on('change',function(){
        if ($('#btn-group-datasetName .vsb-menu ul.multi li.active').length>0){
            $('#btn-group-datasetName button span.title').addClass('black').removeClass('color-707070')
        } else {
            $('#btn-group-datasetName button span.title').addClass('color-707070').removeClass('black')
        }
    })

    let queryString = window.location.search;
    if (queryString.split('&').length > 1){
        // 把條件填入表格
        let urlParams = new URLSearchParams(queryString);
        let entries = urlParams.entries(); 
        
        let d_list = Array();
        let r_list = Array();

        for(const [key, value] of entries) { 
            // 如果是下拉式多選要另外處理
            if ((key != 'datasetName') & (key != 'rightsHolder')){
                $(`[name=${key}]`).val(value)
                // map按鈕
                if (key == 'geo_type'){
                    $(`p[data-type=${value}]`).addClass("active")
                }

                if (key == 'geojson') {
                    if (urlParams.get('geo_type') == 'map') {
                    geoJSON = L.geoJSON(JSON.parse(value)).addTo(map);
                    drawnItems.addLayer(geoJSON);
                    map.fitBounds(geoJSON.getBounds());
                    } else if (urlParams.get('geo_type') == 'circle') {
                    let circle = L.circle([urlParams.get('center_lat'),urlParams.get('center_lon')],
                    parseInt(urlParams.get('circle_radius'),10)*1000, { className: 'addC'}).addTo(map);
                    drawnItems.addLayer(circle);
                    map.fitBounds(circle.getBounds());
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
            } else {
                if (key=='datasetName') {
                    d_list.push(value)
                } else if (key == 'rightsHolder') {
                    r_list.push(value)
                }
            }  
        }

        selectBox.setValue(r_list);
        selectBox2.setValue(d_list);

        if ($('#btn-group-datasetName .vsb-menu ul.multi li.active').length>0){
            $('#btn-group-datasetName button span.title').addClass('black').removeClass('color-707070')
        } else {
            $('#btn-group-datasetName button span.title').addClass('color-707070').removeClass('black')
        }

        if ($('#btn-group-rightsHolder ul.multi li.active').length>0){
            $('#btn-group-rightsHolder button span.title').addClass('black').removeClass('color-707070')
        } else {
            $('#btn-group-rightsHolder button span.title').addClass('color-707070').removeClass('black')
        }

        getRecordByURL(queryString,null,null,null,null)
    }
}

function setTable(response, queryString){
    drawnItems.clearLayers();
    $('.addG, .addC, .resultG_1, .resultG_10, .resultG_5, .resultG_100').remove()

    L.geoJSON(response.map_geojson.grid_1,{className: 'resultG_1', style: style}).addTo(map);
    L.geoJSON(response.map_geojson.grid_5,{className: 'resultG_5', style: style}).addTo(map);
    L.geoJSON(response.map_geojson.grid_10,{className: 'resultG_10', style: style}).addTo(map);
    L.geoJSON(response.map_geojson.grid_100,{className: 'resultG_100', style: style}).addTo(map);
    //map.fitBounds(geoResult.getBounds());

    $('.resultG_1, .resultG_5, .resultG_10, .resultG_100').addClass('d-none')

    if (map.getZoom() < 5) {
        $('.resultG_100').removeClass('d-none')
    } else if (map.getZoom() < 8){
        $('.resultG_10').removeClass('d-none')
    } else if (map.getZoom() < 9){
        $('.resultG_5').removeClass('d-none')
    } else {
        $('.resultG_1').removeClass('d-none')
    }
    
    // 如果有資料回傳則顯示table
    $('.search_condition_are').after(`
    <div class="sc_result">
    <div class="result_inf_top">
        <div class="d-flex-ai-c">
        <button class="cate_btn mr-20px popupField">欄位選項 +</button>
        <div class="w-200px">每頁顯示
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
        <a id="before_sensitive" href="#" class="qmark"></a>
        </div>
    </div>
    <div class="result_table flow-x-auto">
        <table cellspacing="0" cellspacing="0" class="table_style1 record_table">
        </table>						
    </div>
    </div>`)

    $('select[name=shownumber]').on('change',function(){
        getRecordByURL($(this).data('query'), 1,$(this).val(),null,null)
    })

    // 如果querystring裡面有limit的，修改shownumber
    $("select[name=shownumber]").val(response.limit);

    // 如果有敏感資料才有申請按鈕
    if (response.has_sensitive){
        $('#before_sensitive').after(`
        <button class="dw downloadSensitive" data-query="${queryString}" data-count="${response.count}">申請單次使用去模糊化敏感資料</button>
        <a href="#" class="qmark"></a>`)
    } else {
        $('#before_sensitive').after(`
        <button class="dwd" disabled>申請單次使用去模糊化敏感資料</button>
        <a href="#" class="qmark"></a>`)
    }

    // table title
    var table_title = document.createElement("tr");
    table_title.classList.add('table_title');
    let map_dict = response.map_dict;

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
    var function_td = document.createElement("td");
    var text = document.createTextNode('功能');
    function_td.appendChild(text);
    table_title.appendChild(function_td); 

    $('.record_table').append(table_title);
        
    // append rows
    for (let i = 0; i < response.rows.length; i++) {
        let tmp = response.rows[i];
        let tmp_td;
        let tmp_value;
        for (let j = 0; j < Object.keys(map_dict).length; j++){
            tmp_value = tmp[Object.keys(map_dict)[j]];
            if (tmp_value == null){
                tmp_td += `<td class="row-${Object.keys(map_dict)[j]} d-none"></td>`
            } else {
                tmp_td += `<td class="row-${Object.keys(map_dict)[j]} d-none">${tmp_value}</td>`
            }
        }
        let url_mask = "/occurrence/" + tmp.id.toString();
        tmp_td += `<td><a href=${url_mask} class="more" target="_blank">查看</a></td>`
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
        getRecordByURL(queryString,null,response.limit,$(this).data('orderby'),$(this).data('sort'))
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
                    alert('發生未知錯誤！請聯絡管理員')
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
                    alert('發生未知錯誤！請聯絡管理員')
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
        $(`.occ-choice`).removeClass('d-none')
        window.not_selected = $(`.occ-choice input:not(:checked)`)
        window.selected = $(`.occ-choice input:checked`)
    })
}

function getRecordByURL(queryString,page,limit,orderby,sort) {
    // 如果從頁碼點選, 修改page參數
    if (page != null){
        let urlParams = new URLSearchParams(queryString);
        urlParams.set('page',page)
        queryString = urlParams.toString()
        history.pushState(null, '', window.location.pathname + '?'  + queryString);
    }
    // 如果page等於null的話要把page的參數拿掉嗎？

    // 如果調整每頁筆數, 修改limit參數
    if (limit != null){
        let urlParams = new URLSearchParams(queryString);
        urlParams.set('limit',limit)
        urlParams.set('page',1)
        queryString = urlParams.toString()
        history.pushState(null, '', window.location.pathname + '?'  + queryString);
    }

    // 如果調整orderby and sort
    if (orderby != null){
        let urlParams = new URLSearchParams(queryString);
        urlParams.set('orderby',orderby)
        urlParams.set('sort',sort)
        urlParams.set('page',1)
        queryString = urlParams.toString()
        history.pushState(null, '', window.location.pathname + '?'  + queryString);
    }

    // selected_col
    let selected_col = ''
    $(`.occ-choice input:checked`).each(function(){
        selected_col += '&selected_col=' + $(this).attr('id').replace('occ-','')
        }
    )

    $.ajax({
        url: "/get_conditional_records",
        data: queryString + '&csrfmiddlewaretoken=' + $csrf_token + selected_col,
        type: 'POST',
        dataType : 'json',
    })
    .done(function(response) {
        // clear previous results
        $('.sc_result').remove()
        $('.resultG_1, .resultG_10, .resultG_5, .resultG_100').remove()

        if (response.count == 0){
        $('.search_condition_are').after(`<div class="sc_result"><div class="no_data">暫無資料</div></div>`)
        } else {
            // 把之前的清掉
            setTable(response, queryString)

            // 欄位選項
            $(`input[id^="occ-"]`).prop('checked',false)
            // show selected columns
            for (let i = 0; i < response.selected_col.length; i++) {
                $(`.row-${response.selected_col[i]}`).removeClass('d-none');
                $(`#occ-${response.selected_col[i]}`).prop('checked',true);}

            // disable checkebox for common_name_c & scientificName
            $('#occ-common_name_c, #occ-scientificName').prop('disabled',true);
            $('#occ-common_name_c, #occ-scientificName').prop('checked',true);

            // append pagination
            if (response.total_page > 1){  // 判斷是否有下一頁，有才加分頁按鈕
                $('.result_table').after(
                `<div class="d-flex-ai-c-jc-c">
                    <div class="page_number">
                    <a href="javascript:;" class="pre">
                    <span></span>
                    </a>
                    <a href="javascript:;" class="next">
                    <span></span>
                    </a>
                    </div>
                    <span class="ml-20px">
                    跳至<input class="page-jump" data-query='${queryString}' name="jumpto" type="number" min="1" step="1">頁
                    <a class="jumpto pointer">GO</a>  
                    </span>
                </div>`)}		

                $('.jumpto').on('click', function(){
                    getRecordByURL($('input[name=jumpto]').data('query'),$('input[name=jumpto]').val(),null,null,null)
                })

            let html = ''
            for (let i = 0; i < response.page_list.length; i++) {
                if (response.page_list[i] == response.current_page){
                    html += `<a href="javascript:;" class="num now getRecordByURL" data-query="${queryString}" data-page="${response.page_list[i]}">${response.page_list[i]}</a>  `;
                } else {
                    html += `<a href="javascript:;" class="num getRecordByURL" data-query="${queryString}" data-page="${response.page_list[i]}">${response.page_list[i]}</a>  `
                }
            }
            $('.pre').after(html)

            // 如果有上一頁，改掉pre的onclick
            if ((response.current_page - 1) > 0 ){
                $('.pre').addClass('getRecordByURL')
                $('.pre').data('query', queryString)
                $('.pre').data('page', response.current_page-1)
                //$('.pre').attr('onclick',`getRecordByURL('${queryString}',${response.current_page - 1},null,null,null)`);
            }
            // 如果有下一頁，改掉next的onclick
            if (response.current_page < response.total_page){
                $('.next').addClass('getRecordByURL')
                $('.next').data('query', queryString)
                $('.next').data('page', response.current_page+1)
                //$('.next').attr('onclick',`getRecordByURL('${queryString}',${response.current_page + 1},null,null,null)`);
            }

            // 如果有前面的page list, 加上...
            if (response.current_page > 5){
                $('.pre').after(`<a href="javascript:;" class="num bd-0 getRecordByURL" data-query="${queryString}" data-page="${response.current_page-5}">...</a> `)
            }
            // 如果有後面的page list, 加上...
            if (response.page_list[response.page_list.length - 1] < response.total_page){
                if (response.current_page +5 > response.total_page){
                    $('.next').before(`<a href="javascript:;" class="num bd-0 getRecordByURL" data-query="${queryString}" data-page="${response.total_page}">...</a>`)
                } else {
                    $('.next').before(`<a href="javascript:;" class="num bd-0 getRecordByURL" data-query="${queryString}" data-page="${response.current_page+5}">...</a>`)
                }
            }

            $('.getRecordByURL').on('click', function(){
                getRecordByURL($(this).data('query'),$(this).data('page'),$(this).data('limit'),$(this).data('orderby'),$(this).data('sort'))
            })

        }

        $([document.documentElement, document.body]).animate({
            scrollTop: $(".sc_result").offset().top}, 200);

    })
    .fail(function( xhr, status, errorThrown ) {
        if (xhr.status==504){
            alert('要求連線逾時')
        } else {
            alert('發生未知錯誤！請聯絡管理員')
        }
        console.log( 'Error: ' + errorThrown + 'Status: ' + xhr.status)
    })
}

// submit search form
function submitSearch (page, from){

    let map_condition = '';
    if ($('p.active').data('type')=='map'){
        map_condition = '&' + $.param({'geojson': JSON.stringify(drawnItems.toGeoJSON()),'geo_type': 'map'})
    } else if ($('p.active').data('type')=='polygon'){
        map_condition = '&' + $.param({'geo_type': 'polygon'})
    } else if ($('p.active').data('type')=='circle'){
        map_condition = '&' + $.param({'geojson': JSON.stringify(drawnItems.toGeoJSON()), 'circle_radius': $('select[name=circle_radius]').val(),
        'center_lon': $('input[name=center_lon]').val(), 'center_lat': $('input[name=center_lat]').val(), 'geo_type': 'circle'})
    }

    let selected_col = ''

    // 如果是按搜尋，重新給query參數，若是從分頁則不用
    if (from == 'search'){
        //window.condition = $('#searchForm').serialize() + '&' + $.param({'geojson': $('#geojson_textarea').val()})
        var form = $(); //Initialize empty jQuery object
        //Iterate through all inputs, textareas
        $('#searchForm input,#searchForm select').each(function(){
            //Add to jQuery object if not empty
            if ($(this).val().length) {
                form = form.add($(this)); 
            }
        })
        window.condition = form.serialize() + map_condition
    } else {
        // 如果是從分頁，要記錄selected columns
        $(`.occ-choice input:checked`).each(function(){
            selected_col += '&selected_col=' + $(this).attr('id').replace('occ-','')
        })
    }

    history.pushState(null, '', window.location.pathname + '?' + window.condition + '&' + $.param({'page': page})+ '&from=' + from);


    $.ajax({
        url: "/get_conditional_records",
        data: window.condition + '&' + $.param({'page': page})+ '&from=' + from + '&csrfmiddlewaretoken=' + $csrf_token + selected_col,
        type: 'POST',
        dataType : 'json',
    })
    .done(function(response) {
        // clear previous results
        $('.sc_result').remove()
        $('.resultG_1, .resultG_10, .resultG_5, .resultG_100').remove()

        if (response.count == 0){
            $('.search_condition_are').after(`<div class="sc_result"><div class="no_data">暫無資料</div></div>`)
        } else {
            setTable(response, window.condition)

            // 判斷是從分頁或搜尋點選
            if (from == 'search'){
                // uncheck all first
                $(`input[id^="occ-"]`).prop('checked',false)
                // show selected columns
                for (let i = 0; i < response.selected_col.length; i++) {
                $(`.row-${response.selected_col[i]}`).removeClass('d-none');
                $(`#occ-${response.selected_col[i]}`).prop('checked',true);}
            } else {
                sendSelected()
            }

            // disable checkebox for common_name_c & scientificName
            $('#occ-common_name_c, #occ-scientificName').prop('disabled',true);
            $('#occ-common_name_c, #occ-scientificName').prop('checked',true);

            // append pagination
            if (response.total_page > 1){  // 判斷是否有下一頁，有才加分頁按鈕
                $('.result_table').after(
                    `<div class="d-flex-ai-c-jc-c">
                    <div class="page_number">
                    <a href="javascript:;" class="pre">
                        <span></span>
                    </a>
                    <a href="javascript:;" class="next">
                        <span></span>
                    </a>
                    </div>
                    <span class="ml-20px">
                        跳至<input name="jumpto page-jump" type="number" min="1" step="1">頁
                        <a class="jumpto pointer">GO</a>  
                    </span>
                    </div>`)
            }		

            $('.jumpto').on('click', function(){
                submitSearch($('input[name=jumpto]').val(),'page')
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

            $('.submitSearch').on('click', function(){
                submitSearch($(this).data('page'),$(this).data('from'))
            })
        }
        $([document.documentElement, document.body]).animate({
            scrollTop: $(".sc_result").offset().top}, 200);
    })
    .fail(function( xhr, status, errorThrown ) {
        if (xhr.status==504){
            alert('要求連線逾時')
        } else {
            alert('發生未知錯誤！請聯絡管理員')
        }
        console.log( 'Error: ' + errorThrown + 'Status: ' + xhr.status)
    })
}

function sendSelected(){
    let selected_field = $(`.occ-choice input:checked`)
    // 所有都先隱藏，除了common_name_c & scientificName
    $('td[class^="row-"]').addClass('d-none');
    $('.row-common_name_c, .row-scientificName').removeClass('d-none');
    // 再顯示選擇的欄位
    for (let i = 0; i < selected_field.length; i++) {
        $(`td.row-${selected_field[i].id.split('-')[1]}`).removeClass('d-none');
    }
    $(".popbg").addClass('d-none');
}