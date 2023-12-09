var $csrf_token = $('[name="csrfmiddlewaretoken"]').attr("value");


function getWKTMap(map) {
  var neLat = map.getBounds().getNorthEast()['lat'] 
  var neLng = map.getBounds().getNorthEast()['lng']
  var swLat = map.getBounds().getSouthWest()['lat']
  var swLng = map.getBounds().getSouthWest()['lng'] 

  return Number(swLat).toFixed(2) + ',' + Number(swLng).toFixed(2) + ' TO ' + Number(neLat).toFixed(2)+ ',' + Number(neLng).toFixed(2)
}


function drawMapGrid(currentZoomLevel, map, taxonID){
  if (currentZoomLevel < 6) {

    $('[class^=resultG_]').addClass('d-none')
    $('.resultG_100').removeClass('d-none')

  } else if (currentZoomLevel < 9) {

    $('[class^=resultG_]').addClass('d-none')
    $('.resultG_10').removeClass('d-none')


  } else if (currentZoomLevel < 11) {

    $('[class^=resultG_]').addClass('d-none')
    $('.resultG_5').remove()
    $.ajax({
      url: "/get_taxon_dist",
      data: 'taxonID=' + taxonID + '&grid=5&map_bound=' + getWKTMap(map) + '&csrfmiddlewaretoken=' + $csrf_token,
      type: 'POST',
      dataType: 'json',
    })
      .done(function (response) {
        L.geoJSON(response, { className: 'resultG_5', style: style }).addTo(map);
      })
      .fail(function (xhr, status, errorThrown) {
        if (xhr.status == 504) {
          alert(gettext('要求連線逾時'))
        } else {
          alert(gettext('發生未知錯誤！請聯絡管理員'))

        }
        console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
      })

    $('.resultG_5').removeClass('d-none')

  } else {

    $('[class^=resultG_]').addClass('d-none')
    $('.resultG_1').remove()

    $.ajax({
      url: "/get_taxon_dist",
      data: 'taxonID=' + taxonID + '&grid=1&map_bound=' + getWKTMap(map) + '&csrfmiddlewaretoken=' + $csrf_token,
      type: 'POST',
      dataType: 'json',
    })
      .done(function (response) {
        L.geoJSON(response, { className: 'resultG_1', style: style }).addTo(map);
      })
      .fail(function (xhr, status, errorThrown) {
        if (xhr.status == 504) {
          alert(gettext('要求連線逾時'))
        } else {
          alert(gettext('發生未知錯誤！請聯絡管理員'))

        }
        console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
      })

    $('.resultG_1').removeClass('d-none')

  }

}
/*
  $('.popbg.taxon-dist').on('hide', function(){
    $("#map-box").html(""); 
    $("#map-box").html('<div id="map" style="height: 500px; margin: 40px 0 10px 10px"></div>');
  })*/

function getColor(d) {
  return d > 1000 ? '#C50101' :
    d > 500 ? '#D71414' :
      d > 200 ? '#E72424' :
        d > 100 ? '#F73535' :
          d > 50 ? '#FB4C4C' :
            d > 20 ? '#FB6262' :
              d > 10 ? '#FC7E7E' :
                '#FD9696';
}

function style(feature) {
  return {
    fillColor: getColor(feature.properties.counts),
    weight: 0,
    fillOpacity: 0.7
  };
}


