var $csrf_token = $('[name="csrfmiddlewaretoken"]').attr("value");


function getWKTMap() {
    var neLat = map.getBounds().getNorthEast()['lat'] 
    var neLng = map.getBounds().getNorthEast()['lng']
    var swLat = map.getBounds().getSouthWest()['lat']
    var swLng = map.getBounds().getSouthWest()['lng'] 

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

let map = L.map('map', { gestureHandling: true, minZoom: 2}).setView([23.5, 121.2], 7);

var southWest = L.latLng(-89.98155760646617, -179.9),
northEast = L.latLng(89.99346179538875, 179.9);
var bounds = L.latLngBounds(southWest, northEast);

map.setMaxBounds(bounds);
map.on('drag', function() {
    map.panInsideBounds(bounds, { animate: false });
});


L.tileLayer('https://{s}.tile.osm.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://osm.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);


map.on('zoomend', function zoomendEvent(ev) {
    var currentZoomLevel = ev.target.getZoom()
    drawMapGrid(currentZoomLevel)
});


map.on('dragend', function zoomendEvent(ev) {
    var currentZoomLevel = ev.target.getZoom()
    drawMapGrid(currentZoomLevel)
});


function drawMapGrid(currentZoomLevel){
    if (window.has_map){
        $('.loading_area').removeClass('d-none')

        if (currentZoomLevel < 6) {
            window.current_grid_level = 100
            // 這邊也改成後面再算
            $('[class^=resultG_]').addClass('d-none')
            $('.resultG_100').remove()
            $.ajax({
                url: "/get_map_grid",
                data: window.condition + '&grid=100&map_bound=' + getWKTMap() + '&csrfmiddlewaretoken=' + $csrf_token,
                type: 'POST',
                dataType: 'json',
            })
                .done(function (response) {
                    L.geoJSON(response, { className: 'resultG_100', style: style }).addTo(map);
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

            $('.resultG_100').removeClass('d-none')

        } else if (currentZoomLevel < 9) {
            window.current_grid_level = 10
            // 這邊也改成後面再算
            $('[class^=resultG_]').addClass('d-none')
            $('.resultG_10').remove()
            $.ajax({
                url: "/get_map_grid",
                data: window.condition + '&grid=10&map_bound=' + getWKTMap() + '&csrfmiddlewaretoken=' + $csrf_token,
                type: 'POST',
                dataType: 'json',
            })
                .done(function (response) {
                    L.geoJSON(response, { className: 'resultG_10', style: style }).addTo(map);
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

            $('.resultG_10').removeClass('d-none')

        } else if (currentZoomLevel < 11) {
            window.current_grid_level = 5
            $('[class^=resultG_]').addClass('d-none')
            $('.resultG_5').remove()
            $.ajax({
                url: "/get_map_grid",
                data: window.condition + '&grid=5&map_bound=' + getWKTMap() + '&csrfmiddlewaretoken=' + $csrf_token,
                type: 'POST',
                dataType: 'json',
            })
                .done(function (response) {
                    L.geoJSON(response, { className: 'resultG_5', style: style }).addTo(map);
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

            $('.resultG_5').removeClass('d-none')
        } else {
            window.current_grid_level = 1

            $('[class^=resultG_]').addClass('d-none')
            $('.resultG_1').remove()

            $.ajax({
                url: "/get_map_grid",
                data: window.condition + '&grid=1&map_bound=' + getWKTMap() + '&csrfmiddlewaretoken=' + $csrf_token,
                type: 'POST',
                dataType: 'json',
            })
                .done(function (response) {
                    L.geoJSON(response, { className: 'resultG_1', style: style }).addTo(map);
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

            $('.resultG_1').removeClass('d-none')
        }
    }
}

$(document).ready(function () {

    submitSearch()

    $('.popupField').on('click', function () {
        $(`.occ-choice`).removeClass('d-none')
        window.not_selected = $(`.occ-choice input:not(:checked)`)
        window.selected = $(`.occ-choice input:checked`)
    })

    $(".popbg .xx, .popbg .ovhy").click(function (e) {
        if ($(e.target).hasClass("choice-xx") || $(e.target).hasClass("choice-ovhy")) {
            window.not_selected.prop('checked', false);
            window.selected.prop('checked', true);
        }
    });

    $('.sendSelected').on('click', function () {
        sendSelected()
    })

    $('.selectAll').on('click', function () {
        $(`.occ-choice input:checkbox`).prop('checked', true);
    })

    $('.resetAll').on('click', function () {
        $(`.occ-choice input:checkbox:not(:disabled)`).prop('checked', false);
    })

    $('.downloadData').on('click', function () {
        let queryString = $(this).data('query')

        if ($('input[name=is_authenticated]').val() == 'True') {
            $.ajax({
                url: "/send_download_request",
                data: queryString + '&csrfmiddlewaretoken=' + $csrf_token,
                type: 'POST',
                dataType: 'json',
            })
            .done(function (response) {
                alert(gettext('請求已送出，下載檔案處理完成後將以Email通知'))
            })
            .fail(function (xhr, status, errorThrown) {
                if (xhr.status == 504) {
                    alert(gettext('要求連線逾時'))
                } else {
                    alert(gettext('發生未知錯誤！請聯絡管理員'))

                }
                console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
            })
        } else {
            alert(gettext('請先登入'))
        }
    })


    $('.downloadTaxon').on('click', function () {
        let queryString = $(this).data('query')
        if ($('input[name=is_authenticated]').val() == 'True') {
            $.ajax({
                url: "/send_download_request",
                data: queryString + '&csrfmiddlewaretoken=' + $csrf_token + '&taxon=yes',
                type: 'POST',
                dataType: 'json',
            })
            .done(function (result) {
                alert(gettext('請求已送出，下載檔案處理完成後將以Email通知'))
            })
            .fail(function (xhr, status, errorThrown) {
                if (xhr.status == 504) {
                    alert(gettext('要求連線逾時'))
                } else {
                    alert(gettext('發生未知錯誤！請聯絡管理員'))

                }
                console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
            })
        } else {
            alert(gettext('請先登入'))
        }
    })

    $('.downloadSensitive').on('click', function () {
        let queryString = $(this).data('query')
        if ($('input[name=is_authenticated]').val() == 'True') {
            window.open(`/${$lang}/sensitive_agreement?` + queryString)
        } else {
            alert(gettext('請先登入'))
        }
    })

    $('.open-ref').on('click', function(){
        window.open($(this).data('ref'))
    })

    $('.inf_databox .title').on('click', function () {
        $(this).next('.data-item').slideToggle();
        $(this).find('.arr').toggleClass('op');
    });

});


function setTable(response, queryString, from, orderby, sort) {


    // 如果有資料回傳則顯示table
    $('.downloadData').data('query', queryString)
    $('.downloadData').data('count', response.count)
    $('.downloadSensitive').data('query', queryString)
    $('.downloadSensitive').data('count', response.count)
    $('.downloadTaxon').data('query', queryString)
    $('.result_inf_top button.dwd').data('query', queryString)
    $('.result_inf_top_1 select[name="shownumber"]').data('query', queryString)
    $('.return-num').html(response.count.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ","))

    $('select[name=shownumber]').off('change')
    $('select[name=shownumber]').on('change', function () {
        submitSearch(1, 'page', false, $(this).val(), orderby, sort)
    })

    // 如果querystring裡面有limit的，修改shownumber
    $("select[name=shownumber]").val(response.limit);

    // 這邊如果是換頁的話不修改
    if (from != 'page'){
        // 如果有敏感資料才有申請按鈕
        if (!response.has_sensitive) {
            $('button.downloadSensitive').prop('disabled', true);
            $('button.downloadSensitive').addClass('dwd').removeClass('dw')
        } else {
            $('button.downloadSensitive').prop('disabled', false);
            $('button.downloadSensitive').addClass('dw').removeClass('dwd')
        }

        if (!response.has_species) {
            $('button.downloadTaxon').prop('disabled', true);
            $('button.downloadTaxon').addClass('dwd').removeClass('dw')
        } else {
            $('button.downloadTaxon').prop('disabled', false);
            $('button.downloadTaxon').addClass('dw').removeClass('dwd')
        }
    }
    
    // table title
    var table_title = document.createElement("tr");
    table_title.classList.add('table_title');
    let map_dict = response.map_dict;

    var function_td = document.createElement("td");
    var text = document.createTextNode(gettext('功能'));
    function_td.appendChild(text);
    table_title.appendChild(function_td);

    for (let i = 0; i < Object.keys(map_dict).length; i++) {
        var this_td = document.createElement("td");
        this_td.className = `row-${Object.keys(map_dict)[i]} d-none`;
        // 表格title
        var text = document.createTextNode(gettext(map_dict[Object.keys(map_dict)[i]]));
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
        let url_mask = "/occurrence/" + tmp.id.toString();
        tmp_td += `<td><a href=${url_mask} class="more" target="_blank">${gettext('查看')}</a></td>`
        for (let j = 0; j < Object.keys(map_dict).length; j++) {

            // 欄位內容
            tmp_value = tmp[Object.keys(map_dict)[j]];
            if (tmp_value == null) {
                tmp_td += `<td class="row-${Object.keys(map_dict)[j]} d-none"></td>`
            } else {
                if (['basisOfRecord','taxonRank','rightsHolder','dataGeneralizations','taxonGroup'].includes(Object.keys(map_dict)[j])){
                    tmp_value = gettext(tmp_value)
                }
                tmp_td += `<td class="row-${Object.keys(map_dict)[j]} d-none">${tmp_value}</td>`
            }
        }
        $('.record_table').append(`<tr>${tmp_td}</tr>`)
    }

    // 如果queryString裡面沒有指定orderby，使用scientificName
    $('.orderby').not(`[data-orderby=${response.orderby}]`).append('<i class="fa-solid fa-sort sort-icon"></i>')
    if (response.sort == 'asc') {
        $(`.orderby[data-orderby=${response.orderby}]`).append('<i class="fa-solid fa-sort-down sort-icon-active"></i>')
    } else {
        $(`.orderby[data-orderby=${response.orderby}]`).append('<i class="fa-solid fa-sort-up sort-icon-active"></i>')
        $(`.orderby[data-orderby=${response.orderby}]`).data('sort', 'desc');
    }

    $('.orderby').on('click', function () {
        if ($(this).children('svg').hasClass('fa-sort')) {
            $('.orderby:not(this)').children('svg').removeClass('fa-sort-down fa-sort-up sort-icon-active sort-icon').addClass('fa-sort sort-icon');
            $(this).children('svg').removeClass('fa-sort sort-icon-active sort-icon').addClass('fa-sort-down sort-icon-active');
            $(this).data('sort', 'asc');
        } else if ($(this).children('svg').hasClass('fa-sort-down')) {
            $('.orderby:not(this)').children('svg').removeClass('fa-sort-down fa-sort-up sort-icon-active sort-icon').addClass('fa-sort sort-icon');
            $(this).children('svg').removeClass('fa-sort sort-icon-active sort-icon').addClass('fa-sort-up sort-icon-active')
            $(this).data('sort', 'desc');
        } else {
            $('.orderby:not(this)').children('svg').removeClass('fa-sort-down fa-sort-up sort-icon-active sort-icon').addClass('fa-sort sort-icon');
            $(this).children('svg').removeClass('fa-sort sort-icon-active sort-icon').addClass('fa-sort-down sort-icon-active')
            $(this).data('sort', 'asc');
        }

        submitSearch(1, 'orderby', false, response.limit, $(this).data('orderby'), $(this).data('sort'))
    })

}


function submitSearch(page=1, from, new_click, limit, orderby, sort, push_state) {

    // if (push_state == null) { push_state = true }

        let selected_col = ''

        
        if (from == 'page' | from == 'orderby') {
            // 如果是從分頁，要記錄selected columns
            $(`.occ-choice input:checked`).each(function () {
                selected_col += '&selected_col=' + $(this).attr('id').replace('occ-', '')
            })
        }

        if (limit == null) {
            limit = 10
        }

        // 如果調整orderby and sort
        let orderby_str = ''
        if (orderby != null) {
            if (from == 'orderby') {
                page = 1
            }
            orderby_str = '&orderby=' + orderby + '&sort=' + sort
        }

        // 在這邊要先把過去queryString的page , from , limit拿掉
        window.condition = 'record_type=occ&datasetName=' + window.location.pathname.split('/')[2];
        const current_pars = new URLSearchParams(window.condition)

        current_pars.delete('page')
        current_pars.delete('from')
        current_pars.delete('limit')
        current_pars.delete('orderby')
        current_pars.delete('sort')
        current_pars.delete('csrfmiddlewaretoken')

        let queryString = current_pars.toString() + '&page=' + page + '&from=' + from + '&limit=' + limit + orderby_str
        window.condition = queryString

        if (queryString.length > 2000) {
            alert(gettext('您查詢的條件網址超過 2000 個字元，可能無法在所有瀏覽器中正常運作。'))
        } else {

            // if (push_state) {
            //     history.pushState(null, '', window.location.pathname + '?' + queryString)
            // }

            $(".loading_area").removeClass('d-none');

            if (map.getZoom() == undefined){
                window.current_grid_level = 10
            } else if (map.getZoom() < 6) {
                window.current_grid_level = 100
            } else if (map.getZoom() < 9) {
                window.current_grid_level = 10
            } else if (map.getZoom() < 11) {
                window.current_grid_level = 5
            } else {
                window.current_grid_level = 1
            }

            window.has_map = true

            $.ajax({
                url: "/get_conditional_records",
                data: queryString + '&csrfmiddlewaretoken=' + $csrf_token + selected_col + '&map_bound=' + getWKTMap() +'&grid=' + window.current_grid_level,
                type: 'POST',
                dataType: 'json',
            })
            .done(function (response) {

                if (response.message == 'exceed'){

                    $(".loading_area").addClass('d-none');
                    alert(gettext('超過系統可取得的頁數，請嘗試使用結果排序功能或縮小搜尋範圍'))

                } else {

                    // clear previous results
                    $('.record_table tr').remove()
                    $('.page-inf').remove()

                    if (response.count == 0) {
    
                        $('.records-legend').addClass('d-none')
                        $('.result_inf_top').addClass('d-none')
                        $('.result_inf_top_1').addClass('d-none')
                        $('.no_data').removeClass('d-none')
                        $('.resultG_1, .resultG_10, .resultG_5, .resultG_100').remove()

                    } else {
                            
                        $('.records-legend').removeClass('d-none')
    
                        $('.result_inf_top').removeClass('d-none')
                        $('.result_inf_top_1').removeClass('d-none')
    
                        $('.no_data').addClass('d-none')
    
                        // 在這步繪製地圖
                        if (from != 'page' & from != 'orderby') {
                            map.fire('dragend')
                        }
    
                        setTable(response, window.condition, from, orderby, sort)
    
                        // 判斷是從分頁或搜尋點選
                        if (from != 'page') {
                            // uncheck all first
                            $(`input[id^="occ-"]`).prop('checked', false)
                            // show selected columns
                            for (let i = 0; i < response.selected_col.length; i++) {
                                $(`.row-${response.selected_col[i]}`).removeClass('d-none');
                                $(`#occ-${response.selected_col[i]}`).prop('checked', true);
                            }
                        } else {
                            sendSelected()
                        }
    
                        // disable checkebox for common_name_c & scientificName
                        $('#occ-common_name_c, #occ-scientificName').prop('disabled', true);
                        $('#occ-common_name_c, #occ-scientificName').prop('checked', true);
    
                        // append pagination
    
                        if (response.total_page > 1) {  // 判斷是否有下一頁，有才加分頁按鈕
                            $('.result_table').after(
                                `<div class="page-inf">
                                    <div class="page_number">
                                    <a class="pre">
                                        <span></span>
                                    </a>
                                    <a class="next">
                                        <span></span>
                                    </a>
                                    </div>
                                </div>`)
                        }
    
                        let html = ''
                        for (let i = 0; i < response.page_list.length; i++) {
                            if (response.page_list[i] == response.current_page) {
                                html += `<a class="num now submitSearch" data-page="${response.page_list[i]}" data-from="page">${response.page_list[i]}</a>  `;
                            } else {
                                html += `<a class="num submitSearch" data-page="${response.page_list[i]}" data-from="page">${response.page_list[i]}</a>  `
                            }
                        }
                        $('.pre').after(html)
    
                        if ((response.current_page - 1) > 0) {
                            $('.pre').addClass('submitSearch')
                            $('.pre').data('page', response.current_page - 1)
                            $('.pre').data('from', 'page')
                        }
                        // 如果有下一頁，改掉next的onclick
                        if (response.current_page < response.total_page) {
                            $('.next').addClass('submitSearch')
                            $('.next').data('page', response.current_page + 1)
                            $('.next').data('from', 'page')
                        }
    
                        // 如果有前面的page list, 加上...
                        if (response.current_page > 5) {
                            $('.pre').after(`<a class="num bd-0 submitSearch" data-page="${response.current_page - 5}" data-from="page">...</a> `)
                        }
                        // 如果有後面的page list, 加上...
                        if (response.page_list[response.page_list.length - 1] < response.total_page) {
                            if (response.current_page + 5 > response.total_page) {
                                $('.next').before(`<a class="num bd-0 submitSearch" data-page="${response.total_page}" data-from="page">...</a> `)
                            } else {
                                $('.next').before(`<a class="num bd-0 submitSearch" data-page="${response.current_page + 5}" data-from="page">...</a>`)
                            }
                        }
    
                        $('.return-total-page').html(response.total_page)
    
                        if (response.total_page > 1 && !response.page_list.includes(1)) {
                            $('.pre').after('<a class="num mr-5px submitSearch" data-page="1" data-from="page">1</a>')
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
    
                        $('.page_number a.submitSearch').on('click', function () {
                            submitSearch($(this).data('page'), $(this).data('from'), false, $(this).data('limit'), $(this).data('orderby'), $(this).data('sort'))
                        })
                        
                    }
    
                    $('.sc_result').removeClass('d-none')
                    $(".loading_area").addClass('d-none');
                    $([document.documentElement, document.body]).animate({
                        scrollTop: $(".sc_result").offset().top - 80
                    }, 200);
    
                }

            })
            .fail(function (xhr, status, errorThrown) {
                if (xhr.status == 504) {
                    alert(gettext('要求連線逾時'))
                } else {
                    alert(gettext('發生未知錯誤！請聯絡管理員'))

                }
                $(".loading_area").addClass('d-none');
                console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
            })
        }
}



function sendSelected() {
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
