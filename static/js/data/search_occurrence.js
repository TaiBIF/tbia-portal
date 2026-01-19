var $csrf_token = $('[name="csrfmiddlewaretoken"]').attr("value");

let selectBox = new vanillaSelectBox("#rightsHolder", {
    placeHolder: gettext("來源資料庫"),
    search: true, disableSelectAll: true,
    translations: { "all": gettext("全部"), "items": gettext(" 個選項"), "clearAll": gettext("重設") }
});

// set value 之後再加event 不然會被洗掉
$('#rightsHolder').on('change', function (e) {

    e.preventDefault()
    let res = selectBox.getResult()
    let h_str = ''
    for (r of res) {
        h_str += 'holder=' + r + '&'
    }

    let d_str = ''
    if (window.has_par) {
        d_str = '&'
        for (dd in window.d_list){
            d_str += 'datasetKey=' + window.d_list[dd] + '&'
        }
    }    

    // dataset的顏色拿掉
    $('#btn-group-datasetName button span.title').removeClass('black').addClass('color-707070')

    $.ajax({
        url: "/change_dataset?" + h_str + d_str,
        dataType: 'json',
    })
    .done(function (response) {
        if (response.length > 0) {
            selectBox2.enable()
            selectBox2.changeTree(response)
            if (window.has_par) {
                selectBox2.setValue(window.d_list)
            }
        } else {
            selectBox2.disable()
        }
    })

})


let selectBox2 = new vanillaSelectBox("#datasetName",
    {
        search: true,
        placeHolder: gettext("資料集名稱"),
        disableSelectAll: true,
        remote: {
            "onSearch": doSearchDataset, // used for search and init
            "onInitSize": 10, // if > 0 onSearch is used for init to populate le select element with the {onInitSize} first elements
            "onInit": initDataset,
        },
        translations: { "all": gettext("全部"), "items": gettext(" 個選項"), "clearAll": gettext("重設") }
    });
/*
let selectBox3 = new vanillaSelectBox("#sensitiveCategory",{placeHolder:"敏感層級",search:false, disableSelectAll: true,
});*/

let selectBox4 = new vanillaSelectBox("#basisOfRecord", {
    placeHolder: gettext("紀錄類型"), search: false, disableSelectAll: true,
});

let selectBox5 = new vanillaSelectBox("#taxonRank", {
    placeHolder: gettext("鑑定層級"), search: false, disableSelectAll: true,
});

let selectBox6 = new vanillaSelectBox("#circle_radius", {
    placeHolder: gettext("半徑"), search: false, disableSelectAll: true,
});
selectBox6.setValue('1')

let selectBox7 = new vanillaSelectBox("#has_image", {
    placeHolder: gettext("有無影像"), search: false, disableSelectAll: true,
});


let selectBox8 = new vanillaSelectBox("#higherTaxa",
    {
        search: true,
        placeHolder: gettext("較高分類群"),
        disableSelectAll: true,
        remote: {
            "onSearch": doSearch, // used for search and init
            "onInitSize": 10, // if > 0 onSearch is used for init to populate le select element with the {onInitSize} first elements
            "onInit": inithigherTaxa,
        }
    });

let selectBox9 = new vanillaSelectBox("#taxonGroup", {
    placeHolder: gettext("物種類群"), search: false, disableSelectAll: true,
});

let selectBox10 = new vanillaSelectBox("#locality",
    {
        search: true,
        placeHolder: gettext("出現地"),
        disableSelectAll: true,
        remote: {
            "onSearch": doSearchLocality, // used for search and init
            "onInitSize": 10, // if > 0 onSearch is used for init to populate le select element with the {onInitSize} first elements
            "onInit": initLocality,
        },
        translations: { "all": gettext("全部"), "items": gettext(" 個選項"), "clearAll": gettext("重設") }
    });


let selectBox11 = new vanillaSelectBox("#is_native", {
    placeHolder: gettext("是否為原生種"), search: false, disableSelectAll: true,
});

let selectBox12 = new vanillaSelectBox("#is_protected", {
    placeHolder: gettext("是否為保育類"), search: false, disableSelectAll: true,
});

let selectBox13 = new vanillaSelectBox("#county", {
    placeHolder: gettext("縣市"), search: false, disableSelectAll: true,
});


$('#county').on('change', function (e) {

    e.preventDefault()
    let res = selectBox13.getResult()
    selectBox14.changeTree([{ 'value': '', 'text': gettext('-- 不限 --') }])

    // municipality 的顏色拿掉
    $('#btn-group-municipality button span.title').removeClass('black').addClass('color-707070')

    $.ajax({
        url: "/change_municipality?county=" + res,
        dataType: 'json',
    })
    .done(function (response) {

        if (response.length > 0) {
            
            selectBox14.enable()
            final_resp = response
            final_resp.unshift({ 'value': '', 'text': gettext('-- 不限 --') })
            selectBox14.changeTree(final_resp)

            if (window.has_municipality) {
                selectBox14.setValue(window.municipality)
                $('#btn-group-municipality button span.title').addClass('black').removeClass('color-707070')
                window.has_municipality = false
            } else {
                $('#btn-group-municipality button span.title').removeClass('black').addClass('color-707070')
            }
        } else {

            selectBox14.empty()
        }
    })

})



