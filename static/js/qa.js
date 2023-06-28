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


    $('.qa_list ul li').on('click', function(){
        if ($(this).hasClass('now')){
            $(this).removeClass('now')
        } else {
            $(this).addClass('now')
        }
    })

    $('.qa_top_item .tabb li').on('click', function(){
        updateQa(1, $(this).data('type'))
    })

    $('.changePage').on('click', function(){
        updateQa($(this).data('page'), $(this).data('type'))
    })

    $('select[name=qa_type]').on('change', function(){
        updateQa(1, $(this).val())
    })

    let selectBox = new vanillaSelectBox("#qa_type",{"placeHolder":"問題類型",search:false, disableSelectAll: true,
    });

    $('.mobile_tab .vsb-main button').css('border','').css('background','')
    $('.mobile_tab span.caret').addClass('d-none')

    $('.mobile_tab .vsb-main button').on('click',function(){
        if ($(this).next('.mobile_tab .vsb-menu').css('visibility')=='visible'){
            $(this).next('.mobile_tab .vsb-menu').addClass('visible')
        } else {
            $(this).next('.mobile_tab .vsb-menu').css('visibility', '')
            $(this).next('.mobile_tab .vsb-menu').removeClass('visible')
        }
    })

    selectBox.setValue('2')
    $('#btn-group-qa_type button span.title').addClass('color-white')

    $('#qa_type').on('change',function(){
          $('#btn-group-qa_type button span.title').addClass('color-white')
    })


    let urlParams = new URLSearchParams(window.location.search);
    if( urlParams.get('qa_id')){
      window.location = window.location.href + '#qa_hash_' + urlParams.get('qa_id')
    }
    //let menu = urlParams.get('qa_id')
})


function updateQa(page, type){


    $('select[name=qa_type]').val(type)

    $('.page_number').html('')
    $('.qa_top_item .tabb li').removeClass('now')
    $(`.qa_top_item .tabb li.qa_${type}`).addClass('now')

    $.ajax({
        url:'/get_qa_list',
        type: 'POST',
        headers:{'X-CSRFToken': $csrf_token},
        data: {'type': type, 'page': page},

        success: function (response, status){ 
          if( response.data.length >0){
            $('.qa_list ul').html('')
            for (let q of response.data) {
                $('.qa_list ul').append(
                    `
                    <li>
                    <div class="questieon">
                      <div class="mark_title">Q</div>
                      <p>${ q.question }</p>
                      <div class="arr"></div>
                    </div>
                    <div class="ans">
                      <div class="mark_title">A</div>
                      <p>${ q.answer }</p>
                    </div>
                    </li>
                `)
            }

            $('.show_tech').off('click')
            $('.show_tech').on('click', function(){
              $('.tech-pop').removeClass('d-none')
            })

            $('.qa_list ul li').off('click')
            $('.qa_list ul li').on('click', function(){
                if ($(this).hasClass('now')){
                    $(this).removeClass('now')
                } else {
                    $(this).addClass('now')
                }
            })        
              
            $('.page_number').remove()
            $('.qa_list').after(`<div class="page_number"></div>`)

              // 修改頁碼
              if (response.page_list.length > 1){  // 判斷是否有下一頁，有才加分頁按鈕
                  $(`.page_number`).append(
                    `
                      <a href="javascript:;" class="num changePage" data-page="1" data-type="${type}">1</a>
                      <a href="javascript:;" class="pre">上一頁</a>  
                      <a href="javascript:;" class="next">下一頁</a>
                      <a href="javascript:;" class="num changePage" data-page="${response.total_page}" data-type="${type}">${response.total_page}</a>
                  `)
              }		
                
              if (response.page_list.includes(response.current_page-1)){
                $('.pre').addClass('changePage')
                $('.pre').data('page', response.current_page-1)
                $('.pre').data('type', type)
              } else {
                $('.pre').addClass('pt-none')
              }

              let html = ''
              for (let i = 0; i < response.page_list.length; i++) {
                if (response.page_list[i] == response.current_page){
                  html += ` <a href="javascript:;" class="num now changePage" data-page="${response.page_list[i]}" data-type="${type}">${response.page_list[i]}</a>  `;
                } else {
                  html += ` <a href="javascript:;" class="num changePage" data-page="${response.page_list[i]}" data-type="${type}">${response.page_list[i]}</a>  `
                }
              }

              $('.pre').after(html)
      
              // 如果有下一頁，改掉next的onclick
              if (response.current_page < response.total_page){
                $('.next').addClass('changePage')
                $('.next').data('page', response.current_page+1)
                $('.next').data('type', type)
              } else {
                $('.next').addClass('pt-none')
              }  

              $('.changePage').off('click')
              $('.changePage').on('click', function(){
                updateQa($(this).data('page'), $(this).data('type'))
              })
            } else {
                $('.qa_list ul').html('<li class="no_qa">無資料</li>')
            }
            $('.loadingbox').addClass('d-none');
        },
        error: function (xhr, desc, err){
          $('.loadingbox').addClass('d-none');
          alert('未知錯誤，請聯繫管理員');
        }
  });
}
