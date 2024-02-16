var $csrf_token = $('[name="csrfmiddlewaretoken"]').attr("value");

$(function () {

  // default active page
  if (($('input[name=resource_type]').val() != 'all') & ($('input[name=resource_type]').val() != '')) {
    $('.news_tab_in li').removeClass('now');
    $(`#${$('input[name=resource_type]').val()}`).addClass('now');
    $('#db-intro').addClass('d-none')
    updateResource($('input[name=resource_type]').val(), 1)
  } else {
    updateResource('all', 1)
  }

  // $('.changePage').on('click', function () {
  //   updateResource($(this).data('page'), $(this).data('type'))
  // })


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

  // $('.news_tab_in li').click(function () {
  //   $('.news_tab_in li').removeClass('now');
  //   $(this).addClass('now')
  //   updateResource(1, 'search')

  // })

   // 起始類別
   if ($('input[name=resource_type]').val() != '') {
    $(`.news_tab_in .li-resource-${$('input[name=resource_type]').val()}`).addClass('now')
    updateResource($('input[name=resource_type]').val(), 1) 

  } else {
    $(`.news_tab_in .li-resource-all`).addClass('now')
    updateResource('all', 1) 
  }


  $('.updateResource').on('click', function () {
    updateResource($(this).data('type'), 1)
  })

  $('.date_select .search_btn').click(function () {
    $('.already_selected ul').removeClass('d-none');
    $('.already_selected').data('filter', 'yes');
    $('.already_selected p').html(`${$("#start_date").val()}~${$("#end_date").val()}`);
    $('#db-intro').addClass('d-none')
    $('.news_tab_in li.now').trigger('click')
    // updateResource(1, 'search')

  })

  $('.already_selected ul li button.xx').on('click', function () {
    $('.already_selected ul').addClass('d-none');
    $('.already_selected').data('filter', 'no');
    // updateResource(1, 'search')
    $('.news_tab_in li.now').trigger('click')
  })

});


function updateResource(type, page) {


  $('.news_tab_in li').removeClass('now')
  $(`.li-resource-${type}`).addClass('now')


  let query;
  if ($('.already_selected').data('filter') == 'no') {
    query = {
      'type': type,
      'from': 'resource',
      'get_page': page
    }
  } else {
    query = {
      'type': type,
      'from': 'resource',
      'start_date': $("#start_date").val(),
      'end_date': $("#end_date").val(),
      'get_page': page
    }
  }


  $.ajax({
    url: "/get_resource_list",
    data: query,
    headers: { 'X-CSRFToken': $csrf_token },
    type: 'POST',
    dataType: 'json',
  })
    .done(function (response) {
      

      // remove all resources first
      $('.edu_list li').remove()
      $('.page_number').remove()

      if (type == 'all' & page == 1) {
        $('#db-intro').removeClass('d-none')
      } else {
        $('#db-intro').addClass('d-none')
      }

      // append rows
      if (response.rows.length > 0) {
        for (let i = 0; i < response.rows.length; i++) {

          if (response.rows[i].extension == 'pop') {
            $('.edu_list').append(`
          <li class="show_tech">
            <div class="item">
              <div class="cate_dbox">
                <div class="date">${response.rows[i].date}</div>
              </div>
              <a class="title ">${gettext(response.rows[i].title)}</a>
            </div>
          </li>`)
          } else if (response.rows[i].cate == 'link'){
            $('.edu_list').append(`
          <li>
            <div class="item">
            <div class="cate_dbox">
              <div class="cate ${response.rows[i].cate}">${response.rows[i].extension}</div>
              <div class="date">${response.rows[i].date}</div>
            </div>
            <a href="${response.rows[i].url}" class="title" target="_blank">${gettext(response.rows[i].title)}</a>
            </div>
          </li>`)
          } else {
            $('.edu_list').append(`
          <li>
            <div class="item">
            <div class="cate_dbox">
              <div class="cate ${response.rows[i].cate}">${response.rows[i].extension}</div>
              ${ response.rows[i].doc_url != null ? `<div class="cate web"><a href="${response.rows[i].doc_url}" target="_blank" >WEB <i class="fa-solid fa-link"></i></a></div>` : '' }
              <div class="date">${response.rows[i].date}</div>
            </div>
            <a href="/media/${response.rows[i].url}" class="title" target="_blank">${gettext(response.rows[i].title)}</a>
            <a href="/media/${response.rows[i].url}" download class="dow_btn"> </a>
            </div>
          </li>`)
          }
        }


      // 修改頁碼
      $('.edu_list').after(`<div class="page_number"></div>`)
      //if (response.page_list.length > 1){  // 判斷是否有下一頁，有才加分頁按鈕
      $(`.page_number`).append(
        `
            <a class="num changePage" data-page="1" data-type="${type}">1</a>
            <a class="pre"><span></span>${gettext('上一頁')}</a>  
            <a class="next">${gettext('下一頁')}<span></span></a>
            <a class="num changePage" data-page="${response.total_page}" data-type="${type}">${response.total_page}</a>
        `)
      //}		


      let html = ''
      for (let i = 0; i < response.page_list.length; i++) {
        if (response.page_list[i] == response.current_page) {
          html += ` <a class="num now changePage" data-page="${response.page_list[i]}" data-type="${type}">${response.page_list[i]}</a>  `;
        } else {
          html += ` <a class="num changePage" data-page="${response.page_list[i]}" data-type="${type}">${response.page_list[i]}</a>  `
        }
      }

      $('.pre').after(html)

      // 如果有下一頁，改掉next的onclick
      if (response.current_page < response.total_page) {
        $('.next').addClass('changePage')
        $('.next').data('page', response.current_page + 1)
        $('.next').data('type', type)
      } else {
        $('.next').addClass('pt-none')
      }

      if (response.current_page - 1 > 0) {
        $('.pre').addClass('changePage')
        $('.pre').data('page', response.current_page - 1)
        $('.pre').data('type', type)
      } else {
        $('.pre').addClass('pt-none')
      }

      $('.changePage').off('click')
      $('.changePage').on('click', function () {
        updateResource($(this).data('type'),$(this).data('page'))
      })



      $('.show_tech').off('click')
      $('.show_tech').on('click', function () {
        // 每次打開都放第一張
        $('.index_tech .text_tec').html($tutorial[1])
        $('.index_tech .arl').data('index', 10)
        $('.index_tech .arr').data('index', 2)
        $('.tech_pic img').attr('src', "/static/image/tutorial/pic1.png?v1")
        $('.tech-pop').removeClass('d-none')
      })

      } else {
        // if no row, show '無資料'
        $('.edu_list').append(`<li>
      <div class="item">
        <a class="title">${gettext('無資料')}</a>
      </div>
      </li>`)
      }

    })
    .fail(function (xhr, status, errorThrown) {
      alert(gettext('發生未知錯誤！請聯絡管理員'))

      console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
    })
}