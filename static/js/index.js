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


$(document).ready(function () {

  // left
  $('.index_tech .arl').on('click', function(){
    let index = parseInt($(this).data('index'))

    if (index == 1) {
      $(this).data('index', 10)
    } else {
      $(this).data('index', $(this).data('index')-1)
    }

    $('.index_tech .text_tec').html($tutorial[index])
    $('.index_tech .tech_pic img').attr('src', `/static/image/tutorial/pic${index}.png`)
  })


  // right
  $('.index_tech .arr').on('click', function(){
    let index = parseInt($(this).data('index'))

    if (index == 10) {
      $(this).data('index', 1)
    } else {
      $(this).data('index', $(this).data('index')+1)
    }


    $('.index_tech .text_tec').html($tutorial[index])
    $('.index_tech .tech_pic img').attr('src', `/static/image/tutorial/pic${index}.png`)
  })



    $('.updateNews').on('click', function(){
      updateNews($(this).data('type'),1)
    })


  $('#not_show_tech').on('click',function(){

      $.ajax({
        url: "/update_not_show",
        type: 'GET',
      })
      .done(function(response) {
        $('.tech-pop:not(.tech-pop-index)').hide()
      })
  })

  $('.show_tech').on('click', function(){
    $('.tech-pop.tech-pop-index').removeClass('d-none')
  })


    gsap.registerPlugin(ScrollTrigger);

    ScrollTrigger.create({
      trigger: ".section_2",
      start: "top-=45% top",
      // markers: true,
      onEnter: function () {
        $(".section_2").addClass("vivi");
      },
    });
    ScrollTrigger.create({
      trigger: ".section_3",
      start: "top-=80% top",
      // markers: true,
      onEnter: function () {
        $(".section_3").addClass("vivi");
      },
    });
    ScrollTrigger.create({
      trigger: ".section_4",
      start: "top-=80% top",
      // markers: true,
      onEnter: function () {
        $(".section_4").addClass("vivi");
      },
    });


    $('.edu_tag li').click(function(){
      let li_element = $(this)
      let type = this.id
      $.ajax({
          url: "/get_resources",
          data: {
            type: type,
            csrfmiddlewaretoken: $csrf_token,
          },
          type: 'POST',
          dataType : 'json',
      })
      .done(function(response) {
        // change active tab
        $('.edu_tag li').removeClass('now');
        li_element.addClass('now');
        // remove all resources first
        $('.edu_list li').remove()
        // append rows
          if (type=='all'){
            $('.edu_list').append(`
            <li>
            <div class="item">
              <div class="cate_dbox">
                <div class="catepin"><i class="fa-solid fa-thumbtack transform315"></i></div>
              </div>
              <a href="/resources/link" class="title" target="_blank">國內外各大資料庫及推薦網站連結</a>
            </div>
            </li> `)}        
            
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

              $('.show_tech').off('click')
              $('.show_tech').on('click', function(){
                $('.tech-pop.tech-pop-index').removeClass('d-none')
              })
            
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
              <div class="cate_dbox">
              </div>
              <a class="title">無資料</a>
            </div>
          </li>`)
        }
      })
      .fail(function( xhr, status, errorThrown ) {
        alert('發生未知錯誤！請聯絡管理員')
        console.log( 'Error: ' + errorThrown + 'Status: ' + xhr.status)
      })
    })
  

});



function updateNews(type, page){
  $('.news_tab li').removeClass('now')
  $(`.li-news-${type}`).addClass('now')
    $.ajax({
        url:'/get_news_list',
        type: 'POST',
        headers:{'X-CSRFToken': $csrf_token},
        data: {'type': type, 'page': page, 'from_index': 'yes'},
        success: function (response, status){ 
          if( response.data.length >0){
            $('.news_list').html('')
            for (let d of response.data) {
                $('.news_list').append(
                    `
                    <li>
                      <a href="/news/detail/${d.id}" target="_blank" class="imgbox">
                        <img class="img_area" src="${d.image}">
                      </a>
                      <div class="infbox">
                        <div class="center_box">
                          <div class="tag_date">
                            <div class="tag ${d.color}">${d.type_c}</div>
                            <p class="date">${d.publish_date}</p>
                          </div>
                          <a href="/news/detail/${d.id}" target="_blank" class="nstitle">
                            ${d.title}
                          </a>
                        </div>
                      </div>
                    </li>
                    `
                )
            }                        
          } else {
            $('.news_list').html('<li>無資料</li>')
          }
          $('.loadingbox').addClass('d-none');

        },
        error: function (xhr, desc, err){
          $('.loadingbox').addClass('d-none');
          alert('未知錯誤，請聯繫管理員');
        }
    });

}