let selectBox14 = new vanillaSelectBox("#municipality", {
    placeHolder: gettext("鄉鎮市區"), search: false, disableSelectAll: true,
});

function doSearchLocality(what, datasize) {
    let valueProperty = "value";
    let textProperty = "text";

    // 如果搜尋關鍵字為空，直接調用初始化邏輯
    if (what === "" || what === undefined) {
        return initLocality("", 10); 
    }

    return new Promise(function (resolve, reject) {
        var xhr = new XMLHttpRequest();
        xhr.overrideMimeType("application/json");
        xhr.open('GET', '/get_locality?locality=' + what, true);
        xhr.onload = function () {
            if (this.status >= 200 && this.status < 300) {
                var data = JSON.parse(xhr.response);
                let processedData = [];

                // 有輸入關鍵字時，只返回搜尋結果，不包含預設選項
                processedData = data.filter(function (x) {
                    let name = x[textProperty].toLowerCase();
                    what = what.toLowerCase();
                    return name.slice(what).search(getVariants(escapeRegExp(what))) != -1;
                }).map(function (x) {
                    return {
                        value: x[valueProperty],
                        text: x[textProperty]
                    };
                });

                resolve(processedData);
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

function initLocality(what, datasize) {
    let valueProperty = "value";
    let textProperty = "text";
    // let urlParams = new URLSearchParams(window.location.search);
    // let keyword_list = urlParams.getAll('locality')

    return new Promise(function (resolve, reject) {
        var xhr = new XMLHttpRequest();
        xhr.overrideMimeType("application/json");
        // xhr.open('GET', '/get_locality_init?locality=' + keyword_list.join('&locality='), true);
        xhr.open('GET', '/get_locality_init', true);
        xhr.onload = function () {
            if (this.status >= 200 && this.status < 300) {
                var data = JSON.parse(xhr.response);
                let processedData = [];

                if (what == "" && datasize != undefined && datasize > 0) {
                    processedData = data.slice(0, datasize).map(function (x) {
                        return {
                            value: x[valueProperty],
                            text: x[textProperty]
                        };
                    });
                } else {
                    // 這裡是搜尋邏輯，不包含預設選項
                    processedData = data.filter(function (x) {
                        let name = x[textProperty].toLowerCase();
                        what = what.toLowerCase();
                        return name.slice(what).search(getVariants(escapeRegExp(what))) != -1;
                    }).map(function (x) {
                        return {
                            value: x[valueProperty],
                            text: x[textProperty]
                        };
                    });
                }

                resolve(processedData);
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
        weight: 0.7,
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

var legend = L.control({position: 'bottomright'});

legend.onAdd = function (map) {
    var div = L.DomUtil.create('div', 'info legend map-legend d-none'),
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

legend.addTo(map);

L.tileLayer('https://{s}.tile.osm.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://osm.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);
var drawnItems = new L.FeatureGroup();
map.addLayer(drawnItems);

drawControl = new L.Control.Draw({
    draw: {
        position: 'topleft',
        polyline: false,
        rectangle: true,
        circle: false,
        polygon: true,
        marker: false,
        circlemarker: false
    },
    edit: {
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
    drawnItems.addLayer(layer);
});

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
                    L.geoJSON(response, { className: 'resultG_100', style: style, onEachFeature: onEachFeature }).addTo(map);
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
                    L.geoJSON(response, { className: 'resultG_10', style: style, onEachFeature: onEachFeature }).addTo(map);
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
                    L.geoJSON(response, { className: 'resultG_5', style: style, onEachFeature: onEachFeature }).addTo(map);
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
                    L.geoJSON(response, { className: 'resultG_1', style: style, onEachFeature: onEachFeature }).addTo(map);
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

function whenClicked(e) {

    const current_pars = new URLSearchParams(window.condition)

    current_pars.delete('current_grid_level')
    current_pars.delete('current_grid')

    let queryString = current_pars.toString() + '&current_grid_level=' + e.target.feature.properties.current_grid_level + '&current_grid=' + e.target.feature.properties.current_grid
    window.condition = queryString

    submitSearch(1, 'map', false, $('select[name=shownumber]').find(':selected').val(), 'scientificName', 'desc', null) 

}
  
function onEachFeature(feature, layer) {
    //bind click
    layer.on({
        click: whenClicked,
        mouseover: (e) => {
            e.target.setStyle({color: '#3c8299', weight: 2});
          },
        mouseout: (e) => {
            e.target.setStyle({color: '#b2d2dd', weight: 0.7});
          },
  
    });
}
  
  

function initDataset(what, datasize) {
    let valueProperty = "value";
    let textProperty = "text";

    return new Promise(function (resolve, reject) {
        var xhr = new XMLHttpRequest();
        xhr.overrideMimeType("application/json");
        xhr.open('GET', '/change_dataset', true);
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
                        if (name.slice(what).search(getVariants(escapeRegExp(what))) != -1)
                            return {
                                value: x[valueProperty],
                                text: x[textProperty]
                            }
                    });
                }
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


function doSearchDataset(what, datasize) {
    let valueProperty = "value";
    let textProperty = "text";

    // 要限制來源資料庫
    let res = selectBox.getResult()
    let h_str = ''
    for (r of res) {
        h_str += '&holder=' + r
    }

    return new Promise(function (resolve, reject) {
        var xhr = new XMLHttpRequest();
        xhr.overrideMimeType("application/json");
        xhr.open('GET', '/get_dataset?keyword=' + what + h_str, true);
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
                        if (name.slice(what).search(getVariants(escapeRegExp(what))) != -1)
                            return {
                                value: x[valueProperty],
                                text: x[textProperty]
                            }
                    });
                }
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

$(function () {

    $('.resetSearch, .clearGeo').on('click',function(){
        $('.map-legend, .selected_grid_area').addClass('d-none')
    })

    $('#searchForm').on('submit', function(event) { 
        event.preventDefault()
        $('.search_condition_are .submitSearch').trigger('click')
    });


    $('.redirectTBN').on('click', function () {

        $('.tbn-url').attr('href',''); 
        $('.matched_tbn_search').html(''); 
        $('.not_matched_tbn_search').html(''); 
        let queryString = $(this).data('query')

        $.ajax({
            url: "/get_tbn_query",
            data: queryString + '&csrfmiddlewaretoken=' + $csrf_token,
            type: 'POST',
            dataType: 'json',
        })
        .done(function (response) {
            // console.log(response.tbn_url)
            $('.tbn_popup').removeClass('d-none');
            $('.tbn-url').attr('href',response.tbn_url);

            for (i of response.tbn_query ){

                $('.matched_tbn_search').append(`<li>${i}</li>`)

            }

            for (i of response.tbn_error ){
                $('.not_matched_tbn_search').append(`<li>${i}</li>`)
            }
        })
        .fail(function (xhr, status, errorThrown) {
            if (xhr.status == 504) {
                alert(gettext('要求連線逾時'))
            } else {
                alert(gettext('發生未知錯誤！請聯絡管理員'))

            }
            console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
        })
    })


    $('.downloadData').on('click', function () {
        let queryString = $(this).data('query')
        
        if ($('input[name=is_authenticated]').val() == 'True') {
            // 清除選項並顯示 pop box
            clearUserStatForm();
            $('#userStatModal').removeClass('d-none');
            
            // 暫存原本的 query string
            $('#userStatModal').data('original-query', queryString);
        } else {
            alert(gettext('請先登入'))
        }
    })

    $('.downloadTaxon').on('click', function () {
        let queryString = $(this).data('query')
        queryString += '&taxon=yes'
        
        if ($('input[name=is_authenticated]').val() == 'True') {
            // 清除選項並顯示 pop box
            clearUserStatForm();
            $('#userStatModal').removeClass('d-none');
            
            // 暫存原本的 query string
            $('#userStatModal').data('original-query', queryString);
        } else {
            alert(gettext('請先登入'))
        }
    })

    // 清除表單選項
    function clearUserStatForm() {
        $('input[name="user_affiliation"]').prop('checked', false);
        $('input[name="user_role"]').prop('checked', false);
        $('input[name="user_purpose"]').prop('checked', false);
    }

    // 確認送出按鈕
    $('#userStatConfirm').on('click', function () {
        // 檢查是否都有選取
        let affiliation = $('input[name="user_affiliation"]:checked').val();
        let role = $('input[name="user_role"]:checked').val();
        let purpose = $('input[name="user_purpose"]:checked').val();
        
        if (!affiliation || !role || !purpose) {
            alert('請完成所有必填項目');
            return;
        }
        
        // 組合 query string
        let originalQuery = $('#userStatModal').data('original-query');
        let userStatQuery = `&user_affiliation=${affiliation}&user_role=${role}&user_purpose=${purpose}`;
        let finalQuery = originalQuery + userStatQuery;
        
        // 關閉 modal
        // $('#userStatModal').hide();
        $('#userStatModal').addClass('d-none');
        // 執行原本的下載流程
        executeDownload(finalQuery);
    });

    // 執行下載
    function executeDownload(queryString) {
        // console.log(queryString);
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
    }


    // $('.downloadData').on('click', function () {

    //     // TODO 這邊要先跳出使用者統計pop
    //     let queryString = $(this).data('query')

    //     if ($('input[name=is_authenticated]').val() == 'True') {
    //         $.ajax({
    //             url: "/send_download_request",
    //             data: queryString + '&csrfmiddlewaretoken=' + $csrf_token,
    //             type: 'POST',
    //             dataType: 'json',
    //         })
    //         .done(function (response) {
    //             alert(gettext('請求已送出，下載檔案處理完成後將以Email通知'))
    //         })
    //         .fail(function (xhr, status, errorThrown) {
    //             if (xhr.status == 504) {
    //                 alert(gettext('要求連線逾時'))
    //             } else {
    //                 alert(gettext('發生未知錯誤！請聯絡管理員'))

    //             }
    //             console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
    //         })
    //     } else {
    //         alert(gettext('請先登入'))
    //     }
    // })

    // $('.downloadTaxon').on('click', function () {
    //     // TODO 這邊要先跳出使用者統計pop
    //     let queryString = $(this).data('query')
    //     if ($('input[name=is_authenticated]').val() == 'True') {
    //         $.ajax({
    //             url: "/send_download_request",
    //             data: queryString + '&csrfmiddlewaretoken=' + $csrf_token + '&taxon=yes',
    //             type: 'POST',
    //             dataType: 'json',
    //         })
    //         .done(function (result) {
    //             alert(gettext('請求已送出，下載檔案處理完成後將以Email通知'))
    //         })
    //         .fail(function (xhr, status, errorThrown) {
    //             if (xhr.status == 504) {
    //                 alert(gettext('要求連線逾時'))
    //             } else {
    //                 alert(gettext('發生未知錯誤！請聯絡管理員'))

    //             }
    //             console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
    //         })
    //     } else {
    //         alert(gettext('請先登入'))
    //     }
    // })

    $('.downloadSensitive').on('click', function () {
        let queryString = $(this).data('query')
        if ($('input[name=is_authenticated]').val() == 'True') {
            window.open(`/${$lang}/sensitive_agreement?` + queryString)
        } else {
            alert(gettext('請先登入'))
        }
    })

    $('.popupField').on('click', function () {
        $(`.occ-choice`).removeClass('d-none')
        window.not_selected = $(`.occ-choice input:not(:checked)`)
        window.selected = $(`.occ-choice input:checked`)
    })


    $('.resetSearch').on('click', function () {
        $('.clearGeo').trigger('click')
        $('.search_condition_are #searchForm').trigger("reset");
        window.has_par = false
        window.has_municipality = false
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
        selectBox11.empty()
        selectBox12.empty()
        selectBox13.empty()
        selectBox14.empty()
        selectBox14.changeTree([{ 'value': '', 'text': gettext('-- 不限 --') }])
    })

    $('.sendSelected').on('click', function () {
        sendSelected()
    })

    $('.selectAll').on('click', function () {
        $(`.occ-choice input:checkbox`).prop('checked', true);
    })

    $('.resetAll').on('click', function () {
        $(`.occ-choice input:checkbox:not(:disabled)`).prop('checked', false);
    })

    $('.submitSearch').on('click', function () {
        submitSearch($(this).data('page'), $(this).data('from'), $(this).data('new_click'))
    })

    let start_date_picker = new AirDatepicker('#start_date',
        { locale: date_locale, dateFormat: 'yyyy-MM-dd' });

    let end_date_picker = new AirDatepicker('#end_date',
        { locale: date_locale, dateFormat: 'yyyy-MM-dd' });

    $('.show_start').on('click', function () {
        if (start_date_picker.visible) {
            start_date_picker.hide();
        } else {
            start_date_picker.show();
        }
    })

    $('.show_end').on('click', function () {
        if (end_date_picker.visible) {
            end_date_picker.hide();
        } else {
            end_date_picker.show();
        }
    })

    $('.mapGeo').on('click', function () {
        $('.addC, .addG').remove()
        $('p.active').removeClass('active')
        $('.mapGeo').addClass('active');
        $('.leaflet-control.leaflet-draw').removeClass('d-none')
    })

    // 從圓中心框選
    $('.circleGeo').on('click', function () {
        $('.addC, .addG').remove()
        $('.leaflet-control.leaflet-draw').addClass('d-none')
        $(".circle_popup").removeClass('d-none')
    })

    $('.popupGeo').on('click', function () {
        $('.addC').remove()
        $('.leaflet-control.leaflet-draw').addClass('d-none')
        $(".geojson_popup").removeClass('d-none')
    })

    $('.clearGeo').on('click', function () {
        $('p.active').removeClass('active')
        $('.leaflet-control.leaflet-draw').addClass('d-none')
        drawnItems.clearLayers();
        $('.addG, .addC, .addM').remove()
        $('input[name=center_lat]').val('')
        $('input[name=center_lon]').val('')
        $("#circle_radius").val("1").trigger("change");
        $('#geojson_textarea').val('')
        $('input[name=geojson_id]').val('')
        $('[class^=resultG_]').remove()
    })

    $(".popbg .xx, .popbg .ovhy").click(function (e) {
        if ($(e.target).hasClass("choice-xx") || $(e.target).hasClass("choice-ovhy")) {
            window.not_selected.prop('checked', false);
            window.selected.prop('checked', true);
        }
    });

    // disable string input in 數量
    $("#searchForm input[name=organismQuantity]").on("keyup", function () {
        this.value = this.value.replace(/\D/g, '');
    });

    $('.circle_send').click(function () {
        let center_lat = $('input[name=center_lat]').val()
        let center_lon = $('input[name=center_lon]').val()
        $('input[name=center_lat]').val(center_lat.trim())
        $('input[name=center_lon]').val(center_lon.trim())

        // 先把舊的移除
        $('.addC, [class^=resultG_], .addM, .addG').remove()
        if (($('input[name=center_lat]').val() == '') | ($('input[name=center_lon]').val() == '')) {
            alert(gettext('框選失敗！請檢查經緯度格式是否正確'))
        } else if ($('input[name=center_lat]').val() > 90 | $('input[name=center_lat]').val() < -90 | $('input[name=center_lon]').val() > 180 | $('input[name=center_lon]').val() < -180) {
            alert(gettext('框選失敗！請檢查經緯度數值是否正確'))
        } else {
            try {
                let circle = L.circle([$('input[name=center_lat]').val(), $('input[name=center_lon]').val()],
                    parseInt($('select[name=circle_radius]').val(), 10) * 1000, { className: 'addC' }).addTo(map);
                drawnItems.clearLayers();
                drawnItems.addLayer(circle);
                // 這邊要重設
                window.has_map = false
                map.fitBounds(circle.getBounds());
                $('p.active').removeClass('active')
                $('.circleGeo').addClass('active');
                $(".circle_popup").addClass('d-none')
            } catch (e) {
                alert(gettext('框選失敗！請檢查經緯度格式是否正確'))
            }
        }
    })

    $('.geojson_send').click(function () {

        let geoStr = $('#geojson_textarea').val();
        let geoObj;

        try {
            geoObj = JSON.parse(geoStr);
        } catch (e) {
            alert(gettext('上傳失敗！請檢查GeoJSON格式是否正確'));
            return;
        }

        // 格式正確 → 檢查大小
        let geoSizeBytes = new Blob([geoStr]).size;
        let maxSizeBytes = 15 * 1024 * 1024;  // 15 MB

        if (geoSizeBytes > maxSizeBytes) {
            alert(gettext('GeoJSON超過大小上限，請先簡化圖形後再上傳（上限15MB）'));
            return;
        }

        // 先把舊的移除
        $('.addG, [class^=resultG_], .addC, .addM').remove()

        $.ajax({
            url: "/save_geojson",
            data: {
                geojson_text: JSON.stringify(geoObj),
                csrfmiddlewaretoken: $csrf_token
            },
            type: 'POST',
            dataType: 'json',
        })
        .done(function (response) {
            $('input[name=geojson_id]').val(response.geojson_id)
            geoJSON = L.geoJSON(JSON.parse(response.geojson), { className: 'addG' }).addTo(map);
            window.has_map = false
            map.fitBounds(geoJSON.getBounds());
            $('p.active').removeClass('active')
            $(".geojson_popup").addClass('d-none')
            $('.popupGeo').addClass('active');
            drawnItems.clearLayers();
        })
        .fail(function (xhr, status, errorThrown) {
            if (xhr.status == 504) {
                alert(gettext('要求連線逾時'))
            } else {
                alert(gettext('發生未知錯誤！請聯絡管理員'))
            }
            console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
        })

    })

    // 如果按上下一頁
    window.onpopstate = function (event) {
        drawnItems.clearLayers();
        $('.addG, .addC, .addM, .resultG_1, .resultG_10, .resultG_5, .resultG_100').remove()
        changeAction();
    };

});


function doSearch(what, datasize) {
    let valueProperty = "value";
    let textProperty = "text";

    // 如果搜尋關鍵字為空，直接調用初始化邏輯
    if (what === "" || what === undefined) {
        return inithigherTaxa("", 10);
    }

    return new Promise(function (resolve, reject) {
        var xhr = new XMLHttpRequest();
        xhr.overrideMimeType("application/json");
        xhr.open('GET', `/get_higher_taxa?keyword=${what}&lang=${$lang}`, true);
        xhr.onload = function () {
            if (this.status >= 200 && this.status < 300) {
                var data = JSON.parse(xhr.response);

                // 搜尋並過濾資料
                let filteredData = data.filter(function (x) {
                    let name = x[textProperty].toLowerCase();
                    what = what.toLowerCase();
                    return name.search(getVariants(escapeRegExp(what))) !== -1;
                });

                let processedData = filteredData.map(function (x) {
                    return {
                        value: x[valueProperty],
                        text: x[textProperty]
                    };
                });

                // 重要：只有當有搜尋結果時才加入「-- 不限 --」
                // 如果沒有搜尋結果，就不加入，讓 vanillaSelectBox 知道要顯示「沒有符合的項目」
                if (processedData.length > 0) {
                    processedData = [{ 'value': '', 'text': gettext('-- 不限 --') }].concat(processedData);
                }
                
                resolve(processedData);
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
// 修改 inithigherTaxa 函數 - 加入預設選項（但保留原始邏輯）
function inithigherTaxa(what, datasize) {
    let valueProperty = "value";
    let textProperty = "text";
    let urlParams = new URLSearchParams(window.location.search);
    let taxon_id = urlParams.get('higherTaxa')
    let get_url = '/get_higher_taxa'
    if (taxon_id) {
        get_url += `?taxon_id=${taxon_id}`
    }

    return new Promise(function (resolve, reject) {
        var xhr = new XMLHttpRequest();
        xhr.overrideMimeType("application/json");
        xhr.open('GET', get_url, true);
        xhr.onload = function () {
            if (this.status >= 200 && this.status < 300) {
                var data = JSON.parse(xhr.response);
                let processedData = [];

                if (what == "" && datasize != undefined && datasize > 0) {
                    processedData = data.slice(0, datasize).map(function (x) {
                        return {
                            value: x[valueProperty],
                            text: x[textProperty]
                        };
                    });
                } else {
                    processedData = data.filter(function (x) {
                        let name = x[textProperty].toLowerCase();
                        what = what.toLowerCase();
                        return name.slice(what).search(getVariants(escapeRegExp(what))) != -1;
                    }).map(function (x) {
                        return {
                            value: x[valueProperty],
                            text: x[textProperty]
                        };
                    });
                }

                // 加入預設選項（這邊原本就有，保持不變）
                processedData = [{ 'value': '', 'text': gettext('-- 不限 --') }].concat(processedData);
                
                resolve(processedData);
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

function changeAction() {

    $('#btn-group-circle_radius button span.title').addClass('black').removeClass('color-707070')
    $('.vsb-main button').css('border', '').css('background', '')

    let select_length = $(".search_condition_are select, .circle_popup select").length;
    for (let i = 0; i < select_length; i++) {
        let tmp_id = $(".search_condition_are select, .circle_popup select")[i].id;

        $(`#${tmp_id}`).on('change', function () {
            if ($(`#btn-group-${tmp_id} ul li.active`).length > 0) {
                $(`#btn-group-${tmp_id} button span.title`).addClass('black').removeClass('color-707070')
            } else {
                $(`#btn-group-${tmp_id} button span.title`).addClass('color-707070').removeClass('black')
            }
        })
    }

    let queryString = window.location.search;
    let urlParams = new URLSearchParams(queryString);

    //selectBox10.setValue('')

    if (queryString.split('&').length > 1) {
        window.condition = queryString.substring(1)

        // 把條件填入表格
        let entries = urlParams.entries();

        let d_list = Array();
        let r_list = Array();
        let l_list = Array();
        let county;

        for (const [key, value] of entries) {
            if (key == 'datasetName') {
                d_list.push(value)
            } else if (key == 'rightsHolder') {
                r_list.push(value)
                /*} else if (key == 'sensitiveCategory') {
                    selectBox3.setValue(value)*/
            } else if (key == 'basisOfRecord') {
                selectBox4.setValue(value)
            } else if (key == 'taxonRank') {
                selectBox5.setValue(value)
            } else if (key == 'has_image') {
                selectBox7.setValue(value)
            } else if (key == 'is_native') {
                selectBox11.setValue(value)
            } else if (key == 'is_protected') {
                selectBox12.setValue(value)
            } else if (key == 'county') {
                county = value
            } else if (key == 'municipality') {
                window.has_municipality = true
                window.municipality = value
            } else if (key == 'higherTaxa') {
                console.log(value)
            } else if (key == 'taxonGroup') {
                selectBox9.setValue(value)
            } else if (key == 'locality') {
                l_list.push(value)
                //selectBox10.setValue(value)
            } else {

                $(`[name=${key}]`).val(value)
                // map按鈕
                if (key == 'geo_type') {
                    $(`.btnupload p[data-type=${value}]`).addClass("active")

                    // 把地圖畫上去
                    if (urlParams.get('geo_type') == 'circle') {
                        let circle = L.circle([urlParams.get('center_lat'), urlParams.get('center_lon')],
                            parseInt(urlParams.get('circle_radius'), 10) * 1000, { className: 'addC' }).addTo(map);
                        selectBox6.setValue(urlParams.get('circle_radius'))
                        $('#btn-group-circle_radius button span.title').addClass('black').removeClass('color-707070')
                        drawnItems.addLayer(circle);
                        map.fitBounds(circle.getBounds());
                    } else if (urlParams.get('geo_type') == 'map') {
                        var wkt = new Wkt.Wkt();
                        if (urlParams.getAll('polygon')) {
                            for (let i = 0; i < urlParams.getAll('polygon').length; i++) {
                                wkt.read(urlParams.getAll('polygon')[i])
                                obj = wkt.toObject({ className: 'addM' });
                                obj.addTo(map);
                                drawnItems.addLayer(obj);
                            }
                        }
                    } else if (urlParams.get('geo_type') == 'polygon'){
                        if (urlParams.get('geojson_id') != '') {

                            fetch(`/media/geojson/${value}.json`).then((res) => {
                                if (res.ok) {
                                    $('#geojson_textarea').val(JSON.stringify(res.json()))
                                    $.getJSON(`/media/geojson/${value}.json`, function (ret) {
                                        let geoJSON = L.geoJSON(ret, { className: 'addG' }).addTo(map);
                                        map.fitBounds(geoJSON.getBounds());
                                    });
                                } else {
                                    $(`.btnupload p[data-type=polygon]`).removeClass("active")
                                }
                            });
                        }
                    }
                }

            }
        }

        if (d_list.length > 0) {
            window.d_list = d_list;
            window.has_par = true;
        }

        selectBox.setValue(r_list);
        selectBox2.setValue(d_list);
        selectBox10.setValue(l_list);

        if (county){
            selectBox13.setValue(county)
            $("#county").change();
        } else if (window.has_municipality){
            // 這邊會沒辦法append
            selectBox14.setValue(window.municipality)
        }

        // 如果有選項的 顏色改為黑色
        let select_length = $(".search_condition_are [id^=btn-group-]").length;
        for (let i = 0; i < select_length; i++) {
            let tmp_id = $(".search_condition_are [id^=btn-group-]")[i].id;
            if ($(`#${tmp_id} .vsb-menu ul li.active`).length > 0) {
                $(`#${tmp_id} button span.title`).addClass('black').removeClass('color-707070')
            } else {
                $(`#${tmp_id} button span.title`).addClass('color-707070').removeClass('black')
            }
        }

        if (urlParams.get('page')) {
            page = urlParams.get('page')
        } else {
            page = 1
        }
        submitSearch(page, 'change', false, urlParams.get('limit'), urlParams.get('orderby'), urlParams.get('sort'), false)

    }
}

function setTable(response, queryString, from, orderby, sort) {

    // 如果有資料回傳則顯示table
    $('.redirectTBN').data('query', queryString)
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
        if (Object.keys(map_dict)[i]!='associatedMedia'){
            a.className = 'orderby';
            a.dataset.orderby = Object.keys(map_dict)[i];
            a.dataset.sort = 'asc';
        }
        this_td.appendChild(text);
        this_td.appendChild(a);
        table_title.appendChild(this_td);
    }

    $('.record_table').append(table_title);

    // console.log(map_dict);

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
                if (['basisOfRecord','taxonRank','rightsHolder','dataGeneralizations','bioGroup'].includes(Object.keys(map_dict)[j])){
                    tmp_value = gettext(tmp_value)
                }
                tmp_td += `<td class="row-${Object.keys(map_dict)[j]} d-none">${tmp_value}</td>`
            }
        }
        $('.record_table').append(`<tr>${tmp_td}</tr>`)
    }

    // 如果queryString裡面沒有指定orderby，使用scientificName
    $('.orderby').not(`[data-orderby=${response.orderby}]`).append('<i class="fa-solid fa-sort sort-icon"></i>')
    if (response.sort == 'desc') {
        $(`.orderby[data-orderby=${response.orderby}]`).append('<i class="fa-solid fa-sort-down sort-icon-active"></i>')
    } else {
        $(`.orderby[data-orderby=${response.orderby}]`).append('<i class="fa-solid fa-sort-up sort-icon-active"></i>')
        $(`.orderby[data-orderby=${response.orderby}]`).data('sort', 'desc');
    }

    $('.orderby').on('click', function () {
        
        if ($(this).children('svg').hasClass('fa-sort')) {
            $('.orderby:not(this)').children('svg').removeClass('fa-sort-down fa-sort-up sort-icon-active sort-icon').addClass('fa-sort sort-icon');
            $(this).children('svg').removeClass('fa-sort sort-icon-active sort-icon').addClass('fa-sort-down sort-icon-active');
            $(this).data('sort', 'desc');
        } else if ($(this).children('svg').hasClass('fa-sort-down')) { // 如果原本是down (desc)
            $('.orderby:not(this)').children('svg').removeClass('fa-sort-down fa-sort-up sort-icon-active sort-icon').addClass('fa-sort sort-icon');
            $(this).children('svg').removeClass('fa-sort sort-icon-active sort-icon').addClass('fa-sort-up sort-icon-active')
            $(this).data('sort', 'asc');
        } else {  // 如果原本是up (asc)
            $('.orderby:not(this)').children('svg').removeClass('fa-sort-down fa-sort-up sort-icon-active sort-icon').addClass('fa-sort sort-icon');
            $(this).children('svg').removeClass('fa-sort sort-icon-active sort-icon').addClass('fa-sort-down sort-icon-active')
            $(this).data('sort', 'desc');
        }

        submitSearch(1, 'orderby', false, response.limit, $(this).data('orderby'), $(this).data('sort'))
    })

}

// submit search form
function submitSearch(page, from, new_click, limit, orderby, sort, push_state) {

    $('.map-legend').removeClass('d-none');

    if (push_state == null) { push_state = true }

    let map_condition = '';

    if (new_click & ($('.btnupload p.active').data('type') == 'map')) {
        $.ajax({
            url: "/return_geojson_query",
            data: {
                geojson_text: JSON.stringify(drawnItems.toGeoJSON()),
                csrfmiddlewaretoken: $csrf_token
            },
            type: 'POST',
            dataType: 'json',
        })
            .done(function (response) {
                window.g_list = response.polygon
                submitSearch(page, from)
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

        if ($('.btnupload p.active').data('type')) {

            if ($('.btnupload p.active').data('type') == 'circle') {
                if ($('.addC').length > 0) {
                    map_condition = '&' + $.param({ 'geo_type': $('.btnupload p.active').data('type') })
                    map_condition += '&' + $.param({
                        'circle_radius': $('select[name=circle_radius]').val(),
                        'center_lon': $('input[name=center_lon]').val(), 'center_lat': $('input[name=center_lat]').val()
                    })
                } else {
                    $('.btnupload p.active').removeClass('active')
                }

            } else if ($('.btnupload p.active').data('type') == 'map') {
                if (window['g_list']) {
                    if (window['g_list'].length > 0) {
                        map_condition = '&' + $.param({ 'geo_type': $('.btnupload p.active').data('type') })
                        for (let i = 0; i < window['g_list'].length; i++) {
                            map_condition += '&' + $.param({ 'polygon': window['g_list'][i] })
                        }
                    }
                } else {
                    //let queryString = window.location.search;
                    let urlParams = new URLSearchParams(window.location.search);
                    if (urlParams.getAll('polygon')) {
                        if (urlParams.getAll('polygon').length > 0) {
                            map_condition = '&' + $.param({ 'geo_type': $('.btnupload p.active').data('type') })
                            for (let i = 0; i < urlParams.getAll('polygon').length; i++) {
                                map_condition += '&' + $.param({ 'polygon': urlParams.getAll('polygon')[i] })
                            }
                        } else {
                            $('.btnupload p.active').removeClass('active')
                        }
                    } else {
                        $('.btnupload p.active').removeClass('active')
                    }
                }
            } else if ($('.btnupload p.active').data('type') == 'polygon') {
                if ($('.addG').length > 0) {
                    map_condition = '&' + $.param({ 'geo_type': $('.btnupload p.active').data('type') })
                } else {
                    $('.btnupload p.active').removeClass('active')
                }
            }
        }

        let selected_col = ''

        // 如果是按搜尋或從網址進入，重新給query參數，若是從分頁則不用
        if (from == 'search' ) {
            var form = $();
            $('#searchForm input, #searchForm select').each(function () {

                if ($(this).val() != '') {
                    if ($(this).attr('name') == 'geojson_id') {
                        if ($('.btnupload p.active').data('type') == 'polygon'){
                            form = form.add($(this));
                        } 
                    } else {
                        form = form.add($(this));
                    }
                }
            })
            window.condition = form.serialize() + map_condition
        } else if (from == 'page') {
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

            if (push_state) {
                history.pushState(null, '', window.location.pathname + '?' + queryString)
            }

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

                if (response.selected_grid_text!=''){

                    $('.selected_grid_area').removeClass('d-none')
                    $('.selected_grid').html(response.selected_grid_text)

                } else {

                    $('.selected_grid_area').addClass('d-none')
                }

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
                        if (from == 'search' | from == 'change') {
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
    
                        // <span>
                        //     ${gettext('跳至')}<input name="jumpto" type="number" min="1" step="1" class="page-jump">${gettext('頁')}
                        //     <a class="jumpto pointer">GO</a>  
                        // </span>
    
                        // $('.jumpto').on('click', function () {
                        //     if ( isNaN(parseInt($('input[name=jumpto]').val())) ){
                        //         alert(gettext('請輸入有效頁碼'))
                        //     } else {
                        //         submitSearch($('input[name=jumpto]').val(), 'page', false, limit, orderby, sort)
                        //     }
                        // })
    
                        let html = ''
                        for (let i = 0; i < response.page_list.length; i++) {
                            if (response.page_list[i] == response.current_page) {
                                html += `<a class="num now submitSearch" data-page="${response.page_list[i]}" data-from="page">${response.page_list[i]}</a>  `;
                            } else {
                                html += `<a class="num submitSearch" data-page="${response.page_list[i]}" data-from="page">${response.page_list[i]}</a>  `
                            }
                        }
                        $('.pre').after(html)
    
                        // 如果有上一頁，改掉pre的onclick
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
    
                        // // 加上總頁數
                        // if (response.total_page > 1 && !response.page_list.includes(response.total_page)) {
                        //     $('.next').before(`<a class="num ml-5px submitSearch" data-page="${response.total_page}" data-from="page">${response.total_page}</a>`)
                        // }
    
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
