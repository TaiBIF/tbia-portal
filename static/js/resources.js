var $csrf_token = $('[name="csrfmiddlewaretoken"]').attr("value");

let $tutorial = {
  1: "歡迎使用「生物多樣性資料庫共通查詢系統」！<br>如您是第一次使用本系統，建議您可以利用首頁的關鍵字查詢功能，搜尋任何您想得到的內容。",
  2: "關鍵字查詢結果頁面的左側選單除了呈現結果的分類外，也可以針對您所查詢的關鍵字所在欄位，再篩選出對應的結果。",
  3: "關鍵字查詢結果以票卡形式呈現，每張票卡皆以一個物種為單位，其中物種出現紀錄及自然史典藏結果票卡右上角的數字為符合此張票卡結果的資料筆數。<br>關鍵字如出現在多個欄位，則將會呈現多種欄位組合結果的票卡。",
  4: "若您以關鍵字搜尋無法找到精確的結果，可使用右上角的進階搜尋功能（包含物種出現紀錄查詢及自然史典藏查詢）。<br>進階搜尋功能也可以在網頁最上方的標頭中找到。",
  5: "進階搜尋功能可針對特定欄位做搜尋，也可以利用地圖進行空間查詢。",
  6: "進階搜尋的查詢結果預設僅會出現部分欄位，若欲查看其他欄位，可使用結果列表左上方的「欄位選項」勾選您希望呈現的欄位。",
  7: "您查詢的資料結果可在登入後透過「資料下載」功能取得，也可以透過「名錄下載」功能取得您查詢結果中的完整物種名錄。<br>若您希望取得敏感物種的點位資訊，則可透過「申請單次使用去模糊化敏感資料」功能取得。",
  8: "您申請取用的資料檔案皆可在登入後的帳號後台頁面中查閱並下載。",
  9: "進階搜尋的每一筆查詢結果都可以透過最前方的「查看」功能，查閱詳細的資料內容。",
  10: "每一筆資料的詳細內容頁面除了呈現物種分類階層與共通欄位的內容外，如來源資料庫有提供影像及座標點位亦會呈現。<br>除此之外，也可從資料詳細內容頁面外連至來源資料庫查看更完整的資訊。"
}

