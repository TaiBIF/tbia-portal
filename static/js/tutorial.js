

let $tutorial = {
  1: gettext("歡迎使用「生物多樣性資料庫共通查詢系統」！<br>如您是第一次使用本系統，建議您可以利用首頁的關鍵字查詢功能或網頁最上方的放大鏡功能，搜尋任何您想得到的內容。"),
  2: gettext("關鍵字查詢結果頁面的左側選單除了呈現結果的分類外，也可以針對您所查詢的關鍵字所在欄位，再篩選出對應的結果。"),
  3: gettext("關鍵字查詢結果以票卡形式呈現，每張票卡皆以一個物種為單位，其中物種出現紀錄及自然史典藏結果票卡右上角的數字為符合此張票卡結果的資料筆數。<br>關鍵字如出現在多個欄位，則將會呈現多種欄位組合結果的票卡。"),
  4: gettext("若您以關鍵字搜尋無法找到精確的結果，可使用右上角的進階搜尋功能（包含物種出現紀錄查詢及自然史典藏查詢）。<br>進階搜尋功能也可以在網頁最上方的標頭中找到。"),
  5: gettext("進階搜尋功能可針對特定欄位做搜尋，也可以利用地圖進行空間查詢。"),
  6: gettext("進階搜尋的查詢結果預設僅會出現部分欄位，若欲查看其他欄位，可使用結果列表左上方的「欄位選項」勾選您希望呈現的欄位。"),
  7: gettext("您查詢的資料結果可在登入後透過「資料下載」功能取得，也可以透過「名錄下載」功能取得您查詢結果中的完整物種名錄。<br>若您希望取得敏感物種的點位資訊，則可透過「申請單次使用去模糊化敏感資料」功能取得。"),
  8: gettext("您申請取用的資料檔案皆可在登入後的帳號後台頁面中查閱並下載。"),
  9: gettext("進階搜尋的每一筆查詢結果都可以透過最前方的「查看」功能，查閱詳細的資料內容。"),
  10: gettext("每一筆資料的詳細內容頁面除了呈現物種分類階層與共通欄位的內容外，如來源資料庫有提供影像及座標點位亦會呈現。<br>除此之外，也可從資料詳細內容頁面外連至來源資料庫查看更完整的資訊。")
}



$('.show_tech').on('click', function () {
  // 每次打開都放第一張
  $('.index_tech .text_tec').html($tutorial[1])
  $('.index_tech .arl').data('index', 10)
  $('.index_tech .arr').data('index', 2)
  $('.tech_pic img').attr('src', "/static/image/tutorial/pic1.png")
  $('.tech-pop').removeClass('d-none')
})


$('#not_show_tech').on('click', function () {

  $.ajax({
    url: "/update_not_show",
    type: 'GET',
  })
    .done(function (response) {
      $('.tech-pop:not(.tech-pop-index)').hide()
    })
})

// 起始放第一張
$('.index_tech .text_tec').html($tutorial[1])

// left 上一張
$('.index_tech .arl').on('click', function () {
  let index = parseInt($(this).data('index'))

  if (index == 1) {
    $('.index_tech .arl').data('index', 10)
    $('.index_tech .arr').data('index', 2)
  } else if (index == 10) {
    $('.index_tech .arl').data('index', 9)
    $('.index_tech .arr').data('index', 1)
  } else {
    $('.index_tech .arl').data('index', index - 1)
    $('.index_tech .arr').data('index', index + 1)
  }

  $('.index_tech .text_tec').html($tutorial[index])
  $('.index_tech .tech_pic img').attr('src', `/static/image/tutorial/pic${index}.png`)
})


// right 下一張
$('.index_tech .arr').on('click', function () {
  let index = parseInt($(this).data('index'))

  if (index == 10) {
    $('.index_tech .arr').data('index', 1)
    $('.index_tech .arl').data('index', 9)
  } else if (index == 1) {
    $('.index_tech .arr').data('index', index + 1)
    $('.index_tech .arl').data('index', 10)
  } else {
    $('.index_tech .arr').data('index', index + 1)
    $('.index_tech .arl').data('index', index - 1)
  }

  $('.index_tech .text_tec').html($tutorial[index])
  $('.index_tech .tech_pic img').attr('src', `/static/image/tutorial/pic${index}.png`)
})
