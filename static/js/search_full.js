var $csrf_token = $('[name="csrfmiddlewaretoken"]').attr("value");

/*
  $('.popbg.taxon-dist').on('hide', function(){
    $("#map-box").html(""); 
    $("#map-box").html('<div id="map" style="height: 500px; margin: 40px 0 10px 10px"></div>');
  })*/

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

  function getDist(taxonID, common_name_c, formatted_name){
    $("#map-box").html(""); 
    $("#map-box").html('<div id="map">');

    $('.popbg.taxon-dist').removeClass('d-none')

    $('#taxon_name').html(`${formatted_name} ${common_name_c}`)

    $.ajax({
      url: "/get_taxon_dist?taxonID=" + taxonID,
      type: 'GET',
    })
    .done(function(response) {
        // 把之前的清掉
        let map = L.map('map').setView([23.5, 121.2],7);
        L.tileLayer('https://{s}.tile.osm.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://osm.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map);

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
    

        L.geoJSON(response.grid_1,{className: 'resultG_1',style: style}).addTo(map);
        L.geoJSON(response.grid_5,{className: 'resultG_5',style: style}).addTo(map);
        L.geoJSON(response.grid_10,{className: 'resultG_10',style: style}).addTo(map);
        L.geoJSON(response.grid_100,{className: 'resultG_100',style: style}).addTo(map);

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

        map.setView([23.5, 121.2],7)

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


  

  let params = ['item_class', 'record_type','key','value','scientific_name','limit','page','from',
                'doc_type', 'offset_value', 'more_class', 'card_class', 'is_sub', 'focus_card', 'get_record']

  function changeAction(){
    let queryString = window.location.search;
    let urlParams = new URLSearchParams(queryString);
    // 如果只有keyword, show全部elements
    if ((queryString.split('&').length==1)&&(queryString.startsWith('?keyword='))){
      $('.rightbox_content .item').removeClass('d-none')
      $('.rightbox_content .subitem').addClass('d-none')
    }
    if (urlParams.get('item_class')){
      focusComponent(urlParams.get('item_class'), true)
    } else if (urlParams.get('focus_card')){
      focusCards(urlParams.get('record_type'), urlParams.get('key'), true)
    } else if (urlParams.get('get_record')){
      getRecords(urlParams.get('record_type'),urlParams.get('key'),urlParams.get('value'),urlParams.get('scientific_name'),urlParams.get('limit'),urlParams.get('page'),urlParams.get('from'),true)
    } 
  }

  function clickToAnchor(id){
      let offset;
      if ($(window).width() > 1599){
        offset = 145
      } else if ($(window).width() > 999){
        offset = 120
      } else {
        offset = 100
      }
      var target = $(id).offset().top - offset;
      $('html, body').animate({scrollTop:target}, 500);
  }

  $( document ).ready(function() {

    $('.getMoreDocs').on('click', function(){
        getMoreDocs($(this).data('doc_type'),$(this).data('offset_value'),
                    $(this).data('more_class'),$(this).data('card_class'))
    })

    $('.getRecords').on('click', function(){
        getRecords($(this).data('record_type'),$(this).data('key'),$(this).data('value'),$(this).data('scientific_name'),
        $(this).data('limit'),$(this).data('page'),$(this).data('from'),$(this).data('go_back'))
    })

    $('.getDist').on('click', function(){
        getDist($(this).data('taxonID'), $(this).data('common_name_c'), $(this).data('formatted_name'))
    })

    $('.getMoreCards').on('click', function(){
        getMoreCards($(this).data('card_class'),$(this).data('offset_value'),$(this).data('more_type'),$(this).data('is_sub'))
    })

    $('.focusCards').on('click', function(){
        focusCards($(this).data('record_type'),$(this).data('key'),$(this).data('go_back'))
    })

    $('.open-page').on('click', function(){
        location.href = $(this).data('href')
    })

    $('.selectAll').on('click', function(){
        selectAll($(this).data('type'))
    })

    $('.resetAll').on('click', function(){
        resetAll($(this).data('type'))
    })

    $('.sendSelected').on('click', function(){
        sendSelected($(this).data('type'))
    })

    $('.occ_menu, .col_menu, .spe_menu').slideToggle();

    // 如果直接從帶有參數網址列進入
    changeAction(); 

    // 如果按上下一頁
    window.onpopstate = function(event) {
      changeAction();
    };
  })
  

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

  function focusComponent(item_class, go_back){

    // 先移除掉原本的
    $('.item_list li').removeClass('now')
    $('.second_menu a').removeClass('now')
    // 加上現在的
    $(`.li-${item_class}`).addClass('now')
    if (item_class=='item_occ'){
      $(`#facet_occ_all`).addClass('now')
    } else if  (item_class=='item_col'){
      $(`#facet_col_all`).addClass('now')
    } else if (item_class=='item_spe'){
      $(`#facet_spe_all`).addClass('now')
    }

    if ((!go_back)&& ('URLSearchParams' in window)) {
      var searchParams = new URLSearchParams(window.location.search)
      searchParams.set("item_class", item_class);

      params.forEach(function(item, index, array) {
        if (item != 'item_class'){
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

    if (item_class == 'all'){
      $('.rightbox_content .item').removeClass('d-none')
      // 如果是再底下一個階層則不顯示
      $('.rightbox_content .subitem').addClass('d-none')
    } else {
      $(`.rightbox_content .${item_class}`).removeClass('d-none')
      $('.rightbox_content .item').not($(`.${item_class}`)).not($('.items')).addClass('d-none')
      clickToAnchor(`#${item_class}`)
    }

  }

  function getRecords(record_type,key,value,scientific_name,limit,page,from,go_back){

    if ((!go_back)&& ('URLSearchParams' in window)) {
      var searchParams = new URLSearchParams(window.location.search)

      params.forEach(function(item, index, array) {
          searchParams.delete(item)
      });
      searchParams.set("record_type", record_type);
      searchParams.set("key", key);
      searchParams.set("value", value);
      searchParams.set("scientific_name", scientific_name);
      searchParams.set("limit", limit);
      searchParams.set("page", page);
      searchParams.set("from", from);
      searchParams.set("get_record", true);
      
      var newRelativePathQuery = window.location.pathname + '?' + searchParams.toString();
      history.pushState(null, '', newRelativePathQuery);
    }

    // hide all items
    $('.rightbox_content .item').addClass('d-none')

    // 移除前一次的紀錄
    $('.record_title').remove()
    $('.result_inf_top').remove()
    $('.result_table').remove()
    $('.page_number').remove()

    // append rows
    $.ajax({
        url: "/get_records",
        data: { record_type: record_type,
                keyword: $('input[name=keyword]').val(),
                csrfmiddlewaretoken: $csrf_token,
                key: key,
                value: value,
                scientific_name: scientific_name,
                limit: limit,
                page: page},
        type: 'POST',
        dataType : 'json',
      })
      .done(function(response) {
        $('.rightbox_content').append(`
        <div class="titlebox_line record_title" id="records">
          <div class="title">
              <p>${response.title} > 結果列表</p>
              <div class="line"></div>
          </div>
        </div>
        <div class="result_inf_top">
          <button class="cate_btn popupField" data-record_type="${record_type}">欄位選項 +</button>
          <div class="d-flex">
            <p class="datenum mr-10px">資料筆數：${limit.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",")}</p>
            <div class="rightdow">
              <button class="dow_btn downloadData" data-query="${response.search_str}" data-count="${limit}">
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M1 14.5V16.75C1 17.3467 1.23705 17.919 1.65901 18.341C2.08097 18.7629 2.65326 19 3.25 19H16.75C17.3467 19 17.919 18.7629 18.341 18.341C18.7629 17.919 19 17.3467 19 16.75V14.5M14.5 10L10 14.5M10 14.5L5.5 10M10 14.5V1" stroke="#3F5146" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                <p>資料下載</p>
              </button>
              <a href="#" class="qmark"></a>
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

        for (let i = 0; i < Object.keys(map_dict).length; i++) {
            var this_td = document.createElement("td");
            this_td.className = `row-${Object.keys(map_dict)[i]} d-none`;
            //this_td.style.cssText = 'display:none';
            var text = document.createTextNode(map_dict[Object.keys(map_dict)[i]]);
            this_td.appendChild(text);
            table_title.appendChild(this_td); 
        }

        // append 功能
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
            // 日期
            // 經緯度
            // 數量
            if (tmp_value == null){
              tmp_td += `<td class="row-${Object.keys(map_dict)[j]} d-none"></td>`
            } else {
              tmp_td += `<td class="row-${Object.keys(map_dict)[j]} d-none">${tmp_value}</td>`
            }
          }
          if (record_type == 'occ'){
            let url_mask = "/occurrence/" + tmp.id.toString();
            tmp_td += `<td><a href=${url_mask} class="more" target="_blank">查看</a></td>`
          }else{
            let url_mask = "/collection/" + tmp.id.toString();
            tmp_td += `<td><a href=${url_mask} class="more" target="_blank">查看</a></td>`
          }
          $('.record_table').append(
            `<tr>${tmp_td}</tr>`)
        }
        
        // 判斷是從分頁或卡片點選
        if ((from == 'card') || ( $(`.${record_type}-choice input:checked`).length==0 )){ //如果都沒有選的話用預設值
          // uncheck all first
          $(`input[id^="${record_type}-"]`).prop('checked',false)
          // show selected columns
          for (let i = 0; i < response.selected_col.length; i++) {
            $(`.row-${response.selected_col[i]}`).removeClass('d-none');
            $(`#${record_type}-${response.selected_col[i]}`).prop('checked',true);}
            clickToAnchor('#records')
        } else {
          sendSelected(record_type)
        }

        // disable checkebox for key field
        let selected_key = Object.keys(map_dict).find(a => map_dict[a] === key)
        window.selected_key = selected_key
        $(`#${record_type}-${selected_key}`).prop('disabled',true);
        $(`#${record_type}-${selected_key}`).prop('checked',true);

        // append pagination
        if (response.total_page > 1){  // 判斷是否有下一頁，有才加分頁按鈕
          $('.result_table').after(
            `<div class="page_number">
              <a href="javascript:;" class="pre">
                <span></span>
              </a>
              <a href="javascript:;" class="next">
                <span></span>
              </a>
            </div>`)}		
        
        let html = ''
        for (let i = 0; i < response.page_list.length; i++) {
          if (response.page_list[i] == response.current_page){
            html += `<a href="javascript:;" class="num now getRecords"
            data-record_type="${record_type}"
            data-key="${key}"
            data-value="${value}"
            data-scientific_name="${scientific_name}"
            data-limit="${limit}"
            data-page="${response.page_list[i]}"
            data-from="page"
            data-go_back="false">
            ${response.page_list[i]}</a>  `;
          } else {
            html += `<a href="javascript:;" class="num getRecords"
            data-record_type="${record_type}"
            data-key="${key}"
            data-value="${value}"
            data-scientific_name="${scientific_name}"
            data-limit="${limit}"
            data-page="${response.page_list[i]}"
            data-from="page"
            data-go_back="false">
            ${response.page_list[i]}</a>  `
          }
        }
        $('.pre').after(html)

        // 如果有上一頁，改掉pre的onclick
        if ((response.current_page - 1) > 0 ){
            $('.pre').addClass('getRecords')
            $('.pre').data('record_type',record_type)
            $('.pre').data('key',key)
            $('.pre').data('value',value)
            $('.pre').data('scientific_name',scientific_name)
            $('.pre').data('limit',limit)
            $('.pre').data('page',response.current_page-1)
            $('.pre').data('from','page')
            $('.pre').data('go_back',false)
        }
        // 如果有下一頁，改掉next的onclick
        if (response.current_page < response.total_page){
            $('.next').addClass('getRecords')
            $('.next').data('record_type',record_type)
            $('.next').data('key',key)
            $('.next').data('value',value)
            $('.next').data('scientific_name',scientific_name)
            $('.next').data('limit',limit)
            $('.next').data('page',response.current_page+1)
            $('.next').data('from','page')
            $('.next').data('go_back',false)
        }

        // 如果有前面的page list, 加上...
        if (response.current_page > 5){
          $('.pre').after(`<a href="javascript:;" class="num getRecords bd-0" 
            data-record_type="${record_type}"
            data-key="${key}"
            data-value="${value}"
            data-scientific_name="${scientific_name}"
            data-limit="${limit}"
            data-page="${response.current_page-5}"
            data-from="page"
            data-go_back="false">...</a> `)
        }
        // 如果有後面的page list, 加上...
        if (response.page_list[response.page_list.length - 1] < response.total_page){
          if (response.current_page +5 > response.total_page){
            $('.next').before(`<a href="javascript:;" class="num getRecords bd-0" 
            data-record_type="${record_type}"
            data-key="${key}"
            data-value="${value}"
            data-scientific_name="${scientific_name}"
            data-limit="${limit}"
            data-page="${response.total_page}"
            data-from="page"
            data-go_back="false">...</a> `)
          } else {
            $('.next').before(`<a href="javascript:;" class="num getRecords bd-0" 
            data-record_type="${record_type}"
            data-key="${key}"
            data-value="${value}"
            data-scientific_name="${scientific_name}"
            data-limit="${limit}"
            data-page="${response.current_page+5}"
            data-from="page"
            data-go_back="false">...</a>`)
          }
        }

        $('.getRecords').on('click', function(){
            getRecords($(this).data('record_type'),$(this).data('key'),$(this).data('value'),$(this).data('scientific_name'),
            $(this).data('limit'),$(this).data('page'),$(this).data('from'),$(this).data('go_back'))
        })

        $('.popupField').on('click', function(){
            popupField($(this).data('record_type'))
        })

        $('.downloadData').on('click', function(){
            downloadData($(this).data('query'),$(this).data('count'))
        })
    
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

  function focusCards(record_type,key,go_back){
    if ((!go_back)&& ('URLSearchParams' in window)) {
      var searchParams = new URLSearchParams(window.location.search)

      params.forEach(function(item, index, array) {
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

    if (! $(`.item_${record_type}_${key}`).length){
      // taxon
      if (record_type == 'taxon') {
          $.ajax({
            url: "/get_focus_cards_taxon",
            data: { record_type: record_type,
                    keyword: $('input[name=keyword]').val(),
                    csrfmiddlewaretoken: $csrf_token,
                    key: key },
            type: 'POST',
            dataType : 'json',
        })
        .done(function(response) {
          // append item area
          $('.rightbox_content').append(
            `<div class="item subitem ${response.item_class}" id="${response.item_class}_cards">
              <div class="titlebox_line">
                <div class="title">
                  <p>${response.title} (${response.total_count})</p>
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

            if (!(['中文名','學名','中文別名','同物異名'].includes(x.matched_col))) {
              matched = `<p>${x.matched_col}：${ x.matched_value }</p>`
            }

            let image = '<img class="imgarea">'

            if (x.images){
              image = `<img class="imgarea" src="${ x.images.src }">`
            }

            let taieol = '';
            let display = '';

            if (x.taieol_id){
                taieol = `<a target="_blank" href="https://taieol.tw/pages/${x.taieol_id}">生命大百科介紹</a>`
            } else {
                display = ' jc-fe'
            }


            html = `	<li>							
            <div class="flex_top">
              <div class="lefttxt">
                ${matched}
                <p>中⽂名：${x.common_name_c}</p>
                <p>學名：${x.formatted_name}</p>
                <p>中文別名：${ x.alternative_name_c }</p>
                <p>同物異名：${ x.formatted_synonyms }</p>
                <p>出現記錄筆數：${ x.occ_count }</p>
                <p>自然史典藏筆數：${ x.col_count }</p>
              </div>
              <div class="right_img">
                <div class="imgbox">
                  ${image}
                </div>
              </div>
            </div>
            <div class="btn_area ${display}">
              ${taieol}
              <button class="getDist" data-taxonID="${x.taxonID}">分布圖</button>
            </div></li>`

              $(`.${response.card_class}`).append(html)

              $('.getDist').on('click', function(){
                getDist($(this).data('taxonID'), $(this).data('common_name_c'), $(this).data('formatted_name'))
            })
        
          }
          // append 更多結果 button if more than 4 cards
          if (response.has_more == true) {
            $(`.${response.card_class}`).after(`
              <a href="javascript:;" class="more ${record_type}_${key}_more getMoreCards"
              data-card_class=".${response.card_class}"
              data-offset_value="#${record_type}_${key}_offset"
              data-more_type=".${record_type}_${key}_more" 
              data-is_sub="true"> 更多結果 </a>
              <input type="hidden" id="${record_type}_${key}_offset" value="4">`)
          }
          $(`.rightbox_content .${response.item_class}`).removeClass('d-none')
          $('.rightbox_content .item').not($(`.${response.item_class}`)).not($('.items')).addClass('d-none')

          clickToAnchor(`#${response.item_class}_cards`)
        })
        .fail(function( xhr, status, errorThrown ) {
          if (xhr.status==504){
            alert('要求連線逾時')
          } else {
            alert('發生未知錯誤！請聯絡管理員')
          }
          console.log( 'Error: ' + errorThrown + 'Status: ' + xhr.status)
        })

      // occ 或 col
      } else {
        $.ajax({
            url: "/get_focus_cards",
            data: { record_type: record_type,
                    keyword: $('input[name=keyword]').val(),
                    csrfmiddlewaretoken: $csrf_token,
                    key: key },
            type: 'POST',
            dataType : 'json',
        })
        .done(function(response) {
          // append item area
          $('.rightbox_content').append(
            `<div class="item subitem ${response.item_class}" id="${response.item_class}_cards">
              <div class="titlebox_line">
                <div class="title">
                  <p>${response.title} (${response.total_count})</p>
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
            if ( x.matched_col != '中文名' && x.matched_col != '學名'){
              $(`.${response.card_class}`).append( `
              <li class="getRecords" 
                data-record_type="${record_type}"
                data-key="${x.matched_col}"
                data-value="${x.matched_value_ori}"
                data-scientific_name="${x.name}"
                data-limit="${x.count}"
                data-page="1"
                data-from="card"
                data-go_back="false">
                <div class="num">${x.count}</div>
                <div class="num_bottom"></div>
                <p>中文名：${x.common_name_c}</p>
                <p>學名：${x.val}</p>
                <p>${ x.matched_col }：${x.matched_value}</p>
              </li>`)
            } else {
              $(`.${response.card_class}`).append( `
              <li class="getRecords" 
                    data-record_type="${record_type}"
                    data-key="${x.matched_col}"
                    data-value="${x.matched_value_ori}"
                    data-scientific_name="${x.name}"
                    data-limit="${x.count}"
                    data-page="1"
                    data-from="card"
                    data-go_back="false">
                <div class="num">${x.count}</div>
                <div class="num_bottom"></div>
                <p>中文名：${x.common_name_c}</p>
                <p>學名：${x.val}</p>
              </li>`)
            }
          }
          // append 更多結果 button if more than 9 cards
          if (response.has_more == true) {
            $(`.${response.card_class}`).after(`
              <a href="javascript:;" class="more ${record_type}_${key}_more getMoreCards"
              data-card_class=".${response.card_class}" 
              data-offset_value="#${record_type}_${key}_offset"
              data-more_type=".${record_type}_${key}_more" 
              data-is_sub="true">           更多結果 </a>
              <input type="hidden" id="${record_type}_${key}_offset" value="9">`)
          }
          $(`.rightbox_content .${response.item_class}`).removeClass('d-none')
          $('.rightbox_content .item').not($(`.${response.item_class}`)).not($('.items')).addClass('d-none')

          clickToAnchor(`#${response.item_class}_cards`)
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
    } else {
      $(`.rightbox_content .item_${record_type}_${key}`).removeClass('d-none')
      $('.rightbox_content .item').not($(`.item_${record_type}_${key}`)).not($('.items')).addClass('d-none')
      clickToAnchor(`#item_${record_type}_${key}_cards`)
    }

    $('.getMoreCards').on('click', function(){
        getMoreCards($(this).data('card_class'),$(this).data('offset_value'),$(this).data('more_type'),$(this).data('is_sub'))
    })

    $('.getRecords').on('click', function(){
        getRecords($(this).data('record_type'),$(this).data('key'),$(this).data('value'),$(this).data('scientific_name'),
        $(this).data('limit'),$(this).data('page'),$(this).data('from'),$(this).data('go_back'))
    })


  }

  function getMoreDocs(doc_type, offset_value, more_class, card_class){

    //console.log(doc_type, offset_value)
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
        dataType : 'json',
    })
    .done(function(response) {
      (response.has_more==true) ? $(offset_value).val(Number(offset)+ 6 ) : $(more_class).addClass('d-none')

      if (card_class == '.resource-card'){
        for (let i = 0; i < response.rows.length; i++) {
          let x = response.rows[i]
            $(card_class).append(`<li>
              <div class="item h-100p">
                <div class="cate_dbox">
                  <div class="cate pdf">${ x.extension }</div>
                  <div class="date">${ x.date }</div>
                </div>
                <a href="${ x.url }" class="title"> ${ x.title } </a>
                <a href="${ x.url }" download class="dow_btn"> </a>
              </div></li>`)
        }
      } else {
        for (let i = 0; i < response.rows.length; i++) {
          let x = response.rows[i]
            $(card_class).append(`
            <li>
              <div class="nstitle">${ x.title }</div>
              <p>${ x.content }</p>
            </li>`)
          }
      }
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

  function getMoreCards(card_class, offset_value, more_type, is_sub){
    let record_type;
    if (card_class.startsWith('.col')) {
      record_type = 'col'
    } else if (card_class.startsWith('.occ')){
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
          },
          type: 'POST',
          dataType : 'json',
      })
      .done(function(response) {

        (response.has_more==true) ? $(offset_value).val(Number(offset)+ 4 ) : $(more_type).addClass('d-none')
        
        for (let i = 0; i < response.data.length; i++) {
          let x = response.data[i]

          let html;
          let matched = '';

          if (!(['中文名','學名','中文別名','同物異名'].includes(x.matched_col))) {
            matched = `<p>${x.matched_col}：${ x.matched_value }</p>`
          }

          let image = '<img class="imgarea">'

          if (x.images){
            image = `<img class="imgarea" src="${ x.images.src }">`
          }

          let taieol = '';
          let display = '';

          if (x.taieol_id){
            taieol = `<a target="_blank" href="https://taieol.tw/pages/${x.taieol_id}">生命大百科介紹</a>`
          } else {
            display = ' jc-fe'
            }



          html = `	<li>							
          <div class="flex_top">
            <div class="lefttxt">
              ${matched}
              <p>中⽂名：${x.common_name_c}</p>
              <p>學名：${x.formatted_name}</p>
              <p>中文別名：${ x.alternative_name_c }</p>
              <p>同物異名：${ x.formatted_synonyms }</p>
              <p>出現記錄筆數：${ x.occ_count }</p>
              <p>自然史典藏筆數：${ x.col_count }</p>
            </div>
            <div class="right_img">
              <div class="imgbox">
                ${image}
              </div>
            </div>
          </div>
          <div class="btn_area ${display}">
            ${taieol}
            <button class="getDist" data-taxonID="${x.taxonID}">分布圖</button>
          </div></li>`

            $(`${card_class}`).append(html)

            $('.getDist').on('click', function(){
                getDist($(this).data('taxonID'), $(this).data('common_name_c'), $(this).data('formatted_name'))
            })
        

        }
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
      $.ajax({
          url: "/get_more_cards",
          data: {
            card_class: card_class,
            keyword: $('input[name=keyword]').val(),
            csrfmiddlewaretoken: $csrf_token,
            offset: offset,
            is_sub: is_sub,
          },
          type: 'POST',
          dataType : 'json',
      })
      .done(function(response) {
        (response.has_more==true) ? $(offset_value).val(Number(offset)+ 9 ) : $(more_type).addClass('d-none')
        for (let i = 0; i < response.data.length; i++) {
          let x = response.data[i]
          if ( x.matched_col != '中文名' && x.matched_col != '學名'){
            $(card_class).append( `
            <li class="getRecords" 
                data-record_type="${record_type}"
                data-key="${x.matched_col}"
                data-value="${x.matched_value_ori}"
                data-scientific_name="${x.name}"
                data-limit="${x.count}"
                data-page="1"
                data-from="card"
                data-go_back="false">
              <div class="num">${x.count}</div>
              <div class="num_bottom"></div>
              <p>中文名：${x.common_name_c}</p>
              <p>學名：${x.val}</p>
              <p>${ x.matched_col }：${x.matched_value}</p>
            </li>` )
          } else {
            $(card_class).append( `
            <li class="getRecords" 
                data-record_type="${record_type}"
                data-key="${x.matched_col}"
                data-value="${x.matched_value_ori}"
                data-scientific_name="${x.name}"
                data-limit="${x.count}"
                data-page="1"
                data-from="card"
                data-go_back="false">
              <div class="num">${x.count}</div>
              <div class="num_bottom"></div>
              <p>中文名：${x.common_name_c}</p>
              <p>學名：${x.val}</p>
            </li>` )
          }
        }

        $('.getRecords').on('click', function(){
            getRecords($(this).data('record_type'),$(this).data('key'),$(this).data('value'),$(this).data('scientific_name'),
            $(this).data('limit'),$(this).data('page'),$(this).data('from'),$(this).data('go_back'))
        })
    
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
  }


  function resetAll(record_type){
    $(`${record_type} input:checkbox:not(:disabled)`).prop('checked', false);
  }

  function selectAll(record_type){
    $(`${record_type} input:checkbox`).prop('checked', true);
  }

  function popupField(record_type){
    $(`.${record_type}-choice`).removeClass('d-none')
    window.not_selected = $(`.${record_type}-choice input:not(:checked)`)
    window.selected = $(`.${record_type}-choice input:checked`)
  }

  $(".popbg .xx,.popbg .ovhy").not('.taxon-dist').click(function (e) {
    if ($(e.target).hasClass("xx") || $(e.target).hasClass("ovhy")) {
      window.not_selected.prop('checked', false);
      window.selected.prop('checked', true);
    }
  });

  function sendSelected(record_type){
    let selected_field = $(`.${record_type}-choice input:checked`)
    // 所有都先隱藏，除了對到的欄位
    $('td[class^="row-"]').addClass('d-none');
    $(`.row-${window.selected_key}`).removeClass('d-none');
    // 再顯示選擇的欄位
    for (let i = 0; i < selected_field.length; i++) {
      $(`td.row-${selected_field[i].id.split('-')[1]}`).removeClass('d-none');
      //console.log(selected_field[i].id.split('-')[1])
    }
    $(".popbg").addClass('d-none');
  }

  function downloadData(search_str, total_count){
    if ($('input[name=is_authenticated]').val()=='True'){
        $.ajax({
            url: "/send_download_request",
            data: {
              search_str: search_str,
              total_count: total_count,
              csrfmiddlewaretoken: $csrf_token,
              from_full: 'yes',
            },
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
  }