$( function() {

    $('.show_tech').on('click', function(){
      $('.tech-pop').removeClass('d-none')
    })
  
  // left 上一張
  $('.index_tech .arl').on('click', function(){
    let index = parseInt($(this).data('index'))

    if (index == 1) {
      $('.index_tech .arl').data('index', 10)
      $('.index_tech .arr').data('index', 2)
    } else if (index ==10){
      $('.index_tech .arl').data('index', 9)
      $('.index_tech .arr').data('index', 1)
    } else {
      $('.index_tech .arl').data('index', index-1)
      $('.index_tech .arr').data('index', index+1)
    }

    $('.index_tech .text_tec').html($tutorial[index])
    $('.index_tech .tech_pic img').attr('src', `/static/image/tutorial/pic${index}.png`)
  })


  // right 下一張
  $('.index_tech .arr').on('click', function(){
    let index = parseInt($(this).data('index'))

    if (index == 10) {
      $('.index_tech .arr').data('index', 1)
      $('.index_tech .arl').data('index', 9)
    } else if (index ==1){
      $('.index_tech .arr').data('index', index+1)
      $('.index_tech .arl').data('index', 10)
    } else {
      $('.index_tech .arr').data('index', index+1)
      $('.index_tech .arl').data('index', index-1)
    }

    $('.index_tech .text_tec').html($tutorial[index])
    $('.index_tech .tech_pic img').attr('src', `/static/image/tutorial/pic${index}.png`)
  })


  // default active page
  if (($('input[name=resource_type]').val() != 'all' ) & ($('input[name=resource_type]').val() != '' )) {
      $('.news_tab_in li').removeClass('now');
      $(`#${$('input[name=resource_type]').val()}`).addClass('now');
      $('#db-intro').addClass('d-none')
  } 

  $('.changePage').on('click', function(){
    updateResource($(this).data('page'), $(this).data('type'))
  })

  let date_locale = { days: ['周日', '周一', '周二', '周三', '周四', '周五', '周六'],
    daysShort: ['日', '一', '二', '三', '四', '五', '六'],
    daysMin: ['日', '一', '二', '三', '四', '五', '六'],
    months: ['一月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '十一月', '十二月'],
    monthsShort: ['一月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '十一月', '十二月'],
    today: '今天',
    clear: '清除',
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

  $('.news_tab_in li').click(function(){
    $('.news_tab_in li').removeClass('now');
    $(this).addClass('now')
    updateResource(1, 'search')

  })

  $('.date_select .search_btn').click(function(){
    $('.already_selected ul').removeClass('d-none');
    $('.already_selected').data('filter', 'yes');
    $('.already_selected p').html(`${$( "#start_date" ).val()}~${$( "#end_date" ).val()}`);
    $('#db-intro').addClass('d-none')
    updateResource(1,'search')

  })

  $('.already_selected ul li button.xx').on('click', function(){
    $('.already_selected ul').addClass('d-none');
    $('.already_selected').data('filter', 'no');
    updateResource(1,'search')
  })

});


function updateResource(page, by){

  let type = $('.news_tab_in li.now').prop('id');

    let query ;
    if ($('.already_selected').data('filter')=='no'){
        query = {'type':  type,
                'from': 'resource',
                'get_page': page
              }
    } else {
        query = {'type':  type, 
                  'from': 'resource',
                  'start_date':$( "#start_date" ).val(), 
                  'end_date':$( "#end_date" ).val(),
                  'get_page': page}
    }

    
    $.ajax({
      url: "/get_resources",
      data: query,
      headers:{'X-CSRFToken': $csrf_token},
      type: 'POST',
      dataType : 'json',
  })
  .done(function(response) {
  // remove all resources first
    $('.edu_list li').remove()
    $('.page_number').remove()

    if (type == 'all' & page == 1){
      $('#db-intro').removeClass('d-none')
    } else {
      $('#db-intro').addClass('d-none')
    }

    // append rows
    if (response.rows.length > 0){
      for (let i = 0; i < response.rows.length; i++) {

        if (response.rows[i].extension == 'pop') {
          $('.edu_list').append(`
          <li class="show_tech">
            <div class="item">
              <div class="cate_dbox">
                <div class="date">${ response.rows[i].date }</div>
              </div>
              <a href="javascript:;" class="title ">${ response.rows[i].title }</a>
            </div>
          </li>`)
        } else {
          $('.edu_list').append(`
          <li>
            <div class="item">
            <div class="cate_dbox">
              <div class="cate ${response.rows[i].cate}">${response.rows[i].extension}</div>
              <div class="date">${response.rows[i].date}</div>
            </div>
            <a href="/media/${response.rows[i].url}" class="title" target="_blank">${response.rows[i].title}</a>
            <a href="/media/${response.rows[i].url}" download class="dow_btn"> </a>
            </div>
          </li>`)  
        }
      }
    } else {
        // if no row, show '無資料'
      $('.edu_list').append(`<li>
      <div class="item">
        <a class="title">無資料</a>
      </div>
      </li>`)
    }

    $('.edu_list').after(`<div class="page_number"></div>`)

    $('.show_tech').off('click')
    $('.show_tech').on('click', function(){
      $('.tech-pop').removeClass('d-none')
    })
  
      // 修改頁碼
      //if (response.page_list.length > 1){  // 判斷是否有下一頁，有才加分頁按鈕
        $(`.page_number`).append(
          `
            <a href="javascript:;" class="num changePage" data-page="1" data-type="${by}">1</a>
            <a href="javascript:;" class="pre"><span></span>上一頁</a>  
            <a href="javascript:;" class="next">下一頁<span></span></a>
            <a href="javascript:;" class="num changePage" data-page="${response.total_page}" data-type="${by}">${response.total_page}</a>
        `)
      //}		
        


      let html = ''
      for (let i = 0; i < response.page_list.length; i++) {
        if (response.page_list[i] == response.current_page){
          html += ` <a href="javascript:;" class="num now changePage" data-page="${response.page_list[i]}" data-type="${by}">${response.page_list[i]}</a>  `;
        } else {
          html += ` <a href="javascript:;" class="num changePage" data-page="${response.page_list[i]}" data-type="${by}">${response.page_list[i]}</a>  `
        }
      }

      $('.pre').after(html)

      // 如果有下一頁，改掉next的onclick
      if (response.current_page < response.total_page){
        $('.next').addClass('changePage')
        $('.next').data('page', response.current_page+1)
        $('.next').data('type', by)
      } else {
        $('.next').addClass('pt-none')
      }  

      if (response.current_page - 1 > 0){
        $('.pre').addClass('changePage')
        $('.pre').data('page', response.current_page-1)
        $('.pre').data('type', by)
      } else {
        $('.pre').addClass('pt-none')
      }

      $('.changePage').off('click')
      $('.changePage').on('click', function(){
        updateResource($(this).data('page'),  $(this).data('type'))
      })
  })
  .fail(function( xhr, status, errorThrown ) {
    alert('發生未知錯誤！請聯絡管理員')
    console.log( 'Error: ' + errorThrown + 'Status: ' + xhr.status)
  })
}