function getDist(taxonID) {
  // 把之前的清掉
  $("#map-box").html("");
  $("#map-box").html('<div id="map">');

  $('.popbg.taxon-dist').removeClass('d-none')


  let map = L.map('map').setView([23.5, 121.2], 7);
  L.tileLayer('https://{s}.tile.osm.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://osm.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(map);

  map.setView([23.5, 121.2], 7)



  $.ajax({
    url: "/get_taxon_dist_init",
    data: 'taxonID=' + taxonID + '&csrfmiddlewaretoken=' + $csrf_token,
    type: 'POST',
    dataType: 'json',
  })
    .done(function (response) {
      L.geoJSON(response.grid_10, { className: 'resultG_10', style: style }).addTo(map);
      L.geoJSON(response.grid_100, { className: 'resultG_100', style: style }).addTo(map);
      $('.resultG_100').addClass('d-none')

    })
    .fail(function (xhr, status, errorThrown) {
      if (xhr.status == 504) {
        alert(gettext('要求連線逾時'))
      } else {
        alert(gettext('發生未知錯誤！請聯絡管理員'))

      }
      console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
    })

  map.on('zoomend', function zoomendEvent(ev) {

    var currentZoomLevel = ev.target.getZoom()
    drawMapGrid(currentZoomLevel, map, taxonID)

  })

  map.on('dragend', function zoomendEvent(ev) {
    var currentZoomLevel = ev.target.getZoom()
    drawMapGrid(currentZoomLevel, map, taxonID)

  })

}




let params = ['item_class', 'record_type', 'key', 'value', 'scientific_name', 'limit', 'page', 'from',
  'doc_type', 'offset_value', 'more_class', 'card_class', 'is_sub', 'focus_card', 'get_record']

function changeAction() {
  let queryString = window.location.search;
  let urlParams = new URLSearchParams(queryString);

  if (queryString.length > 2000) {

      alert(gettext('您查詢的條件網址超過 2000 個字元，可能無法在所有瀏覽器中正常運作。'))
  
    } else {
    // 如果只有keyword, show全部elements
    if ((queryString.split('&').length == 1) && (queryString.startsWith('?keyword='))) {
      $('.rightbox_content .item').removeClass('d-none')
      $('.rightbox_content .subitem').addClass('d-none')

      // 結果列表移除
      $('.record_title').remove()
      $('.result_inf_top').remove()
      $('.result_table').remove()
      $('.page_number').remove()

    }

    if (urlParams.get('item_class')) {
      focusComponent(urlParams.get('item_class'), true)
    }
    if (urlParams.get('focus_card')) {
      focusCards(urlParams.get('record_type'), urlParams.get('key'), true)
    } else if (urlParams.get('get_record')) {
      //先移除掉原本的
      $('.item_list li').removeClass('now')
      $('.second_menu a').removeClass('now')
      //加上現在的
      $(`.li-item_${urlParams.get('record_type')}`).addClass('now')
      $(`#facet_${urlParams.get('record_type')}_${urlParams.get('key')}`).addClass('now')
      getRecords(urlParams.get('record_type'), urlParams.get('key'), urlParams.get('value'), urlParams.get('scientific_name'),
        urlParams.get('limit'), urlParams.get('page'), urlParams.get('from'), true,
        urlParams.get('orderby'), urlParams.get('sort'))
    }
  }

}

function clickToAnchor(id) {
  let offset;
  if ($(window).width() > 1599) {
    offset = 145
  } else if ($(window).width() > 999) {
    offset = 120
  } else {
    offset = 100
  }
  var target = $(id).offset().top - offset;
  $('html, body').animate({ scrollTop: target }, 500);
}

function addClass(element, className) {
  element.className += ' ' + className;
}

function removeClass(element, className) {
  element.className = element.className.replace(
    new RegExp('( |^)' + className + '( |$)', 'g'), ' ').trim();
}

function plusSlides(n, taxonID, cardclass) {
  slideIndex = parseInt($(`.right_img .mySlides.${taxonID}.d-block[data-cardclass="${cardclass}"]`).data('index'))
  showSlides(slideIndex += n, taxonID, cardclass);
}

function showSlides(n, taxonID, cardclass) {
  let i;
  let slides = document.querySelectorAll(`.right_img .mySlides.${taxonID}[data-cardclass="${cardclass}"]`)
  if (n > slides.length) { slideIndex = 1 }
  if (n < 1) { slideIndex = slides.length }
  for (i = 0; i < slides.length; i++) {
    removeClass(slides[i], 'd-none')
    removeClass(slides[i], 'd-block')
    addClass(slides[i], 'd-none')
  }
  removeClass(slides[slideIndex - 1], 'd-none')
  addClass(slides[slideIndex - 1], 'd-block')

  let slides2 = document.querySelectorAll(`.taxon-pop .mySlides.${taxonID}`)
  if (slides2.length > 0) {
    if (n > slides2.length) { slideIndex = 1 }
    if (n < 1) { slideIndex = slides2.length }
    for (i = 0; i < slides2.length; i++) {
      removeClass(slides2[i], 'd-none')
      removeClass(slides2[i], 'd-block')
      addClass(slides2[i], 'd-none')
    }
    removeClass(slides2[slideIndex - 1], 'd-none')
    addClass(slides2[slideIndex - 1], 'd-block')
  }
}




$(document).ready(function () {

  $('#fullSubmit').on('click', function(){
    $('#fullForm').submit()
  })


  $('#fullForm').on('submit', function(event){
    event.preventDefault()

    if ($('#fullForm input[name=keyword]').val().length > 2000) {
      alert(gettext('您查詢的條件網址超過 2000 個字元，可能無法在所有瀏覽器中正常運作。'))
    } else {
      window.location = `/${$lang}/search/full?keyword=${$('#fullForm input[name=keyword]').val()}`
    }

  })


  $('.imgarea').on('click', function () {
    $('.taxon-pop .taxon-pic').html($(this).parent().parent().parent().html())
    $('.taxon-pop').removeClass('d-none')

    $('.arr-left').off('click')
    $('.arr-left').on('click', function () {
      plusSlides(-1, $(this).data('taxonid'), $(this).data('cardclass'))
    })
    $('.arr-right').off('click')
    $('.arr-right').on('click', function () {
      plusSlides(+1, $(this).data('taxonid'), $(this).data('cardclass'))
    })
  })


  $('.arr-left').on('click', function () {
    plusSlides(-1, $(this).data('taxonid'), $(this).data('cardclass'))
  })

  $('.arr-right').on('click', function () {
    plusSlides(+1, $(this).data('taxonid'), $(this).data('cardclass'))
  })


  $(".popbg .xx,.popbg .ovhy").not('.taxon-dist').click(function (e) {
    if ($(e.target).hasClass("xx") || $(e.target).hasClass("ovhy")) {
      if (window.not_selected != undefined) {
        window.not_selected.prop('checked', false);
      }
      if (window.selected != undefined) {
        window.selected.prop('checked', false);
      }
    }
  });

  $('.getMoreDocs').on('click', function () {
    getMoreDocs($(this).data('doc_type'), $(this).data('offset_value'),
      $(this).data('more_class'), $(this).data('card_class'))
  })

  $('.getRecords').on('click', function () {
    getRecords($(this).data('record_type'), $(this).data('key'), $(this).data('value'), $(this).data('scientific_name'),
      $(this).data('limit'), $(this).data('page'), $(this).data('from'), $(this).data('go_back'), $(this).data('orderby'), $(this).data('sort'))
  })

  $('.getDist').on('click', function () {
    getDist($(this).data('taxonid'))
  })

  $('.getMoreCards').on('click', function () {
    getMoreCards($(this).data('card_class'), $(this).data('offset_value'), $(this).data('more_type'), $(this).data('is_sub'))
  })

  $('.focusCards').on('click', function () {
    focusCards($(this).data('record_type'), $(this).data('key'), $(this).data('go_back'))
  })

  $('.open-page').on('click', function () {
    location.href = $(this).data('href')
  })

  $('.open-news').on('click', function () {
    window.open($(this).data('href'))
  })

  $('.selectAll').on('click', function () {
    selectAll($(this).data('type'))
  })

  $('.resetAll').on('click', function () {
    resetAll($(this).data('type'))
  })

  $('.sendSelected').on('click', function () {
    sendSelected($(this).data('type'))
  })

  $('.occ_menu, .col_menu, .spe_menu').slideToggle();

  // 如果直接從帶有參數網址列進入
  changeAction();

  // 如果按上下一頁
  window.onpopstate = function (event) {
    // console.log(history)
    changeAction();
  };

  $(".mb_fixed_btn").on("click", function (event) {
    $(".mbmove").toggleClass("open");
    $(this).toggleClass("now");
  });

  $(".rd_click").on("click", function (event) {
    $(".rd_click").closest("li").removeClass("now");
    //$(".rd_click").closest("li").find(".second_menu").slideUp();
    $(this).closest("li").toggleClass("now");
    $(this).closest("li").find(".second_menu").slideToggle();
  });

  $(".second_menu a").on("click", function (event) {
    $(this).parent().parent().parent('ul').children('li.now').removeClass("now");
    $(".second_menu a").removeClass("now");
    $(this).addClass("now")
    $(this).parent().parent('li').addClass('now')
  });

  $('.focusComponent').on('click', function () {
    focusComponent($(this).data('item_class'), $(this).data('go_back'))
  })

})



function focusComponent(item_class, go_back) {

  // 先移除掉原本的
  $('.item_list li').removeClass('now')
  $('.second_menu a').removeClass('now')
  // 加上現在的
  $(`.li-${item_class}`).addClass('now')
  if (item_class == 'item_occ') {
    $(`#facet_occ_all`).addClass('now')
  } else if (item_class == 'item_col') {
    $(`#facet_col_all`).addClass('now')
  } else if (item_class == 'item_spe') {
    $(`#facet_spe_all`).addClass('now')
  }

  if ((!go_back) && ('URLSearchParams' in window)) {
    var searchParams = new URLSearchParams(window.location.search)
    searchParams.set("item_class", item_class);

    params.forEach(function (item, index, array) {
      if (item != 'item_class') {
        searchParams.delete(item)
      }
    });

    var newRelativePathQuery = window.location.pathname + '?' + searchParams.toString();
    history.pushState(null, '', newRelativePathQuery);
  }

  // 不顯示最底層結果列表
  $('.record_title').remove()
  $('.result_inf_top').remove()
  $('.result_table').remove()
  $('.page_number').remove()

  if (item_class == 'all') {
    $('.rightbox_content .item').removeClass('d-none')
    // 如果是再底下一個階層則不顯示
    $('.rightbox_content .subitem').addClass('d-none')
  } else {
    $(`.rightbox_content .${item_class}`).removeClass('d-none')
    $('.rightbox_content .item').not($(`.${item_class}`)).not($('.items')).addClass('d-none')
    clickToAnchor(`#${item_class}`)
  }

}

function getRecords(record_type, key, value, scientific_name, limit, page, from, go_back, orderby, sort) {
  $('input[name=keyword]').val($('.keyword-p').html())
  if ((!go_back) && ('URLSearchParams' in window)) {
    var searchParams = new URLSearchParams(window.location.search)

    params.forEach(function (item, index, array) {
      searchParams.delete(item)
    });
    searchParams.set("record_type", record_type);
    searchParams.set("key", key);
    searchParams.set("value", value);
    searchParams.set("scientific_name", scientific_name)
    searchParams.set("limit", limit);
    searchParams.set("page", page);
    searchParams.set("from", from);
    searchParams.set("get_record", true);
    // searchParams.set("orderby", orderby);
    // searchParams.set("sort", sort);
    //queryString = searchParams.toString()
    //var newRelativePathQuery = window.location.pathname + '?' + searchParams.toString();
    //history.pushState(null, '', newRelativePathQuery);
    if (orderby != null) {
      // var urlParams = new URLSearchParams(window.location.search)
      searchParams.set('orderby', orderby)
      searchParams.set('sort', sort)
      if (from == 'orderby') {
        searchParams.set('page', 1)
        page = 1
      }

      //history.pushState(null, '', window.location.pathname + '?'  + queryString);
    }
    queryString = searchParams.toString()
    history.pushState(null, '', window.location.pathname + '?' + queryString);
  }


  // hide all items
  $('.rightbox_content .item').addClass('d-none')

  // 移除前一次的紀錄
  $('.record_title').remove()
  $('.result_inf_top').remove()
  $('.result_table').remove()
  $('.page_number').remove()

  // let $key = key;

  // append rows
  $.ajax({
    url: "/get_records",
    data: {
      record_type: record_type,
      keyword: $('input[name=keyword]').val(),
      csrfmiddlewaretoken: $csrf_token,
      key: key,
      value: value,
      scientific_name: scientific_name,
      limit: limit,
      page: page,
      orderby: orderby,
      sort: sort,
      from: from,
    },
    type: 'POST',
    dataType: 'json',
  })
    .done(function (response) {
      $('.rightbox_content').append(`
        <div class="titlebox_line record_title" id="records">
          <div class="title">
              <p>${gettext(response.title)} > ${gettext('結果列表')}</p>
              <div class="line"></div>
          </div>
        </div>
        <div class="result_inf_top">
          <button class="cate_btn popupField" data-record_type="${record_type}">${gettext('欄位選項')} +</button>
          <div class="d-flex-ai-c">
            <p class="datenum mr-10px">${gettext('資料筆數')}${gettext('：')}${limit.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",")}</p>
            <div class="rightdow">
              <button class="dow_btn downloadData" data-query="${response.search_str}" data-count="${limit}">
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M1 14.5V16.75C1 17.3467 1.23705 17.919 1.65901 18.341C2.08097 18.7629 2.65326 19 3.25 19H16.75C17.3467 19 17.919 18.7629 18.341 18.341C18.7629 17.919 19 17.3467 19 16.75V14.5M14.5 10L10 14.5M10 14.5L5.5 10M10 14.5V1" stroke="#3F5146" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                <p>${gettext('資料下載')}</p>
              </button>
              <a href="/${$lang}/qa?qa_id=14" target="_blank" class="qmark"></a>
            </div>
          </div>

        </div>
        <div class="result_table flow-x-auto">
          <table cellspacing="0" cellspacing="0" class="table_style1 record_table">
          </table>						
        </div>    
        `)
      var table_title = document.createElement("tr");
      table_title.classList.add('table_title');
      let map_dict = response.map_dict;

      // append 功能
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

      // disable checkebox for common_name_c & scientificName
      $('#col-common_name_c, #col-scientificName, #occ-common_name_c, #occ-scientificName').prop('disabled', true);
      $('#col-common_name_c, #col-scientificName, #occ-common_name_c, #occ-scientificName').prop('checked', true);


      // append rows
      for (let i = 0; i < response.rows.length; i++) {
        let tmp = response.rows[i];
        let tmp_td;
        let tmp_value;
        if (record_type == 'occ') {
          let url_mask = "/occurrence/" + tmp.id.toString();
          tmp_td += `<td><a href=${url_mask} class="more" target="_blank">${gettext('查看')}</a></td>`
        } else {
          let url_mask = "/collection/" + tmp.id.toString();
          tmp_td += `<td><a href=${url_mask} class="more" target="_blank">${gettext('查看')}</a></td>`
        }
        for (let j = 0; j < Object.keys(map_dict).length; j++) {
          tmp_value = tmp[Object.keys(map_dict)[j]];
          // 日期
          // 經緯度
          // 數量
          if (tmp_value == null) {
            tmp_td += `<td class="row-${Object.keys(map_dict)[j]} d-none"></td>`
          } else {
            // 'basisOfRecord','rightsHolder' 因為有在關鍵字查詢中 所以不翻譯
              if (['dataGeneralizations','taxonRank','taxonGroup'].includes(Object.keys(map_dict)[j])){
                tmp_value = gettext(tmp_value)
            }
            tmp_td += `<td class="row-${Object.keys(map_dict)[j]} d-none">${tmp_value}</td>`
          }
        }

        $('.record_table').append(
          `<tr>${tmp_td}</tr>`)
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
        getRecords(record_type, key, value, scientific_name, limit, page, 'orderby', go_back, $(this).data('orderby'), $(this).data('sort'))
      })

      // let selected_key = Object.keys(map_dict).find(a => map_dict[a] === key)
      window.selected_key = key
      // 判斷是從分頁或卡片點選
      if ((from == 'card') || ($(`.${record_type}-choice input:checked`).length == 0)) { //如果都沒有選的話用預設值
        // uncheck all first
        $(`input[id^="${record_type}-"]`).prop('checked', false)
        // show selected columns
        for (let i = 0; i < response.selected_col.length; i++) {
          $(`.row-${response.selected_col[i]}`).removeClass('d-none');
          $(`#${record_type}-${response.selected_col[i]}`).prop('checked', true);
        }

        if (key != 'taxonID') {
          $(`.row-${key}`).removeClass('d-none');
        }

        clickToAnchor('#records')

      } else {
        sendSelected(record_type)
      }


      // disable checkebox for key field 預設一定要勾選
      if (key != 'taxonID') {
        $(`#${record_type}-${key}`).prop('disabled', true);
        $(`#${record_type}-${key}`).prop('checked', true);
      }

      // append pagination
      if (response.total_page > 1) {  // 判斷是否有下一頁，有才加分頁按鈕
        $('.result_table').after(
          `<div class="page_number">
              <a class="pre">
                <span></span>
              </a>
              <a class="next">
                <span></span>
              </a>
            </div>`)
      }

      let html = ''
      for (let i = 0; i < response.page_list.length; i++) {
        if (response.page_list[i] == response.current_page) {
          html += `<a class="num now getRecords"
            data-record_type="${record_type}"
            data-key="${key}"
            data-value="${value}"
            data-scientific_name="${scientific_name}"
            data-limit="${limit}"
            data-page="${response.page_list[i]}"
            data-from="page"
            data-go_back="false"
            data-orderby="${response.orderby}"
            data-sort="${response.sort}">
            ${response.page_list[i]}</a>  `;
        } else {
          html += `<a class="num getRecords"
            data-record_type="${record_type}"
            data-key="${key}"
            data-value="${value}"
            data-scientific_name="${scientific_name}"
            data-limit="${limit}"
            data-page="${response.page_list[i]}"
            data-from="page"
            data-go_back="false"
            data-orderby="${response.orderby}"
            data-sort="${response.sort}">
            ${response.page_list[i]}</a>  `
        }
      }
      $('.pre').after(html)

      // 如果有上一頁，改掉pre的onclick
      if ((response.current_page - 1) > 0) {
        $('.pre').addClass('getRecords')
        $('.pre').data('record_type', record_type)
        $('.pre').data('key', key)
        $('.pre').data('value', value)
        $('.pre').data('scientific_name', scientific_name)
        $('.pre').data('limit', limit)
        $('.pre').data('page', response.current_page - 1)
        $('.pre').data('from', 'page')
        $('.pre').data('go_back', false)
        $('.pre').data('orderby', response.orderby)
        $('.pre').data('sort', response.sort)
      }
      // 如果有下一頁，改掉next的onclick
      if (response.current_page < response.total_page) {
        $('.next').addClass('getRecords')
        $('.next').data('record_type', record_type)
        $('.next').data('key', key)
        $('.next').data('value', value)
        $('.next').data('scientific_name', scientific_name)
        $('.next').data('limit', limit)
        $('.next').data('page', response.current_page + 1)
        $('.next').data('from', 'page')
        $('.next').data('go_back', false)
        $('.next').data('orderby', response.orderby)
        $('.next').data('sort', response.sort)
      }

      // 如果有前面的page list, 加上...
      if (response.current_page > 5) {
        $('.pre').after(`<a class="num getRecords bd-0" 
            data-record_type="${record_type}"
            data-key="${key}"
            data-value="${value}"
            data-scientific_name="${scientific_name}"
            data-limit="${limit}"
            data-page="${response.current_page - 5}"
            data-from="page"
            data-go_back="false"
            data-orderby="${response.orderby}"
            data-sort="${response.sort}"
            >...</a> `)
      }
      // 如果有後面的page list, 加上...
      if (response.page_list[response.page_list.length - 1] < response.total_page) {
        if (response.current_page + 5 > response.total_page) {
          $('.next').before(`<a class="num getRecords bd-0" 
            data-record_type="${record_type}"
            data-key="${key}"
            data-value="${value}"
            data-scientific_name="${scientific_name}"
            data-limit="${limit}"
            data-page="${response.total_page}"
            data-from="page"
            data-go_back="false"
            data-orderby="${response.orderby}"
            data-sort="${response.sort}"
            >...</a> `)
        } else {
          $('.next').before(`<a class="num getRecords bd-0" 
            data-record_type="${record_type}"
            data-key="${key}"
            data-value="${value}"
            data-scientific_name="${scientific_name}"
            data-limit="${limit}"
            data-page="${response.current_page + 5}"
            data-from="page"
            data-go_back="false"
            data-orderby="${response.orderby}"
            data-sort="${response.sort}"
            >...</a>`)
        }
      }

      $('.getRecords').off('click')
      $('.getRecords').on('click', function () {
        getRecords($(this).data('record_type'), $(this).data('key'), $(this).data('value'), $(this).data('scientific_name'),
          $(this).data('limit'), $(this).data('page'), $(this).data('from'), $(this).data('go_back'), $(this).data('orderby'), $(this).data('sort'))
      })
      $('.popupField').off('click')
      $('.popupField').on('click', function () {
        popupField($(this).data('record_type'))
      })
      $('.downloadData').off('click')
      $('.downloadData').on('click', function () {
        downloadData($(this).data('query'), $(this).data('count'))
      })

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

function focusCards(record_type, key, go_back) {
  $('input[name=keyword]').val($('.keyword-p').html())

  if ((!go_back) && ('URLSearchParams' in window)) {
    var searchParams = new URLSearchParams(window.location.search)

    params.forEach(function (item, index, array) {
      searchParams.delete(item)
    });

    searchParams.set("record_type", record_type);
    searchParams.set("key", key);
    searchParams.set("focus_card", true);

    var newRelativePathQuery = window.location.pathname + '?' + searchParams.toString();
    history.pushState(null, '', newRelativePathQuery);

  }

  //先移除掉原本的
  $('.item_list li').removeClass('now')
  $('.second_menu a').removeClass('now')
  //加上現在的
  $(`.li-item_${record_type}`).addClass('now')
  $(`#facet_${record_type}_${key}`).addClass('now')

  // 如果focus已存在則不呼叫ajax，但顯示出來
  $('.record_title').remove()
  $('.result_inf_top').remove()
  $('.result_table').remove()
  $('.page_number').remove()

  if (!$(`.item_${record_type}_${key}`).length) {
    // taxon
    if (record_type == 'taxon') {
      $.ajax({
        url: "/get_focus_cards_taxon",
        data: {
          record_type: record_type,
          keyword: $('input[name=keyword]').val(),
          csrfmiddlewaretoken: $csrf_token,
          key: key,
          lang: $lang
        },
        type: 'POST',
        dataType: 'json',
      })
        .done(function (response) {

          // append item area
          $('.rightbox_content').append(
            `<div class="item subitem ${response.item_class}" id="${response.item_class}_cards">
                <div class="titlebox_line">
                  <div class="title">
                    <p>${gettext(response.title)} (${response.total_count})</p>
                    <div class="line"></div>
                  </div>
                </div>
                <ul class="card_list_2 species_list ${response.card_class}">
                </ul>
              </div>`)
          // append cards
          for (let i = 0; i < response.data.length; i++) {
            let x = response.data[i];
            let html;

            let matched = '';
            for (let ii = 0; ii < x.matched.length; ii++) {
              if (!(['中文名', '學名', '中文別名', '同物異名'].includes(x.matched[ii]['matched_col']))) {
                matched += `<p>${gettext(x.matched[ii]['matched_col'])}${gettext('：')}${x.matched[ii]['matched_value']}</p>`
              }
            }

            let image_str = '';

            if (x.images.length > 1) {
              image_str += `
                <div class="arr-left plusSlides" data-index="-1" data-taxonid="${x.taxonID}" data-cardclass="${response.card_class}">
                </div>
                <div class="arr-right plusSlides" data-index="+1" data-taxonid="${x.taxonID}" data-cardclass="${response.card_class}">
                </div>
                `
            }

            for (let ii = 0; ii < x.images.length; ii++) {
              if (ii == 0) {
                image_str += `
                  <div class="picbox mySlides fade ${x.taxonID} d-block" data-index="1" data-cardclass="${response.card_class}">
                  <div class="img-container">
                    <img class="imgarea" src="${x.images[ii].src}">
                    <p class="bottom-right">${x.images[ii].author}</p>
                  </div>
                </div>  
                  `
              } else {
                image_str += `
                  <div class="picbox mySlides fade ${x.taxonID} d-none" data-index="${ii + 1}" data-cardclass="${response.card_class}">
                  <div class="img-container">
                    <img class="imgarea" src="${x.images[ii].src}">
                    <p class="bottom-right">${x.images[ii].author}</p>
                  </div>
                </div>  
                  `
              }
            }

            let right_img_class = ''

            if (x.images.length > 0) {
              right_img_class = 'right_img'
              left_text_class = 'lefttxt'
            } else {
              right_img_class = 'right_img2'
              left_text_class = 'lefttxt2'
            }


            let taieol = '';
            let display = '';

            if (x.taieol_id) {
              taieol = `<a target="_blank" href="https://taieol.tw/pages/${x.taieol_id}">${gettext('生命大百科介紹')}</a>`
            } else {
              display = ' jc-fe'
            }


            html = `	<li>							
              <div class="flex_top">
                <div class="${left_text_class}">
                  <p>${gettext('中⽂名')}${gettext('：')}${x.common_name_c}</p>
                  <p>${gettext('學名')}${gettext('：')}${x.formatted_name}</p>
                  <p>${gettext('中文別名')}${gettext('：')}${x.alternative_name_c}</p>
                  <p>${gettext('同物異名')}${gettext('：')}${x.synonyms}</p>
                  <p>${gettext('分類階層')}${gettext('：')}${gettext(x.taxonRank)}</p>
                  ${matched}
                  <p>${gettext('出現記錄筆數')}${gettext('：')}${x.occ_count}</p>
                  <p>${gettext('自然史典藏筆數')}${gettext('：')}${x.col_count}</p>
                </div>
                <div class="${right_img_class}">
                  <div class="imgbox">
                    ${image_str}
                  </div>
                </div>
              </div>
              <div class="btn_area ${display}">
                ${taieol}
                <button class="getDist" data-taxonid="${x.taxonID}">${gettext('資料分布圖')}</button>
              </div></li>`

            $(`.${response.card_class}`).append(html)

          }

          $('.arr-left').off('click')
          $('.arr-left').on('click', function () {
            plusSlides(-1, $(this).data('taxonid'), $(this).data('cardclass'))
          })
          $('.arr-right').off('click')
          $('.arr-right').on('click', function () {
            plusSlides(+1, $(this).data('taxonid'), $(this).data('cardclass'))
          })

          $('.imgarea').off('click')
          $('.imgarea').on('click', function () {
            $('.taxon-pop .taxon-pic').html($(this).parent().parent().parent().html())
            $('.taxon-pop').removeClass('d-none')

            $('.arr-left').off('click')
            $('.arr-left').on('click', function () {
              plusSlides(-1, $(this).data('taxonid'), $(this).data('cardclass'))
            })
            $('.arr-right').off('click')
            $('.arr-right').on('click', function () {
              plusSlides(+1, $(this).data('taxonid'), $(this).data('cardclass'))
            })
          })

          $('.getDist').off('click')
          $('.getDist').on('click', function () {
            getDist($(this).data('taxonid'))
          })

          $('.getRecords').off('click')
          $('.getRecords').on('click', function () {
            getRecords($(this).data('record_type'), $(this).data('key'), $(this).data('value'), $(this).data('scientific_name'),
              $(this).data('limit'), $(this).data('page'), $(this).data('from'), $(this).data('go_back'), $(this).data('orderby'), $(this).data('sort'))
          })

          // append 更多結果 button if more than 4 cards
          if (response.has_more == true) {
            $(`.${response.card_class}`).after(`
                <a class="more ${record_type}_${key}_more getMoreCards"
                data-card_class=".${response.card_class}"
                data-offset_value="#${record_type}_${key}_offset"
                data-more_type=".${record_type}_${key}_more" 
                data-is_sub="true"> ${gettext('更多結果')} </a>
                <input type="hidden" id="${record_type}_${key}_offset" value="4">
                <div class="no_data ${record_type}_${key}_more_end d-none"> 
                ${gettext('符合關鍵字的搜尋結果過多，本頁面僅列出前30項結果，建議使用進階搜尋功能指定更多或更符合的關鍵字')}
                </div> `)
          }
          $(`.rightbox_content .${response.item_class}`).removeClass('d-none')
          $('.rightbox_content .item').not($(`.${response.item_class}`)).not($('.items')).addClass('d-none')

          clickToAnchor(`#${response.item_class}_cards`)

          $('.getMoreCards').off('click')
          $('.getMoreCards').on('click', function () {
            getMoreCards($(this).data('card_class'), $(this).data('offset_value'), $(this).data('more_type'), $(this).data('is_sub'))
          })

        })
        .fail(function (xhr, status, errorThrown) {
          if (xhr.status == 504) {
            alert(gettext('要求連線逾時'))
          } else {
            alert(gettext('發生未知錯誤！請聯絡管理員'))

          }
          console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
        })

      // occ 或 col
    } else {
      $.ajax({
        url: "/get_focus_cards",
        data: {
          record_type: record_type,
          keyword: $('input[name=keyword]').val(),
          csrfmiddlewaretoken: $csrf_token,
          key: key,
          lang: $lang,
        },
        type: 'POST',
        dataType: 'json',
      })
        .done(function (response) {
          // append item area
          $('.rightbox_content').append(
            `<div class="item subitem ${response.item_class}" id="${response.item_class}_cards">
              <div class="titlebox_line">
                <div class="title">
                  <p>${gettext(response.title)} (${response.total_count})</p>
                  <div class="line"></div>
                </div>
              </div>
              <ul class="card_list_1 ${response.card_class}">
              </ul>
            </div>`)
          // append cards
          for (let i = 0; i < response.data.length; i++) {
            let x = response.data[i];
            let html;

            let matched = '';

            for (let ii = 0; ii < x.matched.length; ii++) {
              if (!(['中文名', '學名', '鑑定層級'].includes(x.matched[ii]['matched_col']))) {
                matched += `<p>${gettext(x.matched[ii]['matched_col'])}${gettext('：')}${x.matched[ii]['matched_value']}</p>`
              }
            }

            let data_key;
            let data_value;

            if ((x.match_type == 'taxon-related') & (x.val != '')) {
              data_key = "taxonID"
              data_value = x.taxonID
            } else {
              data_key = x.matched[0]['key']
              data_value = x.matched[0]['matched_value_ori']
            }

            $(`.${response.card_class}`).append(`
              <li class="getRecords" 
                data-record_type="${record_type}"
                data-key="${data_key}"
                data-value="${data_value}"
                data-scientific_name="${x.name}"
                data-limit="${x.count}"
                data-page="1"
                data-from="card"
                data-go_back="false"
                data-orderby="scientificName"
                data-sort="asc">
                <div class="num">${x.count}</div>
                <div class="num_bottom"></div>
                <p>${gettext('中文名')}${gettext('：')}${x.common_name_c}</p>
                <p>${gettext('學名')}${gettext('：')}${x.val}</p>
                <p>${gettext('鑑定層級')}${gettext('：')}${gettext(x.taxonRank)}</p>
                ${matched}
              </li>`)
          }

          $('.getRecords').off('click')
          $('.getRecords').on('click', function () {
            getRecords($(this).data('record_type'), $(this).data('key'), $(this).data('value'), $(this).data('scientific_name'),
              $(this).data('limit'), $(this).data('page'), $(this).data('from'), $(this).data('go_back'), $(this).data('orderby'), $(this).data('sort'))
          })

          // append 更多結果 button if more than 9 cards
          if (response.has_more == true) {
            $(`.${response.card_class}`).after(`
              <a class="more ${record_type}_${key}_more getMoreCards"
              data-card_class=".${response.card_class}" 
              data-offset_value="#${record_type}_${key}_offset"
              data-more_type=".${record_type}_${key}_more" 
              data-is_sub="true"> ${gettext('更多結果')} </a>
              <input type="hidden" id="${record_type}_${key}_offset" value="9">
              <div class="no_data ${record_type}_${key}_more_end d-none"> 
              ${gettext('符合關鍵字的搜尋結果過多，本頁面僅列出前30項結果，建議使用進階搜尋功能指定更多或更符合的關鍵字')}
              </div>      
              `)
          }
          $(`.rightbox_content .${response.item_class}`).removeClass('d-none')
          $('.rightbox_content .item').not($(`.${response.item_class}`)).not($('.items')).addClass('d-none')

          $('.getMoreCards').off('click')
          $('.getMoreCards').on('click', function () {
            getMoreCards($(this).data('card_class'), $(this).data('offset_value'), $(this).data('more_type'), $(this).data('is_sub'))
          })

          clickToAnchor(`#${response.item_class}_cards`)
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

  } else {
    $(`.rightbox_content .item_${record_type}_${key}`).removeClass('d-none')
    $('.rightbox_content .item').not($(`.item_${record_type}_${key}`)).not($('.items')).addClass('d-none')
    clickToAnchor(`#item_${record_type}_${key}_cards`)
  }

}

function getMoreDocs(doc_type, offset_value, more_class, card_class) {
  $('input[name=keyword]').val($('.keyword-p').html())

  let offset = $(offset_value).val()
  $.ajax({
    url: "/get_more_docs",
    data: {
      doc_type: doc_type,
      keyword: $('input[name=keyword]').val(),
      csrfmiddlewaretoken: $csrf_token,
      offset: offset,
    },
    type: 'POST',
    dataType: 'json',
  })
    .done(function (response) {
      (response.has_more == true) ? $(offset_value).val(Number(offset) + 6) : $(more_class).addClass('d-none')

      if (card_class == '.resource-card') {
        for (let i = 0; i < response.rows.length; i++) {
          let x = response.rows[i]

          if (x.extension == 'pop') {
            $('.edu_list').append(`
          <li class="show_tech">
            <div class="item items h-100p">
              <div class="cate_dbox">
                <div class="date">${x.date}</div>
              </div>
              <a class="title ">${x.title}</a>
            </div>
          </li>`)
          } else if (x.cate == 'link'){
            $('.edu_list').append(`
          <li>
            <div class="item">
            <div class="cate_dbox">
              <div class="cate ${x.cate}">${x.extension}</div>
              <div class="date">${x.date}</div>
            </div>
            <a href="${x.url}" class="title" target="_blank">${gettext(x.title)}</a>
            </div>
          </li>`)
          } else {
            $(card_class).append(`<li>
            <div class="item items h-100p">
              <div class="cate_dbox">
                <div class="cate pdf">${x.extension}</div>
                <div class="date">${x.date}</div>
              </div>
              <a href="/media/${x.url}" class="title" target="_blank"> ${x.title} </a>
              <a href="/media/${x.url}" download class="dow_btn"> </a>
            </div></li>`)
          }

          $('.show_tech').off('click')
          $('.show_tech').on('click', function () {
            // 每次打開都放第一張
            $('.index_tech .text_tec').html($tutorial[1])
            $('.index_tech .arl').data('index', 10)
            $('.index_tech .arr').data('index', 2)
            $('.tech_pic img').attr('src', "/static/image/tutorial/pic1.png?v1")
            $('.tech-pop').removeClass('d-none')
          })

        }
      } else {
        for (let i = 0; i < response.rows.length; i++) {
          let x = response.rows[i]
          $(card_class).append(`
          <li class="open-news" data-href="/${$lang}/news/detail/${x.id}">
            <div class="nstitle">${x.title}</div>
            <p>${x.content}</p>
          </li>`)
        }

        $('.open-news').off('click')
        $('.open-news').on('click', function () {
          window.open($(this).data('href'))
        })

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

}

function getMoreCards(card_class, offset_value, more_type, is_sub) {
  $('input[name=keyword]').val($('.keyword-p').html())

  let record_type;
  if (card_class.startsWith('.col')) {
    record_type = 'col'
  } else if (card_class.startsWith('.occ')) {
    record_type = 'occ'
  } else {
    record_type = 'taxon'
  }

  let offset = $(offset_value).val()
  if (record_type == 'taxon') {
    $.ajax({
      url: "/get_more_cards_taxon",
      data: {
        card_class: card_class,
        keyword: $('input[name=keyword]').val(),
        csrfmiddlewaretoken: $csrf_token,
        offset: offset,
        is_sub: is_sub,
        lang: $lang,
      },
      type: 'POST',
      dataType: 'json',
    })
      .done(function (response) {


        if (response.has_more == true & response.reach_end == false) {

          $(offset_value).val(Number(offset) + 4)

        } else if (response.has_more == true) {

          $(more_type).addClass('d-none')
          if (response.reach_end) {
            $(`${more_type}_end`).removeClass('d-none')
          }

        } else {

          $(more_type).addClass('d-none')

        }

        for (let i = 0; i < response.data.length; i++) {
          let x = response.data[i]
          let html;

          let matched = '';
          for (let ii = 0; ii < x.matched.length; ii++) {
            if (!(['中文名', '學名', '中文別名', '同物異名'].includes(x.matched[ii]['matched_col']))) {
              matched += `<p>${gettext(x.matched[ii]['matched_col'])}${gettext('：')}${x.matched[ii]['matched_value']}</p>`
            }
          }

          let image_str = '';

          if (x.images.length > 1) {
            image_str += `
          <div class="arr-left plusSlides" data-index="-1" data-taxonid="${x.taxonID}" data-cardclass="${card_class.substring(1)}">
          </div>
          <div class="arr-right plusSlides" data-index="+1" data-taxonid="${x.taxonID}" data-cardclass="${card_class.substring(1)}">
          </div>
          `
          }

          for (let ii = 0; ii < x.images.length; ii++) {
            if (ii == 0) {
              image_str += `
            <div class="picbox mySlides fade ${x.taxonID} d-block " data-index="1" data-cardclass="${card_class.substring(1)}">
            <div class="img-container">
              <img class="imgarea" src="${x.images[ii].src}">
              <p class="bottom-right">${x.images[ii].author}</p>
            </div>
          </div>  
            `
            } else {
              image_str += `
            <div class="picbox mySlides fade ${x.taxonID} d-none " data-index="${ii + 1}" data-cardclass="${card_class.substring(1)}">
            <div class="img-container">
              <img class="imgarea" src="${x.images[ii].src}">
              <p class="bottom-right">${x.images[ii].author}</p>
            </div>
          </div>  
            `
            }
          }

          let right_img_class = ''

          if (x.images.length > 0) {
            right_img_class = 'right_img'
            left_text_class = 'lefttxt'
          } else {
            right_img_class = 'right_img2'
            left_text_class = 'lefttxt2'
          }


          let taieol = '';
          let display = '';

          if (x.taieol_id) {
            taieol = `<a target="_blank" href="https://taieol.tw/pages/${x.taieol_id}">${gettext('生命大百科介紹')}</a>`
          } else {
            display = ' jc-fe'
          }

          html = `<li>							
          <div class="flex_top">
          <div class="${left_text_class}">
            <p>${gettext('中⽂名')}${gettext('：')}${x.common_name_c}</p>
            <p>${gettext('學名')}${gettext('：')}${x.formatted_name}</p>
            <p>${gettext('中文別名')}${gettext('：')}${x.alternative_name_c}</p>
            <p>${gettext('同物異名')}${gettext('：')}${x.synonyms}</p>
            <p>${gettext('分類階層')}${gettext('：')}${gettext(x.taxonRank)}</p>
            ${matched}
            <p>${gettext('出現記錄筆數')}${gettext('：')}${x.occ_count}</p>
            <p>${gettext('自然史典藏筆數')}${gettext('：')}${x.col_count}</p>
          </div>
          <div class="${right_img_class}">
            <div class="imgbox">
              ${image_str}
            </div>
          </div>
          </div>
          <div class="btn_area ${display}">
            ${taieol}
            <button class="getDist" data-taxonid="${x.taxonID}">${gettext('資料分布圖')}</button>
          </div></li>`

          $(`${card_class}`).append(html)

          $('.arr-left').off('click')
          $('.arr-left').on('click', function () {
            plusSlides(-1, $(this).data('taxonid'), $(this).data('cardclass'))
          })
          $('.arr-right').off('click')
          $('.arr-right').on('click', function () {
            plusSlides(+1, $(this).data('taxonid'), $(this).data('cardclass'))
          })


          $('.imgarea').off('click')
          $('.imgarea').on('click', function () {
            $('.taxon-pop .taxon-pic').html($(this).parent().parent().parent().html())
            $('.taxon-pop').removeClass('d-none')

            $('.arr-left').off('click')
            $('.arr-left').on('click', function () {
              plusSlides(-1, $(this).data('taxonid'), $(this).data('cardclass'))
            })
            $('.arr-right').off('click')
            $('.arr-right').on('click', function () {
              plusSlides(+1, $(this).data('taxonid'), $(this).data('cardclass'))
            })
          })

          $('.getDist').off('click')
          $('.getDist').on('click', function () {
            getDist($(this).data('taxonid'))
          })
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

  } else {
    $.ajax({
      url: "/get_more_cards",
      data: {
        card_class: card_class,
        keyword: $('input[name=keyword]').val(),
        csrfmiddlewaretoken: $csrf_token,
        offset: offset,
        is_sub: is_sub,
        lang: $lang,
      },
      type: 'POST',
      dataType: 'json',
    })
      .done(function (response) {

        if (response.has_more == true & response.reach_end == false) {
          $(offset_value).val(Number(offset) + 9)
        } else if (response.has_more == true) {
          $(more_type).addClass('d-none')
          if (response.reach_end) {
            $(`${more_type}_end`).removeClass('d-none')
          }
        } else {
          $(more_type).addClass('d-none')
        }

        for (let i = 0; i < response.data.length; i++) {
          let x = response.data[i]

          let matched = '';

          for (let ii = 0; ii < x.matched.length; ii++) {
            if (!(['中文名', '學名', '鑑定層級'].includes(x.matched[ii]['matched_col']))) {
              matched += `<p>${gettext(x.matched[ii]['matched_col'])}${gettext('：')}${x.matched[ii]['matched_value']}</p>`
            }
          }

          let data_key;
          let data_value;

          if ((x.match_type == 'taxon-related') & (x.val != '')) {
            data_key = "taxonID"
            data_value = x.taxonID
          } else {
            data_key = x.matched[0]['key']
            data_value = x.matched[0]['matched_value_ori']
          }

          $(card_class).append(`
        <li class="getRecords" 
            data-record_type="${record_type}"
            data-key="${data_key}"
            data-value="${data_value}"
            data-scientific_name="${x.name}"
            data-limit="${x.count}"
            data-page="1"
            data-from="card"
            data-go_back="false"
            data-orderby="scientificName"
            data-sort="asc">
          <div class="num">${x.count}</div>
          <div class="num_bottom"></div>
          <p>${gettext('中文名')}${gettext('：')}${x.common_name_c}</p>
          <p>${gettext('學名')}${gettext('：')}${x.val}</p>
          <p>${gettext('鑑定層級')}${gettext('：')}${gettext(x.taxonRank)}</p>
          ${matched}
        </li>` )
        }

        $('.getRecords').off('click')
        $('.getRecords').on('click', function () {
          getRecords($(this).data('record_type'), $(this).data('key'), $(this).data('value'), $(this).data('scientific_name'),
            $(this).data('limit'), $(this).data('page'), $(this).data('from'), $(this).data('go_back'), $(this).data('orderby'), $(this).data('sort'))
        })

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
}


function resetAll(record_type) {
  $(`${record_type} input:checkbox:not(:disabled)`).prop('checked', false);
}

function selectAll(record_type) {
  $(`${record_type} input:checkbox`).prop('checked', true);
}

function popupField(record_type) {
  $(`.${record_type}-choice`).removeClass('d-none')
  window.not_selected = $(`.${record_type}-choice input:not(:checked)`)
  window.selected = $(`.${record_type}-choice input:checked`)
}

function sendSelected(record_type) {
  let selected_field = $(`.${record_type}-choice input:checked`)
  // 所有都先隱藏，除了對到的欄位
  $('td[class^="row-"]').addClass('d-none');
  if (window.selected_key != 'taxonID') {
    $(`.row-${window.selected_key}`).removeClass('d-none');
  }
  // 再顯示選擇的欄位
  for (let i = 0; i < selected_field.length; i++) {
    $(`td.row-${selected_field[i].id.split('-')[1]}`).removeClass('d-none');
  }
  $(".popbg").addClass('d-none');
}

function downloadData(search_str, total_count) {
  if ($('input[name=is_authenticated]').val() == 'True') {
    $.ajax({
      url: "/send_download_request",
      data: {
        search_str: search_str,
        // total_count: total_count,
        csrfmiddlewaretoken: $csrf_token,
        from_full: 'yes',
      },
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
}

